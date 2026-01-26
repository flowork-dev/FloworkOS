########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\app_builder\backend\app_router.py total lines 46 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import importlib.util
import os
import asyncio
import inspect

class AppRouter:
    def __init__(self, service_instance):
        self.service = service_instance
        self.app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def get_routes(self):
        return {
            "build_app": self.handle_build,
            "ask_ai": self.handle_ai,
            "get_logs": self.handle_logs # [ADDITION] Kabel Log
        }

    async def _execute_logic(self, file_name, payload):
        path = os.path.join(self.app_path, "backend", "logic", f"{file_name}.py")
        spec = importlib.util.spec_from_file_location(file_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if inspect.iscoroutinefunction(mod.run):
            return await mod.run(self.service, payload)
        return mod.run(self.service, payload)

    async def handle_ai(self, p): return await self._execute_logic("ai_code_assistant", p)
    async def handle_build(self, p): return await self._execute_logic("generate_new_app", p)
    async def handle_logs(self, p): return await self._execute_logic("get_app_logs", p)

def route(app_context, action, data=None):
    router = AppRouter(app_context.service if hasattr(app_context, 'service') else app_context)
    routes = router.get_routes()
    if action in routes:
        func = routes[action]
        if inspect.iscoroutinefunction(func):
            return asyncio.run(func(data))
        return func(data)
    return {"error": "Route not found"}
