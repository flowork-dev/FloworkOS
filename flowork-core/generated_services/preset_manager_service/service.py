########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\generated_services\preset_manager_service\service.py total lines 34 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.kernel_logic import ServiceWorkflowProxy
from flowork_kernel.services.base_service import BaseService

class PresetManagerService(BaseService):
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.proxy = ServiceWorkflowProxy(kernel, service_id, "core_services/preset_manager.flowork")

    def get_preset_versions(self, *args, **kwargs):
        return self.proxy.get_preset_versions(*args, **kwargs)

    def load_preset_version(self, *args, **kwargs):
        return self.proxy.load_preset_version(*args, **kwargs)

    def delete_preset(self, *args, **kwargs):
        return self.proxy.delete_preset(*args, **kwargs)

    def delete_preset_version(self, *args, **kwargs):
        return self.proxy.delete_preset_version(*args, **kwargs)

    def get_preset_data(self, *args, **kwargs):
        return self.proxy.get_preset_data(*args, **kwargs)

    def get_preset_list(self, *args, **kwargs):
        return self.proxy.get_preset_list(*args, **kwargs)

    def save_preset(self, *args, **kwargs):
        return self.proxy.save_preset(*args, **kwargs)
