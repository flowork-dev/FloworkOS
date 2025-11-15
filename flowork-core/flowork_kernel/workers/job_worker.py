########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\workers\job_worker.py total lines 466 
########################################################################

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
from datetime import datetime
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.kernel_logic import Kernel
from flowork_kernel.services.module_manager_service.module_manager_service import ModuleManagerService
from flowork_kernel.services.plugin_manager_service.plugin_manager_service import PluginManagerService
from flowork_kernel.services.tools_manager_service.tools_manager_service import ToolsManagerService
from flowork_kernel.services.trigger_manager_service.trigger_manager_service import TriggerManagerService
from flowork_kernel.services.ai_provider_manager_service.ai_provider_manager_service import AIProviderManagerService
from flowork_kernel.services.preset_manager_service.preset_manager_service import PresetManagerService
from flowork_kernel.services.variable_manager_service.variable_manager_service import VariableManagerService
from flowork_kernel.services.localization_manager_service.localization_manager_service import LocalizationManagerService
from flowork_kernel.services.gateway_connector_service.gateway_connector_service import GatewayConnectorService
from flowork_kernel.services.workflow_executor_service.workflow_executor_service import WorkflowExecutorService
from flowork_kernel.services.event_bus_service.event_bus_service import EventBusService
from flowork_kernel.services.base_service import BaseService
from .watchdog import JobWatchdog
MAX_DB_RETRIES = 5
POLL_INTERVAL_SECONDS = 0.5
class MockService(BaseService):
    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)

def _safe_json_dumps(data_obj):
    """
    (English Hardcode) Safely dumps a potentially circular object to JSON.
    (English Hardcode) It replaces un-serializable objects (like service instances)
    (English Hardcode) with a placeholder string to prevent crashes.
    """
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
            raise e


def _db_retry_wrapper(db_conn, func, *args, **kwargs):
    """Wraps any DB function with retry logic for SQLITE_BUSY."""
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
                raise
        except Exception as e:
            logging.error(f"[Worker PID {pid}] Non-DB Error in wrapper: {e}", exc_info=True)
            raise
    return None
def _db_atomic_claim_job(db_conn):
    """(Worker Process) Atomically claims one PENDING job."""
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
def execute_node_logic(job, node_id, module_id, config_json, input_data):
    """
    (Worker Process - BUKAN PLACEHOLDER LAGI)
    Menjalankan logika modul yang sebenarnya.
    """
    pid = os.getpid()
    logging.info(f"[Worker PID {pid}]: EXECUTING node {node_id} (Module ID: {module_id})...")
    try:
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

        event_bus = Singleton.get_instance(EventBusService)
        if not event_bus:
            logging.error(f"[Worker PID {pid}]: CRITICAL - Could not get EventBus from Singleton.")
            event_bus = None

        def _real_status_updater(message, log_level):
            """
            (English Hardcode) This is the REAL status updater.
            (English Hardcode) It publishes an event that the main process will forward to the GUI.
            """
            try:
                log_entry = {
                    "job_id": job.get('execution_id'),
                    "node_id": job.get('node_id'),
                    "level": log_level,
                    "message": message,
                    "source": module_id,
                    "ts": datetime.now().isoformat()
                }
                if event_bus:
                    event_bus.publish("WORKFLOW_LOG_ENTRY", log_entry, publisher_id=module_id)
                else:
                    logging.info(f"[{log_level}] {message} (EventBus not found)")
            except Exception as e:
                logging.error(f"Failed to publish log event: {e}")


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


        new_clean_payload = {}

        if isinstance(result, dict) and 'data' in result and 'history' in result:
            new_clean_payload['data'] = result.get('data')
            new_clean_payload['history'] = result.get('history', [])
        else:
            new_clean_payload['data'] = result
            new_clean_payload['history'] = input_data.get('history', [])

        logging.info(f"[Worker PID {pid}]: FINISHED node {node_id}.")
        return new_clean_payload

    except Exception as e:
        logging.error(f"[Worker PID {pid}]: FAILED node {node_id}. Error: {e}", exc_info=True)
        return e
def _db_get_downstream_nodes(db_conn, workflow_id, source_node_id):
    """
    (Worker Process) Queries the Edges table to find all downstream nodes.
    """
    pid = os.getpid()
    try:
        cursor = db_conn.cursor()
        query = "SELECT target_node_id FROM Edges WHERE workflow_id = ? AND source_node_id = ?"
        cursor.execute(query, (workflow_id, source_node_id))
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        logging.error(f"[Worker PID {pid}]: Failed to get downstream nodes for {source_node_id}: {e}")
        raise
def _db_get_node_details(db_conn, node_id):
    """
    (Worker Process) Gets the node's module_id (node_type) and config.
    """
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
    """Atomically marks the current job as DONE and queues up the next jobs."""
    cursor = db_conn.cursor()
    cursor.execute("BEGIN IMMEDIATE;")
    try:
        safe_output_json = _safe_json_dumps(output_data)

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
            cursor.executemany(
                "INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                jobs_to_insert
            )
        db_conn.commit()
        logging.info(f"[Worker PID {os.getpid()}] Job {job_id} DONE. Queued {len(jobs_to_insert)} downstream jobs.")


        return len(jobs_to_insert) > 0
    except Exception as e:
        db_conn.rollback()
        logging.error(f"[Worker PID {os.getpid()}] CRITICAL: Failed to finish job {job_id} or queue downstream jobs: {e}", exc_info=True)
        raise
    return False
def _db_fail_job(db_conn, job_id, error_message):
    """Atomically marks the current job as FAILED."""
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
    """
    Target function for each multiprocessing.Process.
    (MODIFIKASI) Sekarang menginisialisasi Kernel minimalis.
    (MODIFIKASI - RISK
    """
    pid = os.getpid()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [Worker PID %(process)d] - %(message)s')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    logging.info(f"Started. DB Path: {db_path}. Waiting for jobs...")
    db_service = DatabaseService(db_name=os.path.basename(db_path))
    db_conn = db_service.create_connection()
    if not db_conn:
        logging.error(f"CRITICAL: Could not create DB connection. Worker is exiting.")
        return
    job_event = None
    WATCHDOG_DEADLINE = int(os.getenv("CORE_JOB_DEADLINE_SECONDS", "120"))
    wd = JobWatchdog(
        deadline_seconds=WATCHDOG_DEADLINE,
        on_timeout=lambda jid: logging.warning(f"[WATCHDOG] Timeout job={jid}")
    )
    logging.info(f"JobWatchdog initialized with a {WATCHDOG_DEADLINE}s deadline.")
    try:
        class WorkerKernel:
            def __init__(self):
                self.project_root_path = project_root
                self.true_root_path = os.path.abspath(os.path.join(self.project_root_path, ".."))
                self.data_path = db_service.data_dir


                self.modules_path = os.path.join(self.true_root_path, "modules")
                self.plugins_path = os.path.join(self.true_root_path, "plugins")
                self.tools_path = os.path.join(self.true_root_path, "tools")
                self.triggers_path = os.path.join(self.true_root_path, "triggers")
                self.ai_providers_path = os.path.join(self.true_root_path, "ai_providers")
                self.ai_models_path = os.path.join(self.true_root_path, "ai_models")
                self.widgets_path = os.path.join(self.true_root_path, "widgets")
                self.formatters_path = os.path.join(self.true_root_path, "formatters")
                self.scanners_path = os.path.join(self.true_root_path, "scanners")

                self.logs_path = os.path.join(self.project_root_path, "logs")
                self.system_plugins_path = os.path.join(
                    self.project_root_path, "system_plugins"
                )
                self.themes_path = os.path.join(self.project_root_path, "themes")
                self.locales_path = os.path.join(self.project_root_path, "locales")
                self.services = {}
            def write_to_log(self, message, level="INFO", source="WorkerKernel"):
                log_level = getattr(logging, level.upper(), logging.INFO)
                logging.log(log_level, f"[{level}] [{source}] {message}")
            def get_service(self, service_id, **kwargs):
                """
                (FIX) Added **kwargs.
                This allows other services (like LocalizationManager) to call
                get_service(..., is_system_call=True) without crashing the worker.
                """
                return Singleton.get_instance(service_id)
        worker_kernel = WorkerKernel()
        Singleton.set_instance(DatabaseService, db_service)
        job_event = Singleton.get_instance(multiprocessing.Event)
        if not job_event:
            logging.error("CRITICAL: Failed to get Job Event from Singleton. Worker will use polling.")

        Singleton.set_instance("event_ipc_queue", event_ipc_queue)
        event_bus = EventBusService(worker_kernel, "event_bus", ipc_queue=event_ipc_queue)

        Singleton.set_instance(EventBusService, event_bus)
        Singleton.set_instance("event_bus", event_bus)

        loc_manager = LocalizationManagerService(worker_kernel, "localization_manager")
        loc_manager.load_all_languages()
        Singleton.set_instance(LocalizationManagerService, loc_manager)
        var_manager = VariableManagerService(worker_kernel, "variable_manager")
        Singleton.set_instance(VariableManagerService, var_manager)
        preset_manager = PresetManagerService(worker_kernel, "preset_manager_service")
        preset_manager.start()
        Singleton.set_instance(PresetManagerService, preset_manager)
        ai_provider_manager = AIProviderManagerService(worker_kernel, "ai_provider_manager_service")
        Singleton.set_instance(AIProviderManagerService, ai_provider_manager)
        module_manager = ModuleManagerService(worker_kernel, "module_manager_service")
        module_manager.discover_and_load_modules()
        Singleton.set_instance(ModuleManagerService, module_manager)
        plugin_manager = PluginManagerService(worker_kernel, "plugin_manager_service")
        plugin_manager.discover_and_load_plugins()
        Singleton.set_instance(PluginManagerService, plugin_manager)
        tools_manager = ToolsManagerService(worker_kernel, "tools_manager_service")
        tools_manager.discover_and_load_tools()
        Singleton.set_instance(ToolsManagerService, tools_manager)
        Singleton.set_instance(GatewayConnectorService, MockService(worker_kernel, "gateway_connector_service"))
        Singleton.set_instance(WorkflowExecutorService, MockService(worker_kernel, "workflow_executor_service"))
        logging.info(f"Worker Kernel services initialized. Modules loaded: {len(module_manager.loaded_modules)}")
    except Exception as e:
        logging.error(f"CRITICAL: Failed to initialize worker kernel: {e}", exc_info=True)
        db_conn.close()
        return
    while True:
        job = None
        new_jobs_were_queued = False
        try:
            job = _db_retry_wrapper(db_conn, _db_atomic_claim_job)
            if job is None:
                if job_event:
                    job_event.clear()
                    logging.debug("No jobs found. Sleeping (waiting for event)...")
                    job_event.wait()
                    logging.debug("Woke up by event. Checking for jobs...")
                else:
                    logging.debug("No jobs found. Sleeping (polling)...")
                    time.sleep(POLL_INTERVAL_SECONDS)
                continue
            logging.info(f"Claimed job {job['job_id']} for node {job['node_id']}")
            input_data = json.loads(job['input_data']) if job['input_data'] else {}
            module_id, config_json = _db_retry_wrapper(db_conn, _db_get_node_details, job['node_id'])
            if not module_id:
                raise Exception(f"Node {job['node_id']} not found in DB.")

            output_data, err = wd.run_with_deadline(
                job['job_id'],
                execute_node_logic,
                job,
                job['node_id'],
                module_id,
                config_json,
                input_data
            )

            if err:
                raise err
            if isinstance(output_data, Exception):
                raise output_data
            downstream_nodes = _db_retry_wrapper(
                db_conn, _db_get_downstream_nodes, job['workflow_id'], job['node_id']
            )
            new_jobs_were_queued = _db_retry_wrapper(
                db_conn, _db_finish_job,
                job['job_id'], job['execution_id'], job['user_id'], job['workflow_id'],
                downstream_nodes, output_data
            )

            try:
                event_bus = Singleton.get_instance("event_bus")
                if event_bus:
                    event_bus.publish(
                        "JOB_COMPLETED_CHECK",
                        {"execution_id": job['execution_id'], "job_id": job['job_id'], "status": "DONE"},
                        publisher_id="job_worker"
                    )
                    logging.info(f"[Worker PID {pid}] Published JOB_COMPLETED_CHECK (DONE) for Exec ID {job['execution_id']}")
                else:
                    logging.warning(f"[Worker PID {pid}] Could not get event_bus to publish JOB_COMPLETED_CHECK.")
            except Exception as e:
                logging.error(f"[Worker PID {pid}] Failed to publish JOB_COMPLETED_CHECK: {e}")

        except Exception as e:
            if job:
                logging.error(f"Execution failed for job {job['job_id']} (Node {job.get('node_id', 'N/A')}). Error: {e}", exc_info=True)
                try:
                    _db_retry_wrapper(db_conn, _db_fail_job, job['job_id'], str(e))

                    try:
                        event_bus = Singleton.get_instance("event_bus")
                        if event_bus:
                            event_bus.publish(
                                "JOB_COMPLETED_CHECK",
                                {"execution_id": job['execution_id'], "job_id": job['job_id'], "status": "FAILED"},
                                publisher_id="job_worker"
                            )
                            logging.info(f"[Worker PID {pid}] Published JOB_COMPLETED_CHECK (FAILED) for Exec ID {job['execution_id']}")
                        else:
                            logging.warning(f"[Worker PID {pid}] Could not get event_bus to publish JOB_COMPLETED_CHECK.")
                    except Exception as e_ipc:
                        logging.error(f"[Worker PID {pid}] Failed to publish JOB_COMPLETED_CHECK (FAILED): {e_ipc}")

                except Exception as db_fail_e:
                    logging.critical(f"CRITICAL: FAILED TO MARK JOB {job['job_id']} AS FAILED IN DB. {db_fail_e}", exc_info=True)
            else:
                logging.critical(f"Unhandled error in worker loop (job was not claimed): {e}", exc_info=True)
                if isinstance(e, sqlite3.Error):
                    time.sleep(POLL_INTERVAL_SECONDS * 2)
        if new_jobs_were_queued and job_event:
            logging.debug(f"Job {job['job_id']} queued new jobs. Ringing bell...")
            job_event.set()
    if db_conn:
        db_conn.close()
    logging.info(f"Shutting down.")
