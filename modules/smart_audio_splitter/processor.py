########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\modules\smart_audio_splitter\processor.py total lines 160 
########################################################################

import os
import sys
import shutil
import json
import subprocess
import importlib
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class SmartAudioSplitter(BaseModule, IExecutable, IDataPreviewer):

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
        vendor_path = os.path.join(self.kernel.project_root_path, "vendor", "ffmpeg", "bin", ffmpeg_executable)
        if os.path.exists(vendor_path): return vendor_path
        if shutil.which(ffmpeg_executable): return ffmpeg_executable
        return None

    def _install_package(self, package_name, import_name=None):
        if not import_name: import_name = package_name
        try:
            importlib.import_module(import_name)
            return True
        except ImportError:
            self.logger(f"Installing {package_name}...", "INFO")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--prefer-binary"])
                return True
            except:
                return False

    def process_file_v4_style(self, source_path, output_dir, file_name, silence_cfg, status_updater):
        from pydub import AudioSegment
        from pydub.silence import split_on_silence

        try:
            original_audio = AudioSegment.from_file(source_path)

            chunks = split_on_silence(
                original_audio,
                min_silence_len=silence_cfg["min_silence_len"],
                silence_thresh=silence_cfg["silence_thresh"],
                keep_silence=50
            )

            if not chunks:
                return 0, "No silence gaps found."

            base_name = os.path.splitext(file_name)[0]


            count = 0
            for i, chunk in enumerate(chunks):
                out_name = f"{base_name}_{i+1:02d}.mp3"
                save_path = os.path.join(output_dir, out_name)

                chunk.export(save_path, format="mp3")
                count += 1

            return count, None
        except Exception as e:
            return 0, str(e)

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):
        if mode == "SIMULATE":
            status_updater("Simulating...", "INFO")
            return {"payload": payload, "output_name": "success"}

        status_updater("Checking libraries...", "INFO")
        pkgs = [("pydub", "pydub")]
        for p, i in pkgs: self._install_package(p, i)

        from pydub import AudioSegment
        if self.ffmpeg_path and os.path.dirname(self.ffmpeg_path):
            os.environ["PATH"] += os.pathsep + os.path.dirname(self.ffmpeg_path)
        AudioSegment.converter = self.ffmpeg_path

        folder_pairs = config.get("folder_pairs", [])
        if not folder_pairs:
            status_updater("No folder pairs configured!", "ERROR")
            return {"payload": payload, "output_name": "error"}

        total_files = 0

        silence_cfg = {
            "min_silence_len": config.get("min_silence_len", 1000),
            "silence_thresh": config.get("silence_thresh", -45)
        }

        valid_exts = ('.mp3', '.wav', '.m4a', '.ogg', '.flac')

        for idx, pair in enumerate(folder_pairs):
            source_folder = pair.get("source")
            dest_folder = pair.get("destination") or pair.get("output")

            if not source_folder or not os.path.exists(source_folder):
                status_updater(f"Skipping invalid source: {source_folder}", "WARN")
                continue

            if not dest_folder:
                try:
                    parent = os.path.dirname(os.path.normpath(source_folder))
                    name = os.path.basename(os.path.normpath(source_folder))
                    dest_folder = os.path.join(parent, f"{name}_SPLIT_RESULT")
                    status_updater(f"⚠️ Auto-Dest: {dest_folder}", "WARN")
                except: continue

            if not os.path.exists(dest_folder):
                try: os.makedirs(dest_folder)
                except: pass

            status_updater(f"Scanning: {os.path.basename(source_folder)}...", "INFO")
            try:
                files = [f for f in os.listdir(source_folder) if f.lower().endswith(valid_exts)]
            except: continue

            for file_name in files:
                full_path = os.path.join(source_folder, file_name)
                status_updater(f"Processing: {file_name}...", "INFO")

                count, error = self.process_file_v4_style(full_path, dest_folder, file_name, silence_cfg, status_updater)

                if error:
                    self.logger(f"Error {file_name}: {error}", "ERROR")
                else:
                    total_files += count
                    status_updater(f"✅ Saved {count} clips to {os.path.basename(dest_folder)}", "SUCCESS")

        status_updater(f"Batch Done. Total: {total_files} clips.", "SUCCESS")

        if "data" not in payload: payload["data"] = {}
        payload["data"]["total_files_created"] = total_files

        return {"payload": payload, "output_name": "success" if total_files > 0 else "error"}

    def get_data_preview(self, config: dict):
        return [{"status": "preview_not_available"}]
