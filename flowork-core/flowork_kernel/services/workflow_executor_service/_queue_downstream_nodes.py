########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\_queue_downstream_nodes.py total lines 36 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import uuid
import time
import json
import sqlite3
import multiprocessing
import asyncio
import random
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.outcome import OutcomeMeter
from flowork_kernel.analyst import Analyst, AnalystReport


async def run(hub, execution_id, finished_node_id, finished_job_id, status='DONE'):
    if not hub.db_service:
        return
    conn = hub.db_service.create_connection()
    if not conn:
        return
    try:
        await hub.execute_async('_queue_downstream_nodes_sync', conn, execution_id, finished_node_id, finished_job_id, status)
    except Exception as e:
        hub.logger.error(f'Failed to queue downstream nodes: {e}', exc_info=True)
    finally:
        conn.close()
