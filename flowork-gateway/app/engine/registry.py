########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\engine\registry.py total lines 139 
########################################################################

import os
import sqlite3
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from app.globals import globals_instance

log = logging.getLogger(__name__)
DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/gateway.db")

def _conn():
    """
    Membuka koneksi SQLite dan MEMASTIKAN tabel registered_engines ada.
    """
    con = sqlite3.connect(DB_PATH, timeout=5.0, isolation_level=None)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA busy_timeout=5000;")

    con.execute("""
        CREATE TABLE IF NOT EXISTS registered_engines (
            id TEXT PRIMARY KEY,
            owner_id TEXT,
            status TEXT,
            last_seen TEXT
        )
    """)
    return con

class EngineNode:
    def __init__(self, engine_id: str, weight: float, capacity: int, last_seen_ts: float, url: str = None):
        self.id = engine_id
        self.weight = weight
        self.capacity = capacity
        self.last_seen_ts = last_seen_ts
        self.url = url

class EngineRegistry:
    def __init__(self):
        self.hb_ttl = int(os.getenv("ENGINE_HB_TTL", "60"))

    @staticmethod
    def register_engine(engine_id: str, user_id: str, sid: str):
        try:
            em = getattr(globals_instance, 'engine_manager', None)
            if em:
                em.active_engine_sessions[engine_id] = sid
                if not hasattr(em, 'sid_to_engine_map'): em.sid_to_engine_map = {}
                em.sid_to_engine_map[sid] = {"engine_id": engine_id, "user_id": user_id}

            con = _conn()
            now = datetime.now(timezone.utc).isoformat()
            con.execute("""
                INSERT INTO registered_engines (id, owner_id, status, last_seen)
                VALUES (?, ?, 'online', ?)
                ON CONFLICT(id) DO UPDATE SET status='online', last_seen=excluded.last_seen
            """, (engine_id, user_id, now))
            con.close()
            log.info(f"✅ Engine {engine_id} registered (SID: {sid})")
            return True
        except Exception as e:
            log.error(f"❌ Registry Error: {e}")
            return False

    @staticmethod
    def unregister_engine(engine_id: str):
        em = getattr(globals_instance, 'engine_manager', None)
        if em:
            sid = em.active_engine_sessions.pop(engine_id, None)
            if sid and hasattr(em, 'sid_to_engine_map'): em.sid_to_engine_map.pop(sid, None)
        try:
            con = _conn()
            con.execute("UPDATE registered_engines SET status='offline' WHERE id=?", (engine_id,))
            con.close()
        except: pass

    @staticmethod
    def get_engine_by_sid(sid: str):
        em = getattr(globals_instance, 'engine_manager', None)
        return em.sid_to_engine_map.get(sid) if em and hasattr(em, 'sid_to_engine_map') else None

    @staticmethod
    def update_engine_status(engine_id: str, data: dict = None):
        try:
            con = _conn()
            con.execute("UPDATE registered_engines SET last_seen=?, status='online' WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), engine_id))
            con.close()
        except: pass

    def get_active_engines(self) -> List[EngineNode]:
        now = int(time.time())
        cutoff = now - self.hb_ttl
        active_nodes = []
        live_sessions = getattr(globals_instance.engine_manager, 'active_engine_sessions', {})
        live_urls = getattr(globals_instance.engine_manager, 'engine_url_map', {})

        try:
            con = _conn()
            cur = con.execute("SELECT id, 1.0, 100, last_seen FROM registered_engines")
            rows = cur.fetchall()
            con.close()

            for row in rows:
                eid, w, cap, last_seen = row
                is_live = eid in live_sessions
                ts = 0
                if last_seen:
                    try: ts = datetime.fromisoformat(last_seen).timestamp()
                    except: ts = now if is_live else 0

                if is_live or ts > cutoff:
                    url = live_urls.get(eid, "http://flowork_core:8989")
                    active_nodes.append(EngineNode(eid, w, cap, ts, url))
        except Exception as e:
            log.error(f"Get engines error: {e}")

        return active_nodes

engine_registry = EngineRegistry()

def list_up_engines() -> Dict[str, Dict]:
    nodes = engine_registry.get_active_engines()
    return {n.id: {"weight": n.weight, "capacity": n.capacity} for n in nodes}

def get_engine_url(engine_id: str) -> Optional[str]:
    live_urls = getattr(globals_instance.engine_manager, 'engine_url_map', {})
    if engine_id in live_urls: return live_urls[engine_id]
    active_nodes = engine_registry.get_active_engines()
    for node in active_nodes:
        if node.id == engine_id: return node.url
    return "http://flowork_core:8989"
