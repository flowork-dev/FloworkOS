########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\deepseek_provider\provider.py total lines 91 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import inspect
import sqlite3 # [ADDITION] Direct DB Support
try:
    from flowork_kernel.api_contract import BaseAIProvider
except ImportError:
    from ai_providers.BaseAIProvider import BaseAIProvider

from .core.DeepSeekConnection import DeepSeekConnection

class DeepSeekProvider(BaseAIProvider):

    def __init__(self, kernel, manifest: dict):
        super().__init__(kernel, manifest)
        self.connection = DeepSeekConnection(self.kernel)

    def list_available_models(self) -> list:
        return ["deepseek-chat", "deepseek-reasoner"]

    def _iron_bank_fetch(self, key_name, user_id=None):
        """[ADDITION] Direct DB Access Bypass"""
        db_paths = ["/app/data/flowork_core.db", "C:\\FLOWORK\\data\\flowork_core.db"]
        db_path = next((p for p in db_paths if os.path.exists(p)), None)
        if not db_path: return None
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(variables)")
            cols = [c[1] for c in cursor.fetchall()]
            key_col = next((x for x in ["name", "key"] if x in cols), "name")
            val_col = "value" if "value" in cols else "val"

            if user_id:
                cursor.execute(f"SELECT {val_col} FROM variables WHERE {key_col} = ? AND user_id = ? LIMIT 1", (key_name, user_id))
                row = cursor.fetchone()
                if row: return row[0]

            cursor.execute(f"SELECT {val_col} FROM variables WHERE {key_col} = ? AND user_id IS NULL LIMIT 1", (key_name,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except: return None

    def get_provider_name(self) -> str:
        return self.loc.get("deepseek_provider_name", fallback="DeepSeek AI")

    def is_ready(self, user_id=None, **kwargs) -> tuple[bool, str]:
        """[REINFORCED] Anti-MockKernel Logic"""
        uid = user_id or kwargs.get('user_id')
        api_key = None

        try:
            if hasattr(self.kernel, 'get_service'):
                var_service = self.kernel.get_service('variable_manager')
                api_key = var_service.get_variable("DEEPSEEK_API_KEY", user_id=uid)
        except: pass

        if not api_key:
            api_key = self._iron_bank_fetch("DEEPSEEK_API_KEY", user_id=uid)

        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = str(api_key)

        try:
            sig = inspect.signature(self.connection.configure)
            success = self.connection.configure(user_id=uid) if 'user_id' in sig.parameters else self.connection.configure()
            if success: return (True, "")
        except: pass

        return (False, "DeepSeek API Key not found in Database.")

    def generate_response(self, prompt: str, **kwargs) -> dict:
        user_id = kwargs.get('user_id')
        is_ready, message = self.is_ready(user_id=user_id)
        if not is_ready:
            return {"status": "error", "message": message}

        target_model = kwargs.get('model', "deepseek-chat")
        try:
            response_dict = self.connection.get_chat_completion(prompt, model=target_model, messages=kwargs.get('messages'))
            if "error" in response_dict:
                return {"status": "error", "message": response_dict['error']}
            return {"status": "success", "data": response_dict["data"]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
