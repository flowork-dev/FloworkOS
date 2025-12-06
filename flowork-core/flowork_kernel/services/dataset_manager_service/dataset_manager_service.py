########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\dataset_manager_service\dataset_manager_service.py total lines 247 
########################################################################

import os
import threading
import json
import uuid
import traceback
import glob
import time
import shutil
import math
from ..base_service import BaseService

class DatasetManagerService(BaseService):
    TRAINING_DIR_NAME = "training"
    CHUNK_SIZE = 10000  # [CONFIG] Maksimal 10.000 data per file JSON

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)

        current_root = os.getcwd()
        if hasattr(self.kernel, 'project_root_path') and self.kernel.project_root_path:
            current_root = self.kernel.project_root_path

        if os.path.basename(current_root) == "flowork-core":
            self.base_path = os.path.abspath(os.path.join(current_root, "..", self.TRAINING_DIR_NAME))
        else:
            self.base_path = os.path.abspath(os.path.join(current_root, self.TRAINING_DIR_NAME))

        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

        self.lock = threading.Lock()

    def register_routes(self, api_router):
        api_router.add_route('/api/v1/datasets', self._handle_list_datasets, methods=['GET'])
        api_router.add_route('/api/v1/datasets', self._handle_create_dataset, methods=['POST'])
        api_router.add_route('/api/v1/datasets', self._handle_options, methods=['OPTIONS'])

        api_router.add_route('/api/v1/datasets/<name>', self._handle_delete_dataset, methods=['DELETE'])
        api_router.add_route('/api/v1/datasets/<name>', self._handle_options, methods=['OPTIONS'])

        api_router.add_route('/api/v1/datasets/<name>/data', self._handle_get_dataset_data, methods=['GET'])
        api_router.add_route('/api/v1/datasets/<name>/data', self._handle_add_data, methods=['POST'])
        api_router.add_route('/api/v1/datasets/<name>/data', self._handle_options, methods=['OPTIONS'])

        api_router.add_route('/api/v1/datasets/<name>/data/<row_id>', self._handle_update_row, methods=['PUT'])
        api_router.add_route('/api/v1/datasets/<name>/data/<row_id>', self._handle_delete_row, methods=['DELETE'])
        api_router.add_route('/api/v1/datasets/<name>/data/<row_id>', self._handle_options, methods=['OPTIONS'])

    def _handle_options(self, request, **kwargs):
        return {"status": "success", "message": "Preflight OK", "_headers": self._cors_headers()}

    def _cors_headers(self):
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, x-gateway-token"
        }


    def list_datasets(self):
        results = []
        try:
            if not os.path.exists(self.base_path): return []
            items = os.listdir(self.base_path)
            for item in items:
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path):
                    json_files = glob.glob(os.path.join(item_path, "*.json"))
                    results.append({"name": item, "count": f"{len(json_files)} Chunks"})
        except Exception as e:
            print(f"[DatasetManager] List Error: {e}")
        return results

    def create_dataset(self, name: str):
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
        path = os.path.join(self.base_path, safe_name)
        if os.path.exists(path): return False
        os.makedirs(path, exist_ok=True)
        return True

    def get_dataset_data(self, dataset_name: str):
        path = os.path.join(self.base_path, dataset_name)
        if not os.path.exists(path): return []

        all_data = []
        json_files = glob.glob(os.path.join(path, "*.json"))
        json_files.sort(key=os.path.getmtime, reverse=True)

        for jf in json_files[:20]:
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list): all_data.extend(data)
                    elif isinstance(data, dict): all_data.append(data)
            except: pass

        return all_data

    def add_data_to_dataset(self, dataset_name: str, data_list: list):
        """
        [BATCHING STRATEGY]
        1. Proses semua data (kasih ID, format messages).
        2. Pecah jadi chunk per 10.000 (self.CHUNK_SIZE).
        3. Save setiap chunk ke file unik.
        """
        dataset_path = os.path.join(self.base_path, dataset_name)
        if not os.path.exists(dataset_path): return False

        processed_list = []
        for item in data_list:
            if 'id' not in item or not item['id']: item['id'] = str(uuid.uuid4())

            if 'prompt' in item and 'response' in item and 'messages' not in item:
                item['messages'] = [
                    {"role": "user", "content": item['prompt']},
                    {"role": "assistant", "content": item['response']}
                ]
            processed_list.append(item)

        total_items = len(processed_list)
        num_chunks = math.ceil(total_items / self.CHUNK_SIZE)

        for i in range(num_chunks):
            start_idx = i * self.CHUNK_SIZE
            end_idx = start_idx + self.CHUNK_SIZE
            chunk_data = processed_list[start_idx:end_idx]

            timestamp = int(time.time() * 1000)
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{dataset_name}_{timestamp}_{unique_id}_part{i+1}.json"
            file_path = os.path.join(dataset_path, filename)

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f, indent=2)
            except Exception as e:
                print(f"[DatasetManager] Failed to save chunk {filename}: {e}")
                return False

        return True

    def delete_dataset(self, name: str):
        path = os.path.join(self.base_path, name)
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
        return False

    def delete_dataset_row(self, dataset_name: str, row_id: str):
        path = os.path.join(self.base_path, dataset_name)
        if not os.path.exists(path): return False

        files = glob.glob(os.path.join(path, "*.json"))

        for f_path in files:
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data_list = json.load(f)

                original_len = len(data_list)
                filtered_list = [d for d in data_list if d.get('id') != row_id]

                if len(filtered_list) < original_len:
                    with open(f_path, 'w', encoding='utf-8') as f:
                        json.dump(filtered_list, f, indent=2)
                    return True
            except: pass

        return False

    def update_dataset_row(self, dataset_name: str, row_data: dict):
        path = os.path.join(self.base_path, dataset_name)
        if not os.path.exists(path): return False

        row_id = row_data.get('id')
        if not row_id: return False

        files = glob.glob(os.path.join(path, "*.json"))
        for f_path in files:
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    data_list = json.load(f)

                found = False
                for i, item in enumerate(data_list):
                    if item.get('id') == row_id:
                        if 'prompt' in row_data and 'response' in row_data:
                            row_data['messages'] = [
                                {"role": "user", "content": row_data['prompt']},
                                {"role": "assistant", "content": row_data['response']}
                            ]
                        data_list[i] = {**item, **row_data}
                        found = True
                        break

                if found:
                    with open(f_path, 'w', encoding='utf-8') as f:
                        json.dump(data_list, f, indent=2)
                    return True
            except: pass

        return False

    def _handle_list_datasets(self, request):
        return {"status": "success", "data": self.list_datasets(), "_headers": self._cors_headers()}

    def _handle_create_dataset(self, request):
        try:
            name = request.json.get("name")
            if not name: return {"status": "error"}, 400
            if self.create_dataset(name):
                return {"status": "success"}, 200
            return {"status": "error", "message": "Exists"}, 409
        except Exception as e: return {"status": "error", "message": str(e)}, 500

    def _handle_delete_dataset(self, request, name):
        if self.delete_dataset(name): return {"status": "success"}, 200
        return {"status": "error"}, 404

    def _handle_get_dataset_data(self, request, name):
        return {"status": "success", "data": self.get_dataset_data(name), "_headers": self._cors_headers()}

    def _handle_add_data(self, request, name):
        try:
            data = request.json.get("data")
            if not data: return {"status": "error"}, 400
            if self.add_data_to_dataset(name, data): return {"status": "success"}, 200
            return {"status": "error", "message": "Dataset not found"}, 404
        except Exception as e: return {"status": "error", "message": str(e)}, 500

    def _handle_update_row(self, request, name, row_id):
        try:
            data = request.json
            data['id'] = row_id
            if self.update_dataset_row(name, data): return {"status": "success"}, 200
            return {"status": "error"}, 404
        except: return {"status": "error"}, 500

    def _handle_delete_row(self, request, name, row_id):
        if self.delete_dataset_row(name, row_id): return {"status": "success"}, 200
        return {"status": "error"}, 404
