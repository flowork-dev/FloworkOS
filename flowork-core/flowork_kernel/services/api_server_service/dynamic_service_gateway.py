########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\dynamic_service_gateway.py total lines 69 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
from aiohttp import web
import json
import logging

logger = logging.getLogger("DynamicRouter")

async def run(hub, request):
    """
    [REPAIRED - FASE 2 SECURITY PATCH]
    Universal Gateway yang menerima request untuk service apapun.
    Sekarang dilengkapi dengan Filter Keamanan untuk memblokir akses ke private methods.
    Route: POST /api/connect/{service_name}/{action}
    """
    try:
        service_name = request.match_info.get('service_name')
        action = request.match_info.get('action')

        if action.startswith('_'):
            logger.warning(f"⛔ [SecurityGuard] Blocked unauthorized access attempt to {service_name}.{action} from {request.remote}")
            return web.json_response({
                'status': 'error',
                'message': '❌ Forbidden: Access to private method denied.'
            }, status=403)

        try:
            data = await request.json()
        except:
            data = {}

        service = hub.get_service(service_name)
        if not service:
            return web.json_response({
                'status': 'error',
                'message': f'Service {service_name} not found or not loaded.'
            }, status=404)

        func = getattr(service, action, None)

        if not func:
            return web.json_response({
                'status': 'error',
                'message': f'Action {action} not found in {service_name}.'
            }, status=404)

        if not callable(func):
            return web.json_response({
                'status': 'error',
                'message': f'Property {action} is not executable.'
            }, status=400)

        logger.info(f"🔀 [Router] Routing to {service_name}.{action}...")

        if asyncio.iscoroutinefunction(func):
            result = await func(data)
        else:
            result = await asyncio.to_thread(func, data)

        return web.json_response({'status': 'success', 'data': result})

    except Exception as e:
        logger.error(f"🔥 [RouterError] Failed routing {service_name}.{action}: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)
