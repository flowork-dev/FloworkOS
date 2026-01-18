########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\start.py total lines 20 
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


def run(hub):
    hub.logger.info('🧠 [NodeManager] Syncing Neural Nodes & Logic Modules...')
    hub.execute_sync('scan_nodes')
    hub.logger.info(f'✅ [NodeManager] Registered {len(hub.nodes_map)} Active Nodes.')
