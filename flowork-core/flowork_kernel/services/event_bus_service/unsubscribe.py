########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\unsubscribe.py total lines 22 
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


def run(hub, subscriber_id: str):
    if subscriber_id in hub.subscribers:
        del hub.subscribers[subscriber_id]
        hub.logger.debug(f'Unsubscribed: {subscriber_id}')
    else:
        hub.logger.warning(f'Attempted to unsubscribe ghost ID: {subscriber_id}')
