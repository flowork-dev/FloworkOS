########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\golden_moment_clipper\backend\app_service.py total lines 510 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import uuid
import shutil
import re
import traceback
import subprocess
import time
import importlib
import threading
import textwrap # [NEW] Untuk auto newline judul
from pathlib import Path

from flowork_kernel.services.base_app_service import BaseAppService

WhisperModel = None
mp_face = None
cv2 = None

class GoldenMomentService(BaseAppService):
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.name = "Golden Moment Studio"
        self.ffmpeg_path, self.ffprobe_path = self._find_ffmpeg_tools()
        self.active_jobs = {}
        self.whisper_cache = {}

        self.muscle = self.kernel.get_service("app_runtime")
        if self.muscle:
            self.logger.info("🎬 [Bridge] Connected to Muscle.")

    def _find_ffmpeg_tools(self):
        return shutil.which("ffmpeg") or "ffmpeg", shutil.which("ffprobe") or "ffprobe"


    def _detect_real_user(self):
        """Helper: Cari folder user asli kalau terjebak di system"""
        try:
            data_root = Path("/app/data/users")
            if not data_root.exists(): data_root = Path(os.getcwd()) / "data" / "users"

            if data_root.exists():
                for entry in os.scandir(data_root):
                    if entry.is_dir() and entry.name != "system":
                        return entry.name
        except: pass
        return "system"

    def _smart_resolve_path(self, path_str, user_id):
        """Logic Path Resolver 'Brutal' ala Downloader"""

        if user_id in ["system", "None", None, ""]:
            real_id = self._detect_real_user()
            if real_id != "system": user_id = real_id

        if hasattr(self, 'get_user_data_path'):
            user_root = Path(self.get_user_data_path(user_id))
        else:
            user_root = Path("/app/data/users") / user_id

        if not path_str: return user_root

        path_str = str(path_str).replace("\\", "/").strip()
        if "/users/system" in path_str:
            path_str = path_str.replace("/users/system", f"/users/{user_id}")

        if path_str.startswith(f"/app/data/users/{user_id}"):
            return Path(path_str)

        system_prefix = "/app/data/users/system"
        if path_str.startswith(system_prefix):
            relative_part = path_str[len(system_prefix):].lstrip("/")
            return user_root / relative_part

        user_prefix = f"/app/data/users/{user_id}"
        if path_str.startswith(user_prefix):
            return Path(path_str)

        clean_rel = path_str.lstrip("/")
        return user_root / clean_rel

    def _broadcast_log(self, message, user_id, level="INFO"):
        try:
            print(f"[{level}] [GoldenMoment] {message}", flush=True)
            if hasattr(self.kernel, 'event_bus'):
                self.kernel.event_bus.publish("APP_LOG_STREAM", {
                    "app_id": "golden_moment_clipper",
                    "message": message,
                    "level": level,
                    "timestamp": time.time(),
                    "_target_user_id": user_id
                })
        except: pass

    def list_directory(self, path: str, user_id: str):
        try:
            target_path = self._smart_resolve_path(path, user_id)

            if not target_path.exists() and "users" in str(target_path):
                try: target_path.mkdir(parents=True, exist_ok=True)
                except: pass

            if not target_path.exists():
                return {"status": "error", "error": "Directory not found"}

            items = []
            user_root = self._smart_resolve_path("", user_id)
            if str(target_path.as_posix()) != str(user_root.as_posix()):
                items.append({
                    "name": "..",
                    "path": str(target_path.parent.as_posix()),
                    "type": "folder",
                    "icon": "mdi-arrow-up-bold"
                })

            for entry in os.scandir(target_path):
                is_dir = entry.is_dir()
                icon = "mdi-folder" if is_dir else "mdi-file-video"

                if not is_dir:
                    ext = entry.name.split('.')[-1].lower() if '.' in entry.name else ""
                    if ext in ['mp4', 'mov', 'avi', 'mkv']: icon = "mdi-movie-play"
                    elif ext in ['jpg', 'png', 'jpeg']: icon = "mdi-image"
                    else: icon = "mdi-file-document-outline"

                items.append({
                    "name": entry.name,
                    "path": str(Path(entry.path).as_posix()),
                    "type": "folder" if is_dir else "file",
                    "icon": icon,
                    "size": entry.stat().st_size if entry.is_file() else 0
                })

            return {
                "status": "success",
                "data": items,
                "items": items,
                "current_path": str(target_path.as_posix())
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


    def _ensure_dependencies(self, job_id, user_id="system"):
        global WhisperModel, mp_face, cv2
        if WhisperModel and mp_face and cv2: return True

        self.log_job(job_id, "⚙️ Checking AI Dependencies (Legacy Mode)...", "info", user_id)

        need_reinstall = False
        try:
            import av
            import faster_whisper
            import mediapipe
            _ = mediapipe.solutions.face_detection
        except (ImportError, AttributeError, RuntimeError):
            need_reinstall = True
            self.log_job(job_id, "⚠️ Library incompatibility detected. Updating...", "warn", user_id)

        if need_reinstall:
            try:
                pkgs_del = ["av", "faster-whisper", "mediapipe", "protobuf"]
                subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y"] + pkgs_del, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                cmds = [
                    "protobuf==3.20.3",
                    "mediapipe==0.10.9",
                    "faster-whisper>=1.0.0",
                    "opencv-python-headless",
                    "numpy<2.0.0"
                ]

                for c in cmds:
                    self.log_job(job_id, f"📦 Installing: {c}...", "info", user_id)
                    subprocess.check_call([sys.executable, "-m", "pip", "install", c], stdout=subprocess.DEVNULL)

                importlib.invalidate_caches()
            except Exception as e:
                self.log_job(job_id, f"❌ Install Failed: {e}", "error", user_id)
                return False

        try:
            for m in ['av', 'faster_whisper', 'mediapipe', 'google.protobuf']:
                if m in sys.modules: del sys.modules[m]

            import faster_whisper
            WhisperModel = faster_whisper.WhisperModel
            import cv2 as cv2_lib
            cv2 = cv2_lib
            import mediapipe as mp
            mp_face = mp.solutions.face_detection

            self.log_job(job_id, "🚀 AI Engine Loaded!", "success", user_id)
            return True
        except Exception as e:
            self.log_job(job_id, f"❌ Load Error: {e}", "error", user_id)
            traceback.print_exc()
            return False

    def init_job(self, user_id):
        job_id = uuid.uuid4().hex[:8]
        self.active_jobs[job_id] = {"status": "running", "user_id": user_id, "logs": [], "created_at": time.time()}
        return job_id

    def log_job(self, job_id, msg, type="info", user_id=None):
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["logs"].append({"msg": msg, "type": type})
            if not user_id: user_id = self.active_jobs[job_id].get("user_id", "system")

        if not user_id: user_id = "system"
        self._broadcast_log(msg, user_id, type.upper())

    def get_job_status(self, job_id):
        if job_id not in self.active_jobs: return {"status": "unknown"}
        job = self.active_jobs[job_id]
        logs = list(job["logs"])
        job["logs"] = []
        return {"status": job["status"], "logs": logs}

    def run_process_safe(self, job_id, config, user_id):
        if user_id in ["system", "None", None, ""]:
            real = self._detect_real_user()
            if real != "system":
                user_id = real
                if job_id in self.active_jobs: self.active_jobs[job_id]["user_id"] = real

        if self.muscle:
            try:
                self.log_job(job_id, "💪 [Bridge] Delegating job to Muscle...", "info", user_id)
                res = self.muscle.execute_app(
                    app_id="golden_moment_clipper",
                    action="process",
                    params=config,
                    user_id=user_id
                )
                if res.get("status") == "success":
                    self.log_job(job_id, f"✅ Muscle Started (PID: {res.get('pid')})", "success", user_id)
                    self.active_jobs[job_id]["status"] = "completed"
                    return
                else:
                    self.log_job(job_id, f"⚠️ Muscle Failed: {res.get('error')}. Fallback to Resident.", "warn", user_id)
            except Exception as e:
                self.log_job(job_id, f"⚠️ Bridge Error: {e}. Fallback.", "warn", user_id)

        try:
            self.process_video_logic(job_id, config, user_id)
            self.active_jobs[job_id]["status"] = "completed"
            self.log_job(job_id, "✅ All Batch Tasks Completed (Resident Mode).", "success", user_id)

            if hasattr(self.kernel, 'event_bus'):
                self.kernel.event_bus.publish("APP_JOB_FINISHED", {
                    "app_id": "golden_moment_clipper",
                    "pid": job_id,
                    "status": "completed",
                    "user_id": user_id
                })

        except Exception as e:
            traceback.print_exc()
            self.active_jobs[job_id]["status"] = "failed"
            self.log_job(job_id, f"❌ CRITICAL ERROR: {str(e)}", "error", user_id)

    def process_video_logic(self, job_id, config, user_id):
        if not self._ensure_dependencies(job_id, user_id): raise Exception("Dependency Error")

        input_path_raw = config.get("input_folder_path")
        output_folder_base = config.get("output_folder")
        outro_path = config.get("outro_path")

        resolved_input = self._smart_resolve_path(input_path_raw, user_id)
        resolved_output = self._smart_resolve_path(output_folder_base, user_id)

        if not os.path.exists(resolved_input):
            try: resolved_input.mkdir(parents=True, exist_ok=True)
            except: pass
            if not os.path.exists(resolved_input):
                raise Exception(f"Input path invalid: {resolved_input}")


        videos = []
        if os.path.isfile(resolved_input):
            videos = [str(resolved_input)]
            self.log_job(job_id, "📂 Mode: Single File Processing", "info", user_id)
        else:
            files = [f for f in os.listdir(resolved_input) if f.lower().endswith(('.mp4','.mov','.avi','.mkv'))]
            files.sort()
            videos = [os.path.join(resolved_input, f) for f in files]
            self.log_job(job_id, f"📂 Mode: Batch Folder ({len(videos)} videos)", "info", user_id)

        if not videos: raise Exception("No videos found.")
        if not os.path.exists(resolved_output): os.makedirs(resolved_output, exist_ok=True)

        timestamps_raw = config.get("timestamps", "")
        tasks = {}

        for line in timestamps_raw.split('\n'):
            line = line.strip()
            if not line: continue
            parts = line.split('|')
            time_part = parts[0].strip()
            vid_id = parts[1].strip() if len(parts) >= 2 else "1"
            clip_title = parts[2].strip() if len(parts) >= 3 else ""

            t_parts = time_part.split('-')
            if len(t_parts) == 2:
                s = self._parse_time(t_parts[0].strip())
                e = self._parse_time(t_parts[1].strip())
                if s is not None and e is not None:
                    if vid_id not in tasks: tasks[vid_id] = []
                    tasks[vid_id].append((s, e, clip_title)) # Simpan judul

        if not tasks: raise Exception("No valid timestamps found.")

        final_outro = None
        if outro_path:
            resolved_outro = self._smart_resolve_path(outro_path, user_id)
            if os.path.exists(resolved_outro):
                self.log_job(job_id, "Standardizing Outro...", "info", user_id)
                temp_outro_dir = os.path.join(resolved_output, "temp_global")
                os.makedirs(temp_outro_dir, exist_ok=True)
                final_outro = os.path.join(temp_outro_dir, "ready_outro.mp4")
                self._normalize_video(str(resolved_outro), final_outro)

        for idx, vid_path in enumerate(videos, 1):
            vid_id_str = str(idx)
            vid_name = os.path.basename(vid_path)
            if vid_id_str not in tasks:
                if len(videos) > 1: self.log_job(job_id, f"⏭️ Skipping {vid_name}", "warn", user_id)
                continue

            segments = tasks[vid_id_str]
            self.log_job(job_id, f"🎬 Video {idx} ({vid_name}) - {len(segments)} segments", "info", user_id)
            current_output_folder = os.path.join(resolved_output, vid_id_str)
            os.makedirs(current_output_folder, exist_ok=True)

            temp_dir = os.path.join(current_output_folder, f"temp_{uuid.uuid4().hex[:4]}")
            os.makedirs(temp_dir, exist_ok=True)
            processed_clips = []

            try:
                total_dur = self._get_duration(vid_path)
                for i, (start, end, title) in enumerate(segments):
                    if start >= total_dur: continue
                    actual_end = min(end, total_dur)
                    if config.get("smart_cut_mode", True):
                        actual_end = self._smart_adjust(vid_path, start, actual_end, temp_dir, config.get("whisper_model", "small"))

                    dur = actual_end - start
                    if dur <= 1: continue

                    base = f"clip_{i+1}_{uuid.uuid4().hex[:4]}"
                    raw = os.path.join(temp_dir, f"raw_{base}.mp4")
                    work = raw
                    final = os.path.join(temp_dir, f"{base}.mp4")

                    self._cut_video(vid_path, start, dur, raw)
                    if config.get("remove_silence", False):
                        jump = os.path.join(temp_dir, f"jump_{base}.mp4")
                        if self._silence_remove(raw, jump): work = jump

                    ass = None
                    if config.get("add_subtitles", True):
                        try:
                            ass = os.path.join(temp_dir, f"{base}.ass")
                            self._gen_subs(work, ass, config.get("whisper_model", "small"), has_title=bool(title))
                        except: pass

                    self.log_job(job_id, f"   > Rendering Clip {i+1}...", "info", user_id)
                    self._ffmpeg_render(work, final, config.get("resize_mode", "podcast_split"), config.get("watermark_text", ""), ass, None, title=title)

                    if not config.get("merge_clips", False) and final_outro:
                        with_outro = os.path.join(temp_dir, f"outro_{base}.mp4")
                        self._concat_smart([final, final_outro], with_outro)
                        final = with_outro

                    if os.path.exists(final): processed_clips.append(final)

                if config.get("merge_clips", False) and processed_clips:
                    if final_outro: processed_clips.append(final_outro)
                    merged_name = f"FullSequence_{vid_id_str}.mp4"
                    merged_path = os.path.join(current_output_folder, merged_name)
                    self._concat_smart(processed_clips, merged_path)
                else:
                    for p in processed_clips:
                        if p == final_outro: continue
                        dst = os.path.join(current_output_folder, os.path.basename(p))
                        if os.path.exists(dst): os.remove(dst)
                        shutil.move(p, dst)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_time(self, t):
        try:
            p = t.split(':')
            if len(p)==2: return int(p[0])*60 + int(p[1])
            if len(p)==3: return int(p[0])*3600 + int(p[1])*60 + int(p[2])
        except: return None

    def _get_duration(self, f):
        try:
            res = subprocess.run([self.ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f], capture_output=True, text=True)
            return float(res.stdout.strip())
        except: return 5.0

    def _cut_video(self, inp, start, dur, out):
        subprocess.run([self.ffmpeg_path, '-y', '-ss', str(start), '-i', inp, '-t', str(dur), '-c', 'copy', out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _normalize_video(self, inp, out):
        cmd = [
            self.ffmpeg_path, '-y', '-i', inp,
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
            '-r', '30', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', '-ar', '44100', '-ac', '2',
            out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _concat_smart(self, clips, out):
        lst = f"list_{uuid.uuid4().hex}.txt"
        with open(lst, 'w') as f:
            for c in clips: f.write(f"file '{os.path.abspath(c)}'\n")
        cmd_copy = [self.ffmpeg_path, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out]
        ret = subprocess.run(cmd_copy, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ret.returncode != 0:
            cmd_enc = [self.ffmpeg_path, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'libx264', '-c:a', 'aac', out]
            subprocess.run(cmd_enc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(lst)

    def _smart_adjust(self, inp, start, end, tmp, model_sz):
        try:
            check_dur = (end - start) + 15
            aud = os.path.join(tmp, f"seek_{uuid.uuid4().hex}.mp3")
            subprocess.run([self.ffmpeg_path, '-y', '-ss', str(start), '-i', inp, '-t', str(check_dur), '-vn', '-acodec', 'libmp3lame', '-q:a', '2', aud], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if model_sz not in self.whisper_cache: self.whisper_cache[model_sz] = WhisperModel(model_sz, device="cpu", compute_type="int8")
            segments, _ = self.whisper_cache[model_sz].transcribe(aud, word_timestamps=True)
            target, best, min_diff = end - start, end, 999
            for s in segments:
                for w in s.words:
                    if w.word.strip()[-1] in '.!?':
                        diff = abs(w.end - target)
                        if diff < min_diff: min_diff, best = diff, start + w.end + 0.2
            os.remove(aud)
            return best
        except: return end

    def _silence_remove(self, inp, out): return False

    def _gen_subs(self, inp, out, model_sz, has_title=False):
        aud = inp.replace(".mp4", ".mp3")
        subprocess.run([self.ffmpeg_path, '-y', '-i', inp, '-vn', '-acodec', 'libmp3lame', aud], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if model_sz not in self.whisper_cache: self.whisper_cache[model_sz] = WhisperModel(model_sz, device="cpu", compute_type="int8")
        segments, _ = self.whisper_cache[model_sz].transcribe(aud, word_timestamps=True)

        margin_v = 730 if has_title else 250

        header = f"""[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,65,&H0000FFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,135,135,{margin_v},1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""
        with open(out, "w", encoding="utf-8") as f:
            f.write(header)
            for s in segments:
                for w in s.words:
                    h1,m1,s1,cs1 = self._time_parts(w.start)
                    h2,m2,s2,cs2 = self._time_parts(w.end)
                    k = int((w.end - w.start)*100)
                    f.write(f"Dialogue: 0,{h1}:{m1:02d}:{s1:02d}.{cs1:02d},{h2}:{m2:02d}:{s2:02d}.{cs2:02d},Default,,0,0,0,,{{\\k{k}}}{w.word.strip()}\n")
        if os.path.exists(aud): os.remove(aud)

    def _time_parts(self, s): return int(s//3600), int((s%3600)//60), int(s%60), int((s%1)*100)

    def _ffmpeg_render(self, inp, out, mode, wm, ass, crop, title=""):
        vf = []
        if mode == "podcast_split":
            m = 20
            vf.append(f"[0:v]crop=w=iw-{2*m}:h=ih-{2*m}:x={m}:y={m},split=2[c1][c2]")
            vf.append(f"[c1]crop=w='min(iw, ih*1.125)':h=ih:x=0:y=0[top]")
            vf.append(f"[c2]crop=w='min(iw, ih*1.125)':h=ih:x='iw-ow':y=0[bottom]")
            vf.append(f"[top][bottom]vstack=inputs=2,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg]")
        else:
            vf.append(f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg]")

        last = "[bg]"

        if title:
            vf.append(f"{last}drawbox=y=ih-200-(ih/4):h=ih/4:w=iw:color=red@0.85:t=fill[boxed]")

            clean_title = title.replace(":", "\\:").replace("'", "").upper()
            wrapped_title = "\\\n".join(textwrap.wrap(clean_title, width=20))

            char_count = len(clean_title)
            base_size = 75 if char_count < 20 else (60 if char_count < 40 else 45)

            vf.append(f"[boxed]drawtext=text='{wrapped_title}':fontcolor=white:fontsize={base_size}:font='Arial-Bold':x=(w-text_w)/2:y=h-200-(h/4)+((h/4)-text_h)/2[titled]")
            last = "[titled]"

        if wm:
            clean_wm = wm.replace(":", "\\:").replace("'", "")
            vf.append(f"{last}drawtext=text='{clean_wm}':fontcolor=white:alpha=0.5:fontsize=40:x=(w-text_w)/2:y=h-200-(h/4)-th-15[wm]")
            last = "[wm]"

        if ass and os.path.exists(ass):
            escaped_ass = ass.replace("\\", "/").replace(":", "\\:")
            vf.append(f"{last}subtitles='{escaped_ass}'[fin]")
            last = "[fin]"

        cmd = [self.ffmpeg_path, '-y', '-i', inp, '-filter_complex', ";".join(vf), '-map', last, '-map', '0:a', '-r', '30', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', '-ar', '44100', '-ac', '2', out]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
