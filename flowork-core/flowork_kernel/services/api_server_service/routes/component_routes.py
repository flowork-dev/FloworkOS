########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes.py total lines 632 
########################################################################

from .base_api_route import BaseApiRoute
import os
import json
import mimetypes
import zipfile
import io
import base64
import shutil
from aiohttp import web

class ComponentRoutes(BaseApiRoute):

    def register_routes(self):
        base_routes = [
            "GET /api/v1/{resource_type}",
            "POST /api/v1/{resource_type}",           # <-- NEW: Handle Create (Dataset)
            "GET /api/v1/{resource_type}/{item_id}",
            "POST /api/v1/{resource_type}/install",
            "PATCH /api/v1/{resource_type}/{item_id}/state",
            "DELETE /api/v1/{resource_type}/{item_id}",
        ]
        routes = {}

        component_types = [
            "modules",
            "plugins",
            "tools",
            "widgets",
            "triggers",
            "ai_providers",
            "datasets", # <-- Penting!
            "models"    # <-- Penting!
        ]

        for route_pattern in base_routes:
            for comp_type in component_types:
                concrete_route = route_pattern.replace("{resource_type}", comp_type)
                method, pattern = concrete_route.split(" ", 1)

                if method == "POST" and pattern.endswith("/install"):
                    routes[concrete_route] = self.handle_install_components
                elif method == "POST" and not pattern.endswith("/package") and not pattern.endswith("/install-package"):
                    routes[concrete_route] = self.handle_create_component
                elif "state" in pattern:
                    routes[concrete_route] = self.handle_patch_component_state
                elif method == "DELETE":
                    routes[concrete_route] = self.handle_delete_components
                else:
                    routes[concrete_route] = self.handle_get_components

        routes["GET /api/v1/ai_providers/services"] = (
            self.handle_get_ai_provider_services
        )
        routes["GET /api/v1/components/{comp_type}/{item_id}/icon"] = (
            self.handle_get_component_icon
        )

        routes["GET /api/v1/widgets/{widget_id}/assets/{filename:.*}"] = self.handle_get_widget_asset

        routes["POST /api/v1/components/package"] = self.handle_package_component

        routes["POST /api/v1/components/install-package"] = self.handle_install_package

        routes["POST /api/v1/components/run"] = self.handle_run_component

        routes["POST /api/v1/components/custom/create"] = self.handle_save_custom_component

        return routes

    async def handle_get_widget_asset(self, request):
        """
        [ADDED BY FLOWORK DEV]
        Serve static files (HTML, JS, CSS, Images) from a specific widget's directory.
        This enables the GUI to render the widget's UI dynamically.
        """
        widget_id = request.match_info.get("widget_id")
        filename = request.match_info.get("filename")

        if not widget_id or not filename:
            return self._json_response({"error": "Missing widget_id or filename"}, status=400)

        manager, error = self._get_manager_for_type("widgets")
        if error:
            return self._json_response({"error": error}, status=503)

        items = self._get_items_from_manager(manager, "widgets")

        if widget_id not in items:
             return self._json_response({"error": f"Widget '{widget_id}' not found or not loaded."}, status=404)

        widget_data = items[widget_id]
        widget_path = widget_data.get("path") or widget_data.get("full_path")

        if not widget_path or not os.path.isdir(widget_path):
             return self._json_response({"error": "Widget directory path is invalid on server."}, status=500)

        target_path = os.path.join(widget_path, filename)

        try:
            requested_abspath = os.path.abspath(target_path)
            widget_abspath = os.path.abspath(widget_path)
            if not requested_abspath.startswith(widget_abspath):
                self.logger(f"Security Alert: Path traversal attempt on widget {widget_id}: {filename}", "WARNING")
                return self._json_response({"error": "Access denied: File outside widget directory."}, status=403)
        except Exception:
             return self._json_response({"error": "Invalid path construction."}, status=400)

        if not os.path.exists(requested_abspath) or not os.path.isfile(requested_abspath):
             return self._json_response({"error": f"Asset '{filename}' not found in widget '{widget_id}'."}, status=404)

        return await self._serve_image_file(request, requested_abspath)

    async def handle_run_component(self, request):
        """
        [ADDED BY FLOWORK DEV]
        Endpoint untuk menjalankan komponen secara langsung (Standalone Execution).
        Menerima payload: { node_id: "...", input: {...} }
        """
        try:
            body = await request.json()
            executor = self.service_instance.kernel.get_service("workflow_executor_service")

            if not executor:
                return self._json_response({"error": "Workflow Executor Service not available."}, status=503)

            await executor.execute_standalone_node(body)

            return self._json_response({
                "status": "success",
                "message": "Execution started.",
                "details": f"Node {body.get('node_id')} queued for execution."
            })
        except Exception as e:
            self.logger(f"Error executing component: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_save_custom_component(self, request):
        """
        [ADDED BY FLOWORK DEV]
        Saves a custom component (Module, Trigger, etc) from Component Forge to disk.
        Triggers Module Manager to reload/install dependencies.
        """
        try:
            body = await request.json()
            comp_id = body.get("id")
            comp_type = body.get("type", "module")
            code_content = body.get("code", "")
            manifest_content = body.get("manifest", {})
            requirements_content = body.get("requirements", "")

            if not comp_id or not code_content:
                return self._json_response({"error": "Missing 'id' or 'code'."}, status=400)

            type_map = {
                "module": "modules",
                "trigger": "triggers",
                "tool": "tools",
                "plugin": "plugins",
                "scanner": "scanners"
            }
            folder_name = type_map.get(comp_type, "modules")

            root_path = os.path.abspath(os.path.join(self.kernel.project_root_path, ".."))
            target_parent_dir = os.path.join(root_path, folder_name)

            if not os.path.exists(target_parent_dir):
                alt_root = os.path.join(self.kernel.project_root_path, "flowork_kernel", folder_name)
                if os.path.exists(alt_root):
                    target_parent_dir = alt_root
                else:
                    os.makedirs(target_parent_dir, exist_ok=True) # Create if completely missing

            comp_dir = os.path.join(target_parent_dir, comp_id)
            os.makedirs(comp_dir, exist_ok=True)

            entry_point = manifest_content.get("entry_point", "processor.py")
            with open(os.path.join(comp_dir, entry_point), "w", encoding="utf-8") as f:
                f.write(code_content)

            with open(os.path.join(comp_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest_content, f, indent=4)

            if requirements_content:
                with open(os.path.join(comp_dir, "requirements.txt"), "w", encoding="utf-8") as f:
                    f.write(requirements_content)

            module_manager = self.service_instance.kernel.get_service("module_manager_service")
            if module_manager:
                import threading
                threading.Thread(target=module_manager.install_component_dependencies, args=(comp_id,)).start()

            self.logger(f"Custom component '{comp_id}' saved to {comp_dir}", "SUCCESS")

            return self._json_response({
                "status": "success",
                "message": f"Component {comp_id} saved. Installing dependencies in background...",
                "path": comp_dir
            })

        except Exception as e:
            self.logger(f"Error saving custom component: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_create_component(self, request):
        resource_type = request.match_info.get("resource_type")

        if resource_type == "datasets":
            manager, error = self._get_manager_for_type(resource_type)
            if error: return self._json_response({"error": error}, status=500)

            try:
                body = await request.json()
                name = body.get("name")
                if not name: return self._json_response({"error": "Name is required"}, status=400)

                if hasattr(manager, "create_dataset"):
                    success = manager.create_dataset(name)
                    if success:
                        return self._json_response({"status": "success", "message": f"Dataset '{name}' created."})
                    return self._json_response({"error": "Dataset already exists or creation failed."}, status=409)
                else:
                    return self._json_response({"error": "Manager does not support creation."}, status=501)
            except Exception as e:
                return self._json_response({"error": str(e)}, status=500)

        return self._json_response({"error": f"Create via API not supported for {resource_type}."}, status=501)

    async def handle_package_component(self, request):
        """
        (English Hardcode) Locates the component folder, reads the FRESH manifest for description,
        and zips the directory into a Base64 string.
        Excludes: .venv, __pycache__, .git, etc.
        """
        try:
            body = await request.json()
            comp_type_singular = body.get("type") # e.g., 'module'
            comp_id = body.get("id") # e.g., 'my_module_id'

            if not comp_type_singular or not comp_id:
                return self._json_response({"error": "Missing 'type' or 'id' in request body."}, status=400)

            type_map = {
                "module": "modules",
                "plugin": "plugins",
                "tool": "tools",
                "trigger": "triggers",
                "widget": "widgets"
            }

            resource_type = type_map.get(comp_type_singular, comp_type_singular + "s")
            manager, error = self._get_manager_for_type(resource_type)

            if error:
                return self._json_response({"error": error}, status=404)

            items = self._get_items_from_manager(manager, resource_type)

            item_data = items.get(comp_id)
            if not item_data:
                return self._json_response({"error": f"Component '{comp_id}' not found in {resource_type}."}, status=404)

            folder_path = item_data.get("path") or item_data.get("full_path")

            manifest_path = os.path.join(folder_path, "manifest.json")
            manifest = {}
            description = ""
            name = comp_id

            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                        description = manifest.get("description") or manifest.get("desc", "")
                        name = manifest.get("name", comp_id)
                except Exception as json_err:
                    self.logger(f"Error reading fresh manifest: {json_err}", "WARNING")
                    manifest = item_data.get("manifest", {})
                    description = manifest.get("description", "")

            if not folder_path or not os.path.isdir(folder_path):
                return self._json_response({"error": "Component folder not found on disk."}, status=500)

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(folder_path):
                    dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", ".venv", "venv", "node_modules", ".idea", ".vscode"]]
                    for file in files:
                        if file.endswith(".pyc") or file == ".DS_Store" or file.endswith(".log"):
                            continue

                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)
                        zip_file.write(file_path, arcname)

            buffer.seek(0)
            zip_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return self._json_response({
                "id": comp_id,
                "name": name,
                "description": description,
                "zip_data": zip_base64,
                "manifest": manifest
            })

        except Exception as e:
            self.logger(f"Error packaging component: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_install_package(self, request):
        """
        (English Hardcode) Receives a Base64 ZIP payload from Marketplace and installs it.
        Payload: { "id": "module_id", "type": "module", "zip_data": "BASE64..." }
        """
        try:
            body = await request.json()
            comp_id = body.get("id")
            comp_type = body.get("type", "module")
            zip_b64 = body.get("zip_data")

            if not comp_id or not zip_b64:
                return self._json_response({"error": "Missing 'id' or 'zip_data' in payload."}, status=400)

            try:
                zip_bytes = base64.b64decode(zip_b64)
            except Exception as e:
                return self._json_response({"error": f"Invalid Base64 data: {str(e)}"}, status=400)

            type_map = {
                "module": "modules",
                "plugin": "plugins",
                "tool": "tools",
                "trigger": "triggers",
                "widget": "widgets"
            }
            folder_name = type_map.get(comp_type, "modules")

            target_parent_dir = os.path.join(self.kernel.project_root_path, "..", folder_name)
            target_parent_dir = os.path.abspath(target_parent_dir)
            target_dir = os.path.join(target_parent_dir, comp_id)

            if os.path.exists(target_dir):
                self.logger(f"Installing: Removing existing folder at {target_dir}", "INFO")
                try:
                    shutil.rmtree(target_dir)
                except Exception as del_err:
                     self.logger(f"Warning: Failed to delete old folder: {del_err}. Attempting overwrite.", "WARNING")

            os.makedirs(target_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                    zf.extractall(target_dir)
            except zipfile.BadZipFile:
                 if os.path.exists(target_dir):
                     shutil.rmtree(target_dir)
                 return self._json_response({"error": "Corrupted ZIP file."}, status=400)

            if not os.path.exists(os.path.join(target_dir, "manifest.json")):
                self.logger(f"Installation failed: No manifest.json found in {target_dir}", "ERROR")
                shutil.rmtree(target_dir)
                return self._json_response({"error": "Invalid package structure: manifest.json not found."}, status=400)

            marker_path = os.path.join(target_dir, ".installed")
            with open(marker_path, 'w') as f:
                f.write("installed_via_marketplace")

            self.logger(f"Successfully installed component '{comp_id}' to {target_dir}", "SUCCESS")

            return self._json_response({
                "status": "success",
                "message": f"Successfully installed {comp_id} to {folder_name}.",
                "path": target_dir
            })

        except Exception as e:
            self.logger(f"Install Error: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def _serve_image_file(self, request, image_path):
        try:
            import aiofiles
            async with aiofiles.open(image_path, "rb") as f:
                image_data = await f.read()
            content_type, _ = mimetypes.guess_type(image_path)
            if not content_type:
                content_type = "application/octet-stream"
            return web.Response(body=image_data, content_type=content_type)
        except Exception as e:
            self.logger(
                f"Error serving icon file '{os.path.basename(image_path)}': {e}",
                "ERROR",
            )
            return self._json_response(
                {"error": "Internal Server Error while serving icon."}, status=500
            )

    async def handle_get_component_icon(self, request):
        comp_type = request.match_info.get("comp_type")
        item_id = request.match_info.get("item_id")

        resource_type = comp_type.rstrip("s") + "s"
        manager, error = self._get_manager_for_type(resource_type)

        true_root_path = os.path.abspath(os.path.join(self.kernel.project_root_path, ".."))
        assets_path = os.path.join(true_root_path, "assets")

        default_icon_path = os.path.join(assets_path, "default_module.png")
        if comp_type.startswith("module"):
            default_icon_path = os.path.join(assets_path, "default_module.png")
        elif comp_type.startswith("plugin"):
            default_icon_path = os.path.join(assets_path, "default_plugin.png")
        elif comp_type.startswith("tool"):
            default_icon_path = os.path.join(assets_path, "default_tool.png")
        elif comp_type.startswith("trigger"):
            default_icon_path = os.path.join(assets_path, "default_trigger.png")

        if error:
            return await self._serve_image_file(request, default_icon_path)

        items = self._get_items_from_manager(manager, resource_type)

        component_data = items.get(item_id)
        if not component_data:
            return await self._serve_image_file(request, default_icon_path)

        manifest = component_data.get("manifest", {})
        icon_filename = manifest.get("icon_file")
        component_path = component_data.get("path") or component_data.get("full_path")

        if icon_filename and component_path:
            icon_path = os.path.join(component_path, icon_filename)
            if os.path.isfile(icon_path):
                return await self._serve_image_file(request, icon_path)

        return await self._serve_image_file(request, default_icon_path)

    async def handle_get_ai_provider_services(self, request):
        manager, error = self._get_manager_for_type("ai_providers")
        if error:
            return self._json_response({"error": error}, status=503)
        providers_info = manager.get_loaded_providers_info()
        return self._json_response(providers_info)

    def _get_manager_for_type(self, resource_type):
        manager_map = {
            "modules": "module_manager_service",
            "plugins": "plugin_manager_service",
            "tools": "tools_manager_service",
            "widgets": "widget_manager_service",
            "triggers": "trigger_manager_service",
            "ai_providers": "ai_provider_manager_service",
            "datasets": "dataset_manager_service",       # <-- NEW
            "models": "ai_provider_manager_service"      # <-- NEW (Model dikelola AI Manager)
        }
        manager_name = manager_map.get(resource_type)
        if not manager_name:
            return None, f"Resource type '{resource_type}' is invalid."
        manager = self.service_instance.kernel.get_service(manager_name)
        if not manager:
            return (
                None,
                f"{manager_name} service is unavailable, possibly due to license restrictions.",
            )
        return manager, None

    def _get_items_from_manager(self, manager, resource_type):
        if resource_type == "models":
            return getattr(manager, "local_models", {})

        elif resource_type == "datasets":
            if hasattr(manager, "list_datasets"):
                try:
                    ds_list = manager.list_datasets()
                    return {d['name']: {"manifest": {"name": d['name']}, "path": ""} for d in ds_list}
                except:
                    return {}
            return {}

        items_attr_map = {
            "module_manager_service": "loaded_modules",
            "plugin_manager_service": "loaded_plugins",
            "tools_manager_service": "loaded_tools",
            "widget_manager_service": "loaded_widgets",
            "trigger_manager_service": "loaded_triggers",
            "ai_provider_manager_service": "loaded_providers",
        }
        items_attr_name = items_attr_map.get(manager.service_id)
        return getattr(manager, items_attr_name, {}) if items_attr_name else {}

    async def handle_get_components(self, request):
        resource_type = (
            request.match_info.get("resource_type") or request.path.split("/")[3]
        )
        item_id = request.match_info.get("item_id", None)
        manager, error = self._get_manager_for_type(resource_type)
        if error:
            return self._json_response([], status=200)

        core_files = await self.service_instance._load_protected_component_ids()

        items = self._get_items_from_manager(manager, resource_type)

        if item_id:
            if item_id in items:
                item_data = items[item_id]
                manifest = item_data.get("manifest", {})
                response_item = {
                    "id": item_id,
                    "name": manifest.get("name", item_id),
                    "version": manifest.get("version", "N/A"),
                    "is_paused": item_data.get("is_paused", False),
                    "description": manifest.get("description", ""),
                    "manifest": manifest,
                    "path": item_data.get("path") or item_data.get("full_path"),
                }
                if resource_type == "models":
                    response_item["type"] = item_data.get("type")
                    response_item["category"] = item_data.get("category")

                return self._json_response(response_item)
            else:
                return self._json_response(
                    {"error": f"Component '{item_id}' not found in '{resource_type}'."},
                    status=404,
                )
        else:
            response_data = []
            for item_id_loop, item_data in items.items():
                manifest = item_data.get("manifest", {})
                comp_obj = {
                    "id": item_id_loop,
                    "name": manifest.get("name", item_id_loop),
                    "version": manifest.get("version", "N/A"),
                    "is_paused": item_data.get("is_paused", False),
                    "description": manifest.get("description", ""),
                    "is_core": item_id_loop in core_files,
                    "tier": manifest.get("tier", "free"),
                    "manifest": manifest,
                }
                if resource_type == "models":
                    comp_obj["type"] = item_data.get("type")
                    comp_obj["category"] = item_data.get("category")
                    if "name" in item_data: comp_obj["name"] = item_data["name"]

                response_data.append(comp_obj)

            query_params = request.query
            try:
                limit = int(query_params.get("limit", 50))
                offset = int(query_params.get("offset", 0))
            except (ValueError, IndexError):
                limit = 50
                offset = 0
            sorted_data = sorted(response_data, key=lambda x: x["name"])
            paginated_data = sorted_data[offset : offset + limit]
            return self._json_response(paginated_data)

    async def handle_install_components(self, request):
        return self._json_response(
            {"error": "Install via API is not implemented yet."}, status=501
        )

    async def handle_delete_components(self, request):
        resource_type = request.match_info.get("resource_type")
        item_id = request.match_info.get("item_id")

        if resource_type == "datasets":
            manager, error = self._get_manager_for_type(resource_type)
            if error: return self._json_response({"error": error}, status=500)
            if hasattr(manager, "delete_dataset"):
                success = manager.delete_dataset(item_id)
                if success:
                     return self._json_response({"status": "success", "message": f"Dataset {item_id} deleted."})
                return self._json_response({"error": "Dataset not found or delete failed"}, status=404)

        return self._json_response(
            {"error": "Delete via API is not implemented yet for this resource."}, status=501
        )

    async def handle_patch_component_state(self, request):
        resource_type = (
            request.match_info.get("resource_type") or request.path.split("/")[3]
        )
        item_id = request.match_info.get("item_id")
        core_files = await self.service_instance._load_protected_component_ids()
        if item_id in core_files:
            error_msg = self.service_instance.loc.get(
                "api_core_component_disable_error",
                fallback="Core components cannot be disabled.",
            )
            return self._json_response({"error": error_msg}, status=403)
        body = await request.json()
        if "paused" not in body or not isinstance(body["paused"], bool):
            return self._json_response(
                {
                    "error": "Request body must contain a boolean 'paused' key."},
                status=400,
            )
        is_paused = body["paused"]
        manager, error = self._get_manager_for_type(resource_type)
        if error:
            return self._json_response({"error": error}, status=503)
        pause_method_name = f"set_{resource_type.rstrip('s')}_paused"
        pause_method = getattr(manager, pause_method_name, None)
        if not pause_method:
            return self._json_response(
                {
                    "error": f"State management method not found on {type(manager).__name__} for '{resource_type}'."
                },
                status=500,
            )
        success = pause_method(item_id, is_paused)
        if success:
            action = "paused" if is_paused else "resumed"
            return self._json_response(
                {
                    "status": "success",
                    "message": f"{resource_type.capitalize()[:-1]} '{item_id}' has been {action}.",
                }
            )
        else:
            return self._json_response(
                {"error": f"{resource_type.capitalize()[:-1]} '{item_id}' not found."},
                status=404,
            )
