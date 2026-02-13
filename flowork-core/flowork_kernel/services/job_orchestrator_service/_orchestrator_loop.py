########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\_orchestrator_loop.py total lines 26 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import traceback

def run(hub, *args, **kwargs):
    hub.logger.info("Orchestrator Loop Started")

    while hub.running:
        try:
            job = hub.execute_sync('_fetch_next_job')

            if job:
                hub.logger.info(f"Processing Job: {job.get('job_id')}")
                hub.execute_sync('_execute_job', job)
            else:
                time.sleep(1)

        except Exception as e:
            hub.logger.error(f"Orchestrator Loop Error: {e}")
            traceback.print_exc()
            time.sleep(5)
