########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\_get_tools_prompt_from_manifests.py total lines 26 
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


def run(hub, tools_for_agent: list) -> str:
    tools_list = []
    for manifest in tools_for_agent:
        tools_list.append(f"- tool_id: {manifest.get('id')}\n   name: {manifest.get('name')}\n   description: {manifest.get('description')}")
    return '\n'.join(tools_list)
