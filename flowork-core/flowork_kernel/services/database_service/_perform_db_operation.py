########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\_perform_db_operation.py total lines 72 
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

def run(hub, query_type, collection, payload):
    """
    Helper internal untuk eksekusi CRUD yang Aman & Cepat (High-Concurrency Ready).
    """
    target_table = None

    if not isinstance(collection, str):
        hub.logger.error(f"❌ [Database] Invalid collection type: {type(collection)}")
        return {'status': 'error', 'message': 'Collection name must be a string'}

    if collection == 'app_storage' or collection.startswith('app_'):
        target_table = 'app_storage'
    else:
        return {'status': 'error', 'message': f'Forbidden access to collection: {collection}'}

    app_id = payload.get('owner_app_id')
    if not app_id:
         return {'status': 'error', 'message': 'Missing owner_app_id in payload'}

    with hub.execute_sync('transaction') as conn:
        cursor = conn.cursor()

        if target_table == 'app_storage':
            if query_type == 'insert':
                orig_key = payload.get('key', str(uuid.uuid4()))
                final_key = f"{collection}:{orig_key}" if collection != 'app_storage' else orig_key
                val = json.dumps(payload.get('value', {}))

                cursor.execute(f'INSERT OR REPLACE INTO {target_table} (key, owner_app_id, value) VALUES (?, ?, ?)',
                               (final_key, app_id, val))
                return {'status': 'success', 'key': orig_key}

            elif query_type == 'select':
                key = payload.get('key')
                if key:
                    final_key = f"{collection}:{key}" if collection != 'app_storage' else key
                    cursor.execute(f'SELECT value FROM {target_table} WHERE owner_app_id=? AND key=?', (app_id, final_key))
                    row = cursor.fetchone()
                    return json.loads(row[0]) if row else None
                else:
                    prefix = f"{collection}:" if collection != 'app_storage' else ""
                    if prefix:
                        cursor.execute(f'SELECT key, value FROM {target_table} WHERE owner_app_id=? AND key LIKE ?', (app_id, f"{prefix}%"))
                    else:
                        cursor.execute(f'SELECT key, value FROM {target_table} WHERE owner_app_id=?', (app_id,))

                    rows = cursor.fetchall()
                    return {r[0].replace(prefix, "", 1): json.loads(r[1]) for r in rows}

            elif query_type == 'delete':
                key = payload.get('key')
                if key:
                    final_key = f"{collection}:{key}" if collection != 'app_storage' else key
                    cursor.execute(f'DELETE FROM {target_table} WHERE owner_app_id=? AND key=?', (app_id, final_key))
                else:
                    prefix = f"{collection}:"
                    cursor.execute(f'DELETE FROM {target_table} WHERE owner_app_id=? AND key LIKE ?', (app_id, f"{prefix}%"))
                return {'status': 'deleted'}

        return {'status': 'error', 'message': f'Operation {query_type} not supported for table {target_table}'}
