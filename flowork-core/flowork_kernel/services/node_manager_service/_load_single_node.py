########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\_load_single_node.py total lines 43 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import importlib.util

def run(hub, app_root, node_cfg, manifest):
    try:
        node_id = node_cfg.get('id')
        rel_path = node_cfg.get('file')
        entry_class = node_cfg.get('entry_class')
        app_id = manifest.get('id')
        if not node_id or not rel_path or not entry_class: return

        bad_modules = ['app_service', 'app_router', 'node_logic', 'node']
        for mod in bad_modules:
            if mod in sys.modules:
                del sys.modules[mod]

        source_file = os.path.join(app_root, rel_path)
        if not os.path.exists(source_file):
            source_file = os.path.join(app_root, 'backend', rel_path)
            if not os.path.exists(source_file):
                hub.logger.warning(f'⚠️ Node file missing for {node_id}')
                return

        original_path = list(sys.path)
        app_backend = os.path.abspath(os.path.join(app_root, 'backend'))

        try:
            if app_backend not in sys.path:
                sys.path.insert(0, app_backend)

            hub.execute_sync('_register_node_class', node_id, app_id, source_file, entry_class, node_cfg, manifest)
        finally:
            sys.path = original_path

    except Exception as e:
        hub.logger.error(f"❌ Error loading node {node_cfg.get('id')}: {e}")
