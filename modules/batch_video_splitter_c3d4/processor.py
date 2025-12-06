########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\batch_video_splitter_c3d4\processor.py total lines 180 
########################################################################

import os
import sys
import subprocess
import shutil
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
from flowork_kernel.utils.file_helper import sanitize_filename
import uuid

def get_startup_info():
    if os.name == 'nt':
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return info
    return None

class BatchVideoSplitterModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.ffmpeg_path = self._find_ffmpeg()
        self._ensure_icon()

    def _ensure_icon(self):
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(module_dir, "icon.png")
            if not os.path.exists(icon_path):
                default_icon = os.path.join(self.kernel.project_root_path, "assets", "default_module.png")
                if os.path.exists(default_icon):
                    shutil.copy(default_icon, icon_path)
        except:
            pass

    def _find_ffmpeg(self):
        ffmpeg_executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        path = os.path.join(
            self.kernel.project_root_path, "vendor", "ffmpeg", "bin", ffmpeg_executable
        )
        if os.path.exists(path):
            return path
        return "ffmpeg"

    def execute(
        self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs
    ):
        if mode == "SIMULATE":
            status_updater("Simulating video split process via Inject UI.", "INFO")
            return {"payload": payload, "output_name": "success"}

        if not self.ffmpeg_path:
            error_msg = "FFmpeg not found. Please ensure FFmpeg is installed."
            self.logger(error_msg, "CRITICAL")
            status_updater(error_msg, "ERROR")
            return {"payload": payload, "output_name": "error"}

        segment_duration = config.get("segment_duration", 3)
        folder_pairs = config.get("folder_pairs", [])
        process_timeout = config.get("process_timeout", 600)

        if not folder_pairs:
            self.logger("No folder pairs provided.", "WARN")
            status_updater("Warning: No input folders configured.", "WARN")

        status_updater(f"Starting batch split (Duration: {segment_duration}s)...", "INFO")

        total_processed_all_jobs = 0
        total_segments_all_jobs = 0
        all_results = []

        for pair in folder_pairs:
            source_folder = pair.get("source")

            output_folder = pair.get("output") or pair.get("destination")

            if not source_folder or not output_folder:
                self.logger(f"Skipping pair. Source: {source_folder}, Output: {output_folder}", "WARN")
                continue

            if not os.path.exists(source_folder):
                self.logger(f"Source folder not found (skipping): {source_folder}", "WARN")
                status_updater(f"Skipping missing source: {source_folder}", "WARN")
                continue

            if not os.path.exists(output_folder):
                try:
                    os.makedirs(output_folder)
                except OSError as e:
                    self.logger(f"Failed to create output folder: {e}", "ERROR")
                    continue

            video_extensions = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".ts")
            files = [
                f for f in os.listdir(source_folder)
                if f.lower().endswith(video_extensions)
            ]

            status_updater(f"Found {len(files)} videos in {source_folder}", "INFO")

            processed_count_job = 0
            total_segments_job = 0

            for i, filename in enumerate(files):
                input_path = os.path.join(source_folder, filename)
                file_base_name = os.path.splitext(filename)[0]
                safe_base_name = sanitize_filename(file_base_name)

                output_pattern = os.path.join(
                    output_folder, f"{safe_base_name}_%03d.mp4"
                )

                cmd = [
                    self.ffmpeg_path,
                    "-i", input_path,
                    "-c", "copy",
                    "-map", "0",
                    "-segment_time", str(segment_duration),
                    "-f", "segment",
                    "-reset_timestamps", "1",
                    output_pattern,
                    "-y"
                ]

                status_updater(f"Processing: {filename} ({i+1}/{len(files)})", "INFO")

                try:
                    subprocess.run(
                        cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=process_timeout,
                        startupinfo=get_startup_info(),
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )

                    processed_count_job += 1

                    generated_segments = len([
                        f for f in os.listdir(output_folder)
                        if f.startswith(safe_base_name) and f.endswith(".mp4")
                    ])
                    total_segments_job += generated_segments

                except subprocess.TimeoutExpired:
                    self.logger(f"Timeout processing '{filename}'. Killed.", "ERROR")
                    continue
                except Exception as e:
                    self.logger(f"Error on '{filename}': {str(e)}", "ERROR")
                    continue

            total_processed_all_jobs += processed_count_job
            total_segments_all_jobs += total_segments_job

            all_results.append({
                "source": source_folder,
                "output": output_folder,
                "files_processed": processed_count_job
            })

        status_updater(
            f"Batch split complete. Processed: {total_processed_all_jobs} files.",
            "SUCCESS",
        )

        if "data" not in payload or not isinstance(payload["data"], dict):
            payload["data"] = {}

        payload["data"]["batch_results"] = all_results
        return {"payload": payload, "output_name": "success"}

    def get_data_preview(self, config: dict):
        return [{"status": "preview_not_available"}]
