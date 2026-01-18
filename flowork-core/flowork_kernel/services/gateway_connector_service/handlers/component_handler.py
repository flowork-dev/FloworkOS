########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\component_handler.py total lines 135 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from flowork_kernel.services.gateway_connector_service.handlers.base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION


import asyncio

class ComponentHandler(BaseHandler):
    def register_events(self):
        @self.sio.event(namespace='/engine-socket')
        async def request_components_list(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                self.logger.error(f"[Core] Received non-versioned 'request_components_list'.")
                return

            real_data = data.get('payload', {})
            user_context = real_data.get('user_context', {})
            user_id = user_context.get('id')
            component_type = real_data.get('component_type')
            self.logger.info(f"Received 'request_components_list' for: {component_type}")

            components_list = []
            error_msg = None
            app_service = self.service.kernel_services.get('app_service')

            if app_service:
                try:
                    norm_cat = component_type if component_type.endswith('s') else f"{component_type}s"

                    items = getattr(app_service, f"loaded_{norm_cat}", None)

                    if not items or len(items) == 0:
                        self.logger.info(f"[Core] Registry for {norm_cat} is empty. Triggering emergency sync.")
                        items = app_service.sync(norm_cat)

                    if items:
                        for item_id, item_data in items.items():
                            manifest = item_data.get("manifest", {})

                            nodes_with_ports = []
                            for node in manifest.get("nodes", []):
                                nodes_with_ports.append({
                                    "id": node.get("id"),
                                    "label": node.get("label") or node.get("name"),
                                    "type": node.get("type", "action"),
                                    "icon": node.get("icon", "mdi-puzzle"),
                                    "input_ports": node.get("input_ports", []),
                                    "output_ports": node.get("output_ports", []),
                                    "inputs": node.get("inputs", []) # Untuk Properties Panel Form
                                })

                            components_list.append({
                                "id": item_id,
                                "name": manifest.get("name", item_id),
                                "version": manifest.get("version", "N/A"),
                                "is_paused": item_data.get("is_paused", False),
                                "description": manifest.get("description", ""),
                                "is_core": item_data.get("is_core", False),
                                "tier": manifest.get("tier", "free"),
                                "is_installed": item_data.get("is_installed", False),
                                "componentType": component_type,
                                "manifest": manifest,
                                "nodes": nodes_with_ports, # [NEW] Injecting explicit ports mapping
                                "icon": manifest.get("icon", "mdi-cube-outline"),

                                "icon_url": item_data.get("icon_url"),
                                "gui_url": item_data.get("gui_url"),
                                "entry_point": item_data.get("entry_point")
                            })
                except Exception as e:
                    error_msg = f"Error processing list for {component_type}: {e}"
                    self.logger.error(f"[Core] {error_msg}", exc_info=True)
            else:
                error_msg = "Unified AppService not found."

            versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                'component_type': component_type,
                'components': components_list,
                'error': error_msg,
                '_target_user_id': user_id
            }}
            await self.sio.emit('response_component_list', versioned_response, namespace='/engine-socket')
            self.logger.info(f"Response sent for {component_type}. Found: {len(components_list)}")

        @self.sio.event(namespace='/engine-socket')
        async def install_component(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            component_type = real_data.get('component_type')
            component_id = real_data.get('component_id')
            app_service = self.service.kernel_services.get('app_service')
            if not app_service: return
            def on_complete(cid, success, message):
                async def send_update():
                    versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                        'component_id': cid, 'component_type': component_type,
                        'success': success, 'message': message, 'is_installed': True,
                        '_target_user_id': user_id
                    }}
                    await self.sio.emit('component_install_status', versioned_response, namespace='/engine-socket')
                    await request_components_list(data)
                loop = asyncio.get_event_loop()
                if loop.is_running(): asyncio.run_coroutine_threadsafe(send_update(), loop)
                else: asyncio.run(send_update())
            if hasattr(app_service, 'install_component'):
                app_service.install_component(component_id, component_type, on_complete)

        @self.sio.event(namespace='/engine-socket')
        async def uninstall_component(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            component_type = real_data.get('component_type')
            component_id = real_data.get('component_id')
            app_service = self.service.kernel_services.get('app_service')
            if not app_service: return
            def on_complete(cid, success, message):
                async def send_update():
                    versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                        'component_id': cid, 'component_type': component_type,
                        'success': success, 'message': message, 'is_installed': False,
                        '_target_user_id': user_id
                    }}
                    await self.sio.emit('component_install_status', versioned_response, namespace='/engine-socket')
                    await request_components_list(data)
                loop = asyncio.get_event_loop()
                if loop.is_running(): asyncio.run_coroutine_threadsafe(send_update(), loop)
                else: asyncio.run(send_update())
            if hasattr(app_service, 'uninstall_component'):
                app_service.uninstall_component(component_id, component_type, on_complete)
