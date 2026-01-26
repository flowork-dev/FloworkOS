########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\chatgpt_app\backend\app_router.py total lines 16 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

class AppRouter:
    def __init__(self, service_instance):
        self.service = service_instance

    def get_routes(self):
        """Daftar kabel saraf yang bisa diakses oleh Kernel Gateway"""
        return {
            "generate": self.service.generate,
            "status": self.service.status
        }
