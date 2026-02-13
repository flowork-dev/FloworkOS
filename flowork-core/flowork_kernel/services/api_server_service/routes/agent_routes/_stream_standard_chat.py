########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\_stream_standard_chat.py total lines 43 
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
        Basic implementation for standard chat.
        """
    provider_manager = getattr(hub.service_instance, 'ai_provider_manager_service', None)
    response = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'application/json'})
    await response.prepare(request)
    if not provider_manager:
        err = json.dumps({'type': 'error', 'message': 'AI Provider Service unavailable in Core.'}) + '\n'
        await response.write(err.encode('utf-8'))
        await response.write_eof()
        return response
    model = body.get('model')
    messages = body.get('messages', [])
    prompt = body.get('prompt')
    if not prompt and messages:
        for m in reversed(messages):
            if m['role'] == 'user':
                prompt = m['content']
                break
    try:
        stream = provider_manager.stream_text(model_id=model, prompt=prompt, system_prompt='You are a helpful Flowork assistant.', temperature=0.7)
        for chunk in stream:
            data = json.dumps({'type': 'content', 'chunk': chunk}) + '\n'
            await response.write(data.encode('utf-8'))
            await asyncio.sleep(0.01)
    except Exception as e:
        err = json.dumps({'type': 'error', 'message': f'Core Error: {str(e)}'}) + '\n'
        await response.write(err.encode('utf-8'))
    await response.write_eof()
    return response
