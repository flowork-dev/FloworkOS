########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\prompt_routes.py total lines 149 
########################################################################

from .base_api_route import BaseApiRoute

class PromptRoutes(BaseApiRoute):

    def register_routes(self):
        return {
            "GET /api/v1/prompts": self.get_all_prompts,
            "POST /api/v1/prompts": self.create_prompt,
            "GET /api/v1/prompts/{prompt_id}": self.get_prompt_by_id,
            "PUT /api/v1/prompts/{prompt_id}": self.update_prompt,
            "DELETE /api/v1/prompts/{prompt_id}": self.delete_prompt,
        }

    def _get_service_or_fail(self):
        service = self.service_instance.kernel.get_service("prompt_manager_service")
        if not service:
            self.logger("CRITICAL: PromptRoutes failed to locate 'prompt_manager_service'. Service might have failed to start.", "ERROR")
        return service

    async def get_all_prompts(self, request):
        prompt_manager = self._get_service_or_fail()
        if not prompt_manager:
            return self._json_response(
                {"error": "PromptManagerService is not available. Check Engine Logs."}, status=503
            )

        try:
            result = prompt_manager.get_all_prompts()
            return self._json_response(result)
        except Exception as e:
            self.logger(f"Error in get_all_prompts: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def get_prompt_by_id(self, request):
        prompt_id = request.match_info.get("prompt_id")
        prompt_manager = self._get_service_or_fail()

        if not prompt_manager:
            return self._json_response(
                {"error": "PromptManagerService is not available."}, status=503
            )

        try:
            result = prompt_manager.get_prompt(prompt_id)
            if result:
                return self._json_response(result)
            else:
                return self._json_response(
                    {"error": "Prompt not found."}, status=404
                )
        except Exception as e:
            self.logger(f"Error in get_prompt_by_id: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def create_prompt(self, request):
        prompt_manager = self._get_service_or_fail()

        if not prompt_manager:
            return self._json_response(
                {"error": "PromptManagerService is not available."}, status=503
            )
        try:
            body = await request.json()
        except Exception:
             return self._json_response(
                {"error": "Invalid JSON body."}, status=400
            )

        if not body:
            return self._json_response(
                {"error": "Request body is required."}, status=400
            )

        try:
            result = prompt_manager.create_prompt(body)
            if result and "error" in result:
                return self._json_response(result, status=400)
            elif result:
                return self._json_response(result, status=201)
            else:
                return self._json_response(
                    {"error": "Service call to create prompt failed."}, status=500
                )
        except Exception as e:
            self.logger(f"Error in create_prompt: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def update_prompt(self, request):
        prompt_id = request.match_info.get("prompt_id")
        prompt_manager = self._get_service_or_fail()

        if not prompt_manager:
            return self._json_response(
                {"error": "PromptManagerService is not available."}, status=503
            )
        try:
            body = await request.json()
        except Exception:
             return self._json_response(
                {"error": "Invalid JSON body."}, status=400
            )

        if not body:
            return self._json_response(
                {"error": "Request body is required."}, status=400
            )

        try:
            result = prompt_manager.update_prompt(prompt_id, body)
            if result and "error" in result:
                return self._json_response(result, status=400)
            elif result:
                return self._json_response(result)
            else:
                return self._json_response(
                    {"error": "Service call to update prompt failed."}, status=500
                )
        except Exception as e:
            self.logger(f"Error in update_prompt: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def delete_prompt(self, request):
        prompt_id = request.match_info.get("prompt_id")
        prompt_manager = self._get_service_or_fail()

        if not prompt_manager:
            return self._json_response(
                {"error": "PromptManagerService is not available."}, status=503
            )

        try:
            result = prompt_manager.delete_prompt(prompt_id)
            if result and "error" in result:
                return self._json_response(result, status=404)
            elif result:
                return self._json_response(result, status=204)
            else:
                return self._json_response(
                    {"error": "Service call to delete prompt failed."}, status=500
                )
        except Exception as e:
            self.logger(f"Error in delete_prompt: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)
