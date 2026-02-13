########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\_execute_job.py total lines 45 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import json
import time
import uuid
import threading
import traceback
import asyncio


def run(hub, job):
    job_id = job['job_id']
    job_type = job['job_type']
    print(f'[JobOrchestrator] 🚦 Starting Job: {job_id} ({job_type})')
    hub.execute_sync('_update_job_status', job_id, 'RUNNING')
    if job['resource_req'] == 'GPU':
        hub.resource_status['GPU'] = 'BUSY'
    try:
        success = False
        error_msg = None
        if job_type.startswith('TRAINING_'):
            success = hub.execute_sync('_dispatch_to_training_service', job)
        elif job_type.startswith('INFERENCE_') or job_type == 'CHAT':
            success = hub.execute_sync('_dispatch_to_ai_service', job)
        elif job_type.startswith('WORKFLOW'):
            success = hub.execute_sync('_dispatch_to_workflow_service', job)
        else:
            error_msg = f'Unknown job type: {job_type}'
        if not success and (not error_msg):
            error_msg = 'Worker returned failure'
        status = 'COMPLETED' if success else 'FAILED'
        hub.execute_sync('_update_job_status', job_id, status, error=error_msg)
    except Exception as e:
        traceback.print_exc()
        hub.execute_sync('_update_job_status', job_id, 'FAILED', error=str(e))
    finally:
        if job['resource_req'] == 'GPU':
            hub.resource_status['GPU'] = 'IDLE'
        print(f'[JobOrchestrator] 🏁 Job {job_id} Finished. GPU Unlocked.')
