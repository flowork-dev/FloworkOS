########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\get_node_instance.py total lines 39 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import importlib.util
import sys
import logging
import inspect
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.utils.path_helper import get_apps_directory


def run(hub, node_id):
    """
        [CRITICAL UPGRADE] Mengambil Instance Node dengan Dependency Injection (Kernel).
        Ini wajib agar Node bisa memanggil 'app_runtime' (Muscle).
        """
    node_cls = hub.execute_sync('get_node_class', node_id)
    if not node_cls:
        hub.logger.warning(f"🕵️\u200d♂️ Node '{node_id}' not in registry. Attempting Heuristic Discovery...")
        node_cls = hub.execute_sync('_attempt_heuristic_discovery', node_id)
    if node_cls:
        try:
            hub.logger.info(f"🧬 Instantiating Node '{node_id}' with Kernel injection...")
            try:
                return node_cls(node_id=node_id, properties={}, kernel=hub.kernel)
            except TypeError:
                hub.logger.warning(f"⚠️ Node '{node_id}' rejected arguments (Legacy Node?). Trying empty init.")
                return node_cls()
        except Exception as e:
            hub.logger.error(f"❌ FATAL: Failed to instantiate node '{node_id}'. Error: {e}")
            return None
    else:
        hub.logger.error(f"❌ Node ID '{node_id}' ABSOLUTELY NOT FOUND anywhere.")
        return None
