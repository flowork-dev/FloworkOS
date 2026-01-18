########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_researcher\backend\app_router.py total lines 54 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import importlib.util
import inspect
import asyncio

class AppRouter:
    def __init__(self, app_context):
        self.app_context = app_context
        self.app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def get_routes(self):
        return {
            "run": self.handle_analysis,
            "analyze_text": self.handle_analysis
        }

    async def _execute_logic(self, file_name, payload):
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
            return {"status": "error", "message": f"Router Error: {str(e)}"}

    async def handle_analysis(self, data):
        return await self._execute_logic("main_logic", data)

def route(app_context, action, data=None):
    """Entry point standar"""
    router = AppRouter(app_context)

    routes = router.get_routes()
    if action in routes:
        func = routes[action]
        if inspect.iscoroutinefunction(func):
            return asyncio.run(func(data))
        return func(data)

    return {"status": "error", "message": f"Route '{action}' not found in AppRouter."}
