########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes.py total lines 386 
########################################################################

from .base_api_route import BaseApiRoute
import os
import json
import mimetypes
import zipfile
import io
import base64
import shutil
import asyncio
from aiohttp import web
import threading

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

        routes["GET /api/v1/components/{comp_type}/{item_id}/assets/{filename:.*}"] = self.handle_get_component_asset

        routes["GET /api/v1/widgets/{widget_id}/assets/{filename:.*}"] = self.handle_get_widget_asset

        routes["POST /api/v1/components/package"] = self.handle_package_component

        routes["POST /api/v1/components/install-package"] = self.handle_install_package

        routes["POST /api/v1/components/run"] = self.handle_run_component

        routes["POST /api/v1/components/custom/create"] = self.handle_save_custom_component

        routes["POST /api/v1/apps/execute/{app_id}/{action}"] = self.handle_app_execute_action

        return routes

    async def handle_app_execute_action(self, request):
        """
        [MATA-MATA FIX] Routes direct GUI calls to Flat App logic.
        Ensures apps like 'File Commander' can browse directories without 403.
        """
        app_id = request.match_info.get("app_id")
        action = request.match_info.get("action")

        try:
            body = await request.json()
        except:
            body = {}

        app_service = self.service_instance.kernel.get_service("app_service")
        instance = app_service.get_instance("apps", app_id)

        if not instance:
            return web.json_response({"error": f"App '{app_id}' logic failed to load."}, status=404)

        method_name = f"action_{action}"
        if hasattr(instance, method_name):
            method = getattr(instance, method_name)
            if asyncio.iscoroutinefunction(method):
                result = await method(body)
            else:
                result = method(body)
            return web.json_response(result)
        elif hasattr(instance, "handle_ui_action"):
            result = await instance.handle_ui_action(action, body)
            return web.json_response(result)

        return web.json_response({"error": f"Action '{action}' unimplemented in '{app_id}' backend."}, status=501)

    async def handle_get_component_asset(self, request):
        """
        [MATA-MATA FIX] Serves static assets from flat folder structure.
        """
        comp_type = request.match_info.get("comp_type")
        item_id = request.match_info.get("item_id")
        filename = request.match_info.get("filename")

        app_service = self.service_instance.kernel.get_service("app_service")
        if not app_service:
            return web.json_response({"error": "AppService unavailable"}, status=503)

        app_info = app_service.registry["apps"]["data"].get(item_id) or \
                   app_service.registry.get(comp_type, {}).get("data", {}).get(item_id)

        if not app_info:
            return web.json_response({"error": f"Component {item_id} not found"}, status=404)

        base_path = app_info.get("path")
        target_file = os.path.join(base_path, filename)

        if not os.path.exists(target_file):
             target_file = os.path.join(base_path, "public", filename)
             if not os.path.exists(target_file):
                 return web.json_response({"error": "Asset gaib"}, status=404)

        return web.FileResponse(target_file, headers={'Access-Control-Allow-Origin': '*'})

    async def handle_get_widget_asset(self, request):
        """
        Serve static files from a specific widget's directory.
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
             return self._json_response({"error": f"Widget '{widget_id}' not found."}, status=404)

        widget_data = items[widget_id]
        widget_path = widget_data.get("path") or widget_data.get("full_path")

        target_path = os.path.join(widget_path, filename)

        if not os.path.exists(target_path) or not os.path.isfile(target_path):
             return self._json_response({"error": f"Asset '{filename}' not found."}, status=404)

        return await self._serve_image_file(request, target_path)

    async def handle_run_component(self, request):
        """
        Endpoint untuk menjalankan komponen secara langsung (Standalone Execution).
        """
        try:
            body = await request.json()
            executor = self.service_instance.kernel.get_service("workflow_executor_service")

            if not executor:
                return self._json_response({"error": "Workflow Executor Service unavailable."}, status=503)

            await executor.execute_standalone_node(body)

            return self._json_response({
                "status": "success",
                "message": "Execution started."
            })
        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def handle_save_custom_component(self, request):
        """
        Saves a custom component from Component Forge to disk.
        """
        try:
            body = await request.json()
            comp_id = body.get("id")
            code_content = body.get("code", "")
            manifest_content = body.get("manifest", {})

            if not comp_id or not code_content:
                return self._json_response({"error": "Missing 'id' or 'code'."}, status=400)

            root_path = os.path.abspath(os.path.join(self.kernel.project_root_path, "..", "app"))
            comp_dir = os.path.join(root_path, comp_id)
            os.makedirs(comp_dir, exist_ok=True)

            entry_point = manifest_content.get("entry_point", "backend/node.py")
            entry_path = os.path.join(comp_dir, entry_point)
            os.makedirs(os.path.dirname(entry_path), exist_ok=True)

            with open(entry_path, "w", encoding="utf-8") as f:
                f.write(code_content)

            with open(os.path.join(comp_dir, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest_content, f, indent=4)

            app_service = self.service_instance.kernel.get_service("app_service")
            if app_service:
                threading.Thread(target=app_service.sync, args=("apps",)).start()

            return self._json_response({"status": "success", "message": f"Component {comp_id} saved."})

        except Exception as e:
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
                    if manager.create_dataset(name):
                        return self._json_response({"status": "success", "message": f"Dataset '{name}' created."})
                    return self._json_response({"error": "Creation failed."}, status=409)

                dataset_app = self._get_app_instance_by_id("dataset_manager")
                if dataset_app and hasattr(dataset_app, "create_dataset"):
                     if dataset_app.create_dataset(name):
                         return self._json_response({"status": "success", "message": f"Dataset '{name}' created via App."})

            except Exception as e:
                return self._json_response({"error": str(e)}, status=500)

        return self._json_response({"error": f"Create via API not supported for {resource_type}."}, status=501)

    def _get_app_instance_by_id(self, app_id: str):
        app_service = self.service_instance.kernel.get_service("app_service")
        if app_service:
            return app_service.get_instance("apps", app_id)
        return None

    async def handle_package_component(self, request):
        try:
            body = await request.json()
            comp_id = body.get("id")
            if not comp_id:
                return self._json_response({"error": "Missing 'id'."}, status=400)

            app_service = self.service_instance.kernel.get_service("app_service")
            item_data = app_service.registry["apps"]["data"].get(comp_id)

            if not item_data:
                return self._json_response({"error": f"Component '{comp_id}' not found."}, status=404)

            folder_path = item_data.get("path")
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(folder_path):
                    dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", ".venv"]]
                    for file in files:
                        file_path = os.path.join(root, file)
                        zip_file.write(file_path, os.path.relpath(file_path, folder_path))

            return self._json_response({"id": comp_id, "zip_data": base64.b64encode(buffer.getvalue()).decode('utf-8')})

        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def handle_install_package(self, request):
        try:
            body = await request.json()
            comp_id = body.get("id")
            zip_b64 = body.get("zip_data")

            if not comp_id or not zip_b64:
                return self._json_response({"error": "Missing 'id' or 'zip_data'."}, status=400)

            target_dir = os.path.join(self.kernel.project_root_path, "..", "app", comp_id)
            os.makedirs(target_dir, exist_ok=True)

            zip_bytes = base64.b64decode(zip_b64)
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                zf.extractall(target_dir)

            return self._json_response({"id": comp_id, "status": "success"})

        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)

    async def _serve_image_file(self, request, image_path):
        try:
            content_type, _ = mimetypes.guess_type(image_path)
            return web.FileResponse(image_path, headers={'Content-Type': content_type or "application/octet-stream"})
        except:
            return self._json_response({"error": "Internal Error serving asset"}, status=500)

    async def handle_get_component_icon(self, request):
        comp_type = request.match_info.get("comp_type")
        item_id = request.match_info.get("item_id")

        app_service = self.service_instance.kernel.get_service("app_service")
        app_info = app_service.registry["apps"]["data"].get(item_id) or \
                   app_service.registry.get(comp_type, {}).get("data", {}).get(item_id)

        if app_info:
            icon_filename = app_info["manifest"].get("icon_file", "icon.svg")
            icon_path = os.path.join(app_info["path"], icon_filename)
            if os.path.exists(icon_path):
                return await self._serve_image_file(request, icon_path)

        return await self._serve_image_file(request, "/app/assets/default_module.png")

    async def handle_get_ai_provider_services(self, request):
        manager, error = self._get_manager_for_type("ai_providers")
        if error: return self._json_response({"error": error}, status=503)
        return self._json_response(manager.get_loaded_providers_info())

    def _get_manager_for_type(self, resource_type):
        """[MATA-MATA FIX] Redirecting all app managers to unified AppService."""
        unified_types = ["modules", "plugins", "tools", "widgets", "triggers", "datasets"] # [GEMINI ADDED] datasets
        if resource_type in unified_types:
            return self.service_instance.kernel.get_service("app_service"), None

        manager_map = {
            "ai_providers": "ai_provider_manager_service",
            "models": "ai_provider_manager_service"
        }
        manager = self.service_instance.kernel.get_service(manager_map.get(resource_type))
        return manager, None if manager else (None, "Service unavailable")

    def _get_items_from_manager(self, manager, resource_type):
        """
        [English Note] Rule 2: Retrieving data from either the AppService registry or legacy services.
        """
        if getattr(manager, 'service_id', '') == "app_service":
            if resource_type == "datasets":
                 return {k: v for k, v in manager.registry["apps"]["data"].items() if v["manifest"].get("category") == "datasets"}

            return getattr(manager, f"loaded_{resource_type}", {})

        if hasattr(manager, "loaded_providers") and resource_type == "ai_providers":
             return manager.loaded_providers

        return {}

    async def handle_get_components(self, request):
        resource_type = request.match_info.get("resource_type") or request.path.split("/")[3]
        item_id = request.match_info.get("item_id")
        manager, error = self._get_manager_for_type(resource_type)
        if error: return self._json_response([], status=200)

        items = self._get_items_from_manager(manager, resource_type)

        if item_id:
            if item_id in items:
                item_data = items[item_id]
                return self._json_response({"id": item_id, "name": item_data["manifest"].get("name", item_id), "manifest": item_data["manifest"]})
            return self._json_response({"error": "Not found"}, status=404)

        response_data = []
        for i_id, data in items.items():
            response_data.append({"id": i_id, "name": data["manifest"].get("name", i_id), "icon_url": data.get("icon_url"), "gui_url": data.get("gui_url"), "manifest": data["manifest"]})
        return self._json_response(response_data)

    async def handle_install_components(self, r): return self._json_response({"error": "501"}, status=501)
    async def handle_delete_components(self, r): return self._json_response({"error": "501"}, status=501)
    async def handle_patch_component_state(self, r): return self._json_response({"status": "success"})
