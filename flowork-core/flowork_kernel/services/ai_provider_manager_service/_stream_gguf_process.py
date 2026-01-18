########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\_stream_gguf_process.py total lines 60 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import importlib.util
import subprocess
import sys
import importlib.metadata
import tempfile
import zipfile
import shutil
import traceback
import time
import hashlib
import threading
import select
import asyncio
import uuid
import glob
from datetime import datetime
from aiohttp import web
from flowork_kernel.utils.file_helper import sanitize_filename


def run(hub, cmd, input_text):
    try:
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, text=False, bufsize=0)
        if input_text:
            process.stdin.write(input_text.encode('utf-8'))
            process.stdin.close()
        hub.logger.warning('!!! [AI STREAM] Connected. Waiting for tokens... !!!')
        while True:
            reads = [process.stdout.fileno()]
            try:
                ret = select.select(reads, [], [], 1.0)
            except (ValueError, OSError):
                break
            if reads[0] in ret[0]:
                char = process.stdout.read(1)
                if not char:
                    if process.poll() is not None:
                        break
                    continue
                try:
                    yield {'type': 'token', 'content': char.decode('utf-8', errors='replace')}
                except Exception:
                    pass
            else:
                yield {'type': 'ping'}
        if process.returncode != 0 and process.returncode is not None:
            err = f'Worker exited with code {process.returncode}.'
            hub.logger.error(f'[AI Worker Error] {err}')
            yield {'type': 'error', 'content': f'\n[System Error: {err}]'}
    except Exception as e:
        hub.logger.error(f'Streaming Exception: {e}')
        yield {'type': 'error', 'content': f'[System Error: {str(e)}]'}
