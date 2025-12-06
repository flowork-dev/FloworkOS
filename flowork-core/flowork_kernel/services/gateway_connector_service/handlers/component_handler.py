########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\component_handler.py total lines 172 
########################################################################

import asyncio
from .base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

class ComponentHandler(BaseHandler):
    def register_events(self):
        @self.sio.event(namespace='/engine-socket')
        async def request_components_list(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                self.logger.error(f"[Core] Received non-versioned 'request_components_list'. Ignoring.")
                return

            real_data = data.get('payload', {})
            user_context = real_data.get('user_context', {})
            user_id = user_context.get('id')
            component_type = real_data.get('component_type')
            self.logger.info(f"Received 'request_components_list' from user {user_id} for type: {component_type}")

            manager_map = {
                'modules': 'module_manager_service',
                'plugins': 'plugin_manager_service',
                'tools': 'tools_manager_service',
                'triggers': 'trigger_manager_service'
            }
            manager_name = manager_map.get(component_type)
            components_list = []
            error_msg = None

            if manager_name:
                manager = self.service.kernel_services.get(manager_name)
                if manager:
                    try:
                        items_attr_map = {
                            "module_manager_service": "loaded_modules",
                            "plugin_manager_service": "loaded_plugins",
                            "tools_manager_service": "loaded_tools",
                            "trigger_manager_service": "loaded_triggers",
                        }
                        items_attr_name = items_attr_map.get(manager.service_id)
                        items = getattr(manager, items_attr_name, {})

                        for item_id_loop, item_data in items.items():
                            manifest = item_data.get("manifest", {})
                            components_list.append(
                                {
                                    "id": item_id_loop,
                                    "name": manifest.get("name", item_id_loop),
                                    "version": manifest.get("version", "N/A"),
                                    "is_paused": item_data.get("is_paused", False),
                                    "description": manifest.get("description", ""),
                                    "is_core": False,
                                    "tier": manifest.get("tier", "free"),
                                    "is_installed": item_data.get("is_installed", False),
                                    "manifest": manifest,
                                }
                            )
                    except Exception as e:
                        error_msg = f"Error processing component list: {e}"
                        self.logger.error(f"[Core] {error_msg}", exc_info=True)
                else:
                    error_msg = f"Component manager '{manager_name}' not found."
                    self.logger.error(f"[Core] {error_msg}")
            else:
                error_msg = f"Invalid component type '{component_type}'."
                self.logger.error(f"[Core] {error_msg}")

            versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                'component_type': component_type,
                'components': components_list,
                'error': error_msg,
                '_target_user_id': user_id
            }}
            await self.sio.emit('response_component_list', versioned_response, namespace='/engine-socket')
            self.logger.info(f"Sent 'response_component_list' for {component_type} to user {user_id}. Count: {len(components_list)}")

        @self.sio.event(namespace='/engine-socket')
        async def install_component(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            component_type = real_data.get('component_type')
            component_id = real_data.get('component_id')
            self.logger.info(f"Received 'install_component' from user {user_id} for {component_id}")

            manager_map = {
                'modules': 'module_manager_service',
                'plugins': 'plugin_manager_service',
                'tools': 'tools_manager_service',
                'triggers': 'trigger_manager_service'
            }
            manager_name = manager_map.get(component_type)
            manager = self.service.kernel_services.get(manager_name)

            if not manager:
                self.logger.error(f"Cannot install {component_id}: Manager {manager_name} not found.")
                return

            def on_complete(cid, success, message):
                self.logger.info(f"Install complete for {cid}: Success={success}, Msg={message}")
                async def send_update():
                    versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                        'component_id': cid,
                        'component_type': component_type,
                        'success': success,
                        'message': message,
                        'is_installed': True,
                        '_target_user_id': user_id
                    }}
                    await self.sio.emit('component_install_status', versioned_response, namespace='/engine-socket')
                    await request_components_list(data)
                try:
                    asyncio.run_coroutine_threadsafe(send_update(), asyncio.get_event_loop())
                except RuntimeError:
                    self.logger.warning("[Install Callback] No event loop, trying asyncio.run()")
                    try:
                        asyncio.run(send_update())
                    except Exception as e:
                        self.logger.error(f"[Install Callback] asyncio.run() failed: {e}")


            manager.install_component_dependencies(component_id, on_complete)

        @self.sio.event(namespace='/engine-socket')
        async def uninstall_component(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            component_type = real_data.get('component_type')
            component_id = real_data.get('component_id')
            self.logger.info(f"Received 'uninstall_component' from user {user_id} for {component_id}")

            manager_map = {
                'modules': 'module_manager_service',
                'plugins': 'plugin_manager_service',
                'tools': 'tools_manager_service',
                'triggers': 'trigger_manager_service'
            }
            manager_name = manager_map.get(component_type)
            manager = self.service.kernel_services.get(manager_name)

            if not manager:
                self.logger.error(f"Cannot uninstall {component_id}: Manager {manager_name} not found.")
                return

            def on_complete(cid, success, message):
                self.logger.info(f"Uninstall complete for {cid}: Success={success}, Msg={message}")
                async def send_update():
                    versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                        'component_id': cid,
                        'component_type': component_type,
                        'success': success,
                        'message': message,
                        'is_installed': False,
                        '_target_user_id': user_id
                    }}
                    await self.sio.emit('component_install_status', versioned_response, namespace='/engine-socket')
                    await request_components_list(data)
                try:
                    asyncio.run_coroutine_threadsafe(send_update(), asyncio.get_event_loop())
                except RuntimeError:
                    self.logger.warning("[Uninstall Callback] No event loop, trying asyncio.run()")
                    try:
                        asyncio.run(send_update())
                    except Exception as e:
                        self.logger.error(f"[Uninstall Callback] asyncio.run() failed: {e}")

            manager.uninstall_component_dependencies(component_id, on_complete)
