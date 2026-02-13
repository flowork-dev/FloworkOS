########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\workflow_executor_service\__init__.py total lines 527 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import importlib
import os
import logging
import asyncio
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


class WorkflowExecutorService(BaseService):
    def start_listeners(self):
        try:
            if not self.db_service:
                self.db_service = Singleton.get_instance(DatabaseService)
            self.event_bus = Singleton.get_instance('event_bus')
            self.app_manager = Singleton.get_instance('app_service')
            try:
                if self.kernel and hasattr(self.kernel, 'services'):
                    self.gateway_connector = self.kernel.services.get('gateway_connector_service')
            except:
                pass
            if not self.db_service:
                self.logger.error('CRITICAL: Missing DB Service from Singleton in start_listeners.')
                return
            if not self.event_bus:
                self.logger.error('CRITICAL: Missing Event Bus from Singleton in start_listeners.')
                return
            self.event_bus.subscribe('JOB_COMPLETED_CHECK', 'workflow_executor_service.check', self._on_job_completed)
            self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            self._watchdog_thread.start()
            self.logger.info('Service initialized. Watchdog Thread started.')
        except Exception as e:
            self.logger.error(f'CRITICAL: Failed to initialize service instances: {e}', exc_info=True)
            self.db_service = None
            self.event_bus = None
    def _watchdog_loop(self):
        self.logger.info('[Watchdog] Started. Monitoring for stuck workflows...')
        while True:
            try:
                time.sleep(3)
                if not self.db_service:
                    continue
                conn = self.db_service.create_connection()
                if not conn:
                    continue
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT execution_id, user_id FROM Executions WHERE status = 'RUNNING'")
                    running_execs = cursor.fetchall()
                    for (exec_id, user_id) in running_execs:
                        if exec_id not in self.execution_user_cache and user_id:
                            self.execution_user_cache[exec_id] = user_id
                        cursor.execute("SELECT job_id, node_id, status FROM Jobs WHERE execution_id = ? AND status IN ('DONE', 'FAILED') ORDER BY finished_at DESC LIMIT 5", (exec_id,))
                        done_jobs = cursor.fetchall()
                        for (job_id, node_id, status) in done_jobs:
                            self._queue_downstream_nodes_sync(conn, exec_id, node_id, job_id, status)
                finally:
                    conn.close()
            except Exception as e:
                self.logger.error(f'[Watchdog] Error in loop: {e}')
                time.sleep(5)
    def _queue_downstream_nodes_sync(self, conn, execution_id, finished_node_id, finished_job_id, status='DONE'):
        try:
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT target_node_id, source_handle FROM Edges WHERE source_node_id = ?', (finished_node_id,))
            except sqlite3.OperationalError:
                cursor.execute("SELECT target_node_id, 'default' FROM Edges WHERE source_node_id = ?", (finished_node_id,))
            targets = cursor.fetchall()
            for (target_node_id, source_handle) in targets:
                is_error_path = source_handle == 'error'
                if status == 'DONE' and is_error_path:
                    continue
                if status == 'FAILED' and (not is_error_path):
                    continue
                cursor.execute('SELECT source_node_id FROM Edges WHERE target_node_id = ?', (target_node_id,))
                dependencies = cursor.fetchall()
                all_met = True
                input_data_merged = {}
                for (dep_source_id,) in dependencies:
                    cursor.execute("SELECT output_data, status FROM Jobs WHERE execution_id = ? AND node_id = ? AND status IN ('DONE', 'FAILED') ORDER BY finished_at DESC LIMIT 1", (execution_id, dep_source_id))
                    row = cursor.fetchone()
                    if not row:
                        all_met = False
                        break
                    try:
                        prev_output = json.loads(row[0]) if row[0] else {}
                        if isinstance(prev_output, dict):
                            input_data_merged.update(prev_output)
                    except:
                        pass
                if all_met:
                    cursor.execute('SELECT 1 FROM Jobs WHERE execution_id = ? AND node_id = ?', (execution_id, target_node_id))
                    if cursor.fetchone():
                        continue
                    new_job_id = str(uuid.uuid4())
                    user_id = self.execution_user_cache.get(execution_id, 'system')
                    cursor.execute('SELECT workflow_id FROM Jobs WHERE job_id = ?', (finished_job_id,))
                    wf_row = cursor.fetchone()
                    workflow_id = wf_row[0] if wf_row else None
                    safe_input = json.dumps(input_data_merged, default=str)
                    cursor.execute("INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id) VALUES (?, ?, ?, 'PENDING', ?, ?, ?)", (new_job_id, execution_id, target_node_id, safe_input, workflow_id, user_id))
                    conn.commit()
                    self._publish_node_status(execution_id, target_node_id, 'RUNNING')
                    job_event = Singleton.get_instance(multiprocessing.Event)
                    if job_event:
                        job_event.set()
        except Exception as e:
            self.logger.error(f'[Watchdog] Failed to queue downstream: {e}')
    def get_user_for_execution(self, execution_id: str) -> str | None:
        return self.execution_user_cache.get(execution_id)
    def set_execution_loop_config(self, execution_id: str, loop_config: dict, workflow_id: str):
        iterations = int(loop_config.get('iterations', 1))
        is_enabled = loop_config.get('isEnabled', False)
        if is_enabled or iterations > 1:
            self.execution_loop_cache[execution_id] = {'config': loop_config, 'current': 1, 'workflow_id': workflow_id}
            self.logger.info(f'Looping ENABLED for {execution_id}. Iterations: {iterations}')
    def start_workflow_execution(self, workflow_id: str, user_id: str, initial_payload: dict, strategy: str='default') -> (str, str):
        if not self.db_service:
            self.logger.error('DB service not available. Cannot start workflow.')
            raise Exception('DatabaseService not initialized.')
        conn = None
        try:
            execution_id = str(uuid.uuid4())
            start_job_id = str(uuid.uuid4())
            self.execution_user_cache[execution_id] = user_id
            if initial_payload and isinstance(initial_payload, dict):
                loop_cfg = initial_payload.get('_runtime_loop_config')
                if loop_cfg:
                    self.set_execution_loop_config(execution_id, loop_cfg, workflow_id)
            conn = self.db_service.create_connection()
            if not conn:
                raise Exception('Failed to create DB connection.')
            cursor = conn.cursor()
            cursor.execute('BEGIN IMMEDIATE;')
            cursor.execute("SELECT node_id FROM Nodes WHERE workflow_id = ? AND node_type = 'flowork.core.trigger.start'", (workflow_id,))
            start_node = cursor.fetchone()
            if not start_node:
                cursor.execute('\n                    SELECT T1.node_id FROM Nodes AS T1\n                    LEFT JOIN Edges AS T2 ON T1.node_id = T2.target_node_id\n                    WHERE T1.workflow_id = ? AND T2.edge_id IS NULL\n                    LIMIT 1\n                    ', (workflow_id,))
                start_node = cursor.fetchone()
            if not start_node:
                raise Exception(f'Cannot find a start node (no inputs) for workflow_id {workflow_id}')
            start_node_id = start_node[0]
            try:
                cursor.execute("\n                    INSERT INTO Executions (execution_id, workflow_id, user_id, strategy, status, created_at, gas_budget_hint)\n                    VALUES (?, ?, ?, ?, 'RUNNING', CURRENT_TIMESTAMP, ?)\n                    ", (execution_id, workflow_id, user_id, strategy, 10000))
            except sqlite3.Error as e:
                self.logger.warning(f"(R5) Failed to create 'Executions' record, maybe table doesn't exist? {e}")
                pass
            safe_input_json = json.dumps(initial_payload, default=str)
            cursor.execute("\n                INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id)\n                VALUES (?, ?, ?, 'PENDING', ?, ?, ?)\n                ", (start_job_id, execution_id, start_node_id, safe_input_json, workflow_id, user_id))
            conn.commit()
            self._publish_node_status(execution_id, start_node_id, 'RUNNING')
            self._publish_log(execution_id, start_node_id, 'Workflow started', 'SUCCESS')
            job_event = Singleton.get_instance(multiprocessing.Event)
            if job_event:
                job_event.set()
            return (execution_id, start_job_id)
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f'Failed to start workflow execution for {workflow_id}: {e}', exc_info=True)
            raise
        finally:
            if conn:
                conn.close()
    async def _on_job_completed(self, event_name: str, subscriber_id: str, event_data: Dict[str, Any]):
        execution_id = event_data.get('execution_id')
        job_id = event_data.get('job_id')
        status = event_data.get('status')
        if not execution_id:
            return
        self.logger.info(f'Job {job_id} ({status}) finished. Checking next steps...')
        node_id = self._get_node_id_by_job(job_id)
        if node_id:
            node_status = 'SUCCESS' if status == 'DONE' else 'FAILED'
            self._publish_node_status(execution_id, node_id, node_status)
            msg = f'Node finished with status: {node_status}'
            lvl = 'SUCCESS' if status == 'DONE' else 'ERROR'
            self._publish_log(execution_id, node_id, msg, lvl)
            if status == 'DONE' or status == 'FAILED':
                await self._queue_downstream_nodes(execution_id, node_id, job_id, status)
        async with self._completion_lock:
            await self._check_workflow_completion(execution_id)
    def _get_node_id_by_job(self, job_id):
        if not self.db_service:
            return None
        conn = self.db_service.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT node_id FROM Jobs WHERE job_id = ?', (job_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except:
            return None
        finally:
            conn.close()
    async def _queue_downstream_nodes(self, execution_id, finished_node_id, finished_job_id, status='DONE'):
        if not self.db_service:
            return
        conn = self.db_service.create_connection()
        if not conn:
            return
        try:
            self._queue_downstream_nodes_sync(conn, execution_id, finished_node_id, finished_job_id, status)
        except Exception as e:
            self.logger.error(f'Failed to queue downstream nodes: {e}', exc_info=True)
        finally:
            conn.close()
    async def _check_workflow_completion(self, execution_id: str):
        if not self.db_service:
            return
        conn = None
        try:
            query = "SELECT 1 FROM Jobs WHERE execution_id = ? AND status IN ('PENDING', 'RUNNING') LIMIT 1"
            conn = self.db_service.create_connection()
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute(query, (execution_id,))
            pending_jobs = cursor.fetchone()
            if not pending_jobs:
                self.logger.info(f'Workflow {execution_id} has no more pending jobs.')
                if await self._handle_global_loop(execution_id, conn):
                    return
                self.logger.info(f'Workflow {execution_id} finished. Generating report...')
                (outcome_report, analysis_report) = self._generate_r5_report(conn, execution_id)
                fail_query = "SELECT 1 FROM Jobs WHERE execution_id = ? AND status = 'FAILED' LIMIT 1"
                cursor.execute(fail_query, (execution_id,))
                has_failures = cursor.fetchone()
                final_status = 'FAILED' if has_failures else 'SUCCEEDED'
                try:
                    cursor.execute('UPDATE Executions SET status = ?, finished_at = CURRENT_TIMESTAMP WHERE execution_id = ?', (final_status, execution_id))
                    conn.commit()
                    self.logger.info(f'(DB FIX) Execution {execution_id} marked as {final_status} in DB.')
                except Exception as db_e:
                    self.logger.error(f'(DB FIX) Failed to update Execution status in DB: {db_e}')
                self._publish_workflow_status(execution_id, final_status, end_time=time.time(), outcome=outcome_report, analysis=analysis_report)
                self.execution_user_cache.pop(execution_id, None)
                self.execution_loop_cache.pop(execution_id, None)
            else:
                pass
        except Exception as e:
            self.logger.error(f'Failed to check workflow completion for {execution_id}: {e}', exc_info=True)
        finally:
            if conn:
                conn.close()
    async def _handle_global_loop(self, execution_id: str, conn) -> bool:
        loop_data = self.execution_loop_cache.get(execution_id)
        if not loop_data:
            return False
        config = loop_data.get('config', {})
        current_iter = loop_data.get('current', 1)
        max_iter = int(config.get('iterations', 1))
        if current_iter >= max_iter:
            self.logger.info(f'[Loop] Execution {execution_id} reached max iterations ({max_iter}). Stopping.')
            return False
        is_delay_enabled = config.get('isDelayEnabled', False)
        if is_delay_enabled:
            delay_type = config.get('delayType', 'static')
            delay_seconds = 0.0
            if delay_type == 'static':
                delay_seconds = float(config.get('delayStatic', 1))
            elif delay_type == 'random_range':
                mn = float(config.get('delayRandomMin', 1))
                mx = float(config.get('delayRandomMax', 5))
                if mn > mx:
                    (mn, mx) = (mx, mn)
                delay_seconds = random.uniform(mn, mx)
            if delay_seconds > 0:
                self.logger.info(f'[Loop] Sleeping for {delay_seconds:.2f}s before iteration {current_iter + 1}...')
                await asyncio.sleep(delay_seconds)
        next_iter = current_iter + 1
        loop_data['current'] = next_iter
        workflow_id = loop_data.get('workflow_id')
        user_id = self.execution_user_cache.get(execution_id)
        self.logger.info(f'[Loop] Restarting workflow {execution_id} (Iteration {next_iter}/{max_iter})...')
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT node_id FROM Nodes WHERE workflow_id = ? AND node_type = 'flowork.core.trigger.start'", (workflow_id,))
            start_node = cursor.fetchone()
            if not start_node:
                cursor.execute('\n                    SELECT T1.node_id FROM Nodes AS T1\n                    LEFT JOIN Edges AS T2 ON T1.node_id = T2.target_node_id\n                    WHERE T1.workflow_id = ? AND T2.edge_id IS NULL\n                    LIMIT 1\n                    ', (workflow_id,))
                start_node = cursor.fetchone()
            if not start_node:
                self.logger.error(f'[Loop] Failed to find start node for restart.')
                return False
            start_node_id = start_node[0]
            new_job_id = str(uuid.uuid4())
            cursor.execute("\n                INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id)\n                VALUES (?, ?, ?, 'PENDING', '{}', ?, ?)\n                ", (new_job_id, execution_id, start_node_id, workflow_id, user_id))
            conn.commit()
            self._publish_node_status(execution_id, start_node_id, 'RUNNING')
            job_event = Singleton.get_instance(multiprocessing.Event)
            if job_event:
                job_event.set()
            self._publish_workflow_status(execution_id, 'RUNNING', end_time=None)
            return True
        except Exception as e:
            self.logger.error(f'[Loop] Failed to restart workflow: {e}')
            conn.rollback()
            return False
    def _generate_r5_report(self, db_conn: Any, execution_id: str) -> (Dict[str, Any], Dict[str, Any]):
        outcome_meter = OutcomeMeter()
        analysis_report = AnalystReport(stats={'empty': True}, tags=[], risks=['no-data'])
        try:
            cursor = db_conn.cursor()
            cursor.execute('SELECT status, COUNT(*) FROM Jobs WHERE execution_id = ? GROUP BY status', (execution_id,))
            rows = cursor.fetchall()
            for (status, count) in rows:
                if status == 'DONE':
                    outcome_meter.record_success(cost=0)
                    outcome_meter.success = count
                elif status == 'FAILED':
                    outcome_meter.record_failure(cost=0)
                    outcome_meter.failure = count
            gas_budget = 10000
            try:
                cursor.execute('SELECT gas_budget_hint FROM Executions WHERE execution_id = ?', (execution_id,))
                row = cursor.fetchone()
                if row:
                    gas_budget = row[0]
            except Exception:
                pass
            fake_events = []
            cursor.execute('SELECT node_id, status, error_message, created_at, finished_at FROM Jobs WHERE execution_id = ? ORDER BY created_at', (execution_id,))
            job_rows = cursor.fetchall()
    
            def parse_ts(t):
                if not t:
                    return time.time()
                if isinstance(t, (int, float)):
                    return float(t)
                try:
                    return datetime.strptime(str(t), '%Y-%m-%d %H:%M:%S').timestamp()
                except ValueError:
                    try:
                        return datetime.fromisoformat(str(t)).timestamp()
                    except Exception:
                        return time.time()
            if job_rows:
                start_ts = parse_ts(job_rows[0][3])
                fake_events.append({'ts': start_ts, 'type': 'agent_boot', 'data': {'gas_limit': gas_budget}})
                for job in job_rows:
                    (node_id, status, error, start, end) = job
                    end_ts = parse_ts(end)
                    if status == 'DONE':
                        fake_events.append({'ts': end_ts, 'type': 'episodic_write', 'data': {'node': node_id}})
                    elif status == 'FAILED':
                        fake_events.append({'ts': end_ts, 'type': 'error', 'data': {'node': node_id, 'error': error}})
            analyst = Analyst(budget_gas_hint=gas_budget)
            analysis_report_obj = analyst.analyze(fake_events)
            analysis_report = analysis_report_obj.to_dict()
            outcome_meter.total_cost = analysis_report.get('stats', {}).get('gas_used', 0)
            return (outcome_meter.summary(), analysis_report)
        except Exception as e:
            self.logger.error(f'(R5) Failed to generate R5 report for {execution_id}: {e}', exc_info=True)
            return (outcome_meter.summary(), analysis_report.to_dict() if isinstance(analysis_report, AnalystReport) else analysis_report)
    def _publish_node_status(self, execution_id: str, node_id: str, status: str):
        if self.event_bus:
            try:
                target_user = self.execution_user_cache.get(execution_id)
                payload = {'job_id': execution_id, 'execution_id': execution_id, 'node_id': node_id, 'status': status, 'timestamp': time.time(), '_target_user_id': target_user}
                self.event_bus.publish('node_status_update', payload, publisher_id='SYSTEM')
                if not self.gateway_connector and self.kernel and hasattr(self.kernel, 'services'):
                    self.gateway_connector = self.kernel.services.get('gateway_connector_service')
                if self.gateway_connector:
                    self.gateway_connector.forward_event_to_gateway('NODE_STATUS_UPDATE', 'vip_express', payload)
            except Exception as e:
                self.logger.error(f'Failed to publish node_status_update: {e}')
    def _publish_workflow_status(self, execution_id: str, status: str, end_time: Optional[float]=None, outcome: Optional[Dict[str, Any]]=None, analysis: Optional[Dict[str, Any]]=None):
        try:
            target_user = self.execution_user_cache.get(execution_id)
            status_data = {'status': status}
            if end_time:
                status_data['end_time'] = end_time
            event_payload = {'job_id': execution_id, 'status_data': status_data, 'outcome': outcome or {}, 'analysis': analysis or {}, '_target_user_id': target_user}
            if self.event_bus:
                self.event_bus.publish('WORKFLOW_EXECUTION_UPDATE', event_payload, publisher_id='SYSTEM')
            if not self.gateway_connector and self.kernel and hasattr(self.kernel, 'services'):
                self.gateway_connector = self.kernel.services.get('gateway_connector_service')
            if self.gateway_connector:
                self.gateway_connector.forward_event_to_gateway('WORKFLOW_EXECUTION_UPDATE', 'vip_express', event_payload)
            self.logger.info(f'Published WORKFLOW_EXECUTION_UPDATE: {status} for {execution_id}')
        except Exception as e:
            self.logger.error(f'Failed to publish WORKFLOW_EXECUTION_UPDATE for {execution_id}: {e}', exc_info=True)
    def _publish_log(self, execution_id: str, node_id: str, message: str, level: str='INFO'):
        """[LOG FIX] Helper to publish logs explicitly via VIP route"""
        if self.event_bus:
            try:
                target_user = self.execution_user_cache.get(execution_id)
                payload = {'job_id': execution_id, 'node_id': node_id, 'message': message, 'level': level, 'ts': time.time(), '_target_user_id': target_user}
                self.event_bus.publish('WORKFLOW_LOG_ENTRY', payload, publisher_id='SYSTEM')
                if not self.gateway_connector and self.kernel and hasattr(self.kernel, 'services'):
                    self.gateway_connector = self.kernel.services.get('gateway_connector_service')
                if self.gateway_connector:
                    self.gateway_connector.forward_event_to_gateway('WORKFLOW_LOG_ENTRY', 'vip_express', payload)
            except Exception as e:
                self.logger.error(f'Failed to publish log: {e}')
    async def execute_standalone_node(self, payload: dict):
        """
            [FIXED BY FLOWORK DEV]
            Executes a single node as an entry point with STANDALONE PROTECTION.
            Avoids DB IntegrityError when workflow_id is missing.
            """
        self.logger.info(f'Executing standalone node request: {payload}')
        raw_node_id = payload.get('node_id')
        user_id = payload.get('user_id', 'direct_command')
        forced_execution_id = payload.get('execution_id')
        forced_job_id = payload.get('job_id')
        input_data = payload.get('input')
        if input_data is None:
            input_data = {k: v for (k, v) in payload.items() if k not in ['node_id', 'user_id', 'engine_id', 'job_id', 'execution_id']}
        if not raw_node_id:
            self.logger.error("execute_standalone_node failed: 'node_id' is missing.")
            return
        if self.app_manager and raw_node_id in self.app_manager.registry.get('apps', {}).get('data', {}):
            self.logger.info(f"[SDK Bridge] Found App Node '{raw_node_id}'. Delegating (Standalone Mode).")
            ctx = {'user_context': {'user_id': user_id}, 'job_id': forced_job_id or str(uuid.uuid4()), 'workflow_id': None}
            pass
        if not self.db_service:
            self.logger.error('execute_standalone_node failed: DB Service unavailable.')
            return
        conn = None
        try:
            conn = self.db_service.create_connection()
            cursor = conn.cursor()
            resolved_node_id = raw_node_id
            workflow_id = None
            try:
                uuid.UUID(raw_node_id)
                cursor.execute('SELECT workflow_id FROM Nodes WHERE node_id = ?', (raw_node_id,))
                row = cursor.fetchone()
                if row:
                    workflow_id = row[0]
            except ValueError:
                cursor.execute('SELECT node_id, workflow_id FROM Nodes WHERE node_type = ? ORDER BY rowid DESC LIMIT 1', (raw_node_id,))
                row = cursor.fetchone()
                if row:
                    resolved_node_id = row[0]
                    workflow_id = row[1]
            if not workflow_id:
                workflow_id = '00000000-0000-0000-0000-000000000000'
            execution_id = forced_execution_id if forced_execution_id else str(uuid.uuid4())
            job_id = forced_job_id if forced_job_id else str(uuid.uuid4())
            self.execution_user_cache[execution_id] = user_id
            cursor.execute("\n                INSERT OR IGNORE INTO Executions (execution_id, workflow_id, user_id, strategy, status, created_at, gas_budget_hint)\n                VALUES (?, ?, ?, ?, 'RUNNING', CURRENT_TIMESTAMP, ?)\n                ", (execution_id, workflow_id, user_id, 'manual_node_trigger', 10000))
            safe_input_json = json.dumps(input_data, default=str)
            cursor.execute("\n                INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id)\n                VALUES (?, ?, ?, 'PENDING', ?, ?, ?)\n                ", (job_id, execution_id, resolved_node_id, safe_input_json, workflow_id, user_id))
            conn.commit()
            self.logger.info(f'[Standalone] DB Execution started! Exec ID: {execution_id}')
            self._publish_node_status(execution_id, resolved_node_id, 'RUNNING')
            self._publish_log(execution_id, resolved_node_id, f'Standalone Job Started: {job_id}', 'INFO')
            job_event = Singleton.get_instance(multiprocessing.Event)
            if job_event:
                job_event.set()
            return {'status': 'queued', 'job_id': job_id, 'execution_id': execution_id}
        except Exception as e:
            self.logger.error(f'execute_standalone_node Exception: {e}', exc_info=True)
            if conn:
                conn.rollback()
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()

    def __init__(self, kernel, service_id):
        self.cells = {}
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger('LazyHub')
        super().__init__(kernel, service_id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_bus = None
        self.execution_user_cache: Dict[str, str] = {}
        self.execution_loop_cache: Dict[str, Dict[str, Any]] = {}
        self._completion_lock = asyncio.Lock()
        self.app_manager = None
        self._watchdog_thread = None
        self.gateway_connector = None
        try:
            self.db_service = Singleton.get_instance(DatabaseService)
            if not self.db_service:
                self.logger.error('CRITICAL: Missing DB Service from Singleton.')
        except Exception as e:
            self.logger.error(f'CRITICAL: Failed to get Singleton instances: {e}')
            self.db_service = None

    def execute_sync(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return module.run(self, *args, **kwargs)

    async def execute_async(self, cell_name, *args, **kwargs):
        module = self._load_cell(cell_name)
        return await module.run(self, *args, **kwargs)

    def _load_cell(self, cell_name):
        if cell_name not in self.cells:
            try:
                module = importlib.import_module(f".{cell_name}", package=__package__)
                self.cells[cell_name] = module
                if hasattr(self, 'logger'):
                    self.logger.info(f"[LazyHub] ✅ Loaded: {cell_name}.py")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"[LazyHub] ❌ Failed to load '{cell_name}': {e}")
                raise e
        return self.cells[cell_name]

    def start(self, *args, **kwargs):
        return self.execute_sync('start', *args, **kwargs)
