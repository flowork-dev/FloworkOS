########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\debug_popup_module\processor.py total lines 80 
########################################################################

"""
document : https://flowork.cloud/p-tinjauan-modul-processorpy-inspektur-data-runtime-debug-popup-id.html
"""
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
import json
from typing import Dict, Any, Callable, Tuple

class DebugPopupModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)

    def execute(self, payload: Dict[str, Any], config: Dict[str, Any], status_updater: Callable, mode: str = 'EXECUTE', **kwargs):
        node_instance_id = config.get("__internal_node_id", self.module_id)

        status_updater("Inspecting payload data...", "INFO")

        popup_title = config.get("popup_title", f"Debug: {node_instance_id}")
        theme_mode = config.get("theme_mode", "Default")
        auto_close = config.get("auto_close_seconds", 0)
        show_meta = config.get("show_metadata", False)

        try:
            data_to_show = payload
            if show_meta:
               data_to_show = {
                   "meta": {
                       "node_id": node_instance_id,
                       "mode": mode,
                       "timestamp": "runtime"
                   },
                   "data": payload
               }

            payload_to_display = json.dumps(data_to_show, indent=4, ensure_ascii=False, default=str)
        except Exception as e:
            self.logger(f"Failed to serialize payload for debug popup: {e}", "ERROR")
            payload_to_display = f"Error: Could not serialize payload.\n{str(e)}"

        event_data = {
            "title": popup_title,
            "content": payload_to_display,
            "config": {
                "theme": theme_mode,
                "auto_close": auto_close,
                "type": "json_viewer" # Hint to UI to use syntax highlighting
            }
        }

        try:
            self.publish_event("SHOW_DEBUG_POPUP", event_data)
            status_updater(
                f"Popup sent to UI ({theme_mode} theme).", "SUCCESS"
            )
        except AttributeError:
            self.logger("EventBus service not found. Logging to console instead.", "WARN")
            self.logger(f"--- DEBUG POPUP CONTENT ({popup_title}) ---", "DEBUG")
            self.logger(payload_to_display, "DEBUG")
            status_updater("Payload logged to console (EventBus service missing).", "WARN")
        except Exception as e:
            self.logger(f"Error publishing SHOW_DEBUG_POPUP event: {e}", "ERROR")
            status_updater(f"Failed to send popup event: {e}", "ERROR")

        return {"payload": payload, "output_name": "output"}

    def get_data_preview(self, config: dict):
        return [
            {
                "status": "ready",
                "message": "Debug inspector is active"
            }
        ]
