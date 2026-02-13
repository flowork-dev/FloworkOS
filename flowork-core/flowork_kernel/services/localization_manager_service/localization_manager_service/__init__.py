########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\localization_manager_service\localization_manager_service\__init__.py total lines 175 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.base_service import BaseService
import importlib
import os
import logging
import asyncio
import os
import json
from collections import OrderedDict


class LocalizationManagerService(BaseService):
    SETTINGS_FILE = 'settings.json'
    MAX_USER_SETTINGS_CACHE = 50
    def get_available_languages_display(self):
        return [self.language_map[lang_code] for lang_code in self.languages.keys() if lang_code in self.language_map]
    def get_current_language_code(self):
        return self.current_lang
    def load_base_languages(self):
        self.kernel.write_to_log('LocalizationManager: Loading base languages from flowork-core/locales...', 'DEBUG')
        self._merge_from_directory(self.locales_path)
    def load_all_languages(self):
        self.kernel.write_to_log('LocalizationManager: Starting full language scan and merge...', 'INFO')
        self.languages.clear()
        self.load_base_languages()
        app_service = self.kernel.get_service('app_service', is_system_call=True)
        component_managers = {'modules': app_service, 'plugins': app_service, 'widgets': app_service, 'triggers': app_service, 'tools': app_service, 'ai_providers': self.kernel.get_service('ai_provider_manager_service', is_system_call=True)}
        for (manager_name, manager) in component_managers.items():
            if manager and hasattr(manager, f'loaded_{manager_name}'):
                items_to_scan = getattr(manager, f'loaded_{manager_name}', {})
                for (item_id, item_data) in items_to_scan.items():
                    if isinstance(item_data, dict) and item_data.get('path'):
                        component_locales_path = os.path.join(item_data['path'], 'locales')
                        self._merge_from_directory(component_locales_path, source_name=item_id)
        self.kernel.write_to_log('LocalizationManager: Language merge complete.', 'SUCCESS')
    def _merge_from_directory(self, directory_path, source_name='base'):
        if os.path.isdir(directory_path):
            for filename in os.listdir(directory_path):
                if filename.endswith('.json'):
                    lang_id = os.path.splitext(filename)[0]
                    filepath = os.path.join(directory_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lang_data = json.load(f)
                            if lang_id not in self.languages:
                                self.languages[lang_id] = {}
                            for (key, value) in lang_data.items():
                                if key in self.languages[lang_id] and source_name != 'base':
                                    self.logger(f"Duplicate locale key '{key}' found from '{source_name}'. Overwriting.", 'WARN')
                                self.languages[lang_id][key] = value
                    except Exception as e:
                        self.kernel.write_to_log(f"Failed to merge language '{lang_id}' from '{source_name}' at {filepath}: {e}", 'ERROR')
    def set_language(self, lang_id, user_id=None):
        if lang_id in self.languages:
            self.current_lang = lang_id
            self.save_setting('language', lang_id, user_id=user_id)
            self.kernel.write_to_log(f"LocalizationManager: Language for user '{user_id}' set to '{lang_id}'.", 'INFO')
            return True
        self.kernel.write_to_log(f"LocalizationManager: Language '{lang_id}' not found.", 'WARN')
        return False
    def get(self, key, fallback=None, **kwargs):
        stripped_key = key.strip()
        if stripped_key.startswith('loc.'):
            stripped_key = stripped_key[4:]
        lang_data = self.languages.get(self.current_lang)
        if lang_data and stripped_key in lang_data:
            text = lang_data[stripped_key]
            return text.format(**kwargs) if kwargs else text
        lang_data_en = self.languages.get('en')
        if lang_data_en and stripped_key in lang_data_en:
            return lang_data_en[stripped_key].format(**kwargs) if kwargs else lang_data_en[stripped_key]
        if fallback is not None:
            if isinstance(fallback, str):
                return fallback.format(**kwargs) if kwargs else fallback
            return fallback
        return f'[{key}]'
    def _get_user_settings_path(self, user_id: str):
        if not user_id:
            return os.path.join(self.kernel.data_path, self.SETTINGS_FILE)
        user_dir = os.path.join(self.users_data_path, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, self.SETTINGS_FILE)
    def _load_settings_from_file(self, user_id):
        settings_file_path = self._get_user_settings_path(user_id)
        try:
            current_settings = {}
            if os.path.exists(settings_file_path):
                with open(settings_file_path, 'r', encoding='utf-8') as f:
                    current_settings = json.load(f)
            default_webhook_port = int(os.getenv('CORE_API_PORT', 8989))
            defaults = {'active_template': 'default', 'language': 'en', 'ai_gpu_layers': -1, 'ai_worker_timeout_seconds': 600, 'webhook_enabled': True, 'webhook_port': default_webhook_port, 'global_error_handler_enabled': False, 'global_error_workflow_preset': '', 'last_run_time': None, 'notifications_enabled': True, 'notifications_duration_seconds': 5, 'notifications_position': 'bottom_right'}
            settings_changed = False
            for (key, value) in defaults.items():
                if key not in current_settings:
                    current_settings[key] = value
                    settings_changed = True
            if settings_changed:
                self._save_settings(current_settings, user_id)
            return current_settings
        except Exception as e:
            self.kernel.write_to_log(f"LocalizationManager: Failed to load settings for user '{user_id}': {e}", 'ERROR')
            return {}
    def _save_settings(self, settings_to_save, user_id=None):
        settings_file_path = self._get_user_settings_path(user_id)
        try:
            with open(settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=4)
            if user_id in self._settings_cache:
                self._settings_cache[user_id] = settings_to_save
        except Exception as e:
            self.kernel.write_to_log(f"LocalizationManager: Failed to save settings for user '{user_id}': {e}", 'ERROR')
    def save_setting(self, key, value, user_id=None):
        current_settings = self.get_all_settings(user_id=user_id)
        current_settings[key] = value
        self._save_settings(current_settings, user_id=user_id)
    def get_setting(self, key, default=None, user_id=None):
        user_settings = self.get_all_settings(user_id=user_id)
        return user_settings.get(key, default)
    def get_all_settings(self, user_id=None):
        if user_id in self._settings_cache:
            self._settings_cache.move_to_end(user_id)
            return self._settings_cache[user_id]
        settings_data = self._load_settings_from_file(user_id)
        self._settings_cache[user_id] = settings_data
        if len(self._settings_cache) > self.MAX_USER_SETTINGS_CACHE:
            self._settings_cache.popitem(last=False)
        lang_to_set = settings_data.get('language', 'en')
        if lang_to_set in self.languages:
            self.current_lang = lang_to_set
        return settings_data

    def __init__(self, kernel, service_id: str):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.locales_path = self.kernel.locales_path
        self.users_data_path = os.path.join(self.kernel.data_path, 'users')
        self.languages = {}
        self.current_lang = 'en'
        self._settings_cache = OrderedDict()
        self.language_map = {'en': 'English', 'id': 'Bahasa Indonesia'}
        os.makedirs(self.locales_path, exist_ok=True)
        os.makedirs(self.users_data_path, exist_ok=True)
        self.kernel.write_to_log("Service 'LocalizationManager' (Multi-Tenant) initialized.", 'DEBUG')
        self.load_base_languages()

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

    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)
