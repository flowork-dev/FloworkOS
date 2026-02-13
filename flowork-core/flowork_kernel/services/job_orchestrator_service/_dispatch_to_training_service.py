########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\_dispatch_to_training_service.py total lines 39 
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
    """
        Manggil fungsi internal AI Training Service.
        [English Note] Rule 2: Redirecting from hardcoded Core Service to dynamic App Instance.
        """
    app_service = hub.kernel.get_service('app_service')
    svc = app_service.get_instance('apps', 'neural_trainer') if app_service else None
    if not svc:
        print('❌ Neural Trainer App not found in system!')
        return False
    payload = json.loads(job['payload'])
    try:
        if hasattr(svc, 'execute_job_direct'):
            return svc.execute_job_direct(job['job_id'], payload)
        else:
            print('⚠️ Neural Trainer using generic node interface.')
            return svc.execute(payload)
    except AttributeError:
        print('⚠️ Method execute_job_direct not implemented in Neural Trainer App.')
        return False
    except Exception as e:
        print(f'Error dispatch training: {e}')
        return False
