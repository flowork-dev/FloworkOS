########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_runtime_service\app_runtime_service.py total lines 146 
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

class AppRuntimeService(BaseService):
    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)
        self.active_processes = {} # {pid: subprocess.Popen}
        self.log_queue = queue.Queue(maxsize=10000)
        self.is_running = True

    def start(self):
        self.logger.info("💪 [Muscle] AppRuntime Engine Online. Ready to flex.")

    def stop(self):
        self.is_running = False
        self.logger.info("💪 [Muscle] Shutting down all sub-processes...")
        for pid, proc in self.active_processes.items():
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except: pass

    def trigger_event_handler(self, app_id: str, action_name: str, payload: dict):
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

            if loop and loop.is_running():
                loop.create_task(self.execute_service_action(app_id, action_name, payload))
            else:
                threading.Thread(
                    target=lambda: asyncio.run(self.execute_service_action(app_id, action_name, payload)),
                    daemon=True
                ).start()
        except Exception as e:
            self.logger.error(f"❌ [Nervous] Failed to trigger event for {app_id}: {e}")

    async def execute_service_action(self, app_id: str, action_name: str, data: dict, retry_count=0):
        app_manager = self.kernel.get_service("app_service")
        if not app_manager:
             app_manager = self.kernel.get_service("app_manager_service")

        if not app_manager:
             self.logger.error("AppManager not found!")
             return {"status": "error", "error": "AppManager Unavailable"}

        try:
            port = app_manager.ensure_app_running(app_id)
        except Exception as e:
            return {"status": "error", "error": f"Failed to start App Daemon: {str(e)}"}

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)

        try:
            loop = asyncio.get_running_loop()

            def socket_transaction():
                client.connect(('127.0.0.1', port))
                payload = json.dumps({"action": action_name, "data": data}).encode('utf-8')
                client.sendall(struct.pack('!I', len(payload)))
                client.sendall(payload)

                header = client.recv(4)
                if not header: raise ConnectionResetError("Empty header")
                length = struct.unpack('!I', header)[0]

                chunks = []
                bytes_recd = 0
                while bytes_recd < length:
                    chunk = client.recv(min(length - bytes_recd, 4096))
                    if not chunk: raise ConnectionResetError("Incomplete body")
                    chunks.append(chunk)
                    bytes_recd += len(chunk)

                response_json = b''.join(chunks).decode('utf-8')
                return json.loads(response_json)

            response = await loop.run_in_executor(None, socket_transaction)
            return response

        except (ConnectionRefusedError, ConnectionResetError, socket.timeout) as e:
            if retry_count < 1:
                self.logger.warning(f"⚠️ [Lazarus] App {app_id} connection failed. Reviving... ({str(e)})")
                app_manager.kill_app(app_id)
                await asyncio.sleep(1)
                return await self.execute_service_action(app_id, action_name, data, retry_count=1)
            else:
                self.logger.error(f"💀 [Lazarus] Failed to revive {app_id} after retry.")
                return {"status": "error", "error": "Service Unavailable (App crashed repeatedly)"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            client.close()

    async def execute_with_timeout(self, func, data, timeout=5):
        loop = asyncio.get_running_loop()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(executor, func, data)
                return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception("Service Timeout: App merespon terlalu lama!")
        except Exception as e:
            raise e

    async def execute_app(self, app_id: str, action: str, params: dict, user_id: str):
        """
        [MODERN REDIRECT] Redirection to standardized Hybrid Action.
        Fixes the 'coroutine never awaited' warning in logs.
        """
        return await self.execute_service_action(app_id, action, params)


    def _extract_percent(self, msg):
        try:
            import re
            match = re.search(r"(\d+(\.\d+)?)%", msg)
            if match: return float(match.group(1))
        except: pass
        return 0
