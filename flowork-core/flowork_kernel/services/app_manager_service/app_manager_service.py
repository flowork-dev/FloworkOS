########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\app_manager_service.py total lines 413 
########################################################################

import os
import json
import importlib.util
import sys
import re # [ADDED BY FLOWORK DEV] Untuk Regex replacement yang lebih robust
import subprocess # [PHASE 3 ADDITION]
import time       # [PHASE 3 ADDITION]
import threading  # [GHOST PROTOCOL] Required for background reaper
import requests   # [PHASE 4 ADDITION] For graceful shutdown requests
from typing import Dict, Any, List, Optional
from ..base_service import BaseService
from flowork_kernel.utils.path_helper import get_apps_directory

class AppService(BaseService):
    """
    THE APP FACE MANAGER
    Murni mengurus GUI, Assets, dan Backend Service (app_service.py).
    Standardized to isolate GUI Path from Logic Path.
    """
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.base_app_path = os.environ.get("FLOWORK_APPS_DIR", str(get_apps_directory()))

        self.registry = {
            "apps":     {"path": self.base_app_path, "data": {}}
        }
        self.instances = {}

        self.port_registry = {} # { "app_id": 5001 }
        self.process_registry = {} # { "app_id": Popen_Object }
        self.next_port = 5001

        self.last_activity = {} # { "app_id": timestamp }
        self.ghost_timeout = 300 # 5 Menit (300 detik) Idle = Kill
        self.is_ghost_active = True

        self.crash_tracker = {} # { "app_id": [timestamp1, timestamp2] }
        self.quarantine_registry = {} # { "app_id": { "reason": str, "timestamp": float } }
        self.CRASH_WINDOW = 60 # Detik
        self.MAX_RESTARTS = 3  # Kali

    def get_assigned_port(self, app_id: str) -> int:
        """Assign or retrieve existing port for an App."""
        if app_id in self.port_registry:
            return self.port_registry[app_id]

        port = self.next_port
        self.next_port += 1
        self.port_registry[app_id] = port
        return port

    def _touch_app_activity(self, app_id):
        """Menandai bahwa App sedang aktif/sibuk"""
        self.last_activity[app_id] = time.time()

    def _check_immune_system(self, app_id):
        """
        Mengecek apakah App sehat atau harus dikarantina.
        Return True jika AMAN, Raise Exception jika BAHAYA.
        """
        now = time.time()

        if app_id in self.quarantine_registry:
            q_data = self.quarantine_registry[app_id]
            if now - q_data['timestamp'] > 3600:
                del self.quarantine_registry[app_id]
                self.logger.info(f"🛡️ [Immune] App '{app_id}' released from quarantine (Time Served).")
            else:
                raise Exception(f"⛔ App '{app_id}' is in QUARANTINE! Reason: {q_data['reason']}")

        history = self.crash_tracker.get(app_id, [])
        history = [t for t in history if now - t < self.CRASH_WINDOW]

        history.append(now)
        self.crash_tracker[app_id] = history

        if len(history) > self.MAX_RESTARTS:
            self.quarantine_registry[app_id] = {
                "reason": "Crash Loop Detected (>3 restarts/min)",
                "timestamp": now
            }
            self.logger.error(f"🛡️ [Immune] CRITICAL: App '{app_id}' entered crash loop. QUARANTINED.")
            raise Exception(f"⛔ App '{app_id}' detected in Crash Loop and has been QUARANTINED.")

        return True

    def _perform_autoheal(self, app_id, app_path):
        """
        Dokter Pribadi: Memanggil LibraryManager untuk re-install dependency.
        """
        self.logger.info(f"🚑 [AutoHeal] Starting emergency repairs for '{app_id}'...")
        lib_manager = self.kernel.get_service("library_manager")
        if not lib_manager:
            self.logger.error("❌ AutoHeal Failed: LibraryManager missing.")
            return False

        req_file = os.path.join(app_path, "requirements.txt")
        if os.path.exists(req_file):
            try:
                lib_manager.resolve_dependencies(app_id, req_file)
                self.logger.info(f"✅ [AutoHeal] Repair successful for '{app_id}'.")
                return True
            except Exception as e:
                self.logger.error(f"❌ [AutoHeal] Repair failed: {e}")
                return False
        else:
            self.logger.warning(f"⚠️ [AutoHeal] No requirements.txt found for '{app_id}'. Cannot heal.")
            return False

    def ensure_app_running(self, app_id: str, retry_count=0):
        """
        Memastikan Daemon Runner untuk App ini hidup.
        Kalau belum hidup, nyalakan! (Auto-Wake)
        """
        self._touch_app_activity(app_id)

        try:
            self._check_immune_system(app_id)
        except Exception as e:
            self.logger.warning(str(e))
            raise e # Tolak start

        if app_id in self.process_registry:
            proc = self.process_registry[app_id]
            if proc.poll() is None: # None artinya masih running
                return self.get_assigned_port(app_id)
            else:
                self.logger.warning(f"⚠️ [AppManager] App {app_id} found dead (Exit Code: {proc.returncode}). Restarting...")

        port = self.get_assigned_port(app_id)
        app_info = self.registry["apps"]["data"].get(app_id)

        if not app_info:
            self.sync("apps")
            app_info = self.registry["apps"]["data"].get(app_id)
            if not app_info:
                 raise Exception(f"App {app_id} not installed or manifest missing.")

        app_path = app_info["path"]

        lib_manager = self.kernel.get_service("library_manager")
        lib_paths = []
        if lib_manager:
            req_file = os.path.join(app_path, "requirements.txt")
            if os.path.exists(req_file):
                self.logger.info(f"📦 [AppManager] Requesting libraries for {app_id}...")
                lib_paths = lib_manager.resolve_dependencies(app_id, req_file)

        lib_paths_str = json.dumps(lib_paths)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        core_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

        runner_script = "/app/app/executor/runner.py"

        if not os.path.exists(runner_script):
            runner_script = os.path.join(self.kernel.project_root_path, "app", "executor", "runner.py")

        app_data_path = os.path.join(self.kernel.project_root_path, "data", "apps_storage", app_id)
        if not os.path.exists(app_data_path):
            os.makedirs(app_data_path, exist_ok=True)

        try:
            cmd = [
                sys.executable,
                runner_script if os.path.exists(runner_script) else os.path.join(core_root, "app", "executor", "runner.py"),
                "--daemon",
                "--port", str(port),
                "--path", app_path,
                "--appid", app_id,
                "--libs", lib_paths_str
            ]

            env_copy = os.environ.copy()
            env_copy["FLOWORK_APP_DATA_PATH"] = app_data_path

            proc = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(runner_script) if os.path.exists(os.path.dirname(runner_script)) else core_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env_copy # Inject ENV
            )

            self.process_registry[app_id] = proc
            self.logger.info(f"🚀 [AppManager] Spawned Daemon for {app_id} on port {port} (PID: {proc.pid})")

            time.sleep(0.5)

            exit_code = proc.poll()
            if exit_code is not None:
                if exit_code == 101 and retry_count < 1: # Exit Code 101 = Dependency Missing
                    self.logger.warning(f"🚑 [AppManager] App '{app_id}' died requesting Auto-Heal (Missing Libs). Administering cure...")

                    healed = self._perform_autoheal(app_id, app_path)

                    if healed:
                        self.logger.info(f"🔁 [AppManager] Restarting healed App '{app_id}'...")
                        if app_id in self.crash_tracker:
                            self.crash_tracker[app_id].pop()

                        return self.ensure_app_running(app_id, retry_count=1)
                    else:
                        raise Exception(f"Auto-Heal failed for {app_id}.")

                raise Exception(f"Immediate Crash Detected! Exit Code: {exit_code}")

            return port

        except Exception as e:
            self.logger.error(f"❌ [AppManager] Failed to spawn runner for {app_id}: {e}")
            raise e

    def kill_app(self, app_id: str):
        """Force kill app daemon with Cleanup Signal."""
        if app_id in self.process_registry:
            port = self.get_assigned_port(app_id)
            proc = self.process_registry[app_id]

            try:
                self.logger.info(f"🧹 [Janitor] Sending cleanup signal to {app_id}...")
                requests.post(f"http://localhost:{port}/cleanup", timeout=2)
            except:
                pass # Mungkin app sudah hang

            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                proc.kill()
            del self.process_registry[app_id]
            self.logger.info(f"💀 [AppManager] Killed App {app_id}")

    def sync(self, category: str = "apps") -> Dict:
        """
        Only syncs APP entities with GUI and Service backends.
        Strictly ignores any node/workflow definitions.
        """
        target_path = self.base_app_path
        if not os.path.exists(target_path): return {}

        for item_id in os.listdir(target_path):
            item_path = os.path.join(target_path, item_id)
            manifest_file = os.path.join(item_path, "manifest.json")

            if os.path.isdir(item_path) and os.path.exists(manifest_file):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)

                    m_id = manifest.get("id")
                    if not m_id: continue

                    provided = manifest.get("provided_services", [])

                    is_quarantined = m_id in self.quarantine_registry
                    status_label = "QUARANTINED" if is_quarantined else "READY"

                    app_info = {
                        "manifest": manifest,
                        "path": item_path,
                        "type": "apps",
                        "is_installed": True,
                        "icon_url": f"/api/v1/components/app/{m_id}/icon",
                        "gui_url": f"/api/v1/muscle-assets/{m_id}/assets/index.html",
                        "services": provided,
                        "status": status_label # Info status untuk GUI
                    }

                    self.registry["apps"]["data"][m_id] = app_info

                except Exception: pass
        return self.registry.get("apps", {"data": {}})["data"]

    def get_registry(self, category: str = "apps"):
        return self.sync("apps")

    def get_instance(self, category: str, item_id: str):
        """
        Retrieves the GUI backend instance.
        Standardized to use app_service.py for the sterile GUI path.
        """
        self._touch_app_activity(item_id)

        if item_id in self.quarantine_registry:
            self.logger.warning(f"🚫 Access to quarantined app '{item_id}' blocked.")
            return None

        instance_key = f"{category}:{item_id}"
        if instance_key in self.instances: return self.instances[instance_key]

        app_info = self.registry["apps"]["data"].get(item_id)
        if not app_info: return None

        app_folder_path = app_info["path"]
        backend_path = os.path.join(app_folder_path, "backend")

        service_file = os.path.join(backend_path, "app_service.py")

        if not os.path.exists(service_file):
            self.logger.warning(f"⚠️ [AppManager] App {item_id} has no app_service.py (GUI path missing).")
            return None

        try:
            module_name = f"flowork_app_exec_{item_id}"
            if app_folder_path not in sys.path: sys.path.insert(0, app_folder_path)
            if backend_path not in sys.path: sys.path.insert(0, backend_path)

            spec = importlib.util.spec_from_file_location(module_name, service_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if isinstance(attr, type) and getattr(attr, '__module__', '') == module_name:
                    if attr_name not in ["BaseModule", "Module", "BaseAppNode", "BaseService", "BaseAppService"]:
                        try: new_instance = attr(item_id, {}, self.kernel)
                        except:
                            try: new_instance = attr(self.kernel, f"app_{item_id}")
                            except: new_instance = attr()

                        self._bind_router_to_instance(new_instance, app_folder_path, item_id)
                        self.instances[instance_key] = new_instance
                        return new_instance
        except Exception as e:
            self.logger.error(f"❌ [AppManager] GUI Service init failed for {item_id}: {e}")
        return None

    def _bind_router_to_instance(self, instance_obj, app_dir, app_id):
        """
        Standardized to use app_router.py.
        Now with Regex POWER for robust imports! 🛡️
        """
        router_path = os.path.join(app_dir, "backend", "app_router.py")

        if os.path.exists(router_path):
            try:
                with open(router_path, 'r') as f:
                    source = f.read()

                    source = re.sub(r'from\s+(?:\.?)\s*service\s+import', 'from app_service import', source)
                    source = re.sub(r'^\s*import\s+service\s*$', 'import app_service as service', source, flags=re.MULTILINE)
                    source = source.replace("from flowork_kernel.router import BaseRouter", "class BaseRouter: def __init__(self, k): self.kernel = k")

                module_name = f"flowork_router_v_final_{app_id}"
                spec = importlib.util.spec_from_file_location(module_name, router_path)
                mod = importlib.util.module_from_spec(spec)
                exec(source, mod.__dict__)

                if hasattr(mod, 'AppRouter'):
                    instance_obj.router = mod.AppRouter(instance_obj)
                    self.logger.info(f"🔗 [Router] Success binding app_router to GUI {app_id}")
            except Exception as e:
                self.logger.error(f"⚠️ [Router] Bind failed for {app_id}: {e}")

    def _ghost_reaper_loop(self):
        """
        Background thread yang memantau App nganggur.
        Jika App tidak disentuh selama self.ghost_timeout, MATIKAN.
        """
        self.logger.info(f"👻 [Ghost] Protocol Activated. Timeout: {self.ghost_timeout}s")
        while self.is_ghost_active:
            time.sleep(30) # Cek setiap 30 detik (hemat CPU)
            try:
                now = time.time()
                active_apps = list(self.last_activity.keys())

                for app_id in active_apps:
                    last_time = self.last_activity.get(app_id, 0)
                    if now - last_time > self.ghost_timeout:
                        if app_id in self.process_registry:
                            self.logger.info(f"👻 [Ghost] App '{app_id}' is idle for {int(now - last_time)}s. Sending to Void (Sleep)...")
                            self.kill_app(app_id)
                            if app_id in self.last_activity:
                                del self.last_activity[app_id]
            except Exception as e:
                self.logger.error(f"👻 [Ghost] Reaper Error: {e}")

    def _setup_neural_listener(self):
        """
        Mendengarkan event log dari App.
        Jika App nge-log (misal: 'Rendering 50%'), kita anggap dia SIBUK.
        """
        if hasattr(self.kernel, 'event_bus'):
            try:
                def heartbeat_handler(event_name, event_id, payload_data):
                    payload = payload_data.get('payload', payload_data)
                    app_id = payload.get('app_id')

                    if app_id:
                        clean_id = app_id.replace("runner_", "").replace("app_", "")
                        if clean_id in self.last_activity:
                            self.last_activity[clean_id] = time.time()

                self.kernel.event_bus.subscribe("APP_LOG_STREAM", "ghost_keeper", heartbeat_handler)
                self.kernel.event_bus.subscribe("APP_PROGRESS", "ghost_keeper_prog", heartbeat_handler)
                self.logger.info("👻 [Ghost] Connected to Nervous System (Smart Keep-Alive Active).")
            except Exception as e:
                self.logger.warning(f"👻 [Ghost] Failed to attach neural listener: {e}")

    def start(self):
        self.sync("apps")

        if self.is_ghost_active:
            self._setup_neural_listener()
            t = threading.Thread(target=self._ghost_reaper_loop, daemon=True, name="GhostReaper")
            t.start()
