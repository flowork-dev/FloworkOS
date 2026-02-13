########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\engine_routes\handle_get_live_stats.py total lines 99 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import datetime
import time
import json
from .base_api_route import BaseApiRoute
from flowork_kernel.exceptions import PermissionDeniedError
from collections import Counter, defaultdict
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.database_service.database_service import DatabaseService


async def run(hub, request):
    user_id_from_header = request.headers.get('X-Flowork-User-ID')
    active_jobs = []
    execution_stats_24h = {'success': 0, 'failed': 0}
    top_failing_presets = Counter()
    slowest_presets_list = []
    is_processing_jobs = False
    db_service = Singleton.get_instance(DatabaseService)
    if not db_service and hub.kernel:
        db_service = hub.kernel.get_service('database_service')
    if not db_service and hasattr(hub.service_instance, 'db_service'):
        db_service = hub.service_instance.db_service
    if not db_service:
        await hub.execute_async('logger', f'[CRITICAL ERROR] DatabaseService NOT FOUND.', 'ERROR', 'ApiServer')
        return await hub.execute_async('_json_response', self._build_empty_stats(self.kernel))
    conn = db_service.create_connection()
    if not conn:
        await hub.execute_async('logger', '[ERROR] DatabaseService found but failed to create connection.', 'ERROR', 'ApiServer')
        return await hub.execute_async('_json_response', self._build_empty_stats(self.kernel))
    try:
        cursor = conn.cursor()
        query_active = "\n                SELECT e.execution_id, w.name, e.created_at\n                FROM Executions e\n                LEFT JOIN Workflows w ON e.workflow_id = w.workflow_id\n                WHERE e.status = 'RUNNING'\n            "
        params_active = []
        cursor.execute(query_active, tuple(params_active))
        active_rows = cursor.fetchall()
        if active_rows:
            for row in active_rows:
                (exec_id, preset_name, created_at) = row
                try:
                    start_dt = datetime.datetime.fromisoformat(str(created_at).replace(' ', 'T'))
                    if start_dt < hub._boot_time - datetime.timedelta(seconds=5):
                        await hub.execute_async('logger', f'[Zombie Hunter] Found zombie job {exec_id} from {start_dt}. Marking FAILED.', 'WARN', 'ApiServer')
                        cursor.execute("UPDATE Executions SET status = 'FAILED', finished_at = CURRENT_TIMESTAMP WHERE execution_id = ?", (exec_id,))
                        conn.commit()
                        continue
                    duration = (datetime.datetime.utcnow() - start_dt).total_seconds()
                    is_processing_jobs = True
                    active_jobs.append({'id': exec_id, 'preset': preset_name or 'Unknown Workflow', 'duration_seconds': round(duration, 2)})
                except Exception as e:
                    await hub.execute_async('logger', f'Error parsing active job {exec_id}: {e}', 'WARN', 'ApiServer')
                    continue
        query_stats = "\n                SELECT status, COUNT(*)\n                FROM Executions\n                WHERE created_at >= datetime('now', '-1 day')\n            "
        params_stats = []
        query_stats += ' GROUP BY status'
        cursor.execute(query_stats, tuple(params_stats))
        stats_rows = cursor.fetchall()
        for (status, count) in stats_rows:
            s_upper = str(status).upper()
            if s_upper in ['DONE', 'SUCCEEDED']:
                execution_stats_24h['success'] += count
            elif s_upper in ['FAILED', 'ERROR', 'STOPPED']:
                execution_stats_24h['failed'] += count
        query_fail = "\n                SELECT w.name, COUNT(*) as cnt\n                FROM Executions e\n                JOIN Workflows w ON e.workflow_id = w.workflow_id\n                WHERE e.status = 'FAILED' AND e.created_at >= datetime('now', '-1 day')\n            "
        params_fail = []
        query_fail += ' GROUP BY w.name ORDER BY cnt DESC LIMIT 5'
        cursor.execute(query_fail, tuple(params_fail))
        fail_rows = cursor.fetchall()
        for (name, count) in fail_rows:
            top_failing_presets[name] = count
        query_slow = "\n                SELECT w.name, AVG((julianday(e.finished_at) - julianday(e.created_at)) * 86400) as avg_dur\n                FROM Executions e\n                JOIN Workflows w ON e.workflow_id = w.workflow_id\n                WHERE e.status = 'SUCCEEDED'\n                  AND e.created_at >= datetime('now', '-1 day')\n                  AND e.finished_at IS NOT NULL\n            "
        params_slow = []
        query_slow += ' GROUP BY w.name ORDER BY avg_dur DESC LIMIT 5'
        cursor.execute(query_slow, tuple(params_slow))
        slow_rows = cursor.fetchall()
        for (name, avg_dur) in slow_rows:
            if avg_dur:
                slowest_presets_list.append({'name': name, 'avg_duration_ms': avg_dur * 1000})
    except Exception as e:
        await hub.execute_async('logger', f'Error querying DB for live-stats: {e}', 'ERROR', 'ApiServer')
    finally:
        conn.close()
    preset_count = 0
    if hub.service_instance.preset_manager and user_id_from_header:
        try:
            preset_list = hub.service_instance.preset_manager.get_preset_list(user_id=user_id_from_header)
            preset_count = len(preset_list)
        except Exception:
            pass
    top_failing_list = [{'name': name, 'count': count} for (name, count) in top_failing_presets.items()]
    app_srv = hub.service_instance.app_service
    system_overview = {'kernel_version': hub.kernel.APP_VERSION, 'license_tier': hub.kernel.license_tier.capitalize(), 'is_busy': is_processing_jobs, 'modules': len(getattr(app_srv, 'loaded_modules', {})) if app_srv else 0, 'plugins': len(getattr(app_srv, 'loaded_plugins', {})) if app_srv else 0, 'widgets': len(getattr(app_srv, 'loaded_widgets', {})) if app_srv else 0, 'triggers': len(getattr(app_srv, 'loaded_triggers', {})) if app_srv else 0, 'presets': preset_count}
    live_data = {'active_jobs': active_jobs, 'system_overview': system_overview, 'execution_stats_24h': execution_stats_24h, 'top_failing_presets': top_failing_list, 'top_slowest_presets': slowest_presets_list, 'recent_activity': list(hub.service_instance.recent_events), 'usage_stats': {'used': execution_stats_24h['success'] + execution_stats_24h['failed']}}
    return await hub.execute_async('_json_response', live_data)
