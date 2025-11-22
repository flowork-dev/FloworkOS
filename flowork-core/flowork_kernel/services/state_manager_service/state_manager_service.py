########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\state_manager_service\state_manager_service.py total lines 190 
########################################################################

import os
import json
import shutil
import threading
from collections import OrderedDict
from ..base_service import BaseService

class StateManagerService(BaseService):

    GLOBAL_STATE_FILENAME = "state.json"
    USER_STATE_FILENAME = "state.json"
    MAX_USER_CACHE_SIZE = 100

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.users_data_path = os.path.join(self.kernel.data_path, "users")
        self.global_state_file_path = os.path.join(
            self.kernel.data_path, self.GLOBAL_STATE_FILENAME
        )
        os.makedirs(self.users_data_path, exist_ok=True)
        self._global_state_cache = {}
        self._user_state_cache = OrderedDict()
        self._lock = threading.Lock()
        self.kernel.write_to_log(
            "Service 'StateManager' (Hybrid Multi-Tenant) initialized.", "DEBUG"
        )
        self._load_global_state()

    def _atomic_write(self, filepath, data):
        """
        Writes data atomically to prevent corruption on crash.
        """
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_path, filepath) # Atomic on POSIX and Windows
        except Exception as e:
            self.kernel.write_to_log(
                f"StateManager: ATOMIC WRITE FAILED for {filepath}: {e}", "ERROR"
            )
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _load_global_state(self):
        try:
            if os.path.exists(self.global_state_file_path):
                with open(self.global_state_file_path, "r", encoding="utf-8") as f:
                    self._global_state_cache = json.load(f)
                self.kernel.write_to_log(
                    f"StateManager: Global state loaded successfully.", "INFO"
                )
            else:
                self._global_state_cache = {}
        except (IOError, json.JSONDecodeError) as e:
            self.kernel.write_to_log(
                f"StateManager: Failed to load global state: {e}. Resetting to empty.",
                "ERROR",
            )
            if os.path.exists(self.global_state_file_path):
                try:
                    shutil.copy(self.global_state_file_path, self.global_state_file_path + ".corrupt")
                except: pass
            self._global_state_cache = {}

    def _save_global_state(self):
        self._atomic_write(self.global_state_file_path, self._global_state_cache)

    def _get_user_state_path(self, user_id: str):
        user_dir = os.path.join(self.users_data_path, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, self.USER_STATE_FILENAME)

    def _load_user_state_from_file(self, user_id: str):
        state_file_path = self._get_user_state_path(user_id)
        try:
            if os.path.exists(state_file_path):
                with open(state_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except (IOError, json.JSONDecodeError) as e:
            self.kernel.write_to_log(f"StateManager: Corrupt user state for {user_id}: {e}", "ERROR")
            return {}

    def _save_user_state_to_file(self, user_id: str, state_data: dict):
        state_file_path = self._get_user_state_path(user_id)
        self._atomic_write(state_file_path, state_data)

    def get(self, key, user_id: str = None, default=None):
        with self._lock:
            if user_id:
                if user_id not in self._user_state_cache:
                    self._user_state_cache[user_id] = self._load_user_state_from_file(
                        user_id
                    )
                    if len(self._user_state_cache) > self.MAX_USER_CACHE_SIZE:
                        self._user_state_cache.popitem(
                            last=False
                        )
                self._user_state_cache.move_to_end(
                    user_id
                )
                return self._user_state_cache[user_id].get(key, default)
            else:
                return self._global_state_cache.get(key, default)

    def get_all(self, user_id: str = None):
        """
        Retrieves the entire state dictionary (clone) for a user or global.
        """
        with self._lock:
            if user_id:
                if user_id not in self._user_state_cache:
                    self._user_state_cache[user_id] = self._load_user_state_from_file(
                        user_id
                    )
                return self._user_state_cache[user_id].copy()
            else:
                return self._global_state_cache.copy()

    def set(self, key, value, user_id: str = None):
        with self._lock:
            if user_id:
                if user_id not in self._user_state_cache:
                    self._user_state_cache[user_id] = self._load_user_state_from_file(
                        user_id
                    )
                self._user_state_cache[user_id][key] = value
                self._user_state_cache.move_to_end(user_id)
                self._save_user_state_to_file(user_id, self._user_state_cache[user_id])
                self.kernel.write_to_log(
                    f"StateManager: State for key '{key}' for user '{user_id}' has been set.",
                    "DEBUG",
                )
            else:
                self._global_state_cache[key] = value
                self._save_global_state()
                self.kernel.write_to_log(
                    f"StateManager: Global state for key '{key}' has been set.", "DEBUG"
                )

    def update_all(self, data: dict, user_id: str = None):
        """
        Updates multiple keys at once.
        """
        with self._lock:
            if user_id:
                if user_id not in self._user_state_cache:
                    self._user_state_cache[user_id] = self._load_user_state_from_file(
                        user_id
                    )
                self._user_state_cache[user_id].update(data)
                self._save_user_state_to_file(user_id, self._user_state_cache[user_id])
            else:
                self._global_state_cache.update(data)
                self._save_global_state()

    def delete(self, key, user_id: str = None):
        with self._lock:
            if user_id:
                if user_id not in self._user_state_cache:
                    self._user_state_cache[user_id] = self._load_user_state_from_file(
                        user_id
                    )
                if key in self._user_state_cache[user_id]:
                    del self._user_state_cache[user_id][key]
                    self._save_user_state_to_file(
                        user_id, self._user_state_cache[user_id]
                    )
                    self.kernel.write_to_log(
                        f"StateManager: State for key '{key}' for user '{user_id}' has been deleted.",
                        "DEBUG",
                    )
            else:
                if key in self._global_state_cache:
                    del self._global_state_cache[key]
                    self._save_global_state()
                    self.kernel.write_to_log(
                        f"StateManager: Global state for key '{key}' has been deleted.",
                        "DEBUG",
                    )
