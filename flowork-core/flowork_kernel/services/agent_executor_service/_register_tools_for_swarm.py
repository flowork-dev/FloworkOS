########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\_register_tools_for_swarm.py total lines 49 
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


def run(hub, swarm_registry: LocalSwarmRegistry, tools_list: list, base_payload: dict, workflow_context_id: str):
    for node_data in tools_list:
        tool_id = node_data.get('module_id')
        if not tool_id:
            continue

        def create_tool_handler(node_info: dict, tool_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:

            def _tool_handler(task_payload: Dict[str, Any]) -> Dict[str, Any]:
                hub.logger.info(f"[SwarmWorker] Executing tool '{tool_name}' via local swarm...")
                try:
                    payload_for_tool = base_payload.copy()
                    if 'data' not in payload_for_tool or not isinstance(payload_for_tool.get('data'), dict):
                        payload_for_tool['data'] = {}
                    payload_for_tool['data'].update(task_payload)
                    result = hub.workflow_executor.execute_workflow_synchronous(nodes={node_info['id']: node_info}, connections={}, initial_payload=payload_for_tool, logger=hub.logger.debug, status_updater=lambda a, b, c: hub.logger.debug(f'[SwarmWorker] Tool Status: {b} - {c}'), workflow_context_id=f'{workflow_context_id}_swarm_task', mode='EXECUTE', job_status_updater=None)
                    if isinstance(result, Exception):
                        raise result
                    if isinstance(result, dict) and 'payload' in result:
                        return result['payload']
                    return {'error': 'Tool executed but returned invalid structure.'}
                except Exception as e:
                    hub.logger.error(f"[SwarmWorker] Tool '{tool_name}' failed: {e}", exc_info=True)
                    return {'error': str(e)}
            return _tool_handler
        tool_handler_func = create_tool_handler(node_data, tool_id)
        swarm_registry.register(tool_id, tool_handler_func)
        hub.logger.debug(f"[R6] Registered tool '{tool_id}' with LocalSwarmRegistry.")
