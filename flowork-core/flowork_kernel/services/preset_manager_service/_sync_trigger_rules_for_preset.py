########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\_sync_trigger_rules_for_preset.py total lines 31 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import shutil
import datetime
import threading
from flowork_kernel.exceptions import PresetNotFoundError
from flowork_kernel.utils.flowchain_verifier import verify_workflow_chain, calculate_hash
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.singleton import Singleton
import logging


def run(hub, preset_name, workflow_data, user_id, is_delete=False):
    if not hub.state_manager or not hub.trigger_manager:
        return
    all_rules = hub.state_manager.get('trigger_rules', user_id=user_id, default={})
    for rid in [rid for (rid, r) in all_rules.items() if r.get('preset_to_run') == preset_name]:
        del all_rules[rid]
    if not is_delete and workflow_data:
        for node in [n for n in workflow_data.get('nodes', []) if n.get('manifest', {}).get('type') == 'TRIGGER']:
            rule_id = f"node::{node['id']}"
            all_rules[rule_id] = {'name': f"Trigger {preset_name} ({node['name']})", 'trigger_id': node['module_id'], 'preset_to_run': preset_name, 'config': node.get('config_values', {}), 'is_enabled': True, '__owner_user_id': user_id}
    hub.state_manager.set('trigger_rules', all_rules, user_id=user_id)
    if hasattr(hub.trigger_manager, 'start_all_listeners'):
        hub.trigger_manager.start_all_listeners()
