########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\startup_service\_attempt_auto_login.py total lines 25 
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
    hub.logger.info('StartupService: Attempting to load local user identity...')
    state_manager = hub.kernel.get_service('state_manager', is_system_call=True)
    if not state_manager:
        hub.logger.warning('StateManager not found. Cannot load user identity.')
        hub.kernel.current_user = None
        return
    hub.logger.info('StartupService: No user identity loaded at startup. Waiting for GUI connection.')
    hub.kernel.current_user = None
    state_manager.delete('current_user_data')
    state_manager.delete('user_session_token')
