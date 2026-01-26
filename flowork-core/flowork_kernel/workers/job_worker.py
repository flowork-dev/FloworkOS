########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\workers\job_worker.py total lines 314 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

print("!!! [WORKER SPY] FILE EXECUTION STARTED.", flush=True)

import os
import logging
import time
import json
import sqlite3
import random
import uuid
import multiprocessing
import sys
import asyncio
import traceback
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

MAX_DB_RETRIES = 5
POLL_INTERVAL_SECONDS = 0.5

class MockService:
    def __init__(self, kernel, service_id):
        self.kernel = kernel
        self.service_id = service_id

class ContextEventBus:
    def __init__(self, real_bus, user_id):
        self.real_bus = real_bus
        self.user_id = user_id
    def subscribe(self, p, s, c): return self.real_bus.subscribe(p, s, c)
    def unsubscribe(self, s): return self.real_bus.unsubscribe(s)
    def publish(self, n, p, pub="SYSTEM"):
        if isinstance(p, dict) and self.user_id: p['_target_user_id'] = self.user_id
        return self.real_bus.publish(n, p, pub)

def _safe_json_dumps(data_obj):
    try: return json.dumps(data_obj, default=str)
    except: return None

def _db_retry_wrapper(db_conn, func, *args, **kwargs):
    for attempt in range(MAX_DB_RETRIES):
        try: return func(db_conn, *args, **kwargs)
        except sqlite3.Error as e:
            if 'locked' in str(e) or 'busy' in str(e):
                time.sleep(random.uniform(0.1, 0.5) * (2 ** attempt))
            else:
                raise
        except Exception: raise
    return None

def _db_atomic_claim_job(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        cursor.execute("SELECT job_id, execution_id, node_id, input_data, workflow_id, user_id FROM Jobs WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT 1")
        row = cursor.fetchone()
        if row:
            job_id, eid, nid, ind, wid, uid = row
            cursor.execute("UPDATE Jobs SET status = 'RUNNING', started_at = CURRENT_TIMESTAMP WHERE job_id = ?", (job_id,))
            db_conn.commit()
            return {'job_id': job_id, 'execution_id': eid, 'node_id': nid, 'input_data': ind, 'workflow_id': wid, 'user_id': uid}
        db_conn.commit()
        return None
    except Exception as e:
        db_conn.rollback()
        raise e

def execute_node_logic(job, node_id, module_id, config_json, input_data, Singleton):
    pid = os.getpid()
    job_owner_id = job.get('user_id')

    try:
        node_manager = Singleton.get_instance("node_manager_service")
        if not node_manager: raise Exception("NodeManagerService NULL - Neural logic source missing.")

        module_instance = node_manager.get_node_instance(module_id)

        if not module_instance:
            raise Exception(f"Neuron Logic '{module_id}' not found in registry.")

        combined_inputs = {**config_json, **(input_data.get('data', {}) if isinstance(input_data, dict) else {})}

        real_eb = Singleton.get_instance("event_bus")
        event_bus = ContextEventBus(real_eb, job_owner_id) if real_eb else None

        if module_instance:
            setattr(module_instance, 'event_bus', event_bus)

            module_instance.context = {
                "job_id": job.get('job_id'),
                "workflow_id": job.get('workflow_id'),
                "execution_id": job.get('execution_id'),
                "user_context": {"user_id": job_owner_id},
                "kernel": Singleton.get_instance("kernel_stub")
            }

        print(f"[WORKER-{pid}] 🏃 Executing Logic: {module_id}", flush=True)

        if asyncio.iscoroutinefunction(module_instance.execute):
            result = asyncio.run(module_instance.execute(combined_inputs))
        else:
            result = module_instance.execute(combined_inputs)

        print(f"[WORKER-{pid}] 🏁 Logic Finished. Result Type: {type(result)}", flush=True)

        active_port = "success"
        if isinstance(result, tuple) and len(result) == 2:
             active_port = result[1]
             result = result[0]

        if isinstance(result, dict) and len(result) == 1 and ("success" in result or "error" in result):
             active_port = list(result.keys())[0]
             result = result[active_port]

        new_clean_payload = {"data": result, "history": input_data.get('history', []) if isinstance(input_data, dict) else []}
        return new_clean_payload, active_port

    except Exception as e:
        traceback.print_exc()
        return e, "error"

def _db_get_downstream_nodes(db_conn, workflow_id, source_node_id, active_port):
    cursor = db_conn.cursor()
    SUCCESS_PORTS = ['success', 'output', 'default', 'source', 'out', 'main', 'result']

    if active_port in SUCCESS_PORTS:
         query = "SELECT target_node_id FROM Edges WHERE workflow_id = ? AND source_node_id = ? AND (source_handle IN ('success', 'output', 'default', 'source', 'out', 'main', 'result') OR source_handle IS NULL OR source_handle = '')"
         params = (workflow_id, source_node_id)
    else:
         query = "SELECT target_node_id FROM Edges WHERE workflow_id = ? AND source_node_id = ? AND source_handle = ?"
         params = (workflow_id, source_node_id, active_port)

    cursor.execute(query, params)
    return [row[0] for row in cursor.fetchall()]

def _db_get_node_details(db_conn, node_id):
    cursor = db_conn.cursor()
    cursor.execute("SELECT node_type, config_json FROM Nodes WHERE node_id = ?", (node_id,))
    row = cursor.fetchone()
    return (row[0], json.loads(row[1]) if row[1] else {}) if row else (None, None)

def _db_finish_job(db_conn, job_id, eid, uid, wid, downstream, output):
    cursor = db_conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        safe_out = _safe_json_dumps(output)
        cursor.execute("UPDATE Jobs SET status = 'DONE', finished_at = CURRENT_TIMESTAMP, output_data = ? WHERE job_id = ?", (safe_out, job_id))

        for n in downstream:
            cursor.execute("INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), eid, n, 'PENDING', safe_out, wid, uid))

        db_conn.commit()
        return len(downstream) > 0
    except:
        db_conn.rollback()
        raise

def _db_fail_job(db_conn, job_id, error):
    cursor = db_conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        cursor.execute("UPDATE Jobs SET status = 'FAILED', finished_at = CURRENT_TIMESTAMP, error_message = ? WHERE job_id = ?", (str(error), job_id))
        db_conn.commit()
    except: db_conn.rollback()

def worker_process(db_path: str, project_root: str, event_ipc_queue: multiprocessing.Queue):
    if project_root not in sys.path: sys.path.insert(0, project_root)
    try:
        from flowork_kernel.singleton import Singleton
        from flowork_kernel.services.database_service.database_service import DatabaseService
        from flowork_kernel.services.app_manager_service.app_manager_service import AppService
        from flowork_kernel.services.node_manager_service.node_manager_service import NodeManagerService
        from flowork_kernel.services.event_bus_service.event_bus_service import EventBusService

        class WorkerKernelStub:
            def __init__(self):
                self.project_root_path = project_root
                self.app_path = os.path.join(project_root, "app")
                self.data_path = os.path.join(project_root, "data")
                self.globally_disabled_components = []

            def get_service(self, sid):
                return Singleton.get_instance(sid)

            def write_to_log(self, message, level="INFO", source="WorkerStub", **kwargs):
                print(f"[{level}] [{source}] {message}", flush=True)

        stub = WorkerKernelStub()
        Singleton.set_instance("kernel_stub", stub)

        app_svc = AppService(stub, "app_service")
        app_svc.start()
        Singleton.set_instance("app_service", app_svc)

        node_manager = NodeManagerService(stub, "node_manager_service")
        node_manager.start()
        Singleton.set_instance("node_manager_service", node_manager)

        eb_svc = EventBusService(stub, "event_bus", ipc_queue=event_ipc_queue)
        Singleton.set_instance("event_bus", eb_svc)

        db_svc = DatabaseService(stub, "worker_db_service")
        db_svc.db_path = db_path
        db_conn = db_svc.create_connection()

        if not db_conn:
            print("❌ [WORKER] Failed to connect to DB!", flush=True)
            return

        print("✅ [WORKER] Ready to process jobs.", flush=True)

    except:
        traceback.print_exc()
        return

    while True:
        job = None
        try:
            job = _db_retry_wrapper(db_conn, _db_atomic_claim_job)
            if job is None:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            print(f"👷 [WORKER] Claimed Job: {job['job_id']} (Node: {job['node_id']})", flush=True)

            eb = Singleton.get_instance("event_bus")

            if eb:
                payload = {
                    "execution_id": job['execution_id'],
                    "job_id": job['job_id'],
                    "node_id": job['node_id'],
                    "status": "RUNNING",
                    "timestamp": time.time(),
                    "_target_user_id": job['user_id']
                }
                eb.publish("WORKFLOW_EXECUTION_UPDATE", payload, publisher_id="job_worker")
                eb.publish("node_status_update", payload, publisher_id="job_worker")

            input_d = json.loads(job['input_data']) if job['input_data'] else {}
            m_id, cfg = _db_retry_wrapper(db_conn, _db_get_node_details, job['node_id'])

            if not m_id:
                raise Exception(f"Node {job['node_id']} not found.")

            out_d, port = execute_node_logic(job, job['node_id'], m_id, cfg, input_d, Singleton)

            if isinstance(out_d, Exception):
                raise out_d

            print(f"💾 [WORKER] Logic Done. Updating DB... (Port: {port})", flush=True)

            down = _db_retry_wrapper(db_conn, _db_get_downstream_nodes, job['workflow_id'], job['node_id'], port)
            has_next = _db_retry_wrapper(db_conn, _db_finish_job, job['job_id'], job['execution_id'], job['user_id'], job['workflow_id'], down, out_d)

            print(f"📣 [WORKER] DB Updated. Publishing Success Events...", flush=True)

            if eb:
                success_payload = {
                    "node_id": job['node_id'],
                    "status": "SUCCESS",
                    "execution_id": job['execution_id'],
                    "job_id": job['job_id'],
                    "timestamp": time.time(),
                    "_target_user_id": job['user_id'],
                    "output": out_d
                }
                eb.publish("node_status_update", success_payload, publisher_id="job_worker")

                if not has_next:
                    eb.publish("WORKFLOW_EXECUTION_UPDATE", {
                        "execution_id": job['execution_id'],
                        "status": "COMPLETED", # Sinyal sakti buat GUI
                        "timestamp": time.time(),
                        "_target_user_id": job['user_id']
                    }, publisher_id="job_worker")

                eb.publish("APP_JOB_FINISHED", {
                    "app_id": m_id,
                    "pid": job['job_id'],
                    "status": "completed",
                    "user_id": job['user_id']
                })

            print(f"✅ [WORKER] Job {job['job_id']} FULLY COMPLETED.", flush=True)

        except Exception as e:
            print(f"❌ [WORKER] JOB FAILED: {e}", flush=True)
            if job:
                _db_retry_wrapper(db_conn, _db_fail_job, job['job_id'], str(e))
                eb = Singleton.get_instance("event_bus")
                if eb:
                    eb.publish("node_status_update", {
                        "node_id": job['node_id'],
                        "status": "FAILED",
                        "execution_id": job['execution_id'],
                        "error": str(e),
                        "_target_user_id": job['user_id']
                    }, publisher_id="job_worker")

                    eb.publish("WORKFLOW_EXECUTION_UPDATE", {
                        "execution_id": job['execution_id'],
                        "status": "FAILED",
                        "error": str(e),
                        "_target_user_id": job['user_id']
                    }, publisher_id="job_worker")
            time.sleep(POLL_INTERVAL_SECONDS)
