########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\start_session.py total lines 63 
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


async def run(hub, data: dict, emit_callback: Callable[[str, dict], Awaitable[None]], fac_rt: FacRuntime):
    session_id = data.get('session_id')
    intent = data.get('intent')
    context = data.get('context', {})
    if not session_id or not intent:
        hub.logger.error(f'[AgentExecutor] Invalid start_session request. Missing session_id or intent.')
        await emit_callback('core:agent_error', {'session_id': session_id, 'code': 'INVALID_START', 'message': 'Core received invalid start request (missing session_id or intent).'})
        return
    if session_id in hub.sessions:
        hub.logger.warning(f'[AgentExecutor] Session {session_id} already exists. Attempting to cancel old one.')
        await (await hub.execute_async('cancel_session', {'session_id': session_id}))
    input_queue = asyncio.Queue()
    expires_at = fac_rt.fac_dict.get('expires_at')
    timeout_seconds = None
    if expires_at:
        timeout_seconds = max(1, expires_at - time.time())
        hub.logger.info(f'[AgentSession {session_id}] FAC: Applying TTL. Timeout in {timeout_seconds:.2f}s.')
    hub.logger.info(f'[AgentSession {session_id}] FAC: Applying Gas Limit of {fac_rt.budget.total} (from FacRuntime).')
    agent_task_logic = await hub.execute_async('_run_session_logic', session_id, intent, context, emit_callback, input_queue, fac_rt=fac_rt)

    async def session_wrapper():
        try:
            await asyncio.wait_for(agent_task_logic, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            hub.logger.warning(f'[AgentSession {session_id}] Session timed out (TTL exceeded).')
            try:
                await emit_callback('core:agent_error', {'session_id': session_id, 'code': 'AGENT_TIMED_OUT', 'message': 'Agent session exceeded its time-to-live (TTL).'})
            except Exception:
                pass
        except asyncio.CancelledError:
            raise
        except Exception as e:
            hub.logger.error(f'[AgentSession {session_id}] Session wrapper CRASHED: {e}', exc_info=True)
            try:
                await emit_callback('core:agent_error', {'session_id': session_id, 'code': 'SESSION_WRAPPER_CRASH', 'message': str(e)})
            except Exception:
                pass
    agent_task = asyncio.create_task(session_wrapper())
    hub.session_locks[session_id] = asyncio.Lock()
    async with hub.session_locks[session_id]:
        hub.sessions[session_id] = {'task': agent_task, 'input_queue': input_queue, 'emit_callback': emit_callback, 'conversation_history': [], 'last_observation': 'No actions taken yet.', 'objective': intent}
    hub.logger.info(f'[AgentExecutor] Agent session {session_id} started in a new task.')
