########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\security\fac_utils.py total lines 101 
########################################################################

from __future__ import annotations
from typing import Dict, Any, Optional
import os
import time
import hmac
import hashlib
import base64
import json

FAC_SIGNING_KEY = os.getenv("FAC_SIGNING_KEY", "default-unsafe-signing-key-please-change-me")
if FAC_SIGNING_KEY == "default-unsafe-signing-key-please-change-me":
    print(
        "[WARN] FAC_SIGNING_KEY is set to default. This is INSECURE. "
        "Set a strong secret in your .env file.",
        flush=True
    )

FAC_TTL_SECONDS = int(os.getenv("FAC_TTL_SECONDS", "3600"))

def _get_fac_signing_key_bytes() -> bytes:

    return FAC_SIGNING_KEY.encode("utf-8")

def _serialize_fac_for_signing(fac_dict: Dict[str, Any]) -> bytes:

    fac_copy = fac_dict.copy()
    fac_copy.pop("signature", None)

    return json.dumps(fac_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sign_fac_dict(fac_dict: Dict[str, Any]) -> Dict[str, Any]:

    if not FAC_SIGNING_KEY:
        raise ValueError("FAC_SIGNING_KEY is not set. Cannot sign FAC.")

    message_bytes = _serialize_fac_for_signing(fac_dict)
    key_bytes = _get_fac_signing_key_bytes()

    signature_bytes = hmac.new(key_bytes, message_bytes, hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature_bytes).decode("utf-8")

    fac_dict["signature"] = signature_b64
    return fac_dict

def verify_fac_signature(fac_dict: Dict[str, Any]) -> bool:

    if not FAC_SIGNING_KEY:
        print("[WARN] FAC_SIGNING_KEY is not set. Signature verification skipped.", flush=True)
        return True

    signature_b64 = fac_dict.get("signature")
    if not signature_b64:
        return False

    message_bytes = _serialize_fac_for_signing(fac_dict)
    key_bytes = _get_fac_signing_key_bytes()

    try:
        expected_signature_bytes = hmac.new(key_bytes, message_bytes, hashlib.sha256).digest()
        provided_signature_bytes = base64.urlsafe_b64decode(signature_b64.encode("utf-8"))

        return hmac.compare_digest(expected_signature_bytes, provided_signature_bytes)
    except Exception:
        return False

def validate_fac_ttl(fac_dict: Dict[str, Any], max_ttl_seconds: int = 7200) -> None:

    now = time.time()
    issued_at = fac_dict.get("issued_at", 0)
    expires_at = fac_dict.get("expires_at", 0)

    if not isinstance(issued_at, (int, float)) or not isinstance(expires_at, (int, float)):
        raise PermissionError("FAC time fields (iat/exp) are invalid")

    if expires_at <= now:
        raise PermissionError("FAC has expired")

    if issued_at > (now + 60):
        raise PermissionError("FAC was issued in the future (check clocks)")

    ttl = expires_at - issued_at
    if ttl <= 0:
        raise PermissionError("FAC expiration is before issue time")

    if ttl > max_ttl_seconds:
        raise PermissionError(f"FAC TTL ({ttl}s) exceeds maximum allowed ({max_ttl_seconds}s)")

def validate_fac_budget(fac_dict: Dict[str, Any], max_budget: int = 20000) -> None:

    budget = fac_dict.get("budget_gas", 0)
    if not isinstance(budget, int) or budget <= 0:
        raise PermissionError("FAC budget_gas must be a positive integer")

    if budget > max_budget:
        raise PermissionError(f"FAC budget ({budget}) exceeds maximum allowed ({max_budget})")
