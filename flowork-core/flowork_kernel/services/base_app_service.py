########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_app_service.py total lines 73 
########################################################################

import os
import shutil
from pathlib import Path
from .base_service import BaseService

class BaseAppService(BaseService):
    """
    THE APP FACE BASE
    Specifically handles Virtual Path mapping for the Dashboard.
    Ensures 'delete_item' and 'create_folder' return Virtual Paths.

    [INHERITANCE NOTE]
    This class automatically inherits:
    - Immortality Matrix (Recovery Tiers) from BaseService.
    - Security Jail Logic from BaseService.
    """

    def _to_virtual_path(self, physical_path):
        """[English Note] Translates server paths to GUI-friendly /app/data/."""
        from flowork_kernel.utils.path_helper import get_data_directory
        data_dir = str(get_data_directory())
        p_str = str(physical_path)

        if p_str.startswith(data_dir):
            rel = p_str[len(data_dir):].replace("\\", "/").lstrip("/")
            return f"/app/data/{rel}"

        return p_str.replace("\\", "/")

    def _resolve_and_secure_path(self, path_str, user_id):
        if path_str:
            clean_path = str(path_str).replace("\\", "/")

            if "/users/system" in clean_path and user_id and user_id != "system":
                clean_path = clean_path.replace("/users/system", f"/users/{user_id}")

            user_prefix_detect = f"/users/{user_id}"
            if user_prefix_detect in clean_path:
                parts = clean_path.split(user_prefix_detect, 1)
                if len(parts) > 1:
                    clean_path = parts[1].lstrip("/")

            path_str = clean_path.lstrip("/")

        return super()._resolve_and_secure_path(path_str, user_id)

    def secure_list_directory(self, path, user_id):
        """[App Path] Overrides Node listing to provide Virtual Paths."""
        res = super().secure_list_directory(path, user_id)

        if res.get("status") == "success":
            res["current_path"] = self._to_virtual_path(res["current_path"])
            for item in res["items"]:
                item["path"] = self._to_virtual_path(item.get("physical_path") or item.get("path"))
        return res

    def secure_create_folder(self, current_path, name, user_id):
        """[App Path] Returns Virtual Path of the new folder."""
        res = super().secure_create_folder(current_path, name, user_id)

        if res.get("status") == "success":
            res["path"] = self._to_virtual_path(res.get("physical_path") or res.get("path"))
        return res

    def secure_delete_path(self, path, user_id):
        """[App Path] Wrapper for delete to ensure smart resolution applies."""
        return super().secure_delete_path(path, user_id)
