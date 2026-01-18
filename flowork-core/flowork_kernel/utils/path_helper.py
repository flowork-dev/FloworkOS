########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\utils\path_helper.py total lines 43 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
from pathlib import Path

IS_DOCKER = os.path.exists("/.dockerenv")

def get_apps_directory():
    """
    [English Note] Returns the standardized apps directory.
    Crucial for aligning with docker-compose volume mounts (/app/app).
    """
    if IS_DOCKER:
        return Path("/app/app")
    else:
        dev_path = Path("C:/FLOWORK/app")
        if dev_path.exists(): return dev_path
        fallback = Path(os.getcwd()) / "app"
        fallback.mkdir(exist_ok=True)
        return fallback

def get_data_directory():
    """Resolves the central data directory for DB and user storage."""
    if IS_DOCKER: return Path("/app/data")
    base = Path("C:/FLOWORK/data") if os.name == 'nt' else Path(os.getcwd()) / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base

def resolve_user_path(user_id: str, sub_dir: str = "") -> Path:
    """Creates isolated sandbox paths for users."""
    user_path = get_data_directory() / "users" / str(user_id)
    if sub_dir: user_path = user_path / sub_dir
    user_path.mkdir(parents=True, exist_ok=True)
    return user_path

def normalize_path(path_str):
    """Fix slashes for cross-platform compatibility."""
    return str(Path(path_str).resolve())
