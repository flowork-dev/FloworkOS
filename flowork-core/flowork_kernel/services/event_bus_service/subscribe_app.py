########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\subscribe_app.py total lines 26 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
import logging
import multiprocessing
import queue
import threading
import time
import traceback
from flowork_kernel.services.base_service import BaseService


def run(hub, event_pattern: str, app_id: str, action_name: str):
    """
        Mendaftarkan App Eksternal agar dibangunkan saat event terjadi.
        """
    if event_pattern not in hub.app_subscriptions:
        hub.app_subscriptions[event_pattern] = []
    entry = (app_id, action_name)
    if entry not in hub.app_subscriptions[event_pattern]:
        hub.app_subscriptions[event_pattern].append(entry)
        hub.logger.info(f"🔌 [Nervous] App '{app_id}' attached to event '{event_pattern}' (Action: {action_name})")
