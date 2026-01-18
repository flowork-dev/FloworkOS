########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\deepseek_provider\core\DeepSeekConnection.py total lines 91 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import requests
import json
import os
import sqlite3 # [ADDITION]

class DeepSeekConnection:
    def __init__(self, kernel):
        self.kernel = kernel
        self.api_key = None
        self.base_url = "https://api.deepseek.com"

    def _fetch_from_db(self, key_name):
        """[ADDITION] Direct SQLite Bypass."""
        db_paths = ["/app/data/flowork_core.db", "C:\\FLOWORK\\data\\flowork_core.db"]
        db_path = next((p for p in db_paths if os.path.exists(p)), None)
        if not db_path: return None
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM variables WHERE name = ? LIMIT 1", (key_name,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except: return None

    def configure(self, user_id=None):
        """Ambil API Key dengan proteksi MockKernel."""
        try:
            if hasattr(self.kernel, 'variable_manager'):
                self.api_key = self.kernel.variable_manager.get_variable("DEEPSEEK_API_KEY", user_id=user_id)
        except:
            self.api_key = None

        if not self.api_key:
            self.api_key = os.environ.get("DEEPSEEK_API_KEY")

        if not self.api_key:
            self.api_key = self._fetch_from_db("DEEPSEEK_API_KEY")

        if not self.api_key:
            if hasattr(self.kernel, 'write_to_log'):
                self.kernel.write_to_log("[DeepSeekConnection] API Key missing.", "WARNING")
            return False
        return True

    def get_chat_completion(self, prompt, model="deepseek-chat", messages=None, **kwargs):
        if not self.api_key:
            return {"error": "Not configured"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        history = messages if messages else []
        if not history:
            history = [{"role": "user", "content": prompt}]

        payload = {
            "model": model,
            "messages": history,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7)
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                return {"data": result['choices'][0]['message']['content']}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}

    def get_embeddings(self, text: str):
        return []

    def list_available_models(self):
        return ["deepseek-chat", "deepseek-reasoner"]
