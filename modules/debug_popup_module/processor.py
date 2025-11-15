########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\debug_popup_module\processor.py total lines 57 
########################################################################

from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
import json
from typing import Dict, Any, Callable, Tuple
class DebugPopupModule(BaseModule, IExecutable, IDataPreviewer):
    """
    Core module for displaying debug information in a popup window on the UI.
    """
    TIER = "free"
    def __init__(self, module_id, services):
        super().__init__(module_id, services)
    def execute(self, payload: Dict[str, Any], config: Dict[str, Any], status_updater: Callable, mode: str = 'EXECUTE', **kwargs):
        """
        Executes the module: formats the payload and publishes the SHOW_DEBUG_POPUP event.
        """
        node_instance_id = config.get("__internal_node_id", self.module_id)
        status_updater("Preparing to log payload...", "INFO")
        popup_title = config.get("popup_title", f"Debug from Node: {node_instance_id}")
        try:
            payload_to_display = json.dumps(payload, indent=4, ensure_ascii=False, default=str)
        except Exception as e:
            self.logger(f"Failed to serialize payload for debug popup: {e}", "ERROR")
            payload_to_display = f"Error: Could not serialize payload.\n{str(e)}"
        event_data = {
            "title": popup_title,
            "content": payload_to_display
        }
        try:
            self.publish_event("SHOW_DEBUG_POPUP", event_data)
            status_updater(
                "Debug data sent to UI for display.", "SUCCESS"
            )
        except AttributeError:
            self.logger("EventBus service not found. Logging to console instead.", "WARN")
            self.logger(f"--- DEBUG PAYLOAD from node '{node_instance_id}' ---", "DEBUG")
            self.logger(payload_to_display, "DEBUG")
            self.logger(f"--- END DEBUG PAYLOAD ---", "DEBUG")
            status_updater("Payload logged to console (EventBus service missing).", "WARN")
        except Exception as e:
            self.logger(f"Error publishing SHOW_DEBUG_POPUP event: {e}", "ERROR")
            status_updater(f"Failed to send popup event: {e}", "ERROR")
        return {"payload": payload, "output_name": "output"}
    def get_data_preview(self, config: dict):
        """
        Provides a sample of what this module might output for the Data Canvas.
        """
        return [
            {
                "status": "preview_not_available",
                "reason": "Displays live payload data during execution.",
            }
        ]
