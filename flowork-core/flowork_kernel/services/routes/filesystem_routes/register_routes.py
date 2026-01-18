########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\routes\filesystem_routes\register_routes.py total lines 15 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
from urllib.parse import urlparse, parse_qs
from .base_api_route import BaseApiRoute


def run(hub):
    return {'GET /api/v1/filesystem/drives': hub.handle_list_drives, 'GET /api/v1/filesystem/list': hub.handle_list_directory}
