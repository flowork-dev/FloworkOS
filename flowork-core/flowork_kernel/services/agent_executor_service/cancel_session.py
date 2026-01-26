########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\cancel_session.py total lines 32 
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
    session_info = hub.sessions.get(session_id)
    if session_info and session_info.get('task'):
        try:
            session_info['task'].cancel()
            hub.logger.info(f'[AgentExecutor] Cancellation request sent to session task {session_id}.')
        except Exception as e:
            hub.logger.error(f'[AgentExecutor] Error during task cancellation for {session_id}: {e}')
    else:
        hub.logger.warning(f'[AgentExecutor] Could not cancel session {session_id}: Task not found.')
