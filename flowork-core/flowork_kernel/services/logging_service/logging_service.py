########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\logging_service\logging_service.py total lines 132 
########################################################################

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from datetime import datetime

import logging

class LoggingService(BaseService):


    def __init__(self, kernel, name="logging_service"):

        super().__init__(kernel, name)
        self.logger = None
        self.log_level = logging.DEBUG
        self.log_dir = os.path.join(self.kernel.get_root_dir(), 'logs')
        self.log_file = os.path.join(self.log_dir, 'flowork_core.log')
        self.gateway_connector = None

    def start(self):

        try:
            self.gateway_connector = Singleton.get_instance(self.kernel, 'gateway_connector_service')
        except Exception as e:
            if self.logger:
                self.logger.error(f"[LoggingService] Failed to get GatewayConnector: {e}")
            else:
                print(f"ERROR: [LoggingService] Failed to get GatewayConnector: {e}")
            self.gateway_connector = None

        if self.logger:
            self.logger.info(f"[LoggingService] Started. GatewayConnector linked: {self.gateway_connector is not None}")
        else:
            print("[LoggingService] Started.")

    def setup(self, log_level_str='DEBUG', log_to_file=True):

        os.makedirs(self.log_dir, exist_ok=True)

        try:
            self.log_level = getattr(logging, log_level_str.upper(), logging.DEBUG)
        except AttributeError:
            self.log_level = logging.DEBUG

        self.logger = logging.getLogger("FloworkCore")
        self.logger.setLevel(self.log_level)
        self.logger.handlers = []

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(processName)s] - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        if log_to_file:
            file_handler = RotatingFileHandler(
                self.log_file, maxBytes=10*1024*1024, backupCount=5
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.logger.info(f"LoggingService setup complete. Level: {log_level_str}")

    def _log(self, level, message, source, **kwargs):

        if not self.logger:
            print(f"LOGGER NOT INITIALIZED: [{source}] {message}")
            return

        if level < self.log_level:
            return

        log_message = f"[{source}] {message}"
        self.logger.log(level, log_message)

        if self.gateway_connector:
            user_id = kwargs.get('user_id')
            job_id = kwargs.get('job_id')
            node_id = kwargs.get('node_id')

            if user_id:
                try:
                    level_name = logging.getLevelName(level)
                    self.gateway_connector.send_workflow_log_entry(
                        user_id=user_id,
                        job_id=job_id,
                        node_id=node_id,
                        level=level_name,
                        message=message,
                        source=source,
                        ts=datetime.now().isoformat()
                    )
                except Exception as e:
                    self.logger.error(f"[LoggingService] CRITICAL: Failed to emit log entry to Gateway: {e}")

    def info(self, message, source="System", **kwargs):
        self._log(logging.INFO, message, source, **kwargs)

    def warn(self, message, source="System", **kwargs):
        self._log(logging.WARNING, message, source, **kwargs)

    def error(self, message, source="System", **kwargs):
        self._log(logging.ERROR, message, source, **kwargs)

    def debug(self, message, source="System", **kwargs):
        self._log(logging.DEBUG, message, source, **kwargs)

    def critical(self, message, source="System", **kwargs):
        self._log(logging.CRITICAL, message, source, **kwargs)

    def success(self, message, source="System", **kwargs):
        self._log(logging.INFO, message, source, **kwargs)

    def detail(self, message, source="System", **kwargs):
        self.debug(message, source, **kwargs)

    def get_logger(self):

        return self.logger
