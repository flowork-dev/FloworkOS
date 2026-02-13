########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_file_commander\backend\app_service.py total lines 304 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import shutil
import time
import asyncio
from pathlib import Path
from flowork_kernel.services.base_app_service import BaseAppService


class FileManagerService(BaseAppService):
    """
    THE FILE COMMANDER BRAIN - GUI EDITION
    Upgraded to handle batch deletion safely and prevent Quarantine loops.
    """
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.name = "Flowork File Manager"

        self.muscle = self.kernel.get_service("app_runtime")
        if self.muscle:
            self.logger.info("📂 [Bridge] File Commander linked to Muscle.")

        try:
            self.kernel.write_to_log(f"[{self.name}] Service Initialized.", "INFO")
        except:
            self.logger.info(f"[{self.name}] Service Initialized.")

    def start(self):
        try:
            self.kernel.write_to_log(f"[{self.name}] Ready.", "SUCCESS")
        except:
            self.logger.info(f"[{self.name}] Ready.")

    def stop(self):
        pass

    def _detect_real_user(self):
        try:
            data_root = Path("/app/data/users")
            if data_root.exists():
                for entry in os.scandir(data_root):
                    if entry.is_dir() and entry.name != "system":
                        return entry.name
        except: pass
        return "system"

    def _smart_resolve_path(self, path_str, user_id):
        """Resolves path intelligently, redirecting 'system' paths to user_id."""
        if user_id == "system":
            real_id = self._detect_real_user()
            if real_id != "system":
                user_id = real_id

        if hasattr(self, 'get_user_data_path'):
            user_root = Path(self.get_user_data_path(user_id))
        else:
            user_root = Path("/app/data/users") / user_id

        if not path_str:
            return user_root, user_root

        path_str = str(path_str).replace("\\", "/").strip()

        system_prefix = "/app/data/users/system"
        if path_str.startswith(system_prefix):
            relative_part = path_str[len(system_prefix):].lstrip("/")
            return user_root / relative_part, user_root

        user_prefix = f"/app/data/users/{user_id}"
        if path_str.startswith(user_prefix):
            return Path(path_str), user_root

        clean_rel = path_str.lstrip("/")
        return user_root / clean_rel, user_root

    def _to_virtual_path(self, real_path):
        """Helper to convert real path back to virtual for UI."""
        return real_path.replace("\\", "/")

    def _broadcast_log(self, message, user_id, level="INFO"):
        try:
            print(f"[{level}] [FileCommander] {message}", flush=True)
            if hasattr(self.kernel, 'event_bus'):
                self.kernel.event_bus.publish("APP_LOG_STREAM", {
                    "app_id": "flowork_file_commander",
                    "message": message,
                    "level": level,
                    "timestamp": time.time(),
                    "_target_user_id": user_id
                })
        except: pass

    async def _delegate_to_muscle(self, action, payload, user_id="system"):
        if not self.muscle: return None
        try:
            return await self.muscle.execute_service_action(
                app_id="flowork_file_commander",
                action_name=action,
                data={**payload, "user_context": {"user_id": user_id}}
            )
        except Exception as e:
            return None

    async def list_files(self, path: str, user_id: str):
        try:
            target_path, _ = self._smart_resolve_path(path, user_id)

            if not target_path.exists() and "users" in str(target_path):
                try: target_path.mkdir(parents=True, exist_ok=True)
                except: pass

            if not target_path.exists():
                return {"status": "error", "error": "Directory not found"}

            items = []
            for entry in os.scandir(target_path):
                is_dir = entry.is_dir()
                icon = "mdi-folder" if is_dir else "mdi-file-document-outline"

                if not is_dir:
                    ext = entry.name.split('.')[-1].lower() if '.' in entry.name else ""
                    if ext in ['jpg', 'png', 'jpeg', 'gif']: icon = "mdi-image"
                    elif ext in ['mp4', 'mkv', 'avi']: icon = "mdi-video"
                    elif ext in ['mp3', 'wav']: icon = "mdi-music"
                    elif ext in ['py', 'js', 'html', 'css', 'json']: icon = "mdi-code-tags"
                    elif ext in ['zip', 'rar', 'tar']: icon = "mdi-zip-box"

                items.append({
                    "name": entry.name,
                    "path": self._to_virtual_path(entry.path),
                    "type": "folder" if is_dir else "file",
                    "icon": icon,
                    "size": entry.stat().st_size if entry.is_file() else 0,
                    "modified": entry.stat().st_mtime
                })

            return {
                "status": "success",
                "data": items,
                "current_path": self._to_virtual_path(str(target_path)),
                "items": items
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def create_new_folder(self, current_path: str, name: str, user_id: str):
        muscle_res = await self._delegate_to_muscle("create_folder", {"path": current_path, "name": name}, user_id)
        if muscle_res and muscle_res.get("status") == "success":
            return muscle_res

        try:
            base_path, _ = self._smart_resolve_path(current_path, user_id)
            new_folder_path = base_path / name

            if new_folder_path.exists():
                return {"status": "error", "error": "Folder already exists"}

            new_folder_path.mkdir(parents=True, exist_ok=True)
            self._broadcast_log(f"Created folder: {name}", user_id)

            return {
                "status": "success",
                "path": self._to_virtual_path(str(new_folder_path))
            }
        except Exception as e:
            self._broadcast_log(f"Create folder failed: {e}", user_id, "ERROR")
            return {"status": "error", "error": str(e)}

    async def create_new_file(self, current_path: str, name: str, content: str, user_id: str):
        muscle_res = await self._delegate_to_muscle("create_file", {"path": current_path, "name": name, "content": content}, user_id)
        if muscle_res and muscle_res.get("status") == "success":
            return muscle_res

        try:
            base_path, _ = self._smart_resolve_path(current_path, user_id)
            new_file_path = base_path / name

            if new_file_path.exists():
                return {"status": "error", "error": "File already exists"}

            with open(new_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self._broadcast_log(f"Created file: {name}", user_id)

            return {
                "status": "success",
                "path": self._to_virtual_path(str(new_file_path))
            }
        except Exception as e:
            self._broadcast_log(f"Create file failed: {e}", user_id, "ERROR")
            return {"status": "error", "error": str(e)}

    async def delete_item(self, path: str, user_id: str):
        target_path, _ = self._smart_resolve_path(path, user_id)
        if not target_path.exists():
            return {"status": "success"}

        muscle_res = await self._delegate_to_muscle("delete_item", {"path": path}, user_id)
        if muscle_res and muscle_res.get("status") == "success":
            return muscle_res

        try:
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)

            self._broadcast_log(f"Deleted: {target_path.name}", user_id)
            return {"status": "success"}
        except Exception as e:
            self._broadcast_log(f"Delete failed: {e}", user_id, "ERROR")
            return {"status": "error", "error": str(e)}

    async def rename_item(self, path: str, new_name: str, user_id: str):
        muscle_res = await self._delegate_to_muscle("rename_item", {"path": path, "new_name": new_name}, user_id)
        if muscle_res and muscle_res.get("status") == "success":
            return muscle_res

        try:
            target_path, _ = self._smart_resolve_path(path, user_id)

            if not target_path.exists():
                return {"status": "error", "error": "Item not found"}

            new_path = target_path.parent / new_name

            if new_path.exists():
                return {"status": "error", "error": "Name already exists"}

            target_path.rename(new_path)
            self._broadcast_log(f"Renamed {target_path.name} to {new_name}", user_id)

            return {"status": "success"}
        except Exception as e:
            self._broadcast_log(f"Rename failed: {e}", user_id, "ERROR")
            return {"status": "error", "error": str(e)}

    async def delete_batch_items(self, paths: list, user_id: str):
        muscle_res = await self._delegate_to_muscle("delete_batch", {"paths": paths}, user_id)
        if muscle_res and muscle_res.get("status") == "success":
            return muscle_res

        deleted_count = 0
        errors = []

        self._broadcast_log("Muscle offline/crashed. Processing batch locally via Resident...", user_id, "WARNING")

        for path in paths:
            try:
                target_path, _ = self._smart_resolve_path(path, user_id)
                if not target_path.exists():
                    deleted_count += 1
                    continue

                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)

                deleted_count += 1
            except Exception as e:
                errors.append(f"{path}: {str(e)}")

            await asyncio.sleep(0.005) # Beri nafas buat event loop

        log_msg = f"Batch Delete Complete: {deleted_count} items removed via Resident."
        self._broadcast_log(log_msg, user_id)

        return {
            "status": "success" if deleted_count > 0 or not errors else "error",
            "deleted": deleted_count,
            "errors": errors
        }

    async def read_file_content(self, path: str, user_id: str):
        try:
            target_path, _ = self._smart_resolve_path(path, user_id)

            if not target_path.exists() or not target_path.is_file():
                return {"error": "Invalid file"}

            if target_path.stat().st_size > 1024 * 1024:
                return {"error": "File too large for preview"}

            with open(target_path, 'r', encoding='utf-8') as f:
                return {"status": "success", "content": f.read()}
        except UnicodeDecodeError:
            return {"error": "Binary file"}
        except Exception as e:
            return {"error": str(e)}

    async def get_download_path(self, path: str, user_id: str):
        try:
            target_path, _ = self._smart_resolve_path(path, user_id)
            if target_path.exists() and target_path.is_file():
                return str(target_path)
            return None
        except: return None
