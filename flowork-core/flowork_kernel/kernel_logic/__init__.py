########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\__init__.py total lines 222 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
import os
import sys
import json
import time
import logging
import threading
import queue
import importlib
import datetime
import asyncio
from typing import List, Dict, Any, Callable
import requests
from packaging import version
from flowork_kernel.exceptions import PermissionDeniedError


class Kernel(Formatter):
    instance = None
    APP_VERSION = '1.0.0'
    license_tier: str = 'architect'
    is_premium: bool = True
    DEV_MODE_PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAysqZG2+F82W0TgLHmF3Y\n0GRPEZvXvmndTY84N/wA1ljt+JxMBVsmcVTkv8f1TrmFRD19IDzl2Yzb2lgqEbEy\nGFxHhudC28leDsVEIp8B+oYWVm8Mh242YKYK8r5DAvr9CPQivnIjZ4BWgKKddMTd\nharVxLF2CoSoTs00xWKd6VlXfoW9wdBvoDVifL+hCMepgLLdQQE4HbamPDJ3bpra\npCgcAD5urmVoJEUJdjd+Iic27RBK7jD1dWDO2MASMh/0IyXyM8i7RDymQ88gZier\nU0OdWzeCWGyl4EquvR8lj5GNz4vg2f+oEY7h9AIC1f4ARtoihc+apSntqz7nAqa/\nsQIDAQAB\n-----END PUBLIC KEY-----'
    TIER_HIERARCHY = {'free': 0, 'builder': 1, 'creator': 2, 'architect': 3, 'enterprise': 4}
    MODULE_CAPABILITY_MAP = {'stable_diffusion_xl_module': 'ai_local_models', 'agent_host': 'ai_architect', 'core_compiler_module': 'core_compiler', 'function_runner_module': 'ai_architect', 'Dynamic Media Stitcher': 'video_processing', 'video_storyboard_stitcher_d5e6': 'video_processing'}
    class FileSystemProxy:
    
        def __init__(self, kernel):
            self.kernel = kernel
            self.os_module = os
            self.shutil_module = __import__('shutil')
    
        def _check_permission(self, caller_module_id: str, required_permission: str):
            permission_manager = self.kernel.get_service('permission_manager_service', is_system_call=True)
            if permission_manager:
                if not permission_manager.check_permission(required_permission):
                    raise PermissionDeniedError(f"Module '{caller_module_id}' does not have the required permission: '{required_permission}'")
    
        def read(self, file_path, mode='r', encoding='utf-8', caller_module_id: str=None):
            self._check_permission(caller_module_id, 'file_system:read')
            with open(file_path, mode, encoding=encoding) as f:
                return f.read()
    
        def write(self, file_path, data, mode='w', encoding='utf-8', caller_module_id: str=None):
            self._check_permission(caller_module_id, 'file_system:write')
            with open(file_path, mode, encoding=encoding) as f:
                f.write(data)
    
        def exists(self, path, caller_module_id: str=None):
            self._check_permission(caller_module_id, 'file_system:read')
            return self.os_module.path.exists(path)
    
        def remove(self, path, caller_module_id: str=None):
            self._check_permission(caller_module_id, 'file_system:write')
            return self.os_module.remove(path)
    
        def rmtree(self, path, caller_module_id: str=None):
            self._check_permission(caller_module_id, 'file_system:write')
            return self.shutil_module.rmtree(path)
    class NetworkProxy:
    
        def __init__(self, kernel):
            self.kernel = kernel
            self.requests_module = requests
    
        def _check_permission(self, caller_module_id: str, required_permission: str):
            permission_manager = self.kernel.get_service('permission_manager_service', is_system_call=True)
            if permission_manager:
                if not permission_manager.check_permission(required_permission):
                    raise PermissionDeniedError(f"Module '{caller_module_id}' does not have the required permission: '{required_permission}'")
    
        def get(self, url, caller_module_id: str=None, **kwargs):
            self._check_permission(caller_module_id, 'network:get')
            return self.requests_module.get(url, **kwargs)
    
        def post(self, url, caller_module_id: str=None, **kwargs):
            self._check_permission(caller_module_id, 'network:post')
            return self.requests_module.post(url, **kwargs)

    def __init__(self, project_root_path: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        Kernel.instance = self
        self.project_root_path = project_root_path
        self.base_path = project_root_path
        self.is_dev_mode = self._validate_dev_mode()
        self._log_dev_mode_on_init = self.is_dev_mode
        self.services: Dict[str, Any] = {}
        self.startup_complete = False
        self.current_user = None
        self.globally_disabled_components = set()
        self.app_path = os.getenv('FLOWORK_APP_PATH', os.path.join(self.project_root_path, 'app'))
        if not os.path.exists(self.app_path) and os.path.exists('/app/app'):
            self.app_path = '/app/app'
        external_data_path = os.getenv('FLOWORK_DATA_PATH')
        if external_data_path and os.path.isdir(external_data_path):
            self.data_path = external_data_path
            self.modules_path = os.path.join(self.data_path, 'modules')
            self.plugins_path = os.path.join(self.data_path, 'plugins')
            self.widgets_path = os.path.join(self.data_path, 'widgets')
            self.triggers_path = os.path.join(self.data_path, 'triggers')
            self.ai_providers_path = os.path.join(self.data_path, 'ai_providers')
            self.formatters_path = os.path.join(self.data_path, 'formatters')
            self.tools_path = os.path.join(self.data_path, 'tools')
            self.logs_path = os.path.join(self.project_root_path, 'logs')
            self.system_plugins_path = os.path.join(self.project_root_path, 'system_plugins')
            self.themes_path = os.path.join(self.project_root_path, 'themes')
            self.locales_path = os.path.join(self.project_root_path, 'locales')
        else:
            if external_data_path:
                print(f"[KERNEL WARNING] FLOWORK_DATA_PATH set to '{external_data_path}' but it's not a valid directory. Falling back to internal paths.")
            else:
                print('[KERNEL INFO] FLOWORK_DATA_PATH not set. Using internal paths.')
            self.data_path = os.path.join(self.project_root_path, 'data')
            self.logs_path = os.path.join(self.project_root_path, 'logs')
            self.modules_path = os.path.join(self.project_root_path, 'modules')
            self.plugins_path = os.path.join(self.project_root_path, 'plugins')
            self.system_plugins_path = os.path.join(self.project_root_path, 'system_plugins')
            self.widgets_path = os.path.join(self.project_root_path, 'widgets')
            self.themes_path = os.path.join(self.project_root_path, 'themes')
            self.triggers_path = os.path.join(self.project_root_path, 'triggers')
            self.locales_path = os.path.join(self.project_root_path, 'locales')
            self.ai_providers_path = os.path.join(self.project_root_path, 'ai_providers')
            self.formatters_path = os.path.join(self.project_root_path, 'formatters')
            self.tools_path = os.path.join(self.project_root_path, 'tools')
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(self.logs_path, exist_ok=True)
        prot_path = os.path.join(self.data_path, 'protected_components.txt')
        if not os.path.exists(prot_path):
            try:
                with open(prot_path, 'w', encoding='utf-8') as f:
                    f.write('# Flowork Protected Components List\n')
            except:
                pass
        self.log_queue = queue.Queue()
        self.cmd_log_queue = queue.Queue()
        self.file_system = self.FileSystemProxy(self)
        self.network = self.NetworkProxy(self)
        self.json_logger = None
        self.dashboard_socketio = None
        self._setup_file_logger()
        if self._log_dev_mode_on_init:
            self.write_to_log('Kernel booted in secure DEVELOPMENT MODE.', 'WARN')
        self._load_services_from_manifest()

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

    def set_globally_disabled_components(self, *args, **kwargs):
        return self.execute_sync('set_globally_disabled_components', *args, **kwargs)
    async def restart_application(self, *args, **kwargs):
        return await self.execute_async('restart_application', *args, **kwargs)
    async def shutdown_application(self, *args, **kwargs):
        return await self.execute_async('shutdown_application', *args, **kwargs)
    def _validate_dev_mode(self, *args, **kwargs):
        return self.execute_sync('_validate_dev_mode', *args, **kwargs)
    def get_component_instance(self, *args, **kwargs):
        return self.execute_sync('get_component_instance', *args, **kwargs)
    def loc(self, *args, **kwargs):
        return self.execute_sync('loc', *args, **kwargs)
    def event_bus(self, *args, **kwargs):
        return self.execute_sync('event_bus', *args, **kwargs)
    def _log_queue_worker(self, *args, **kwargs):
        return self.execute_sync('_log_queue_worker', *args, **kwargs)
    def _load_services_from_manifest(self, *args, **kwargs):
        return self.execute_sync('_load_services_from_manifest', *args, **kwargs)
    def _load_service(self, *args, **kwargs):
        return self.execute_sync('_load_service', *args, **kwargs)
    def get_service(self, *args, **kwargs):
        return self.execute_sync('get_service', *args, **kwargs)
    async def start_all_services(self, *args, **kwargs):
        return await self.execute_async('start_all_services', *args, **kwargs)
    def hot_reload_components(self, *args, **kwargs):
        return self.execute_sync('hot_reload_components', *args, **kwargs)
    async def stop_all_services(self, *args, **kwargs):
        return await self.execute_async('stop_all_services', *args, **kwargs)
    def is_premium_user(self, *args, **kwargs):
        return self.execute_sync('is_premium_user', *args, **kwargs)
    def is_monetization_active(self, *args, **kwargs):
        return self.execute_sync('is_monetization_active', *args, **kwargs)
    def is_tier_sufficient(self, *args, **kwargs):
        return self.execute_sync('is_tier_sufficient', *args, **kwargs)
    def activate_license_online(self, *args, **kwargs):
        return self.execute_sync('activate_license_online', *args, **kwargs)
    def deactivate_license_on_server(self, *args, **kwargs):
        return self.execute_sync('deactivate_license_on_server', *args, **kwargs)
    def _setup_file_logger(self, *args, **kwargs):
        return self.execute_sync('_setup_file_logger', *args, **kwargs)
    def write_to_log(self, *args, **kwargs):
        return self.execute_sync('write_to_log', *args, **kwargs)
    def request_manual_approval(self, *args, **kwargs):
        return self.execute_sync('request_manual_approval', *args, **kwargs)
    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)
