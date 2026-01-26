########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\router.py total lines 21 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
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
