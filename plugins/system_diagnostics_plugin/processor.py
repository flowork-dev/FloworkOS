########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\plugins\system_diagnostics_plugin\processor.py total lines 14 
########################################################################

from flowork_kernel.api_contract import BaseModule
class SystemDiagnosticsPlugin(BaseModule):

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.diagnostics_service = self.kernel.get_service("diagnostics_service")
    def execute(self, payload, config, status_updater, mode='EXECUTE', **kwargs):
        return payload
