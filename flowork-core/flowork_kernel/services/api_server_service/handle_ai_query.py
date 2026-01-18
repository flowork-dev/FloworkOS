########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\handle_ai_query.py total lines 42 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from aiohttp import web
import json

async def run(hub, request):
    """
    Menangani request query AI dari App/UI ke AI Provider Manager.
    """
    try:
        body = await request.json()
    except:
        return web.json_response({'error': 'Invalid JSON body'}, status=400)

    ai_provider = hub.kernel.get_service('ai_provider_manager_service')
    if not ai_provider:
        return web.json_response({'error': 'AI Provider Service Offline'}, status=503)

    task_type = body.get('task_type', 'text')
    prompt = body.get('prompt')
    endpoint_id = body.get('endpoint_id')
    user_id = body.get('user_id', 'system')

    if not prompt:
        return web.json_response({'error': 'Prompt is required'}, status=400)

    try:
        res = ai_provider.query_ai_by_task(
            task_type=task_type,
            prompt=prompt,
            endpoint_id=endpoint_id,
            user_id=user_id,
            **body
        )

        return web.json_response({'status': 'success', 'response': res})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
