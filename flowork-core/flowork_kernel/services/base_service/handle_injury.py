########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_service\handle_injury.py total lines 60 
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

def run(hub, error):
    """
        🏥 RUANG UGD (Triage): Menentukan tingkat keparahan luka service.
        """
    hub.retry_count += 1
    error_msg = str(error)
    stack_trace = traceback.format_exc()
    hub.logger.error(f'⚠️ {hub.service_id} INJURED (Strike {hub.retry_count}): {error_msg}')
    tier = RecoveryTier.TIER_1_SELF_HEAL
    if 'MemoryError' in error_msg or 'BrokenPipe' in error_msg:
        tier = RecoveryTier.TIER_3_HARD_RESTART
    elif 'SystemExit' in error_msg:
        tier = RecoveryTier.TIER_4_KERNEL_PANIC
    if hub.retry_count > hub.max_retries:
        hub.logger.warning(f'🔄 {hub.service_id} Exhausted retries. Escalating to Tier 2.')
        tier = RecoveryTier.TIER_2_SOFT_RESTART
    if tier == RecoveryTier.TIER_1_SELF_HEAL:
        time.sleep(2)
        hub.logger.info(f'🩹 {hub.service_id} Self-healing...')
    elif tier == RecoveryTier.TIER_2_SOFT_RESTART:
        hub.execute_sync('cleanup_resources')
        time.sleep(5)
        hub.retry_count = 0
        hub.logger.info(f'🧘 {hub.service_id} Soft Restart completed.')
    elif tier == RecoveryTier.TIER_3_HARD_RESTART:
        if hub.doctor:
            hub.logger.critical(f'🚑 {hub.service_id} Requesting HARD RESTART from Vitality!')
            hub.doctor.report_critical_failure(hub.service_id, stack_trace)
            hub.is_running = False
        else:
            hub.logger.critical(f'💀 {hub.service_id} Died without a Doctor. Process terminating.')
            exit(1)
    elif tier == RecoveryTier.TIER_4_KERNEL_PANIC:
        hub.logger.critical('🔥 KERNEL PANIC! SYSTEM MELTDOWN!')
        if hub.doctor:
            hub.doctor.trigger_system_reboot()
        else:
            exit(1)
