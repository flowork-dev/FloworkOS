########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\golden_moment_clipper\processor.py total lines 619 
########################################################################

import os
import sys
import subprocess
import uuid
import shutil
import re
import traceback
import json
import math
import numpy as np
from flowork_kernel.api_contract import BaseModule, IExecutable

print("--- [GoldenMoment] ATTEMPTING IMPORTS ---", file=sys.stderr)
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("❌ [GoldenMoment] Faster-Whisper NOT FOUND.", file=sys.stderr)

try:
    import cv2
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("❌ [GoldenMoment] MediaPipe/OpenCV NOT FOUND.", file=sys.stderr)

class GoldenMomentClipper(BaseModule, IExecutable):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.kernel = services.get("kernel")
        self.ffmpeg_path, self.ffprobe_path = self._find_ffmpeg_tools()
        self.whisper_cache = {}

    def _find_ffmpeg_tools(self):
        return shutil.which("ffmpeg") or "ffmpeg", shutil.which("ffprobe") or "ffprobe"

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):
        if mode == "SIMULATE":
            return {"payload": payload, "output_name": "success"}


        input_folder_path = config.get("input_folder_path")

        timestamps_raw = config.get("timestamps", "")
        resize_mode = config.get("resize_mode", "podcast_split")
        safety_margin = int(config.get("safety_margin", 20))

        whisper_model_size = config.get("whisper_model", "small")
        do_smart_cut = config.get("smart_cut_mode", True)

        do_remove_silence = config.get("remove_silence", False)
        silence_db_val = int(config.get("silence_threshold", 30))
        silence_db = f"-{silence_db_val}dB"

        do_subs = config.get("add_subtitles", True)
        sub_size = int(config.get("subtitle_size", 65))

        watermark_text = config.get("watermark_text", "MADE WITH FLOWORK")
        watermark_size = int(config.get("watermark_size", 45))

        enable_outro = config.get("enable_outro", False)
        closing_video = config.get("closing_video_path")

        do_merge = config.get("merge_clips", True)
        out_folder = config.get("output_folder")


        if not input_folder_path or not os.path.exists(input_folder_path):
            return self._error("Input Folder not found!", status_updater)

        if not out_folder:
            return self._error("Output folder not specified!", status_updater)

        valid_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        source_videos = []
        try:
            for f in os.listdir(input_folder_path):
                if f.lower().endswith(valid_extensions):
                    source_videos.append(os.path.join(input_folder_path, f))
        except Exception as e:
            return self._error(f"Error scanning folder: {str(e)}", status_updater)

        if not source_videos:
             return self._error(f"No valid video files found in {input_folder_path}", status_updater)

        status_updater(f"📂 Found {len(source_videos)} video files to process.", "INFO")

        segments = []
        for line in timestamps_raw.split('\n'):
            line = line.strip()
            if not line: continue
            parts = line.split('-')
            if len(parts) == 2:
                start = self._parse_time(parts[0].strip())
                end = self._parse_time(parts[1].strip())
                if start is not None and end is not None:
                    segments.append((start, end))

        if not segments:
            return self._error("No valid timestamps found!", status_updater)

        processed_clips = []
        session_id = uuid.uuid4().hex[:6]
        temp_dir = os.path.join(out_folder, f"temp_{session_id}")
        os.makedirs(temp_dir, exist_ok=True)

        try:

            normalized_outro_path = None
            if enable_outro and closing_video and os.path.exists(closing_video):
                status_updater("🛠️ Normalizing Outro (Forcing Format)...", "INFO")
                normalized_outro_path = os.path.join(temp_dir, "normalized_outro.mp4")

                is_ok = self._force_normalize_video(closing_video, normalized_outro_path)
                if not is_ok:
                    status_updater("⚠️ Gagal normalize outro. Outro dilewati.", "WARNING")
                    normalized_outro_path = None

            global_clip_index = 0
            for vid_idx, input_video in enumerate(source_videos):
                video_name = os.path.basename(input_video)
                status_updater(f"🎬 Processing Video {vid_idx+1}/{len(source_videos)}: {video_name}", "INFO")

                total_dur = self._get_exact_duration(input_video)

                for i, (start, end) in enumerate(segments):
                    global_clip_index += 1

                    if start >= total_dur:
                        status_updater(f"⚠️ Timestamp {start}s exceeds duration of {video_name}. Skipping.", "WARNING")
                        continue

                    actual_end = end
                    if actual_end > total_dur:
                        actual_end = total_dur
                        status_updater(f"⚠️ End time capped to video duration for {video_name}.", "WARNING")

                    if do_smart_cut and FASTER_WHISPER_AVAILABLE:
                        status_updater(f"[Clip {global_clip_index}] 🎯 Sniper Mode: Hunting nearest DOT...", "INFO")
                        new_end = self._smart_adjust_timestamps(
                            input_video, start, actual_end, temp_dir,
                            status_updater, whisper_model_size
                        )
                        if new_end != actual_end:
                            actual_end = new_end
                            status_updater(f"[Clip {global_clip_index}] ✅ Dot Found! Shifted end.", "INFO")
                        else:
                            status_updater(f"[Clip {global_clip_index}] ⚠️ No dot found. Keeping original.", "INFO")

                    duration = actual_end - start
                    if duration <= 1: continue # Skip ultra short clips

                    clip_base = f"batch_{vid_idx}_{i+1}_{uuid.uuid4().hex[:4]}"
                    raw_clip_path = os.path.join(temp_dir, f"raw_{clip_base}.mp4")
                    working_clip_path = raw_clip_path
                    final_clip_path = os.path.join(temp_dir, f"final_{clip_base}.mp4")

                    status_updater(f"[Clip {global_clip_index}] Cutting Video...", "INFO")
                    self._cut_video(input_video, start, duration, raw_clip_path)

                    if do_remove_silence:
                        status_updater(f"[Clip {global_clip_index}] Removing Silence...", "INFO")
                        jump_cut_path = os.path.join(temp_dir, f"jump_{clip_base}.mp4")
                        if self._remove_silence(raw_clip_path, jump_cut_path, silence_db):
                            working_clip_path = jump_cut_path
                            status_updater(f"[Clip {global_clip_index}] Jump Cut Applied.", "INFO")

                    status_updater(f"[Clip {global_clip_index}] Processing Visuals...", "INFO")

                    ass_path = None
                    if do_subs and FASTER_WHISPER_AVAILABLE:
                        try:
                            ass_path = os.path.join(temp_dir, f"{clip_base}.ass")
                            self._generate_original_style_ass(working_clip_path, ass_path, sub_size, whisper_model_size)
                        except: ass_path = None

                    crop_expr = None
                    if MEDIAPIPE_AVAILABLE:
                        if resize_mode == "face_jump":
                            status_updater(f"[Clip {global_clip_index}] 🤖 AI Analyzing: Face Jump...", "INFO")
                            crop_expr = self._analyze_face_jump_3s(working_clip_path)
                        elif resize_mode == "mouse_smooth":
                            status_updater(f"[Clip {global_clip_index}] 🖱️ AI Analyzing: Mouse Smooth...", "INFO")
                            crop_expr = self._analyze_mouse_smooth(working_clip_path)

                    self._apply_ffmpeg_processing(
                        working_clip_path, final_clip_path, resize_mode,
                        safety_margin, watermark_text, watermark_size,
                        ass_path, crop_expr
                    )

                    if normalized_outro_path and not do_merge:
                        status_updater(f"[Clip {global_clip_index}] Attaching Outro (Safe Mode)...", "INFO")
                        temp_with_outro = os.path.join(temp_dir, f"outro_{clip_base}.mp4")

                        success = self._concat_safe(final_clip_path, normalized_outro_path, temp_with_outro)
                        if success:
                            if os.path.exists(final_clip_path): os.remove(final_clip_path)
                            os.rename(temp_with_outro, final_clip_path)

                    if os.path.exists(final_clip_path):
                        processed_clips.append(final_clip_path)

            final_output = ""
            if do_merge and len(processed_clips) > 0:
                if normalized_outro_path:
                    status_updater("Appending Unified Outro...", "INFO")
                    processed_clips.append(normalized_outro_path)

                status_updater("Merging all clips from ALL videos...", "INFO")
                merged_name = f"GoldenMoment_Batch_{session_id}.mp4"
                merged_path = os.path.join(out_folder, merged_name)
                self._merge_videos(processed_clips, merged_path)
                final_output = merged_path
            else:
                final_output = out_folder
                for p in processed_clips:
                    dst = os.path.join(out_folder, os.path.basename(p))
                    if os.path.exists(p):
                        if os.path.exists(dst): os.remove(dst)
                        shutil.move(p, dst)

            try: shutil.rmtree(temp_dir, ignore_errors=True)
            except: pass

            status_updater("✅ All Batch Processing Done!", "SUCCESS")
            return {"payload": {"data": {"output_path": final_output}}, "output_name": "success"}

        except Exception as e:
            traceback.print_exc()
            return self._error(f"Processing Failed: {str(e)}", status_updater)

    def _force_normalize_video(self, input_path, output_path):
        """
        [THE EQUALIZER]
        Memaksa video jadi standar baku:
        - Res: 1080x1920 (Portrait)
        - FPS: 30 (Wajib sama!)
        - Audio: 44100 Hz AAC
        """
        try:
            has_audio = self._has_audio(input_path)
            duration = self._get_exact_duration(input_path)

            vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"

            cmd = [self.ffmpeg_path, '-y', '-i', input_path]

            if not has_audio:
                cmd += ['-f', 'lavfi', '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100:d={duration}']
                cmd += ['-map', '0:v', '-map', '1:a']
                cmd += ['-shortest']
            else:
                cmd += ['-map', '0:v', '-map', '0:a']

            cmd += [
                '-vf', vf,
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
                '-c:a', 'aac', '-ar', '44100',
                output_path
            ]

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ [Normalize Error]: {e.stderr.decode()}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ [Normalize Exception]: {str(e)}", file=sys.stderr)
            return False

    def _concat_safe(self, v1, v2, output_path):
        try:
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', v1, '-i', v2,
                '-filter_complex', '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]',
                '-map', '[outv]', '-map', '[outa]',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
                '-c:a', 'aac',
                output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ [Concat Error]: {e.stderr.decode()}", file=sys.stderr)
            return False

    def _apply_ffmpeg_processing(self, input_path, output_path, mode, margin, wm_text, wm_size, ass_path, crop_expr=None):
        has_audio = self._has_audio(input_path)
        dur = self._get_exact_duration(input_path)

        layout_filter = ""
        if mode == "podcast_split":
            layout_filter = (
                f"[0:v]crop=w=iw-{2*margin}:h=ih-{2*margin}:x={margin}:y={margin}[clean];"
                f"[clean]split=2[c1][c2];"
                f"[c1]crop=w='min(iw, ih*1.125)':h=ih:x=0:y=0[top];"
                f"[c2]crop=w='min(iw, ih*1.125)':h=ih:x='iw-ow':y=0[bottom];"
                f"[top][bottom]vstack=inputs=2[vstacked];"
                f"[vstacked]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg]"
            )
        elif mode == "crop":
            layout_filter = (
                f"[0:v]crop=w=iw-{2*margin}:h=ih-{2*margin}:x={margin}:y={margin}[clean];"
                f"[clean]crop='ih*(9/16)':ih,scale=1080:1920,setsar=1[bg]"
            )
        elif mode in ["face_jump", "mouse_smooth"]:
            if not crop_expr: crop_expr = "(iw-ow)/2"
            layout_filter = (
                f"[0:v]crop=w='min(iw, ih*(9/16))':h=ih:x='{crop_expr}':y=0[cropped];"
                f"[cropped]scale=1080:1920,setsar=1[bg]"
            )
        else: # Fit
            layout_filter = (
                f"[0:v]crop=w=iw-{2*margin}:h=ih-{2*margin}:x={margin}:y={margin}[clean];"
                f"[clean]scale=1080:-1,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[bg]"
            )

        layout_filter += ";[bg]fps=30[bg_fps];"
        current_stream = "[bg_fps]"

        filter_chain = layout_filter

        if wm_text:
            wm_cmd = (
                f"drawtext=text='{wm_text}':fontcolor=white@0.3:fontsize={wm_size}:"
                f"x='(w-text_w)/2 + ((w-text_w)/2 - 50) * sin(t/2.5)':"
                f"y='(h-text_h)/2 + ((h-text_h)/2 - 50) * cos(t/3.5)':"
                f"shadowcolor=black@0.5:shadowx=2:shadowy=2"
            )
            filter_chain += f"{current_stream}{wm_cmd}[with_wm]"
            current_stream = "[with_wm]"
        else:
            filter_chain += f"{current_stream}null[with_wm]"
            current_stream = "[with_wm]"

        if ass_path and os.path.exists(ass_path):
            safe_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
            sub_cmd = f"subtitles='{safe_ass_path}'"
            filter_chain += f";{current_stream}{sub_cmd}[v_final]"
            current_stream = "[v_final]"
        else:
            filter_chain += f";{current_stream}null[v_final]"

        cmd = [self.ffmpeg_path, '-y', '-i', input_path]

        if not has_audio:
            cmd += ['-f', 'lavfi', '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100:d={dur}']
            audio_map = '1:a'
            cmd += ['-shortest']
        else:
            audio_map = '[a_final]'
            filter_chain += f";[0:a]aresample=44100[a_final]"

        cmd += ['-filter_complex', filter_chain]
        cmd += ['-map', '[v_final]', '-map', audio_map]
        cmd += [
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
            '-c:a', 'aac', '-ar', '44100',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"❌ [Processing Error]: {e.stderr.decode()}", file=sys.stderr)
            raise e

    def _has_audio(self, filepath):
        cmd = [self.ffprobe_path, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", filepath]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            return len(res.stdout.strip()) > 0
        except: return False

    def _get_exact_duration(self, filepath):
        cmd = [self.ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            return float(res.stdout.strip())
        except: return 5.0

    def _analyze_face_jump_3s(self, video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        target_w = int(height * (9/16))
        if target_w > width: target_w = width
        interval_frames = int(fps * 3)
        mp_face = mp.solutions.face_detection
        keyframes = []
        with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face_detection:
            frame_idx = 0
            current_x = (width - target_w) // 2
            while cap.isOpened():
                success, image = cap.read()
                if not success: break
                if frame_idx % interval_frames == 0:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(image_rgb)
                    best_face_x = None
                    max_size = 0
                    if results.detections:
                        for detection in results.detections:
                            bboxC = detection.location_data.relative_bounding_box
                            area = bboxC.width * bboxC.height
                            cx = int((bboxC.xmin + bboxC.width / 2) * width)
                            if area > max_size:
                                max_size = area
                                best_face_x = cx
                        if best_face_x is not None:
                            new_x = best_face_x - (target_w // 2)
                            new_x = max(0, min(new_x, width - target_w))
                            current_x = new_x
                    time_sec = frame_idx / fps
                    keyframes.append((time_sec, current_x))
                frame_idx += 1
        cap.release()
        return self._build_step_expression(keyframes, (width-target_w)//2)

    def _analyze_mouse_smooth(self, video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        target_w = int(height * (9/16))
        if target_w > width: target_w = width
        backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
        smoothed_x = (width - target_w) // 2
        alpha = 0.05
        keyframes = []
        frame_idx = 0
        step = int(fps * 0.5)
        keyframes.append((0.0, smoothed_x))
        while cap.isOpened():
            success, image = cap.read()
            if not success: break
            fgMask = backSub.apply(image)
            if frame_idx > 0 and frame_idx % step == 0:
                contours, _ = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                center_motion_x = None
                max_area = 0
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > 100:
                        x, y, w, h = cv2.boundingRect(cnt)
                        cx = x + w//2
                        if area > max_area:
                            max_area = area
                            center_motion_x = cx
                target_x = smoothed_x
                if center_motion_x is not None:
                    ideal_x = center_motion_x - (target_w // 2)
                    ideal_x = max(0, min(ideal_x, width - target_w))
                    target_x = ideal_x
                smoothed_x = (smoothed_x * (1 - alpha)) + (target_x * alpha)
                time_sec = frame_idx / fps
                keyframes.append((time_sec, int(smoothed_x)))
            frame_idx += 1
        cap.release()
        return self._build_lerp_expression(keyframes, (width-target_w)//2)

    def _build_step_expression(self, keyframes, default_val):
        if not keyframes: return str(default_val)
        terms = []
        for i in range(len(keyframes) - 1):
            t_curr, val_curr = keyframes[i]
            t_next, _ = keyframes[i+1]
            term = f"(gte(t,{t_curr:.3f})*lt(t,{t_next:.3f})*{val_curr})"
            terms.append(term)
        last_t, last_val = keyframes[-1]
        terms.append(f"(gte(t,{last_t:.3f})*{last_val})")
        return "+".join(terms) if terms else str(default_val)

    def _build_lerp_expression(self, keyframes, default_val):
        if not keyframes: return str(default_val)
        if len(keyframes) == 1: return str(keyframes[0][1])
        terms = []
        for i in range(len(keyframes) - 1):
            t1, v1 = keyframes[i]
            t2, v2 = keyframes[i+1]
            dur = t2 - t1
            if dur <= 0.001: dur = 0.001
            lerp_expr = f"({v1}+({v2}-{v1})*(t-{t1})/{dur:.3f})"
            term = f"(gte(t,{t1:.3f})*lt(t,{t2:.3f})*{lerp_expr})"
            terms.append(term)
        last_t, last_v = keyframes[-1]
        terms.append(f"(gte(t,{last_t:.3f})*{last_v})")
        return "+".join(terms)

    def _smart_adjust_timestamps(self, input_path, start_sec, end_sec, temp_dir, status_updater, model_size):
        try:
            buffer_after = 20.0
            check_duration = (end_sec - start_sec) + buffer_after
            temp_audio = os.path.join(temp_dir, f"smart_seek_{uuid.uuid4().hex}.mp3")
            cmd = [self.ffmpeg_path, '-y', '-ss', str(start_sec), '-i', input_path, '-t', str(check_duration), '-vn', '-acodec', 'libmp3lame', '-q:a', '2', temp_audio]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not os.path.exists(temp_audio): return end_sec
            if model_size not in self.whisper_cache:
                self.whisper_cache[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
            model = self.whisper_cache[model_size]
            segments, _ = model.transcribe(temp_audio, word_timestamps=True)
            target_relative_end = end_sec - start_sec
            dot_candidates = []
            for segment in segments:
                for word in segment.words:
                    w = word.word.strip()
                    if not w: continue
                    if w.endswith('.'):
                         dot_candidates.append({"time": word.end, "dist": abs(word.end - target_relative_end)})
            if not dot_candidates:
                for segment in segments:
                    for word in segment.words:
                        w = word.word.strip()
                        if w.endswith('?') or w.endswith('!'):
                             dot_candidates.append({"time": word.end, "dist": abs(word.end - target_relative_end)})
            os.remove(temp_audio)
            if dot_candidates:
                dot_candidates.sort(key=lambda x: x['dist'])
                return start_sec + dot_candidates[0]['time'] + 0.1
            return end_sec
        except: return end_sec

    def _remove_silence(self, input_path, output_path, db_threshold="-30dB", min_duration=0.5):
        try:
            cmd_detect = [self.ffmpeg_path, '-i', input_path, '-af', f'silencedetect=noise={db_threshold}:d={min_duration}', '-f', 'null', '-']
            result = subprocess.run(cmd_detect, capture_output=True, text=True)
            log_output = result.stderr
            silence_starts = [float(x) for x in re.findall(r'silence_start: (\d+(?:\.\d+)?)', log_output)]
            silence_ends = [float(x) for x in re.findall(r'silence_end: (\d+(?:\.\d+)?)', log_output)]
            if not silence_starts: return False
            duration_cmd = [self.ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path]
            dur_res = subprocess.run(duration_cmd, capture_output=True, text=True)
            total_duration = float(dur_res.stdout.strip())
            keep_segments = []
            current_time = 0.0
            count = min(len(silence_starts), len(silence_ends))
            for i in range(count):
                if silence_starts[i] > current_time: keep_segments.append((current_time, silence_starts[i]))
                current_time = silence_ends[i]
            if current_time < total_duration: keep_segments.append((current_time, total_duration))
            if not keep_segments: return False
            filter_str = ""
            concat_str = ""
            for idx, (start, end) in enumerate(keep_segments):
                filter_str += f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{idx}];"
                filter_str += f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{idx}];"
                concat_str += f"[v{idx}][a{idx}]"
            concat_str += f"concat=n={len(keep_segments)}:v=1:a=1[outv][outa]"
            cmd_process = [self.ffmpeg_path, '-y', '-i', input_path, '-filter_complex', filter_str + concat_str, '-map', '[outv]', '-map', '[outa]', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', output_path]
            subprocess.run(cmd_process, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except: return False

    def _generate_original_style_ass(self, video_path, output_path, font_size, model_size):
        audio_temp = video_path.replace(".mp4", ".mp3")
        subprocess.run([self.ffmpeg_path, '-y', '-i', video_path, '-vn', '-acodec', 'libmp3lame', audio_temp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if model_size not in self.whisper_cache: self.whisper_cache[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
        model = self.whisper_cache[model_size]
        segments, _ = model.transcribe(audio_temp, word_timestamps=True)
        header = f"""[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,{font_size},&H0000FFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,135,135,250,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            for segment in segments:
                for word in segment.words:
                    start = self._fmt_time(word.start)
                    end = self._fmt_time(word.end)
                    dur = int((word.end - word.start) * 100)
                    text = f"{{\\k{dur}}}{word.word.strip()}"
                    f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
        if os.path.exists(audio_temp): os.remove(audio_temp)

    def _cut_video(self, input_path, start, duration, output_path):
        cmd = [self.ffmpeg_path, '-y', '-ss', str(start), '-i', input_path, '-t', str(duration), '-c', 'copy', output_path]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _merge_videos(self, clips, output_path):
        list_file = f"list_{uuid.uuid4().hex}.txt"
        with open(list_file, 'w') as f:
            for clip in clips: f.write(f"file '{os.path.abspath(clip)}'\n")
        cmd = [self.ffmpeg_path, '-y', '-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', output_path]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            cmd_reencode = [self.ffmpeg_path, '-y', '-f', 'concat', '-safe', '0', '-i', list_file, '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', output_path]
            subprocess.run(cmd_reencode, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(list_file)

    def _fmt_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def _parse_time(self, time_str):
        try:
            parts = time_str.split(':')
            if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except: return None
        return None

    def _error(self, msg, updater):
        updater(msg, "ERROR")
        return {"payload": {"data": {"error": msg}}, "output_name": "error"}
