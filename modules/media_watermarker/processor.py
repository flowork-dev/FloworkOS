########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\modules\media_watermarker\processor.py total lines 208 
########################################################################

import os
import sys
import json
import subprocess
import uuid
import shutil
import traceback
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

print("--- [HydroSeal] Initializing Branding Unit (Hunter-Mode)... ---", file=sys.stderr, flush=True)

def get_startup_info():
    if os.name == 'nt':
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return info
    return None

class MediaWatermarker(BaseModule, IExecutable, IDataPreviewer):

    TIER = "builder"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.logger_service = services.get("logger")
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
        except: pass

    def _find_ffmpeg(self):
        ffmpeg_executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        path = os.path.join(self.kernel.project_root_path, "vendor", "ffmpeg", "bin", ffmpeg_executable)
        if os.path.exists(path): return path
        return "ffmpeg"

    def _log(self, msg, level="INFO"):
        if self.logger_service: self.logger_service(msg, level)
        print(f"[{level}] {msg}", file=sys.stderr)

    def _extract_inputs_recursive(self, payload):
        found = {}
        if isinstance(payload, dict):
            for k, v in payload.items():
                if isinstance(v, (str, int, float, bool)) and k not in found:
                    found[k] = v
                elif isinstance(v, dict):
                    nested = self._extract_inputs_recursive(v)
                    found.update(nested)
        return found

    def _resolve_file_path(self, path):
        if path and os.path.exists(path): return path

        filename = os.path.basename(path)
        self._log(f"🕵️ Path '{path}' not found. Hunting for '{filename}'...", "WARN")

        search_locations = [
            f"/app/data/{filename}",
            f"/app/data/downloads/{filename}",
            f"/mnt/videos/{filename}",          # Folder Video User
            f"/mnt/videos/cliper/{filename}",   # Folder Cliper (Sering dipake)
            f"/app/flowork_kernel/assets/{filename}"
        ]

        for candidate in search_locations:
            if os.path.exists(candidate):
                self._log(f"✅ Found it at: {candidate}", "INFO")
                return candidate

        return path # Nyerah, balikin path asli biar error

    def _sanitize_output_path(self, path):
        clean = path.replace("\\", "/")
        if ":" in clean: # Windows path detected
            if "videos" in clean.lower(): return "/mnt/videos"
            return "/app/data/branded_output"
        return clean

    def _get_video_info(self, path):
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", path
        ]
        try:
            output = subprocess.check_output(cmd, startupinfo=get_startup_info()).decode("utf-8").strip()
            w, h = map(int, output.split("x"))
            return w, h
        except Exception as e:
            self._log(f"Probe failed for {path}: {e}", "WARN")
            return 1920, 1080

    def execute(self, payload, config, status_updater, mode="EXECUTE", **kwargs):
        if mode == "SIMULATE":
            return {"payload": payload, "output_name": "success"}

        if not self.ffmpeg_path:
            status_updater("FFmpeg Missing!", "ERROR")
            return {"payload": payload, "output_name": "error"}

        try:
            extracted_inputs = self._extract_inputs_recursive(payload)
            inputs = {**config, **extracted_inputs}
            print(f"DEBUG INPUTS: {json.dumps(inputs)}", file=sys.stderr)

            raw_source = inputs.get("input_path")
            raw_watermark = inputs.get("watermark_path")

            source_path = self._resolve_file_path(raw_source)
            watermark_path = self._resolve_file_path(raw_watermark)

            raw_output = inputs.get("output_folder", "/app/data/branded_output")
            output_folder = self._sanitize_output_path(raw_output)

            if not source_path or not os.path.exists(source_path):
                status_updater(f"Missing Input: {os.path.basename(raw_source)}", "ERROR")
                return {"payload": payload, "output_name": "error"}

            if not watermark_path or not os.path.exists(watermark_path):
                status_updater(f"Missing Logo: {os.path.basename(raw_watermark)}", "ERROR")
                return {"payload": payload, "output_name": "error"}

            if not os.path.exists(output_folder):
                try: os.makedirs(output_folder, exist_ok=True)
                except: pass

            video_name = os.path.basename(source_path)
            status_updater(f"🔒 Locked: {video_name}", "INFO")

            x_ratio = inputs.get("x_ratio")
            y_ratio = inputs.get("y_ratio")
            scale_pct = float(inputs.get("scale_percent", 15)) / 100.0
            opacity = float(inputs.get("opacity", 0.8))
            position = inputs.get("position", "top_right")

            vid_w, vid_h = self._get_video_info(source_path)
            scale_filter = f"scale={int(vid_w * scale_pct)}:-1"

            overlay_coord = ""
            if x_ratio is not None and y_ratio is not None:
                final_x = int(vid_w * float(x_ratio))
                final_y = int(vid_h * float(y_ratio))
                overlay_coord = f"{final_x}:{final_y}"
            else:
                pad = 20
                coord_map = {
                    "top_left": f"{pad}:{pad}",
                    "top_right": f"W-w-{pad}:{pad}",
                    "bottom_left": f"{pad}:H-h-{pad}",
                    "bottom_right": f"W-w-{pad}:H-h-{pad}",
                    "center": "(W-w)/2:(H-h)/2"
                }
                overlay_coord = coord_map.get(position, coord_map["top_right"])

            out_filename = f"Sealed_{uuid.uuid4().hex[:4]}_{video_name}"
            out_path = os.path.join(output_folder, out_filename)

            filter_cmd = (
                f"[1:v]{scale_filter},format=rgba,"
                f"colorchannelmixer=aa={opacity}[wm];"
                f"[0:v][wm]overlay={overlay_coord}"
            )

            cmd = [
                self.ffmpeg_path, "-y",
                "-i", source_path,
                "-i", watermark_path,
                "-filter_complex", filter_cmd,
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "copy",
                out_path
            ]

            status_updater(f"⚙️ Stamping...", "INFO")

            subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, startupinfo=get_startup_info(), timeout=600
            )

            status_updater(f"✅ DONE: {out_filename}", "SUCCESS")

            if "data" not in payload: payload["data"] = {}
            payload["data"]["file_path"] = out_path

            return {"output_name": "success", "payload": payload}

        except Exception as e:
            traceback.print_exc()
            status_updater(f"Error: {str(e)}", "ERROR")
            return {"payload": payload, "output_name": "error"}

    def get_data_preview(self, config: dict):
        return [{"status": "HydroSeal Ready"}]
