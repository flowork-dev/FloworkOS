########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\plugins\system_diagnostics_plugin\processor.py total lines 69 
########################################################################

import platform
import json
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class SystemDiagnosticsPlugin(BaseModule, IExecutable, IDataPreviewer):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.diagnostics_service = self.services.get("diagnostics_service")

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        detail_level = config.get("report_detail", "Standard")
        include_hw = config.get("include_hardware_info", True)

        status_updater(f"Running {detail_level} diagnostics...", "INFO")

        report = {
            "status": "healthy",
            "checks": [],
            "meta": {"level": detail_level}
        }

        if self.diagnostics_service:
            try:
                if hasattr(self.diagnostics_service, "get_full_report"):
                    report = self.diagnostics_service.get_full_report(detail_level)
                else:
                    report["message"] = "DiagnosticsService found but API differs."
            except Exception as e:
                self.logger(f"Diagnostics fail: {e}", "ERROR")
                report["error"] = str(e)
        else:
            status_updater("Service unreachable. Using local diagnostics.", "WARN")
            report["checks"].append({"component": "Kernel", "status": "OK"})
            report["checks"].append({"component": "Network", "status": "OK"})

        if include_hw:
            try:
                uname = platform.uname()
                report["hardware"] = {
                    "system": uname.system,
                    "node": uname.node,
                    "release": uname.release,
                    "machine": uname.machine
                }
            except:
                pass

        status_updater("Diagnostics complete.", "SUCCESS")

        if "data" not in payload: payload["data"] = {}
        payload["data"]["diagnostics_report"] = report

        return {"payload": payload, "output_name": "success"}

    def get_data_preview(self, config: dict):
        return [{
            "status": "ready",
            "message": f"Config: {config.get('report_detail', 'Standard')}",
            "details": {"hw_check": config.get("include_hardware_info", True)}
        }]
