########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\universal_downloader\backend\app_service.py total lines 527 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import shutil
import logging
import asyncio
import subprocess
import sys
import time
import threading
import uuid
from pathlib import Path
from flowork_kernel.services.base_app_service import BaseAppService

yt_dlp = None

class UniversalDownloaderService(BaseAppService):
    def __init__(self, kernel=None, service_id=None):
        if kernel and service_id:
            super().__init__(kernel, service_id)
        else:
            self.logger = logging.getLogger(f"AppService.{service_id if service_id else 'UniversalDownloader'}")

        self.name = "Universal Downloader"
        self.service_id = service_id
        self.kernel = kernel # Assign manual

        self._ensure_dependency()

        self.active_jobs = {}

        self.muscle = None
        if self.kernel:
            self.muscle = self.kernel.get_service("app_runtime")
            if self.muscle:
                self.logger.info("✅ [Service] Connected to THE MUSCLE (AppRuntime).")
            else:
                self.logger.warning("⚠️ [Service] Muscle not found! Falling back to legacy mode.")

            self._attach_log_listener()

            try:
                self.kernel.write_to_log(f"[{self.name}] Service Initialized.", "INFO")
            except:
                self.logger.info(f"[{self.name}] Service Initialized.")
        else:
             self.logger.warning("⚠️ [Service] Initialized via Empty Constructor.")

    def _attach_log_listener(self):
        if self.kernel and hasattr(self.kernel, 'event_bus'):
            self.kernel.event_bus.subscribe("APP_LOG_STREAM", self._handle_event_log)
            self.kernel.event_bus.subscribe("EXECUTION_LOG", self._handle_event_log)
            self.logger.info("👂 [Listener] Attached to EventBus for Log Bridging.")

    def _handle_event_log(self, event_name, data):
        try:
            if data.get('app_id') != 'universal_downloader': return

            msg = data.get('message') or data.get('raw') or ""
            user_id = data.get('user_id') or data.get('_target_user_id')
            level = data.get('level', 'INFO')

            if not user_id or not msg: return

            for jid, job in self.active_jobs.items():
                if job.get('user_id') == user_id and job.get('status') == 'running':
                    if 'logs' not in job: job['logs'] = []
                    job['logs'].append({"msg": msg, "type": level})

                    if "###SEQUENCE_COMPLETE###" in msg or "Final Outcome" in msg:
                        job['status'] = 'completed'
                        job['logs'].append({"msg": "✅ [System] Job marked as COMPLETED via Bridge.", "type": "success"})
                    break
        except: pass

    def _ensure_dependency(self):
        global yt_dlp
        try:
            import yt_dlp as lib
            yt_dlp = lib
        except ImportError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
                import yt_dlp as lib
                yt_dlp = lib
            except:
                self.logger.error("Failed to install yt-dlp Python lib.")
                return False

        try:
            subprocess.check_call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            self.logger.warning("[Auto-Setup] FFmpeg not found. Installing system dependency for Audio support...")
            try:
                subprocess.call(["apt-get", "update"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.call(["apt-get", "install", "-y", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.logger.info("[Auto-Setup] FFmpeg installed successfully.")
            except:
                try:
                    subprocess.call(["apk", "add", "--no-cache", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except:
                    self.logger.error("[Auto-Setup] Failed to install FFmpeg. Videos might be silent!")

        return True

    def _detect_real_user(self):
        try:
            data_root = Path("/app/data/users")
            if not data_root.exists():
                data_root = Path(os.getcwd()) / "data" / "users"

            if data_root.exists():
                for entry in os.scandir(data_root):
                    if entry.is_dir() and entry.name != "system":
                        return entry.name
        except: pass
        return "system"

    def _smart_resolve_path(self, path_str, user_id):
        if user_id in ["system", "None", None]:
            real_id = self._detect_real_user()
            if real_id != "system":
                user_id = real_id

        if hasattr(self, 'get_user_data_path'):
            user_root = Path(self.get_user_data_path(user_id))
        else:
            user_root = Path("/app/data/users") / user_id

        if not path_str:
            return user_root / "downloads", user_root

        path_str = str(path_str).replace("\\", "/").strip()
        if "/users/system" in path_str:
            path_str = path_str.replace("/users/system", f"/users/{user_id}")

        if path_str.startswith(f"/app/data/users/{user_id}"):
            return Path(path_str), user_root

        system_prefix = "/app/data/users/system"
        if path_str.startswith(system_prefix):
            relative_part = path_str[len(system_prefix):].lstrip("/")
            return user_root / relative_part, user_root

        user_prefix = f"/app/data/users/{user_id}"
        if path_str.startswith(user_prefix):
            return Path(path_str), user_root

        clean_rel = path_str.lstrip("/")
        return user_root / clean_rel, user_root

    def _broadcast_log(self, message, user_id, level="INFO"):
        try:
            print(f"[{level}] [UniversalDL] {message}", flush=True)
            for jid, job in self.active_jobs.items():
                if job.get('user_id') == user_id and job.get('status') == 'running':
                    if 'logs' not in job: job['logs'] = []
                    job['logs'].append({"msg": message, "type": level})

            if self.kernel and hasattr(self.kernel, 'event_bus'):
                self.kernel.event_bus.publish("APP_LOG_STREAM", {
                    "app_id": "universal_downloader",
                    "message": message,
                    "level": level,
                    "timestamp": time.time(),
                    "_target_user_id": user_id
                })
        except: pass

    def start(self):
        self.logger.info(f"[{self.name}] Ready.")

    def stop(self):
        pass

    def list_files(self, path: str, user_id: str):
        try:
            target_path, _ = self._smart_resolve_path(path, user_id)


            if not target_path.exists():
                try:
                    target_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"📂 [Auto-Create] Created missing directory: {target_path}")
                except Exception as e:
                    return {"status": "error", "error": f"Directory not found and failed to create: {e}"}

            items = []
            for entry in os.scandir(target_path):
                items.append({
                    "name": entry.name,
                    "path": str(Path(entry.path).as_posix()),
                    "type": "folder" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else 0
                })

            return {
                "status": "success",
                "data": items,
                "current_path": str(target_path.as_posix()),
                "items": items
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def create_new_folder(self, current_path: str, name: str, user_id: str):
        try:
            base_path, _ = self._smart_resolve_path(current_path, user_id)
            new_folder_path = base_path / name

            if new_folder_path.exists():
                return {"status": "error", "error": "Folder already exists"}

            new_folder_path.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "path": str(new_folder_path)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def delete_item(self, path: str, user_id: str):
        try:
            target_path, _ = self._smart_resolve_path(path, user_id)

            if not target_path.exists():
                return {"status": "error", "error": "Item not found"}

            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def rename_item(self, path: str, new_name: str, user_id: str):
        try:
            target_path, _ = self._smart_resolve_path(path, user_id)
            if not target_path.exists():
                return {"status": "error", "error": "Item not found"}

            new_path = target_path.parent / new_name
            target_path.rename(new_path)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def delete_batch_items(self, paths: list, user_id: str):
        deleted_count = 0
        errors = []
        for path in paths:
            result = self.delete_item(path, user_id)
            if result.get("status") == "success":
                deleted_count += 1
            else:
                errors.append(f"{path}: {result.get('error')}")

        return {
            "status": "success" if deleted_count > 0 else "error",
            "deleted": deleted_count,
            "errors": errors
        }

    def read_file_content(self, path: str, user_id: str):
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

    def get_download_path(self, path: str, user_id: str):
        try:
            target_path, _ = self._smart_resolve_path(path, user_id)
            if target_path.exists() and target_path.is_file():
                return str(target_path)
            return None
        except: return None


    async def execute(self, input_data, **kwargs):
        config = input_data if isinstance(input_data, dict) else {}
        user_context = kwargs.get('user_context', {})
        if not user_context and isinstance(config, dict):
            user_context = config.get('user_context', {})

        user_id = (
            user_context.get('user_id') or
            user_context.get('id') or
            kwargs.get('user_id') or
            'system'
        )

        return self.start_background_download(
            config.get('url'),
            config.get('output_folder') or config.get('output_dir'),
            config.get('format_mode', 'best'),
            user_id
        )

    def start_background_download(self, url, output_folder, format_mode, user_id):
        """
        [HYBRID] Attempts to delegate to Muscle via Socket.
        Falls back to local thread if Muscle is absent.
        """
        if user_id == "system":
            real_id = self._detect_real_user()
            if real_id != "system":
                user_id = real_id

        self._broadcast_log(f"Initializing download job for {user_id}", user_id)

        if self.muscle:
            self.logger.info(f"💪 [Bridge] Delegating job to Muscle: {url}")

            result = self.muscle.execute_app(
                app_id="universal_downloader",
                action="download",
                params={
                    "url": url,
                    "output_folder": output_folder,
                    "format_mode": format_mode
                },
                user_id=user_id
            )

            job_id = result.get('pid') or str(uuid.uuid4())

            self.active_jobs[job_id] = {
                "status": "running" if result.get('status') == 'success' else "failed",
                "progress": "muscle_processing",
                "muscle_pid": result.get('pid'),
                "user_id": user_id,
                "logs": [],
                "results": []
            }

            return {"status": "job_started", "job_id": job_id}

        else:
            self.logger.warning("⚠️ Muscle DEAD. Using legacy thread mode.")
            job_id = str(uuid.uuid4())
            self.active_jobs[job_id] = {
                "status": "running",
                "progress": "queued",
                "user_id": user_id,
                "logs": [],
                "results": []
            }
            thread = threading.Thread(
                target=self._run_job_thread,
                args=(job_id, url, output_folder, format_mode, user_id)
            )
            thread.start()
            return {"status": "job_started", "job_id": job_id}

    def get_job_status(self, job_id):
        return self.active_jobs.get(job_id, {"status": "unknown"})

    def get_job_progress(self, job_id):
        if job_id not in self.active_jobs:
            return {"status": "unknown", "logs": []}

        job = self.active_jobs[job_id]
        current_logs = list(job.get("logs", []))

        job["logs"] = []

        return {
            "status": job["status"],
            "progress": job.get("progress", ""),
            "logs": current_logs
        }

    def _run_job_thread(self, job_id, url, output_folder, format_mode, user_id):
        try:
            result = self._perform_download(url, output_folder, format_mode, user_id, job_id)
            if result.get('status') == 'success':
                self.active_jobs[job_id]['status'] = 'completed'
                self.active_jobs[job_id]['results'] = result.get('downloaded', [])
            else:
                self.active_jobs[job_id]['status'] = 'failed'
                self.active_jobs[job_id]['error'] = result.get('error')
        except Exception as e:
            self.active_jobs[job_id]['status'] = 'failed'
            self.active_jobs[job_id]['error'] = str(e)
        finally:
            try:
                if self.kernel:
                    self.kernel.event_bus.publish("APP_JOB_FINISHED", {
                        "app_id": "universal_downloader",
                        "pid": job_id,
                        "status": self.active_jobs[job_id].get('status', 'unknown'),
                        "user_id": user_id
                    })
                    self.kernel.write_to_log(f"###SEQUENCE_COMPLETE### (Job: {job_id})", "SUCCESS", node_id=job_id, source="APP:universal_downloader")
            except Exception as ev_err:
                self.logger.error(f"Failed to publish finish event: {ev_err}")

    def run_download(self, url, output_folder, format_mode, user_id):
        if self.muscle:
             self.muscle.execute_app(
                app_id="universal_downloader",
                action="download",
                params={"url": url, "output_folder": output_folder, "format_mode": format_mode},
                user_id=user_id
            )
             return {"status": "success", "message": "Job sent to Muscle"}

        if not yt_dlp: self._ensure_dependency()
        return self._perform_download(url, output_folder, format_mode, user_id)

    def _perform_download(self, url, output_folder_path, format_mode, user_id, job_id=None):
        try:
            target_path, _ = self._smart_resolve_path(output_folder_path, user_id)

            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)

            urls = [u.strip() for u in url.split('\n') if u.strip()]
            results = []
            last_log_time = 0

            def progress_hook(d):
                nonlocal last_log_time
                if d['status'] == 'downloading':
                    if job_id and job_id in self.active_jobs:
                        self.active_jobs[job_id]['progress'] = d.get('_percent_str', '...')

                    current_time = time.time()
                    if current_time - last_log_time >= 3:
                        p_str = d.get('_percent_str', 'N/A').replace('%','')
                        speed = d.get('_speed_str', 'N/A')
                        eta = d.get('_eta_str', 'N/A')
                        log_msg = f"⚡ [Neural DL] {p_str}% @ {speed} | ETA: {eta}"
                        self._broadcast_log(log_msg, user_id)
                        last_log_time = current_time

                elif d['status'] == 'finished':
                    self._broadcast_log("✅ [Neural DL] Download Complete. Converting...", user_id, "SUCCESS")

            for idx, single_url in enumerate(urls, 1):
                try:
                    time.sleep(1)

                    filename_tmpl = f"{idx}.%(ext)s"
                    target_file = str(target_path / filename_tmpl)

                    opts = {
                        'outtmpl': target_file,
                        'quiet': True,
                        'progress_hooks': [progress_hook],
                        'no_continue': True,
                        'retries': 3,
                        'nocheckcertificate': True,
                        'ignoreerrors': True,
                    }

                    if format_mode == 'audio_mp3':
                        opts.update({
                            'format': 'bestaudio/best',
                            'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',
                            }]
                        })
                    else:

                        height_filter = ""
                        if format_mode == '4k': height_filter = "[height=2160]"
                        elif format_mode == '2k': height_filter = "[height=1440]"
                        elif format_mode == '1080p': height_filter = "[height=1080]"
                        elif format_mode == '720p': height_filter = "[height=720]"
                        elif format_mode == '480p': height_filter = "[height=480]"
                        elif format_mode == '360p': height_filter = "[height=360]"

                        f_str = (
                            f"bestvideo{height_filter}[ext=mp4]+bestaudio[ext=m4a]/"
                            f"bestvideo{height_filter}+bestaudio/"
                            f"best{height_filter}[ext=mp4]/"
                            f"best"
                        )

                        opts.update({
                            'format': f_str,
                            'merge_output_format': 'mp4',
                            'postprocessors': [{
                                'key': 'FFmpegVideoConvertor',
                                'preferedformat': 'mp4',
                            }]
                        })

                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(single_url, download=True)

                        if info is None:
                            self.logger.error(f"❌ [YT-DLP] Failed to extract info for {single_url}. Possibly auth/cookie issue.")
                            self._broadcast_log(f"❌ [Error] Link rejected by YouTube (Auth/Geo-block): {single_url}", user_id, "ERROR")
                            continue

                        final_filename = ydl.prepare_filename(info)

                        if format_mode == 'audio_mp3':
                            final_filename = os.path.splitext(final_filename)[0] + ".mp3"
                        else:
                            final_filename = os.path.splitext(final_filename)[0] + ".mp4"

                        results.append({"file": os.path.basename(final_filename), "title": info.get('title', 'Unknown'), "path": str(final_filename)})

                except Exception as e:
                    self.logger.error(f"Download failed for {single_url}: {str(e)}")
                    continue

            return {"status": "success", "downloaded": results}

        except Exception as e:
            return {"status": "error", "error": str(e)}
