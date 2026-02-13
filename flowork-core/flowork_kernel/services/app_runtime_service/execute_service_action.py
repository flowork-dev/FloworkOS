########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_runtime_service\execute_service_action.py total lines 106 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import socket
import struct
import subprocess
import threading
import asyncio
import queue
import importlib.util
import concurrent.futures
from typing import Dict, Any
from flowork_kernel.services.base_service import BaseService


async def run(hub, app_id: str, action_name: str, data: dict, retry_count=0, user_id=None):
    """
    Eksekutor Aksi Service: Mengirim perintah ke Daemon App via Socket. [cite: 245]
    Fix: Meneruskan user_id untuk Secret Injection (Roadmap Poin 4).
    Fix 2.0: Menangani ensure_app_running baik sync maupun async (Smart Await).
    """
    app_manager = hub.kernel.get_service('app_service')
    if not app_manager:
        app_manager = hub.kernel.get_service('app_manager_service')

    if not app_manager:
        hub.logger.error('AppManager not found!')
        return {'status': 'error', 'error': 'AppManager Unavailable'}

    try:
        port_or_coro = app_manager.ensure_app_running(app_id, user_id=user_id)

        if asyncio.iscoroutine(port_or_coro):
            port = await port_or_coro
        else:
            port = port_or_coro

    except Exception as e:
        return {'status': 'error', 'error': f'Failed to start App Daemon: {str(e)}'}

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(15)

    try:
        loop = asyncio.get_running_loop()

        def socket_transaction():
            client.connect(('127.0.0.1', int(port)))

            request_payload = {
                'action': action_name,
                'data': data,
                'metadata': {'user_id': user_id, 'timestamp': time.time()}
            }

            payload = json.dumps(request_payload).encode('utf-8')
            client.sendall(struct.pack('!I', len(payload)))
            client.sendall(payload)

            header = client.recv(4)
            if not header:
                raise ConnectionResetError('Empty header')
            length = struct.unpack('!I', header)[0]

            chunks = []
            bytes_recd = 0
            while bytes_recd < length:
                chunk = client.recv(min(length - bytes_recd, 4096))
                if not chunk:
                    raise ConnectionResetError('Incomplete body')
                chunks.append(chunk)
                bytes_recd += len(chunk)

            response_json = b''.join(chunks).decode('utf-8')
            return json.loads(response_json)

        response = await loop.run_in_executor(None, socket_transaction)
        return response

    except (ConnectionRefusedError, ConnectionResetError, socket.timeout, socket.error) as e:
        if retry_count < 1:
            hub.logger.warning(f'⚠️ [Lazarus] App {app_id} link failed. Attempting revival... ({str(e)})')
            kill_res = app_manager.kill_app(app_id)
            if asyncio.iscoroutine(kill_res):
                await kill_res

            await asyncio.sleep(1.5)
            return await hub.execute_async('execute_service_action', app_id, action_name, data, retry_count=1, user_id=user_id)
        else:
            hub.logger.error(f'💀 [Lazarus] App {app_id} is dead beyond revival.')
            return {'status': 'error', 'error': 'Service Unavailable (App crashed repeatedly)'}
    except Exception as e:
        hub.logger.error(f"❌ [SocketExec] Error: {e}")
        return {'status': 'error', 'error': str(e)}
    finally:
        try:
            client.close()
        except:
            pass
