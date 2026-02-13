########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\hardware_io_service\start.py total lines 16 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import logging
from flowork_kernel.services.base_service import BaseService


def run(hub):
    """Memulai pemindaian indra sistem"""
    hub.logger.info('👁️ HardwareIOService (Indra) is ONLINE.')
    hub.execute_sync('_scan_hardware_capabilities')
