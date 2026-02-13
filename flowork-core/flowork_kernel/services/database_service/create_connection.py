########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\create_connection.py total lines 40 
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
    """Creates a new connection to the SQLite database with Robot-Class Optimization."""
    try:
        conn = sqlite3.connect(hub.db_path)

        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA busy_timeout = 10000;') # Naikin ke 10s buat jutaan user paralel
        conn.execute('PRAGMA foreign_keys = ON;')

        conn.execute('PRAGMA mmap_size = 268435456;') # 256MB mmap

        conn.execute('PRAGMA cache_size = -10000;') # ~10MB memory cache

        conn.execute('PRAGMA synchronous = NORMAL;')

        conn.row_factory = sqlite3.Row

        return conn
    except sqlite3.Error as e:
        if hasattr(hub, 'logger'):
            hub.logger.error(f'Failed to create database connection: {e}', exc_info=True)
        return None
