########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\workflow_handler.py total lines 422 
########################################################################

import time
import json
import uuid
import sqlite3
import multiprocessing
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from .base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

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
                user_id = user_context.get('id')
                execution_id = real_data.get('job_id')
                workflow_id = real_data.get('preset_name')
                initial_payload = real_data.get('initial_payload', {})
                workflow_data = real_data.get('workflow_data', {})
                start_node_id = real_data.get('start_node_id')

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

                self.logger.info(f"Received 'execute_workflow' for user {user_id} (Exec ID: {execution_id}")
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
                        self.logger.info(f"Successfully inserted/replaced {len(nodes_to_insert)} node definitions.")

                    cursor.execute("DELETE FROM Edges WHERE workflow_id = ?", (workflow_id,))
                    edges_to_insert = []
                    for edge in edges:
                        edges_to_insert.append((
                            workflow_id,
                            edge.get('source'),
                            edge.get('target'),
                            edge.get('source_port_name') or edge.get('sourceHandle'), # GUI sends sourceHandle
                            edge.get('target_port_name') or edge.get('targetHandle')  # GUI sends targetHandle
                        ))

                    if edges_to_insert:
                        cursor.executemany(
                            "INSERT INTO Edges (workflow_id, source_node_id, target_node_id, source_handle, target_handle) VALUES (?, ?, ?, ?, ?)",
                            edges_to_insert
                        )
                        self.logger.info(f"Successfully inserted {len(edges_to_insert)} edge definitions with routing handles.")


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
                        job_event = Singleton.get_instance(multiprocessing.Event)
                        if job_event:
                            job_event.set()
                            self.logger.debug(f"Job event (bell) set for Exec ID: {execution_id}")
                        else:
                            self.logger.error("Failed to get job_event from Singleton. Workers may not wake up immediately.")
                    except Exception as e:
                        self.logger.error(f"Error while setting job_event (bell): {e}", exc_info=True)
                except sqlite3.IntegrityError as ie:
                    conn.rollback()
                    self.logger.error(f"DB IntegrityError for Exec ID {execution_id} (Workflow ID: {workflow_id}): {ie}", exc_info=False)
                    self.logger.warning(f"This is likely a 'ghost' workflow from a stale GUI cache. Sending error to user.")
                    try:
                        event_bus = self.service.kernel_services.get("event_bus")
                        if event_bus:
                            event_bus.publish(
                                "WORKFLOW_EXECUTION_UPDATE",
                                {
                                    "job_id": execution_id,
                                    "status_data": {
                                        "status": "FAILED",
                                        "error_message": f"Database Error: Workflow ID '{workflow_id}' not found. This can happen after a system rebuild. Please re-save your workflow and try again.",
                                        "end_time": time.time(),
                                    },
                                    "_target_user_id": user_id
                                },
                            )
                    except Exception as e_event:
                        self.logger.error(f"Failed to publish execution failure event: {e_event}")
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Failed to insert jobs into DB: {e}", exc_info=True)
                    try:
                        event_bus = self.service.kernel_services.get("event_bus")
                        if event_bus:
                            event_bus.publish(
                                "WORKFLOW_EXECUTION_UPDATE",
                                {
                                    "job_id": execution_id,
                                    "status_data": {
                                        "status": "FAILED",
                                        "error_message": f"Core Engine Error: {str(e)}",
                                        "end_time": time.time(),
                                    },
                                    "_target_user_id": user_id
                                },
                            )
                    except Exception as e_event:
                        self.logger.error(f"Failed to publish generic execution failure event: {e_event}")

                finally:
                    conn.close()
            except Exception as e:
                self.logger.error(f"Error handling 'execute_workflow': {e}", exc_info=True)
                try:
                    event_bus = self.service.kernel_services.get("event_bus")
                    if event_bus and execution_id:
                        event_bus.publish(
                            "WORKFLOW_EXECUTION_UPDATE",
                            {
                                "job_id": execution_id,
                                "status_data": {
                                    "status": "FAILED",
                                    "error_message": f"Core Engine Critical Error: {str(e)}",
                                    "end_time": time.time(),
                                },
                                "_target_user_id": user_id
                            },
                        )
                except Exception as e_event:
                    self.logger.error(f"Failed to publish top-level execution failure event: {e_event}")

        @self.sio.event(namespace='/engine-socket')
        async def execute_standalone_node(data):
            execution_id = None
            try:
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                    self.logger.error(f"[Core] Received non-versioned 'execute_standalone_node'. Ignoring.")
                    return

                real_data = data.get('payload', {})
                user_context = real_data.get('user_context', {})
                user_id = user_context.get('id')
                execution_id = real_data.get('job_id')
                node_data = real_data.get('node_data')
                initial_payload = real_data.get('initial_payload', {})
                mode = real_data.get('mode', 'EXECUTE')

                if not node_data or not node_data.get('module_id'):
                    self.logger.error(f"No 'node_data' in 'execute_standalone_node' payload.")
                    return

                workflow_id = f"standalone__{node_data.get('module_id')}"

                self.logger.info(f"Received 'execute_standalone_node' for user {user_id} (Exec ID: {execution_id}")

                db_service = Singleton.get_instance(DatabaseService)
                if not db_service:
                    self.logger.error("'db_service' not found. Cannot execute.")
                    return

                node_data['id'] = node_data.get('module_id') # (English Hardcode) Standalone nodes use module_id as node_id
                nodes = [node_data]
                edges = []
                starting_nodes = [node_data['id']]

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

                    self.logger.info(f"Ensuring parent execution '{execution_id}' exists in DB...")
                    cursor.execute(
                        "INSERT OR IGNORE INTO Executions (execution_id, workflow_id, user_id, status, strategy) VALUES (?, ?, ?, ?, ?)",
                        (execution_id, workflow_id, user_id, 'RUNNING', 'fast') # (English Hardcode) Use 'fast' strategy for standalone
                    )

                    self.logger.info(f"Inserting/Updating {len(nodes)} node definitions into DB for Workflow: {workflow_id}")
                    nodes_to_insert = [(
                        node.get('id'),
                        workflow_id,
                        node.get('module_id'),
                        json.dumps(node.get('config_values', {}))
                    ) for node in nodes]

                    if nodes_to_insert:
                        cursor.executemany(
                            "INSERT OR REPLACE INTO Nodes (node_id, workflow_id, node_type, config_json) VALUES (?, ?, ?, ?)",
                            nodes_to_insert
                        )

                    jobs_to_insert = []
                    for node_id in starting_nodes:
                        job_id = execution_id # (English Hardcode) Use the exact job_id from GUI
                        jobs_to_insert.append((
                            job_id,
                            execution_id, # (English Hardcode) Use job_id as execution_id for standalone
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
                    self.logger.info(f"Successfully queued 1 standalone job in DB for Exec ID: {execution_id}")

                    try:
                        job_event = Singleton.get_instance(multiprocessing.Event)
                        if job_event:
                            job_event.set()
                            self.logger.debug(f"Job event (bell) set for Exec ID: {execution_id}")
                        else:
                            self.logger.error("Failed to get job_event from Singleton. Workers may not wake up immediately.")
                    except Exception as e:
                        self.logger.error(f"Error while setting job_event (bell): {e}", exc_info=True)

                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Failed to insert standalone job into DB: {e}", exc_info=True)
                finally:
                    conn.close()

            except Exception as e:
                self.logger.error(f"Error handling 'execute_standalone_node': {e}", exc_info=True)

        @self.sio.on('stop_workflow', namespace='/engine-socket')
        async def on_stop_workflow(data):
            try:
                self.logger.info(f"[Core] Received 'stop_workflow' from Gateway.")
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                    self.logger.error(f"[Core] Non-versioned 'stop_workflow'. Ignoring.")
                    return

                payload = data.get('payload', {})
                execution_id = payload.get('job_id')
                user_id = payload.get('user_context', {}).get('id')

                if not execution_id:
                    self.logger.error(f"[Core] 'stop_workflow' received without 'job_id'. Ignoring.")
                    return

                db_service = Singleton.get_instance(DatabaseService)
                if not db_service:
                    self.logger.error("'db_service' not found. Cannot stop workflow.")
                    return

                conn = db_service.create_connection()
                if not conn:
                    self.logger.error("Failed to create DB connection. Cannot stop workflow.")
                    return

                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE Executions SET status = 'STOPPED' WHERE execution_id = ?", (execution_id,))
                    cursor.execute("UPDATE Jobs SET status = 'CANCELLED' WHERE execution_id = ? AND status = 'PENDING'", (execution_id,))
                    conn.commit()
                    self.logger.info(f"[Core] Workflow {execution_id} marked as STOPPED. All pending jobs cancelled.")

                    event_bus = self.service.kernel_services.get("event_bus")
                    if event_bus:
                        event_bus.publish(
                            "WORKFLOW_EXECUTION_UPDATE",
                            {
                                "job_id": execution_id,
                                "status_data": {
                                    "status": "STOPPED",
                                    "end_time": time.time(),
                                },
                                "_target_user_id": user_id
                            },
                        )

                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Failed to update DB for 'stop_workflow' {execution_id}: {e}", exc_info=True)
                finally:
                    conn.close()

            except Exception as e:
                self.logger.error(f"Error handling 'stop_workflow': {e}", exc_info=True)

        @self.sio.on('pause_workflow', namespace='/engine-socket')
        async def on_pause_workflow(data):
            try:
                self.logger.info(f"[Core] Received 'pause_workflow' from Gateway.")
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                    self.logger.error(f"[Core] Non-versioned 'pause_workflow'. Ignoring.")
                    return

                payload = data.get('payload', {})
                execution_id = payload.get('job_id')
                user_id = payload.get('user_context', {}).get('id')

                if not execution_id:
                    self.logger.error(f"[Core] 'pause_workflow' received without 'job_id'. Ignoring.")
                    return

                db_service = Singleton.get_instance(DatabaseService)
                if not db_service:
                    self.logger.error("'db_service' not found. Cannot pause workflow.")
                    return

                conn = db_service.create_connection()
                if not conn:
                    self.logger.error("Failed to create DB connection. Cannot pause workflow.")
                    return

                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE Executions SET status = 'PAUSED' WHERE execution_id = ?", (execution_id,))
                    cursor.execute("UPDATE Jobs SET status = 'PAUSED' WHERE execution_id = ? AND status = 'PENDING'", (execution_id,))
                    conn.commit()
                    self.logger.info(f"[Core] Workflow {execution_id} marked as PAUSED. All pending jobs paused.")

                    event_bus = self.service.kernel_services.get("event_bus")
                    if event_bus:
                        event_bus.publish(
                            "WORKFLOW_EXECUTION_UPDATE",
                            {
                                "job_id": execution_id,
                                "status_data": {
                                    "status": "PAUSED",
                                },
                                "_target_user_id": user_id
                            },
                        )

                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Failed to update DB for 'pause_workflow' {execution_id}: {e}", exc_info=True)
                finally:
                    conn.close()

            except Exception as e:
                self.logger.error(f"Error handling 'pause_workflow': {e}", exc_info=True)
