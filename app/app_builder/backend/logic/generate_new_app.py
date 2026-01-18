########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\app_builder\backend\logic\generate_new_app.py total lines 169 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import inspect

TEMPLATE_MAIN_PY = """

def run(app_context, action=None, data=None, *args, **kwargs):
    \"\"\"
    FLOWORK STANDARD VESSEL (GENERATED V7)
    File ini stateless. Jangan taruh logic di sini.
    Tugasnya hanya meneruskan 'action' ke 'backend/app_router.py'.
    \"\"\"
    if action:
        try:
            return app_context.execute_backend("app_router", action=action, data=data)
        except Exception as e:
            return {"status": "error", "message": f"Vessel Bridge Error: {str(e)}"}

    return {
        "status": "ready",
        "app": "Generated App",
        "version": "1.0.0",
        "message": "Engine is active and waiting for instructions."
    }
"""

TEMPLATE_ROUTER_PY = """
import os
import importlib.util
import inspect
import asyncio
import traceback

class AppRouter:
    def __init__(self, app_context):
        self.app_context = app_context
        self.app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def get_routes(self):
        \"\"\"
        Peta Routing: Action dari UI -> Logic File yang sesuai.
        \"\"\"
        return {
            "run": self.handle_execution,
            "analyze": self.handle_execution,
            "execute": self.handle_execution
        }

    async def _execute_logic(self, file_name, payload):
        \"\"\"Dynamic Loader buat jalanin file di folder logic\"\"\"
        try:
            logic_path = os.path.join(self.app_path, "backend", "logic", f"{file_name}.py")

            if not os.path.exists(logic_path):
                return {"status": "error", "message": f"Logic file {file_name} not found."}

            spec = importlib.util.spec_from_file_location(file_name, logic_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if inspect.iscoroutinefunction(mod.run):
                return await mod.run(self.app_context, payload)
            return mod.run(self.app_context, payload)
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": f"Router Error: {str(e)}"}

    async def handle_execution(self, data):
        return await self._execute_logic("main_logic", data)

def route(app_context, action, data=None):
    \"\"\"Entry point standar yang dipanggil main.py\"\"\"
    try:
        router = AppRouter(app_context)

        routes = router.get_routes()
        if action in routes:
            func = routes[action]
            if inspect.iscoroutinefunction(func):
                return asyncio.run(func(data))
            return func(data)

        return {"status": "error", "message": f"Route '{action}' not found in AppRouter."}
    except Exception as e:
        return {"status": "error", "message": f"Route Crash: {str(e)}"}
"""

TEMPLATE_SERVICE_PY = """
import logging

class AppService:
    def __init__(self, kernel, service_id):
        self.kernel = kernel
        self.service_id = service_id
        self.logger = logging.getLogger(f"App.{service_id}")
        self.logger.info(f"✅ Service {service_id} initialized.")

def run(kernel, service_id):
    \"\"\"Factory function wajib untuk inisialisasi service\"\"\"
    return AppService(kernel, service_id)
"""

def run(context, data, *args, **kwargs):
    """
    EVOLUTIONARY HANDS V7 (Immutable Skeleton):
    Menulis berkas secara fisik.
    Mengabaikan input AI untuk 'main.py' dan 'app_router.py',
    menggantinya dengan template baku agar 100% valid dan stateless.
    """
    app_id = data.get('app_id', '').strip()
    bundle = data.get('bundle', {})

    if not app_id: return {"status": "error", "message": "App ID missing."}

    try:
        app_service = context.kernel.get_service('app_service')
        app_service.scaffold_app(app_id)
        app_dir = os.path.join(app_service.base_app_path, app_id)

        dynamic_files = {
            "main_logic_py": "backend/logic/main_logic.py",
            "config_schema": "config_schema.json",
            "manifest": "manifest.json",
            "icon_svg": "icon.svg",
            "index_html": "index.html",
            "requirements_txt": "requirements.txt"
        }

        written_files = []

        for key, rel_path in dynamic_files.items():
            content = bundle.get(key)
            if content:
                if key in ["manifest", "config_schema"] and isinstance(content, (dict, list)):
                    content = json.dumps(content, indent=4)

                full_path = os.path.join(app_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
                written_files.append(rel_path)

        path_main = os.path.join(app_dir, "main.py")
        with open(path_main, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE_MAIN_PY.strip())
        written_files.append("main.py")

        path_router = os.path.join(app_dir, "backend/app_router.py")
        os.makedirs(os.path.dirname(path_router), exist_ok=True)
        with open(path_router, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE_ROUTER_PY.strip())
        written_files.append("backend/app_router.py")

        path_service = os.path.join(app_dir, "backend/app_service.py")
        with open(path_service, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE_SERVICE_PY.strip())
        written_files.append("backend/app_service.py")

        app_service.sync()
        return {"status": "success", "message": f"Integrated V7 Architecture: {', '.join(written_files)}"}

    except Exception as e:
        return {"status": "error", "message": f"HANDS_FAULT: {str(e)}"}
