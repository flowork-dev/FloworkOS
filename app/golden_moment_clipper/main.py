########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\golden_moment_clipper\main.py total lines 177 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import uuid
import shutil
import subprocess
import time
import importlib
import traceback
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
except:
    sys.stdout.reconfigure(line_buffering=True)

DATA_ROOT = Path("/app/data/users")
if not DATA_ROOT.exists():
    DATA_ROOT = Path(os.getcwd()) / "data" / "users"

try:
    import faster_whisper
    import mediapipe
    import cv2 as cv2_lib

    WhisperModel = faster_whisper.WhisperModel
    mp_face = mediapipe.solutions.face_detection
    cv2 = cv2_lib
    print("🚀 [Muscle] AI Engine Loaded from Global Warehouse!", flush=True)
except ImportError as e:
    print(f"❌ [Critical] Missing AI conduit: {e}. Ensure Global Warehouse has processed requirements.txt", flush=True)

def auto_detect_user(user_id):
    if user_id in ["system", "None", "", None] and DATA_ROOT.exists():
        try:
            potential = [d.name for d in DATA_ROOT.iterdir() if d.is_dir() and d.name != "system"]
            if len(potential) >= 1:
                print(f"🕵️‍♂️ [Identity-Shift] Switching context from '{user_id}' to '{potential[0]}'", flush=True)
                return potential[0]
        except: pass
    return user_id

def get_user_storage(user_id):
    real_id = auto_detect_user(user_id)
    path = DATA_ROOT / real_id
    path.mkdir(parents=True, exist_ok=True)
    return path

def resolve_path(path_str, user_id):
    real_id = auto_detect_user(user_id)
    user_root = DATA_ROOT / real_id

    if not user_root.exists(): user_root.mkdir(parents=True, exist_ok=True)
    if not path_str: return None

    clean_path = str(path_str).replace("\\", "/").strip()

    if "/users/system" in clean_path:
        clean_path = clean_path.replace("/users/system", f"/users/{real_id}")

    if clean_path.startswith(f"/app/data/users/{real_id}"):
        return clean_path

    clean_relative = clean_path
    if clean_relative.startswith("/app/data/users"):
        clean_relative = Path(clean_relative).name

    clean_relative = clean_relative.lstrip("/\\").replace("..", "")

    return str(user_root / clean_relative)

def find_ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"

def process_video(params, user_id):

    ffmpeg = find_ffmpeg()

    input_path = resolve_path(params.get("input_folder_path"), user_id)
    output_base = resolve_path(params.get("output_folder"), user_id)

    print(f"📂 [Input] {input_path}", flush=True)
    print(f"📂 [Output] {output_base}", flush=True)

    if not input_path or not os.path.exists(input_path):
        return {"status": "error", "error": f"Input not found: {input_path}"}

    videos = []
    if os.path.isfile(input_path):
        videos = [input_path]
    else:
        videos = [os.path.join(input_path, f) for f in os.listdir(input_path)
                  if f.lower().endswith(('.mp4','.mov','.avi','.mkv'))]

    if not videos: return {"status": "error", "error": "No videos found"}

    timestamps_raw = params.get("timestamps", "")
    tasks = {}
    for line in timestamps_raw.split('\n'):
        line = line.strip()
        if not line: continue
        parts = line.split('|')
        time_part = parts[0].strip()
        vid_id = parts[1].strip() if len(parts) >= 2 else "1"
        t_parts = time_part.split('-')
        if len(t_parts) == 2:
            if vid_id not in tasks: tasks[vid_id] = []
            tasks[vid_id].append((t_parts[0], t_parts[1]))

    print(f"🎬 [Muscle] Processing {len(videos)} videos with {len(tasks)} task groups.", flush=True)

    processed_count = 0

    for idx, vid_path in enumerate(videos, 1):
        vid_id_str = str(idx)
        if vid_id_str not in tasks: continue

        segments = tasks[vid_id_str]
        print(f"   > Video {idx}: {os.path.basename(vid_path)} ({len(segments)} clips)", flush=True)

        vid_out_dir = os.path.join(output_base, vid_id_str)
        os.makedirs(vid_out_dir, exist_ok=True)

        for i, (start_str, end_str) in enumerate(segments):
            out_name = f"clip_{i+1}_{uuid.uuid4().hex[:4]}.mp4"
            out_path = os.path.join(vid_out_dir, out_name)

            cmd = [
                ffmpeg, '-y', '-ss', start_str, '-i', vid_path, '-to', end_str,
                '-c:v', 'libx264', '-c:a', 'aac', '-preset', 'ultrafast', out_path
            ]

            try:
                print(f"⚡ [Clipping] Creating segment {i+1}...", flush=True)
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(out_path):
                    print(f"     + Created: {out_name}", flush=True)
                    processed_count += 1
            except Exception as e:
                print(f"     ! Error on clip {i+1}: {e}", flush=True)

    return {"status": "success", "processed": processed_count}

if __name__ == "__main__":
    print("🎬 Golden Moment Muscle Loaded.", flush=True)

    payload_str = os.environ.get("FLOWORK_PAYLOAD")
    if not payload_str: sys.exit(1)

    try:
        payload = json.loads(payload_str)
        action = payload.get("action")
        params = payload.get("params", {})
        user_id = payload.get("user_id", "system")

        print(f"📋 Operation: {action.upper()}", flush=True)

        result = {}
        if action == "process":
            result = process_video(params, user_id)
        else:
            result = {"status": "error", "error": f"Unknown action: {action}"}

        print("\n--- RESULT ---", flush=True)
        print(json.dumps(result), flush=True)

    except Exception as e:
        print(f"🔥 Critical Video Error: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
