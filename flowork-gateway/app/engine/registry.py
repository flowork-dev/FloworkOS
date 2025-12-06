########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\engine\registry.py total lines 110 
########################################################################

"""
document : https://flowork.cloud/p-tinjauan-arsitektur-registrypy-monitor-denyut-jantung-engine-id.html
"""

import os
import sqlite3
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse

log = logging.getLogger(__name__)
DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/gateway.db")

def _conn():
    con = sqlite3.connect(DB_PATH, timeout=5.0, isolation_level=None)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA busy_timeout=5000;")
    return con

class EngineNode:
    def __init__(self, engine_id: str, weight: float, capacity: int, last_seen_ts: float, url: str = None):
        self.id = engine_id
        self.weight = weight
        self.capacity = capacity
        self.last_seen_ts = last_seen_ts
        self.url = url

    @property
    def last_heartbeat_utc(self) -> datetime:
        return datetime.fromtimestamp(self.last_seen_ts, tz=timezone.utc)

class EngineRegistry:
    def __init__(self):
        self.hb_ttl = int(os.getenv("ENGINE_HB_TTL", "60"))

    def get_active_engines(self) -> List[EngineNode]:
        now = int(time.time())
        cutoff = now - self.hb_ttl
        active_nodes = []

        default_dev_url = "http://flowork_core:8989"

        try:
            con = _conn()


            cur = con.execute("""
                SELECT id,
                       1.0 as weight,
                       100 as capacity,
                       last_seen
                FROM registered_engines
            """)

            rows = cur.fetchall()
            con.close()

            for row in rows:
                eid, w, cap, last_seen_val = row

                last_seen_ts = 0
                if last_seen_val:
                    try:
                        if isinstance(last_seen_val, str):
                            dt = datetime.fromisoformat(last_seen_val)
                            last_seen_ts = dt.timestamp()
                        elif isinstance(last_seen_val, (int, float)):
                            last_seen_ts = last_seen_val
                    except:
                        last_seen_ts = now

                active_nodes.append(EngineNode(eid, w, cap, last_seen_ts, default_dev_url))

        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                log.warning("[EngineRegistry] Table 'registered_engines' missing. Using Fallback Dev Engine.")
                active_nodes.append(EngineNode("dev-fallback", 1.0, 100, now, default_dev_url))
            else:
                log.error(f"[EngineRegistry] SQL Error: {e}")
        except Exception as e:
            log.error(f"[EngineRegistry] Failed to fetch active engines: {e}")
            active_nodes.append(EngineNode("emergency-fallback", 1.0, 100, now, default_dev_url))

        return active_nodes

engine_registry = EngineRegistry()

def list_up_engines() -> Dict[str, Dict]:
    nodes = engine_registry.get_active_engines()
    return {n.id: {"weight": n.weight, "capacity": n.capacity} for n in nodes}

def get_engine_url(engine_id: str) -> Optional[str]:
    """
    Mencari Full URL dari Engine ID.
    """
    active_nodes = engine_registry.get_active_engines()
    for node in active_nodes:
        if node.id == engine_id:
            return node.url

    return "http://flowork_core:8989"
