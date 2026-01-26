########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_file_commander\main.py total lines 181 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import shutil
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
except:
    sys.stdout.reconfigure(line_buffering=True)

DATA_ROOT = Path("/app/data/users")

def auto_detect_user(user_id):
    """Detect real user ID if 'system' is passed but data exists"""
    if user_id in ["system", "None", "", None] and DATA_ROOT.exists():
        try:
            potential = [d.name for d in DATA_ROOT.iterdir() if d.is_dir() and d.name != "system"]
            if len(potential) >= 1:
                return potential[0]
        except: pass
    return user_id

def resolve_path(path_str, user_id):
    """Secure path resolution to prevent directory traversal with Anti-Nesting"""
    real_id = auto_detect_user(user_id)
    user_root = DATA_ROOT / real_id

    if not user_root.exists():
        try: user_root.mkdir(parents=True, exist_ok=True)
        except: pass

    if not path_str: return user_root

    clean_path = str(path_str).replace("\\", "/").strip()

    if "/users/system" in clean_path:
        clean_path = clean_path.replace("/users/system", f"/users/{real_id}")

    if clean_path.startswith(real_id + "/"):
        clean_path = clean_path[len(real_id)+1:]
    elif clean_path == real_id:
        clean_path = ""

    if clean_path.startswith(f"/app/data/users/{real_id}"):
        return Path(clean_path)

    clean_relative = clean_path
    if clean_relative.startswith("/app/data/users"):
        clean_relative = Path(clean_relative).name

    clean_relative = clean_relative.lstrip("/\\").replace("..", "")

    return user_root / clean_relative

def action_create_folder(params, user_id):
    path_raw = params.get("path")
    name = params.get("name")
    if not name: return {"status": "error", "error": "Folder name required"}

    target_dir = resolve_path(path_raw, user_id) / name

    if target_dir.exists():
        return {"status": "error", "error": "Folder already exists"}

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ [Muscle] Created folder: {name}", flush=True)
    return {"status": "success", "path": str(target_dir)}

def action_create_file(params, user_id):
    path_raw = params.get("path")
    name = params.get("name")
    content = params.get("content", "")
    if not name: return {"status": "error", "error": "File name required"}

    target_file = resolve_path(path_raw, user_id) / name

    if target_file.exists():
        return {"status": "error", "error": "File already exists"}

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ [Muscle] Created file: {name}", flush=True)
    return {"status": "success", "path": str(target_file)}

def action_delete_item(params, user_id):
    path_raw = params.get("path")
    target = resolve_path(path_raw, user_id)

    if not target.exists():
        return {"status": "success"}

    if target.is_dir():
        shutil.rmtree(target)
    else:
        os.remove(target)

    print(f"🗑️ [Muscle] Deleted: {target.name}", flush=True)
    return {"status": "success"}

def action_rename_item(params, user_id):
    path_raw = params.get("path")
    new_name = params.get("new_name")
    if not new_name: return {"status": "error", "error": "New name required"}

    target = resolve_path(path_raw, user_id)
    if not target.exists():
        return {"status": "error", "error": "Item not found"}

    new_path = target.parent / new_name
    if new_path.exists():
        return {"status": "error", "error": "New name already exists"}

    target.rename(new_path)
    print(f"📝 [Muscle] Renamed {target.name} -> {new_name}", flush=True)
    return {"status": "success"}

def action_delete_batch(params, user_id):
    paths = params.get("paths", [])
    deleted = 0
    errors = []

    for p in paths:
        target = resolve_path(p, user_id)
        try:
            if target.exists():
                if target.is_dir(): shutil.rmtree(target)
                else: os.remove(target)
                deleted += 1
        except Exception as e:
            errors.append(f"{target.name}: {str(e)}")

    print(f"🗑️ [Muscle] Batch delete complete. Removed: {deleted}", flush=True)
    return {"status": "success", "deleted": deleted, "errors": errors}

if __name__ == "__main__":
    print("🤖 File Commander Muscle [Otot] Online.", flush=True)

    payload_str = os.environ.get("FLOWORK_PAYLOAD")
    if not payload_str:
        print("❌ Error: Neural Payload missing.", flush=True)
        sys.exit(1)

    try:
        payload = json.loads(payload_str)
        action = payload.get("action")
        params = payload.get("params", {})
        user_context = params.get("user_context", {})
        user_id = user_context.get("user_id") or payload.get("user_id", "system")

        print(f"📋 Operation: {action.upper()} | User: {user_id}", flush=True)

        result = {}
        if action == "create_folder":
            result = action_create_folder(params, user_id)
        elif action == "create_file":
            result = action_create_file(params, user_id)
        elif action == "delete_item":
            result = action_delete_item(params, user_id)
        elif action == "rename_item":
            result = action_rename_item(params, user_id)
        elif action == "delete_batch":
            result = action_delete_batch(params, user_id)
        else:
            result = {"status": "error", "error": f"Unknown action: {action}"}

        print("--- RESULT ---", flush=True)
        print(json.dumps(result), flush=True)

    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), flush=True)
        sys.exit(1)
