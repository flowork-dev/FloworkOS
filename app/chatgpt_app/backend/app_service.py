########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\chatgpt_app\backend\app_service.py total lines 114 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import logging
import json
import asyncio
import sqlite3
import sys
import requests

class ChatGPTService:
    def __init__(self, kernel_stub, service_id):
        self.hub = kernel_stub
        self.service_id = service_id
        self.logger = logging.getLogger("App.Jarvis")
        self.keys = {}
        self.identity = "You are Assistant Flowork, a supreme neural interface integrated into the FloworkOS micro-kernel system."
        self.inject_secrets()
        self._neural_path_linker()

    def _neural_path_linker(self):
        """Force inject global library paths"""
        warehouse_path = "/app/data/global_libs"
        if not os.path.exists(warehouse_path): warehouse_path = "C:\\FLOWORK\\data\\global_libs"
        if os.path.exists(warehouse_path):
            if warehouse_path not in sys.path: sys.path.append(warehouse_path)
            for entry in os.scandir(warehouse_path):
                if entry.is_dir():
                    if entry.path not in sys.path: sys.path.append(entry.path)
                    try:
                        for sub in os.scandir(entry.path):
                            if sub.is_dir() and sub.path not in sys.path: sys.path.append(sub.path)
                    except: pass

    def inject_secrets(self):
        """Dynamic Column Detection mirroring AI Council"""
        target_vars = ["OPENAI_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY"]
        db_path = "/app/data/flowork_core.db"
        if not os.path.exists(db_path): db_path = "C:\\FLOWORK\\data\\flowork_core.db"
        if not os.path.exists(db_path): return

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(variables)")
            cols = [c[1] for c in cursor.fetchall()]
            key_col = next((x for x in ["name", "key", "variable_name"] if x in cols), None)
            val_col = "value" if "value" in cols else "val"

            if key_col:
                for key in target_vars:
                    cursor.execute(f"SELECT {val_col} FROM variables WHERE {key_col} = ? LIMIT 1", (key,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        self.keys[key] = str(row[0])
                        os.environ[key] = self.keys[key]
            conn.close()
        except Exception as e:
            self.logger.error(f"❌ [IronBank] Secret injection failed: {e}")

    async def generate(self, payload):
        prompt = payload.get("prompt", "")
        provider = payload.get("model_provider", "openai")

        if not prompt: return {"status": "error", "message": "Neural command empty."}

        if any(x in prompt.lower() for x in ["siapa kamu", "who are you", "identitas"]):
            return {"status": "success", "data": "I am AI Flowork, your supreme neural assistant within the FloworkOS architecture."}

        try:
            if provider == "openai": return await self._query_openai(prompt)
            elif provider == "gemini": return await self._query_gemini(prompt)
            elif provider == "deepseek": return await self._query_deepseek(prompt)
            return {"status": "error", "message": "Unknown Neural Engine."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _query_openai(self, prompt):
        key = self.keys.get("OPENAI_API_KEY")
        if not key: return {"status": "error", "message": "OpenAI Key Missing"}
        import openai
        client = openai.OpenAI(api_key=key)
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": self.identity}, {"role": "user", "content": prompt}]
        )
        return {"status": "success", "data": res.choices[0].message.content}

    async def _query_gemini(self, prompt):
        key = self.keys.get("GEMINI_API_KEY")
        if not key: return {"status": "error", "message": "Gemini Key Missing"}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": f"{self.identity}\n\nCommand: {prompt}"}]}]}
        r = requests.post(url, json=payload, timeout=60)
        if r.status_code == 200:
            return {"status": "success", "data": r.json()['candidates'][0]['content']['parts'][0]['text']}
        return {"status": "error", "message": f"Gemini Error: {r.text}"}

    async def _query_deepseek(self, prompt):
        key = self.keys.get("DEEPSEEK_API_KEY")
        if not key: return {"status": "error", "message": "DeepSeek Key Missing"}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        data = {"model": "deepseek-chat", "messages": [{"role": "system", "content": self.identity}, {"role": "user", "content": prompt}]}
        r = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data, timeout=60)
        if r.status_code == 200:
            return {"status": "success", "data": r.json()['choices'][0]['message']['content']}
        return {"status": "error", "message": f"DeepSeek Error: {r.text}"}

    async def status(self, payload=None):
        return {"status": "online", "engines": list(self.keys.keys())}
