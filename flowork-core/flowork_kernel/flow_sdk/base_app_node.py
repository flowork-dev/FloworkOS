########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\flow_sdk\base_app_node.py total lines 151 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import time
import uuid
import logging
from abc import ABC, abstractmethod

class BaseAppNode(ABC):
    """
    Base Class untuk semua App Node di Flowork.
    [GEMINI FIX] Updated signature to support (node_id, properties, kernel)
    and added **kwargs to execute() for worker compatibility.
    """
    def __init__(self, node_id=None, properties=None, kernel=None, context=None):
        if isinstance(node_id, dict) and properties is None:
            self.context = node_id
            self.node_id = self.context.get("id")
            self.properties = self.context.get("config_values", {})
            self.kernel = self.context.get("kernel")
        else:
            self.node_id = node_id
            self.properties = properties or {}
            self.kernel = kernel
            self.context = context or {}

        self.logger = getattr(self.kernel, 'logger', logging.getLogger("BaseAppNode"))
        self.manifest_def = self.context.get("node_def", {})

        if not self.kernel and isinstance(self.context, dict):
            self.kernel = self.context.get('kernel')

        self.user_id = "default_user"
        if isinstance(self.context, dict) and "user_context" in self.context:
             uc = self.context["user_context"]
             if uc and isinstance(uc, dict):
                 self.user_id = uc.get("user_id", "default_user")

        if os.getenv("FLOWORK_USER_ID"):
             self.user_id = os.getenv("FLOWORK_USER_ID")

        self.base_data_dir = os.getenv("FLOWORK_DATA_DIR", r"C:\FLOWORK\data" if os.name == 'nt' else "./data")

        self.user_workspace = os.path.join(self.base_data_dir, "users", self.user_id)
        self._ensure_workspace()

    def _ensure_workspace(self):
        """Memastikan folder user ada sebelum dipakai."""
        if not os.path.exists(self.user_workspace):
            try:
                os.makedirs(self.user_workspace, exist_ok=True)
            except Exception as e:
                self.logger.error(f"[SDK] Failed to create workspace: {e}")

    def get_file_path(self, filename: str) -> str:
        """[SECURE PATH RESOLVER] Mencegah Directory Traversal (../)"""
        clean_name = os.path.basename(filename)
        return os.path.join(self.user_workspace, clean_name)

    def save_text(self, filename: str, content: str):
        """Helper praktis untuk simpan text ke user workspace."""
        path = self.get_file_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.logger.info(f"[SDK] Saved to: {path}")
        return path

    def load_text(self, filename: str) -> str:
        """Helper praktis untuk baca text dari user workspace."""
        path = self.get_file_path(filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def get_arg(self, inputs: dict, name: str, default=None):
        """Retrieves a value from inputs safely."""
        val = inputs.get(name)
        if val is not None:
            return val
        if self.manifest_def:
            for field in self.manifest_def.get("inputs", []):
                if field.get("name") == name:
                    return field.get("default", default)
        return default

    def set_output(self, port_name: str, data: any) -> dict:
        """Standard way to structure output."""
        return {port_name: data}

    @abstractmethod
    async def execute(self, input_data=None, **kwargs):
        """
        [GEMINI FIX] Added **kwargs to prevent TypeError when called by JobWorker
        with named arguments (payload, config, status_updater).
        """
        raise NotImplementedError("App Node must implement execute()")

    def request_frontend_action(self, action_name, payload, timeout=60):
        """JURUS HYBRID: Python <-> Browser sync bridge."""
        if not self.kernel:
            self.logger.warning("Kernel context missing. Hybrid features might fail.")

        event_bus = self.kernel.get_service("event_bus") if self.kernel else None
        if not event_bus:
            self.logger.error("EventBus service missing. Cannot signal Frontend.")
            return None

        job_id = "unknown"
        if isinstance(self.context, dict):
             job_id = self.context.get("job_id", "unknown_job")

        request_id = f"req_{job_id}_{uuid.uuid4().hex[:8]}"

        session_id = "broadcast"
        if isinstance(self.context, dict) and "user_context" in self.context:
             uc = self.context["user_context"]
             if uc and isinstance(uc, dict):
                 session_id = uc.get("session_id", "broadcast")

        self.logger.info(f"🌉 [HybridBridge] Requesting Frontend Action: {action_name}")

        event_bus.publish(
            "HYBRID_ACTION_REQUEST",
            {
                "request_id": request_id,
                "target_session": session_id,
                "app_id": getattr(self, 'app_id', 'unknown_app'),
                "action": action_name,
                "payload": payload
            }
        )

        if self.kernel:
            if not hasattr(self.kernel, "memory_store"):
                self.kernel.memory_store = {}

            start_time = time.time()
            while time.time() - start_time < timeout:
                response_key = f"response_{request_id}"
                if response_key in self.kernel.memory_store:
                    result = self.kernel.memory_store.pop(response_key)
                    self.logger.info(f"✅ [HybridBridge] Received Response")
                    return result
                time.sleep(0.5)

            raise TimeoutError(f"Frontend did not respond within {timeout}s.")
