########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\_run_agent_loop.py total lines 45 
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


async def run(hub, task_id: str, instruction: str, tools: List[str]):
    """
        [PHASE 3] The Brain Loop (ReAct Pattern Sederhana)
        """
    try:
        hub.logger.info(f'[Task {task_id}] Thinking...')
        prompt = f"""\n            You are a helpful AI Agent.\n            User Request: {instruction}\n\n            Available Tools: {', '.join(tools)}\n\n            Thought Process:\n            1. Analyze the request.\n            2. Pick a tool if needed.\n            3. Output JSON: {{ "action": "tool_name", "args": {{...}} }} OR {{ "action": "finish", "response": "..." }}\n            """
        await asyncio.sleep(1)
        action = 'finish'
        response_text = f"I have processed your request: '{instruction}'. Since I am in Beta, I simulated the execution using tools: {tools}."
        if 'email' in instruction.lower() and 'email_sender' in tools:
            action = 'email_sender'
            hub.logger.info(f'[Task {task_id}] Executing Tool: email_sender')
            await asyncio.sleep(1)
            response_text = 'Email sent successfully (Simulated).'
        hub.active_tasks[task_id]['status'] = 'completed'
        hub.active_tasks[task_id]['result'] = response_text
        if hub.event_bus:
            hub.event_bus.publish('AGENT_TASK_UPDATE', {'task_id': task_id, 'status': 'completed', 'output': response_text})
        hub.logger.info(f'[Task {task_id}] Finished. Result: {response_text}')
    except Exception as e:
        hub.logger.error(f'[Task {task_id}] Failed: {e}', exc_info=True)
        hub.active_tasks[task_id]['status'] = 'failed'
        hub.active_tasks[task_id]['error'] = str(e)
