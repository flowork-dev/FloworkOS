########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\handle_chat_completions.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base_api_route import BaseApiRoute
from aiohttp import web
import json
import asyncio


async def run(hub, request):
    """
        Handles standard Chat Completions AND Neural Council Sessions.
        Streamed response compatible with Gateway.
        """
    try:
        body = await request.json()
    except:
        return await hub.execute_async('_json_response', {'error': 'Invalid JSON'}, status=400)
    if body.get('is_council'):
        return await (await hub.execute_async('_stream_council_session', request, body))
    return await (await hub.execute_async('_stream_standard_chat', request, body))
