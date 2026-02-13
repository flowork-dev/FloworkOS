########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\start_task.py total lines 30 
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


async def run(hub, instruction: str, tools: List[str], user_id: str) -> str:
    """
        Memulai task agent secara asynchronous (Fire-and-forget).
        """
    task_id = str(uuid.uuid4())
    hub.logger.info(f'[AgentExecutor] Starting Ad-hoc Task {task_id} for user {user_id}. Instruction: {instruction[:50]}...')
    hub.active_tasks[task_id] = {'status': 'running', 'instruction': instruction, 'logs': [], 'result': None}
    asyncio.create_task(await hub.execute_async('_run_agent_loop', task_id, instruction, tools))
    return task_id
