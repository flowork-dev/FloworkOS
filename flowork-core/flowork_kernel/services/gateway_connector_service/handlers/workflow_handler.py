########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\workflow_handler.py total lines 258 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION


import time
import json
import uuid
import sqlite3
import multiprocessing
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService

class WorkflowHandler(BaseHandler):
    def register_events(self):
        @self.sio.event(namespace='/engine-socket')
        async def execute_workflow(data):
            execution_id = None
            workflow_id = None

            try:
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                    self.logger.error(f"[Core] Received non-versioned 'execute_workflow'. Ignoring.")
                    return

                real_data = data.get('payload', {})
                user_context = real_data.get('user_context', {})
                user_id = user_context.get('id', 'system') # Default to system if missing
                execution_id = real_data.get('job_id')
                workflow_id = real_data.get('preset_name')
                initial_payload = real_data.get('initial_payload', {})
                workflow_data = real_data.get('workflow_data', {})
                start_node_id = real_data.get('start_node_id')

                if not workflow_id:
                    wf_name_candidate = workflow_data.get('name')
                    if wf_name_candidate:
                        workflow_id = wf_name_candidate
                    else:
                        workflow_id = f"adhoc_{uuid.uuid4().hex[:8]}"
                        self.logger.warning(f"⚠️ [Core] Client sent empty 'preset_name'. Generated fallback ID: {workflow_id}")

                global_loop_config = workflow_data.get('global_loop_config')
                if global_loop_config:
                      workflow_executor = self.service.kernel_services.get("workflow_executor_service")
                      if workflow_executor and hasattr(workflow_executor, 'set_execution_loop_config'):
                          workflow_executor.set_execution_loop_config(execution_id, global_loop_config, workflow_id)
                          self.logger.info(f"[Loop] Registered loop config for {execution_id}: {global_loop_config}")
                      else:
                          self.logger.warning(f"[Loop] Failed to register loop config. Executor service missing or incompatible.")

                force_strategy = real_data.get("strategy")
                context = {"force_strategy": force_strategy} if force_strategy else {}
                strategy = self.service.router.pick(context)
                self.logger.info(f"(R5) Strategy selected for {execution_id}: {strategy}")

                self.logger.info(f"Received 'execute_workflow' for user {user_id} (Exec ID: {execution_id})")
                db_service = Singleton.get_instance(DatabaseService)
                if not db_service:
                    self.logger.error("'db_service' not found. Cannot execute.")
                    return

                nodes = workflow_data.get('nodes', [])
                edges = workflow_data.get('connections', [])
                target_node_ids = {edge['target'] for edge in edges}

                if start_node_id:
                    starting_nodes = [start_node_id]
                    self.logger.info(f"Starting workflow {execution_id} from specific node: {start_node_id}")
                else:
                    starting_nodes = [node['id'] for node in nodes if node['id'] not in target_node_ids]

                if not starting_nodes:
                    self.logger.warning(f"Workflow {workflow_id} has no starting nodes. Execution stopped.")
                    return

                conn = db_service.create_connection()
                if not conn:
                    self.logger.error("Failed to create DB connection. Cannot queue jobs.")
                    return

                try:
                    cursor = conn.cursor()
                    self.logger.info(f"Ensuring parent workflow '{workflow_id}' exists in DB...")

                    cursor.execute(
                        "INSERT OR IGNORE INTO Workflows (workflow_id, name) VALUES (?, ?)",
                        (workflow_id, workflow_id)
                    )

                    cursor.execute(
                        "INSERT INTO Executions (execution_id, workflow_id, user_id, status, strategy) VALUES (?, ?, ?, ?, ?)",
                        (execution_id, workflow_id, user_id, 'RUNNING', strategy)
                    )

                    self.logger.info(f"Inserting/Updating {len(nodes)} node definitions into DB for Workflow: {workflow_id}")
                    nodes_to_insert = []
                    for node in nodes:
                        nodes_to_insert.append((
                            node.get('id'),
                            workflow_id,
                            node.get('module_id'),
                            json.dumps(node.get('config_values', {}))
                        ))

                    if nodes_to_insert:
                        cursor.executemany(
                            "INSERT OR REPLACE INTO Nodes (node_id, workflow_id, node_type, config_json) VALUES (?, ?, ?, ?)",
                            nodes_to_insert
                        )

                    cursor.execute("DELETE FROM Edges WHERE workflow_id = ?", (workflow_id,))
                    edges_to_insert = []
                    for edge in edges:
                        edges_to_insert.append((
                            workflow_id,
                            edge.get('source'),
                            edge.get('target'),
                            edge.get('source_port_name') or edge.get('sourceHandle'),
                            edge.get('target_port_name') or edge.get('targetHandle')
                        ))

                    if edges_to_insert:
                        cursor.executemany(
                            "INSERT INTO Edges (workflow_id, source_node_id, target_node_id, source_handle, target_handle) VALUES (?, ?, ?, ?, ?)",
                            edges_to_insert
                        )

                    jobs_to_insert = []
                    for node_id in starting_nodes:
                        job_id = str(uuid.uuid4())
                        jobs_to_insert.append((
                            job_id,
                            execution_id,
                            node_id,
                            'PENDING',
                            json.dumps(initial_payload),
                            workflow_id,
                            user_id
                        ))

                    cursor.executemany(
                        "INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        jobs_to_insert
                    )
                    conn.commit()

                    self.logger.info(f"Successfully queued {len(starting_nodes)} starting jobs in DB for Exec ID: {execution_id}")

                    try:
                        job_event = Singleton.get_instance(multiprocessing.Event) or Singleton.get_instance("job_event")
                        if job_event:
                            job_event.set()
                            self.logger.debug(f"Job event (bell) set for Exec ID: {execution_id}")
                        else:
                            eb = self.service.kernel_services.get("event_bus")
                            if eb: eb.publish("WAKE_WORKERS", {"execution_id": execution_id})
                            self.logger.error("Failed to get job_event from Singleton. Used EventBus fallback.")
                    except Exception as e:
                        self.logger.error(f"Error while setting job_event (bell): {e}", exc_info=True)

                except sqlite3.IntegrityError as ie:
                    conn.rollback()
                    self.logger.error(f"DB IntegrityError for Exec ID {execution_id}: {ie}")
                finally:
                    conn.close()
            except Exception as e:
                self.logger.error(f"Error handling 'execute_workflow': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def execute_standalone_node(data):
            execution_id = None
            try:
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
                real_data = data.get('payload', {})
                user_id = real_data.get('user_context', {}).get('id')
                execution_id = real_data.get('job_id')
                node_data = real_data.get('node_data')
                initial_payload = real_data.get('initial_payload', {})

                if not node_data: return

                workflow_id = f"standalone__{node_data.get('module_id')}"

                db_service = Singleton.get_instance(DatabaseService)
                if not db_service: return

                node_data['id'] = node_data.get('module_id')
                nodes = [node_data]
                starting_nodes = [node_data['id']]

                conn = db_service.create_connection()
                if not conn: return
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO Workflows (workflow_id, name) VALUES (?, ?)", (workflow_id, workflow_id))
                    cursor.execute("INSERT OR IGNORE INTO Executions (execution_id, workflow_id, user_id, status, strategy) VALUES (?, ?, ?, 'RUNNING', 'fast')", (execution_id, workflow_id, user_id))

                    nodes_to_insert = [(node.get('id'), workflow_id, node.get('module_id'), json.dumps(node.get('config_values', {}))) for node in nodes]
                    cursor.executemany("INSERT OR REPLACE INTO Nodes (node_id, workflow_id, node_type, config_json) VALUES (?, ?, ?, ?)", nodes_to_insert)

                    jobs_to_insert = [(execution_id, execution_id, node_id, 'PENDING', json.dumps(initial_payload), workflow_id, user_id) for node_id in starting_nodes]
                    cursor.executemany("INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)", jobs_to_insert)
                    conn.commit()

                    job_event = Singleton.get_instance(multiprocessing.Event) or Singleton.get_instance("job_event")
                    if job_event: job_event.set()
                finally:
                    conn.close()
            except Exception as e:
                self.logger.error(f"Error handling 'execute_standalone_node': {e}")

        @self.sio.on('stop_workflow', namespace='/engine-socket')
        async def on_stop_workflow(data):
            try:
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
                payload = data.get('payload', {})
                execution_id = payload.get('job_id')
                user_id = payload.get('user_context', {}).get('id')
                db_service = Singleton.get_instance(DatabaseService)
                if not db_service: return
                conn = db_service.create_connection()
                if not conn: return
                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE Executions SET status = 'STOPPED' WHERE execution_id = ?", (execution_id,))
                    cursor.execute("UPDATE Jobs SET status = 'CANCELLED' WHERE execution_id = ? AND status = 'PENDING'", (execution_id,))
                    conn.commit()
                    eb = self.service.kernel_services.get("event_bus")
                    if eb: eb.publish("WORKFLOW_EXECUTION_UPDATE", {"job_id": execution_id, "status_data": {"status": "STOPPED", "end_time": time.time()}, "_target_user_id": user_id})
                finally:
                    conn.close()
            except Exception as e: self.logger.error(f"Error stop_workflow: {e}")

        @self.sio.on('pause_workflow', namespace='/engine-socket')
        async def on_pause_workflow(data):
            try:
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
                payload = data.get('payload', {})
                execution_id = payload.get('job_id')
                user_id = payload.get('user_context', {}).get('id')
                db_service = Singleton.get_instance(DatabaseService)
                if not db_service: return
                conn = db_service.create_connection()
                if not conn: return
                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE Executions SET status = 'PAUSED' WHERE execution_id = ?", (execution_id,))
                    cursor.execute("UPDATE Jobs SET status = 'PAUSED' WHERE execution_id = ? AND status = 'PENDING'", (execution_id,))
                    conn.commit()
                    eb = self.service.kernel_services.get("event_bus")
                    if eb: eb.publish("WORKFLOW_EXECUTION_UPDATE", {"job_id": execution_id, "status_data": {"status": "PAUSED"}, "_target_user_id": user_id})
                finally: conn.close()
            except Exception as e: self.logger.error(f"Error pause_workflow: {e}")
