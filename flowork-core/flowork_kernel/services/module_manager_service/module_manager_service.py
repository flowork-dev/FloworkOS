########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\module_manager_service\module_manager_service.py total lines 361 
########################################################################

import os
import json
import importlib.util
import subprocess
import sys
import traceback
from ..base_service import BaseService
import zipfile
import tempfile
import shutil
from flowork_kernel.exceptions import PermissionDeniedError
import hashlib
import threading
import time

class ModuleManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.modules_dir = self.kernel.modules_path
        self.loaded_modules = {}
        self.instance_cache = {}
        self.paused_status_file = os.path.join(
            self.kernel.data_path, "paused_modules.json"
        )
        self._manual_approval_callbacks = {}

        self.known_requirements = {
            "golden_moment_clipper": [
                "numpy",
                "opencv-python-headless",
                "mediapipe",
                "faster-whisper",
                "protobuf==3.20.3"
            ],
            "agent_host": [], # Tidak butuh deps khusus
            "metrics_dashboard": [] # Tidak butuh deps khusus
        }

        self.watch_map = {
            'modules':      {'service': 'module_manager_service',   'loader': 'discover_and_load_modules'},
            'plugins':      {'service': 'plugin_manager_service',   'loader': 'discover_and_load_plugins'},
            'tools':        {'service': 'tools_manager_service',    'loader': 'discover_and_load_tools'},
            'triggers':     {'service': 'trigger_manager_service',  'loader': 'discover_and_load_triggers'},
            'widgets':      {'service': 'widget_manager_service',   'loader': 'discover_and_load_widgets'},
            'scanners':     {'service': 'scanner_manager_service',  'loader': 'discover_and_load_scanners'},
            'ai_providers': {'service': 'ai_provider_manager_service', 'loader': 'reload_providers'}
        }

        self._installing_lock = threading.Lock()
        self._watchdog_active = True

        self._start_watchdog()

        self.logger.debug("Service 'ModuleManager' initialized.")

    def _get_root_path(self):
        if os.path.exists("/app/flowork_kernel/modules"):
            return "/app/flowork_kernel"

        if os.path.exists("/app/modules"):
            return "/app"

        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "flowork_kernel", "modules")):
            return os.path.join(cwd, "flowork_kernel")

        return getattr(self.kernel, "project_root_path", cwd)

    def install_component_dependencies(self, component_id: str, on_complete=None):
        self.logger.info(f"🔧 [Manual Install] Request received for: {component_id}")
        target_path = None
        target_label = ""

        if component_id in self.loaded_modules:
            target_path = self.loaded_modules[component_id]["path"]
            target_label = f"[MODULE] {component_id}"
        else:
            root_path = self._get_root_path()
            for folder_name in self.watch_map.keys():
                candidate = os.path.join(root_path, folder_name, component_id)
                if os.path.isdir(candidate):
                    target_path = candidate
                    target_label = f"[{folder_name.upper()}] {component_id}"
                    break

        if not target_path:
            msg = f"Component '{component_id}' not found on disk."
            self.logger.error(f"❌ [Manual Install] {msg}")
            if on_complete: on_complete(False, msg)
            return False, msg

        with self._installing_lock:
            success, msg = self._smart_install(target_path, component_id) # Pass component_id for lookup

        if success: self.discover_and_load_modules()
        if on_complete: on_complete(success, msg)
        return success, msg

    def _smart_install(self, path, component_id_or_label):
        req_file = os.path.join(path, "requirements.txt")
        marker_file = os.path.join(path, ".installed")
        hash_file = os.path.join(path, ".requirements_hash")

        simple_id = component_id_or_label
        if "]" in simple_id:
            simple_id = simple_id.split("] ")[-1].strip()

        if not os.path.exists(req_file):
            if simple_id in self.known_requirements:
                backup_libs = self.known_requirements[simple_id]

                if len(backup_libs) > 0:
                    self.logger.warning(f"⚠️ [Installer] Requirements missing for '{simple_id}'. ACTIVATING EMERGENCY RESTORE...")
                    try:
                        content = "\n".join(backup_libs)
                        with open(req_file, "w") as f:
                            f.write(content)
                        self.logger.info(f"✅ [Installer] Restored requirements.txt with {len(backup_libs)} libraries.")
                    except Exception as e:
                        return False, f"Failed to restore requirements: {e}"
                else:
                    self.logger.info(f"ℹ️ [Installer] Component '{simple_id}' requires no dependencies. Marking installed.")
                    try:
                        with open(marker_file, "w") as f: f.write(f"Installed (Zero Deps) on {time.ctime()}")
                        return True, "Installed (No Dependencies)"
                    except: return False, "Marker fail"
            else:
                self.logger.info(f"ℹ️ [Installer] No requirements found for '{simple_id}'. Assuming standalone.")
                try:
                    with open(marker_file, "w") as f: f.write(f"Installed (No Deps) on {time.ctime()}")
                    return True, "Installed (No Dependencies)"
                except: return False, "Marker fail"

        self.logger.info(f"📦 [Installer] Installing dependencies for {simple_id}...")
        try:
            python_exe = sys.executable
            cmd = [
                python_exe, "-m", "pip", "install",
                "-r", req_file,
                "--disable-pip-version-check",
                "--prefer-binary"
            ]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            if proc.returncode == 0:
                with open(marker_file, "w") as f: f.write(f"Installed on {time.ctime()}")
                with open(hash_file, "w") as f: f.write(self._calculate_file_hash(req_file))
                self.logger.info(f"✅ [Installer] Success: {simple_id}")
                return True, "Dependencies installed successfully."
            else:
                err = f"PIP Error: {proc.stdout[:300]}..."
                self.logger.error(f"❌ [Installer] Failed: {simple_id} -> {err}")
                return False, err
        except Exception as e:
            self.logger.error(f"❌ [Installer] Exception: {e}")
            return False, str(e)

    def _start_watchdog(self):
        thread = threading.Thread(target=self._watchdog_loop, daemon=True, name="Flowork-Watchdog")
        thread.start()

    def _watchdog_loop(self):
        time.sleep(3)
        self.logger.info("🚀 [Watchdog] INITIAL SCAN STARTED...")
        try:
            self._scan_targets_and_install(verbose=True)
            self.logger.info("✅ [Watchdog] INITIAL BOOT SCAN COMPLETE.")
        except Exception as e:
            self.logger.error(f"⚠️ [Watchdog] Boot Scan Error: {e}")

        while self._watchdog_active:
            try:
                time.sleep(10)
                self._scan_targets_and_install(verbose=False)
            except Exception as e:
                self.logger.error(f"🐶 [Watchdog] Loop Error: {e}")

    def _scan_targets_and_install(self, verbose=False):
        root_path = self._get_root_path()
        if verbose: self.logger.info(f"🐶 [Watchdog] Scanning Root: {root_path}")

        for folder_name, config in self.watch_map.items():
            base_dir = os.path.join(root_path, folder_name)
            if not os.path.exists(base_dir): continue

            try: items = os.listdir(base_dir)
            except: continue

            for item_name in items:
                if item_name.startswith(".") or item_name.startswith("__"): continue
                item_path = os.path.join(base_dir, item_name)
                if not os.path.isdir(item_path): continue

                is_target = "golden_moment" in item_name

                if self._needs_check(item_path, item_name, verbose=(verbose and is_target)):
                    with self._installing_lock:
                        if self._needs_check(item_path, item_name):
                            label = f"[{folder_name.upper()}] {item_name}"
                            if verbose or is_target: self.logger.info(f"📦 [Watchdog] Auto-Installing: {label}")

                            success, _ = self._smart_install(item_path, item_name)

                            if success:
                                self._trigger_reload(config['service'], config['loader'], label)

    def _needs_check(self, path, item_name, verbose=False):
        marker = os.path.join(path, ".installed")
        req = os.path.join(path, "requirements.txt")

        if not os.path.exists(marker):
            if verbose: self.logger.info(f"   -> Missing marker. Queueing...")
            return True

        if not os.path.exists(req) and item_name in self.known_requirements:
            if len(self.known_requirements[item_name]) > 0:
                if verbose: self.logger.info(f"   -> Critical requirements missing! Queueing restore...")
                return True

        if os.path.exists(req):
            if os.path.getmtime(req) > os.path.getmtime(marker):
                if verbose: self.logger.info(f"   -> Requirements updated. Queueing...")
                return True

        return False

    def _trigger_reload(self, svc, method, label):
        try:
            s = self.kernel.get_service(svc)
            if s and hasattr(s, method):
                self.logger.info(f"🔄 [Watchdog] Reloading {label}")
                threading.Thread(target=getattr(s, method)).start()
        except: pass

    def _calculate_file_hash(self, filepath):
        try:
            hasher = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""): hasher.update(chunk)
            return hasher.hexdigest()
        except: return ""


    def discover_and_load_modules(self):
        self.logger.info("ModuleManager: Loading discovered modules...")
        if not hasattr(self.kernel, "globally_disabled_components"):
            self.kernel.globally_disabled_components = set()

        try:
            root = self._get_root_path()
            modules_path = os.path.join(root, "modules")
            if os.path.exists(modules_path): self.modules_dir = modules_path
        except: pass

        self.loaded_modules.clear()
        self.instance_cache.clear()
        paused_ids = self._load_paused_status()

        if os.path.exists(self.modules_dir):
            for item_id in os.listdir(self.modules_dir):
                if item_id in self.kernel.globally_disabled_components: continue
                item_dir = os.path.join(self.modules_dir, item_id)
                if os.path.isdir(item_dir) and item_id != "__pycache__":
                    manifest_path = os.path.join(item_dir, "manifest.json")
                    if not os.path.exists(manifest_path): continue
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f: manifest = json.load(f)
                        is_installed = os.path.exists(os.path.join(item_dir, ".installed"))

                        module_data = {
                            "manifest": manifest, "path": item_dir, "installed_as": "module",
                            "is_paused": item_id in paused_ids, "permissions": manifest.get("permissions", []),
                            "tier": manifest.get("tier", "free").lower(), "is_installed": is_installed
                        }

                        self.loaded_modules[item_id] = module_data

                        manifest_id = manifest.get("id")
                        if manifest_id and manifest_id != item_id:
                             self.loaded_modules[manifest_id] = module_data
                             self.logger.info(f"   -> Registered Alias: '{manifest_id}' points to '{item_id}'")

                    except Exception as e: self.logger.warning(f"Manifest error {item_id}: {e}")

        var_mgr = self.kernel.get_service("variable_manager_service")
        if var_mgr: var_mgr.autodiscover_and_sync_variables()
        self.logger.info(f"ModuleManager: Loaded {len(self.loaded_modules)} modules.")

    def get_instance(self, module_id):
        if module_id in self.instance_cache: return self.instance_cache[module_id]
        data = self.loaded_modules.get(module_id)
        if not data or data.get("is_paused"): return None
        if not data.get("is_installed", False): return None

        try:
            vendor = os.path.join(data["path"], "vendor")
            if os.path.isdir(vendor) and vendor not in sys.path: sys.path.insert(0, vendor)

            entry = data["manifest"].get("entry_point")
            if not entry: return None
            mod_file, cls_name = entry.split(".")
            src = os.path.join(data["path"], f"{mod_file}.py")

            spec = importlib.util.spec_from_file_location(f"modules.{module_id.replace('-','_')}", src)
            lib = importlib.util.module_from_spec(spec)
            pkg_name = f"modules.{module_id.replace('-','_')}"
            if pkg_name not in sys.modules: sys.modules[pkg_name] = lib

            spec.loader.exec_module(lib)
            Processor = getattr(lib, cls_name)

            svc_map = {}
            for req in data["manifest"].get("requires_services", []):
                if req == "loc": svc_map["loc"] = self.kernel.get_service("localization_manager")
                elif req == "logger": svc_map["logger"] = self.kernel.write_to_log
                elif req == "kernel": svc_map["kernel"] = self.kernel
                else:
                    s = self.kernel.get_service(req)
                    if s: svc_map[req] = s

            inst = Processor(module_id, svc_map)
            if hasattr(inst, "on_load"): inst.on_load()
            self.instance_cache[module_id] = inst
            return inst
        except Exception as e:
            self.logger.error(f"Instantiation error {module_id}: {e}")
            return None

    def install_component(self, zip_filepath: str) -> (bool, str):
        return True, "Zip uploaded. Watchdog will process it."

    def uninstall_component(self, component_id: str) -> (bool, str):
        if component_id not in self.loaded_modules: return False, "Not loaded"
        try:
            path = self.loaded_modules[component_id]["path"]
            shutil.rmtree(path)
            del self.loaded_modules[component_id]
            if component_id in self.instance_cache: del self.instance_cache[component_id]
            return True, "Uninstalled"
        except Exception as e: return False, str(e)

    def get_manifest(self, mid): return self.loaded_modules.get(mid, {}).get("manifest")
    def get_module_permissions(self, mid): return self.loaded_modules.get(mid, {}).get("permissions", [])
    def get_module_tier(self, mid): return self.loaded_modules.get(mid, {}).get("tier", "free")
    def _load_paused_status(self):
        try:
            with open(self.paused_status_file) as f: return json.load(f)
        except: return []
    def _save_paused_status(self):
        try:
            p = [k for k,v in self.loaded_modules.items() if v.get("is_paused")]
            with open(self.paused_status_file, "w") as f: json.dump(p, f)
        except: pass
