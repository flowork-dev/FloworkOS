########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\workers\job_worker.py total lines 592 
########################################################################

print("!!! [WORKER SPY] FILE EXECUTION STARTED. Python interpreter is reading this file.", flush=True)

import os
print("!!! [WORKER SPY] Import 'os' OK.", flush=True)

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

print("!!! [WORKER SPY] Basic imports (sys, logging, json, etc.) OK.", flush=True)

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

    def subscribe(self, event_pattern: str, subscriber_id: str, callback: callable):
        return self.real_bus.subscribe(event_pattern, subscriber_id, callback)

    def unsubscribe(self, subscriber_id: str):
        return self.real_bus.unsubscribe(subscriber_id)

    def publish(self, event_name: str, payload: dict, publisher_id: str = "SYSTEM"):
        if isinstance(payload, dict) and self.user_id:
            payload['_target_user_id'] = self.user_id

        return self.real_bus.publish(event_name, payload, publisher_id)

def _safe_json_dumps(data_obj):
    if data_obj is None:
        return None
    try:
        return json.dumps(data_obj, default=str)
    except (TypeError, ValueError) as e:
        if 'Circular reference' in str(e):
            pid = os.getpid()
            logging.warning(f"[Worker PID {pid}] Detected circular reference in job output. Failing job.")
            raise ValueError(f"Circular reference detected in node output. Cannot save to DB. Error: {e}")
        else:
            print(f"!!! [SPY] JSON DUMPS ERROR: {e}. Data type: {type(data_obj)}", flush=True)
            raise e

def _db_retry_wrapper(db_conn, func, *args, **kwargs):
    pid = os.getpid()
    for attempt in range(MAX_DB_RETRIES):
        try:
            return func(db_conn, *args, **kwargs)
        except sqlite3.Error as e:
            if 'locked' in str(e) or 'busy' in str(e):
                logging.warning(f"[Worker PID {pid}] DB Busy/Locked on attempt {attempt+1}/{MAX_DB_RETRIES}. Retrying...")
                if attempt == MAX_DB_RETRIES - 1:
                    logging.critical(f"[Worker PID {pid}] DB failed permanently after {MAX_DB_RETRIES} retries.")
                    raise
                sleep_time = random.uniform(0.1, 0.5) * (2 ** attempt)
                time.sleep(sleep_time)
            else:
                logging.error(f"[Worker PID {pid}] Unhandled DB Error: {e}", exc_info=True)
                print(f"!!! [SPY] UNHANDLED DB ERROR in wrapper: {e}", flush=True)
                raise
        except Exception as e:
            logging.error(f"[Worker PID {pid}] Non-DB Error in wrapper: {e}", exc_info=True)
            print(f"!!! [SPY] Error in DB Wrapper: {e}", flush=True)
            traceback.print_exc()
            raise
    return None

def _db_atomic_claim_job(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        cursor.execute(
            "SELECT job_id, execution_id, node_id, input_data, workflow_id, user_id FROM Jobs "
            "WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            job_id, execution_id, node_id, input_data, workflow_id, user_id = row
            cursor.execute(
                "UPDATE Jobs SET status = 'RUNNING', started_at = CURRENT_TIMESTAMP "
                "WHERE job_id = ?", (job_id,)
            )
            db_conn.commit()
            print(f"!!! [SPY] Job CLAIMED: {job_id} for Node: {node_id}", flush=True)
            return {
                'job_id': job_id,
                'execution_id': execution_id,
                'node_id': node_id,
                'input_data': input_data,
                'workflow_id': workflow_id,
                'user_id': user_id
            }
        else:
            db_conn.commit()
            return None
    except Exception as e:
        db_conn.rollback()
        raise e

def execute_node_logic(job, node_id, module_id, config_json, input_data, Singleton):
    pid = os.getpid()
    logging.info(f"[Worker PID {pid}]: EXECUTING node {node_id} (Module ID: {module_id})...")
    print(f"!!! [SPY] Starting execute_node_logic for {module_id}", flush=True)

    job_owner_id = job.get('user_id')

    try:
        ModuleManagerService = Singleton.get_instance("ModuleManagerService_class")
        PluginManagerService = Singleton.get_instance("PluginManagerService_class")
        ToolsManagerService = Singleton.get_instance("ToolsManagerService_class")

        module_manager = Singleton.get_instance(ModuleManagerService)
        plugin_manager = Singleton.get_instance(PluginManagerService)
        tools_manager = Singleton.get_instance(ToolsManagerService)

        if not module_manager or not plugin_manager or not tools_manager:
            raise Exception("Component Managers not found in worker Singleton.")

        module_instance = None
        if module_id in module_manager.loaded_modules:
            module_instance = module_manager.get_instance(module_id)
        elif module_id in plugin_manager.loaded_plugins:
            module_instance = plugin_manager.get_instance(module_id)
        elif module_id in tools_manager.loaded_tools:
            module_instance = tools_manager.get_instance(module_id)

        if not module_instance:
            raise Exception(f"Component instance for '{module_id}' could not be loaded from any manager.")

        real_event_bus = Singleton.get_instance("event_bus")

        if not real_event_bus:
            logging.error(f"[Worker PID {pid}]: CRITICAL - Could not get EventBus from Singleton. LOGS AND POPUPS WILL FAIL.")
            event_bus = None
        else:
             event_bus = ContextEventBus(real_event_bus, job_owner_id)

        if module_instance:
            setattr(module_instance, 'event_bus', event_bus)
            if hasattr(module_instance, 'services') and isinstance(module_instance.services, dict):
                module_instance.services['event_bus'] = event_bus

        def _real_status_updater(message, log_level):
            try:
                log_entry = {
                    "job_id": job.get('execution_id'),
                    "node_id": job.get('node_id'),
                    "level": log_level,
                    "message": message,
                    "source": module_id,
                    "ts": datetime.now().isoformat(),
                    "_target_user_id": job_owner_id
                }

                print(f"[Worker PID {pid}] [STATUS UPDATE] {message}", flush=True)

                if event_bus:
                    event_bus.publish("WORKFLOW_LOG_ENTRY", log_entry, publisher_id=module_id)
                else:
                    logging.warning(f"[Worker PID {pid}] Cannot publish WORKFLOW_LOG_ENTRY, event_bus is None.")
            except Exception as e:
                logging.error(f"Failed to publish log event: {e}")

        logging.info(f"[Worker PID {pid}] Calling module_instance.execute() for {module_id}...")
        print(f"!!! [SPY] INVOKING .execute() on {module_id}...", flush=True)

        try:
            if asyncio.iscoroutinefunction(module_instance.execute):
                result = asyncio.run(module_instance.execute(
                    payload=input_data,
                    config=config_json,
                    status_updater=_real_status_updater,
                    mode='EXECUTE'
                ))
            else:
                result = module_instance.execute(
                    payload=input_data,
                    config=config_json,
                    status_updater=_real_status_updater,
                    mode='EXECUTE'
                )
        except Exception as exec_err:
            print(f"!!! [SPY] CRITICAL: Exception inside module code {module_id}: {exec_err}", flush=True)
            traceback.print_exc()
            raise exec_err

        logging.info(f"[Worker PID {pid}] module_instance.execute() finished for {module_id}.")
        print(f"!!! [SPY] Execution Finished. Analyzing Result...", flush=True)

        new_clean_payload = {}
        active_port = "success" # Default port is success if not specified

        if isinstance(result, dict):
            if 'payload' in result and isinstance(result['payload'], dict):
                 raw_payload = result['payload']

                 if 'data' in raw_payload:
                     new_clean_payload['data'] = raw_payload.get('data')
                     new_clean_payload['history'] = raw_payload.get('history', [])
                 else:
                     new_clean_payload['data'] = raw_payload
                     new_clean_payload['history'] = input_data.get('history', [])

            elif 'data' in result and 'history' in result:
                new_clean_payload['data'] = result.get('data')
                new_clean_payload['history'] = result.get('history', [])

            else:
                new_clean_payload['data'] = result
                new_clean_payload['history'] = input_data.get('history', [])

            if "output_name" in result:
                active_port = result["output_name"]
            elif "error" in result:
                active_port = "failure"
        else:
            new_clean_payload['data'] = result
            new_clean_payload['history'] = input_data.get('history', [])

        if "start" in module_id.lower() or "trigger" in module_id.lower():
             if active_port == "success":
                 active_port = "output"

        logging.info(f"[Worker PID {pid}]: FINISHED node {node_id}. Active Port: {active_port}")
        print(f"!!! [SPY] NODE DONE. Active Port determined: '{active_port}'", flush=True)
        return new_clean_payload, active_port

    except Exception as e:
        logging.error(f"[Worker PID {pid}]: FAILED node {node_id}. Error: {e}", exc_info=True)
        print(f"!!! [SPY] GENERIC ERROR in execute_node_logic: {e}", flush=True)
        traceback.print_exc()
        return e, "error"

def _db_get_downstream_nodes(db_conn, workflow_id, source_node_id, active_port):
    """
    (English Hardcode) Fetches downstream nodes connected to the specific active_port.
    INTELLIGENT ROUTING LOGIC ADDED.
    """
    pid = os.getpid()
    try:
        cursor = db_conn.cursor()

        logging.info(f"[Worker {pid}] Routing Check: Node {source_node_id} finished with port '{active_port}'")
        print(f"!!! [SPY] ROUTING CHECK -> Workflow: {workflow_id}, Source: {source_node_id}, Port: {active_port}", flush=True)

        SUCCESS_PORTS = ['success', 'output', 'default', 'source', 'out', 'main', 'result']

        if active_port in SUCCESS_PORTS:
             query = """
                SELECT target_node_id, source_handle
                FROM Edges
                WHERE workflow_id = ?
                  AND source_node_id = ?
                  AND (
                      source_handle IN ('success', 'output', 'default', 'source', 'out', 'main', 'result')
                      OR source_handle IS NULL
                      OR source_handle = ''
                      OR (source_handle NOT LIKE '%error%' AND source_handle NOT LIKE '%fail%')
                  )
             """
             params = (workflow_id, source_node_id)
        else:
             query = """
                SELECT target_node_id, source_handle
                FROM Edges
                WHERE workflow_id = ?
                  AND source_node_id = ?
                  AND source_handle = ?
             """
             params = (workflow_id, source_node_id, active_port)

        print(f"!!! [SPY] Executing SQL for Routing...", flush=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()

        print(f"!!! [SPY] DB Returned {len(rows)} edges: {rows}", flush=True)

        found_nodes = [row[0] for row in rows]
        logging.info(f"[Worker {pid}] Routing Result: Found {len(found_nodes)} downstream nodes: {found_nodes}")
        print(f"!!! [SPY] Final Downstream Nodes: {found_nodes}", flush=True)
        return found_nodes

    except Exception as e:
        logging.error(f"[Worker PID {pid}]: Failed to get downstream nodes for {source_node_id} (Port: {active_port}): {e}")
        print(f"!!! [SPY] ROUTING ERROR: {e}", flush=True)
        raise

def _db_get_node_details(db_conn, node_id):
    pid = os.getpid()
    try:
        cursor = db_conn.cursor()
        query = "SELECT node_type, config_json FROM Nodes WHERE node_id = ?"
        cursor.execute(query, (node_id,))
        row = cursor.fetchone()
        if row:
            return row[0], json.loads(row[1]) if row[1] else {}
        return None, None
    except Exception as e:
        logging.error(f"[Worker PID {pid}]: Failed to get node details for {node_id}: {e}")
        raise

def _db_finish_job(db_conn, job_id, execution_id, user_id, workflow_id, downstream_nodes, output_data):
    print(f"!!! [SPY] Finishing Job {job_id}. Downstream: {downstream_nodes}. Serializing output...", flush=True)
    cursor = db_conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        safe_output_json = _safe_json_dumps(output_data)
        print(f"!!! [SPY] Output serialized (len: {len(safe_output_json) if safe_output_json else 0}). Updating DB...", flush=True)

        cursor.execute(
            "UPDATE Jobs SET status = 'DONE', finished_at = CURRENT_TIMESTAMP, output_data = ? "
            "WHERE job_id = ?",
            (safe_output_json, job_id)
        )

        jobs_to_insert = []
        for next_node_id in downstream_nodes:
            new_job_id = str(uuid.uuid4())
            jobs_to_insert.append((
                new_job_id,
                execution_id,
                next_node_id,
                'PENDING',
                safe_output_json,
                workflow_id,
                user_id
            ))

        if jobs_to_insert:
            print(f"!!! [SPY] Inserting {len(jobs_to_insert)} NEW JOBS into DB...", flush=True)
            cursor.executemany(
                "INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                jobs_to_insert
            )

        db_conn.commit()
        print(f"!!! [SPY] Transaction COMMITTED. Job {job_id} is officially DONE.", flush=True)

        if downstream_nodes:
            logging.info(f"[Worker PID {os.getpid()}] Job {job_id} DONE. Queued {len(jobs_to_insert)} downstream jobs for: {downstream_nodes}")
        else:
            cursor.execute("SELECT COUNT(*) FROM Jobs WHERE execution_id = ? AND status IN ('PENDING', 'RUNNING')", (execution_id,))
            remaining = cursor.fetchone()[0]
            if remaining == 0:
                 logging.info(f"[Worker PID {os.getpid()}] Job {job_id} DONE. No downstream nodes. Workflow Execution {execution_id} seems COMPLETE.")
                 print(f"!!! [SPY] WORKFLOW COMPLETE DETECTED. No remaining jobs.", flush=True)
            else:
                 logging.info(f"[Worker PID {os.getpid()}] Job {job_id} DONE. No direct downstream, but {remaining} other jobs pending/running.")

        return len(jobs_to_insert) > 0
    except Exception as e:
        db_conn.rollback()
        logging.error(f"[Worker PID {os.getpid()}] CRITICAL: Failed to finish job {job_id} or queue downstream jobs: {e}", exc_info=True)
        print(f"!!! [SPY] DB FINISH ERROR: {e}", flush=True)
        traceback.print_exc()
        raise
    return False

def _db_fail_job(db_conn, job_id, error_message):
    cursor = db_conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        cursor.execute(
            "UPDATE Jobs SET status = 'FAILED', finished_at = CURRENT_TIMESTAMP, error_message = ? "
            "WHERE job_id = ?",
            (str(error_message), job_id)
        )
        db_conn.commit()
        logging.error(f"[Worker PID {os.getpid()}] Job {job_id} FAILED. Status marked in DB.")
    except Exception as e:
        db_conn.rollback()
        logging.critical(f"[Worker PID {os.getpid()}] CRITICAL: Failed to mark job {job_id} as FAILED in DB: {e}", exc_info=True)
        raise

def worker_process(db_path: str, project_root: str, event_ipc_queue: multiprocessing.Queue):
    pid = os.getpid()
    print(f"!!! [WORKER SPY] PID {pid} ALIVE. DB PATH: {db_path} !!!", flush=True)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from flowork_kernel.singleton import Singleton
        from flowork_kernel.services.database_service.database_service import DatabaseService
        from flowork_kernel.kernel_logic import Kernel
        from flowork_kernel.services.module_manager_service.module_manager_service import ModuleManagerService
        from flowork_kernel.services.plugin_manager_service.plugin_manager_service import PluginManagerService
        from flowork_kernel.services.tools_manager_service.tools_manager_service import ToolsManagerService
        from flowork_kernel.services.ai_provider_manager_service.ai_provider_manager_service import AIProviderManagerService
        from flowork_kernel.services.preset_manager_service.preset_manager_service import PresetManagerService
        from flowork_kernel.services.variable_manager_service.variable_manager_service import VariableManagerService
        from flowork_kernel.services.localization_manager_service.localization_manager_service import LocalizationManagerService
        from flowork_kernel.services.gateway_connector_service.gateway_connector_service import GatewayConnectorService
        from flowork_kernel.services.workflow_executor_service.workflow_executor_service import WorkflowExecutorService
        from flowork_kernel.services.event_bus_service.event_bus_service import EventBusService
        from flowork_kernel.services.base_service import BaseService
        from flowork_kernel.workers.watchdog import JobWatchdog

        class DynamicMockService(BaseService):
            def __init__(self, kernel, service_id):
                super().__init__(kernel, service_id)

        Singleton.set_instance("ModuleManagerService_class", ModuleManagerService)
        Singleton.set_instance("PluginManagerService_class", PluginManagerService)
        Singleton.set_instance("ToolsManagerService_class", ToolsManagerService)

    except Exception as e:
        logging.error(f"CRITICAL: Failed to import kernel modules: {e}", exc_info=True)
        traceback.print_exc()
        return

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [Worker PID %(process)d] - %(message)s',
        stream=sys.stdout
    )

    try:
        class MiniKernelStub:
            def __init__(self, path):
                self.data_path = os.path.dirname(path)

        mini_kernel = MiniKernelStub(db_path)
        db_service = DatabaseService(mini_kernel, "worker_db_service")
        db_service.db_path = db_path
        db_conn = db_service.create_connection()
        if not db_conn:
            logging.error(f"CRITICAL: Could not create DB connection. Worker is exiting.")
            return
    except Exception as e:
         logging.error(f"CRITICAL: Failed to init DB Service in worker: {e}", exc_info=True)
         traceback.print_exc()
         return

    job_event = None
    WATCHDOG_DEADLINE = int(os.getenv("CORE_JOB_DEADLINE_SECONDS", "120"))
    wd = JobWatchdog(
        deadline_seconds=WATCHDOG_DEADLINE,
        on_timeout=lambda jid: logging.warning(f"[WATCHDOG] Timeout job={jid}")
    )

    print("!!! [SPY] Worker setup complete. Entering Job Loop...", flush=True)

    while True:
        job = None
        new_jobs_were_queued = False
        try:
            job = _db_retry_wrapper(db_conn, _db_atomic_claim_job)
            if job is None:
                if job_event:
                    if job_event.wait(timeout=POLL_INTERVAL_SECONDS):
                        job_event.clear()
                else:
                    time.sleep(POLL_INTERVAL_SECONDS)
                continue

            logging.info(f"Claimed job {job['job_id']} for node {job['node_id']}")
            print(f"!!! [SPY] Processing Job: {job['job_id']}. Fetching node details...", flush=True)

            input_data = json.loads(job['input_data']) if job['input_data'] else {}
            module_id, config_json = _db_retry_wrapper(db_conn, _db_get_node_details, job['node_id'])

            if not module_id:
                raise Exception(f"Node {job['node_id']} not found in DB.")

            print(f"!!! [SPY] Running logic for {module_id}...", flush=True)


            try:
                result_direct = execute_node_logic(
                    job,
                    job['node_id'],
                    module_id,
                    config_json,
                    input_data,
                    Singleton
                )
                execution_result = result_direct
                execution_error = None
            except Exception as e:
                execution_result = None
                execution_error = e


            if execution_error:
                print(f"!!! [SPY] Execution returned ERROR: {execution_error}", flush=True)
                raise execution_error

            if execution_result is None:
                raise Exception(f"Node {module_id} returned NO RESULT (None).")

            output_data, active_port = execution_result
            print(f"!!! [SPY] Unpacked Result -> Output Data Type: {type(output_data)}, Active Port: {active_port}", flush=True)

            if isinstance(output_data, Exception):
                print(f"!!! [SPY] Module returned Exception: {output_data}", flush=True)
                raise output_data

            print(f"!!! [SPY] CHECKPOINT: Exec done. Preparing to find downstream nodes...", flush=True)

            try:
                downstream_nodes = _db_retry_wrapper(
                    db_conn, _db_get_downstream_nodes, job['workflow_id'], job['node_id'], active_port
                )
            except Exception as routing_err:
                print(f"!!! [SPY] CRASH DURING ROUTING CALL: {routing_err}", flush=True)
                traceback.print_exc()
                raise routing_err

            print(f"!!! [SPY] CHECKPOINT: Routing done. Downstream: {len(downstream_nodes)}. Finishing job...", flush=True)

            new_jobs_were_queued = _db_retry_wrapper(
                db_conn, _db_finish_job,
                job['job_id'], job['execution_id'], job['user_id'], job['workflow_id'],
                downstream_nodes, output_data
            )

            try:
                event_bus = Singleton.get_instance("event_bus")
                if event_bus:
                    payload = {"execution_id": job['execution_id'], "job_id": job['job_id'], "status": "DONE"}
                    if job.get('user_id'):
                        payload['_target_user_id'] = job['user_id']

                    event_bus.publish(
                        "JOB_COMPLETED_CHECK",
                        payload,
                        publisher_id="job_worker"
                    )
                    print(f"!!! [SPY] JOB_COMPLETED_CHECK published.", flush=True)
            except Exception as e:
                logging.error(f"[Worker PID {pid}] Failed to publish JOB_COMPLETED_CHECK: {e}")

        except Exception as e:
            print(f"!!! [SPY] OUTER LOOP EXCEPTION DETECTED: {e}", flush=True)
            traceback.print_exc()

            if job:
                logging.error(f"Execution failed for job {job['job_id']}. Error: {e}", exc_info=True)
                try:
                    _db_retry_wrapper(db_conn, _db_fail_job, job['job_id'], str(e))

                    try:
                        event_bus = Singleton.get_instance("event_bus")
                        if event_bus:
                            payload = {"execution_id": job['execution_id'], "job_id": job['job_id'], "status": "FAILED"}
                            if job.get('user_id'):
                                payload['_target_user_id'] = job['user_id']

                            event_bus.publish(
                                "JOB_COMPLETED_CHECK",
                                payload,
                                publisher_id="job_worker"
                            )
                    except Exception as e_ipc:
                        logging.error(f"[Worker PID {pid}] Failed to publish JOB_COMPLETED_CHECK (FAILED): {e_ipc}")

                except Exception as db_fail_e:
                    logging.critical(f"CRITICAL: FAILED TO MARK JOB {job['job_id']} AS FAILED IN DB. {db_fail_e}", exc_info=True)
            else:
                time.sleep(POLL_INTERVAL_SECONDS * 2)

        if new_jobs_were_queued and job_event:
            job_event.set()

    if db_conn:
        db_conn.close()
