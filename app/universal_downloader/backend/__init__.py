########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\universal_downloader\backend\__init__.py total lines 19 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys

current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from .node import DownloaderNode
    from .service import UniversalDownloaderService as DownloaderService
    from .router import AppRouter
except ImportError as e:
    print(f"[Downloader Backend] Neural Import failure: {e}")
