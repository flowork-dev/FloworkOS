########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\event_routes.py total lines 33 
########################################################################

from .base_api_route import BaseApiRoute
class EventRoutes(BaseApiRoute):

    def register_routes(self):

        return {
            "POST /api/v1/events/publish": self.handle_publish_event,
        }
    async def handle_publish_event(self, request):

        body = await request.json()
        if "event_name" not in body or "event_data" not in body:
            return self._json_response(
                {"error": "Request body must contain 'event_name' and 'event_data'."},
                status=400,
            )
        event_bus = self.kernel.get_service("event_bus")
        if not event_bus:
            return self._json_response(
                {"error": "EventBus service is not available."}, status=503
            )
        event_bus.publish(
            body["event_name"], body["event_data"], publisher_id="ApiClient_GUI"
        )
        return self._json_response(
            {"status": "event_published", "event_name": body["event_name"]}, status=202
        )
