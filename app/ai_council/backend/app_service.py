########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\backend\app_service.py total lines 105 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import sys
import os
import threading
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path: sys.path.append(parent_dir)

try:
    import main
except ImportError as e:
    print(f"❌ Failed to import main: {e}")

class AICouncilService:
    def __init__(self, kernel, service_id):
        self.kernel = kernel
        self.logger = logging.getLogger("Node.ai_council")

    def start_session(self, topic, user_id, previous_job_id=None, agent_config=None, files=None):

        if previous_job_id and previous_job_id != "null":
            job_id = previous_job_id
            self.logger.info(f"🔄 Resuming session: {job_id}")
        else:
            job_id = f"job_{int(time.time())}"
            self.logger.info(f"🆕 Creating new session: {job_id}")

        enriched_topic = topic
        try:
            router = self.kernel.get_service("neural_knowledge_router")
            if router:
                knowledge_results = router.execute_sync("search_knowledge", topic, user_id, limit=3)
                if knowledge_results:
                    context_header = "\n\n[NEURAL VAULT CONTEXT - PRIORITASKAN DATA INI]"
                    context_body = ""
                    for res in knowledge_results:
                        context_body += f"\n- {res['content']} (Sumber: {res['source']})"

                    enriched_topic = f"{topic}{context_header}{context_body}"
                    self.logger.info(f"🧠 RAG: Council meeting enriched with {len(knowledge_results)} vault records.")
        except Exception as e:
            self.logger.error(f"⚠️ RAG Auto-Search bypassed: {e}")

        def run_job():
            payload = {
                "action": "start_meeting",
                "params": {
                    "topic": enriched_topic, # Topik yang sudah diperkaya konteks RAG
                    "original_topic": topic, # Tetap simpan topik asli buat jaga-jaga
                    "job_id": job_id,
                    "previous_job_id": previous_job_id,
                    "agent_config": agent_config or {},
                    "files": files or [] # PASS FILES
                },
                "user_id": user_id
            }
            if hasattr(main, 'run'): main.run(payload)

        thread = threading.Thread(target=run_job)
        thread.start()
        return job_id

    def get_job(self, job_id):
        if hasattr(main, 'run'):
            return main.run({"action": "check", "params": {"job_id": job_id}})
        return None

    def get_available_agents(self):
        if hasattr(main, 'run'):
            return main.run({"action": "get_agents", "params": {}})
        return {"status": "error"}

    def get_history_list(self):
        if hasattr(main, 'run'):
            return main.run({"action": "get_history", "params": {}})
        return {"status": "error"}

    def rename_session(self, job_id, new_title):
        if hasattr(main, 'run'):
            return main.run({"action": "rename_history", "params": {"job_id": job_id, "title": new_title}})
        return {"status": "error"}

    def delete_session(self, job_id):
        if hasattr(main, 'run'):
            return main.run({"action": "delete_history", "params": {"job_id": job_id}})
        return {"status": "error"}

    def stop_session(self, job_id):
        self.logger.info(f"🛑 Stopping session request: {job_id}")
        if hasattr(main, 'run'):
            return main.run({"action": "stop_meeting", "params": {"job_id": job_id}})
        return {"status": "error"}

    def trigger_main_run(self, payload):
        if hasattr(main, 'run'):
            return main.run(payload)
        return {"status": "error"}
