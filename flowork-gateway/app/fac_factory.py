########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\fac_factory.py total lines 87 
########################################################################

from __future__ import annotations
from typing import Dict, Any, Optional
import os
import time

from app.models import User, RegisteredEngine
from app.security.fac_utils import (
    validate_fac_budget,
    validate_fac_ttl,
    sign_fac_dict,
    FAC_TTL_SECONDS
)

DEFAULT_BUDGET = int(os.getenv("FAC_DEFAULT_BUDGET_OWNER", "10000"))
MAX_BUDGET = int(os.getenv("FAC_MAX_BUDGET_OWNER", "500000"))

def _owner_default_namespace(owner_id: str, engine_id: str) -> str:

    return f"{owner_id}/{engine_id}"

def build_fac_for_owner(
    request_user: User,
    engine: RegisteredEngine,
    intent: str
) -> Dict[str, Any]:


    caps = [
        {
            "name": "agent.run",
            "scope": {"engine_id": "*"},
            "description": "Owner-level access (full permissions)"
        },
        {
            "name": "http.fetch",
            "scope": {"domain": "*"},
            "description": "Owner-level HTTP access (full)"
        },
        {
            "name": "fs.read",
            "scope": {"path_prefix": "*"},
            "description": "Owner-level filesystem read (full)"
        }
    ]

    namespace = _owner_default_namespace(
        owner_id=str(request_user.id),
        engine_id=str(engine.id),
    )

    fac: Dict[str, Any] = {
        "agent_id": f"agent-owner-{request_user.id[:8]}",
        "version": "v1",
        "owner_id": str(request_user.id),
        "engine_id": str(engine.id),
        "role": "Owner",
        "capabilities": caps,
        "memory_mounts": [
            {
                "mount_type": "episodic",
                "mount_id": str(request_user.id),
                "access": "rw"
            },
            {
                "mount_type": "permanent",
                "mount_id": str(request_user.id),
                "access": "rw"
            }
        ],
        "budget_gas": min(DEFAULT_BUDGET, MAX_BUDGET),
        "namespace": namespace,
        "issued_at": time.time(),
        "expires_at": time.time() + FAC_TTL_SECONDS,
        "signature": None
    }

    validate_fac_budget(fac, max_budget=MAX_BUDGET)
    validate_fac_ttl(fac, max_ttl_seconds=FAC_TTL_SECONDS * 2)
    fac = sign_fac_dict(fac)

    return fac
