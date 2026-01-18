########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\_touch_app_activity.py total lines 21 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time

def run(hub, app_id):
    """
    Menandai bahwa App sedang aktif/sibuk.
    Sinkron ke dua variabel untuk kompatibilitas sistem Lazarus & GhostReaper.
    """
    if not app_id:
        return

    now = time.time()

    hub.app_activity[app_id] = now

    hub.last_activity[app_id] = now
