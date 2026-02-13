########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_service\secure_list_directory.py total lines 36 
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

def run(hub, path, user_id):
    """[Logical Path] List directory without UI-specific '..' breadcrumbs."""
    try:
        (target, _) = hub.execute_sync('_resolve_and_secure_path', path, user_id)
        items = []
        if target.exists() and target.is_dir():
            for item in sorted(os.listdir(target)):
                if item.startswith('.'):
                    continue
                full_path = target / item
                items.append({'name': item, 'type': 'directory' if full_path.is_dir() else 'file', 'physical_path': str(full_path), 'path': str(full_path)})
        return {'status': 'success', 'items': items, 'current_path': str(target)}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
