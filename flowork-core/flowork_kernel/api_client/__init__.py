########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\__init__.py total lines 157 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import requests
import json
import os
import threading
import time
import random
from flowork_kernel.kernel import Kernel


class ApiClient():
    def __init__(self, base_url='http://localhost:8989/api/v1', kernel=None):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        self.local_base_url = base_url
        self.kernel = kernel or Kernel.instance
        self._loc_cache = None
        self.cache = {}
        self.cache_lock = threading.Lock()

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def loc(self, *args, **kwargs):
        return self.execute_sync('loc', *args, **kwargs)
    def _get_variable(self, *args, **kwargs):
        return self.execute_sync('_get_variable', *args, **kwargs)
    def _get_local_auth_headers(self, *args, **kwargs):
        return self.execute_sync('_get_local_auth_headers', *args, **kwargs)
    def _handle_response(self, *args, **kwargs):
        return self.execute_sync('_handle_response', *args, **kwargs)
    def register_user(self, *args, **kwargs):
        return self.execute_sync('register_user', *args, **kwargs)
    def forgot_password(self, *args, **kwargs):
        return self.execute_sync('forgot_password', *args, **kwargs)
    def login_user(self, *args, **kwargs):
        return self.execute_sync('login_user', *args, **kwargs)
    def get_user_profile_by_token(self, *args, **kwargs):
        return self.execute_sync('get_user_profile_by_token', *args, **kwargs)
    def validate_license_activation(self, *args, **kwargs):
        return self.execute_sync('validate_license_activation', *args, **kwargs)
    def restart_application(self, *args, **kwargs):
        return self.execute_sync('restart_application', *args, **kwargs)
    def get_all_settings(self, *args, **kwargs):
        return self.execute_sync('get_all_settings', *args, **kwargs)
    def save_settings(self, *args, **kwargs):
        return self.execute_sync('save_settings', *args, **kwargs)
    def get_conversion_status(self, *args, **kwargs):
        return self.execute_sync('get_conversion_status', *args, **kwargs)
    def get_agents(self, *args, **kwargs):
        return self.execute_sync('get_agents', *args, **kwargs)
    def save_agent(self, *args, **kwargs):
        return self.execute_sync('save_agent', *args, **kwargs)
    def delete_agent(self, *args, **kwargs):
        return self.execute_sync('delete_agent', *args, **kwargs)
    def run_agent(self, *args, **kwargs):
        return self.execute_sync('run_agent', *args, **kwargs)
    def get_agent_run_status(self, *args, **kwargs):
        return self.execute_sync('get_agent_run_status', *args, **kwargs)
    def stop_agent_run(self, *args, **kwargs):
        return self.execute_sync('stop_agent_run', *args, **kwargs)
    def get_presets(self, *args, **kwargs):
        return self.execute_sync('get_presets', *args, **kwargs)
    def get_preset_data(self, *args, **kwargs):
        return self.execute_sync('get_preset_data', *args, **kwargs)
    def save_preset(self, *args, **kwargs):
        return self.execute_sync('save_preset', *args, **kwargs)
    def delete_preset(self, *args, **kwargs):
        return self.execute_sync('delete_preset', *args, **kwargs)
    def update_variable(self, *args, **kwargs):
        return self.execute_sync('update_variable', *args, **kwargs)
    def update_variable_state(self, *args, **kwargs):
        return self.execute_sync('update_variable_state', *args, **kwargs)
    def delete_variable(self, *args, **kwargs):
        return self.execute_sync('delete_variable', *args, **kwargs)
    def get_components(self, *args, **kwargs):
        return self.execute_sync('get_components', *args, **kwargs)
    def get_ai_provider_services(self, *args, **kwargs):
        return self.execute_sync('get_ai_provider_services', *args, **kwargs)
    def install_component(self, *args, **kwargs):
        return self.execute_sync('install_component', *args, **kwargs)
    def delete_component(self, *args, **kwargs):
        return self.execute_sync('delete_component', *args, **kwargs)
    def update_component_state(self, *args, **kwargs):
        return self.execute_sync('update_component_state', *args, **kwargs)
    def get_dashboard_layout(self, *args, **kwargs):
        return self.execute_sync('get_dashboard_layout', *args, **kwargs)
    def save_dashboard_layout(self, *args, **kwargs):
        return self.execute_sync('save_dashboard_layout', *args, **kwargs)
    def get_tab_session(self, *args, **kwargs):
        return self.execute_sync('get_tab_session', *args, **kwargs)
    def save_tab_session(self, *args, **kwargs):
        return self.execute_sync('save_tab_session', *args, **kwargs)
    def open_managed_tab(self, *args, **kwargs):
        return self.execute_sync('open_managed_tab', *args, **kwargs)
    def upload_component(self, *args, **kwargs):
        return self.execute_sync('upload_component', *args, **kwargs)
    def upload_model(self, *args, **kwargs):
        return self.execute_sync('upload_model', *args, **kwargs)
    def get_state(self, *args, **kwargs):
        return self.execute_sync('get_state', *args, **kwargs)
    def set_state(self, *args, **kwargs):
        return self.execute_sync('set_state', *args, **kwargs)
    def delete_state(self, *args, **kwargs):
        return self.execute_sync('delete_state', *args, **kwargs)
    def get_tab_preset(self, *args, **kwargs):
        return self.execute_sync('get_tab_preset', *args, **kwargs)
    def set_tab_preset(self, *args, **kwargs):
        return self.execute_sync('set_tab_preset', *args, **kwargs)
    def execute_raw_workflow(self, *args, **kwargs):
        return self.execute_sync('execute_raw_workflow', *args, **kwargs)
    def stop_workflow(self, *args, **kwargs):
        return self.execute_sync('stop_workflow', *args, **kwargs)
    def pause_workflow(self, *args, **kwargs):
        return self.execute_sync('pause_workflow', *args, **kwargs)
    def resume_workflow(self, *args, **kwargs):
        return self.execute_sync('resume_workflow', *args, **kwargs)
    def send_approval_response(self, *args, **kwargs):
        return self.execute_sync('send_approval_response', *args, **kwargs)
    def validate_node_config(self, *args, **kwargs):
        return self.execute_sync('validate_node_config', *args, **kwargs)
    def logout(self, *args, **kwargs):
        return self.execute_sync('logout', *args, **kwargs)
    def generate_workflow_from_prompt(self, *args, **kwargs):
        return self.execute_sync('generate_workflow_from_prompt', *args, **kwargs)
    def clear_system_cache(self, *args, **kwargs):
        return self.execute_sync('clear_system_cache', *args, **kwargs)
    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)
