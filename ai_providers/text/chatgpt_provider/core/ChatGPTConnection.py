########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\chatgpt_provider\core\ChatGPTConnection.py total lines 142 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import requests
import json
import sqlite3 # [ADDITION] Support Direct DB Access

class ChatGPTConnection:
    def __init__(self, kernel):
        self.kernel = kernel
        self.api_key = None
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.emb_url = "https://api.openai.com/v1/embeddings"

    def _fetch_from_db(self, key_name):
        """[ADDITION] IronBank Logic: Ambil key langsung dari SQLite jika kernel Mock."""
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

    def configure(self):
        try:
            if hasattr(self.kernel, 'variable_manager'):
                self.api_key = self.kernel.variable_manager.get_variable("OPENAI_API_KEY")
        except:
            self.api_key = None

        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            self.api_key = self._fetch_from_db("OPENAI_API_KEY")

        if not self.api_key:
            if hasattr(self.kernel, 'write_to_log'):
                self.kernel.write_to_log("[ChatGPTConnection] API Key not found in DB or Env.", "WARNING")
            return False

        return True

    def get_chat_completion(self, prompt, messages=None, model="gpt-4o"):
        if not self.api_key:
            return {"error": "Missing API Key"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload_messages = []
        if messages:
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if content:
                    payload_messages.append({"role": role, "content": content})

        if not payload_messages or payload_messages[-1]["content"] != prompt:
            payload_messages.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": payload_messages,
            "max_tokens": 4096
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return {"data": content}
        except Exception as e:
            return {"error": str(e)}

    def get_chat_stream(self, prompt, messages=None, model="gpt-4o"):
        if not self.api_key:
            yield "Error: Missing API Key"
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload_messages = []
        if messages:
            for m in messages:
                payload_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        payload_messages.append({"role": "user", "content": prompt})

        data = { "model": model, "messages": payload_messages, "stream": True }

        try:
            with requests.post(self.api_url, headers=headers, json=data, stream=True, timeout=60) as r:
                for line in r.iter_lines():
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: ') and line_str != 'data: [DONE]':
                            try:
                                json_str = line_str[6:]
                                chunk = json.loads(json_str)
                                delta = chunk['choices'][0]['delta']
                                if 'content' in delta:
                                    yield delta['content']
                            except: pass
        except Exception as e:
            yield f"[Stream Error: {e}]"

    def get_embeddings(self, text: str, model="text-embedding-3-small"):
        if not self.api_key:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "model": model
        }

        try:
            res = requests.post(self.emb_url, headers=headers, json=data, timeout=30)
            res.raise_for_status()
            return res.json()['data'][0]['embedding']
        except Exception as e:
            if hasattr(self.kernel, 'write_to_log'):
                self.kernel.write_to_log(f"[ChatGPT] Embedding Request Failed: {e}", "ERROR")
            return []
