########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\log_recorder_service\log_recorder_service.py total lines 128 
########################################################################

import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from flowork_kernel.services.base_service import BaseService

class LogRecorderService(BaseService):
    """
    THE BLACKBOX 📓
    Tugas: Mencatat semua kejadian penting ke dalam file fisik (Disk).
    Fitur:
    - Log Rotation (Biar harddisk gak penuh).
    - Dual Channel (System Log & App Log).
    - Crash Evidence Preservation.
    """

    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)

        self.log_dir = os.path.join(self.kernel.project_root_path, "data", "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        self.file_logger = logging.getLogger("FloworkBlackbox")
        self.file_logger.setLevel(logging.INFO)
        self.file_logger.propagate = False # Jangan lempar ke console lagi (berisik)

        log_file_path = os.path.join(self.log_dir, "flowork_system.log")
        handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10*1024*1024, # 10 MB
            backupCount=5,
            encoding='utf-8'
        )

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        self.file_logger.addHandler(handler)

    def start(self):
        self.logger.info("📓 [Blackbox] Recorder Active. Tape is rolling...")

        self.kernel.event_bus.subscribe("execution_log", "blackbox_sys", self._record_system_log)
        self.kernel.event_bus.subscribe("WORKFLOW_LOG_ENTRY", "blackbox_wf", self._record_system_log)

        self.kernel.event_bus.subscribe("APP_LOG_STREAM", "blackbox_app", self._record_app_log)
        self.kernel.event_bus.subscribe("APP_ERROR", "blackbox_err", self._record_app_error)

    def stop(self):
        self.logger.info("📓 [Blackbox] Stopping Recorder.")

    def _record_system_log(self, payload, *args):
        try:

            data = payload
            if not isinstance(data, (dict, str)) and args:
                for arg in args:
                    if isinstance(arg, (dict, str)):
                        data = arg
                        break

            if isinstance(data, str):
                data = {"message": data}

            level = data.get("level", "INFO").upper() if isinstance(data, dict) else "INFO"
            source = data.get("source", "SYSTEM") if isinstance(data, dict) else "SYSTEM"
            msg = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            node_id = data.get("node_id", "") if isinstance(data, dict) else ""

            log_entry = f"[{source}] {msg}"
            if node_id:
                log_entry = f"[{source}][{node_id}] {msg}"

            if level == "ERROR" or level == "CRITICAL":
                self.file_logger.error(log_entry)
            elif level == "WARNING":
                self.file_logger.warning(log_entry)
            else:
                self.file_logger.info(log_entry)

        except Exception:
            pass

    def _record_app_log(self, payload, *args):
        try:
            data = payload
            if not isinstance(data, dict) and args:
                for arg in args:
                    if isinstance(arg, dict):
                        data = arg
                        break

            if not isinstance(data, dict): return

            app_id = data.get("app_id", "unknown_app")
            msg = data.get("message", "")
            pid = data.get("pid", "?")

            log_entry = f"[APP:{app_id}][PID:{pid}] {msg}"
            self.file_logger.info(log_entry)

        except Exception:
            pass

    def _record_app_error(self, payload, *args):
        try:
            data = payload
            if not isinstance(data, dict) and args:
                for arg in args:
                    if isinstance(arg, dict):
                        data = arg
                        break

            if not isinstance(data, dict): return

            app_id = data.get("app_id", "unknown_app")
            error = data.get("error", "Unknown Error")
            log_entry = f"[APP_CRASH:{app_id}] ❌ {error}"
            self.file_logger.error(log_entry)
        except Exception:
            pass
