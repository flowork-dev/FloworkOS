########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\settings_routes.py total lines 53 
########################################################################

from .base_api_route import BaseApiRoute

class SettingsRoutes(BaseApiRoute):

    def register_routes(self):
        return {
            "GET /api/v1/settings": self.handle_get_settings,
            "PATCH /api/v1/settings": self.handle_patch_settings,
            "GET /api/v1/user/preferences": self.handle_get_settings,
            "PATCH /api/v1/user/preferences": self.handle_patch_settings,
        }

    async def handle_get_settings(self, request):
        """
        Retrieves global settings from StateManager.
        """
        state_manager = self.service_instance.kernel.get_service("state_manager_service")
        if not state_manager:
            return self._json_response(
                {"error": "StateManager service is unavailable."}, status=503
            )

        settings = state_manager.get_all()
        return self._json_response(settings)

    async def handle_patch_settings(self, request):
        """
        Updates settings via StateManager.
        """
        state_manager = self.service_instance.kernel.get_service("state_manager_service")
        if not state_manager:
            return self._json_response(
                {"error": "StateManager service is unavailable."}, status=503
            )

        try:
            body = await request.json()
            if not body:
                return self._json_response({"error": "Empty payload"}, status=400)

            state_manager.update_all(body)

            return self._json_response(
                {"status": "success", "message": "Settings updated.", "settings": state_manager.get_all()}
            )
        except Exception as e:
            return self._json_response({"error": f"Failed to update settings: {str(e)}"}, status=500)
