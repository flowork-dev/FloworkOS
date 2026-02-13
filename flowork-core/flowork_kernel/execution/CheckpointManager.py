########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\execution\CheckpointManager.py total lines 37 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

class CheckpointManager:

    def __init__(self, kernel):

        self.kernel = kernel
        self.state_manager = self.kernel.get_service("state_manager")
    def save(self, context_id: str, node_id: str, payload: dict, node_name: str):

        if not self.state_manager:
            self.kernel.write_to_log("CheckpointManager Error: StateManager service not available.", "ERROR")
            return
        checkpoint_key = f"checkpoint::{context_id}"
        checkpoint_data = {
            "node_id": node_id,
            "payload": payload
        }
        self.state_manager.set(checkpoint_key, checkpoint_data)
        self.kernel.write_to_log(f"CHECKPOINT: Workflow state saved after node '{node_name}'.", "INFO")
    def load(self, context_id: str):

        if not self.state_manager:
            return None, None
        checkpoint_key = f"checkpoint::{context_id}"
        saved_checkpoint = self.state_manager.get(checkpoint_key)
        if saved_checkpoint and isinstance(saved_checkpoint, dict):
            resume_node_id = saved_checkpoint.get("node_id")
            resume_payload = saved_checkpoint.get("payload")
            if resume_node_id and resume_payload is not None:
                self.state_manager.delete(checkpoint_key)
                return resume_node_id, resume_payload
        return None, None
