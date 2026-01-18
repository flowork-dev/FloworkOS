########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\generated_services\core_lifecycle_service\service.py total lines 16 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.kernel_logic import ServiceWorkflowProxy
from flowork_kernel.services.base_service import BaseService

class CoreLifecycleService(BaseService):
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.proxy = ServiceWorkflowProxy(kernel, service_id, "core_services/core_lifecycle.flowork")

    def start__core__lifecycle(self, *args, **kwargs):
        return self.proxy.start__core__lifecycle(*args, **kwargs)
