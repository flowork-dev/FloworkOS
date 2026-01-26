########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_service\start.py total lines 29 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import os
import shutil
import time
import traceback
import threading
from enum import Enum
from pathlib import Path


class RecoveryTier(Enum):
    TIER_1_SELF_HEAL = 1
    TIER_2_SOFT_RESTART = 2
    TIER_3_HARD_RESTART = 3
    TIER_4_KERNEL_PANIC = 4

def run(hub):
    """Jantung Utama: Menjalankan run_logic dalam perlindungan Try/Catch Abadi."""
    hub.is_running = True
    hub.logger.info(f'🚀 {hub.service_id} STARTED with Immortal Matrix.')
    if hub.__class__.run_logic == BaseService.run_logic:
        return
    threading.Thread(target=hub._immortal_loop, daemon=True, name=f'{hub.service_id}_Loop').start()
