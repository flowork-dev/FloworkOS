########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\biz_canvas_architect\backend\app_router.py total lines 136 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

try:
    from fastapi import APIRouter, HTTPException, BackgroundTasks
    from pydantic import BaseModel
except ImportError:
    APIRouter = object
    BaseModel = object
    HTTPException = Exception
    BackgroundTasks = object

import asyncio
from backend.app_service import BizCanvasService

if APIRouter is not object:
    router = APIRouter()

    class TopicRequest(BaseModel):
        topic: str
        mode: str = "standard"
        providers: list = ["gemini"]

    class RenameRequest(BaseModel):
        job_id: str
        new_title: str

    class DeleteRequest(BaseModel):
        job_id: str

    class RegenerateBlockRequest(BaseModel):
        job_id: str
        block_key: str
        providers: list = ["gemini"]

    class UpdateBlockRequest(BaseModel):
        job_id: str
        block_key: str
        new_content: str

    @router.get("/status")
    async def check_status():
        return {"status": "online"}

    @router.post("/history")
    async def api_get_history():
        service = BizCanvasService()
        return service.get_all_history()

    @router.post("/history/rename")
    async def api_rename_history(req: RenameRequest):
        service = BizCanvasService()
        return service.rename_session(req.job_id, req.new_title)

    @router.post("/history/delete")
    async def api_delete_history(req: DeleteRequest):
        service = BizCanvasService()
        return service.delete_session(req.job_id)

    @router.post("/generate")
    async def generate_canvas(req: TopicRequest, background_tasks: BackgroundTasks):
        service = BizCanvasService()
        job_id = service.start_simulation(req.topic, req.mode, req.providers)
        background_tasks.add_task(service.process_simulation, job_id, req.topic, req.mode)
        return {"job_id": job_id, "status": "processing"}

    @router.post("/get_canvas")
    async def get_canvas_http(payload: dict):
        service = BizCanvasService()
        job_id = payload.get("job_id")
        data = service.get_simulation_result(job_id)
        if not data: raise HTTPException(status_code=404)
        return data

    @router.post("/regenerate_block")
    async def api_regenerate_block(req: RegenerateBlockRequest):
        service = BizCanvasService()
        return await service.regenerate_specific_block(req.job_id, req.block_key, req.providers)

    @router.post("/update_block")
    async def api_update_block(req: UpdateBlockRequest):
        service = BizCanvasService()
        return service.update_block_content(req.job_id, req.block_key, req.new_content)

else:
    router = None

class AppRouter:
    def __init__(self, service_instance):
        self.service = service_instance

    def get_routes(self):
        return {
            "generate": self.generate,
            "get_canvas": self.get_canvas,
            "history": self.get_history,
            "rename_history": self.rename_history,
            "delete_history": self.delete_history,
            "history/rename": self.rename_history,
            "history/delete": self.delete_history,
            "regenerate_block": self.regenerate_block,
            "update_block": self.update_block
        }

    async def generate(self, payload):
        topic = payload.get("topic")
        mode = payload.get("mode", "standard")
        providers = payload.get("providers", ["gemini"])
        job_id = self.service.start_simulation(topic, mode, providers)
        asyncio.create_task(self.service.process_simulation(job_id, topic, mode))
        return {"job_id": job_id, "status": "processing"}

    async def get_canvas(self, payload):
        return self.service.get_simulation_result(payload.get("job_id"))

    async def get_history(self, payload):
        return self.service.get_all_history()

    async def rename_history(self, payload):
        return self.service.rename_session(payload.get("job_id"), payload.get("new_title"))

    async def delete_history(self, payload):
        return self.service.delete_session(payload.get("job_id"))

    async def regenerate_block(self, payload):
        return await self.service.regenerate_specific_block(
            payload.get("job_id"), payload.get("block_key"), payload.get("providers", [])
        )

    async def update_block(self, payload):
        return self.service.update_block_content(
            payload.get("job_id"), payload.get("block_key"), payload.get("new_content")
        )
