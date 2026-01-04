########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\permission_manager_service\permission_manager_service.py total lines 25 
########################################################################

import logging
from flowork_kernel.services.base_service import BaseService

class PermissionManagerService(BaseService):
    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)

        self.logger.warning("PermissionManager: Running in Open Core mode. All permission checks will be approved.")

    def check_permission(self, permission_name: str, context: dict = None) -> bool:
        """
        Always approve in Open Core / Dev Mode.
        Security is now handled by BaseService paths & AppRuntime sandboxing.
        """
        return True

    def request_approval(self, module_id, reason):
        self.logger.info(f"Auto-approving request from {module_id}: {reason}")
        return True
