########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\gremlin.py total lines 25 
########################################################################

from __future__ import annotations
import os
import random

def maybe_chaos_inject(stage: str) -> None:
    """
    (R5) Activate by setting FLOWORK_CHAOS_MODE=1 (dev/test only).
    Optional knobs:
     - FLOWORK_CHAOS_P (0..1) : overall probability weight (default 0.10)
    """
    if os.getenv("FLOWORK_CHAOS_MODE", "0") != "1":
        return

    p = float(os.getenv("FLOWORK_CHAOS_P", "0.10"))
    roll = random.random()
    if roll < p * 0.5:
        raise TimeoutError(f"[Gremlin] Simulated timeout at {stage}")
    if roll < p:
        raise ValueError(f"[Gremlin] Corrupted input at {stage}")
