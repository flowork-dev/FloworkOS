########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\app_builder\main.py total lines 15 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

def run(app_context, action=None, data=None, *args, **kwargs):
    """
    Entry point utama App-Builder.
    Meneruskan perintah ke backend router jika ada action.
    """
    if action:
        return app_context.execute_backend("app_router", action=action, data=data)

    return {"status": "ready", "message": "App Builder UI is active."}
