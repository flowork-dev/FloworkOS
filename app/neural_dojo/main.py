########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\neural_dojo\main.py total lines 71 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import webview
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

class MockKernel:
    def log(self, msg): print(f"[KERNEL] {msg}")

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from backend.app_service import NeuralService
    from backend.app_router import AppRouter

    kernel_stub = MockKernel()
    service_instance = NeuralService(kernel_stub, "desktop_mode")
    router_instance = AppRouter(service_instance)
    routes = router_instance.get_routes()

    print("✅ Backend Initialized Successfully")
except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
    sys.exit(1)

class NeuralAPI:
    """Jembatan JS ke Python"""
    def run_app(self, app_id, payload):
        action = payload.get('action')
        print(f"⚡ [Frontend] {action}")

        if action in routes:
            handler = routes[action]
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(handler(payload))
                loop.close()
                return response
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Action '{action}' not found"}

    def log_viewer(self): pass

if __name__ == "__main__":
    html_path = os.path.join(current_dir, "index.html")
    if not os.path.exists(html_path):
        print("Error: index.html not found")
        sys.exit(1)

    api = NeuralAPI()
    window = webview.create_window(
        "Neural Dojo (Desktop Mode)",
        url=html_path,
        width=1200,
        height=800,
        background_color='#020617',
        js_api=api
    )
    webview.start(debug=True)
