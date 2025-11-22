########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\prompt_receiver_module\processor.py total lines 38 
########################################################################

from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
class PromptReceiverModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"
    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.node_instance_id = None
    def on_canvas_load(self, node_id: str):

        self.node_instance_id = node_id
        self.logger(
            f"Receiver node '{self.node_instance_id}' is ready on the canvas.", "INFO"
        )
    def execute(
        self, payload, config, status_updater, mode="EXECUTE", **kwargs
    ):

        self.node_instance_id = config.get(
            "__internal_node_id", self.node_instance_id or self.module_id
        )
        status_updater(f"Passing data through...", "INFO")
        status_updater("Data received and passed.", "SUCCESS")
        return {"payload": payload, "output_name": "output"}
    def _copy_node_id_to_clipboard(self, node_id):

        pass
    def get_data_preview(self, config: dict):

        self.logger(
            f"'get_data_preview' is not yet implemented for {self.module_id}", "WARN"
        )
        return [{"status": "preview not implemented"}]
