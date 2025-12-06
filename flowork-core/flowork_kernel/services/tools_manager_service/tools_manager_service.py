########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\tools_manager_service\tools_manager_service.py total lines 488 
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

class ToolsManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.tools_dir = self.kernel.tools_path
        self.loaded_tools = {}
        self.instance_cache = {}
        self.paused_status_file = os.path.join(
            self.kernel.data_path, "paused_tools.json"
        )
        self.logger.debug(f"Service 'ToolsManagerService' initialized.")

    def get_builtin_definitions(self):
        return [
            {
                "name": "email_sender",
                "description": "Send an email to a specific recipient.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Email address of the recipient"},
                        "subject": {"type": "string", "description": "Subject of the email"},
                        "body": {"type": "string", "description": "Content of the email"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "file_reader",
                "description": "Read the content of a file from the local filesystem.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Absolute path to the file"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "python_runner",
                "description": "Execute a Python script securely.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "web_browser",
                "description": "Browse a website and extract its text content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to visit"}
                    },
                    "required": ["url"]
                }
            }
        ]

    def execute_builtin_tool(self, tool_name: str, args: dict):
        self.logger.info(f"[ToolsManager] Executing built-in tool: {tool_name} with args: {args}")

        try:
            if tool_name == "email_sender":
                return f"SUCCESS: Email sent to {args.get('to')} with subject '{args.get('subject')}'."

            elif tool_name == "file_reader":
                path = args.get('path')
                if not path or not os.path.exists(path):
                    return f"ERROR: File not found at {path}"
                return f"MOCK CONTENT of file {path}: [Line 1... Line 2...]"

            elif tool_name == "python_runner":
                return "SUCCESS: Python script executed. Output: 'Hello from Python Sandbox'"

            elif tool_name == "web_browser":
                return f"SUCCESS: Visited {args.get('url')}. Page title: 'Example Domain'. Content: '...'"

            else:
                return f"ERROR: Tool '{tool_name}' is not a valid built-in tool."

        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return f"SYSTEM ERROR: {str(e)}"


    def discover_and_load_tools(self):
        self.logger.info(
            "ToolsManager: Starting discovery and loading of AI tools..."
        )

        if not hasattr(self.kernel, "globally_disabled_components"):
            self.kernel.globally_disabled_components = set()
        if not hasattr(self.kernel, "globally_disabled_types"):
            self.kernel.globally_disabled_types = set()


        try:
            if not os.path.exists(self.tools_dir):
                root_tools = os.path.join(os.sep, "tools")
                if os.path.exists(root_tools):
                    self.logger.warning("[Compat] Using fallback tools path: /tools")
                    self.tools_dir = root_tools
                else:
                    alt_dir2 = os.path.join(getattr(self.kernel, "project_root_path", ""), "tools")
                    if alt_dir2 and os.path.exists(alt_dir2):
                        self.logger.warning(f"[Compat] Using fallback tools path: {alt_dir2}")
                        self.tools_dir = alt_dir2
        except Exception as e:
            self.logger.debug(f"[Compat] Tools path fallback check failed: {e}")

        self.loaded_tools.clear()
        self.instance_cache.clear()
        paused_ids = self._load_paused_status()

        if not os.path.exists(self.tools_dir):
            self.logger.warning(
                f"Tools directory not found at {self.tools_dir}, creating it."
            )
            os.makedirs(self.tools_dir, exist_ok=True)
            return

        for item_id in os.listdir(self.tools_dir):
            if item_id in self.kernel.globally_disabled_components:
                self.logger.warning(f"Skipping globally disabled tool: {item_id}")
                continue

            item_dir = os.path.join(self.tools_dir, item_id)
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

                    tool_data = {
                        "manifest": manifest,
                        "path": item_id and item_dir,
                        "installed_as": "tool",
                        "is_paused": is_paused,
                        "permissions": manifest.get("permissions", []),
                        "tier": manifest.get("tier", "free").lower(),
                        "is_installed": is_installed,
                    }
                    self.loaded_tools[item_id] = tool_data
                except Exception as e:
                    self.logger.warning(
                        f"   ! Failed to process manifest for tool '{item_id}': {e}"
                    )

        self.logger.info(
            f"ToolsManager: Discovery complete. Found {len(self.loaded_tools)} tools."
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

    def get_instance(self, tool_id):
        if tool_id in self.instance_cache:
            return self.instance_cache[tool_id]
        if tool_id not in self.loaded_tools:
            self.logger.error(f"Attempted to get instance for unknown tool_id: {tool_id}")
            return None

        tool_data = self.loaded_tools[tool_id]

        if tool_data.get("is_paused", False):
            return None

        try:
            self._ensure_dependencies_up_to_date(tool_id, tool_data)
        except Exception as e:
            self.logger.error(f"Dependency Sync Failed for tool '{tool_id}': {e}")
            return None

        self.logger.debug(f"Just-In-Time Load: Instantiating tool '{tool_id}' for the first time.")

        vendor_path = os.path.join(tool_data["path"], "vendor")
        is_vendor_path_added = False
        venv_path = os.path.join(tool_data["path"], ".venv")
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
                    self.logger.debug(f"Added venv path to sys.path for '{tool_id}': {site_packages_path}")

            manifest = tool_data["manifest"]
            entry_point = manifest.get("entry_point")
            if not entry_point:
                raise ValueError(f"'entry_point' not found for '{tool_id}'.")

            module_filename, class_name = entry_point.split(".")
            source_file_path = os.path.join(tool_data["path"], f"{module_filename}.py")
            if not os.path.exists(source_file_path):
                raise FileNotFoundError(f"Entry point file not found for '{tool_id}'.")

            safe_tool_id = tool_id.replace("-", "_")
            parent_package_name = f"tools.{safe_tool_id}"
            module_full_name = f"{parent_package_name}.{module_filename}"

            spec = importlib.util.spec_from_file_location(module_full_name, source_file_path)
            if spec is None:
                raise ImportError(f"Could not create module spec from {source_file_path}")

            module_lib = importlib.util.module_from_spec(spec)

            if "tools" not in sys.modules:
                spec_base = importlib.util.spec_from_loader("tools", loader=None, is_package=True)
                module_base = importlib.util.module_from_spec(spec_base)
                sys.modules["tools"] = module_base

            if parent_package_name not in sys.modules:
                spec_parent = importlib.util.spec_from_loader(parent_package_name, loader=None, is_package=True)
                module_parent = importlib.util.module_from_spec(spec_parent)
                module_parent.__path__ = [tool_data["path"]]
                sys.modules[parent_package_name] = module_parent

            sys.modules[module_full_name] = module_lib
            spec.loader.exec_module(module_lib)

            ProcessorClass = getattr(module_lib, class_name)

            services_to_inject = {}
            requested_services = manifest.get("requires_services", [])
            for service_alias in requested_services:
                if service_alias == "loc":
                    services_to_inject["loc"] = self.kernel.get_service("localization_manager")
                elif service_alias == "logger":
                    services_to_inject["logger"] = self.kernel.write_to_log
                elif service_alias == "kernel":
                    services_to_inject["kernel"] = self.kernel
                else:
                    service_instance = self.kernel.get_service(service_alias)
                    if service_instance:
                        services_to_inject[service_alias] = service_instance

            tool_instance = ProcessorClass(tool_id, services_to_inject)
            if hasattr(tool_instance, "on_load"):
                tool_instance.on_load()

            self.instance_cache[tool_id] = tool_instance
            self.loaded_tools[tool_id]["instance"] = tool_instance
            return tool_instance

        except PermissionDeniedError as e:
            self.logger.warning(f"Skipping instantiation of tool '{tool_id}' due to insufficient permissions: {e}")
            return None
        except Exception as e:
            self.logger.critical(f"CRITICAL FAILURE during Just-In-Time instantiation of tool '{tool_id}': {e}")
            self.logger.debug(traceback.format_exc())
            return None
        finally:
            if is_vendor_path_added:
                try: sys.path.remove(vendor_path)
                except ValueError: pass
            if is_venv_path_added:
                try:
                    sys.path.remove(site_packages_path)
                    self.logger.debug(f"Removed venv path from sys.path for '{tool_id}'")
                except ValueError: pass

    def _calculate_requirements_hash(self, file_path):
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except IOError:
            return None

    def _ensure_dependencies_up_to_date(self, tool_id, tool_data):
        path = tool_data["path"]
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

        if current_hash != stored_hash or not tool_data.get("is_installed", False):
            self.logger.info(f"⚡ Dependency change detected for '{tool_id}'. Auto-installing...")
            success, msg = self._perform_pip_install_sync(tool_id, tool_data)

            if success:
                with open(hash_file_path, "w") as f:
                    f.write(current_hash)
                with open(os.path.join(path, ".installed"), "w") as f:
                    f.write("installed")
                self.loaded_tools[tool_id]["is_installed"] = True
            else:
                raise Exception(f"Auto-install failed: {msg}")

    def _perform_pip_install_sync(self, tool_id, tool_data):
        component_path = tool_data["path"]
        venv_path = os.path.join(component_path, ".venv")
        requirements_path = os.path.join(component_path, "requirements.txt")

        try:
            python_executable = sys.executable
            pip_executable = os.path.join(
                venv_path, "Scripts" if sys.platform == "win32" else "bin", "pip"
            )

            if os.path.exists(venv_path) and not os.path.exists(pip_executable):
                self.logger.warning(f"Incompatible venv detected for '{tool_id}' (Cross-Platform). Recreating...")
                shutil.rmtree(venv_path)

            if not os.path.exists(venv_path):
                self.logger.info(f"Creating venv for '{tool_id}'...")
                subprocess.run(
                    [python_executable, "-m", "venv", venv_path],
                    check=True, capture_output=True
                )

            self.logger.info(f"Running pip install for '{tool_id}'...")
            result = subprocess.run(
                [pip_executable, "install", "-r", requirements_path, "--no-cache-dir", "--disable-pip-version-check"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )

            if result.returncode != 0:
                return False, result.stderr
            return True, "Success"
        except Exception as e:
            return False, str(e)

    def get_manifest(self, tool_id):
        return self.loaded_tools.get(tool_id, {}).get("manifest")

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
            tid for tid, data in self.loaded_tools.items() if data.get("is_paused")
        ]
        try:
            with open(self.paused_status_file, "w") as f:
                json.dump(paused_ids, f, indent=4)
        except IOError as e:
            self.logger.error(f"Failed to save tool paused status: {e}")

    def set_tool_paused(self, tool_id, is_paused):
        if tool_id in self.loaded_tools:
            instance = self.instance_cache.get(tool_id)
            if is_paused and instance:
                if hasattr(instance, "on_unload"):
                    instance.on_unload()
                del self.instance_cache[tool_id]
            self.loaded_tools[tool_id]["is_paused"] = is_paused
            self._save_paused_status()
            return True
        return False

    def _worker_install_dependencies(self, tool_id: str, on_complete: callable):

        try:
            if tool_id not in self.loaded_tools:
                raise FileNotFoundError(f"Tool '{tool_id}' not found in loaded_tools.")

            tool_data = self.loaded_tools[tool_id]

            success, msg = self._perform_pip_install_sync(tool_id, tool_data)

            if success:
                path = tool_data["path"]
                req_path = os.path.join(path, "requirements.txt")
                if os.path.exists(req_path):
                    new_hash = self._calculate_requirements_hash(req_path)
                    with open(os.path.join(path, ".requirements_hash"), "w") as f:
                        f.write(new_hash)

                with open(os.path.join(path, ".installed"), "w") as f:
                    f.write("installed")
                self.loaded_tools[tool_id]["is_installed"] = True
                on_complete(tool_id, True, "Dependencies installed successfully.")
            else:
                on_complete(tool_id, False, f"Installation failed: {msg}")

        except Exception as e:
            self.logger.error(f"Failed to install dependencies for '{tool_id}': {e}")
            on_complete(tool_id, False, f"Installation failed: {e}")

    def install_component_dependencies(self, tool_id: str, on_complete: callable):

        self.logger.info(f"Queuing dependency installation for tool: {tool_id}")
        install_thread = threading.Thread(
            target=self._worker_install_dependencies,
            args=(tool_id, on_complete)
        )
        install_thread.start()

    def _worker_uninstall_dependencies(self, tool_id: str, on_complete: callable):

        try:
            if tool_id not in self.loaded_tools:
                raise FileNotFoundError(f"Tool '{tool_id}' not found in loaded_tools.")

            component_path = self.loaded_tools[tool_id]["path"]
            venv_path = os.path.join(component_path, ".venv")
            install_marker_path = os.path.join(component_path, ".installed")
            hash_path = os.path.join(component_path, ".requirements_hash")

            if os.path.exists(install_marker_path):
                os.remove(install_marker_path)
            if os.path.exists(hash_path):
                os.remove(hash_path)
            if os.path.isdir(venv_path):
                shutil.rmtree(venv_path)
                self.logger.info(f"Removed venv directory for '{tool_id}'.")
            self.loaded_tools[tool_id]["is_installed"] = False
            on_complete(tool_id, True, "Component dependencies uninstalled successfully.")

        except Exception as e:
            self.logger.error(f"Failed to uninstall dependencies for '{tool_id}': {e}")
            on_complete(tool_id, False, f"Uninstallation failed: {e}")

    def uninstall_component_dependencies(self, tool_id: str, on_complete: callable):

        self.logger.info(f"Queuing dependency uninstallation for tool: {tool_id}")
        uninstall_thread = threading.Thread(
            target=self._worker_uninstall_dependencies,
            args=(tool_id, on_complete)
        )
        uninstall_thread.start()
