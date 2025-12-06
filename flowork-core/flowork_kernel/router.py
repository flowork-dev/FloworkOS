########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\router.py total lines 21 
########################################################################

from __future__ import annotations
from typing import List, Dict, Any, Optional
import random
import os

class StrategyRouter:

    def __init__(self, strategies: List[str], seed: Optional[int] = None):
        self.strategies = strategies or ["default"]
        self._rng = random.Random(seed or int(os.getenv("FLOWORK_ROUTER_SEED", "0") or "0"))

    def pick(self, context: Dict[str, Any]) -> str:
        if "force_strategy" in context:
            return context["force_strategy"]
        return self._rng.choice(self.strategies)
