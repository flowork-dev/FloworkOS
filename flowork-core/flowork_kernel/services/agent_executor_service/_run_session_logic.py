########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\_run_session_logic.py total lines 89 
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


async def run(hub, session_id: str, initial_intent: str, context: dict, emit_callback: Callable[[str, dict], Awaitable[None]], input_queue: asyncio.Queue, fac_rt: FacRuntime):
    hub.logger.info(f'[AgentSession {session_id}] Task starting. Intent: {initial_intent[:50]}...')
    history = []
    try:
        await emit_callback('core:agent_status', {'session_id': session_id, 'phase': 'running'})
        ai_provider = hub.ai_manager.get_default_provider('text')
        if not ai_provider:
            hub.logger.error(f"[AgentSession {session_id}] No default 'text' AI provider found.")
            raise Exception('No default text AI provider is configured on this engine.')
        chat_session = ai_provider.create_chat_session(history=history)
        hub.logger.info(f'[AgentSession {session_id}] Created chat session with provider: {ai_provider.provider_id}')
        current_input = initial_intent
        while True:
            if current_input:
                try:
                    fac_rt.budget.consume(1)
                    hub.logger.info(f'[AgentSession {session_id}] Gas charge OK. Remaining: {fac_rt.budget.remaining()}')
                except (PermissionError, PermissionDeniedError) as e:
                    hub.logger.warning(f'[AgentSession {session_id}] Gas limit exceeded: {e}')
                    await emit_callback('core:agent_error', {'session_id': session_id, 'code': 'GAS_LIMIT_EXCEEDED', 'message': f'Agent session has exceeded its gas limit: {e}'})
                    break
                hub.logger.debug(f'[AgentSession {session_id}] Sending to AI: {current_input[:50]}...')
                response_stream = None
                full_response = ''
                try:
                    response_stream = await chat_session.send_message_streaming_async(current_input)
                    async for chunk in response_stream:
                        if chunk:
                            full_response += chunk
                            await emit_callback('core:agent_token', {'session_id': session_id, 'text': chunk})
                    hub.logger.debug(f'[AgentSession {session_id}] Full AI response: {full_response[:50]}...')
                except Exception as e:
                    hub.logger.error(f'[AgentSession {session_id}] AI streaming failed: {e}', exc_info=True)
                    await emit_callback('core:agent_error', {'session_id': session_id, 'code': 'AI_STREAM_ERROR', 'message': f'Error during AI streaming: {e}'})
            hub.logger.debug(f'[AgentSession {session_id}] Waiting for next user input...')
            next_input_data = await input_queue.get()
            if next_input_data is None:
                hub.logger.info(f'[AgentSession {session_id}] Received stop signal.')
                break
            current_input = next_input_data.get('text')
            tool_response = next_input_data.get('tool')
            if tool_response:
                hub.logger.info(f"[AgentSession {session_id}] Received tool response: {tool_response.get('name')}")
                current_input = f'Tool Response: {json.dumps(tool_response)}'
            elif not current_input:
                hub.logger.debug(f'[AgentSession {session_id}] Received empty input, waiting again.')
                current_input = None
                continue
    except asyncio.CancelledError:
        hub.logger.info(f'[AgentSession {session_id}] Task was cancelled.')
        try:
            await emit_callback('core:agent_status', {'session_id': session_id, 'phase': 'cancelled'})
            await emit_callback('core:agent_done', {'session_id': session_id, 'outcome': 'cancelled'})
        except Exception:
            pass
    except Exception as e:
        hub.logger.error(f'[AgentSession {session_id}] Session loop CRASHED: {e}', exc_info=True)
        try:
            await emit_callback('core:agent_error', {'session_id': session_id, 'code': 'SESSION_CRASH', 'message': str(e)})
        except Exception as e2:
            hub.logger.error(f'[AgentSession {session_id}] FAILED TO SEND CRASH ERROR: {e2}')
    finally:
        if session_id in hub.session_locks:
            async with hub.session_locks[session_id]:
                if session_id in hub.sessions:
                    del hub.sessions[session_id]
            del hub.session_locks[session_id]
        hub.logger.info(f'[AgentSession {session_id}] Task finished and cleaned up.')
