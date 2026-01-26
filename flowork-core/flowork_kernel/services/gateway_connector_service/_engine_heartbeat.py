########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\_engine_heartbeat.py total lines 78 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

import socketio
import os
import asyncio
import logging
import uuid
import json
import multiprocessing
import requests
import time
import sqlite3
import threading
import traceback
from dotenv import load_dotenv
from typing import Dict, Any
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
from flowork_kernel.router import StrategyRouter
from flowork_kernel.fac_enforcer import FacRuntime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

CURRENT_PAYLOAD_VERSION = 2

async def run(hub):
    """
    [PROTECTED TASK] Vital signs monitoring.
    Heartbeat dipaksa 3 detik untuk menjaga kestabilan Cloudflare Tunnel.
    """
    hub.logger.info("💓 [Vitality] Heartbeat pulse accelerated to 3s (Tunnel Protection Active).")

    while hub.is_running:
        try:
            if not getattr(hub, 'sio', None) or not hub.sio.connected:
                await asyncio.sleep(3) # Cek ulang koneksi setiap 3 detik
                continue

            if '/engine-socket' not in hub.sio.namespaces:
                await asyncio.sleep(3)
                continue

            cpu = psutil.cpu_percent() if PSUTIL_AVAILABLE else 0
            mem = psutil.virtual_memory().percent if PSUTIL_AVAILABLE else 0

            active_sessions = len(getattr(hub, 'g_active_sessions', []))

            payload = {
                'engine_id': hub.engine_id,
                'user_id': hub.user_id,
                'ts': int(time.time()),
                'cpu_percent': cpu,
                'memory_percent': mem,
                'metrics': {
                    'pid': os.getpid(),
                    'active_fac_sessions': active_sessions
                }
            }

            await hub.sio.emit('engine_vitals_update', payload, namespace='/engine-socket')

        except Exception as e:
            if hasattr(hub, 'logger'):
                hub.logger.warning(f'Heartbeat skipped: {e}')
            else:
                print(f"[Heartbeat] Error: {e}")

        await asyncio.sleep(3)
