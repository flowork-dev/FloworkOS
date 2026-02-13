########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\outcome.py total lines 36 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from __future__ import annotations
from typing import Dict, Any

class OutcomeMeter:

    def __init__(self):
        self.success = 0
        self.failure = 0
        self.total_cost = 0.0

    def record_success(self, cost: float = 0.0) -> None:
        self.success += 1
        self.total_cost += float(cost)

    def record_failure(self, cost: float = 0.0) -> None:
        self.failure += 1
        self.total_cost += float(cost)

    def summary(self) -> Dict[str, Any]:
        total = self.success + self.failure
        return {
            "success": self.success,
            "failure": self.failure,
            "total": total,
            "success_rate": (self.success / total) if total else 0.0,
            "total_cost": self.total_cost,
        }

    def to_timeline(self) -> Dict[str, Any]:
        return self.summary()
