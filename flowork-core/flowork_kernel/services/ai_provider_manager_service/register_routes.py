########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_provider_manager_service\register_routes.py total lines 34 
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


def run(hub, api_router):
    api_router.add_route('/api/v1/models/local', hub._handle_list_local_models, methods=['GET'])
    api_router.add_route('/api/v1/models/local', hub._handle_options, methods=['OPTIONS'])
    api_router.add_route('/api/v1/models/rescan', hub._handle_rescan_models, methods=['POST'])
    api_router.add_route('/api/v1/models/rescan', hub._handle_options, methods=['OPTIONS'])
    api_router.add_route('/api/v1/ai/files/view', hub._handle_view_file, methods=['GET'])
