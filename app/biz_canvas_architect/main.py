########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\biz_canvas_architect\main.py total lines 51 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from backend.app_router import router as app_router
    IS_SCANNING = False
except ImportError:
    IS_SCANNING = True
    FastAPI = object # Dummy

def init_app():
    if IS_SCANNING: return None

    app = FastAPI(title="The Iron Canvas API")

    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    if app_router:
        app.include_router(app_router, prefix="", tags=["BizCanvas"])
        app.include_router(app_router, prefix="/api/v1/apps/execute/biz_canvas_architect", tags=["BizCanvasProxy"])

    @app.get("/")
    async def serve_gui():
        return FileResponse(os.path.join(current_dir, "index.html"))

    return app

app = init_app()

if __name__ == "__main__":
    if not IS_SCANNING:
        port = int(os.getenv("PORT", 8006))
        print(f"🚀 The Iron Canvas started on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
