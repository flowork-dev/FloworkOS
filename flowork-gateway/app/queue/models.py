########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\queue\models.py total lines 106 
########################################################################

import os
import sqlite3
import json
import time
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from .. import db
from ..models import Job
DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/gateway.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
def _conn():
    con = sqlite3.connect(DB_PATH, timeout=5.0, isolation_level=None)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA busy_timeout=5000;")
    return con
def init_queue_schema():
    con = _conn()
    con.executescript()
    con.close()
def enqueue_job(user_id:str, engine_id:str, payload:Dict[str,Any], priority:int=100, delay:int=0, job_id:str=None) -> str:

    jid = job_id or str(uuid.uuid4())
    now = int(time.time())
    con = _conn()
    con.execute(
        "INSERT INTO jobs(id,user_id,engine_id,payload,priority,status,retries,max_retries,created_at,available_at,version)"
        "VALUES(?,?,?,?,?,'queued',0,3,?,?,0)",
        (jid, user_id, engine_id, json.dumps(payload), priority, now, now + delay)
    )
    con.close()
    return jid
def claim_next_job(engine_id:str, worker_id:str) -> Optional[Dict[str,Any]]:

    con = _conn()
    cur = con.cursor()
    now = int(time.time())
    row = cur.execute(, (engine_id, now)).fetchone()
    if not row:
        con.close()
        return None
    jid, payload, prio, ver = row
    upd = cur.execute(, (now, worker_id, jid, ver))
    con.commit()
    if upd.rowcount != 1:
        con.close()
        return None
    con.close()
    return {"id": jid, "payload": json.loads(payload), "priority": prio}
def finish_job(jid:str, ok:bool, retry_delay:int=0):
    con = _conn()
    cur = con.cursor()
    now = int(time.time())
    if ok:
        cur.execute("UPDATE jobs SET status='done', version=version+1 WHERE id=?", (jid,))
    else:
        cur.execute("SELECT retries, max_retries FROM jobs WHERE id=?", (jid,))
        row = cur.fetchone()
        if not row:
            con.close(); return
        retries, max_retries = row
        if retries + 1 >= max_retries:
            cur.execute("UPDATE jobs SET status='error', version=version+1 WHERE id=?", (jid,))
        else:
            cur.execute(, (now + retry_delay, jid))
    con.commit()
    con.close()
def queue_depth(engine_id:str) -> int:
    con = _conn()
    row = con.execute("SELECT COUNT(*) FROM jobs WHERE engine_id=? AND status='queued'", (engine_id,)).fetchone()
    con.close()
    return row[0] if row else 0
def get_job(jid: str) -> Optional[Job]:

    try:
        return db.session.get(Job, jid)
    except Exception as e:
        print(f"Error in get_job: {e}")
        return None
class JobDispatcher:

    def enqueue_job(self, job_id:str, user_id:str, engine_id:str, workflow_id:str, payload:Dict[str,Any]) -> Optional[Job]:

        try:
            combined_payload = payload or {}
            combined_payload["_workflow_id"] = workflow_id
            jid = enqueue_job(
                user_id=user_id,
                engine_id=engine_id,
                payload=combined_payload,
                job_id=job_id
            )
            return Job(id=jid, created_at=datetime.utcnow())
        except Exception as e:
            print(f"Error in JobDispatcher.enqueue_job: {e}")
            return None
    def get_job(self, job_id: str) -> Optional[Job]:

        return get_job(job_id)
