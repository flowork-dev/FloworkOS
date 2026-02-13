########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\_stream_council_session.py total lines 38 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
from aiohttp import web
import json
import asyncio


async def run(hub, request, body):
    """
        Orchestrates the Council Session and streams chunks back to Gateway.
        """
    response = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'application/json', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})
    await response.prepare(request)
    try:
        app_service = hub.kernel.get_service('app_service')
        architect_app = app_service.get_instance('apps', 'flowork_architect') if app_service else None
        if not architect_app:
            err = json.dumps({'type': 'error', 'message': 'Neural Architect App is not installed. Council unavailable.'}) + '\n'
            await response.write(err.encode('utf-8'))
            await response.write_eof()
            return response
        judge_id = body.get('judge_id')
        members = body.get('members', [])
        topic = body.get('topic') or body.get('prompt')
        iterator = architect_app.stream_deliberation(judge_id, members, topic)
        for chunk_str in iterator:
            await response.write(chunk_str.encode('utf-8'))
            await asyncio.sleep(0.01)
    except Exception as e:
        err_msg = json.dumps({'type': 'error', 'message': str(e)}) + '\n'
        await response.write(err_msg.encode('utf-8'))
    await response.write_eof()
    return response
