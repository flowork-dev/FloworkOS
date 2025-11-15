########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\sharing_fac.py total lines 100 
########################################################################

from __future__ import annotations
from typing import Dict, Any
import os
import time

from app.models import User, RegisteredEngine, EngineShare
from app.security.fac_utils import (
    validate_fac_budget,
    validate_fac_ttl,
    sign_fac_dict,
    FAC_TTL_SECONDS
)

DEFAULT_BUDGET = int(os.getenv("FAC_DEFAULT_BUDGET_SHARED", "1000"))
MAX_BUDGET = int(os.getenv("FAC_MAX_BUDGET_SHARED", "20000"))

def _owner_anchored_namespace(owner_id: str, engine_id: str, recipient_id: str) -> str:
    """
    (English Hardcode) Owner-anchored namespace with per-recipient suffix:
    (English Hardcode) <owner_id>/<engine_id>/u:<recipient_id>
    (English Hardcode) Reason:
    (English Hardcode)  - Keeps billing/ownership under the owner's tree
    (English Hardcode)  - Segregates episodes per recipient (no mixing)
    """
    return f"{owner_id}/{engine_id}/u:{recipient_id}"

def build_fac_for_shared_engine(
    request_user: User,
    engine: RegisteredEngine
) -> Dict[str, Any]:
    """
    (English Hardcode) Build FAC for a user who received an EngineShare.
    (English Hardcode) Policy:
    (English Hardcode)  - Must have an active share record (is_active=True is assumed if share exists)
    (English Hardcode)  - Role 'runner' or 'admin' required to execute (reader is blocked)
    (English Hardcode)  - Capabilities kept minimal: 'agent.run' (engine-scoped)
    (English Hardcode)  - Episodic mount: recipient's mount RW (keeps their notes/kv)
    (English Hardcode)  - Namespace: owner-anchored + recipient suffix to separate episodes
    """

    share: EngineShare | None = (
        EngineShare.query
        .filter_by(engine_id=engine.id, user_id=request_user.id)
        .first()
    )

    if not share:
        raise PermissionError("No active share found for this engine")

    role = getattr(share, "role", "reader")

    if role not in ("runner", "admin"):
        raise PermissionError(f"Share role '{role}' does not permit running this engine")

    caps = [
        {
            "name": "agent.run",
            "scope": {"engine_id": str(engine.id)},
            "description": "Permit running the shared engine by ID"
        }
    ]

    namespace = _owner_anchored_namespace(
        owner_id=str(engine.user_id),
        engine_id=str(engine.id),
        recipient_id=str(request_user.id),
    )

    fac: Dict[str, Any] = {
        "agent_id": f"agent-shared-{request_user.id[:8]}",
        "version": "v1",
        "owner_id": str(engine.user_id),
        "engine_id": str(engine.id),
        "role": f"SharedEngineRunner",
        "capabilities": caps,
        "memory_mounts": [
            {
                "mount_type": "episodic",
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
