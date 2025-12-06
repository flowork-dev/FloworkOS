########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\plugin_manager_service\plugin_manager_service.py total lines 475 
########################################################################

import os
import json
import importlib.util
import subprocess
import sys
import traceback
from flowork_kernel.api_contract import BaseModule
from ..base_service import BaseService
import zipfile
import tempfile
import shutil
import hashlib
from flowork_kernel.exceptions import PermissionDeniedError
import threading
import shutil

class PluginManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.plugins_dir = self.kernel.plugins_path
        self.system_plugins_dir = self.kernel.system_plugins_path
        self.loaded_plugins = {}
        self.instance_cache = {}
        self.paused_status_file = os.path.join(
            self.kernel.data_path, "paused_plugins.json"
        )
        self.logger.debug(
            f"Service 'PluginManagerService' initialized."
        )

    def discover_and_load_plugins(self):
        self.logger.info(
            "PluginManager: Starting discovery and loading based on folder location..."
        )

        if not hasattr(self.kernel, "globally_disabled_components"):
            self.kernel.globally_disabled_components = set()
        if not hasattr(self.kernel, "globally_disabled_types"):
            self.kernel.globally_disabled_types = set()

        try:
            if not os.path.exists(self.plugins_dir):
                alt_dir = os.path.join(getattr(self.kernel, "project_root_path", ""), "plugins")
                if alt_dir and os.path.exists(alt_dir):
                    self.logger.warning(f"[Compat] Using fallback plugins path: {alt_dir}")
                    self.plugins_dir = alt_dir
        except Exception:
            pass

        self.loaded_plugins.clear()
        self.instance_cache.clear()
        paused_ids = self._load_paused_status()

        paths_to_scan = [self.plugins_dir, self.system_plugins_dir]
        for base_path in paths_to_scan:
            if not os.path.exists(base_path):
                continue

            self.logger.debug(
                f"PluginManager: Scanning for plugins in '{base_path}'"
            )

            for item_id in os.listdir(base_path):
                if item_id in self.kernel.globally_disabled_components:
                    self.logger.warning(f"Skipping globally disabled plugin: {item_id}")
                    continue

                item_dir = os.path.join(base_path, item_id)
                if os.path.isdir(item_dir) and item_id != "__pycache__":
                    manifest_path = os.path.join(item_dir, "manifest.json")
                    if not os.path.exists(manifest_path):
                        continue

                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)

                        is_paused = item_id in paused_ids
                        install_marker_path = os.path.join(item_dir, ".installed")
                        is_installed = os.path.exists(install_marker_path)

                        module_data = {
                            "manifest": manifest,
                            "path": item_dir,
                            "installed_as": "plugin",
                            "is_paused": is_paused,
                            "permissions": manifest.get("permissions", []),
                            "tier": manifest.get("tier", "free").lower(),
                            "is_installed": is_installed,
                        }
                        self.loaded_plugins[item_id] = module_data
                    except Exception as e:
                        self.logger.warning(
                            f"   ! Failed to process manifest for plugin '{item_id}': {e}"
                        )

        self.logger.info(
            f"PluginManager: Discovery complete. Found {len(self.loaded_plugins)} plugins."
        )

        event_bus = self.kernel.get_service("event_bus")
        if event_bus:
            event_bus.publish("COMPONENT_LIST_CHANGED", {"type": "plugin"})
            self.logger.info(
                "PluginManager: Fired COMPONENT_LIST_CHANGED event after discovery."
            )

    def _get_venv_site_packages_path(self, venv_path):

        if sys.platform == "win32":
            return os.path.join(venv_path, "Lib", "site-packages")
        else:
            lib_path = os.path.join(venv_path, "lib")
            if os.path.isdir(lib_path):
                py_dirs = [d for d in os.listdir(lib_path) if d.startswith('python')]
                if py_dirs:
                    return os.path.join(lib_path, py_dirs[0], "site-packages")
        return None

    def force_reload_plugins(self):
        self.logger.info(
            "PluginManager: Force reload triggered, re-scanning all plugin directories..."
        )
        self.discover_and_load_plugins()
        self.logger.info(
            "PluginManager: Force reload complete and notification sent via Event Bus."
        )

    def get_instance(self, plugin_id):
        if plugin_id in self.instance_cache:
            return self.instance_cache[plugin_id]
        if plugin_id not in self.loaded_plugins:
            self.logger.error(
                f"Attempted to get instance for unknown plugin_id: {plugin_id}"
            )
            return None

        plugin_data = self.loaded_plugins[plugin_id]

        if plugin_data.get("is_paused", False):
            return None

        try:
            self._ensure_dependencies_up_to_date(plugin_id, plugin_data)
        except Exception as e:
            self.logger.error(f"Dependency Sync Failed for plugin '{plugin_id}': {e}")
            return None

        self.logger.debug(
            f"Just-In-Time Load: Instantiating plugin '{plugin_id}' for the first time."
        )

        vendor_path = os.path.join(plugin_data["path"], "vendor")
        is_vendor_path_added = False
        venv_path = os.path.join(plugin_data["path"], ".venv")
        site_packages_path = self._get_venv_site_packages_path(venv_path)
        is_venv_path_added = False

        try:
            if os.path.isdir(vendor_path) and vendor_path not in sys.path:
                sys.path.insert(0, vendor_path)
                is_vendor_path_added = True

            if site_packages_path and os.path.isdir(site_packages_path):
                if site_packages_path not in sys.path:
                    sys.path.insert(0, site_packages_path)
                    is_venv_path_added = True
                    self.logger.debug(f"Added venv path to sys.path for '{plugin_id}': {site_packages_path}")

            manifest = plugin_data["manifest"]
            entry_point = manifest.get("entry_point")
            if not entry_point:
                raise ValueError(f"'entry_point' not found for '{plugin_id}'.")

            module_filename, class_name = entry_point.split(".")
            source_file_path = os.path.join(
                plugin_data["path"], f"{module_filename}.py"
            )

            if not os.path.exists(source_file_path):
                raise FileNotFoundError(
                    f"Entry point file not found for '{plugin_id}'."
                )

            safe_plugin_id = plugin_id.replace("-", "_")
            parent_package_name = f"plugins.{safe_plugin_id}"
            module_full_name = f"{parent_package_name}.{module_filename}"

            spec = importlib.util.spec_from_file_location(
                module_full_name, source_file_path
            )
            if spec is None:
                raise ImportError(
                    f"Could not create module spec from {source_file_path}"
                )

            module_lib = importlib.util.module_from_spec(spec)

            if "plugins" not in sys.modules:
                spec_base = importlib.util.spec_from_loader(
                    "plugins", loader=None, is_package=True
                )
                module_base = importlib.util.module_from_spec(spec_base)
                sys.modules["plugins"] = module_base

            if parent_package_name not in sys.modules:
                spec_parent = importlib.util.spec_from_loader(
                    parent_package_name, loader=None, is_package=True
                )
                module_parent = importlib.util.module_from_spec(spec_parent)
                module_parent.__path__ = [plugin_data["path"]]
                sys.modules[parent_package_name] = module_parent

            sys.modules[module_full_name] = module_lib

            self.logger.debug(
                f"Executing module '{module_full_name}' for plugin '{plugin_id}'..."
            )

            spec.loader.exec_module(module_lib)

            self.logger.info(
                f"Module execution successful for '{plugin_id}'."
            )

            ProcessorClass = getattr(module_lib, class_name)

            services_to_inject = {}
            requested_services = manifest.get("requires_services", [])
            for service_alias in requested_services:
                if service_alias == "loc":
                    services_to_inject["loc"] = self.kernel.get_service(
                        "localization_manager"
                    )
                elif service_alias == "logger":
                    services_to_inject["logger"] = self.kernel.write_to_log
                elif service_alias == "kernel":
                    services_to_inject["kernel"] = self.kernel
                else:
                    service_instance = self.kernel.get_service(service_alias)
                    if service_instance:
                        services_to_inject[service_alias] = service_instance

            self.logger.debug(
                f"Initializing class '{class_name}' for plugin '{plugin_id}'..."
            )

            plugin_instance = ProcessorClass(plugin_id, services_to_inject)

            self.logger.info(
                f"Class initialization successful for '{plugin_id}'."
            )

            if hasattr(plugin_instance, "on_load"):
                plugin_instance.on_load()

            self.instance_cache[plugin_id] = plugin_instance
            self.loaded_plugins[plugin_id]["instance"] = plugin_instance
            return plugin_instance

        except PermissionDeniedError as e:
            self.logger.warning(
                f"Skipping instantiation of plugin '{plugin_id}' due to insufficient permissions: {e}"
            )
            return None
        except Exception as e:
            self.logger.critical(
                f"CRITICAL FAILURE during Just-In-Time instantiation of plugin '{plugin_id}': {e}"
            )
            self.logger.debug(traceback.format_exc())
            return None
        finally:
            if is_vendor_path_added:
                try:
                    sys.path.remove(vendor_path)
                except ValueError:
                    pass
            if is_venv_path_added:
                try:
                    sys.path.remove(site_packages_path)
                    self.logger.debug(f"Removed venv path from sys.path for '{plugin_id}'")
                except ValueError:
                    pass

    def _calculate_requirements_hash(self, file_path):
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except IOError:
            return None

    def _ensure_dependencies_up_to_date(self, plugin_id, plugin_data):
        path = plugin_data["path"]
        req_path = os.path.join(path, "requirements.txt")
        hash_file_path = os.path.join(path, ".requirements_hash")

        if not os.path.exists(req_path):
            return

        current_hash = self._calculate_requirements_hash(req_path)
        stored_hash = None

        if os.path.exists(hash_file_path):
            try:
                with open(hash_file_path, "r") as f:
                    stored_hash = f.read().strip()
            except:
                pass

        if current_hash != stored_hash or not plugin_data.get("is_installed", False):
            self.logger.info(f"⚡ Dependency change detected for '{plugin_id}'. Auto-installing...")
            success, msg = self._perform_pip_install_sync(plugin_id, plugin_data)

            if success:
                with open(hash_file_path, "w") as f:
                    f.write(current_hash)
                with open(os.path.join(path, ".installed"), "w") as f:
                    f.write("installed")
                self.loaded_plugins[plugin_id]["is_installed"] = True
            else:
                raise Exception(f"Auto-install failed: {msg}")

    def _perform_pip_install_sync(self, plugin_id, plugin_data):
        component_path = plugin_data["path"]
        venv_path = os.path.join(component_path, ".venv")
        requirements_path = os.path.join(component_path, "requirements.txt")

        try:
            python_executable = sys.executable
            pip_executable = os.path.join(
                venv_path, "Scripts" if sys.platform == "win32" else "bin", "pip"
            )

            if os.path.exists(venv_path) and not os.path.exists(pip_executable):
                self.logger.warning(f"Incompatible venv detected for '{plugin_id}' (Cross-Platform). Recreating...")
                shutil.rmtree(venv_path)

            if not os.path.exists(venv_path):
                self.logger.info(f"Creating venv for '{plugin_id}'...")
                subprocess.run(
                    [python_executable, "-m", "venv", venv_path],
                    check=True, capture_output=True
                )

            self.logger.info(f"Running pip install for '{plugin_id}'...")
            result = subprocess.run(
                [pip_executable, "install", "-r", requirements_path, "--no-cache-dir", "--disable-pip-version-check"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )

            if result.returncode != 0:
                return False, result.stderr
            return True, "Success"
        except Exception as e:
            return False, str(e)

    def get_manifest(self, plugin_id):
        return self.loaded_plugins.get(plugin_id, {}).get("manifest")

    def _load_paused_status(self):
        if os.path.exists(self.paused_status_file):
            try:
                with open(self.paused_status_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_paused_status(self):
        paused_ids = [
            pid for pid, data in self.loaded_plugins.items() if data.get("is_paused")
        ]
        try:
            with open(self.paused_status_file, "w") as f:
                json.dump(paused_ids, f, indent=4)
        except IOError as e:
            self.logger.error(
                f"Failed to save plugin paused status: {e}"
            )

    def set_plugin_paused(self, plugin_id, is_paused):
        if plugin_id in self.loaded_plugins:
            instance = self.instance_cache.get(plugin_id)
            if is_paused and instance:
                if hasattr(instance, "on_unload"):
                    instance.on_unload()
                del self.instance_cache[plugin_id]
            self.loaded_plugins[plugin_id]["is_paused"] = is_paused
            self._save_paused_status()
            return True
        return False

    def _worker_install_dependencies(self, plugin_id: str, on_complete: callable):

        try:
            if plugin_id not in self.loaded_plugins:
                raise FileNotFoundError(f"Plugin '{plugin_id}' not found in loaded_plugins.")

            plugin_data = self.loaded_plugins[plugin_id]

            success, msg = self._perform_pip_install_sync(plugin_id, plugin_data)

            if success:
                path = plugin_data["path"]
                req_path = os.path.join(path, "requirements.txt")
                if os.path.exists(req_path):
                    new_hash = self._calculate_requirements_hash(req_path)
                    with open(os.path.join(path, ".requirements_hash"), "w") as f:
                        f.write(new_hash)

                with open(os.path.join(path, ".installed"), "w") as f:
                    f.write("installed")
                self.loaded_plugins[plugin_id]["is_installed"] = True
                on_complete(plugin_id, True, "Dependencies installed successfully.")
            else:
                on_complete(plugin_id, False, f"Installation failed: {msg}")

        except Exception as e:
            self.logger.error(f"Failed to install dependencies for '{plugin_id}': {e}")
            on_complete(plugin_id, False, f"Installation failed: {e}")

    def install_component_dependencies(self, plugin_id: str, on_complete: callable):

        self.logger.info(f"Queuing dependency installation for plugin: {plugin_id}")
        install_thread = threading.Thread(
            target=self._worker_install_dependencies,
            args=(plugin_id, on_complete)
        )
        install_thread.start()

    def _worker_uninstall_dependencies(self, plugin_id: str, on_complete: callable):

        try:
            if plugin_id not in self.loaded_plugins:
                raise FileNotFoundError(f"Plugin '{plugin_id}' not found in loaded_plugins.")

            plugin_data = self.loaded_plugins[plugin_id]
            component_path = plugin_data["path"]
            venv_path = os.path.join(component_path, ".venv")
            install_marker_path = os.path.join(component_path, ".installed")
            hash_path = os.path.join(component_path, ".requirements_hash")

            if os.path.exists(install_marker_path):
                os.remove(install_marker_path)
            if os.path.exists(hash_path):
                os.remove(hash_path)
            if os.path.isdir(venv_path):
                shutil.rmtree(venv_path)
                self.logger.info(f"Removed venv directory for '{plugin_id}'.")

            self.loaded_plugins[plugin_id]["is_installed"] = False
            on_complete(plugin_id, True, "Component dependencies uninstalled successfully.")

        except Exception as e:
            self.logger.error(f"Failed to uninstall dependencies for '{plugin_id}': {e}")
            on_complete(plugin_id, False, f"Uninstallation failed: {e}")

    def uninstall_component_dependencies(self, plugin_id: str, on_complete: callable):

        self.logger.info(f"Queuing dependency uninstallation for plugin: {plugin_id}")
        uninstall_thread = threading.Thread(
            target=self._worker_uninstall_dependencies,
            args=(plugin_id, on_complete)
        )
        uninstall_thread.start()
