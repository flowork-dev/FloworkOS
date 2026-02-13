########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_client\_get_variable.py total lines 21 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import requests
import json
import os
import threading
import time
import random
from flowork_kernel.kernel import Kernel


def run(hub, var_name):
    if hub.kernel:
        variable_manager = hub.kernel.get_service('variable_manager')
        if variable_manager:
            return variable_manager.get_variable(var_name)
    return None
