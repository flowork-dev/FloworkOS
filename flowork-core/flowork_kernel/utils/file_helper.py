########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\utils\file_helper.py total lines 64 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import re
import shutil
import logging

logger = logging.getLogger("Kernel.Utils.FileHelper")

def sanitize_filename(filename: str) -> str:
    """
    [GEMINI - NEW] Essential for AI Provider Manager.
    Cleans filenames to prevent path injection and OS-specific errors.
    """
    if not filename:
        return "unnamed_file"
    filename = os.path.basename(filename)
    return re.sub(r'[^\w\-\.]', '_', filename)

def ensure_directory(path: str):
    """Ensures a directory exists, creating it if necessary."""
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")

def get_file_extension(filename: str) -> str:
    """Returns the lowercase extension of a file."""
    return os.path.splitext(filename)[1].lower()

def safe_delete(path: str):
    """Deletes a file or directory safely."""
    if not os.path.exists(path):
        return
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        logger.debug(f"Deleted: {path}")
    except Exception as e:
        logger.error(f"Error deleting {path}: {e}")

def load_json_file(file_path: str):
    import json
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"JSON Read Error in {file_path}: {e}")
        return None

def is_safe_path(basedir, path, follow_symlinks=True):
    if follow_symlinks:
        return os.path.realpath(path).startswith(os.path.realpath(basedir))
    return os.path.abspath(path).startswith(os.path.abspath(basedir))
