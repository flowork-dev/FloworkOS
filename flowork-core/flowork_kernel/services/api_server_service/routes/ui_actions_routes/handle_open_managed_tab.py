########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\ui_actions_routes\handle_open_managed_tab.py total lines 20 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute


async def run(hub, request):
    body = await request.json()
    if not body or 'tab_key' not in body:
        return await hub.execute_async('_json_response', {'error': "Request must contain a 'tab_key'."}, status=400)
    event_bus = hub.service_instance.event_bus
    if not event_bus:
        return await hub.execute_async('_json_response', {'error': 'EventBus service is not available.'}, status=503)
    tab_key = body['tab_key']
    event_bus.publish('OPEN_MANAGED_TAB_REQUEST', {'tab_key': tab_key}, publisher_id='ApiServer')
    await hub.execute_async('logger', f"Published OPEN_MANAGED_TAB_REQUEST event for tab_key: '{tab_key}'", 'INFO')
    return await hub.execute_async('_json_response', {'status': 'accepted', 'message': f"Request to open tab '{tab_key}' has been broadcasted."}, status=202)
