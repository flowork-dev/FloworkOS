########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\system_routes.py total lines 244 
########################################################################

import time
import os
import shutil
import threading
import json
from collections import Counter, defaultdict
from .base_api_route import BaseApiRoute
from aiohttp import web
import datetime
from flowork_kernel.exceptions import (
    PermissionDeniedError,
)

class SystemRoutes(BaseApiRoute):

    def register_routes(self) -> dict:
        return {
            "GET /health": self.handle_health_check,
            "GET /metrics": self.handle_get_metrics,
            "GET /api/v1/dashboard/summary": self.handle_get_dashboard_summary,
            "POST /api/v1/addons/upload": self.handle_addon_upload,
            "POST /api/v1/system/actions/hot_reload": self.handle_hot_reload,
            "GET /api/v1/status": self.handle_get_status,
            "POST /api/v1/system/actions/restart": self.handle_system_restart,
            "POST /api/v1/system/actions/shutdown": self.handle_system_shutdown,
            "POST /api/v1/system/actions/clear_cache": self.handle_clear_cache,
            "POST /api/v1/system/actions/browse_folder": self.handle_browse_folder,
            "POST /api/v1/system/diagnostics/run": self.handle_run_diagnostics,
        }

    async def handle_run_diagnostics(self, request):
        """
        Handles the request to run system diagnostics/scanners.
        Payload: { "scan_id": "optional_id", "target_scanner_id": "optional_scanner_key" }
        """
        try:
            body = await request.json()
            scan_id = body.get("scan_id", f"SCAN-{int(time.time())}")
            target_scanner_id = body.get("target_scanner_id")

            diag_service = self.kernel.get_service("diagnostics_service")
            if not diag_service:
                 return self._json_response(
                     {"error": "Diagnostics Service is not loaded in the kernel."},
                     status=503
                 )

            self.logger(f"Diagnostics requested. ID: {scan_id}, Target: {target_scanner_id}", "INFO")

            result = diag_service.start_scan_headless(scan_id, target_scanner_id)

            return self._json_response(result, status=200)

        except Exception as e:
            self.logger(f"Failed to execute diagnostics: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_system_restart(self, request):
        try:
            permission_manager = self.kernel.get_service(
                "permission_manager_service", is_system_call=True
            )
            if permission_manager:
                permission_manager.check_permission("engine_management")
            self.logger(
                "API request received to restart the engine.", "WARN", "ApiServer"
            )
            await self.kernel.restart_application()
            return self._json_response(
                {"status": "accepted", "message": "Engine restart process initiated."},
                status=202,
            )
        except PermissionDeniedError as e:
            self.logger(
                f"Permission denied for engine restart: {e}", "CRITICAL", "ApiServer"
            )
            return self._json_response({"error": str(e)}, status=403)
        except Exception as e:
            self.logger(
                f"Error during engine restart request: {e}", "CRITICAL", "ApiServer"
            )
            return self._json_response(
                {"error": "Internal server error during restart."}, status=500
            )

    async def handle_system_shutdown(self, request):
        try:
            permission_manager = self.kernel.get_service(
                "permission_manager_service", is_system_call=True
            )
            if permission_manager:
                permission_manager.check_permission("engine_management")
            self.logger(
                "API request received to shut down the engine.", "CRITICAL", "ApiServer"
            )
            await self.kernel.shutdown_application()
            return self._json_response(
                {"status": "accepted", "message": "Engine shutdown process initiated."},
                status=202,
            )
        except PermissionDeniedError as e:
            self.logger(
                f"Permission denied for engine shutdown: {e}", "CRITICAL", "ApiServer"
            )
            return self._json_response({"error": str(e)}, status=403)
        except Exception as e:
            self.logger(
                f"Error during engine shutdown request: {e}", "CRITICAL", "ApiServer"
            )
            return self._json_response(
                {"error": "Internal server error during shutdown."}, status=500
            )

    async def handle_get_dashboard_summary(self, request):
        return self._json_response(
            {
                "status": "deprecated",
                "message": "This endpoint is deprecated. Dashboard summary is now provided by the Gateway.",
            }
        )

    def handle_browse_folder(self, handler):
        self.logger(
            "API call received for browsing folder. This feature is conceptually flawed for a server.",
            "WARN",
        )
        fallback_path = "C:/FLOWORK/MANUAL_PATH_REQUIRED"
        handler._send_response(
            200,
            {
                "success": True,
                "path": fallback_path,
                "message": "Manual path entry required. Server cannot browse folders.",
            },
        )

    async def handle_health_check(self, request):
        status_info = {"status": "ready", "message": "Core API server is responsive."}
        return self._json_response(status_info, status=200)

    async def handle_get_metrics(self, request):
        metrics_service = self.service_instance.metrics_service
        if not metrics_service:
            return self._json_response(
                {"error": "Metrics service is not available."}, status=503
            )
        metrics_data = metrics_service.serve_metrics()
        return web.Response(body=metrics_data, content_type="text/plain; version=0.0.4")

    async def handle_get_status(self, request):
        status_info = {
            "status": "ok",
            "version": self.kernel.APP_VERSION,
            "timestamp": time.time(),
        }
        return self._json_response(status_info)

    async def handle_addon_upload(self, request):
        addon_service = self.service_instance.addon_service
        if not addon_service:
            return self._json_response(
                {"error": "CommunityAddonService is not available."}, status=503
            )
        body = await request.json()
        comp_type, component_id, description, tier = (
            body.get("comp_type"),
            body.get("component_id"),
            body.get("description"),
            body.get("tier"),
        )
        if not all([comp_type, component_id, description, tier]):
            return self._json_response(
                {
                    "error": "Request body must contain 'comp_type', 'component_id', 'description', and 'tier'."
                },
                status=400,
            )
        try:
            success, result_message = addon_service.upload_component(
                comp_type, component_id, description, tier
            )
            if success:
                return self._json_response(
                    {"status": "success", "message": result_message}, status=200
                )
            else:
                return self._json_response({"error": result_message}, status=500)
        except Exception as e:
            self.logger(f"API Addon Upload Error: {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)

    async def handle_hot_reload(self, request):
        try:
            self.kernel.hot_reload_components()
            return self._json_response(
                {"status": "success", "message": "Hot reload process initiated."},
                status=200,
            )
        except Exception as e:
            self.logger(f"Hot reload via API failed: {e}", "CRITICAL")
            return self._json_response(
                {"error": f"Internal server error during hot reload: {e}"}, status=500
            )

    async def handle_clear_cache(self, request):
        try:
            deleted_folders, deleted_files = 0, 0
            for root, dirs, files in os.walk(
                self.kernel.project_root_path, topdown=False
            ):
                if "__pycache__" in dirs:
                    pycache_path = os.path.join(root, "__pycache__")
                    try:
                        shutil.rmtree(pycache_path)
                        deleted_folders += 1
                    except OSError:
                        pass

            data_folder = self.kernel.data_path
            if os.path.isdir(data_folder):
                for filename in os.listdir(data_folder):
                    if filename.endswith(".cache"):
                        try:
                            os.remove(os.path.join(data_folder, filename))
                            deleted_files += 1
                        except OSError:
                            pass
            summary = f"Cache clear complete. Removed {deleted_folders} folders and {deleted_files} cache files."
            self.logger(summary, "SUCCESS")
            return self._json_response(
                {"status": "success", "message": summary}, status=200
            )
        except Exception as e:
            self.logger(f"Clear cache via API failed: {e}", "CRITICAL")
            return self._json_response(
                {"error": f"Internal server error during cache clearing: {e}"},
                status=500,
            )
