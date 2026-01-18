########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scheduler_service\register_schedule.py total lines 18 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

async def run(hub, app_id, schedule_entry):
    cron_str = schedule_entry.get("cron")
    action = schedule_entry.get("action")

    if cron_str and action:
        hub.active_schedules.append({
            "app_id": app_id,
            "cron": cron_str,
            "action": action,
            "last_run": 0
        })
        hub.logger.info(f"📍 [Scheduler] Registered: {app_id} -> {action} ({cron_str})")
