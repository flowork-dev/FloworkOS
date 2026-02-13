########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\middleware_handler.py total lines 50 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
from aiohttp import web

async def run(hub, app, handler):
    """
    [FACTORY PATTERN FIX]
    Middleware aiohttp memanggil ini dengan (app, handler).
    Kita harus me-return fungsi wrapper yang menerima (request).
    """

    async def middleware(request):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*'
        }

        if request.method == 'OPTIONS':
            return web.Response(status=204, headers=headers)

        try:
            response = await handler(request)

            if not isinstance(response, web.StreamResponse):
                if isinstance(response, (dict, list)):
                    response = web.json_response(response)

            if response:
                response.headers.update(headers)

            return response

        except Exception as e:
            error_msg = str(e)
            if hasattr(hub, 'logger'):
                hub.logger.error(f"[Middleware] Error handling request: {error_msg}")

            return web.json_response(
                {'error': error_msg},
                status=500,
                headers=headers
            )

    return middleware
