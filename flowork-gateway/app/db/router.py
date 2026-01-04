########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\db\router.py total lines 53 
########################################################################

import os
import sqlite3
import logging
from functools import lru_cache
from typing import Optional
from flask import Flask
log = logging.getLogger(__name__)
DATA_DIR = os.getenv("SQLITE_DATA_DIR", "/app/data/engines")
os.makedirs(DATA_DIR, exist_ok=True)
PRAGMAS = [
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA busy_timeout=5000;",
    "PRAGMA temp_store=MEMORY;",
    "PRAGMA cache_size=-8000;",
]
def _apply_pragmas(con: sqlite3.Connection):

    cur = con.cursor()
    for p in PRAGMAS:
        cur.execute(p)
    con.commit()
def _db_path(engine_id: str) -> str:

    safe = "".join(ch for ch in engine_id if ch.isalnum() or ch in ("-", "_"))
    return os.path.join(DATA_DIR, f"{safe}.db")
class ShardManager:

    def __init__(self):
        self.app: Optional[Flask] = None
        log.info("[DB Router] ShardManager instance created.")
    def init_app(self, app: Flask):
        self.app = app
        log.info("[DB Router] Initialized sharded engine DB router (init_app).")
    @lru_cache(maxsize=1024)
    def get_connection(self, engine_id: str) -> sqlite3.Connection:

        path = _db_path(engine_id)
        con = sqlite3.connect(path, timeout=5.0, isolation_level=None)
        _apply_pragmas(con)
        return con
    def ensure_engine_schema(self, engine_id: str):

        con = self.get_connection(engine_id)
        con.executescript()
        log.debug(f"[DB Router] Schema ensured for engine {engine_id}")
db_router = ShardManager()
