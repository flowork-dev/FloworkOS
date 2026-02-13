########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel_logic\request_manual_approval.py total lines 30 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import logging
import threading
import queue
import importlib
import datetime
import asyncio
from typing import List, Dict, Any, Callable
import requests
from packaging import version
from flowork_kernel.exceptions import PermissionDeniedError


def run(hub, module_id: str, message: str, callback_func: Callable):
    log_message = f"Manual approval requested by module '{module_id}': {message}"
    hub.execute_sync('write_to_log', log_message, 'WARN')
    if hub.event_bus:
        event_data = {'module_id': module_id, 'message': message, 'workflow_context_id': hub.execute_sync('get_service', 'workflow_executor_service').get_current_context_id()}
        hub.event_bus.publish('MANUAL_APPROVAL_REQUESTED', event_data, publisher_id=module_id)
    else:
        hub.execute_sync('write_to_log', 'EventBus not available, cannot broadcast approval request.', 'ERROR')
