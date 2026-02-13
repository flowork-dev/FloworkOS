########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\app_builder\backend\logic\get_app_logs.py total lines 25 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os

def run(context, data, *args, **kwargs):
    """
    The Eyes: Membaca log untuk feedback loop evolusi.
    """
    app_id = data.get('app_id')
    log_path = "C:\\FLOWORK\\logs\\flowork.log" if os.name == 'nt' else "/app/logs/flowork.log"

    if not os.path.exists(log_path):
        return {"status": "error", "message": "Log file not discovered."}

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            relevant = [l for l in lines if app_id in l][-100:]
            return {"status": "success", "logs": "".join(relevant)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
