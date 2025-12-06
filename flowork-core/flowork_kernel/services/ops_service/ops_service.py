########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ops_service\ops_service.py total lines 97 
########################################################################

import os
import psutil
import shutil
from flask import jsonify
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.services.workflow_executor_service.workflow_executor_service import WorkflowExecutorService
from flowork_kernel.exceptions import OpsServiceError

MIN_WORKERS = int(os.getenv("CORE_MIN_WORKERS", "1"))


def get_system_vitals():

    try:
        cpu_percent = psutil.cpu_percent(interval=None)

        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_used_gb = memory.used / (1024**3)
        memory_percent = memory.percent

        disk_usage = psutil.disk_usage('/')
        disk_total_gb = disk_usage.total / (1024**3)
        disk_used_gb = disk_usage.used / (1024**3)
        disk_percent = disk_usage.percent

        process_count = len(psutil.pids())

        vitals = {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory_total_gb, 2),
                "used_gb": round(memory_used_gb, 2),
                "percent": memory_percent
            },
            "disk": {
                "total_gb": round(disk_total_gb, 2),
                "used_gb": round(disk_used_gb, 2),
                "percent": disk_percent
            },
            "process_count": process_count
        }
        return vitals

    except Exception as e:
        print(f"Error getting system vitals: {e}")
        raise OpsServiceError(f"Failed to retrieve system vitals: {e}")

def get_worker_stats(kernel_instance):

    try:
        executor: WorkflowExecutorService = Singleton.get_instance(kernel_instance, 'workflow_executor_service')
        if not executor or not executor.worker_pool:
            return {"error": "Worker pool not initialized."}

        pool_stats = executor.worker_pool.get_stats()
        return pool_stats

    except Exception as e:
        print(f"Error getting worker stats: {e}")
        raise OpsServiceError(f"Failed to retrieve worker stats: {e}")


def get_autoscaling_advice(vitals, worker_stats):

    advice = "STABLE"
    reason = "System load is nominal."

    cpu_load = vitals.get('cpu_percent', 0)
    mem_load = vitals.get('memory', {}).get('percent', 0)

    active_workers = worker_stats.get('active_workers', 0)
    pool_size = worker_stats.get('pool_size', 1)

    if cpu_load > 90 or mem_load > 85:
        advice = "SCALE_UP"
        reason = f"High system load (CPU: {cpu_load}%, Mem: {mem_load}%). "

    if pool_size > 0 and (active_workers / pool_size) > 0.8:
        advice = "SCALE_UP"
        reason = reason + f"High worker saturation ({active_workers}/{pool_size} active)."

    if cpu_load < 20 and mem_load < 40 and active_workers == 0 and pool_size > MIN_WORKERS:
        advice = "SCALE_DOWN"
        reason = f"Low system load (CPU: {cpu_load}%, Mem: {mem_load}%) and no active workers."

    return {
        "advice": advice,
        "reason": reason
    }
