########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\run_server.py total lines 269 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

try:
    import unsloth
    import logging
    logging.info("[Unsloth] Early load OK. Memory optimizations active.")
except ImportError:
    pass

import sys
import os
import time
import json
import importlib
import importlib.util
import traceback
import logging
import asyncio
import multiprocessing
import threading
from multiprocessing import Process, Queue, Event
from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

core_path_for_guard = os.path.abspath(os.path.dirname(__file__))
if core_path_for_guard not in sys.path:
    sys.path.insert(0, core_path_for_guard)

from flowork_kernel.security.env_guard import enforce_strict_env
enforce_strict_env()

from flowork_kernel.singleton import Singleton
from flowork_kernel.heartbeat import start_heartbeat
from flowork_kernel.workers.job_worker import worker_process

class SafeDict(dict):
    def get(self, key, default=None, **kwargs):
        fallback = kwargs.pop("fallback", None)
        if default is None and fallback is not None:
            default = fallback
        val = super().get(key, default)
        if val is None: return SafeDict()
        if isinstance(val, dict) and not isinstance(val, SafeDict):
            return SafeDict(val)
        return val
    def __getattr__(self, item): return self.get(item, SafeDict())
    def setdefault(self, key, default=None):
        if key not in self:
            super().setdefault(key, {} if default is None else default)
        return self.get(key)
    def __getitem__(self, key):
        if key in self:
            val = super().__getitem__(key)
            if val is None: return SafeDict()
            if isinstance(val, dict) and not isinstance(val, SafeDict):
                return SafeDict(val)
            return val
        return SafeDict()

def _harden_api_server(api_server):
    if not api_server: return
    current = getattr(api_server, "config", None)
    if current is None:
        api_server.config = SafeDict()
    elif isinstance(current, dict) and not isinstance(current, SafeDict):
        api_server.config = SafeDict(current)

    for section in ("cors", "server", "uvicorn", "security", "auth"):
        _ = api_server.config.setdefault(section, SafeDict())

    if not hasattr(api_server, "settings") or getattr(api_server, "settings") is None:
        api_server.settings = api_server.config

def display_banner():
    print("=" * 70)
    print("""
        ███████╗██╗      ██████╗ ██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
        ██╔════╝██║     ██╔═══██╗██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
        █████╗  ██║     ██║   ██║██║ █╗ ██║██║   ██║██████╔╝█████╔╝
        ██╔══╝  ██║     ██║   ██║██║███╗██║██║   ██║██╔══██╗██╔═██╗
        ██║     ███████╗╚██████╔╝╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
        ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ██╗

        >> NEURAL ARCHITECT CORE - DYNAMIC ASSEMBLY <<
        >> STATUS: ALL 25 ORGANS DISCOVERED <<
        """)

def ensure_packages_exist():
    project_root = os.path.abspath(os.path.dirname(__file__))
    packages_to_check = ["generated_services"]
    for package in packages_to_check:
        package_path = os.path.join(project_root, package)
        init_file = os.path.join(package_path, "__init__.py")
        os.makedirs(package_path, exist_ok=True)
        if not os.path.exists(init_file):
            try:
                with open(init_file, "w") as f: pass
            except Exception: pass

class NeuralOrchestrator:
    def __init__(self, kernel, ipc_queue=None):
        self.kernel = kernel
        self.services_config = []
        self.project_root = os.path.abspath(os.path.dirname(__file__))
        self.ipc_queue = ipc_queue
        self.spawned_instances = [] # Per Rule 1 (Melacak instansi yang baru lahir)

    def load_manifest(self):
        manifest_path = os.path.join(self.project_root, "flowork_kernel", "services.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r") as f:
                    data = json.load(f)
                    self.services_config = data.get("services", [])
                    return True
            except Exception as e:
                logging.error(f"❌ [Orchestrator] Manifest Read Error: {e}")
        return False

    def assemble(self):
        logging.info("🧠 [Orchestrator] Starting Neural Assembly Sequence...")
        loaded_ids = set()
        remaining = list(self.services_config)

        while remaining:
            initial_len = len(remaining)
            for config in list(remaining):
                service_id = config["id"]
                deps = config.get("dependencies", [])
                if all(d in loaded_ids for d in deps):
                    instance = self._spawn_service(config)
                    if instance: self.spawned_instances.append((service_id, instance))
                    loaded_ids.add(service_id)
                    remaining.remove(config)
            if len(remaining) == initial_len:
                logging.error(f"❌ [Orchestrator] Unresolved Dependencies: {[r['id'] for r in remaining]}")
                break

        self._ignite_life_support()
        logging.info(f"✅ [Orchestrator] Assembly Complete. {len(loaded_ids)} Organs online.")

    def _spawn_service(self, config):
        try:
            service_id = config["id"]
            module_path = config["module_path"]
            class_name = config["class_name"]
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            if service_id == "event_bus" and self.ipc_queue:
                instance = cls(self.kernel, service_id, ipc_queue=self.ipc_queue)
            else:
                instance = cls(self.kernel, service_id)

            if config.get("singleton", True):
                Singleton.set_instance(service_id, instance)
                Singleton.set_instance(cls, instance)

            self.kernel.register_service(instance)

            if hasattr(instance, "setup") and service_id == "logging_service":
                instance.setup(log_level_str='DEBUG', log_to_file=True)

            if service_id == "app_runtime" and hasattr(instance, "start"):
                pass

            logging.info(f"🧬 [Spawn] organ '{service_id}' integrated.")
            return instance
        except Exception as e:
            logging.error(f"❌ [Orchestrator] Spawn Failed for {config.get('id')}: {e}")
            return None

    def _ignite_life_support(self):
        """Menyalakan fungsi monitoring setelah rakitan selesai"""
        for s_id, instance in self.spawned_instances:
            if s_id == "event_bus":
                instance.start()
                threading.Thread(target=instance.run_logic, daemon=True, name="EventBus_Watchdog").start()
            elif s_id == "vitality_service":
                threading.Thread(target=instance.run_logic, daemon=True, name="Vitality_Doctor").start()
            elif s_id not in ["app_runtime", "logging_service"] and hasattr(instance, "start"):
                if not asyncio.iscoroutinefunction(instance.start):
                    try: instance.start()
                    except: pass

async def main_async(kernel_services_dict):
    api_server = Singleton.get_instance("api_server_service")
    gateway_connector = Singleton.get_instance("gateway_connector_service")
    app_runtime = Singleton.get_instance("app_runtime") # [FIX] Added: Retrieve AppRuntimeService

    if not gateway_connector or not api_server: return

    _harden_api_server(api_server)
    gateway_connector.set_kernel_services(kernel_services_dict)

    print(f"--- FLOWORK Core Neural Services are running ---")
    await api_server.start()
    await asyncio.gather(
        asyncio.create_task(gateway_connector.start()),
        asyncio.create_task(app_runtime.start()) if app_runtime and hasattr(app_runtime, "start") else asyncio.sleep(0), # [FIX] Added: Start app_runtime in async loop
        asyncio.Event().wait()
    )

def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    project_root = os.path.abspath(os.path.dirname(__file__))

    class MockKernel:
        def __init__(self):
            self.APP_VERSION = "1.2.3-final"
            self.project_root_path = project_root
            self.app_path = os.path.join(project_root, "app")
            self.data_path = os.path.join(project_root, "data")
            self.locales_path = os.path.join(project_root, "locales")
            self.logs_path = os.path.join(project_root, "logs")
            self.themes_path = os.path.join(project_root, "themes")
            self.services = SafeDict()

        def get_root_dir(self): return self.project_root_path
        def write_to_log(self, msg, level="INFO", src="MockKernel"):
            logging.log(getattr(logging, level.upper(), logging.INFO), f"[{src}] {msg}")

        @property
        def event_bus(self): return self.get_service("event_bus")
        @property
        def loc(self): return self.get_service("localization_manager")

        def register_service(self, instance):
            sid = getattr(instance, "service_id", None)
            if sid: self.services[sid] = instance
            return True

        def get_service(self, sid, *args, **kwargs):
            if sid in self.services: return self.services[sid]
            return Singleton.get_instance(sid) or SafeDict()

    mock_kernel = MockKernel()
    event_ipc_queue = multiprocessing.Queue()

    orchestrator = NeuralOrchestrator(mock_kernel, ipc_queue=event_ipc_queue)
    if orchestrator.load_manifest():
        orchestrator.assemble()

    kernel_services_dict = {s_id: inst for s_id, inst in mock_kernel.services.items()}
    db_s = Singleton.get_instance("database_service")
    DB_PATH = os.path.abspath(db_s.db_path) if db_s else os.path.join(project_root, "data", "flowork_core.db")

    for i in range(2):
        Process(target=worker_process, args=(DB_PATH, project_root, event_ipc_queue), name=f"JobWorker-{i}").start()

    start_heartbeat()
    try:
        asyncio.run(main_async(kernel_services_dict))
    except KeyboardInterrupt: pass
    except Exception: traceback.print_exc()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    display_banner()
    ensure_packages_exist()
    main()
