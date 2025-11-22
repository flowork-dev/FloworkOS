########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\preset_manager_service\preset_manager_service.py total lines 137 
########################################################################

import os
import json
import shutil
import datetime
import threading
from ..base_service import BaseService
from flowork_kernel.exceptions import PresetNotFoundError
from flowork_kernel.utils.flowchain_verifier import verify_workflow_chain, calculate_hash
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.singleton import Singleton
import logging

class PresetManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)

        possible_paths = [
            "/app/data/users",                        # Docker
            r"C:\FLOWORK\data\users",                 # Windows Native
            os.path.join(self.kernel.data_path, "users") # Fallback
        ]

        self.users_data_path = next((p for p in possible_paths if os.path.exists(os.path.dirname(p))), possible_paths[1])

        os.makedirs(self.users_data_path, exist_ok=True)
        self._save_lock = threading.Lock()
        self.state_manager = self.kernel.get_service("state_manager_service")
        self.trigger_manager = None
        self.db_service = None

        self.logger.info(f"Preset Manager Storage: {self.users_data_path}")

    def start(self):
        self.trigger_manager = self.kernel.get_service("trigger_manager_service")
        self.db_service = Singleton.get_instance(DatabaseService)
        if not self.db_service:
            self.logger.critical("CRITICAL: DatabaseService missing.")
        os.makedirs(self.users_data_path, exist_ok=True)

    def _get_workflow_id(self, user_id: str, name: str) -> str:
        return f"{user_id or '_global'}::{name}"

    def _get_user_presets_path(self, user_id: str):
        target_user = user_id if user_id else "_global"
        path = os.path.join(self.users_data_path, target_user, "presets")
        if not os.path.exists(path): os.makedirs(path, exist_ok=True)
        return path

    def _get_preset_workflow_path(self, user_id: str, name: str):
        return os.path.join(self._get_user_presets_path(user_id), name)

    def _get_latest_version_file(self, workflow_path: str):
        if not os.path.isdir(workflow_path): return None, 0
        files = [f for f in os.listdir(workflow_path) if f.endswith('.json') and f.startswith('v')]
        if not files: return None, 0
        latest = max(files, key=lambda x: int(x.split('_')[0][1:]) if x.split('_')[0][1:].isdigit() else 0)
        version = int(latest.split('_')[0][1:]) if latest.split('_')[0][1:].isdigit() else 0
        return os.path.join(workflow_path, latest), version

    def _sync_trigger_rules_for_preset(self, preset_name, workflow_data, user_id, is_delete=False):
        if not self.state_manager or not self.trigger_manager: return
        all_rules = self.state_manager.get("trigger_rules", user_id=user_id, default={})
        for rid in [rid for rid, r in all_rules.items() if r.get("preset_to_run") == preset_name]:
            del all_rules[rid]
        if not is_delete and workflow_data:
            for node in [n for n in workflow_data.get("nodes", []) if n.get("manifest", {}).get("type") == "TRIGGER"]:
                rule_id = f"node::{node['id']}"
                all_rules[rule_id] = {
                    "name": f"Trigger {preset_name} ({node['name']})",
                    "trigger_id": node["module_id"],
                    "preset_to_run": preset_name,
                    "config": node.get("config_values", {}),
                    "is_enabled": True,
                    "__owner_user_id": user_id
                }
        self.state_manager.set("trigger_rules", all_rules, user_id=user_id)
        self.trigger_manager.start_all_listeners()

    def get_preset_list(self, user_id: str):
        path = self._get_user_presets_path(user_id)
        try:
            folders = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and not d.startswith("_")]
            return [{"name": name, "id": name} for name in sorted(folders)]
        except Exception as e:
            self.logger.error(f"List error: {e}")
            return []

    def get_preset_data(self, name: str, user_id: str):
        wf_path = self._get_preset_workflow_path(user_id, name)
        file_path, _ = self._get_latest_version_file(wf_path)
        if not file_path: return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f).get("workflow_data")
        except: return None

    def save_preset(self, name: str, workflow_data: dict, user_id: str, signature: str, public_address: str = None) -> bool:
        if not name or not user_id: return False
        wf_path = self._get_preset_workflow_path(user_id, name)
        os.makedirs(wf_path, exist_ok=True)

        with self._save_lock:
            _, last_ver = self._get_latest_version_file(wf_path)
            ver = last_ver + 1
            ts = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            fname = f"v{ver}_{ts}.json"

            payload = {
                "version": ver, "timestamp": ts, "author_id": public_address or user_id,
                "workflow_data": workflow_data, "signature": signature
            }

            with open(os.path.join(wf_path, fname), 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)

            self._sync_trigger_rules_for_preset(name, workflow_data, user_id)
            self.logger.info(f"Preset '{name}' saved (v{ver}).")
            return True

    def delete_preset(self, name: str, user_id: str) -> bool:
        wf_path = self._get_preset_workflow_path(user_id, name)
        if os.path.exists(wf_path):
            shutil.rmtree(wf_path)
            self._sync_trigger_rules_for_preset(name, None, user_id, is_delete=True)
            return True
        return False

    def get_preset_versions(self, name, user_id): return []
    def load_preset_version(self, name, ver, user_id): return None
    def delete_preset_version(self, name, ver, user_id): return False
