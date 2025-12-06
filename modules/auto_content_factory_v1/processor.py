########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\auto_content_factory_v1\processor.py total lines 306 
########################################################################

import os
import sys
import subprocess
import random
import uuid
import shutil
import time
import math
import gc
from flowork_kernel.api_contract import BaseModule, IExecutable
from flowork_kernel.utils.file_helper import sanitize_filename

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

class AutoContentFactoryModule(BaseModule, IExecutable):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.kernel = getattr(self, 'kernel', None)
        self.services = services

        self.ffmpeg_path = None
        self.ffprobe_path = None
        self.temp_root = None

    def _find_ffmpeg_tools(self):
        ffmpeg_exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        ffprobe_exe = "ffprobe.exe" if os.name == "nt" else "ffprobe"
        if self.kernel:
            base = os.path.join(self.kernel.project_root_path, "vendor", "ffmpeg", "bin")
            ff_path = os.path.join(base, ffmpeg_exe)
            fp_path = os.path.join(base, ffprobe_exe)
            if os.path.exists(ff_path):
                return ff_path, fp_path
        return "ffmpeg", "ffprobe"

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):
        if mode == "SIMULATE":
            return {"payload": payload, "output_name": "success"}

        if not self.kernel: self.kernel = self.services.get("kernel")
        if not self.kernel: return self._error("CRITICAL: Kernel missing.", status_updater)
        if not self.temp_root: self.temp_root = os.path.join(self.kernel.data_path, "factory_cache")
        if not self.ffmpeg_path: self.ffmpeg_path, self.ffprobe_path = self._find_ffmpeg_tools()
        if not self.ffmpeg_path: return self._error("FFmpeg not found.", status_updater)

        layer_pairs = config.get("layer_pairs", [])
        output_folder = config.get("output_folder")
        clip_duration = float(config.get("clip_duration", 2))
        do_subs = config.get("add_subtitles", True)
        cleanup = config.get("clear_temp_cache", True)

        if not layer_pairs: return self._error("No Source Layers defined.", status_updater)
        if not output_folder: return self._error("Output folder not set.", status_updater)

        session_id = str(uuid.uuid4())[:8]
        session_root = os.path.join(self.temp_root, session_id)
        shreds_root = os.path.join(session_root, "shreds")
        parts_root = os.path.join(session_root, "parts")
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(shreds_root, exist_ok=True)
        os.makedirs(parts_root, exist_ok=True)

        whisper = None
        if do_subs and FASTER_WHISPER_AVAILABLE:
            status_updater("Fase 0: Loading AI Subtitle Model...", "INFO")
            try:
                whisper = WhisperModel("base", device="auto", compute_type="int8")
            except Exception as e:
                self.logger(f"Failed to load Whisper: {e}", "WARN")

        layer_shred_pools = {}
        layer_audio_sources = {}

        for idx, layer in enumerate(layer_pairs):
            vid_src = layer.get("source")
            aud_src = layer.get("output")

            if not vid_src or not os.path.exists(vid_src): continue
            if not aud_src or not os.path.exists(aud_src): continue

            audios = [os.path.join(aud_src, f) for f in os.listdir(aud_src) if f.lower().endswith(('.mp3','.wav','.m4a'))]
            random.shuffle(audios)
            layer_audio_sources[idx] = audios

            current_shred_folder = os.path.join(shreds_root, f"L{idx}")
            os.makedirs(current_shred_folder, exist_ok=True)
            status_updater(f"Fase 1: Memotong video Layer {idx+1}...", "INFO")

            raw_vids = [f for f in os.listdir(vid_src) if f.lower().endswith(('.mp4','.mov','.mkv','.avi'))]
            for vid in raw_vids:
                in_path = os.path.join(vid_src, vid)
                fname = sanitize_filename(os.path.splitext(vid)[0])
                out_pattern = os.path.join(current_shred_folder, f"{fname}_%03d.mp4")

                subprocess.run([
                    self.ffmpeg_path, "-i", in_path, "-c", "copy", "-map", "0",
                    "-segment_time", str(clip_duration), "-f", "segment", "-reset_timestamps", "1",
                    out_pattern, "-y"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)

            shreds = [os.path.join(current_shred_folder, f) for f in os.listdir(current_shred_folder) if f.endswith(".mp4")]
            random.shuffle(shreds)
            layer_shred_pools[idx] = shreds

            self.logger(f"Layer {idx+1} Ready: {len(audios)} Audios, {len(shreds)} Shreds.", "INFO")
            gc.collect()

        generated_parts_pools = {}

        for idx, audios in layer_audio_sources.items():
            shreds_pool = layer_shred_pools.get(idx, [])
            generated_parts_pools[idx] = []
            layer_part_folder = os.path.join(parts_root, f"L{idx}")
            os.makedirs(layer_part_folder, exist_ok=True)

            status_updater(f"Fase 2: Compositing Layer {idx+1}...", "INFO")

            for aud_path in audios:
                if not shreds_pool:
                    self.logger(f"Layer {idx+1} kehabisan stok video unik. Stop produksi layer ini.", "WARN")
                    break

                dur = self._get_duration(aud_path)
                if dur <= 0: continue

                needed_clips_count = math.ceil(dur / clip_duration)

                if len(shreds_pool) < needed_clips_count:
                    self.logger(f"Layer {idx+1} sisa stok ({len(shreds_pool)}) tidak cukup untuk audio {os.path.basename(aud_path)} (butuh {needed_clips_count}). Skip audio ini.", "WARN")
                    continue

                chosen_clips = []
                for _ in range(needed_clips_count):
                    chosen_clips.append(shreds_pool.pop(0))

                temp_vis = os.path.join(session_root, f"t_vis_{uuid.uuid4()}.mp4")
                self._safe_concat_clips(chosen_clips, temp_vis)

                for used_clip in chosen_clips:
                    try: os.remove(used_clip)
                    except: pass

                part_name = f"part_L{idx}_{uuid.uuid4().hex[:6]}.mp4"
                part_path = os.path.join(layer_part_folder, part_name)

                try:
                    self._render_part_final(temp_vis, aud_path, part_path, dur, config, whisper)
                    if os.path.exists(part_path):
                        generated_parts_pools[idx].append(part_path)
                except Exception as e:
                    self.logger(f"Gagal render part layer {idx+1}: {e}", "ERROR")

                if os.path.exists(temp_vis):
                    try: os.remove(temp_vis)
                    except: pass

                gc.collect()

        counts = [len(pool) for idx, pool in generated_parts_pools.items()]

        if not counts:
            return self._error("Gagal memproduksi part apapun.", status_updater)

        final_qty = min(counts)
        status_updater(f"Fase 3: Merakit {final_qty} Video Final (Mengikuti layer paling sedikit)...", "INFO")

        success_count = 0

        for i in range(final_qty):
            sequence_paths = []
            sorted_layers = sorted(generated_parts_pools.keys())

            for idx in sorted_layers:
                pool = generated_parts_pools[idx]
                rand_idx = random.randint(0, len(pool)-1)
                part_file = pool.pop(rand_idx)
                sequence_paths.append(part_file)

            final_name = f"Story_{i+1}_{uuid.uuid4().hex[:6]}.mp4"
            final_out = os.path.join(output_folder, final_name)

            self._safe_concat_clips(sequence_paths, final_out)

            if os.path.exists(final_out):
                success_count += 1
                status_updater(f"Video Jadi: {final_name}", "INFO")
                for p in sequence_paths:
                    try: os.remove(p)
                    except: pass

        if cleanup:
            status_updater("Fase 4: Membersihkan file sementara...", "INFO")
            try:
                time.sleep(1)
                shutil.rmtree(session_root, ignore_errors=True)
            except Exception as e:
                self.logger(f"Cleanup warning: {e}", "WARN")

        status_updater(f"Selesai! {success_count} Video Unik berhasil dibuat.", "SUCCESS")
        return {"payload": {"count": success_count}, "output_name": "success"}


    def _get_duration(self, path):
        cmd = [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            val = r.stdout.strip()
            return float(val) if val else 0
        except: return 0

    def _safe_concat_clips(self, clips, out):
        list_f = out + ".txt"
        with open(list_f, "w", encoding="utf-8") as f:
            for c in clips:
                safe_path = os.path.abspath(c).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        cmd = [
            self.ffmpeg_path, "-f", "concat", "-safe", "0", "-i", list_f,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
            "-c:a", "aac", "-b:a", "128k",
            "-y", out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try: os.remove(list_f)
        except: pass

    def _render_part_final(self, vid, aud, out, duration, cfg, whisper):
        work_dir = os.path.dirname(os.path.abspath(vid))
        vid_filename = os.path.basename(vid)
        aud_abs = os.path.abspath(aud)
        out_abs = os.path.abspath(out)

        vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        ass_filename = None

        if whisper:
            temp_ass_name = "subs.ass"
            temp_ass_path = os.path.join(work_dir, temp_ass_name)
            if self._gen_ass(aud_abs, whisper, cfg, temp_ass_path):
                ass_filename = temp_ass_name
                vf += f",subtitles='{ass_filename}'"

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", vid_filename,
            "-i", aud_abs,
            "-map", "0:v", "-map", "1:a",
            "-vf", vf,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            "-shortest",
            out_abs
        ]

        subprocess.run(
            cmd, cwd=work_dir,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        )

        if ass_filename:
            try: os.remove(os.path.join(work_dir, ass_filename))
            except: pass

    def _gen_ass(self, aud, model, cfg, out_path):
        try:
            segs, _ = model.transcribe(aud, word_timestamps=True)
            hex_c = cfg.get('subtitle_color', '#FFFF00').replace('#', '')
            if len(hex_c) != 6: hex_c = "FFFF00"
            color = f"&H00{hex_c[4:6]}{hex_c[2:4]}{hex_c[0:2]}".upper()

            header = f"""[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BorderStyle, Outline, Shadow, Alignment, MarginV\nStyle: Default,Arial,60,{color},&H00000000,1,3,0,2,250\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""
            lines = []
            for s in segs:
                if not s.words: continue
                txt = "".join([f"{{\\k{int((w.end-w.start)*100)}}}{w.word.strip()} " for w in s.words])
                def t(s):
                    h,r = divmod(int(s),3600); m,sec=divmod(r,60); cs=int((s-int(s))*100)
                    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"
                lines.append(f"Dialogue: 0,{t(s.start)},{t(s.end)},Default,,0,0,0,,{txt}")

            with open(out_path, "w", encoding="utf-8") as f: f.write(header + "\n".join(lines))
            return True
        except Exception as e:
            self.logger(f"Subtitle Gen Error: {e}", "ERROR")
            return False

    def _error(self, m, u):
        self.logger(m, "ERROR")
        u(m, "ERROR")
        return {"payload": {"error": m}, "output_name": "error"}
