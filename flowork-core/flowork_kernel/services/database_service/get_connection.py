########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\get_connection.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sqlite3
import logging
import json
import uuid
from contextlib import contextmanager
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton

DB_SCHEMA_VERSION = 7


def run(hub):
    """
        Alias for create_connection to maintain compatibility with services
        expecting get_connection() pattern.
        """
    return hub.execute_sync('create_connection')
