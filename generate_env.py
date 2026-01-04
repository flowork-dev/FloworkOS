########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\generate_env.py total lines 407 
########################################################################

import os
import sys
import re
import json
import uuid
import secrets
import shutil
import time
from pathlib import Path
from typing import Dict, Set

GUI_KEY_FILE_NAME = "DO_NOT_DELETE_private_key.txt"

def _arg_value(argv, key_prefix: str) -> str | None:
    key_prefix_eq = f"{key_prefix}="
    for i, arg in enumerate(argv):
        if arg.startswith(key_prefix_eq):
            return arg[len(key_prefix_eq):]
        if arg == key_prefix and i + 1 < len(argv):
            return argv[i + 1]
    return None

def _has_arg(argv, key: str) -> bool:
    return key in argv

def _get_root(argv) -> Path:
    env_root = os.environ.get("FLOWORK_ROOT")
    if env_root:
        return Path(env_root).resolve()
    arg_root = _arg_value(argv, "--root")
    if arg_root:
        return Path(arg_root).resolve()
    return Path(__file__).parent.resolve()

def _gen_secret(length: int = 48) -> str:
    return secrets.token_hex(length)

def _gen_uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"

def _print_hint(key: str, value: str, show_len: int = 6):
    print(f"[hint] Generated {key} = {value[:show_len]}...")

ROTATABLE_KEYS: Set[str] = {
    "JWT_SECRET_KEY",
    "ADMIN_DEFAULT_PASSWORD",
    "ADMIN_TOKEN",
    "GATEWAY_SECRET_TOKEN",
    "FLOWORK_ENGINE_ID",
    "FLOWORK_ENGINE_TOKEN",
    "FAC_SIGNING_KEY",
    "ENGINE_OWNER_PRIVATE_KEY",
}

DEFAULT_ADMIN_USERNAME = "admin"

def write_gui_login_key(data_dir: Path, private_key: str):

    if not private_key:
        print("[warn] Cannot write GUI login key: ENGINE_OWNER_PRIVATE_KEY is missing.")
        return

    key_file_path = data_dir / GUI_KEY_FILE_NAME

    content = [
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
        "!!! YOUR LOGIN PRIVATE KEY IS:",
        "",
        f"{private_key}",
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
        "\n",
        "(English Hardcode) This key allows the Flowork GUI to connect to your local Engine.",
        "(English Hardcode) DO NOT DELETE THIS FILE OR SHARE THIS KEY.",
    ]

    try:
        key_file_path.write_text("\n".join(content), encoding="utf-8")
        print(f"[ok] Wrote GUI login key to {key_file_path}")
    except Exception as e:
        print(f"[error] FAILED to write GUI login key to {key_file_path}: {e}")

def main(argv):
    try:
        root_dir = _get_root(argv)
        env_path = root_dir / ".env"
        data_dir = root_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"[info] Target FLOWORK_ROOT: {root_dir}")
        print(f"[info] Target .env file:   {env_path}")
        print(f"[info] Target data dir:    {data_dir}")
    except Exception as e:
        print(f"[fatal] Failed to initialize root path: {e}", file=sys.stderr)
        print(f"[fatal] Please check permissions.", file=sys.stderr)
        sys.exit(1)

    force_rotate_all = _has_arg(argv, "--force")
    rotate_specific_raw = _arg_value(argv, "--rotate")
    rotate_specific = set(rotate_specific_raw.split(",")) if rotate_specific_raw else set()

    if force_rotate_all:
        print("[warn] --force enabled. ALL rotatable keys will be REGENERATED.")
    elif rotate_specific:
        print(f"[info] --rotate enabled for: {', '.join(rotate_specific)}")

    if env_path.exists() and (force_rotate_all or rotate_specific):
        try:
            ts = time.strftime("%Y%m%d%H%M%S")
            bak_path = env_path.parent / f".env.bak-{ts}"
            shutil.copyfile(env_path, bak_path)
            print(f"[info] Created backup of existing .env: {bak_path}")
        except Exception as e:
            print(f"[error] FAILED to create .env backup: {e}", file=sys.stderr)
            sys.exit(1)

    existing_env: Dict[str, str] = {}
    if env_path.exists():
        print(f"[info] Loading existing {env_path}")
        try:
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    existing_env[key.strip()] = value.strip()
        except Exception as e:
            print(f"[error] Failed to read {env_path}: {e}. Starting fresh.")
            existing_env = {}

    new_env = existing_env.copy()

    def _should_rotate(key: str) -> bool:
        if key not in ROTATABLE_KEYS:
            return False
        if key not in new_env:
            return True
        if force_rotate_all:
            return True
        if key in rotate_specific:
            return True
        return False


    JWT_SECRET_KEY = new_env.get("JWT_SECRET_KEY")
    if _should_rotate("JWT_SECRET_KEY"):
        JWT_SECRET_KEY = _gen_secret(64)
        new_env["JWT_SECRET_KEY"] = JWT_SECRET_KEY
        _print_hint("JWT_SECRET_KEY", JWT_SECRET_KEY)

    ADMIN_DEFAULT_PASSWORD = new_env.get("ADMIN_DEFAULT_PASSWORD")
    if _should_rotate("ADMIN_DEFAULT_PASSWORD"):
        ADMIN_DEFAULT_PASSWORD = secrets.token_urlsafe(24)
        new_env["ADMIN_DEFAULT_PASSWORD"] = ADMIN_DEFAULT_PASSWORD
        _print_hint("ADMIN_DEFAULT_PASSWORD", ADMIN_DEFAULT_PASSWORD)

    ADMIN_TOKEN = new_env.get("ADMIN_TOKEN")
    if _should_rotate("ADMIN_TOKEN"):
        ADMIN_TOKEN = f"fk-admin-{secrets.token_urlsafe(48)}"
        new_env["ADMIN_TOKEN"] = ADMIN_TOKEN
        _print_hint("ADMIN_TOKEN", ADMIN_TOKEN)

    GATEWAY_SECRET_TOKEN = new_env.get("GATEWAY_SECRET_TOKEN")
    if _should_rotate("GATEWAY_SECRET_TOKEN"):
        GATEWAY_SECRET_TOKEN = _gen_secret(48)
        new_env["GATEWAY_SECRET_TOKEN"] = GATEWAY_SECRET_TOKEN
        _print_hint("GATEWAY_SECRET_TOKEN", GATEWAY_SECRET_TOKEN)

    FLOWORK_ENGINE_ID = new_env.get("FLOWORK_ENGINE_ID")
    if _should_rotate("FLOWORK_ENGINE_ID"):
        FLOWORK_ENGINE_ID = _gen_uuid("eng")
        new_env["FLOWORK_ENGINE_ID"] = FLOWORK_ENGINE_ID
        _print_hint("FLOWORK_ENGINE_ID", FLOWORK_ENGINE_ID, show_len=8)

    FLOWORK_ENGINE_TOKEN = new_env.get("FLOWORK_ENGINE_TOKEN")
    if _should_rotate("FLOWORK_ENGINE_TOKEN"):
        FLOWORK_ENGINE_TOKEN = f"fk-eng-{secrets.token_urlsafe(64)}"
        new_env["FLOWORK_ENGINE_TOKEN"] = FLOWORK_ENGINE_TOKEN
        _print_hint("FLOWORK_ENGINE_TOKEN", FLOWORK_ENGINE_TOKEN, show_len=10)

    FAC_SIGNING_KEY = new_env.get("FAC_SIGNING_KEY")
    if _should_rotate("FAC_SIGNING_KEY"):
        FAC_SIGNING_KEY = _gen_secret(48)
        new_env["FAC_SIGNING_KEY"] = FAC_SIGNING_KEY
        _print_hint("FAC_SIGNING_KEY", FAC_SIGNING_KEY, show_len=10)

    gui_key_to_inject = None
    try:
        gui_key_file_path = data_dir / GUI_KEY_FILE_NAME

        if gui_key_file_path.exists():
            print(f"[info] Found existing GUI key file at: {gui_key_file_path}")
            key_file_content = gui_key_file_path.read_text(encoding="utf-8")
            match = re.search(r"(0x[a-fA-F0-9]{64})", key_file_content)
            if match:
                gui_key_to_inject = match.group(1)
                print(f"[ok] Found existing GUI key to inject: {gui_key_to_inject[:10]}...")
            else:
                print(f"[warn] GUI key file exists, but no 0x key was found inside.")
        else:
            print(f"[info] No existing GUI key file found at {gui_key_file_path}.")
    except Exception as e:
        print(f"[error] Failed to read existing GUI key file: {e}.")

    if _should_rotate("ENGINE_OWNER_PRIVATE_KEY") and not gui_key_to_inject:
        print("[info] Generating new ENGINE_OWNER_PRIVATE_KEY.")
        new_key = "0x" + _gen_secret(32)
        new_env["ENGINE_OWNER_PRIVATE_KEY"] = new_key
        _print_hint("NEW ENGINE_OWNER_PRIVATE_KEY", new_key, 10)

    elif gui_key_to_inject:
        if new_env.get("ENGINE_OWNER_PRIVATE_KEY") != gui_key_to_inject:
            new_env["ENGINE_OWNER_PRIVATE_KEY"] = gui_key_to_inject
            print(f"[ok] INJECTED existing GUI key into .env")
        else:
            print(f"[ok] .env ENGINE_OWNER_PRIVATE_KEY already matches existing GUI key.")

    elif "ENGINE_OWNER_PRIVATE_KEY" not in new_env:
        print("[info] No ENGINE_OWNER_PRIVATE_KEY in .env and no GUI key found. Generating new key.")
        new_key = "0x" + _gen_secret(32)
        new_env["ENGINE_OWNER_PRIVATE_KEY"] = new_key
        _print_hint("NEW ENGINE_OWNER_PRIVATE_KEY", new_key, 10)

    else:
        print("[ok] Using existing ENGINE_OWNER_PRIVATE_KEY from .env file.")


    root_dir_host_os = str(root_dir).replace("/", "\\")
    data_dir_host_os = str(data_dir).replace("/", "\\")

    STATIC_VARS = {
        "ENV": "production",
        "DEBUG": "0",
        "LOG_FORMAT": "json",
        "LOG_SENSITIVE": "0",
        "PUBLIC_BASE_URL": "http://127.0.0.1:8000",
        "GW_ALLOWED_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173",

        "GATEWAY_LOG_DIR": f"{data_dir_host_os}\\logs",
        "CORE_LOG_DIR": f"{data_dir_host_os}\\logs",
        "LOG_LEVEL": "INFO",
        "STRICT_ENV": "true",
        "JWT_ALGORITHM": "HS256",
        "JWT_HEADER_NAME": "Authorization",
        "JWT_HEADER_TYPE": "Bearer",
        "DATABASE_URL": f"sqlite:///{data_dir_host_os}\\gateway.db",
        "DATABASE_URL_Q_00": f"sqlite:///{data_dir_host_os}\\queue_00.db",
        "DATABASE_URL_Q_01": f"sqlite:///{data_dir_host_os}\\queue_01.db",
        "DATABASE_URL_Q_02": f"sqlite:///{data_dir_host_os}\\queue_02.db",
        "DATABASE_URL_Q_03": f"sqlite:///{data_dir_host_os}\\queue_03.db",
        "DATABASE_URL_RL": f"sqlite:///{data_dir_host_os}\\ratelimit.db",
        "DATABASE_URL_ETL": f"sqlite:///{data_dir_host_os}\\etl_outbox.db",
        "DEFAULT_ADMIN_USERNAME": DEFAULT_ADMIN_USERNAME,
        "DOCKER_DATA_DIR": "./data",
        "DOCKER_CORE_DIR": "./flowork-core",
        "DOCKER_GATEWAY_DIR": "./flowork-gateway",
        "FLOWORK_CORE_HOST": "127.0.0.1",
        "FLOWORK_CORE_PORT": "8001",
        "FLOWORK_GATEWAY_URL": "http://127.0.0.1:8000",
        "FLOWORK_TUNNEL_URL": "http://127.0.0.1:8002",
        "GATEWAY_PORT_HOST": "8000",
        "ETL_OUTBOX_ENABLED": "true",
        "ETL_OUTBOX_TARGET_DIR": f"{data_dir_host_os}/etl_outbox",
        "CAPSULE_DIR": f"{root_dir_host_os}\\capsules",
        "CAPSULE_REPO_DIR": f"{root_dir_host_os}\\repos",

        "TUNNEL_TOKEN": "PASTE_CLOUDFLARED_TUNNEL_TOKEN_HERE",
        "SOCKET_URL": "PASTE_YOUR_SOCKET_URL_HERE",

        "FAC_TTL_SECONDS": "3600",
        "FAC_DEFAULT_BUDGET": "256",
        "FAC_MAX_BUDGET": "20000",
    }

    for key, value in STATIC_VARS.items():
        new_env.setdefault(key, value)

    if new_env.get("ENV", "production").lower() == "production":
        if new_env.get("DEBUG") != "0":
            print("[info] ENV=production detected. Forcing DEBUG=0.")
            new_env["DEBUG"] = "0"
        if new_env.get("LOG_SENSITIVE") != "0":
            print("[info] ENV=production detected. Forcing LOG_SENSITIVE=0 (redaction enabled).")
            new_env["LOG_SENSITIVE"] = "0"


    DEPRECATED_VARS = {
        "FLOWORK_ADMIN_PASSWORD",
        "FLOWORK_ADMIN_TOKEN",
        "INTERNAL_API_SECRET",
        "USER_RATE_LIMIT",
        "ENGINE_RATE_LIMIT",
        "GW_JWT_SECRET",
        "CLOUDFLARED_TOKEN", # Moved to TUNNEL_TOKEN or removed
    }

    cleaned_env = {}
    keys_removed = []

    gw_jwt = new_env.get("GW_JWT_SECRET")
    jwt_key = new_env.get("JWT_SECRET_KEY")

    if jwt_key:
        new_env["JWT_SECRET_KEY"] = jwt_key
    elif gw_jwt:
        new_env["JWT_SECRET_KEY"] = gw_jwt
        print("[info] Copied deprecated GW_JWT_SECRET to JWT_SECRET_KEY")


    for key, value in new_env.items():
        if key not in DEPRECATED_VARS:
            cleaned_env[key] = value
        else:
            keys_removed.append(key)

    if keys_removed:
        print(f"[info] Removed deprecated keys: {', '.join(keys_removed)}")

    new_env = cleaned_env


    sorted_keys = sorted(new_env.keys())

    output_lines = [
        "########################################################################",
        "# Flowork Environment Configuration (C:\\FLOWORK\\.env)",
        "# (English Hardcode) Generated by generate_env.py",
        "########################################################################",
        "\n# (English Hardcode) --- Security (Rotatable) ---",
        "# (English Hardcode) WARNING: DO NOT SHARE THESE KEYS.",
    ]

    for key in sorted_keys:
        if key in ROTATABLE_KEYS:
            output_lines.append(f"{key}={new_env[key]}")

    output_lines.append("\n# (English Hardcode) --- Configuration (Defaults) ---")

    for key in sorted_keys:
        if key not in ROTATABLE_KEYS:
            output_lines.append(f"{key}={new_env[key]}")

    output_content = "\n".join(output_lines) + "\n"

    try:
        if env_path.exists():
            if env_path.read_text(encoding="utf-8") != output_content:
                env_path.write_text(output_content, encoding="utf-8")
                print(f"[ok] Wrote changes to {env_path}")
            else:
                print(f"[ok] {env_path} is already up-to-date.")
        else:
            env_path.write_text(output_content, encoding="utf-8")
            print(f"[ok] Wrote new {env_path}")
    except Exception as e:
        print(f"[fatal] FAILED to write {env_path}: {e}", file=sys.stderr)
        print(f"[fatal] Please check file permissions.", file=sys.stderr)
        sys.exit(1)

    write_gui_login_key(data_dir, new_env.get("ENGINE_OWNER_PRIVATE_KEY"))


    deprecated_conf_path = data_dir / "docker-engine.conf"
    try:
        conf = {
            "engine_id": new_env.get("FLOWORK_ENGINE_ID"),
            "engine_token": new_env.get("FLOWORK_ENGINE_TOKEN"),
            "gateway_url": new_env.get("FLOWORK_GATEWAY_URL"),
            "log_level": new_env.get("LOG_LEVEL"),
            "data_dir": "/app/data",
            "core_log_dir": "/app/data/logs",
        }
        conf_content = json.dumps(conf, indent=4)
        if deprecated_conf_path.exists():
            if deprecated_conf_path.read_text(encoding="utf-8") != conf_content:
                deprecated_conf_path.unlink()
                deprecated_conf_path.write_text(conf_content, encoding="utf-8")
                print(f"[ok] Wrote changes to {deprecated_conf_path} (DEPRECATED)")
            else:
                print(f"[ok] {deprecated_conf_path} is already up-to-date. (DEPRECATED)")
        else:
            deprecated_conf_path.write_text(conf_content, encoding="utf-8")
            print(f"[ok] Wrote new {deprecated_conf_path} (DEPRECATED)")
    except Exception as e:
        print(f"[error] Failed writing {deprecated_conf_path}: {e}")

    _print_hint("DEFAULT_ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    _print_hint("ADMIN_DEFAULT_PASSWORD", ADMIN_DEFAULT_PASSWORD)
    _print_hint("ADMIN_TOKEN", ADMIN_TOKEN)
    _print_hint("JWT_SECRET_KEY", JWT_SECRET_KEY)
    _print_hint("GATEWAY_SECRET_TOKEN", GATEWAY_SECRET_TOKEN)
    _print_hint("FLOWORK_ENGINE_ID", FLOWORK_ENGINE_ID, show_len=8)
    _print_hint("FLOWORK_ENGINE_TOKEN", FLOWORK_ENGINE_TOKEN, show_len=10)
    _print_hint("ENGINE_OWNER_PRIVATE_KEY", new_env.get("ENGINE_OWNER_PRIVATE_KEY", "N/A"), 10)

    if force_rotate_all or rotate_specific:
        print("\n[SUCCESS] Keys rotated successfully.")
    else:
        print("\n[SUCCESS] Environment files verified.")

if __name__ == "__main__":
    main(sys.argv)
