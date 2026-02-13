########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\universal_downloader\main.py total lines 229 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import subprocess
import shutil
import random
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
except:
    sys.stdout.reconfigure(line_buffering=True)

yt_dlp = None
try:
    import yt_dlp as yt_lib
    yt_dlp = yt_lib
except ImportError:
    print("⚠️ [Muscle] yt-dlp conduit missing. Waiting for Global Warehouse injection...", flush=True)

DATA_ROOT = Path("/app/data/users")

def neural_matrix_pulse():
    print("⚡ [Neural-Matrix] Synchronizing with Flowork Muscle Service...", flush=True)
    time.sleep(0.1)

try:
    subprocess.check_call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    print("⚠️ [Warning] FFmpeg core not detected. Media conversion capabilities limited.", flush=True)

def auto_detect_user(user_id):
    if user_id in ["system", "None", "", None] and DATA_ROOT.exists():
        try:
            potential = [d.name for d in DATA_ROOT.iterdir() if d.is_dir() and d.name != "system"]
            if len(potential) >= 1:
                print(f"🕵️‍♂️ [Identity-Shift] Switching context from '{user_id}' to '{potential[0]}'", flush=True)
                return potential[0]
        except: pass
    return user_id

def resolve_path(path_str, user_id):
    real_id = auto_detect_user(user_id)
    user_root = DATA_ROOT / real_id

    if not user_root.exists():
        try: user_root.mkdir(parents=True, exist_ok=True)
        except: pass

    if not path_str: return user_root

    clean_path = str(path_str).replace("\\", "/").strip()

    if "/users/system" in clean_path:
        clean_path = clean_path.replace("/users/system", f"/users/{real_id}")

    if clean_path.startswith(f"/app/data/users/{real_id}"):
        return Path(clean_path)

    clean_relative = clean_path
    if clean_relative.startswith("/app/data/users"):
        clean_relative = Path(clean_relative).name

    clean_relative = clean_relative.lstrip("/\\").replace("..", "")

    return user_root / clean_relative

def action_download(params, user_id):
    if not yt_dlp:
        return {"status": "error", "error": "yt-dlp conduit missing. Check Global Warehouse installation."}

    urls = params.get("url", "").splitlines()
    format_mode = params.get("format_mode", "best")
    output_raw = params.get("output_folder") or params.get("output_dir")

    output_dir = resolve_path(output_raw, user_id)
    if not output_dir.exists():
        try: output_dir.mkdir(parents=True, exist_ok=True)
        except: pass

    print(f"📂 [Target] {output_dir}", flush=True)
    neural_matrix_pulse()

    results = []

    def progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%','')
            try:
                print(f"⚡ [Neural DL] {p}% @ {d.get('_speed_str')} | ETA: {d.get('_eta_str')}", flush=True)
            except: pass
        if d['status'] == 'finished':
            print("✅ [Neural DL] Download Complete. Converting...", flush=True)

    for single_url in urls:
        single_url = single_url.strip()
        if not single_url: continue

        print(f"⬇️ [Ingest] {single_url}", flush=True)

        try:
            ydl_opts = {
                'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [progress_hook],
                'restrictfilenames': True,
            }

            if format_mode == 'audio_mp3':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            elif format_mode == 'video_only':
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                })
            else:
                ydl_opts.update({'format': 'best'})

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(single_url, download=True)
                filename = ydl.prepare_filename(info)

                if format_mode == 'audio_mp3':
                    filename = os.path.splitext(filename)[0] + '.mp3'

                results.append({
                    "url": single_url,
                    "file": os.path.basename(filename),
                    "path": filename,
                    "title": info.get('title', 'Unknown')
                })
                print(f"✨ [Success] {os.path.basename(filename)}", flush=True)

        except Exception as e:
            print(f"❌ [Failure] {single_url}: {e}", flush=True)
            results.append({"url": single_url, "error": str(e)})

    return {"status": "success", "downloaded": results}

def action_browse(params, user_id):
    path_raw = params.get("path")
    target = resolve_path(path_raw, user_id)

    if not target.exists():
        return {"status": "error", "error": "Directory not found"}

    items = []
    for entry in os.scandir(target):
        items.append({
            "name": entry.name,
            "type": "folder" if entry.is_dir() else "file",
            "size": entry.stat().st_size if entry.is_file() else 0
        })
    return {"status": "success", "data": items, "current_path": str(target)}

def action_create_folder(params, user_id):
    path_raw = params.get("path")
    name = params.get("name")
    if not name: return {"status": "error"}

    base = resolve_path(path_raw, user_id)
    target = base / name

    if target.exists(): return {"status": "error", "error": "Exists"}
    target.mkdir(parents=True, exist_ok=True)
    return {"status": "success"}

def action_delete(params, user_id):
    path_raw = params.get("path")
    target = resolve_path(path_raw, user_id)

    if not target.exists(): return {"status": "error", "error": "Not found"}

    if target.is_dir(): shutil.rmtree(target)
    else: os.remove(target)
    return {"status": "success"}

if __name__ == "__main__":
    print("🤖 Universal Downloader [Level Dewa] Online.", flush=True)

    payload_str = os.environ.get("FLOWORK_PAYLOAD")
    if not payload_str:
        if len(sys.argv) > 1:
            print(f"🔧 CLI Mode: {sys.argv[1]}", flush=True)
            sys.exit(0)
        print("❌ Error: Neural Payload missing.", flush=True)
        sys.exit(1)

    try:
        payload = json.loads(payload_str)
        action = payload.get("action")
        params = payload.get("params", {})
        user_id = payload.get("user_id", "system")

        print(f"📋 Operation: {action.upper()}", flush=True)

        result = {}
        if action in ["download", "start_download", "quick_download", "download_file"]:
            result = action_download(params, user_id)
        elif action in ["browse", "browse_directory", "list_files"]:
            result = action_browse(params, user_id)
        elif action == "create_new_folder":
            result = action_create_folder(params, user_id)
        elif action == "delete_item":
            result = action_delete(params, user_id)
        else:
            result = {"status": "error", "error": f"Unknown sequence: {action}"}

        print("--- RESULT ---", flush=True)
        print(json.dumps(result), flush=True)

    except Exception as e:
        print(f"🔥 Critical Failure: {e}", flush=True)
        sys.exit(1)
