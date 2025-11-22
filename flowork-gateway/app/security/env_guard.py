########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\security\env_guard.py total lines 81 
########################################################################

import os
import sys
from typing import Dict, Any, Optional

def check_strict_env():

    is_strict = os.environ.get('STRICT_ENV', 'true').lower() == 'true'
    if not is_strict:
        print("[BOOT][WARN] STRICT_ENV=false. Skipping default credential check. THIS IS INSECURE.")
        return
    print("[BOOT] STRICT_ENV=true. Checking for default credentials...")
    weak_creds = {
        "JWT_SECRET_KEY": "changeme",
        "ADMIN_DEFAULT_PASSWORD": "admin"
    }
    is_default = False
    for key, default_value in weak_creds.items():
        if os.environ.get(key) == default_value:
            print(f"[BOOT][FATAL] Default credential detected for '{key}'.", file=sys.stderr)
            is_default = True
    if is_default:
        print("[BOOT][FATAL] Please change these values in your .env file before starting.", file=sys.stderr)
        sys.exit(1)
    print("[BOOT] Strict ENV check passed.")


_BAD_SECRETS = {"", "please-change-me", "changeme", "secret", "default", "test"}

def _truthy(v: Optional[str]) -> bool:
    if v is None: return False
    return v.strip().lower() in {"1","true","yes","on"}

def assert_secret(varname: str, min_len: int = 32) -> None:
    v = os.getenv(varname, "")
    if v in _BAD_SECRETS or len(v) < min_len:
        raise RuntimeError(f"Unsafe secret for {varname}: min_len={min_len} and must not be default/example")

def guard_runtime() -> Dict[str, Any]:

    env = os.getenv("ENV", "production").lower()
    debug = os.getenv("DEBUG", "0")
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    allowed = os.getenv("GW_ALLOWED_ORIGINS", "")
    public_url = os.getenv("PUBLIC_BASE_URL", "")

    try:
        assert_secret("JWT_SECRET_KEY", min_len=64)
    except RuntimeError:
        print("[WARN] JWT_SECRET_KEY is weak/missing. Checking alias GW_JWT_SECRET...")
        assert_secret("GW_JWT_SECRET", min_len=64)
        print("[WARN] ... Alias GW_JWT_SECRET is OK, but please migrate to JWT_SECRET_KEY.")

    fac_key = os.getenv("FAC_SIGNING_KEY", "")
    if fac_key:
        if len(fac_key) < 32:
            raise RuntimeError("FAC_SIGNING_KEY too short; use the generator script.")

    if env == "production":
        if _truthy(debug):
            raise RuntimeError("ENV=production but DEBUG=1. This is insecure. Set DEBUG=0.")
        if allowed.strip() in {"*", "http://*", "https://*"} or not allowed.strip():
            print(f"[WARN] GW_ALLOWED_ORIGINS is '{allowed}'. This is unsafe for production.")
        if not public_url or "127.0.0.1" in public_url or "localhost" in public_url:
            print(f"[WARN] PUBLIC_BASE_URL is '{public_url}'. This may not be reachable for webhooks/callbacks in production.")

    return {
        "env": env,
        "debug": "0" if env == "production" else debug,
        "log_level": log_level,
        "log_format": os.getenv("LOG_FORMAT", "json"),
        "log_redact": os.getenv("LOG_SENSITIVE", "0") not in ("1", "true", "yes", "on"),
        "allowed_origins_set": bool(allowed.strip()) and allowed.strip() != "*",
        "public_base_url_set": bool(public_url and "127.0.0.1" not in public_url),
        "fac_signing_key_present": bool(fac_key),
    }
