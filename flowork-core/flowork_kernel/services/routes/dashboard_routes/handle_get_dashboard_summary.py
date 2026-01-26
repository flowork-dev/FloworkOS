########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\routes\dashboard_routes\handle_get_dashboard_summary.py total lines 50 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import time
from collections import Counter
from .base_api_route import BaseApiRoute


async def run(hub, request):
    active_jobs = []
    if hub.service_instance.job_statuses:
        with hub.service_instance.job_statuses_lock:
            for (job_id, job_data) in hub.service_instance.job_statuses.items():
                if job_data.get('status') == 'RUNNING':
                    start_time = job_data.get('start_time', 0)
                    duration = time.time() - start_time
                    active_jobs.append({'id': job_id, 'preset': job_data.get('preset_name', 'N/A'), 'duration_seconds': round(duration, 2)})
    recent_events = list(hub.service_instance.recent_events)
    execution_stats = {'success': 0, 'failed': 0}
    preset_counter = Counter()
    history_file_path = os.path.join(hub.kernel.data_path, 'metrics_history.jsonl')
    twenty_four_hours_ago = time.time() - 24 * 60 * 60
    try:
        if os.path.exists(history_file_path):
            with open(history_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        metric = log_entry.get('metrics', {})
                        if metric.get('timestamp', 0) >= twenty_four_hours_ago:
                            status = metric.get('status')
                            if status == 'SUCCESS':
                                execution_stats['success'] += 1
                            elif status in ['ERROR', 'FAILED']:
                                execution_stats['failed'] += 1
                            preset_name = metric.get('preset_name')
                            if preset_name:
                                preset_counter[preset_name] += 1
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        await hub.execute_async('logger', f'Dashboard API: Could not read or parse metrics log: {e}', 'WARN')
    top_presets = [{'name': name, 'count': count} for (name, count) in preset_counter.most_common(5)]
    summary_data = {'active_jobs': active_jobs, 'recent_events': recent_events, 'execution_stats_24h': execution_stats, 'top_presets_24h': top_presets}
    return await hub.execute_async('_json_response', summary_data)
