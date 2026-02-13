########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes\register_routes.py total lines 13 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from aiohttp import web
import json
import asyncio


def run(hub):
    return {'GET /api/v1/agents': hub.handle_get_agents, 'GET /api/v1/agents/{agent_id}': hub.handle_get_agent, 'POST /api/v1/agents': hub.handle_post_agents, 'DELETE /api/v1/agents/{agent_id}': hub.handle_delete_agent, 'POST /api/v1/agents/{agent_id}/run': hub.handle_run_agent, 'GET /api/v1/agents/run/{run_id}': hub.handle_get_agent_run_status, 'POST /api/v1/agents/run/{run_id}/stop': hub.handle_stop_agent_run, 'POST /api/v1/agent/run': hub.handle_run_agent_task_adhoc, 'POST /api/v1/ai/chat/completions': hub.handle_chat_completions}
