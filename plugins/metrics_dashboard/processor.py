########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\plugins\metrics_dashboard\processor.py total lines 86 
########################################################################

import random
import time
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class MetricsDashboardModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.state_manager = self.services.get("state_manager")

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        title = config.get("dashboard_title", "System Monitor")
        tracked_metrics = config.get("tracked_metrics", [])

        status_updater(f"Updating {title}...", "INFO")


        metrics_data = {}
        alerts = []

        for item in tracked_metrics:
            m_type = item.get("metric_key")
            threshold = int(item.get("alert_threshold", 80))

            val = 0
            unit = ""

            if m_type == "CPU Usage":
                val = random.randint(10, 90)
                unit = "%"
            elif m_type == "Memory Usage":
                val = random.randint(40, 85)
                unit = "%"
            elif m_type == "Active Threads":
                val = random.randint(5, 50)
                unit = "threads"
            elif m_type == "Task Queue":
                val = random.randint(0, 15)
                unit = "jobs"
            elif m_type == "Workflow Success Rate":
                val = random.randint(95, 100)
                unit = "%"

            metrics_data[m_type] = {
                "value": val,
                "unit": unit,
                "status": "CRITICAL" if (m_type != "Workflow Success Rate" and val > threshold) else "OK"
            }

            if metrics_data[m_type]["status"] == "CRITICAL":
                alerts.append(f"{m_type} high ({val}{unit})")

        if alerts:
            status_updater(f"Alerts: {', '.join(alerts)}", "WARN")
        else:
            status_updater("All systems nominal.", "SUCCESS")

        if "data" not in payload: payload["data"] = {}
        payload["data"]["metrics_snapshot"] = metrics_data
        payload["data"]["dashboard_meta"] = {
            "title": title,
            "timestamp": time.time()
        }

        return {"payload": payload, "output_name": "success"}

    def get_data_preview(self, config: dict):
        tracked = config.get("tracked_metrics", [])
        metric_names = [m.get("metric_key", "Unknown") for m in tracked]

        if not metric_names:
            return [{"status": "inactive", "message": "No metrics configured"}]

        return [{
            "status": "ready",
            "message": f"Monitoring {len(metric_names)} metrics",
            "details": {"monitored": metric_names}
        }]
