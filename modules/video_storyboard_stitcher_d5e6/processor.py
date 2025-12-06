########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\video_storyboard_stitcher_d5e6\processor.py total lines 190 
########################################################################

import os
import sys
import subprocess
import random
import uuid
import shutil
from flowork_kernel.api_contract import BaseModule, IExecutable
from flowork_kernel.utils.file_helper import sanitize_filename

def get_startup_info():
    if os.name == 'nt':
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return info
    return None

class VideoStoryboardStitcherModule(BaseModule, IExecutable):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.ffmpeg_path = self._find_ffmpeg()
        self._ensure_icon()

    def _ensure_icon(self):
        """
        Checks if icon.png exists in the module folder.
        If not, copies the default_module.png from assets.
        """
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(module_dir, "icon.png")

            if not os.path.exists(icon_path):
                default_icon = os.path.join(self.kernel.project_root_path, "assets", "default_module.png")
                if os.path.exists(default_icon):
                    shutil.copy(default_icon, icon_path)
                    self.logger("Icon missing. Restored from default_module.png", "INFO")
        except Exception as e:
            self.logger(f"Icon auto-fix failed: {e}", "WARN")

    def _find_ffmpeg(self):
        ffmpeg_executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        path = os.path.join(self.kernel.project_root_path, "vendor", "ffmpeg", "bin", ffmpeg_executable)
        if os.path.exists(path):
            return path
        return ffmpeg_executable

    def execute(
        self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs
    ):
        if mode == "SIMULATE":
            status_updater("Simulating storyboard stitch...", "INFO")
            return {"payload": payload, "output_name": "success"}

        video_sections = config.get("video_sections", [])
        output_folder = config.get("output_folder")
        prefix = sanitize_filename(config.get("output_filename_prefix", "storyboard"))

        delete_after_use = True

        if not video_sections:
            return self.error_payload("No video sections/folders defined.")
        if not output_folder:
            return self.error_payload("Output folder not selected.")
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                return self.error_payload(f"Cannot create output folder: {e}")

        section_pools = []
        folder_names = []

        status_updater("Scanning folders...", "INFO")

        for section in video_sections:
            path = section.get("folder_path") if isinstance(section, dict) else section

            if not path or not os.path.exists(path):
                self.logger(f"Folder not found or empty path: {path}", "WARN")
                continue

            clips = [
                os.path.join(path, f)
                for f in os.listdir(path)
                if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm"))
            ]

            if not clips:
                self.logger(f"Warning: Folder {os.path.basename(path)} is empty. Skipping.", "WARN")
                continue

            random.shuffle(clips)
            section_pools.append(clips)
            folder_names.append(os.path.basename(path))

        if not section_pools:
            return self.error_payload("No valid video clips found in any section.")

        min_count = min(len(pool) for pool in section_pools)

        status_updater(f"Found {len(section_pools)} folders. Generating {min_count} videos.", "INFO")

        created_videos = []

        for i in range(min_count):
            current_batch_files = []

            for pool in section_pools:
                current_batch_files.append(pool[i]) # Access by index (shuffled)

            output_filename = f"{prefix}_{i+1:03d}.mp4"
            output_path = os.path.join(output_folder, output_filename)

            status_updater(f"Stitching {i+1}/{min_count}: {output_filename}", "INFO")

            try:
                self._run_ffmpeg_concat(current_batch_files, output_path)
                created_videos.append(output_path)

                if delete_after_use:
                    for f_path in current_batch_files:
                        try:
                            if os.path.exists(f_path):
                                os.remove(f_path)
                                self.logger(f"Deleted source: {os.path.basename(f_path)}", "DEBUG")
                        except Exception as del_err:
                            self.logger(f"Failed to delete {f_path}: {del_err}", "WARN")

            except Exception as e:
                self.logger(f"Failed to stitch video {i+1}: {e}", "ERROR")

        status_updater(f"Completed. Created {len(created_videos)} videos.", "SUCCESS")

        if "data" not in payload:
            payload["data"] = {}
        payload["data"]["stitched_video_paths"] = created_videos
        payload["data"]["total_created"] = len(created_videos)

        return {"payload": payload, "output_name": "success"}

    def _run_ffmpeg_concat(self, clip_list, output_path):
        temp_list_path = os.path.join(self.kernel.data_path, f"concat_{uuid.uuid4()}.txt")

        try:
            with open(temp_list_path, "w", encoding="utf-8") as f:
                for clip_path in clip_list:
                    safe_path = os.path.abspath(clip_path).replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")


            command = [
                self.ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", temp_list_path,
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-r", "30",
                output_path
            ]

            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            )

        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg Error: {e.stderr}")
        finally:
            if os.path.exists(temp_list_path):
                os.remove(temp_list_path)

    def error_payload(self, msg):
        self.logger(msg, "ERROR")
        return {"payload": {"data": {"error": msg}}, "output_name": "error"}
