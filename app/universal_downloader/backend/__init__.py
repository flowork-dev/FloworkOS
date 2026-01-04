########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\universal_downloader\backend\__init__.py total lines 19 
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
