########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\fac_enforcer.py total lines 142 
########################################################################

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, Type
import time
import os
import hmac
import hashlib
import base64
import json
import logging

from flowork_kernel.capabilities.agent_run import AgentRun


logger = logging.getLogger(__name__)

CAPABILITY_IMPLEMENTATIONS: Dict[str, Type] = {
    "agent.run": AgentRun,

}

DEFAULT_COSTS = {
    "agent.run": 0,
    "http.fetch": 5,
    "fs.read": 2,
}

FAC_SIGNING_KEY = os.getenv("FAC_SIGNING_KEY", "default-unsafe-signing-key-please-change-me")
if FAC_SIGNING_KEY == "default-unsafe-signing-key-please-change-me":
    logger.warning("FAC_SIGNING_KEY is set to default. This is INSECURE.")


class BudgetMeter:

    def __init__(self, total: int):
        self.total = int(total)
        self.used = 0

    def remaining(self) -> int:
        return max(0, self.total - self.used)

    def consume(self, units: int) -> None:
        if units < 0:
            units = 0
        if self.used + units > self.total:
            raise PermissionError(f"Out of gas: used={self.used}, add={units}, total={self.total}")
        self.used += units

class FacRuntime:


    def __init__(self, fac_dict: Dict[str, Any]):
        if not isinstance(fac_dict, dict):
            raise ValueError("FAC must be a dictionary")

        self.fac_dict = fac_dict

        if not self._verify_signature():
            raise PermissionError("FAC signature invalid")

        self._validate_ttl()

        self.owner_id = str(fac_dict.get("owner_id", ""))
        self.engine_id = str(fac_dict.get("engine_id", ""))
        self.namespace = str(fac_dict.get("namespace", ""))

        self.budget = BudgetMeter(int(fac_dict.get("budget_gas", 0)))


        self.cap_impls: Dict[str, Any] = {}
        for spec in fac_dict.get("capabilities", []):
            spec_name = spec.get("name")
            impl_cls = CAPABILITY_IMPLEMENTATIONS.get(spec_name)

            if not impl_cls:
                raise PermissionError(f"Unknown capability in FAC: {spec_name}")

            self.cap_impls[spec_name] = impl_cls(scope=spec.get("scope", {}))

    def _serialize_for_signing(self) -> bytes:

        fac_copy = self.fac_dict.copy()
        fac_copy.pop("signature", None)
        return json.dumps(fac_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _verify_signature(self) -> bool:

        signature_b64 = self.fac_dict.get("signature")
        if not signature_b64:
            logger.warning("FAC missing signature. Denying.")
            return False

        message_bytes = self._serialize_for_signing()
        key_bytes = FAC_SIGNING_KEY.encode("utf-8")

        try:
            expected_signature_bytes = hmac.new(key_bytes, message_bytes, hashlib.sha256).digest()
            provided_signature_bytes = base64.urlsafe_b64decode(signature_b64.encode("utf-8"))

            return hmac.compare_digest(expected_signature_bytes, provided_signature_bytes)
        except Exception as e:
            logger.error(f"FAC signature verification error: {e}")
            return False

    def _validate_ttl(self, max_ttl_seconds: int = 7200) -> None:

        now = time.time()
        issued_at = self.fac_dict.get("issued_at", 0)
        expires_at = self.fac_dict.get("expires_at", 0)

        if not isinstance(issued_at, (int, float)) or not isinstance(expires_at, (int, float)):
            raise PermissionError("FAC time fields (iat/exp) are invalid")
        if expires_at <= now:
            raise PermissionError(f"FAC has expired (exp: {expires_at} vs now: {now})")
        if issued_at > (now + 300):
            raise PermissionError("FAC was issued in the future (check clocks)")

        ttl = expires_at - issued_at
        if ttl <= 0 or ttl > max_ttl_seconds:
            raise PermissionError(f"FAC TTL ({ttl}s) is invalid or exceeds max ({max_ttl_seconds}s)")

    def _cost_for(self, cap_name: str, size_bytes: int = 0) -> int:

        base = DEFAULT_COSTS.get(cap_name, 1)
        kb = (size_bytes + 1023) // 1024
        return base + kb


    def permit_run_engine(self, engine_id_to_run: str) -> None:

        cap = self.cap_impls.get("agent.run")
        if not cap:
            raise PermissionError("FAC does not allow 'agent.run' capability")

        self.budget.consume(self._cost_for("agent.run"))

        cap.permit_engine(engine_id_to_run)
