########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\flowork-gui-lite\lib\api_client.py total lines 162 
########################################################################

import requests
import json
import os
class ApiClient:
    def __init__(self, kernel_for_logging=None):
        self.kernel_logger = None
        self.base_url = self._load_gateway_url()
        self.session = requests.Session()
        self.api_key = self._load_api_key()
    def _load_api_key(self):
        try:
            gui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            project_root = os.path.abspath(os.path.join(gui_root, ".."))
            variables_path = os.path.join(
                project_root, "flowork-core", "data", "variables.json"
            )
            if os.path.exists(variables_path):
                with open(variables_path, "r", encoding="utf-8") as f:
                    variables = json.load(f)
                    api_key_data = variables.get("FLOWORK_API_KEY")
                    if api_key_data and api_key_data.get("value"):
                        self._log("Successfully loaded API Key for client.", "SUCCESS")
                        return api_key_data.get("value")
        except Exception as e:
            self._log(f"Could not load API key from variables.json: {e}", "ERROR")
        self._log("API Key not found. API calls will likely be unauthorized.", "WARN")
        return None
    def _load_gateway_url(self):
        try:
            gui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            config_path = os.path.join(gui_root, "servers.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    servers = json.load(f)
                    if servers and isinstance(servers, list) and servers[0]:
                        self._log(
                            f"ApiClient configured to use Gateway URL: {servers[0]}",
                            "INFO",
                        )
                        return servers[0]
        except Exception as e:
            self._log(f"Could not load Gateway URL from servers.json: {e}", "CRITICAL")
        self._log("Gateway URL not found, using fallback: http://localhost", "WARN")
        return "http://localhost"
    def _log(self, message, level="INFO"):
        if self.kernel_logger:
            self.kernel_logger(f"[ApiClient] {message}", level)
        else:
            print(f"[ApiClient] [{level}] {message}")
    def _make_request(self, method, endpoint, json_data=None, params=None):
        if not self.base_url:
            return False, {
                "error": "Gateway URL is not configured in flowork-gui/servers.json"
            }
        if not self.api_key:
            self.api_key = self._load_api_key()
        full_endpoint = f"api/v1/{endpoint.lstrip('/')}"
        url = f"{self.base_url.rstrip('/')}/{full_endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return True, {}
            response_json = response.json()
            return True, response_json
        except requests.exceptions.HTTPError as e:
            error_msg = f"API HTTP Error for {method} {url}: {e.response.status_code}"
            self._log(error_msg, "ERROR")
            try:
                return False, e.response.json()
            except json.JSONDecodeError:
                return False, {"error": error_msg, "details": e.response.text}
        except requests.exceptions.RequestException as e:
            error_msg = f"API Request Failed for {method} {url}: Could not connect to Gateway. Details: {e}"
            self._log(error_msg, "ERROR")
            return False, {"error": error_msg}
    def execute_raw_workflow(
        self,
        nodes: list,
        connections: list,
        initial_payload: dict,
        start_node_id: str = None,
    ):
        """Sends the entire workflow structure to the server for immediate execution."""
        payload = {
            "nodes": nodes,
            "connections": connections,
            "initial_payload": initial_payload,
            "start_node_id": start_node_id,
        }
        return self._make_request("POST", "workflow/execute_raw", json_data=payload)
    def get_job_status(self, job_id: str):
        """Polls the server for the status of a specific job."""
        return self._make_request("GET", f"workflow/status/{job_id}")
    def publish_event(self, event_name: str, event_data: dict):
        payload = {"event_name": event_name, "event_data": event_data}
        return self._make_request("POST", "events/publish", json_data=payload)
    def get_themes(self):
        return self._make_request("GET", "themes")
    def add_new_workflow_tab(self):
        return self._make_request("POST", "ui/actions/add_new_workflow_tab")
    def open_managed_tab(self, tab_key: str):
        return self._make_request(
            "POST", "ui/actions/open_managed_tab", json_data={"tab_key": tab_key}
        )
    def get_components(self, component_type: str, component_id: str = None):
        endpoint = f"{component_type}"
        if component_id:
            endpoint += f"/{component_id}"
        return self._make_request("GET", endpoint)
    def get_ai_provider_services(self):
        return self._make_request("GET", "ai_providers/services")
    def get_presets(self):
        return self._make_request("GET", "presets")
    def get_preset_data(self, preset_name: str):
        return self._make_request("GET", f"presets/{preset_name}")
    def get_all_settings(self):
        return self._make_request("GET", "settings")
    def get_state(self, key: str):
        return self._make_request("GET", f"uistate/generic/{key}")
    def set_state(self, key: str, value: any):
        return self._make_request("POST", f"uistate/generic/{key}", json_data=value)
    def delete_state(self, key: str):
        return self._make_request("DELETE", f"uistate/generic/{key}")
    def save_dashboard_layout(self, tab_id: str, layout_data: dict):
        return self._make_request(
            "POST", f"uistate/dashboards/{tab_id}", json_data=layout_data
        )
    def get_dashboard_layout(self, tab_id: str):
        return self._make_request("GET", f"uistate/dashboards/{tab_id}")
    def save_settings(self, settings_data: dict):
        return self._make_request("PATCH", "settings", json_data=settings_data)
    def get_variables(self):
        return self._make_request("GET", "variables")
    def update_variable(self, name, value, is_secret, is_enabled=True, mode=None):
        payload = {"value": value, "is_secret": is_secret, "is_enabled": is_enabled}
        if mode:
            payload["mode"] = mode
        return self._make_request("PUT", f"variables/{name}", json_data=payload)
    def update_variable_state(self, name: str, is_enabled: bool):
        payload = {"enabled": is_enabled}
        return self._make_request("PATCH", f"variables/{name}/state", json_data=payload)
    def delete_variable(self, name):
        return self._make_request("DELETE", f"variables/{name}")
    def trigger_hot_reload(self):
        return self._make_request("POST", "system/actions/hot_reload")
