########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\app\executor\runner.py total lines 206 
########################################################################

import os
import sys
import json
import argparse
import socketio
import asyncio
import traceback
import importlib.util
import logging
import time
from aiohttp import web

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Runner] %(message)s')
logger = logging.getLogger("AppRunner")

sio = socketio.AsyncClient()

APP_INSTANCE = None
APP_ROUTER = None
APP_ID = None

async def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description='Flowork App Daemon Runner')
    parser.add_argument('--port', type=int, required=True, help='Port for local API')
    parser.add_argument('--path', type=str, required=True, help='Path to App Source')
    parser.add_argument('--appid', type=str, required=True, help='App ID')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--libs', type=str, default='[]', help='JSON List of injected library paths')

    args = parser.parse_args()

    global APP_ID
    APP_ID = args.appid

    try:
        lib_paths = json.loads(args.libs)
        if lib_paths:
            logger.info(f"💉 Injecting {len(lib_paths)} library paths from Warehouse...")
            for p in lib_paths:
                if p not in sys.path:
                    sys.path.insert(0, p)
    except Exception as e:
        logger.error(f"❌ Failed to inject libraries: {e}")

    if args.path not in sys.path:
        sys.path.insert(0, args.path)

    backend_path = os.path.join(args.path, "backend")
    if os.path.exists(backend_path) and backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    load_success = load_app_modules(args.path, args.appid)

    if not load_success:
        logger.error("🔥 Failed to load App Modules. Exiting.")
        sys.exit(1)

    gateway_url = os.environ.get("GATEWAY_URL", "http://localhost:8000")

    try:
        await sio.connect(gateway_url, headers={
            "X-Muscle-ID": args.appid,
            "X-Muscle-Type": "daemon_runner"
        }, namespaces=['/engine-socket'])
        logger.info(f"✅ Connected to Nervous System at {gateway_url}")
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to Gateway Socket: {e}. Running in Local-Only mode.")

    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_post('/execute', handle_execute)
    app.router.add_post('/cleanup', handle_cleanup)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', args.port)
    logger.info(f"🚀 Runner active on port {args.port}")
    await site.start()

    while True:
        await asyncio.sleep(3600)

def load_app_modules(app_path, app_id):
    global APP_INSTANCE, APP_ROUTER
    try:
        service_file = os.path.join(app_path, "backend", "app_service.py")
        if not os.path.exists(service_file):
            logger.error("❌ app_service.py not found!")
            return False

        module_name = f"runner_svc_{app_id}"
        spec = importlib.util.spec_from_file_location(module_name, service_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        service_cls = None
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, type) and attr_name.endswith("Service"):
                service_cls = attr
                break

        if not service_cls:
            logger.error("❌ No Service class found in app_service.py")
            return False

        class IsolatedKernel:
            def get_service(self, sid): return None
            def write_to_log(self, msg, lvl="INFO"): logger.info(f"[AppLog] {msg}")
            class EventBusStub:
                def publish(self, topic, payload):
                    asyncio.create_task(sio.emit("muscle_event", {"topic": topic, "payload": payload}, namespace='/engine-socket'))
            event_bus = EventBusStub()
            app_data_path = os.environ.get("FLOWORK_APP_DATA_PATH", f"/app/data/apps_storage/{app_id}")
            def get_app_data_path(self): return self.app_data_path

        kernel_stub = IsolatedKernel()
        kernel_stub.app_data_path = os.environ.get("FLOWORK_APP_DATA_PATH", f"/app/data/apps_storage/{app_id}")

        APP_INSTANCE = service_cls(kernel_stub, f"runner_{app_id}")
        if hasattr(APP_INSTANCE, 'start'):
            if asyncio.iscoroutinefunction(APP_INSTANCE.start):
                asyncio.run(APP_INSTANCE.start())
            else:
                APP_INSTANCE.start()

        router_file = os.path.join(app_path, "backend", "app_router.py")
        if os.path.exists(router_file):
            r_spec = importlib.util.spec_from_file_location(f"runner_router_{app_id}", router_file)
            r_mod = importlib.util.module_from_spec(r_spec)
            r_spec.loader.exec_module(r_mod)
            if hasattr(r_mod, 'AppRouter'):
                APP_ROUTER = r_mod.AppRouter(APP_INSTANCE)
                logger.info("🔗 AppRouter attached.")
        return True

    except ModuleNotFoundError as e:
        logger.error(f"🚑 [AUTOHEAL] Critical Missing Dependency detected: {e.name}")
        sys.exit(101)
    except Exception as e:
        logger.error(f"🔥 Critical Load Error: {e}")
        traceback.print_exc()
        return False

async def handle_health(request):
    return web.json_response({"status": "alive", "app_id": APP_ID})

async def handle_cleanup(request):
    logger.info("🧹 [Janitor] Received cleanup signal.")
    if APP_INSTANCE:
        cleanup_method = getattr(APP_INSTANCE, "on_stop", getattr(APP_INSTANCE, "cleanup", None))
        if cleanup_method:
            try:
                if asyncio.iscoroutinefunction(cleanup_method): await cleanup_method()
                else: cleanup_method()
                logger.info("✅ App Cleanup finished.")
            except Exception as e: logger.error(f"❌ App Cleanup failed: {e}")
    return web.json_response({"status": "cleaned"})

async def handle_execute(request):
    try:
        data = await request.json()
        action = data.get("action"); payload = data.get("payload", {})
        result = await process_action(action, payload)
        return web.json_response(result)
    except Exception as e: return web.json_response({"status": "error", "error": str(e)})

@sio.on('execute_action', namespace='/engine-socket')
async def on_execute_action(data):
    req_id = data.get("request_id"); action = data.get("action"); payload = data.get("payload", {})
    logger.info(f"⚡ [Socket] Received Action: {action}")
    result = await process_action(action, payload)
    if req_id: await sio.emit('action_result', {"request_id": req_id, "result": result}, namespace='/engine-socket')

async def process_action(action, payload):
    global APP_ROUTER, APP_INSTANCE
    if not APP_ROUTER: return {"status": "error", "error": "Router not initialized"}
    routes = APP_ROUTER.get_routes(); handler = routes.get(action)
    if not handler: return {"status": "error", "error": f"Action '{action}' not found"}
    try:
        if asyncio.iscoroutinefunction(handler): return await handler(payload)
        else: return handler(payload)
    except Exception as e:
        logger.error(f"❌ Execution Error ({action}): {e}")
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

if __name__ == '__main__':
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
