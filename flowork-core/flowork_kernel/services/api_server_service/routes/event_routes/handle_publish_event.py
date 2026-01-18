########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\event_routes\handle_publish_event.py total lines 18 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    body = await request.json()
    if 'event_name' not in body or 'event_data' not in body:
        return await hub.execute_async('_json_response', {'error': "Request body must contain 'event_name' and 'event_data'."}, status=400)
    event_bus = hub.kernel.get_service('event_bus')
    if not event_bus:
        return await hub.execute_async('_json_response', {'error': 'EventBus service is not available.'}, status=503)
    event_bus.publish(body['event_name'], body['event_data'], publisher_id='ApiClient_GUI')
    return await hub.execute_async('_json_response', {'status': 'event_published', 'event_name': body['event_name']}, status=202)
