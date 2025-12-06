########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\system_handler.py total lines 301 
########################################################################

import os
import asyncio
import time
import json
from .base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SystemHandler(BaseHandler):
    def register_events(self):
        @self.sio.event(namespace='/engine-socket')
        async def connect():
            self.logger.info("Attempting to connect to Gateway at {}...".format(self.service.gateway_url))
            try:
                self.logger.info(f"Connection to /engine-socket established. Auth was sent in connect() call.")

                if self.service._watchdog_task is None or self.service._watchdog_task.done():
                    self.service._watchdog_task = asyncio.create_task(self.service._run_watchdog())

            except Exception as e:
                self.logger.error(f"Error during connect event: {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def auth_success(data):
            user_id = data.get('user_id')
            self.service.user_id = user_id
            self.logger.info(f"Engine authenticated successfully for user: {user_id}")

            try:
                await asyncio.sleep(0.5)

                api_server = self.service.kernel_services.get("api_server_service")
                loc_manager = self.service.kernel_services.get("localization_manager")

                if not api_server or not loc_manager:
                    self.logger.error("[GatewayConnector] CRITICAL: ApiServer or LocalizationManager not found in kernel_services. Cannot send 'engine_ready'.")
                    return

                port = loc_manager.get_setting("webhook_port", 8990)

                internal_host = "flowork_core"
                internal_api_url = f"http://{internal_host}:{port}"
                self.service.internal_api_url = internal_api_url

                ready_payload_v2 = {
                    'internal_api_url': internal_api_url,
                    'engine_id': self.service.engine_id,
                    'user_id': self.service.user_id,
                    'capabilities': ['workflow', 'datasets', 'variables']
                }
                await self.sio.emit('engine_ready', ready_payload_v2, namespace='/engine-socket')
                self.logger.info(f"Sent 'engine_ready' to Gateway. Reported internal URL: {internal_api_url}")

                if self.service._hb_task is None or self.service._hb_task.done():
                    self.service._hb_task = asyncio.create_task(self.service._engine_heartbeat())

            except Exception as e:
                self.logger.error(f"Failed to send 'engine_ready' event after auth: {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def auth_failed(data):
            error_message = data.get('error')
            self.logger.error(f"Engine authentication failed: {error_message}")
            await self.service.stop()

        @self.sio.event(namespace='/engine-socket')
        async def disconnect():
            self.logger.info("Disconnected from Gateway /engine-socket.")
            try:
                if self.service._hb_task and not self.service._hb_task.done():
                    self.service._hb_task.cancel()

                if self.service._watchdog_task and not self.service._watchdog_task.done():
                    self.service._watchdog_task.cancel()
                    self.logger.info("[Watchdog] Stopped due to disconnect.")

            except Exception as _:
                pass

            self.service.g_active_sessions.clear()
            self.logger.info("[GatewayConnector] Cleared all active FAC runtimes due to disconnect.")

            self.logger.warning(f"[Gateway R6] Disconnected. Failing {len(self.service._pending_swarm_tasks)} pending swarm tasks.")
            async with self.service._pending_swarm_tasks_lock:
                for task_id, task_future in self.service._pending_swarm_tasks.items():
                    if not task_future.done():
                        task_future.set_result({"error": "GatewayError: Engine disconnected from Gateway."})
                self.service._pending_swarm_tasks.clear()

        @self.sio.event(namespace='/engine-socket')
        async def filesystem_list_request(data):
            """
            Handles file listing requests from Gateway (GUI) via Socket.IO.
            This is the active handler, not the REST one!
            """
            self.logger.info(f"[GatewayConnector] Received 'filesystem_list_request' from Gateway")

            payload = data
            if isinstance(data, dict) and data.get('v') == CURRENT_PAYLOAD_VERSION:
                payload = data.get('payload', {})

            req_path = payload.get('path', '')

            normalized_req = os.path.normpath(req_path).replace("\\", "/") if req_path else ""
            if normalized_req == "/app" or normalized_req.startswith("/app/") or "FLOWORK" in normalized_req.upper():
                 self.logger.warning(f"[FS] Blocked access to protected path: {req_path}")
                 await self.sio.emit('FILESYSTEM_LIST_RESPONSE', {
                        'error': '⛔ Access Denied: Protected System Folder',
                        'path': req_path
                    }, namespace='/engine-socket')
                 return

            try:
                if not req_path:
                    items = []
                    video_paths = ["/mnt/videos", "/host_mnt/c/Users", "/mnt/c/Users", "/mnt"]
                    for v_path in video_paths:
                        if os.path.exists(v_path):
                            label = "📂 Videos (Mounted)" if "videos" in v_path else f"💾 Drive ({v_path})"
                            items.append({
                                "name": label,
                                "is_dir": True,
                                "path": v_path,
                                "type": "drive"
                            })

                    items.append({
                        "name": "💻 Linux Root (/)",
                        "is_dir": True,
                        "path": "/",
                        "type": "drive"
                    })

                    response_payload = {'path': '', 'items': items}
                    await self.sio.emit('FILESYSTEM_LIST_RESPONSE', response_payload, namespace='/engine-socket')
                    self.logger.info(f"[FS] Sent DRIVE LIST ({len(items)} items)")
                    return

                target_path = os.path.abspath(req_path)

                if not os.path.isdir(target_path):
                    await self.sio.emit('FILESYSTEM_LIST_RESPONSE', {
                        'error': f'Invalid directory: {target_path}',
                        'path': req_path
                    }, namespace='/engine-socket')
                    return

                items = []
                try:
                    SYSTEM_FOLDERS = ['proc', 'sys', 'dev', 'run', 'boot', 'etc', 'var', 'tmp', 'usr', 'bin', 'sbin', 'lib', 'lib64', 'opt', 'srv', 'root', 'app']

                    dir_content = sorted(os.listdir(target_path), key=lambda s: s.lower())

                    for item_name in dir_content:
                        if item_name.startswith('.'): continue

                        if target_path == "/" and item_name in SYSTEM_FOLDERS: continue

                        if "FLOWORK" in item_name.upper(): continue

                        item_path = os.path.join(target_path, item_name)
                        is_dir = os.path.isdir(item_path)
                        items.append({
                            "name": item_name,
                            "is_dir": is_dir,
                            "path": os.path.abspath(item_path).replace(os.sep, '/')
                        })

                except Exception as list_err:
                    self.logger.error(f"[FS] Error listing dir {target_path}: {list_err}")
                    await self.sio.emit('FILESYSTEM_LIST_RESPONSE', {
                        'error': f'Cannot read directory: {str(list_err)}',
                        'path': req_path
                    }, namespace='/engine-socket')
                    return

                response_payload = {
                    'path': target_path.replace(os.sep, '/'),
                    'items': items
                }

                await self.sio.emit('FILESYSTEM_LIST_RESPONSE', response_payload, namespace='/engine-socket')
                self.logger.info(f"[FS] Sent list response for {target_path} ({len(items)} items)")

            except Exception as e:
                self.logger.error(f"[FS] Critical error processing request: {e}", exc_info=True)
                await self.sio.emit('FILESYSTEM_LIST_RESPONSE', {
                    'error': f'Server Error: {str(e)}',
                    'path': req_path
                }, namespace='/engine-socket')

        @self.sio.event(namespace='/engine-socket')
        async def request_settings(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                self.logger.error(f"[Core] Received non-versioned 'request_settings'. Ignoring.")
                return

            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            self.logger.info(f"Received 'request_settings' from user {user_id}")
            settings_data = {}
            error_msg = None
            try:
                loc_manager = self.service.kernel_services.get("localization_manager")
                if loc_manager:
                    settings_data = loc_manager.get_all_settings(user_id=user_id)
                else:
                    error_msg = "LocalizationManager not found."
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"[Core] Error processing 'request_settings': {e}", exc_info=True)

            versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                'settings': settings_data,
                'error': error_msg,
                '_target_user_id': user_id
            }}
            await self.sio.emit('settings_response', versioned_response, namespace='/engine-socket')
            self.logger.info(f"Sent 'settings_response' to user {user_id}")

        @self.sio.event(namespace='/engine-socket')
        async def save_settings(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                self.logger.error(f"[Core] Received non-versioned 'save_settings'. Ignoring.")
                return

            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            settings_to_save = real_data.get('settings')
            self.logger.info(f"Received 'save_settings' from user {user_id}")
            try:
                loc_manager = self.service.kernel_services.get("localization_manager")
                if loc_manager:
                    loc_manager._save_settings(settings_to_save, user_id=user_id)
                else:
                    raise Exception("LocalizationManager not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'save_settings': {e}", exc_info=True)

        @self.sio.on('*', namespace='/engine-socket')
        async def catch_all(event, data):
            known_events = [
                'connect',
                'auth_success',
                'auth',
                'auth_failed',
                'disconnect',
                'request_presets_list',
                'save_preset',
                'request_variables',
                'engine_ready',
                'engine_vitals_update',
                'forward_event_to_gui',
                'execute_workflow',
                'request_components_list',
                'request_settings',
                'save_settings',
                'update_variable',
                'delete_variable',
                'request_prompts_list',
                'update_prompt',
                'delete_prompt',
                'request_local_models',
                'start_training_job',
                'request_training_job_status',
                'request_datasets_list',
                'load_dataset_data',
                'create_dataset',
                'add_dataset_data',
                'delete_dataset',
                'update_dataset_row',
                'delete_dataset_row',
                'install_component',
                'uninstall_component',
                'gw:start_session',
                'gw:cancel_session',
                'gw:agent_input',
                'stop_workflow',
                'pause_workflow',
                'gateway:execute_swarm_task',
                'gateway:swarm_task_result',
                'core:request_swarm_task',
                'core:swarm_task_result',
                'delete_preset',
                'request_load_preset',
                'response_load_preset',
                'execute_standalone_node',
                'filesystem_list_request' # Added to known events
            ]
            if event not in known_events:
                self.logger.warning(f"Received unhandled event '{event}' in /engine-socket namespace.")
