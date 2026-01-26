########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\stop.py total lines 45 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

import socketio
import os
import asyncio
import logging
import uuid
import json
import multiprocessing
import requests
import time
import sqlite3
import threading
import traceback
from dotenv import load_dotenv
from typing import Dict, Any
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.router import StrategyRouter
from flowork_kernel.fac_enforcer import FacRuntime
from .handlers.system_handler import SystemHandler
from .handlers.workflow_handler import WorkflowHandler
from .handlers.data_handler import DataHandler
from .handlers.component_handler import ComponentHandler
from .handlers.ai_handler import AIHandler

CURRENT_PAYLOAD_VERSION = 2


async def run(hub):
    hub.is_running = False
    if hub.sio:
        await hub.sio.disconnect()

    @hub.sio.on('*', namespace='/engine-socket')
    async def catch_all(event, data):
        known_events = ['connect', 'auth_success', 'auth', 'auth_failed', 'disconnect', 'request_presets_list', 'save_preset', 'request_variables', 'engine_ready', 'engine_vitals_update', 'forward_event_to_gui', 'execute_workflow', 'request_components_list', 'request_settings', 'save_settings', 'update_variable', 'delete_variable', 'request_prompts_list', 'update_prompt', 'delete_prompt', 'request_local_models', 'start_training_job', 'request_training_job_status', 'request_datasets_list', 'load_dataset_data', 'create_dataset', 'add_dataset_data', 'delete_dataset', 'update_dataset_row', 'delete_dataset_row', 'install_component', 'uninstall_component', 'gw:start_session', 'gw:cancel_session', 'gw:agent_input', 'stop_workflow', 'pause_workflow', 'gateway:execute_swarm_task', 'gateway:swarm_task_result', 'core:request_swarm_task', 'core:swarm_task_result', 'delete_preset', 'request_load_preset', 'response_load_preset', 'execute_standalone_node', 'filesystem_list_request', 'system_browse', 'gw:dispatch_event', 'db_proxy']
        if event not in known_events:
            hub.logger.warning(f"Received unhandled event '{event}' in /engine-socket namespace.")
