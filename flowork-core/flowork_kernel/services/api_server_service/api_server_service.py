########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\api_server_service.py total lines 234 
########################################################################

import asyncio
from aiohttp import web
import threading
import json
import uuid
import time
import os
import sys
import mimetypes
import importlib.util
import functools
from collections import deque
from ..base_service import BaseService
from flowork_kernel.utils.path_helper import get_apps_directory
from .routes.filesystem_routes import FilesystemRoutes
from .routes.engine_routes import EngineRoutes
from .routes.preset_routes import PresetRoutes
from .routes.ui_state_routes import UIStateRoutes
from flowork_kernel.utils.tracing_setup import setup_tracing

class ApiServerService(BaseService):
    def __init__(self, kernel, service_id: str):
        BaseService.__init__(self, kernel, service_id)
        self.tracer = setup_tracing(service_name="flowork-core")
        self.recent_events = deque(maxlen=15)
        self.app = None; self.runner = None; self.site = None

    async def handle_muscle_assets(self, request):
        app_id = request.match_info.get('app_id')
        raw_filename = request.match_info.get('filename')
        filename = raw_filename.replace('assets/', '') if 'assets/' in raw_filename else raw_filename
        if not filename: filename = "index.html"
        apps_dir = get_apps_directory()
        actual_path = apps_dir / app_id / filename
        if not actual_path.exists(): actual_path = apps_dir / app_id / "index.html"
        if str(actual_path).endswith('.html'):
            try:
                with open(actual_path, 'r', encoding='utf-8') as f: content = f.read()
                bridge_script = """
                <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/6.7.0/ethers.umd.min.js"></script>
                <script id="flowork-auth-bridge">
                (function() {
                    window.addEventListener('message', function(e) {
                        if (e.data && (e.data.type === 'FLOWORK_IDENTITY_SYNC' || e.data.type === 'CMD_LOAD')) {
                            window.FLOWORK_AUTH = { headers: { 'X-User-Address': e.data.userAddress, 'X-Signature': e.data.signature, 'X-Signed-Message': e.data.messageToSign, 'X-Flowork-Engine-ID': e.data.engineId, 'X-Payload-Version': '2' } };
                            localStorage.setItem('flowork_bridge_cache', JSON.stringify(window.FLOWORK_AUTH));
                        }
                    });
                    window.FLOWORK_AUTH = JSON.parse(localStorage.getItem('flowork_bridge_cache') || '{}');
                    const origFetch = window.fetch;
                    window.fetch = async function() {
                        const args = [...arguments];
                        if (window.FLOWORK_AUTH && window.FLOWORK_AUTH.headers && args[0].includes('/api/v1/')) {
                            if (!args[1]) args[1] = { method: 'POST' };
                            if (!args[1].headers) args[1].headers = {};
                            Object.assign(args[1].headers, window.FLOWORK_AUTH.headers);
                            if (!args[1].headers['Content-Type']) args[1].headers['Content-Type'] = 'application/json';
                        }
                        return originalFetch.apply(this, args);
                    };
                })();
                </script>
                """
                if "</body>" in content: content = content.replace("</body>", bridge_script + "</body>")
                else: content += bridge_script
                return web.Response(body=content, content_type='text/html', headers={'Access-Control-Allow-Origin': '*'})
            except Exception: pass
        ctype, _ = mimetypes.guess_type(str(actual_path))
        return web.FileResponse(actual_path, headers={'Access-Control-Allow-Origin': '*', 'Content-Type': ctype or 'application/octet-stream'})

    async def handle_legacy_icon(self, request):
        app_id = request.match_info.get('app_id')
        apps_dir = get_apps_directory()
        target_dir = apps_dir / app_id
        for name in ["icon.svg", "icon.png", "logo.svg", "logo.png"]:
            p = target_dir / name
            if p.exists():
                return web.FileResponse(str(p), headers={'Access-Control-Allow-Origin': '*'})
        return web.Response(status=404, text="Icon not found")

    async def handle_get_apps_native(self, request):
        app_srv = self.kernel.get_service("app_service")
        if not app_srv: return web.json_response([])
        all_muscles = []
        for aid, info in app_srv.get_registry("apps").items():
            all_muscles.append({
                "id": aid,
                "name": info["manifest"].get("name", aid),
                "manifest": info["manifest"],
                "icon_url": info.get("icon_url"),
                "gui_url": f"/api/v1/muscle-assets/{aid}/assets/index.html",
                "category": info["type"],
                "status": "active",
                "services": info.get("services", []) # [ADDED] Show services in API response
            })
        return web.json_response(all_muscles)

    async def dynamic_service_gateway(self, request):
        """
        Pintu gerbang untuk semua API yang dibuat oleh App/Plugin.
        Menangani route: /api/connect/<service_name>/<action>
        """
        service_name = request.match_info.get('service_name')
        action = request.match_info.get('action')

        try:
            payload = await request.json()
        except:
            payload = {}

        provider_app_id = None
        app_srv = self.kernel.get_service("app_service")

        if app_srv:
            registry = app_srv.get_registry("apps")
            for aid, info in registry.items():
                if service_name in info.get("services", []):
                    provider_app_id = aid
                    break

        if not provider_app_id:
            provider_app_id = service_name

        app_runtime = self.kernel.get_service("app_runtime")
        if not app_runtime:
            return web.json_response({"error": "AppRuntime Service not available"}, status=503)

        try:
            result = await app_runtime.execute_service_action(
                app_id=provider_app_id,
                action_name=action,
                data=payload
            )
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": f"Gateway Error: {str(e)}"}, status=500)

    async def handle_app_execute(self, request):
        app_id = request.match_info.get('app_id')
        action = request.match_info.get('action')
        try: body = await request.json()
        except: body = {}

        if not action: action = body.get('action')
        if not action: return web.json_response({"error": "Action missing"}, status=400)

        if "user_context" not in body:
            body["user_context"] = {"user_id": request.headers.get("X-Flowork-User-ID", "system")}

        app_srv = self.kernel.get_service("app_service")
        instance = None
        if app_srv:
            instance = app_srv.get_instance("apps", app_id) or app_srv.get_instance("tools", app_id)

        if instance:
            handler = None
            if hasattr(instance, 'router'):
                routes = instance.router.get_routes()
                handler = routes.get(action)
            if not handler and hasattr(instance, action): handler = getattr(instance, action)

            if handler:
                try:
                    res = await handler(body) if asyncio.iscoroutinefunction(handler) else await asyncio.get_event_loop().run_in_executor(None, functools.partial(handler, body))
                    return web.json_response(res)
                except Exception as e: return web.json_response({"error": str(e)}, status=500)

        muscle = self.kernel.get_service("app_runtime")
        if muscle:
            try:
                res = await muscle.execute_app(
                    app_id=app_id,
                    action=action,
                    params=body,
                    user_id=body["user_context"]["user_id"]
                )
                if isinstance(res, str):
                    try: res = json.loads(res)
                    except: pass
                return web.json_response(res)
            except Exception as e:
                return web.json_response({"error": f"Muscle Execution Failed: {str(e)}"}, status=500)

        return web.json_response({"error": f"App {app_id} not found (Resident or Muscle)"}, status=404)

    def _load_api_routes(self):
        self.app.router.add_get('/api/v1/apps', self.handle_get_apps_native)
        self.app.router.add_get('/api/v1/muscle-assets/{app_id}/assets/{filename:.*}', self.handle_muscle_assets)
        self.app.router.add_get('/api/v1/components/app/{app_id}/icon', self.handle_legacy_icon)
        self.app.router.add_get('/api/v1/user/preferences', lambda r: web.json_response({"status": "success"}))

        self.app.router.add_post("/api/v1/apps/execute/{app_id}/{action}", self.handle_app_execute)
        self.app.router.add_post("/api/v1/apps/execute/{app_id}", self.handle_app_execute)

        self.app.router.add_post("/api/connect/{service_name}/{action}", self.dynamic_service_gateway)

        all_rc = [FilesystemRoutes, EngineRoutes, PresetRoutes, UIStateRoutes]
        for rc in all_rc:
            try:
                inst = rc(self); regs = inst.register_routes()
                for route, hand in regs.items():
                    m, p = route.split(" ", 1)
                    if p == '/api/v1/user/preferences': continue
                    self.app.router.add_route(m, p, hand)
            except Exception: pass

    async def start(self):
        self.app = web.Application(middlewares=[self.middleware_handler])
        self._load_api_routes()
        port = getattr(self, 'loc', {}).get_setting("webhook_port", 8989) if hasattr(self, 'loc') else 8989
        self.runner = web.AppRunner(self.app); await self.runner.setup()
        await web.TCPSite(self.runner, "0.0.0.0", port).start()
        self.kernel.write_to_log(f"!!! [SKELETON] Neural API Live at {port}", "SUCCESS")

    async def stop(self):
        if self.runner: await self.runner.cleanup()

    @web.middleware
    async def middleware_handler(self, request, handler):
        headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS", "Access-Control-Allow-Headers": "*"}
        if request.method == "OPTIONS": return web.Response(status=204, headers=headers)
        try:
            response = await handler(request)
            if not isinstance(response, web.StreamResponse):
                if isinstance(response, (dict, list)): response = web.json_response(response)
            if response: response.headers.update(headers)
            return response
        except Exception as e: return web.json_response({"error": str(e)}, status=500, headers=headers)
