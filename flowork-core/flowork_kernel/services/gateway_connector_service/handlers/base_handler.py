########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\base_handler.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
from typing import Any


CURRENT_PAYLOAD_VERSION = 2

class BaseHandler:
    def __init__(self, service):
        """
        :param service: Instance of GatewayConnectorService (passed dynamically)
        """
        self.service = service

        self.logger = getattr(service, 'logger', logging.getLogger('BaseHandler'))
        self.sio = getattr(service, 'sio', None)

    def register_events(self):
        """
        Wajib diimplementasikan oleh subclass.
        """
        raise NotImplementedError("Handlers must implement register_events()")
