########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\transaction.py total lines 44 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sqlite3
import time
from contextlib import contextmanager

@contextmanager
def run(hub):
    """
    Context manager dengan Neural Retry.
    Menangani 'database is locked' saat jutaan request/startup masal.
    """
    conn = None
    retries = 10  # Lebih sabar
    delay = 0.2

    while retries > 0:
        try:
            conn = hub.execute_sync('create_connection')
            if not conn: raise ConnectionError('DB Link Failed.')

            conn.execute('BEGIN IMMEDIATE TRANSACTION;')
            yield conn
            conn.commit()
            break

        except sqlite3.OperationalError as e:
            if 'locked' in str(e).lower():
                retries -= 1
                time.sleep(delay)
                if conn: conn.close()
                continue
            else:
                if conn: conn.rollback()
                raise e
        except Exception as e:
            if conn: conn.rollback()
            raise e
        finally:
            if conn: conn.close()
