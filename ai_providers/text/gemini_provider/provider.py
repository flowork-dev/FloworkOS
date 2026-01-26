########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\gemini_provider\provider.py total lines 48 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import logging
from .core.GeminiConnection import GeminiConnection

class GeminiProvider:
    def __init__(self, kernel, manifest: dict, *args, **kwargs):
        self.kernel = kernel
        self.manifest = manifest
        self.connection = GeminiConnection()

    def list_available_models(self) -> list:
        return ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]

    def is_ready(self, user_id=None, **kwargs) -> tuple[bool, str]:
        """Tiru AI Council - Direct DB Fetching"""
        uid = user_id or kwargs.get('user_id')
        db_path = "C:\\FLOWORK\\data\\flowork_core.db" if os.name == 'nt' else "/app/data/flowork_core.db"

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM variables WHERE name = ? LIMIT 1", ("GEMINI_API_KEY",))
            row = cursor.fetchone()
            if row: os.environ["GEMINI_API_KEY"] = str(row[0])
            conn.close()
        except: pass

        if not os.environ.get("GEMINI_API_KEY"):
            return (False, "GEMINI_API_KEY missing.")
        return (True, "")

    def generate_response(self, prompt, **kwargs):
        is_ready, msg = self.is_ready(user_id=kwargs.get('user_id'))
        if not is_ready: return {"status": "error", "message": msg}

        try:
            target_model = kwargs.get('model', 'gemini-2.0-flash-exp')
            res = self.connection.generate_content(target_model, prompt)
            return {"status": "success", "data": res}
        except Exception as e:
            return {"status": "error", "message": str(e)}
