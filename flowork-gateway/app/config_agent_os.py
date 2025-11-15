########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\config_agent_os.py total lines 22 
########################################################################

import os

AGENT_KERNEL_WS_URL = os.getenv("AGENT_KERNEL_WS_URL", "ws://flowork-core:8765")

ALLOWED_ORIGINS = [
    os.getenv("GW_ALLOWED_ORIGINS", "http://localhost:3000"),
]

HEALTH_PRIMARY = os.getenv("GW_HEALTH_PRIMARY", "/health")
HEALTH_FALLBACK = os.getenv("GW_HEALTH_FALLBACK", "/api/v1/system/health")

JWT_SECRET = os.getenv("GW_JWT_SECRET", "please-change-me")
RATE_LIMIT = os.getenv("GW_RATE_LIMIT", "60/min")

DB_PATH = os.getenv("GW_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "gateway.sqlite3")))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
