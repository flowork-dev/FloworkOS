########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\_register_node_class.py total lines 37 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import importlib.util

def run(hub, node_id, app_id, source_file, entry_class_name, node_cfg=None, manifest=None):
    try:
        generic_mods = ['app_service', 'app_router', 'node_logic', 'node']
        for g_mod in generic_mods:
            if g_mod in sys.modules: del sys.modules[g_mod]

        node_dir = os.path.dirname(source_file)
        if node_dir not in sys.path: sys.path.insert(0, node_dir)

        unique_module_name = f'flowork_nodes.{app_id}.{node_id}'.replace('-', '_')
        spec = importlib.util.spec_from_file_location(unique_module_name, source_file)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[unique_module_name] = mod
            spec.loader.exec_module(mod)
            if hasattr(mod, entry_class_name):
                node_cls = getattr(mod, entry_class_name)
                hub.nodes_map[node_id] = node_cls
                if node_cfg and manifest:
                    hub.nodes_metadata.append({'id': node_id, 'name': node_cfg.get('name', node_id), 'app_id': app_id})
                hub.logger.info(f'✅ [Registered] Node: {node_id} | Class: {entry_class_name}')

                if node_dir in sys.path: sys.path.remove(node_dir)
                return node_cls
    except Exception as e:
        hub.logger.error(f'❌ Registration Failed for {node_id}: {e}')
    return None
