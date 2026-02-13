########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\gemini_provider\core\GeminiConnection.py total lines 66 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import logging
import sqlite3
import sys
import importlib
import pkgutil

logger = logging.getLogger("Provider.Gemini")

class GeminiConnection:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None

    def _fetch_from_db(self, key_name):
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

    def connect(self):
        if not self.api_key: self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key: self.api_key = self._fetch_from_db("GEMINI_API_KEY")
        if not self.api_key: return None

        try:
            import google
            if not hasattr(google, 'genai'):
                for loader, name, ispkg in pkgutil.walk_packages(google.__path__, google.__name__ + '.'):
                    if 'genai' in name:
                        importlib.import_module(name)

            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            return self.client
        except Exception as e:
            logger.error(f"❌ [GeminiConnection] SDK Import Failure: {e}")
            return None

    def get_client(self):
        if not self.client: self.connect()
        return self.client

    def generate_content(self, model_name, prompt):
        client = self.get_client()
        if not client:
            return "ERROR: Gemini SDK (google-genai) gagal di-import. Pastikan docker sudah di-rebuild atau library sudah terinstall sempurna."

        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text
        except Exception as e:
            return f"ERROR: {e}"
