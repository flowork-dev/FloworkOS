########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\backend\app_router.py total lines 73 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging

class AppRouter:
    def __init__(self, service_instance):
        self.service = service_instance
        self.logger = logging.getLogger("AppRouter.AICouncil")

    def get_routes(self):
        return {
            "start_meeting": self.handle_start,
            "start": self.handle_start,
            "check": self.handle_check,
            "get_agents": self.handle_get_agents,
            "get_history": self.handle_get_history,
            "rename_history": self.handle_rename_history,
            "delete_history": self.handle_delete_history,
            "stop_meeting": self.handle_stop,
            "execute": self.handle_execute
        }

    async def handle_start(self, payload: dict):
        user_id = payload.get("user_id", "system")
        topic = payload.get("topic", "Tech Trends")
        previous_job_id = payload.get("previous_job_id")

        if not previous_job_id: previous_job_id = payload.get("job_id")

        agent_config = payload.get("agent_config", {})
        files = payload.get("files", []) # Catch files

        self.logger.info(f"📥 Start: {topic} | Files: {len(files)}")

        job_id = self.service.start_session(topic, user_id, previous_job_id, agent_config, files)

        return {"status": "success", "job_id": job_id}

    async def handle_check(self, payload: dict):
        job_id = payload.get("job_id")
        job = self.service.get_job(job_id)
        if job: return {"status": "success", "data": job}
        return {"status": "error", "error": "Job not found"}

    async def handle_get_agents(self, payload: dict):
        agents = self.service.get_available_agents()
        return agents

    async def handle_get_history(self, payload: dict):
        return self.service.get_history_list()

    async def handle_rename_history(self, payload: dict):
        return self.service.rename_session(payload.get("job_id"), payload.get("title"))

    async def handle_delete_history(self, payload: dict):
        return self.service.delete_session(payload.get("job_id"))

    async def handle_stop(self, payload: dict):
        job_id = payload.get("job_id") or payload.get("params", {}).get("job_id")
        return self.service.stop_session(job_id)

    async def handle_execute(self, payload: dict):
        action = payload.get("action")
        params = payload.get("params", {})
        if action == "stop_meeting":
            return self.service.stop_session(params.get("job_id"))
        if action == "like_message":
            return self.service.trigger_main_run(payload)
        return {"status": "error", "message": f"Action {action} not mapped"}
