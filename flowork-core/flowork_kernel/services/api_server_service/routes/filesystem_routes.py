########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\filesystem_routes.py total lines 180 
########################################################################

import os
import sys
import json
import mimetypes
from urllib.parse import urlparse, parse_qs
from .base_api_route import BaseApiRoute
from aiohttp import web

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class FilesystemRoutes(BaseApiRoute):

    def register_routes(self):
        return {
            "GET /api/v1/filesystem/drives": self.handle_list_drives,
            "GET /api/v1/filesystem/list": self.handle_list_directory,
            "GET /api/v1/files/view": self.handle_view_file,
            "GET /api/v1/ai/files/view": self.handle_view_file,
        }

    def _get_safe_roots(self):
        roots = [os.path.abspath(self.kernel.project_root_path)]

        if hasattr(self.kernel, 'data_path'):
            roots.append(os.path.abspath(self.kernel.data_path))

        browseable_paths_config = os.path.join(
            self.kernel.data_path, "browseable_paths.json"
        )
        try:
            if os.path.exists(browseable_paths_config):
                with open(browseable_paths_config, "r", encoding="utf-8") as f:
                    user_defined_paths = json.load(f)
                    if isinstance(user_defined_paths, list):
                        for path in user_defined_paths:
                            if os.path.isdir(path):
                                roots.append(os.path.abspath(path))
        except Exception as e:
            self.logger(f"Could not load or parse 'browseable_paths.json': {e}", "WARN")

        user_home = os.path.expanduser("~")
        common_dirs = [
            "Desktop",
            "Documents",
            "Downloads",
            "Pictures",
            "Music",
            "Videos",
        ]
        for d in common_dirs:
            path = os.path.join(user_home, d)
            if os.path.isdir(path):
                roots.append(os.path.abspath(path))

        if PSUTIL_AVAILABLE:
            for partition in psutil.disk_partitions():
                roots.append(os.path.abspath(partition.mountpoint))
        else:
            if sys.platform == "win32":
                import string
                for letter in string.ascii_uppercase:
                    drive = f"{letter}:\\"
                    if os.path.isdir(drive):
                        roots.append(drive)

        return sorted(list(set(roots)))

    async def handle_list_drives(self, request):
        try:
            safe_roots = self._get_safe_roots()
            drives_info = []
            for path in safe_roots:
                name = path
                user_home = os.path.expanduser("~")
                if path.startswith(user_home):
                    relative_part = os.path.relpath(path, user_home)
                    if relative_part == ".":
                        name = "User Home"
                    else:
                        name = f"My {relative_part}"
                drives_info.append({"name": name, "path": path.replace(os.sep, "/")})
            return self._json_response(drives_info)
        except Exception as e:
            return self._json_response(
                {"error": f"Could not list drives: {str(e)}"}, status=500
            )

    async def handle_list_directory(self, request):
        safe_roots = self._get_safe_roots()
        req_path = request.query.get("path", "")
        if not req_path:
            target_path = os.path.abspath(self.kernel.project_root_path)
        else:
            target_path = os.path.abspath(req_path)

        target_path = os.path.normpath(target_path)

        is_safe = any(
            target_path.startswith(os.path.normpath(root)) for root in safe_roots
        )

        if target_path.startswith("/app/data") or "generated_images" in target_path:
            is_safe = True

        if not is_safe:
            self.logger(f"Forbidden path access attempt: {target_path}", "CRITICAL")
            return self._json_response(
                {"error": "Access to the requested path is forbidden."},
                status=403,
            )
        try:
            if not os.path.isdir(target_path):
                return self._json_response(
                    {"error": f"Path is not a valid directory: {target_path}"},
                    status=400,
                )
            items = []
            for item_name in sorted(os.listdir(target_path), key=lambda s: s.lower()):
                item_path = os.path.join(target_path, item_name)
                is_dir = os.path.isdir(item_path)
                items.append(
                    {
                        "name": item_name,
                        "type": "directory" if is_dir else "file",
                        "path": os.path.abspath(item_path).replace(os.sep, "/"),
                    }
                )
            return self._json_response(items)
        except Exception as e:
            self.logger(f"Error listing directory '{target_path}': {str(e)}", "ERROR")
            return self._json_response(
                {"error": str(e)}, status=500
            )

    async def handle_view_file(self, request):
        file_path = request.query.get("path")
        if not file_path:
            return self._json_response({"error": "Missing 'path' parameter."}, status=400)

        target_path = os.path.abspath(file_path)

        if not os.path.exists(target_path):
            return self._json_response({"error": "File not found."}, status=404)

        if not os.path.isfile(target_path):
            return self._json_response({"error": "Path is not a file."}, status=400)

        allowed_prefixes = [
            os.path.abspath(self.kernel.project_root_path),
            os.path.abspath(self.kernel.data_path),
            "/app/data"
        ]
        allowed_prefixes.extend(self._get_safe_roots())

        is_safe = any(target_path.startswith(p) for p in allowed_prefixes)

        if not is_safe:
             self.logger(f"Blocked access to file outside safe scope: {target_path}", "WARN")
             return self._json_response({"error": "Access denied."}, status=403)

        try:
            mime_type, _ = mimetypes.guess_type(target_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'

            return web.FileResponse(target_path, headers={"Content-Type": mime_type})

        except Exception as e:
            self.logger(f"Error serving file '{target_path}': {e}", "ERROR")
            return self._json_response({"error": str(e)}, status=500)
