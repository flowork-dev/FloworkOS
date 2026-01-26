########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\handle_input.py total lines 42 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import threading
import json
import time
import re
import os
import asyncio
import uuid
from typing import Callable, Awaitable, List, Dict, Any, Optional
from flowork_kernel.singleton import Singleton
from flowork_kernel.swarm import LocalSwarmRegistry, SwarmCoordinator
from flowork_kernel.context import boot_agent, AgentContext
from flowork_kernel.fac_enforcer import FacRuntime
from flowork_kernel.exceptions import PermissionDeniedError


async def run(hub, data: dict):
    session_id = data.get('session_id')
    payload = data.get('payload')
    fac_rt: Optional[FacRuntime] = None
    if hub.gateway_connector:
        fac_rt = hub.gateway_connector.g_active_sessions.get(session_id)
    if not fac_rt:
        hub.logger.warning(f'[AgentExecutor] Input for {session_id} REJECTED: No valid FAC runtime found (session may have expired or failed start).')
        try:
            emit_callback = hub.sessions.get(session_id, {}).get('emit_callback')
            if emit_callback:
                await emit_callback('core:agent_error', {'session_id': session_id, 'code': 'SESSION_INVALID', 'message': 'No valid session runtime found. Please restart session.'})
        except Exception as e:
            hub.logger.error(f'Failed to send session invalid error: {e}')
        return
    session_info = hub.sessions.get(session_id)
    if session_info and session_info.get('input_queue'):
        await session_info['input_queue'].put(payload)
        hub.logger.info(f'[AgentExecutor] Input queued for session {session_id}.')
    else:
        hub.logger.warning(f'[AgentExecutor] Could not queue input for session {session_id}: Session not found or queue missing.')
