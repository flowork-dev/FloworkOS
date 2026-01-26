########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\gremlin.py total lines 21 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from __future__ import annotations
import os
import random

def maybe_chaos_inject(stage: str) -> None:

    if os.getenv("FLOWORK_CHAOS_MODE", "0") != "1":
        return

    p = float(os.getenv("FLOWORK_CHAOS_P", "0.10"))
    roll = random.random()
    if roll < p * 0.5:
        raise TimeoutError(f"[Gremlin] Simulated timeout at {stage}")
    if roll < p:
        raise ValueError(f"[Gremlin] Corrupted input at {stage}")
