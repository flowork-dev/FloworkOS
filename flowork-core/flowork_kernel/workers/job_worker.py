########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\workers\job_worker.py total lines 594 
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
        print(f"!!! [WORKER SPY] MockService '{service_id}' instantiated.", flush=True)

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
                raise
        except Exception as e:
            logging.error(f"[Worker PID {pid}] Non-DB Error in wrapper: {e}", exc_info=True)
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

        """CRITICAL FIX: Get event_bus using the string alias "event_bus"."""
        real_event_bus = Singleton.get_instance("event_bus")

        if not real_event_bus:
            logging.error(f"[Worker PID {pid}]: CRITICAL - Could not get EventBus from Singleton. LOGS AND POPUPS WILL FAIL.")
            print(f"!!! [WORKER ERROR {pid}] Could not get 'event_bus' from Singleton. LOGS/POPUPS WILL FAIL.", flush=True)
            event_bus = None
        else:
             event_bus = ContextEventBus(real_event_bus, job_owner_id)
             logging.debug(f"[Worker PID {pid}] EventBus found. Publishing ability ENABLED. User Context: {job_owner_id}")
             print(f"!!! [WORKER SPY {pid}] EventBus for {module_id} successfully retrieved and wrapped for User {job_owner_id}.", flush=True)

        if module_instance:
            setattr(module_instance, 'event_bus', event_bus)
            if hasattr(module_instance, 'services') and isinstance(module_instance.services, dict):
                module_instance.services['event_bus'] = event_bus
                logging.debug(f" Injected EventBus into module {module_id}")

        def _real_status_updater(message, log_level):
            try:
                log_entry = {
                    "job_id": job.get('execution_id'),
                    "node_id": job.get('node_id'),
                    "level": log_level,
                    "message": message,
                    "source": module_id,
                    "ts": datetime.now().isoformat(),
                    "_target_user_id": job_owner_id # (English Hardcode) Also inject into logs directly
                }

                print(f"[Worker PID {pid}] [STATUS UPDATE] {message}", flush=True)

                if event_bus:
                    logging.info(f"[Worker PID {pid}] Publishing WORKFLOW_LOG_ENTRY via event_bus.")
                    print(f"!!! [WORKER SPY {pid}] Publishing 'WORKFLOW_LOG_ENTRY': {message}", flush=True)
                    event_bus.publish("WORKFLOW_LOG_ENTRY", log_entry, publisher_id=module_id)
                else:
                    logging.warning(f"[Worker PID {pid}] Cannot publish WORKFLOW_LOG_ENTRY, event_bus is None.")
                    print(f"!!! [WORKER ERROR {pid}] Cannot publish log, event_bus is None.", flush=True)
            except Exception as e:
                logging.error(f"Failed to publish log event: {e}")

        logging.info(f"[Worker PID {pid}] Calling module_instance.execute() for {module_id}...")
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

        logging.info(f"[Worker PID {pid}] module_instance.execute() finished for {module_id}.")
        print(f"!!! [WORKER SPY {pid}] Module {module_id} execute() finished.", flush=True)

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
        print(f"!!! [WORKER SPY {pid}] Added project root to sys.path: {project_root}", flush=True)

    try:
        print("!!! [WORKER SPY] Attempting kernel imports...", flush=True)
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
        from flowork_kernel.workers.watchdog import JobWatchdog
        print(f"!!! [WORKER SPY {pid}] Kernel imports successful.", flush=True)

        class DynamicMockService(BaseService):
            def __init__(self, kernel, service_id):
                super().__init__(kernel, service_id)

        Singleton.set_instance("ModuleManagerService_class", ModuleManagerService)
        Singleton.set_instance("PluginManagerService_class", PluginManagerService)
        Singleton.set_instance("ToolsManagerService_class", ToolsManagerService)

    except ImportError as e:
        print(f"!!! [WORKER CRASH {pid}] FAILED TO IMPORT KERNEL MODULES: {e}", flush=True)
        logging.error(f"CRITICAL: Failed to import kernel modules: {e}", exc_info=True)
        return
    except Exception as e:
        print(f"!!! [WORKER CRASH {pid}] UNKNOWN ERROR DURING IMPORT: {e}", flush=True)
        logging.error(f"CRITICAL: Unknown error during kernel imports: {e}", exc_info=True)
        return

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [Worker PID %(process)d] - %(message)s',
        stream=sys.stdout
    )

    logging.info(f"Started. DB Path: {db_path}. Waiting for jobs...")
    print(f"!!! [WORKER SPY {pid}] Logging configured.", flush=True)

    try:
        print(f"!!! [WORKER SPY {pid}] Initializing DatabaseService...", flush=True)

        """ [FIX START] Create a 'MiniKernel' stub to satisfy DatabaseService dependencies"""
        class MiniKernelStub:
            def __init__(self, path):
                self.data_path = os.path.dirname(path)

        mini_kernel = MiniKernelStub(db_path)
        """ Pass the stub instead of None"""
        db_service = DatabaseService(mini_kernel, "worker_db_service")
        """[FIX END]"""

        db_service.db_path = db_path
        db_conn = db_service.create_connection()
        if not db_conn:
            logging.error(f"CRITICAL: Could not create DB connection. Worker is exiting.")
            print(f"!!! [WORKER CRASH {pid}] Could not create DB connection. Exiting.", flush=True)
            return
        print(f"!!! [WORKER SPY {pid}] DB Service and connection OK.", flush=True)
    except Exception as e:
         logging.error(f"CRITICAL: Failed to init DB Service in worker: {e}", exc_info=True)
         print(f"!!! [WORKER CRASH {pid}] Failed to init DB Service: {e}. Exiting.", flush=True)
         return

    job_event = None
    WATCHDOG_DEADLINE = int(os.getenv("CORE_JOB_DEADLINE_SECONDS", "120"))
    wd = JobWatchdog(
        deadline_seconds=WATCHDOG_DEADLINE,
        on_timeout=lambda jid: logging.warning(f"[WATCHDOG] Timeout job={jid}")
    )
    logging.info(f"JobWatchdog initialized with a {WATCHDOG_DEADLINE}s deadline.")
    print(f"!!! [WORKER SPY {pid}] Watchdog OK. Starting Kernel init...", flush=True)

    try:
        class WorkerKernel:
            def __init__(self):
                self.project_root_path = project_root
                self.true_root_path = os.path.abspath(os.path.join(self.project_root_path, ".."))
                self.data_path = os.path.dirname(db_path)

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
                self.system_plugins_path = os.path.join(self.project_root_path, "system_plugins")
                self.themes_path = os.path.join(self.project_root_path, "themes")
                self.locales_path = os.path.join(self.project_root_path, "locales")
                self.services = {}
                self.globally_disabled_components = set()

            def write_to_log(self, message, level="INFO", source="WorkerKernel"):
                log_level = getattr(logging, level.upper(), logging.INFO)
                logging.log(log_level, f"[{level}] [{source}] {message}")

            def get_service(self, service_id, **kwargs):
                return Singleton.get_instance(service_id)

        print(f"!!! [WORKER SPY {pid}] WorkerKernel class defined.", flush=True)
        worker_kernel = WorkerKernel()

        db_service.kernel = worker_kernel
        Singleton.set_instance(DatabaseService, db_service)

        print(f"!!! [WORKER SPY {pid}] WorkerKernel instance created.", flush=True)

        job_event = Singleton.get_instance(multiprocessing.Event)
        if not job_event:
            logging.warning("Job Event not found in Singleton. Worker will use polling.")
        print(f"!!! [WORKER SPY {pid}] Got Job Event from Singleton.", flush=True)

        Singleton.set_instance("event_ipc_queue", event_ipc_queue)
        print(f"!!! [WORKER SPY {pid}] Set IPC Queue in Singleton.", flush=True)

        event_bus = EventBusService(worker_kernel, "event_bus", ipc_queue=event_ipc_queue)
        Singleton.set_instance(EventBusService, event_bus)
        Singleton.set_instance("event_bus", event_bus)
        print(f"!!! [WORKER SPY {pid}] EventBusService initialized and set in Singleton.", flush=True)

        logging.info("Initializing Worker Managers...")
        print(f"!!! [WORKER SPY {pid}] Initializing LocalizationManagerService...", flush=True)
        loc_manager = LocalizationManagerService(worker_kernel, "localization_manager")
        loc_manager.load_all_languages()
        Singleton.set_instance(LocalizationManagerService, loc_manager)

        print(f"!!! [WORKER SPY {pid}] Initializing VariableManagerService...", flush=True)
        var_manager = VariableManagerService(worker_kernel, "variable_manager")
        Singleton.set_instance(VariableManagerService, var_manager)

        print(f"!!! [WORKER SPY {pid}] Initializing PresetManagerService...", flush=True)
        preset_manager = PresetManagerService(worker_kernel, "preset_manager_service")
        preset_manager.start()
        Singleton.set_instance(PresetManagerService, preset_manager)

        print(f"!!! [WORKER SPY {pid}] Initializing AIProviderManagerService...", flush=True)
        ai_provider_manager = AIProviderManagerService(worker_kernel, "ai_provider_manager_service")
        Singleton.set_instance(AIProviderManagerService, ai_provider_manager)

        print(f"!!! [WORKER SPY {pid}] Initializing ModuleManagerService...", flush=True)
        module_manager = ModuleManagerService(worker_kernel, "module_manager_service")
        module_manager.discover_and_load_modules()
        Singleton.set_instance(ModuleManagerService, module_manager)

        print(f"!!! [WORKER SPY {pid}] Initializing PluginManagerService...", flush=True)
        plugin_manager = PluginManagerService(worker_kernel, "plugin_manager_service")
        plugin_manager.discover_and_load_plugins()
        Singleton.set_instance(PluginManagerService, plugin_manager)

        print(f"!!! [WORKER SPY {pid}] Initializing ToolsManagerService...", flush=True)
        tools_manager = ToolsManagerService(worker_kernel, "tools_manager_service")
        tools_manager.discover_and_load_tools()
        Singleton.set_instance(ToolsManagerService, tools_manager)

        print(f"!!! [WORKER SPY {pid}] Setting Mock Services...", flush=True)
        Singleton.set_instance(GatewayConnectorService, DynamicMockService(worker_kernel, "gateway_connector_service"))
        Singleton.set_instance(WorkflowExecutorService, DynamicMockService(worker_kernel, "workflow_executor_service"))

        logging.info(f"Worker Kernel services initialized. Modules loaded: {len(module_manager.loaded_modules)}")
        print(f"!!! [WORKER BOOT] PID {pid} ENTERING JOB LOOP !!!", flush=True)

    except Exception as e:
        logging.error(f"CRITICAL: Failed to initialize worker kernel: {e}", exc_info=True)
        print(f"!!! [WORKER CRASH] PID {pid} DIED DURING INIT: {e}", flush=True)
        if db_conn: db_conn.close()
        return

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
            print(f"!!! [WORKER SPY {pid}] Claimed job {job['job_id']} for node {job['node_id']}", flush=True)
            input_data = json.loads(job['input_data']) if job['input_data'] else {}
            module_id, config_json = _db_retry_wrapper(db_conn, _db_get_node_details, job['node_id'])

            if not module_id:
                raise Exception(f"Node {job['node_id']} not found in DB.")

            print(f"!!! [WORKER SPY {pid}] Running logic for {module_id} with watchdog...", flush=True)
            output_data, err = wd.run_with_deadline(
                job['job_id'],
                execute_node_logic,
                job,
                job['node_id'],
                module_id,
                config_json,
                input_data,
                Singleton # (English Hardcode) Pass Singleton to execute_node_logic
            )
            print(f"!!! [WORKER SPY {pid}] Logic finished for {module_id}.", flush=True)

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
            print(f"!!! [WORKER SPY {pid}] Job {job['job_id']} finished and marked DONE in DB.", flush=True)

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
                    logging.info(f"[Worker PID {pid}] Published JOB_COMPLETED_CHECK (DONE) for Exec ID {job['execution_id']}")
                else:
                    logging.warning(f"[Worker PID {pid}] Could not get event_bus to publish JOB_COMPLETED_CHECK.")
            except Exception as e:
                logging.error(f"[Worker PID {pid}] Failed to publish JOB_COMPLETED_CHECK: {e}")

        except Exception as e:
            if job:
                logging.error(f"Execution failed for job {job['job_id']} (Node {job.get('node_id', 'N/A')}). Error: {e}", exc_info=True)
                print(f"!!! [WORKER ERROR {pid}] Execution failed for job {job['job_id']}: {e}", flush=True)
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
                            logging.info(f"[Worker PID {pid}] Published JOB_COMPLETED_CHECK (FAILED) for Exec ID {job['execution_id']}")
                    except Exception as e_ipc:
                        logging.error(f"[Worker PID {pid}] Failed to publish JOB_COMPLETED_CHECK (FAILED): {e_ipc}")

                except Exception as db_fail_e:
                    logging.critical(f"CRITICAL: FAILED TO MARK JOB {job['job_id']} AS FAILED IN DB. {db_fail_e}", exc_info=True)
            else:
                if not isinstance(e, sqlite3.OperationalError):
                     logging.critical(f"Unhandled error in worker loop: {e}", exc_info=True)
                time.sleep(POLL_INTERVAL_SECONDS * 2)

        if new_jobs_were_queued and job_event:
            logging.debug(f"Job {job['job_id']} queued new jobs. Ringing bell...")
            job_event.set()

    if db_conn:
        db_conn.close()
    logging.info(f"Shutting down.")
    print(f"!!! [WORKER SHUTDOWN {pid}] Worker loop exited. DB connection closed.", flush=True)
