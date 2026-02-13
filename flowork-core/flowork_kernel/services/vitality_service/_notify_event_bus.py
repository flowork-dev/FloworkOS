########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\_notify_event_bus.py total lines 23 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import threading
import traceback
import asyncio
import json
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton


def run(hub, event, data):
    """Mengirim data kesehatan ke Saraf Pusat"""
    try:
        eb = Singleton.get_instance('event_bus')
        if eb:
            eb.publish(event, data, publisher_id='vitality_service')
    except:
        pass
