########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\Dynamic Media Stitcher\processor.py total lines 365 
########################################################################

import os
import sys
import subprocess
import json
import math
import time
import random
import shutil
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
from flowork_kernel.utils.file_helper import sanitize_filename
import uuid
import re

def get_startup_info():
    if os.name == 'nt':
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return info
    return None

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

class DynamicMediaStitcherModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.ffmpeg_path, self.ffprobe_path = self._find_ffmpeg_tools()
        self.whisper_model_cache = {}
        self.fonts_path = os.path.join(self.kernel.data_path, "fonts")
        os.makedirs(self.fonts_path, exist_ok=True)
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

    def _find_ffmpeg_tools(self):
        ffmpeg_executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        ffprobe_executable = "ffprobe.exe" if os.name == "nt" else "ffprobe"

        ffmpeg_path = os.path.join(self.kernel.project_root_path, "vendor", "ffmpeg", "bin", ffmpeg_executable)
        ffprobe_path = os.path.join(self.kernel.project_root_path, "vendor", "ffmpeg", "bin", ffprobe_executable)

        if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
            return ffmpeg_path, ffprobe_path

        return "ffmpeg", "ffprobe"

    def execute(
        self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs
    ):
        if mode == "SIMULATE":
            status_updater("Simulating stitch process...", "INFO")
            return {"payload": payload, "output_name": "success"}

        if not self.ffmpeg_path:
            return self.error_payload("FFmpeg not found. Check system installation.")

        job_list = config.get("job_list", [])

        if not job_list:
             v_single = config.get("video_folder")
             if v_single:
                 job_list = [{
                     "video_folder": v_single,
                     "audio_folder": config.get("audio_folder"),
                     "output_folder": config.get("output_folder")
                 }]

        if not job_list:
            return self.error_payload("No jobs configured. Please add items in 'Stitching Jobs Configuration'.")

        duration_ref = config.get("duration_reference", "audio")
        self.process_timeout = config.get("process_timeout", 1200)

        all_results = []
        total_created = 0

        for i, job in enumerate(job_list):
            v_folder = job.get("video_folder")
            a_folder = job.get("audio_folder")
            o_folder = job.get("output_folder")

            job_label = f"Job {i+1}"

            if not v_folder or not a_folder or not o_folder:
                self.logger(f"{job_label} incomplete config, skipping.", "WARN")
                continue

            if not os.path.exists(v_folder):
                self.logger(f"{job_label} Video folder missing: {v_folder}", "WARN")
                continue
            if not os.path.exists(a_folder):
                self.logger(f"{job_label} Audio folder missing: {a_folder}", "WARN")
                continue

            try:
                os.makedirs(o_folder, exist_ok=True)
            except Exception as e:
                self.logger(f"{job_label} Output folder error: {e}", "ERROR")
                continue

            status_updater(f"Processing {job_label}...", "INFO")

            v_files = sorted([os.path.join(v_folder, f) for f in os.listdir(v_folder) if f.lower().endswith((".mp4", ".mov", ".mkv", ".avi", ".webm"))])
            a_files = sorted([os.path.join(a_folder, f) for f in os.listdir(a_folder) if f.lower().endswith((".mp3", ".wav", ".m4a"))])

            if not v_files or not a_files:
                self.logger(f"{job_label} empty folders.", "WARN")
                continue

            if duration_ref == "audio":
                for audio_idx, a_path in enumerate(a_files):
                    status_updater(f"Processing Audio {audio_idx+1}/{len(a_files)}: {os.path.basename(a_path)}", "INFO")
                    try:
                        dur = self._get_duration(a_path)
                        if dur <= 0: continue

                        clips, _ = self._gather_clips(v_files, dur)
                        if not clips: continue

                        temp_vid = os.path.join(self.kernel.data_path, f"t_vid_{uuid.uuid4()}.mp4")
                        self._stitch_video(clips, temp_vid)

                        out_name = f"{sanitize_filename(os.path.splitext(os.path.basename(a_path))[0])}.mp4"
                        final_out = os.path.join(o_folder, out_name)

                        self._merge_final(temp_vid, a_path, final_out, config, status_updater)

                        if os.path.exists(temp_vid): os.remove(temp_vid)

                        for used_clip in clips:
                            try:
                                if os.path.exists(used_clip):
                                    os.remove(used_clip)
                            except Exception as del_err:
                                self.logger(f"Failed to delete clip {used_clip}: {del_err}", "WARN")

                        try:
                            if os.path.exists(a_path):
                                os.remove(a_path)
                        except Exception as del_err:
                             self.logger(f"Failed to delete audio {a_path}: {del_err}", "WARN")

                        total_created += 1
                        all_results.append({"source": a_path, "output": final_out})
                        status_updater(f"Created: {out_name}", "INFO")

                    except Exception as e:
                        import traceback
                        self.logger(f"Error on {os.path.basename(a_path)}: {e}\n{traceback.format_exc()}", "ERROR")

            else: # Video Reference
                 for v_path in v_files:
                    try:
                        dur = self._get_duration(v_path)
                        if dur <= 0: continue

                        clips, _ = self._gather_clips(a_files, dur)
                        if not clips: continue

                        temp_aud = os.path.join(self.kernel.data_path, f"t_aud_{uuid.uuid4()}.mp3")
                        self._stitch_audio(clips, temp_aud)

                        out_name = f"{sanitize_filename(os.path.splitext(os.path.basename(v_path))[0])}.mp4"
                        final_out = os.path.join(o_folder, out_name)

                        self._merge_final(v_path, temp_aud, final_out, config, status_updater, temp_audio=True)

                        if os.path.exists(temp_aud): os.remove(temp_aud)

                        for used_clip in clips:
                            try:
                                if os.path.exists(used_clip):
                                    os.remove(used_clip)
                            except: pass
                        try:
                            if os.path.exists(v_path):
                                os.remove(v_path)
                        except: pass

                        total_created += 1
                        all_results.append({"source": v_path, "output": final_out})

                    except Exception as e:
                        import traceback
                        self.logger(f"Error on {os.path.basename(v_path)}: {e}\n{traceback.format_exc()}", "ERROR")

        status_updater(f"Completed. {total_created} videos created.", "SUCCESS")

        if "data" not in payload: payload["data"] = {}
        payload["data"]["stitcher_results"] = all_results
        payload["data"]["total_videos_created"] = total_created

        return {"payload": payload, "output_name": "success"}

    def _get_duration(self, p):
        if not self.ffprobe_path: return 0
        cmd = [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", p]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=get_startup_info())
            return float(res.stdout.strip())
        except: return 0

    def _gather_clips(self, pool, target):
        used = []
        curr = 0
        local_pool = pool.copy()
        random.shuffle(local_pool)

        attempts = 0
        max_attempts = len(pool) * 3

        while curr < target and attempts < max_attempts:
            if not local_pool:
                local_pool = pool.copy()
                random.shuffle(local_pool)
            clip = local_pool.pop(0)
            attempts += 1
            dur = self._get_duration(clip)
            if dur > 0:
                used.append(clip)
                curr += dur
        return used, curr

    def _stitch_video(self, clips, out):
        list_f = os.path.join(self.kernel.data_path, f"l_{uuid.uuid4()}.txt")

        with open(list_f, "w", encoding="utf-8") as f:
            for c in clips:
                safe_path = os.path.abspath(c).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        subprocess.run([self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", list_f, "-c", "copy", out],
                       check=True, timeout=self.process_timeout, startupinfo=get_startup_info())
        os.remove(list_f)

    def _stitch_audio(self, clips, out):
        self._stitch_video(clips, out)

    def _merge_final(self, vid, aud, out, cfg, updater, temp_audio=False):
        cmd = [self.ffmpeg_path, "-y", "-i", vid, "-i", aud, "-map", "0:v", "-map", "1:a", "-shortest"]

        vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"

        if cfg.get("add_subtitles", True):
            try:
                model = self._get_whisper_model(cfg.get("subtitle_model_size", "base"), updater)
                ass = self._gen_ass(aud, model, cfg)
                if ass:
                     safe_ass = ass.replace("\\", "/").replace(":", "\\:")
                     vf += f",subtitles='{safe_ass}'"
            except Exception as e:
                self.logger(f"Subtitle generation skipped/failed: {e}", "WARN")

        cmd.extend(["-vf", vf, "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-r", "30", out])
        subprocess.run(cmd, check=True, timeout=self.process_timeout, startupinfo=get_startup_info())

    def _get_whisper_model(self, size, updater):
        if size in self.whisper_model_cache: return self.whisper_model_cache[size]
        if not FASTER_WHISPER_AVAILABLE:
            raise Exception("faster-whisper library not installed. Please run 'pip install faster-whisper'")
        updater("Loading AI...", "INFO")
        m = WhisperModel(size, device="auto", compute_type="int8")
        self.whisper_model_cache[size] = m
        return m

    def _gen_ass(self, aud, model, cfg):
        segments, _ = model.transcribe(aud, language="id", word_timestamps=True)

        correction_map = {}
        dict_str = cfg.get("correction_dictionary", "")
        if dict_str:
            for line in dict_str.split("\n"):
                if ":" in line:
                    w, c = line.split(":", 1)
                    correction_map[w.strip().lower()] = c.strip()

        font = cfg.get("subtitle_font", "Arial")

        try:
            raw_size = cfg.get("subtitle_font_size", 40)
            size = int(raw_size)
        except:
            size = 40

        self.logger(f"Generating ASS: Font={font}, Size={size}", "INFO")

        def clean_hex(h):
            if not h: return "&H00FFFFFF"
            h = str(h).lstrip("#")
            if len(h) < 6: return "&H00FFFFFF"
            return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()

        p_color = clean_hex(cfg.get("subtitle_primary_color", "#FFFFFF"))
        s_color = clean_hex(cfg.get("subtitle_secondary_color", "#FFFF00"))
        border = 1 if cfg.get("subtitle_style") != "Default" else 0


        header = [
            "[Script Info]",
            "Title: Flowork",
            "ScriptType: v4.00+",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "",
            "[V4+ Styles]",
            f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{font},{size},{p_color},{s_color},&H00000000,&H00000000,0,0,0,0,100,100,0,0,{border},{border},{border},2,50,50,550,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        events = []
        for seg in segments:
            if not getattr(seg, 'words', None): continue
            line = []
            for w in seg.words:
                clean = re.sub(r"^\W+|\W+$", "", w.word.strip())
                if clean.lower() in correction_map:
                    clean = correction_map[clean.lower()]

                k_dur = int((w.end - w.start) * 100)
                line.append(f"{{\\k{k_dur}}}{clean} ")

            def fmt(s):
                h, r = divmod(int(s), 3600)
                m, sec = divmod(r, 60)
                cs = int((s - int(s)) * 100)
                return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"

            events.append(f"Dialogue: 0,{fmt(seg.start)},{fmt(seg.end)},Default,,0,0,0,,{''.join(line)}")

        ass_file = os.path.join(self.kernel.data_path, f"{uuid.uuid4()}.ass")
        with open(ass_file, "w", encoding="utf-8") as f: f.write("\n".join(header + events))
        return ass_file

    def error_payload(self, msg):
        self.logger(msg, "ERROR")
        return {"payload": {"data": {"error": msg}}, "output_name": "error"}

    def get_data_preview(self, config):
        return [{"status": "preview_not_available"}]
