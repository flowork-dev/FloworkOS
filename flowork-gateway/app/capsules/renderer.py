########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\capsules\renderer.py total lines 69 
########################################################################

from __future__ import annotations
from typing import Dict, Any, List
import os, time, os.path

from app.security.fac_utils import (
    validate_fac_budget,
    validate_fac_ttl,
    sign_fac_dict
)

CAPSULE_REPO_DIR = os.getenv("CAPSULE_REPO_DIR", r"C:\FLOWORK\repos")

def _map_path_prefix(scope: Dict[str, Any]) -> Dict[str, Any]:

    out = dict(scope)
    pp = str(scope.get("path_prefix", "")).strip()
    if not pp:
        return out
    if pp.startswith("/repo"):
        rest = pp[len("/repo"):].lstrip("/\\")
        mapped = os.path.join(CAPSULE_REPO_DIR, rest)
        out["path_prefix"] = os.path.abspath(mapped)
    return out

def _normalize_capabilities(caps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in caps:
        c2 = dict(c)
        sc = dict(c2.get("scope", {}))
        if "path_prefix" in sc:
            sc = _map_path_prefix(sc)
        c2["scope"] = sc
        out.append(c2)
    return out

def fac_from_capsule(user: Dict[str, Any], engine: Dict[str, Any], capsule: Dict[str, Any]) -> Dict[str, Any]:
    ft = dict(capsule["fac_template"])
    role = ft.get("role", "CapsuleAgent")
    budget = int(ft.get("budget_gas", 256))
    caps = _normalize_capabilities(ft.get("capabilities", []))

    fac = {
        "agent_id": f"capsule-{capsule['capsule_id']}",
        "version": "v1",
        "owner_id": str(engine["owner_id"]),
        "engine_id": str(engine["id"]),
        "role": role,
        "capabilities": caps,
        "memory_mounts": [
            {"mount_type": "episodic", "mount_id": str(user["id"]), "access": "rw"}
        ],
        "budget_gas": budget,
        "namespace": f"{engine['owner_id']}/{engine['id']}/caps:{capsule['capsule_id']}/u:{user['id']}",
        "issued_at": time.time(),
        "expires_at": time.time() + int(os.getenv("FAC_TTL_SECONDS", "3600")),
        "signature": None
    }

    validate_fac_budget(fac, max_budget=int(os.getenv("FAC_MAX_BUDGET", "20000")))
    validate_fac_ttl(fac, max_ttl_seconds=24*3600)

    fac = sign_fac_dict(fac)
    return fac
