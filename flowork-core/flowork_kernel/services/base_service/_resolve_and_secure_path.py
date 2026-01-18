########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_service\_resolve_and_secure_path.py total lines 58 
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

def run(hub, relative_path, user_id):
    """
        [Node-Path Logic]
        Resolves physical paths for workflow execution.
        Strictly prevents escaping user jail during logic operations.
        """
    from flowork_kernel.utils.path_helper import get_data_directory
    data_dir = get_data_directory()
    user_jail = Path(os.path.abspath(data_dir / 'users' / str(user_id)))
    if not user_jail.exists():
        user_jail.mkdir(parents=True, exist_ok=True)
    path_str = str(relative_path or '').strip()
    if path_str in ['', '.', '/', '\\', 'ROOT', 'default']:
        return (user_jail, user_jail)
    virtual_prefix = '/app/data'
    target_path = None
    normalized_str = path_str.replace('\\', '/')
    if normalized_str.startswith(virtual_prefix):
        relative_part = normalized_str[len(virtual_prefix):].lstrip('/')
        possible_target = Path(os.path.abspath(data_dir / relative_part))
        if str(possible_target).startswith(str(user_jail)):
            target_path = possible_target
    if not target_path:
        try:
            possible_abs = Path(os.path.abspath(path_str))
            if str(possible_abs).startswith(str(user_jail)):
                target_path = possible_abs
        except:
            pass
    if not target_path:
        clean_rel = path_str.lstrip('/\\')
        target_path = Path(os.path.abspath(user_jail / clean_rel))
    if not str(target_path).startswith(str(user_jail)):
        hub.logger.warning(f'🚨 [Security] Node Path Escape Attempt by {user_id}. Target: {target_path}')
        raise PermissionError('Security: Path Escape Attempt Detected')
    return (target_path, user_jail)
