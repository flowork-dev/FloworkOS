########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\biz_canvas_architect\backend\app_service.py total lines 336 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import uuid
import time
import json
import asyncio
import logging
import os
import requests
import sqlite3

try:
    from backend.agents import cto, cmo, cfo, ceo
except ImportError:
    try:
        from .agents import cto, cmo, cfo, ceo
    except ImportError:
        import agents.cto as cto
        import agents.cmo as cmo
        import agents.cfo as cfo
        import agents.ceo as ceo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "canvas_storage.json")

def inject_god_mode_secrets():
    """Mengambil API Key dari database pusat Flowork dengan scanning agresif"""
    target_vars = ["GEMINI_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]
    db_path = "/app/data/flowork_core.db"

    if not os.path.exists(db_path):
        print("⚠️ [GodMode] Central Database not found at /app/data/flowork_core.db")
        return

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        possible_tables = ["variables", "settings", "configs"]
        for table in possible_tables:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = [c[1] for c in cursor.fetchall()]
                if not cols: continue

                key_col = next((x for x in ["name", "key", "variable_name", "setting_key"] if x in cols), None)
                val_col = next((x for x in ["value", "val", "setting_value"] if x in cols), None)

                if key_col and val_col:
                    for key in target_vars:
                        if os.getenv(key): continue

                        cursor.execute(f"SELECT {val_col} FROM {table} WHERE {key_col} = ? LIMIT 1", (key,))
                        row = cursor.fetchone()
                        if row and row[0]:
                            os.environ[key] = str(row[0])
                            print(f"✅ [GodMode] Injected {key} from table '{table}'")
            except Exception as e:
                continue
        conn.close()
    except Exception as e:
        print(f"❌ [GodMode] Injection Failed: {e}")

class BizCanvasService:
    def __init__(self, kernel=None, instance_id=None, *args, **kwargs):
        inject_god_mode_secrets() # Panggil injector saat start
        self.kernel = kernel
        self.instance_id = instance_id
        self.jobs = {}
        self.logger = logging.getLogger("BizCanvas")
        self._load_db()

    def _load_db(self):
        """Load history dengan validasi path"""
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    content = f.read()
                    if content.strip():
                        self.jobs = json.loads(content)
                    else:
                        self.jobs = {}
                self.logger.info(f"📂 [Storage] Loaded {len(self.jobs)} sessions from {DB_FILE}")
            except Exception as e:
                self.logger.error(f"❌ [Storage] Load Error: {e}")
                self.jobs = {}
        else:
            self.logger.warning(f"⚠️ [Storage] {DB_FILE} not found. Starting fresh.")
            self.jobs = {}

    def _save_db(self):
        """Atomic save biar file nggak corrupt (Lazarus Protocol)"""
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            with open(DB_FILE + ".tmp", "w") as f:
                json.dump(self.jobs, f, indent=2)
                f.flush()
                if hasattr(os, 'fsync'):
                    os.fsync(f.fileno()) # Force write to physical disk

            if os.path.exists(DB_FILE):
                try:
                    os.replace(DB_FILE + ".tmp", DB_FILE)
                except OSError:
                    os.remove(DB_FILE)
                    os.rename(DB_FILE + ".tmp", DB_FILE)
            else:
                os.rename(DB_FILE + ".tmp", DB_FILE)
            return True # Success signal
        except Exception as e:
            self.logger.error(f"❌ [Storage] Save DB Error: {e}")
            return False

    def get_all_history(self):
        self._load_db()
        history = []
        for jid, data in self.jobs.items():
            history.append({
                "job_id": jid,
                "topic": data.get("topic", "Tanpa Judul"),
                "status": data.get("status", "unknown"),
                "date": time.strftime("%d/%m %H:%M", time.localtime(data.get("created_at", time.time())))
            })
        return sorted(history, key=lambda x: x["date"], reverse=True)

    def rename_session(self, job_id, new_title):
        self._load_db()
        if job_id in self.jobs:
            self.jobs[job_id]["topic"] = new_title
            if self._save_db():
                return {"status": "success", "new_title": new_title}
            else:
                return {"status": "error", "message": "Disk write failed"}
        return {"status": "error", "message": f"Job {job_id} not found."}

    def delete_session(self, job_id):
        self._load_db()
        if job_id in self.jobs:
            self.jobs.pop(job_id, None)
            if self._save_db():
                return {"status": "success"}
            else:
                return {"status": "error", "message": "Failed to sync deletion to disk"}
        return {"status": "error", "message": f"Session {job_id} not found."}

    def update_block_content(self, job_id, block_key, new_content):
        self._load_db()
        if job_id in self.jobs:
            if "canvas" not in self.jobs[job_id]:
                self.jobs[job_id]["canvas"] = {}
            self.jobs[job_id]["canvas"][block_key] = new_content
            self._save_db()
            return {"status": "success"}
        return {"status": "error", "message": "Job not found"}

    def start_simulation(self, topic: str, mode: str, providers: list = []) -> str:
        job_id = str(uuid.uuid4())
        if not providers: providers = ["gemini"]

        self.jobs[job_id] = {
            "id": job_id,
            "topic": topic,
            "mode": mode,
            "providers": providers,
            "status": "thinking",
            "progress": 0,
            "logs": [f"🚀 Rapat dimulai... Menggunakan otak {', '.join(providers)}"],
            "created_at": time.time(),
            "canvas": {}
        }
        self._save_db()
        return job_id

    async def process_simulation(self, job_id: str, topic: str, mode: str):
        if job_id not in self.jobs: return
        job = self.jobs[job_id]
        providers = job["providers"]

        try:
            job["logs"].append("⚡ Para Eksekutif (CTO, CMO, CFO) sedang melakukan riset mendalam...")
            self._save_db()

            results = await asyncio.gather(
                self._call_ai(cto.get_prompt(topic), "CTO", providers),
                self._call_ai(cmo.get_prompt(topic), "CMO", providers),
                self._call_ai(cfo.get_prompt(topic), "CFO", providers)
            )
            cto_res, cmo_res, cfo_res = results

            for res in [cto_res, cmo_res, cfo_res]:
                if "error" in res:
                    raise Exception(f"AI Failure: {res.get('details', res['error'])}")

            job["canvas"].update(cto_res)
            job["canvas"].update(cmo_res)
            job["canvas"].update(cfo_res)
            job["progress"] = 80
            self._save_db()

            job["logs"].append("🏛️ CEO sedang menyusun strategi final...")
            ceo_res = await self._call_ai(ceo.get_prompt(topic, cto_res, cmo_res, cfo_res), "CEO", providers)

            if "error" in ceo_res:
                raise Exception(f"CEO AI Failure: {ceo_res.get('details', ceo_res['error'])}")

            job["canvas"].update(ceo_res)

            job["progress"] = 100
            job["status"] = "completed"
            job["logs"].append("✅ Rapat Selesai. Dokumen siap.")
            self._save_db()

        except Exception as e:
            job["status"] = "error"
            error_msg = str(e).replace("AI_SUBSYSTEM_FAILURE: ", "")
            job["logs"].append(f"🔥 KESALAHAN REAL: {error_msg}")
            self.logger.error(f"Simulation Error: {e}")
            self._save_db()

    async def regenerate_specific_block(self, job_id, block_key, providers):
        self._load_db()
        if job_id in self.jobs:
            job = self.jobs[job_id]
            topic = job["topic"]

            role_map = {
                "key_partners": "CTO", "key_activities": "CTO", "key_resources": "CTO",
                "customer_segments": "CMO", "channels": "CMO", "customer_relationships": "CMO",
                "cost_structure": "CFO", "revenue_streams": "CFO",
                "value_propositions": "CEO"
            }
            role = role_map.get(block_key, "CEO")

            prompt = [
                {"role": "system", "content": f"Kamu adalah {role} expert. Tugasmu: REVISI bagian '{block_key}' untuk bisnis '{topic}'. Berikan analisis yang LEBIH DETIL, LEBIH KRITIS, dan LEBIH BANYAK (Minimal 5 poin). Format Output: Langsung isi konten Markdown (Bullet points), jangan pakai JSON."},
                {"role": "user", "content": f"Berikan strategi baru untuk {block_key}. Jangan pelit ide!"}
            ]

            new_content = await self._generate_text_real(prompt, providers)

            if new_content.startswith("ERROR_CORE:"):
                return {"error": "Gagal Regenerate", "details": new_content}

            self.jobs[job_id]["canvas"][block_key] = new_content
            self._save_db()
            return {"status": "updated", "content": new_content}
        return {"error": "Job not found"}

    def get_simulation_result(self, job_id: str):
        self._load_db()
        return self.jobs.get(job_id)

    async def _call_ai(self, messages, role, providers):
        json_instruction = {"role": "system", "content": "IMPORTANT: Output MUST be valid JSON only. Do not wrap in markdown code blocks. No preamble."}
        messages.insert(0, json_instruction)

        raw_response = ""
        try:
            raw_response = await self._generate_text_real(messages, providers)

            if raw_response.startswith("ERROR_CORE:"):
                 return {"error": "Subsystem Error", "details": raw_response}

            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON from AI ({role})")
            return {"error": "Format JSON Rusak", "details": f"AI Ngaco/Limit: {raw_response[:100]}"}
        except Exception as e:
            self.logger.error(f"AI Call Error: {e}")
            return {"error": "Connection Fail", "details": str(e)}

    async def _generate_text_real(self, messages, providers):
        all_errors = []

        if "chatgpt" in providers or "gpt-4" in providers:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {"model": "gpt-4-turbo-preview", "messages": messages, "temperature": 0.7}
                    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=60)
                    if response.status_code == 200:
                        return response.json()['choices'][0]['message']['content']
                    else:
                        all_errors.append(f"OpenAI {response.status_code}: {response.text[:50]}")
                except Exception as e:
                    all_errors.append(f"OpenAI Connection Error: {str(e)}")

        if "gemini" in providers:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    contents = []
                    for m in messages:
                        role = "user" if m["role"] == "user" else "model"
                        if m["role"] == "system": continue
                        contents.append({"role": role, "parts": [{"text": m["content"]}]})

                    if messages[0]["role"] == "system":
                        if contents: contents[0]["parts"][0]["text"] = messages[0]["content"] + "\n\n" + contents[0]["parts"][0]["text"]
                        else: contents.append({"role": "user", "parts": [{"text": messages[0]["content"]}]})

                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    response = requests.post(url, json={"contents": contents}, timeout=60)
                    if response.status_code == 200:
                        return response.json()['candidates'][0]['content']['parts'][0]['text']
                    else:
                        err_data = response.json()
                        err_msg = err_data.get('error', {}).get('message', 'Unknown Gemini Error')
                        all_errors.append(f"Gemini {response.status_code}: {err_msg}")
                except Exception as e:
                    all_errors.append(f"Gemini Connection Error: {str(e)}")

        if "deepseek" in providers:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key:
                try:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {"model": "deepseek-chat", "messages": messages}
                    response = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=60)
                    if response.status_code == 200:
                        return response.json()['choices'][0]['message']['content']
                    else:
                        all_errors.append(f"DeepSeek {response.status_code}: {response.text[:50]}")
                except Exception as e:
                    all_errors.append(f"DeepSeek Connection Error: {str(e)}")

        self.logger.warning("No valid AI Provider found/working. Reporting actual errors.")

        combined_error = " | ".join(all_errors) if all_errors else "API Keys missing in environment."
        return f"ERROR_CORE: {combined_error}"
