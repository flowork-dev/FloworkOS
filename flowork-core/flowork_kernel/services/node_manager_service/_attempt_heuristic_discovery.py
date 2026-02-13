########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\_attempt_heuristic_discovery.py total lines 54 
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
        [ZERO MAINTENANCE] Mode Detektif:
        Mencari class node secara brute-force di folder app jika manifest.json berantakan.
        """
    target_app_path = os.path.join(hub.base_apps_path, node_id)
    if not os.path.exists(target_app_path):
        for d in os.listdir(hub.base_apps_path):
            if d.lower() == node_id.lower():
                target_app_path = os.path.join(hub.base_apps_path, d)
                break
    if not os.path.exists(target_app_path):
        hub.logger.error(f'🕵️\u200d♂️ Directory not found for heuristic search: {target_app_path}')
        return None
    candidates = ['node.py', 'app_node.py', 'main.py', os.path.join('backend', 'node.py'), os.path.join('backend', 'app_node.py'), f'{node_id}.py']
    for cand in candidates:
        file_path = os.path.join(target_app_path, cand)
        if os.path.exists(file_path):
            hub.logger.info(f'🕵️\u200d♂️ Found potential node file: {file_path}')
            try:
                unique_name = f"flowork_adhoc.{node_id}_{cand.replace('/', '_').replace('.', '_')}"
                spec = importlib.util.spec_from_file_location(unique_name, file_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[unique_name] = mod
                    spec.loader.exec_module(mod)
                    for (name, obj) in inspect.getmembers(mod):
                        if inspect.isclass(obj) and obj.__module__ == unique_name:
                            has_run = hasattr(obj, 'run') and callable(getattr(obj, 'run'))
                            has_execute = hasattr(obj, 'execute') and callable(getattr(obj, 'execute'))
                            if has_run or has_execute:
                                hub.logger.info(f'🎯 BINGO! Found compatible Node Class: {name}')
                                hub.nodes_map[node_id] = obj
                                return obj
            except Exception as e:
                hub.logger.warning(f'🕵️\u200d♂️ Failed inspection on {cand}: {e}')
    hub.logger.error(f"🕵️\u200d♂️ Heuristic search failed. No valid Node class found for '{node_id}'")
    return None
