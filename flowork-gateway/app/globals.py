########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\globals.py total lines 108 
########################################################################

import threading
import time
import random
import requests
import os
import json
from collections import deque, defaultdict
import hmac

HEALTH_CHECK_INTERVAL = 10

traffic_log = deque(maxlen=100)
request_counter = 0
counter_lock = threading.Lock()
pending_auths = {}

RATE_LIMIT_ATTEMPTS = 20
RATE_LIMIT_WINDOW = 60
connection_attempts = defaultdict(list)
rate_limit_lock = threading.Lock()

class EngineManager:
    def __init__(self):
        self.engine_last_seen_cache = {}
        self.engine_last_seen_lock = threading.Lock()
        self.active_engine_sessions = {}

        self.user_selected_engine_map = {}

        self.engine_session_map = {}
        self.engine_url_map = {}
        self.engine_vitals_cache = {}
        self.job_statuses = {}
        self.job_statuses_lock = threading.Lock()
        self.gui_sessions = {}

        self.g_core_servers = []
        self.g_server_lock = threading.Lock()
        self.healthy_core_servers = []
        self.health_lock = threading.Lock()

    def perform_health_checks(self, app):
        """
        (Indonesia Hardcode) Loop pengecekan kesehatan server core secara berkala.
        """
        while True:
            with app.app_context():
                current_healthy = []
                servers_to_check = list(self.engine_url_map.values())


                for server_url in servers_to_check:
                    try:
                        resp = requests.get(f"{server_url}/health", timeout=2)
                        if resp.status_code == 200 and resp.json().get("status") == "ready":
                            current_healthy.append(server_url)
                        else:
                            app.logger.warning(
                                f"[MATA-MATA HEALTH-CHECK] Server {server_url} TIDAK SEHAT, status code: {resp.status_code}"
                            )
                    except requests.exceptions.RequestException as e:
                        pass

                with self.health_lock:
                    self.healthy_core_servers = current_healthy

            time.sleep(HEALTH_CHECK_INTERVAL)

    def get_next_core_server(self):
        with self.health_lock:
            if not self.healthy_core_servers:
                return None
            return random.choice(self.healthy_core_servers)

    def load_servers(self, app):
        APP_DIR = os.path.dirname(os.path.abspath(__file__))
        SERVER_CONFIG_FILE = os.path.join(APP_DIR, "..", "servers.json")
        with self.g_server_lock:
            if not os.path.exists(SERVER_CONFIG_FILE):
                self.g_core_servers = []
            else:
                try:
                    with open(SERVER_CONFIG_FILE, "r") as f:
                        self.g_core_servers = json.load(f)
                except:
                    self.g_core_servers = []

def perform_health_checks(app):
    globals_instance.engine_manager.perform_health_checks(app)

class Globals:
    def __init__(self):
        self.engine_manager = EngineManager()
        self._core_client = None

    def get_core_client(self):
        if not self._core_client:
            from app.net.client_core import post_core # Example
            pass
        return None # Placeholder

globals_instance = Globals()
