########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\triggers\process_trigger\processor.py total lines 132 
########################################################################

import threading
import time
import psutil
import datetime
from flowork_kernel.api_contract import BaseModule, IExecutable, BaseTriggerListener, IDataPreviewer

class ProcessListener(BaseTriggerListener):

    def __init__(self, trigger_id, config, services, **kwargs):
        super().__init__(trigger_id, config, services, **kwargs)
        self.process_name = self.config.get("process_name")
        self.event_to_watch = self.config.get("event_to_watch", "started")
        self.check_interval = int(self.config.get("check_interval", 5))

        self.is_currently_running = False
        self._stop_event = threading.Event()
        self._thread = None

    def _is_process_running(self):
        target = self.process_name.lower()
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == target:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def _monitor_loop(self):
        self.is_currently_running = self._is_process_running()

        while not self._stop_event.is_set():
            time.sleep(self.check_interval)

            try:
                process_is_now_running = self._is_process_running()

                event_payload = None

                if process_is_now_running and not self.is_currently_running:
                    if self.event_to_watch == "started":
                        event_payload = {"event": "started", "process_name": self.process_name}

                elif not process_is_now_running and self.is_currently_running:
                    if self.event_to_watch == "stopped":
                        event_payload = {"event": "stopped", "process_name": self.process_name}

                self.is_currently_running = process_is_now_running

                if event_payload:
                    full_payload = {
                        "trigger_info": {
                            "type": "process",
                            "event": event_payload["event"],
                            "process_name": event_payload["process_name"],
                            "timestamp": time.time()
                        },
                        "data": {
                            "process_name": event_payload["process_name"],
                            "status": event_payload["event"]
                        }
                    }
                    self.logger(f"Process Event Detected: {self.process_name} -> {event_payload['event']}", "INFO")
                    self._on_event(full_payload)

            except Exception as e:
                self.logger(f"Error in process monitor loop: {e}", "ERROR")

    def start(self):
        if not self.process_name:
            self.logger(f"Process Trigger '{self.rule_id}' failed: Process name not configured.", "ERROR")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self.is_running = True
        self.logger(f"Process Watcher started for '{self.process_name}' (Interval: {self.check_interval}s)", "INFO")

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.is_running = False
        self.logger(f"Process Watcher stopped.", "INFO")


class ProcessTriggerModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        process_name = config.get("process_name", "notepad.exe")
        event = config.get("event_to_watch", "started")

        status_updater(f"Simulating Process Trigger: {process_name} ({event})", "INFO")

        if 'data' not in payload:
            payload['data'] = {}

        payload['data']['trigger_info'] = {
            'type': 'process',
            'event': event,
            'process_name': process_name,
            'source': 'manual_simulation',
            'timestamp': datetime.datetime.now().isoformat()
        }

        payload['data']['process_name'] = process_name
        payload['data']['status'] = event

        status_updater("Workflow triggered manually (Simulated).", "SUCCESS")

        return {"payload": payload, "output_name": "output"}

    def get_data_preview(self, config: dict):
        proc = config.get("process_name", "None")
        evt = config.get("event_to_watch", "started")
        return [{
            "status": "watching",
            "message": f"{proc}",
            "details": {"wait_for": evt}
        }]
