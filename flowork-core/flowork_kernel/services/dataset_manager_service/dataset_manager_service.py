########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\dataset_manager_service\dataset_manager_service.py total lines 176 
########################################################################

import os
import threading
import json
import uuid
from ..base_service import BaseService

class DatasetManagerService(BaseService):
    DB_NAME = "datasets.json"

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.db_path = os.path.join(self.kernel.data_path, self.DB_NAME)
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
        """Handler Basa-Basi Browser (CORS Preflight)"""
        return {
            "status": "success",
            "message": "Preflight OK",
            "_headers": self._cors_headers()
        }

    def _cors_headers(self):
        """Header Sakti Penolak Bala CORS"""
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, x-gateway-token"
        }

    def _handle_list_datasets(self, request):
        data = self.list_datasets()
        return {"status": "success", "data": data, "_headers": self._cors_headers()}

    def _handle_create_dataset(self, request):
        try:
            payload = request.json
            name = payload.get("name")
            if not name:
                return {"status": "error", "message": "Name is required", "_headers": self._cors_headers()}, 400

            success = self.create_dataset(name)
            if success:
                return {"status": "success", "message": f"Dataset '{name}' created.", "_headers": self._cors_headers()}
            return {"status": "error", "message": "Dataset already exists.", "_headers": self._cors_headers()}, 409
        except Exception as e:
            return {"status": "error", "message": str(e), "_headers": self._cors_headers()}, 500

    def _handle_delete_dataset(self, request, name):
        success = self.delete_dataset(name)
        if success:
            return {"status": "success", "message": "Dataset deleted.", "_headers": self._cors_headers()}
        return {"status": "error", "message": "Dataset not found.", "_headers": self._cors_headers()}, 404

    def _handle_get_dataset_data(self, request, name):
        data = self.get_dataset_data(name)
        return {"status": "success", "data": data, "_headers": self._cors_headers()}

    def _handle_add_data(self, request, name):
        try:
            payload = request.json
            data_rows = payload.get("data")
            if not data_rows or not isinstance(data_rows, list):
                return {"status": "error", "message": "Field 'data' must be a list.", "_headers": self._cors_headers()}, 400

            success = self.add_data_to_dataset(name, data_rows)
            if success:
                return {"status": "success", "message": "Data added.", "_headers": self._cors_headers()}
            return {"status": "error", "message": "Dataset not found.", "_headers": self._cors_headers()}, 404
        except Exception as e:
            return {"status": "error", "message": str(e), "_headers": self._cors_headers()}, 500

    def _handle_update_row(self, request, name, row_id):
        try:
            payload = request.json
            payload['id'] = row_id
            success = self.update_dataset_row(name, payload)
            if success:
                return {"status": "success", "message": "Row updated.", "_headers": self._cors_headers()}
            return {"status": "error", "message": "Dataset/Row not found.", "_headers": self._cors_headers()}, 404
        except Exception as e:
            return {"status": "error", "message": str(e), "_headers": self._cors_headers()}, 500

    def _handle_delete_row(self, request, name, row_id):
        success = self.delete_dataset_row(name, row_id)
        if success:
            return {"status": "success", "message": "Row deleted.", "_headers": self._cors_headers()}
        return {"status": "error", "message": "Dataset/Row not found.", "_headers": self._cors_headers()}, 404


    def _read_db(self):
        with self.lock:
            if not os.path.exists(self.db_path): return {}
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f: return json.load(f)
            except (json.JSONDecodeError, IOError): return {}

    def _write_db(self, data):
        with self.lock:
            with open(self.db_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

    def list_datasets(self):
        db = self._read_db()
        return [{"name": name} for name in db.keys()]

    def get_dataset_data(self, dataset_name: str):
        db = self._read_db()
        return db.get(dataset_name, [])

    def create_dataset(self, name: str):
        db = self._read_db()
        if name in db: return False
        db[name] = []
        self._write_db(db)
        return True

    def add_data_to_dataset(self, dataset_name: str, data_list: list):
        db = self._read_db()
        if dataset_name not in db: return False
        for item in data_list:
            if 'id' not in item or not item['id']: item['id'] = str(uuid.uuid4())
        db[dataset_name].extend(data_list)
        self._write_db(db)
        return True

    def delete_dataset(self, name: str):
        db = self._read_db()
        if name in db:
            del db[name]
            self._write_db(db)
            return True
        return False

    def update_dataset_row(self, dataset_name: str, row_data: dict):
        db = self._read_db()
        if dataset_name not in db or 'id' not in row_data: return False
        dataset = db[dataset_name]
        for i, row in enumerate(dataset):
            if row.get('id') == row_data['id']:
                dataset[i] = row_data
                self._write_db(db)
                return True
        return False

    def delete_dataset_row(self, dataset_name: str, row_id: str):
        db = self._read_db()
        if dataset_name not in db: return False
        original_count = len(db[dataset_name])
        db[dataset_name] = [row for row in db[dataset_name] if row.get('id') != row_id]
        if len(db[dataset_name]) < original_count:
            self._write_db(db)
            return True
        return False
