########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\execute_remote_swarm_task.py total lines 43 
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


async def run(hub, task_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        tool_id = task_payload.get('tool_id')
        if not tool_id:
            return {'error': "EngineError (Worker): Remote task missing 'tool_id'"}
        hub.logger.info(f"[RemoteSwarmWorker] Received task {task_payload.get('task_id')} for tool: {tool_id}")
        node_data = await hub.execute_async('_find_tool_manifest_as_node', tool_id)
        if not node_data:
            hub.logger.error(f"[RemoteSwarmWorker] Tool '{tool_id}' not found on this worker engine.")
            return {'error': f"EngineError (Worker): Tool '{tool_id}' not found on this worker engine."}
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, hub.workflow_executor.execute_workflow_synchronous, {node_data['id']: node_data}, {}, task_payload, hub.logger.debug, lambda a, b, c: hub.logger.debug(f'[RemoteSwarm] Tool Status: {b} - {c}'), f"remote_swarm_task_{task_payload.get('task_id')}", 'EXECUTE', None)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, dict) and 'payload' in result:
            hub.logger.info(f"[RemoteSwarmWorker] Task {task_payload.get('task_id')} completed successfully.")
            return result['payload']
        hub.logger.warning(f'[RemoteSwarmWorker] Tool {tool_id} ran but returned invalid structure.')
        return {'error': 'EngineError (Worker): Tool executed but returned invalid structure.'}
    except Exception as e:
        hub.logger.error(f"[RemoteSwarmWorker] Task {task_payload.get('task_id')} FAILED: {e}", exc_info=True)
        return {'error': f'EngineError (Worker): {e}'}
