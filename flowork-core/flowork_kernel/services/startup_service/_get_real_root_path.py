########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\startup_service\_get_real_root_path.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import asyncio
import subprocess
import sys
import os
from flowork_kernel.exceptions import MandatoryUpdateRequiredError, PermissionDeniedError


def run(hub):
    """[MUTATED] Cerdas menentukan root path (Docker vs Local)"""
    if os.path.exists('/app/app'):
        return '/app/app'
    kernel_path = getattr(hub.kernel, 'project_root_path', None)
    if kernel_path:
        unified_app = os.path.join(kernel_path, '..', 'app')
        if os.path.exists(unified_app):
            return os.path.abspath(unified_app)
        internal_app = os.path.join(kernel_path, 'app')
        if os.path.exists(internal_app):
            return os.path.abspath(internal_app)
    return os.getcwd()
