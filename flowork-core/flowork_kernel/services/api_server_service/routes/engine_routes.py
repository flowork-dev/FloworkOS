########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\engine_routes.py total lines 304 
########################################################################

import datetime
import time
import json
from .base_api_route import BaseApiRoute
from flowork_kernel.exceptions import PermissionDeniedError
from collections import Counter, defaultdict

from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService

class EngineRoutes(BaseApiRoute):

    def __init__(self, service_instance):
        super().__init__(service_instance)
        self._os_scheduler_service = None
        self._boot_time = datetime.datetime.utcnow()

    @property
    def os_scheduler(self):
        if self._os_scheduler_service is None:
            self._os_scheduler_service = self.kernel.get_service(
                "os_scheduler_service", is_system_call=True
            )
        return self._os_scheduler_service

    def register_routes(self):
        return {
            "POST /api/v1/engine/actions/schedule": self.handle_schedule_action,
            "POST /api/v1/engine/actions/cancel-schedule": self.handle_cancel_schedule,
            "GET /api/v1/engine/live-stats": self.handle_get_live_stats,
        }

    async def handle_get_live_stats(self, request):
        user_id_from_header = request.headers.get("X-Flowork-User-ID")

        active_jobs = []
        execution_stats_24h = {"success": 0, "failed": 0}
        top_failing_presets = Counter()
        slowest_presets_list = []
        is_processing_jobs = False

        db_service = Singleton.get_instance(DatabaseService)
        if not db_service and self.kernel:
            db_service = self.kernel.get_service("database_service")
        if not db_service and hasattr(self.service_instance, 'db_service'):
             db_service = self.service_instance.db_service

        if not db_service:
             self.logger(f"[CRITICAL ERROR] DatabaseService NOT FOUND.", "ERROR", "ApiServer")
             return self._json_response(self._build_empty_stats(self.kernel))

        conn = db_service.create_connection()
        if not conn:
             self.logger("[ERROR] DatabaseService found but failed to create connection.", "ERROR", "ApiServer")
             return self._json_response(self._build_empty_stats(self.kernel))

        try:
            cursor = conn.cursor()

            query_active = """
                SELECT e.execution_id, w.name, e.created_at
                FROM Executions e
                LEFT JOIN Workflows w ON e.workflow_id = w.workflow_id
                WHERE e.status = 'RUNNING'
            """
            params_active = []


            cursor.execute(query_active, tuple(params_active))
            active_rows = cursor.fetchall()

            if active_rows:
                for row in active_rows:
                    exec_id, preset_name, created_at = row
                    try:
                         start_dt = datetime.datetime.fromisoformat(str(created_at).replace(' ', 'T'))

                         if start_dt < (self._boot_time - datetime.timedelta(seconds=5)):
                             self.logger(f"[Zombie Hunter] Found zombie job {exec_id} from {start_dt}. Marking FAILED.", "WARN", "ApiServer")
                             cursor.execute("UPDATE Executions SET status = 'FAILED', finished_at = CURRENT_TIMESTAMP WHERE execution_id = ?", (exec_id,))
                             conn.commit()
                             continue # Skip adding to active list

                         duration = (datetime.datetime.utcnow() - start_dt).total_seconds()
                         is_processing_jobs = True
                         active_jobs.append({
                            "id": exec_id,
                            "preset": preset_name or "Unknown Workflow",
                            "duration_seconds": round(duration, 2)
                        })
                    except Exception as e:
                         self.logger(f"Error parsing active job {exec_id}: {e}", "WARN", "ApiServer")
                         continue

            query_stats = """
                SELECT status, COUNT(*)
                FROM Executions
                WHERE created_at >= datetime('now', '-1 day')
            """
            params_stats = []


            query_stats += " GROUP BY status"

            cursor.execute(query_stats, tuple(params_stats))
            stats_rows = cursor.fetchall()

            for status, count in stats_rows:
                s_upper = str(status).upper()
                if s_upper in ['DONE', 'SUCCEEDED']:
                    execution_stats_24h["success"] += count
                elif s_upper in ['FAILED', 'ERROR', 'STOPPED']:
                    execution_stats_24h["failed"] += count

            query_fail = """
                SELECT w.name, COUNT(*) as cnt
                FROM Executions e
                JOIN Workflows w ON e.workflow_id = w.workflow_id
                WHERE e.status = 'FAILED' AND e.created_at >= datetime('now', '-1 day')
            """
            params_fail = []


            query_fail += " GROUP BY w.name ORDER BY cnt DESC LIMIT 5"

            cursor.execute(query_fail, tuple(params_fail))
            fail_rows = cursor.fetchall()
            for name, count in fail_rows:
                top_failing_presets[name] = count

            query_slow = """
                SELECT w.name, AVG((julianday(e.finished_at) - julianday(e.created_at)) * 86400) as avg_dur
                FROM Executions e
                JOIN Workflows w ON e.workflow_id = w.workflow_id
                WHERE e.status = 'SUCCEEDED'
                  AND e.created_at >= datetime('now', '-1 day')
                  AND e.finished_at IS NOT NULL
            """
            params_slow = []


            query_slow += " GROUP BY w.name ORDER BY avg_dur DESC LIMIT 5"

            cursor.execute(query_slow, tuple(params_slow))
            slow_rows = cursor.fetchall()
            for name, avg_dur in slow_rows:
                if avg_dur:
                    slowest_presets_list.append({
                        "name": name,
                        "avg_duration_ms": avg_dur * 1000
                    })

        except Exception as e:
            self.logger(f"Error querying DB for live-stats: {e}", "ERROR", "ApiServer")
        finally:
            conn.close()

        preset_count = 0
        if self.service_instance.preset_manager and user_id_from_header:
            try:
                preset_list = self.service_instance.preset_manager.get_preset_list(user_id=user_id_from_header)
                preset_count = len(preset_list)
            except Exception:
                 pass

        top_failing_list = [{"name": name, "count": count} for name, count in top_failing_presets.items()]

        system_overview = {
            "kernel_version": self.kernel.APP_VERSION,
            "license_tier": self.kernel.license_tier.capitalize(),
            "is_busy": is_processing_jobs,
            "modules": len(self.service_instance.module_manager_service.loaded_modules) if self.service_instance.module_manager_service else 0,
            "plugins": len(self.service_instance.plugin_manager_service.loaded_plugins) if self.service_instance.plugin_manager_service else 0,
            "widgets": len(self.service_instance.widget_manager_service.loaded_widgets) if self.service_instance.widget_manager_service else 0,
            "triggers": len(self.service_instance.trigger_manager_service.loaded_triggers) if self.service_instance.trigger_manager_service else 0,
            "presets": preset_count,
        }

        live_data = {
            "active_jobs": active_jobs,
            "system_overview": system_overview,
            "execution_stats_24h": execution_stats_24h,
            "top_failing_presets": top_failing_list,
            "top_slowest_presets": slowest_presets_list,
            "recent_activity": list(self.service_instance.recent_events),
            "usage_stats": {"used": execution_stats_24h["success"] + execution_stats_24h["failed"]}
        }

        return self._json_response(live_data)

    def _build_empty_stats(self, kernel):
        return {
            "active_jobs": [],
            "system_overview": {
                "kernel_version": kernel.APP_VERSION if kernel else "Unknown",
                "status": "db_unavailable"
            },
            "execution_stats_24h": {"success": 0, "failed": 0},
            "top_failing_presets": [],
            "top_slowest_presets": [],
            "recent_activity": [],
            "usage_stats": {"used": 0}
        }

    async def handle_schedule_action(self, request):
        try:
            permission_manager = self.kernel.get_service(
                "permission_manager_service", is_system_call=True
            )
            if permission_manager:
                permission_manager.check_permission("engine_management")

            body = await request.json()
            action_type = body.get("action_type")
            timestamp_str = body.get("timestamp")
            task_name = body.get("task_name")

            if not all([action_type, timestamp_str, task_name]):
                return self._json_response(
                    {"error": "Missing action_type, timestamp, or task_name"},
                    status=400,
                )

            scheduled_dt = datetime.datetime.fromisoformat(timestamp_str)
            if not self.os_scheduler:
                return self._json_response(
                    {"error": "OsSchedulerService is not available."}, status=503
                )

            success = self.os_scheduler.schedule_action(
                action_type, scheduled_dt, task_name
            )

            if success:
                return self._json_response(
                    {
                        "status": "success",
                        "message": f"Action '{action_type}' scheduled successfully.",
                    },
                    status=202,
                )
            else:
                return self._json_response(
                    {"error": "Failed to schedule action via OS scheduler."}, status=500
                )

        except PermissionDeniedError as e:
            return self._json_response({"error": str(e)}, status=403)
        except Exception as e:
            self.logger(f"Error handling schedule action: {e}", "CRITICAL")
            return self._json_response(
                {"error": f"Internal Server Error: {e}"}, status=500
            )

    async def handle_cancel_schedule(self, request):
        try:
            permission_manager = self.kernel.get_service(
                "permission_manager_service", is_system_call=True
            )
            if permission_manager:
                permission_manager.check_permission("engine_management")

            body = await request.json()
            task_name = body.get("task_name")

            if not task_name:
                return self._json_response({"error": "Missing task_name"}, status=400)

            if not self.os_scheduler:
                return self._json_response(
                    {"error": "OsSchedulerService is not available."}, status=503
                )

            success = self.os_scheduler.cancel_task(task_name)

            if success:
                return self._json_response(
                    {
                        "status": "success",
                        "message": f"Task '{task_name}' cancelled successfully.",
                    },
                    status=200,
                )
            else:
                return self._json_response(
                    {
                        "error": f"Failed to cancel task '{task_name}'. It may have already run or does not exist."
                    },
                    status=404,
                )

        except PermissionDeniedError as e:
            return self._json_response({"error": str(e)}, status=403)
        except Exception as e:
            self.logger(f"Error handling cancel schedule action: {e}", "CRITICAL")
            return self._json_response(
                {"error": f"Internal Server Error: {e}"}, status=500
            )
