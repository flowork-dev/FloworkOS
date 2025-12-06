########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\handlers\data_handler.py total lines 383 
########################################################################

import json
from flowork_kernel.singleton import Singleton
from flowork_kernel.services.variable_manager_service.variable_manager_service import VariableManagerService
from .base_handler import BaseHandler, CURRENT_PAYLOAD_VERSION

class DataHandler(BaseHandler):
    def register_events(self):
        @self.sio.event(namespace='/engine-socket')
        async def request_presets_list(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                self.logger.error(f"[Core] Received non-versioned 'request_presets_list'. Ignoring.")
                return
            real_data = data.get('payload', {})
            user_context = real_data.get('user_context', {})
            user_id = user_context.get('id')
            self.logger.info(f"Received 'request_presets_list' from user {user_id}")
            try:
                preset_manager = self.service.kernel_services.get("preset_manager_service")
                if preset_manager:
                    presets = preset_manager.get_preset_list(user_id)
                    versioned_response = {
                        'v': CURRENT_PAYLOAD_VERSION,
                        'payload': {'presets': presets, '_target_user_id': user_id}
                    }
                    await self.sio.emit('response_presets_list', versioned_response, namespace='/engine-socket')
                    self.logger.info(f"Sent preset list to user {user_id}. Count: {len(presets)}")
                else:
                    self.logger.error("'preset_manager_service' not found in kernel services.")
                    versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'presets': [], 'error': 'Preset service unavailable', '_target_user_id': user_id}}
                    await self.sio.emit('response_presets_list', versioned_response, namespace='/engine-socket')
            except Exception as e:
                self.logger.error(f"Error processing 'request_presets_list': {e}", exc_info=True)
                versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'presets': [], 'error': str(e), '_target_user_id': user_id}}
                await self.sio.emit('response_presets_list', versioned_response, namespace='/engine-socket')

        @self.sio.event(namespace='/engine-socket')
        async def save_preset(data):
            preset_name = None
            try:
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                    self.logger.error(f"[Core] Received non-versioned 'save_preset'. Ignoring.")
                    return
                real_data = data.get('payload', {})
                user_context = real_data.get('user_context', {})
                user_id = user_context.get('id')
                public_address = user_context.get('public_address')
                preset_name = real_data.get('name')
                preset_data = real_data.get('workflow_data')
                signature = real_data.get('signature')
                if not signature:
                    self.logger.error(f"Received 'save_preset' without signature from user {user_id}. Ignoring.")
                    return

                self.logger.info(f"Received 'save_preset' request from user {user_id} for preset: {preset_name}")
                preset_manager = self.service.kernel_services.get("preset_manager_service")
                if not preset_manager:
                    self.logger.error("'preset_manager_service' not found. Cannot save preset.")
                    return
                try:
                    preset_manager.save_preset(
                        name=preset_name,
                        workflow_data=preset_data,
                        user_id=user_id,
                        signature=signature,
                        public_address=public_address # (English Hardcode) ADDED BY BEO
                    )
                    self.logger.info(f"Successfully saved preset {preset_name} for user {user_id}")
                except Exception as e:
                    self.logger.error(f"Could not save preset '{preset_name}': {e}", exc_info=True)
            except Exception as e:
                self.logger.error(f"Error handling 'save_preset' (outer try): {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def delete_preset(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            preset_name = real_data.get('name')
            self.logger.info(f"Received 'delete_preset' from user {user_id} for preset: {preset_name}")
            try:
                preset_manager = self.service.kernel_services.get("preset_manager_service")
                if preset_manager:
                    preset_manager.delete_preset(preset_name, user_id=user_id)
                    self.logger.info(f"Successfully deleted preset '{preset_name}' for user {user_id}")
                    await request_presets_list({'v': CURRENT_PAYLOAD_VERSION, 'payload': real_data})
                else:
                    raise Exception("PresetManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'delete_preset': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def request_load_preset(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            preset_name = real_data.get('name')
            self.logger.info(f"Received 'request_load_preset' from user {user_id} for preset: {preset_name}")

            preset_data = None
            error_msg = None
            try:
                preset_manager = self.service.kernel_services.get("preset_manager_service")
                if preset_manager:
                    preset_data = preset_manager.get_preset_data(preset_name, user_id=user_id)
                    if preset_data is None:
                        error_msg = "Preset not found."
                else:
                    error_msg = "PresetManagerService not found."
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'request_load_preset': {e}", exc_info=True)
                error_msg = str(e)

            versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                'name': preset_name,
                'workflow_data': preset_data,
                'error': error_msg,
                '_target_user_id': user_id
            }}
            await self.sio.emit('response_load_preset', versioned_response, namespace='/engine-socket')
            self.logger.info(f"Sent 'response_load_preset' to user {user_id} for preset '{preset_name}'")


        @self.sio.event(namespace='/engine-socket')
        async def request_variables(data):
            try:
                if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                    self.logger.error(f"[Core] Received non-versioned 'request_variables'. Ignoring.")
                    return
                real_data = data.get('payload', {})
                user_id = real_data.get('user_context', {}).get('id')
                self.logger.info(f"Received 'request_variables' from user {user_id}")
                variable_manager = Singleton.get_instance(VariableManagerService)
                variables_list = []
                if variable_manager:
                    variables_list = variable_manager.get_all_variables_for_api(user_id=user_id)
                else:
                    self.logger.error("VariableManagerService not found in Singleton. Cannot get variables.")
                versioned_response = {
                    'v': CURRENT_PAYLOAD_VERSION,
                    'payload': {'variables': variables_list, '_target_user_id': user_id}
                }
                await self.sio.emit('response_variables', versioned_response, namespace='/engine-socket')
                self.logger.info(f"Sent 'response_variables' back to user {user_id}")
            except Exception as e:
                self.logger.error(f"Error handling 'request_variables': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def update_variable(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            var_name = real_data.get('name')
            var_data = real_data.get('data')
            self.logger.info(f"Received 'update_variable' from user {user_id} for var: {var_name}")
            try:
                var_manager = Singleton.get_instance(VariableManagerService)
                if var_manager:
                    var_manager.set_variable(
                        var_name,
                        var_data.get('value'),
                        var_data.get('is_secret', False),
                        var_data.get('is_enabled', True),
                        mode=var_data.get('mode', 'single'),
                        user_id=user_id
                    )
            except Exception as e:
                    self.logger.error(f"[Core] Error processing 'update_variable': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def delete_variable(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            var_name = real_data.get('name')
            self.logger.info(f"Received 'delete_variable' from user {user_id} for var: {var_name}")
            try:
                var_manager = Singleton.get_instance(VariableManagerService)
                if var_manager:
                    var_manager.delete_variable(var_name, user_id=user_id)
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'delete_variable': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def request_prompts_list(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            self.logger.info(f"Received 'request_prompts_list' from user {user_id}")
            prompts_list = []
            error_msg = None
            try:
                prompt_manager = self.service.kernel_services.get("prompt_manager_service")
                if prompt_manager:
                    prompts_list = prompt_manager.get_all_prompts()
                else:
                    error_msg = "PromptManagerService not found."
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"[Core] Error processing 'request_prompts_list': {e}", exc_info=True)

            versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {
                'prompts': prompts_list,
                'error': error_msg,
                '_target_user_id': user_id
            }}
            await self.sio.emit('response_prompts_list', versioned_response, namespace='/engine-socket')
            self.logger.info(f"Sent 'response_prompts_list' to user {user_id}")

        @self.sio.event(namespace='/engine-socket')
        async def update_prompt(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            prompt_data = real_data.get('prompt_data')
            self.logger.info(f"Received 'update_prompt' from user {user_id}")
            try:
                prompt_manager = self.service.kernel_services.get("prompt_manager_service")
                if prompt_manager:
                    if 'id' in prompt_data and prompt_data['id']:
                        prompt_manager.update_prompt(prompt_data['id'], prompt_data)
                    else:
                        prompt_manager.create_prompt(prompt_data)
                    await request_prompts_list(data)
                else:
                    raise Exception("PromptManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'update_prompt': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def delete_prompt(data):
            """ (English Hardcode) Handles delete prompt from Gateway """
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION:
                return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            prompt_id = real_data.get('prompt_id')
            self.logger.info(f"Received 'delete_prompt' from user {user_id} for prompt: {prompt_id}")
            try:
                prompt_manager = self.service.kernel_services.get("prompt_manager_service")
                if prompt_manager:
                    prompt_manager.delete_prompt(prompt_id)
                    await request_prompts_list(data)
                else:
                    raise Exception("PromptManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'delete_prompt': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def request_datasets_list(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            self.logger.info(f"Received 'request_datasets_list' from user {user_id}")
            datasets_list = []
            error_msg = None
            try:
                dataset_manager = self.service.kernel_services.get("dataset_manager_service")
                if dataset_manager:
                    datasets_list = dataset_manager.list_datasets()
                else:
                    error_msg = "DatasetManagerService not found."
            except Exception as e:
                error_msg = str(e)
            versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'datasets': datasets_list, 'error': error_msg, '_target_user_id': user_id}}
            await self.sio.emit('response_datasets_list', versioned_response, namespace='/engine-socket')

        @self.sio.event(namespace='/engine-socket')
        async def load_dataset_data(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            name = real_data.get('name')
            self.logger.info(f"Received 'load_dataset_data' from user {user_id} for {name}")
            dataset_data = []
            error_msg = None
            try:
                dataset_manager = self.service.kernel_services.get("dataset_manager_service")
                if dataset_manager:
                    dataset_data = dataset_manager.get_dataset_data(name)
                else:
                    error_msg = "DatasetManagerService not found."
            except Exception as e:
                error_msg = str(e)
            versioned_response = {'v': CURRENT_PAYLOAD_VERSION, 'payload': {'data': dataset_data, 'error': error_msg, '_target_user_id': user_id}}
            await self.sio.emit('response_dataset_data', versioned_response, namespace='/engine-socket')

        @self.sio.event(namespace='/engine-socket')
        async def create_dataset(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            name = real_data.get('name')
            self.logger.info(f"Received 'create_dataset' from user {user_id} for {name}")
            try:
                dataset_manager = self.service.kernel_services.get("dataset_manager_service")
                if dataset_manager:
                    dataset_manager.create_dataset(name)
                    await request_datasets_list(data)
                else:
                    raise Exception("DatasetManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'create_dataset': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def add_dataset_data(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            name = real_data.get('name')
            rows = real_data.get('data')
            self.logger.info(f"Received 'add_dataset_data' from user {user_id} for {name}")
            try:
                dataset_manager = self.service.kernel_services.get("dataset_manager_service")
                if dataset_manager:
                    dataset_manager.add_data_to_dataset(name, rows)
                    await load_dataset_data(data)
                else:
                    raise Exception("DatasetManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'add_dataset_data': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def delete_dataset(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            name = real_data.get('name')
            self.logger.info(f"Received 'delete_dataset' from user {user_id} for {name}")
            try:
                dataset_manager = self.service.kernel_services.get("dataset_manager_service")
                if dataset_manager:
                    dataset_manager.delete_dataset(name)
                    await request_datasets_list(data)
                else:
                    raise Exception("DatasetManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'delete_dataset': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def update_dataset_row(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            name = real_data.get('name')
            row_data = real_data.get('row_data')
            self.logger.info(f"Received 'update_dataset_row' from user {user_id} for {name}")
            try:
                dataset_manager = self.service.kernel_services.get("dataset_manager_service")
                if dataset_manager:
                    dataset_manager.update_dataset_row(name, row_data)
                    await load_dataset_data(data)
                else:
                    raise Exception("DatasetManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'update_dataset_row': {e}", exc_info=True)

        @self.sio.event(namespace='/engine-socket')
        async def delete_dataset_row(data):
            if not isinstance(data, dict) or data.get('v') != CURRENT_PAYLOAD_VERSION: return
            real_data = data.get('payload', {})
            user_id = real_data.get('user_context', {}).get('id')
            name = real_data.get('name')
            row_id = real_data.get('row_id')
            self.logger.info(f"Received 'delete_dataset_row' from user {user_id} for {name}")
            try:
                dataset_manager = self.service.kernel_services.get("dataset_manager_service")
                if dataset_manager:
                    dataset_manager.delete_dataset_row(name, row_id)
                    await load_dataset_data(data)
                else:
                    raise Exception("DatasetManagerService not found.")
            except Exception as e:
                self.logger.error(f"[Core] Error processing 'delete_dataset_row': {e}", exc_info=True)
