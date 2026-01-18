########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\app\executor\runner.py total lines 267 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
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
import struct
import socket
import inspect # [NEW] Wajib untuk cek signature handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Runner] %(message)s')
logger = logging.getLogger("AppRunner")

sio = socketio.AsyncClient()

APP_INSTANCE = None
APP_ROUTER = None
APP_ID = None
EVENT_HANDLERS = {}
KERNEL_STUB = None # [NEW] Global reference untuk Isolated Kernel

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

    global APP_ID, KERNEL_STUB
    APP_ID = args.appid

    try:
        lib_paths = json.loads(args.libs)
        if lib_paths:
            logger.info(f"💉 [Warehouse-Link] Injecting {len(lib_paths)} shared library paths...")
            for p in lib_paths:
                if p not in sys.path:
                    sys.path.insert(0, p)
    except Exception as e:
        logger.error(f"❌ Failed to inject libraries from Warehouse: {e}")

    if args.path not in sys.path:
        sys.path.insert(0, args.path)

    backend_path = os.path.join(args.path, "backend")
    if os.path.exists(backend_path) and backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    load_success = load_app_modules(args.path, args.appid)

    if not load_success:
        logger.error("🔥 Failed to load App Modules. Exiting.")
        sys.exit(1)

    gateway_url = os.environ.get("GATEWAY_URL", "http://gateway:8000")
    try:
        await sio.connect(gateway_url, headers={
            "X-Muscle-ID": args.appid,
            "X-Muscle-Type": "daemon_runner"
        }, namespaces=['/engine-socket'])
        logger.info(f"✅ Connected to Nervous System (Core) at {gateway_url}")
    except Exception as e:
        logger.warning(f"\033[93m⚠️ Gateway Socket link failed: {e}. App is now in OFFLINE mode.\033[0m")

    server = await asyncio.start_server(
        handle_socket_client, '0.0.0.0', args.port,
        family=socket.AF_INET,
        flags=socket.AI_PASSIVE,
        reuse_address=True
    )
    logger.info(f"🚀 [Immortal Bridge] App '{args.appid}' standby on port {args.port}")

    async with server:
        await server.serve_forever()

async def handle_socket_client(reader, writer):
    """
    [FASE 3] Menangani koneksi Raw TCP dari Core.
    Protocol: 4 Byte Header (Length) + JSON Payload
    """
    try:
        header = await reader.read(4)
        if not header: return

        length = struct.unpack('!I', header)[0]
        data = await reader.readexactly(length)
        payload = json.loads(data.decode('utf-8'))

        action = payload.get("action")
        data_body = payload.get("params", payload.get("data", {}))

        response_data = {}
        if action == "cleanup":
            logger.info("🧹 [Janitor] Received cleanup signal (Ghost Protocol).")
            await perform_cleanup()
            response_data = {"status": "cleaned"}
        else:
            response_data = await process_action(action, data_body)

        response_bytes = json.dumps(response_data).encode('utf-8')
        writer.write(struct.pack('!I', len(response_bytes)))
        writer.write(response_bytes)
        await writer.drain()

    except Exception as e:
        logger.error(f"❌ Socket Bridge Error: {e}")
        error_res = json.dumps({"status": "error", "error": str(e)}).encode('utf-8')
        try:
            writer.write(struct.pack('!I', len(error_res)))
            writer.write(error_res)
            await writer.drain()
        except: pass
    finally:
        writer.close()

async def perform_cleanup():
    if APP_INSTANCE:
        cleanup_method = getattr(APP_INSTANCE, "on_stop", getattr(APP_INSTANCE, "cleanup", None))
        if cleanup_method:
            try:
                if asyncio.iscoroutinefunction(cleanup_method): await cleanup_method()
                else: cleanup_method()
            except: pass

def load_app_modules(app_path, app_id):
    global APP_INSTANCE, APP_ROUTER, KERNEL_STUB
    try:
        service_file = os.path.join(app_path, "backend", "app_service.py")
        if not os.path.exists(service_file):
            logger.error("❌ app_service.py not found!")
            return False

        def safe_exit(code=0):
            logger.warning(f"🛡️ [Interceptor] Blocked sys.exit({code}) from App '{app_id}'.")
            raise Exception("Exit blocked by Runner Security.")
        sys.exit = safe_exit

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

        if not service_cls: return False

        class IsolatedKernel:
            def __init__(self, aid):
                self._aid = aid
                self.app_id = aid # Support proper identification
                self.app_data_path = os.environ.get("FLOWORK_APP_DATA_PATH", f"/app/data/apps_storage/{aid}")

            def get_service(self, sid):
                if sid in ['app_runtime', 'app_runtime_service', 'app_service']:
                    return self
                return None

            def write_to_log(self, msg, lvl="INFO"):
                logger.info(f"[AppLog] {msg}")
                asyncio.create_task(sio.emit("muscle_log", {"message": msg, "level": lvl, "app_id": self._aid}, namespace='/engine-socket'))

            def get_app_data_path(self): return self.app_data_path

            class EventBusStub:
                def publish(self, topic, payload):
                    if isinstance(payload, dict): payload['_source_app_id'] = APP_ID
                    asyncio.create_task(sio.emit("muscle_event", {"topic": topic, "payload": payload}, namespace='/engine-socket'))

                def subscribe(self, topic, callback):
                    EVENT_HANDLERS[topic] = callback
                    logger.info(f"👂 [EventBus] Subscribed to topic: {topic}")

            class DatabaseStub:
                async def insert(self, collection, data, key=None): return await self._rpc("insert", collection, {"value": data, "key": key})
                async def find(self, collection, query={}): return await self._rpc("select", collection, {"key": query.get("key")})
                async def delete(self, collection, key): return await self._rpc("delete", collection, {"key": key})
                async def _rpc(self, action, collection, payload):
                    if not sio.connected: return None
                    try:
                        return await sio.call('db_proxy', {"action": action, "collection": collection, "payload": payload, "app_id": app_id}, namespace='/engine-socket', timeout=10)
                    except: return None

            @property
            def event_bus(self): return self.EventBusStub()
            @property
            def db(self): return self.DatabaseStub()
            @property
            def app_runtime(self): return self

        KERNEL_STUB = IsolatedKernel(app_id)
        APP_INSTANCE = service_cls(KERNEL_STUB, f"runner_{app_id}")

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
                logger.info("🔗 AppRouter synchronized and attached.")
        return True

    except Exception as e:
        logger.error(f"🔥 Critical Module Load Error: {e}")
        traceback.print_exc()
        return False

async def process_action(action, payload):
    global APP_ROUTER, KERNEL_STUB
    if not APP_ROUTER: return {"status": "error", "error": "Router not initialized"}

    routes = APP_ROUTER.get_routes()
    handler = routes.get(action)
    if not handler: return {"status": "error", "error": f"Action '{action}' not found"}

    try:
        sig = inspect.signature(handler)
        params_count = len(sig.parameters)

        if params_count >= 2:
            if asyncio.iscoroutinefunction(handler): return await handler(KERNEL_STUB, payload)
            else: return handler(KERNEL_STUB, payload)
        else:
            if asyncio.iscoroutinefunction(handler): return await handler(payload)
            else: return handler(payload)

    except Exception as e:
        logger.error(f"❌ App Execution Error ({action}): {e}")
        return {"status": "error", "error": str(e)}

if __name__ == '__main__':
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
