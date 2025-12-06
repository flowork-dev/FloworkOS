########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\plugins\metrics_logger_plugin\metrics_logger.py total lines 75 
########################################################################

import os
import json
import time
from flowork_kernel.api_contract import BaseModule

class MetricsLogger(BaseModule):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.subscription_id = f"{self.module_id}_listener"
        self.log_file_path = None

    def on_load(self):
        """
        Called when the service is started by the Kernel/PluginManager.
        """
        config = getattr(self, 'config', {})
        filename = config.get("log_filename", "metrics_history.jsonl")
        self.auto_flush = config.get("auto_flush", True)

        self.log_file_path = os.path.join(self.kernel.data_path, filename)

        if self.event_bus:
            self.event_bus.subscribe(
                event_name="NODE_EXECUTION_METRIC",
                subscriber_id=self.subscription_id,
                callback=self.on_metrics_updated
            )
            self.logger(f"Metrics Logger active. Logging to: {filename}", "INFO")
        else:
            self.logger("CRITICAL: EventBus service missing. Logger cannot start.", "ERROR")

    def on_unload(self):
        """
        Called when plugin is disabled or system is shutting down.
        Crucial for cleanup in the new architecture.
        """
        if self.event_bus:
            self.event_bus.unsubscribe(
                event_name="NODE_EXECUTION_METRIC",
                subscriber_id=self.subscription_id
            )
            self.logger("Metrics Logger unsubscribed and shutting down.", "INFO")

    def on_metrics_updated(self, event_payload):
        """
        Callback triggered whenever a node finishes execution and emits metrics.
        """
        if not self.log_file_path:
            return

        metrics_data = event_payload.get("data", event_payload) if isinstance(event_payload, dict) else event_payload

        log_entry = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "metrics": metrics_data
        }

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
                if self.auto_flush:
                    f.flush()
                    os.fsync(f.fileno())
        except Exception as e:
            self.logger(f"Failed to write metric: {str(e)}", "ERROR")
