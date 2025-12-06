########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\folder_purge\processor.py total lines 80 
########################################################################

import os
import shutil
import traceback
from flowork_kernel.api_contract import BaseModule, IExecutable

class FolderPurge(BaseModule, IExecutable):

    TIER = "builder"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.logger = services.get("logger")

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):
        if mode == "SIMULATE":
            return {
                "payload": {"data": {"deleted_count": 0}},
                "output_name": "success"
            }

        target_folder = config.get("target_folder")
        safety_lock = config.get("safety_lock", False)

        if not target_folder:
            return self._error("No folder selected!", status_updater)

        if not os.path.exists(target_folder):
            return self._error(f"Target path does not exist: {target_folder}", status_updater)

        if not safety_lock:
            return self._error("Safety Lock is ACTIVE. Please toggle the confirmation switch.", status_updater)

        try:
            status_updater(f"🗑️ Starting Purge on: {target_folder}", "INFO")

            items = os.listdir(target_folder)
            count = 0
            total_items = len(items)

            if total_items == 0:
                 status_updater("🧹 Folder is already empty.", "SUCCESS")
                 return {"payload": {"data": {"deleted_count": 0}}, "output_name": "success"}

            for item in items:
                item_path = os.path.join(target_folder, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path) # Delete file or symlink
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path) # Delete subfolder recursively

                    count += 1

                    if count % 10 == 0 or count == total_items:
                         status_updater(f"🔥 Deleted {count}/{total_items} items...", "INFO")

                except Exception as e:
                    self.logger.error(f"Failed to delete {item_path}: {e}")
                    status_updater(f"⚠️ Failed to delete {item}: {str(e)}", "WARNING")

            status_updater(f"✅ Cleaned {count} items successfully!", "SUCCESS")

            return {
                "payload": {"data": {"deleted_count": count}},
                "output_name": "success"
            }

        except Exception as e:
            traceback.print_exc()
            return self._error(f"Purge System Error: {str(e)}", status_updater)

    def _error(self, msg, updater):
        updater(msg, "ERROR")
        return {"payload": {"data": {"error": msg}}, "output_name": "error"}
