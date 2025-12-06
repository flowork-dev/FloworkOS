########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\triggers\file_system_trigger\processor.py total lines 57 
########################################################################

import os
import datetime
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class FileSystemTriggerModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        path = config.get("path_to_watch", "")
        events = config.get("events_to_watch", ["created"])

        status_updater(f"Simulating file event in: {path}", "INFO")

        if not path:
            self.logger("Warning: No path configured for simulation.", "WARN")
            path = "/simulated/path"

        if 'data' not in payload:
            payload['data'] = {}

        mock_filename = "simulation_test_file.txt"
        mock_full_path = os.path.join(path, mock_filename)

        payload['data']['trigger_info'] = {
            'type': 'file_system',
            'event_type': events[0] if events else 'created',
            'is_directory': False,
            'src_path': mock_full_path,
            'filename': mock_filename,
            'timestamp': datetime.datetime.now().isoformat(),
            'source': 'manual_simulation'
        }

        payload['data']['file_path'] = mock_full_path

        status_updater("Workflow triggered manually (Simulated File).", "SUCCESS")

        return {"payload": payload, "output_name": "output"}

    def get_data_preview(self, config: dict):
        path = config.get("path_to_watch", "Not Set")
        events = config.get("events_to_watch", [])
        return [{
            "status": "watching",
            "message": f"{path}",
            "details": {"events": ", ".join(events)}
        }]
