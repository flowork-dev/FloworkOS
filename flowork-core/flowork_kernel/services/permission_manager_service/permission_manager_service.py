########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\permission_manager_service\permission_manager_service.py total lines 19 
########################################################################

from ..base_service import BaseService
from flowork_kernel.exceptions import PermissionDeniedError
class PermissionManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.logger("PermissionManager: Running in Open Core mode. All permission checks will be approved.", "WARN")
    def load_rules_from_source(self, rules_dict):
        self.logger("Permission rules loading is skipped in Open Core mode.", "INFO")
        pass
    def check_permission(self, capability: str, is_system_call: bool = False) -> bool:

        return True
