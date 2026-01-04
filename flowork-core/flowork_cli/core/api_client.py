########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_cli\core\api_client.py total lines 33 
########################################################################

import requests
import json
import os
class ApiClient:

    def __init__(self, base_url="http://localhost:8989/api/v1"):
        self.base_url = base_url
    def _handle_response(self, response):

        if 200 <= response.status_code < 300:
            if response.status_code == 204 or not response.content:
                return True, {}
            return True, response.json()
        else:
            try:
                error_data = response.json()
                message = error_data.get("error", "Unknown API error")
            except json.JSONDecodeError:
                message = response.text
            return False, message
    def get_server_status(self):

        try:
            response = requests.get(f"{self.base_url}/status", timeout=3)
            return self._handle_response(response)
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection to API server failed: {e}"
