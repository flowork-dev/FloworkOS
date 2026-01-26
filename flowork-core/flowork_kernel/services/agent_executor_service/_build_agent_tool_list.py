########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\_build_agent_tool_list.py total lines 34 
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


def run(hub, connected_tools: list) -> list:
    tools_for_agent = []
    if hub.app_service:
        for node_data in connected_tools:
            component_id = node_data.get('module_id')
            manifest = hub.app_service.get_manifest(component_id)
            if manifest:
                full_tool_data = {**manifest, **node_data}
                tools_for_agent.append(full_tool_data)
    tools_for_agent.append({'id': 'swarm_fan_out', 'name': 'Swarm Fan-Out (Local)', 'description': "Executes a task in parallel on *local tools* on *this* engine. 'engine_ids' is a list of *tool_ids* (e.g., ['http_fetch', 'fs_read']), 'task' is the payload for all of them.", 'is_swarm_tool': True})
    if hub.gateway_swarm_coordinator:
        tools_for_agent.append({'id': 'swarm_fan_out_gateway', 'name': 'Swarm Fan-Out (Gateway / Multi-Node)', 'description': "Executes a task in parallel on *other* engines via the Gateway. 'engine_ids' is a list of *real Engine IDs* (e.g., ['engine-id-A', 'engine-id-B']). 'task' is the payload, which *must* include the 'tool_id' you want those engines to run.", 'is_swarm_tool': True})
    return tools_for_agent
