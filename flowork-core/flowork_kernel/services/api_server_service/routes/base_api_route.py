########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\base_api_route.py total lines 20 
########################################################################

from abc import ABC, abstractmethod
from aiohttp import web
class BaseApiRoute(ABC):

    def __init__(self, service_instance):
        self.service_instance = service_instance
        self.kernel = service_instance.kernel
        self.logger = self.kernel.write_to_log
    def _json_response(self, data, status=200, headers=None):
        return web.json_response(data, status=status, headers=headers)
    @abstractmethod
    def register_routes(self) -> dict:

        pass
