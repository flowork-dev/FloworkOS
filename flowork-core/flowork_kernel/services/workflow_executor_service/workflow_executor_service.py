########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\workflow_executor_service\workflow_executor_service.py total lines 318 
########################################################################

import logging
import uuid
import time
import json
from typing import Dict, Any, List, Optional
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService
from flowork_kernel.services.event_bus_service.event_bus_service import EventBusService
from flowork_kernel.outcome import OutcomeMeter
from flowork_kernel.analyst import Analyst, AnalystReport

class WorkflowExecutorService(BaseService):
    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_bus = None
        self.execution_user_cache: Dict[str, str] = {}
        try:
            self.db_service = Singleton.get_instance(DatabaseService)
            if not self.db_service:
                 self.logger.error("CRITICAL: Missing DB Service from Singleton.")
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to get Singleton instances: {e}")
            self.db_service = None


    def start_listeners(self):
        """
        (English Hardcode) Final initialization step, called manually from run_server.py
        (English Hardcode) after the Main Event Bus loop is set.
        """
        try:
            if not self.db_service:
                self.db_service = Singleton.get_instance(DatabaseService)
            self.event_bus = Singleton.get_instance("event_bus")

            if not self.db_service:
                 self.logger.error("CRITICAL: Missing DB Service from Singleton in start_listeners.")
                 return

            if not self.event_bus:
                 self.logger.error("CRITICAL: Missing Event Bus from Singleton in start_listeners.")
                 return

            self.event_bus.subscribe(
                "JOB_COMPLETED_CHECK",
                self._on_job_completed,
                "workflow_executor_service.check"
            )
            self.logger.info("Service initialized. Subscribed to JOB_COMPLETED_CHECK.")

        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to initialize service instances: {e}", exc_info=True)
            self.db_service = None
            self.event_bus = None

    def get_user_for_execution(self, execution_id: str) -> str | None:
        """(R5) Helper for GatewayConnector to find the user_id for a live execution."""
        return self.execution_user_cache.get(execution_id)

    def start_workflow_execution(self, workflow_id: str, user_id: str, initial_payload: dict, strategy: str = "default") -> (str, str):
        """
        (R5) This is the new entry point called by GatewayConnector.
        It creates the master Execution record and the first 'start' job.
        """
        if not self.db_service:
            self.logger.error("DB service not available. Cannot start workflow.")
            raise Exception("DatabaseService not initialized.")

        conn = None
        try:
            execution_id = str(uuid.uuid4())
            start_job_id = str(uuid.uuid4())

            self.execution_user_cache[execution_id] = user_id

            conn = self.db_service.create_connection()
            if not conn:
                raise Exception("Failed to create DB connection.")

            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")

            cursor.execute(
                "SELECT node_id FROM Nodes WHERE workflow_id = ? AND node_type = 'flowork.core.trigger.start'",
                (workflow_id,)
            )
            start_node = cursor.fetchone()

            if not start_node:
                cursor.execute(
                    """
                    SELECT T1.node_id FROM Nodes AS T1
                    LEFT JOIN Edges AS T2 ON T1.node_id = T2.target_node_id
                    WHERE T1.workflow_id = ? AND T2.edge_id IS NULL
                    LIMIT 1
                    """,
                    (workflow_id,)
                )
                start_node = cursor.fetchone()

            if not start_node:
                raise Exception(f"Cannot find a start node (no inputs) for workflow_id {workflow_id}")

            start_node_id = start_node[0]

            try:
                cursor.execute(
                    """
                    INSERT INTO Executions (execution_id, workflow_id, user_id, strategy, status, created_at, gas_budget_hint)
                    VALUES (?, ?, ?, ?, 'RUNNING', CURRENT_TIMESTAMP, ?)
                    """,
                    (execution_id, workflow_id, user_id, strategy, 10000)
                )
            except sqlite3.Error as e:
                self.logger.warning(f"(R5) Failed to create 'Executions' record, maybe table doesn't exist? {e}")
                pass

            safe_input_json = json.dumps(initial_payload, default=str)
            cursor.execute(
                """
                INSERT INTO Jobs (job_id, execution_id, node_id, status, input_data, workflow_id, user_id)
                VALUES (?, ?, ?, 'PENDING', ?, ?, ?)
                """,
                (start_job_id, execution_id, start_node_id, safe_input_json, workflow_id, user_id)
            )

            conn.commit()

            job_event = Singleton.get_instance(multiprocessing.Event)
            if job_event:
                job_event.set()

            return execution_id, start_job_id

        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Failed to start workflow execution for {workflow_id}: {e}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()

    def _on_job_completed(self, event_name: str, subscriber_id: str, event_data: Dict[str, Any]):
        """
        (English Hardcode) Event handler for JOB_COMPLETED_CHECK.
        (English Hardcode) Callback signature MUST match (event_name, subscriber_id, payload).
        """
        execution_id = event_data.get("execution_id")
        job_id = event_data.get("job_id")
        status = event_data.get("status")

        if not execution_id:
            self.logger.warning(f"Received JOB_COMPLETED_CHECK without execution_id. Ignoring.")
            return

        self.logger.info(f"Job {job_id} ({status}) finished. Checking completion status for Exec ID: {execution_id}")
        self._check_workflow_completion(execution_id)

    def _check_workflow_completion(self, execution_id: str):
        """
        (R5 MODIFIED)
        (English Hardcode) Checks the DB to see if all jobs for this workflow are finalized (DONE or FAILED).
        (English Hardcode) If so, fires the final event (WITH R5 REPORT) to the GUI.
        """
        if not self.db_service:
            self.logger.error("DB service not available. Cannot check workflow completion.")
            return

        conn = None
        try:
            query = "SELECT 1 FROM Jobs WHERE execution_id = ? AND status IN ('PENDING', 'RUNNING') LIMIT 1"

            conn = self.db_service.create_connection()
            if not conn:
                self.logger.error("Failed to create DB connection. Cannot check workflow completion.")
                return

            cursor = conn.cursor()
            cursor.execute(query, (execution_id,))
            pending_jobs = cursor.fetchone()

            if not pending_jobs:
                self.logger.info(f"Workflow {execution_id} has no more pending jobs. Generating R5 report...")

                outcome_report, analysis_report = self._generate_r5_report(conn, execution_id)

                self._publish_workflow_status(
                    execution_id,
                    "COMPLETED",
                    end_time=time.time(),
                    outcome=outcome_report,
                    analysis=analysis_report
                )

                self.execution_user_cache.pop(execution_id, None)

            else:
                self.logger.info(f"Workflow {execution_id} still has pending/running jobs. Not complete yet.")

        except Exception as e:
            self.logger.error(f"Failed to check workflow completion for {execution_id}: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

    def _generate_r5_report(self, db_conn: Any, execution_id: str) -> (Dict[str, Any], Dict[str, Any]):
        """(R5) Helper to generate Outcome and Analyst reports from DB data."""

        outcome_meter = OutcomeMeter()
        analysis_report = AnalystReport(stats={"empty": True}, tags=[], risks=["no-data"])

        try:
            cursor = db_conn.cursor()

            cursor.execute(
                "SELECT status, COUNT(*) FROM Jobs WHERE execution_id = ? GROUP BY status",
                (execution_id,)
            )
            rows = cursor.fetchall()
            for status, count in rows:
                if status == 'DONE':
                    outcome_meter.record_success(cost=0)
                    outcome_meter.success = count
                elif status == 'FAILED':
                    outcome_meter.record_failure(cost=0)
                    outcome_meter.failure = count


            gas_budget = 10000
            try:
                cursor.execute(
                    "SELECT gas_budget_hint FROM Executions WHERE execution_id = ?",
                    (execution_id,)
                )
                row = cursor.fetchone()
                if row:
                    gas_budget = row[0]
            except Exception:
                pass

            fake_events = []
            cursor.execute(
                "SELECT node_id, status, error_message, created_at, finished_at FROM Jobs WHERE execution_id = ? ORDER BY created_at",
                (execution_id,)
            )
            job_rows = cursor.fetchall()

            if job_rows:
                fake_events.append({"ts": job_rows[0][3], "type": "agent_boot", "data": {"gas_limit": gas_budget}})

                for job in job_rows:
                    node_id, status, error, start, end = job
                    if status == 'DONE':
                        fake_events.append({"ts": end, "type": "episodic_write", "data": {"node": node_id}})
                    elif status == 'FAILED':
                        fake_events.append({"ts": end, "type": "error", "data": {"node": node_id, "error": error}})

            analyst = Analyst(budget_gas_hint=gas_budget)
            analysis_report_obj = analyst.analyze(fake_events)
            analysis_report = analysis_report_obj.to_dict()

            outcome_meter.total_cost = analysis_report.get("stats", {}).get("gas_used", 0)

            return outcome_meter.summary(), analysis_report

        except Exception as e:
            self.logger.error(f"(R5) Failed to generate R5 report for {execution_id}: {e}", exc_info=True)
            return outcome_meter.summary(), analysis_report.to_dict() if isinstance(analysis_report, AnalystReport) else analysis_report


    def _publish_workflow_status(self, execution_id: str, status: str, end_time: Optional[float] = None,
                                 outcome: Optional[Dict[str, Any]] = None,
                                 analysis: Optional[Dict[str, Any]] = None):
        """
        (R5 MODIFIED)
        (English Hardcode) Publishes the final workflow status update (with reports) to the Event Bus.
        """
        if not self.event_bus:
            self.event_bus = Singleton.get_instance("event_bus")
            if not self.event_bus:
                self.logger.error("Event Bus not available. Cannot publish workflow status.")
                return

        try:
            status_data = {"status": status}
            if end_time:
                status_data["end_time"] = end_time

            event_payload = {
                "job_id": execution_id,
                "status_data": status_data,
                "outcome": outcome or {},
                "analysis": analysis or {}
            }

            self.event_bus.publish("WORKFLOW_EXECUTION_UPDATE", event_payload, publisher_id="SYSTEM")
            self.logger.info(f"Published WORKFLOW_EXECUTION_UPDATE: {status} for {execution_id}")

        except Exception as e:
            self.logger.error(f"Failed to publish WORKFLOW_EXECUTION_UPDATE for {execution_id}: {e}", exc_info=True)


    async def execute_standalone_node(self, payload: dict):
        """
        (Per Roadmap 6/8) Executes a single node without a workflow context.
        This can also use the job queue.
        """
        self.logger.info("Executing standalone node... (Refactor pending)")
        pass
