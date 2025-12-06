########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\base_handler.py total lines 25 
########################################################################

import logging
from typing import Any

CURRENT_PAYLOAD_VERSION = 2

class BaseHandler:
    def __init__(self, service):
        """
        :param service: Instance of GatewayConnectorService
        """
        self.service = service
        self.logger = service.logger
        self.sio = service.sio

    def register_events(self):
        """
        (English Hardcode) Each handler must implement this to register its socket events.
        """
        raise NotImplementedError("Handlers must implement register_events()")
