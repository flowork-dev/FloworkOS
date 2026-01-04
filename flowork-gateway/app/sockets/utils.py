########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\sockets\utils.py total lines 172 
########################################################################

import re
import logging
from flask import current_app
from ..extensions import db, socketio as sio
from ..models import RegisteredEngine, User, EngineShare, WorkflowShare
from ..globals import globals_instance
from ..sharing_fac import build_fac_for_shared_engine
from ..helpers import (
    get_db_session,
    find_active_engine_session
)
from sqlalchemy.orm import joinedload

def _redact_content(text: str) -> str:
    if not isinstance(text, str):
        return text

    API_KEY_PATTERN = re.compile(r'\b(sk|gsk|pk|rk)_[a-zA-Z0-9-]{30,}\b')

    try:
        redacted = API_KEY_PATTERN.sub("[REDACTED_API_KEY]", text)
        return redacted
    except Exception:
        return "[REDACTION_ERROR]"


def _safe_get_session(sid: str, namespace: str):
    try:
        return sio.server.get_session(sid, namespace=namespace)
    except Exception:
        return None

def _inject_fac_if_needed(session, user_id: str, engine_id: str, payload: dict) -> dict:
    """
    Mengecek apakah user adalah owner. Jika BUKAN, generate FAC token
    dan suntikkan ke dalam payload agar Core Engine mengizinkan eksekusi.
    """
    try:
        if not engine_id:
            return payload

        engine_id_str = str(engine_id)

        engine = session.query(RegisteredEngine).filter_by(id=engine_id_str).first()
        if not engine:
            return payload

        if str(engine.user_id) != str(user_id):
            if user_id:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    fac = build_fac_for_shared_engine(user, engine)
                    payload['__fac__'] = fac

        return payload
    except Exception as e:
        print(f"[Gateway AuthZ] Error generating FAC: {e}")
        return payload

def _broadcast_response(engine_id: str, event_name: str, data):
    """
    Mengirimkan event ke Owner DAN semua Guest yang punya akses ke Engine ini.
    Hanya digunakan untuk event umum (Status Engine, Vitals).
    """
    app = current_app._get_current_object()
    session = get_db_session()
    try:
        engine = session.query(RegisteredEngine).filter_by(id=engine_id).first()
        if engine:
            sio.emit(event_name, data, room=str(engine.user_id), namespace='/gui-socket')

        shares = session.query(EngineShare).filter_by(engine_id=engine_id).all()
        for share in shares:
            try:
                sio.emit(event_name, data, room=str(share.user_id), namespace='/gui-socket')
            except Exception as loop_err:
                app.logger.error(f"[Broadcast] Failed to emit to guest {share.user_id}: {loop_err}")

    except Exception as e:
        app.logger.error(f"[Broadcast] Error broadcasting {event_name}: {e}")
    finally:
        session.close()

def _resolve_sid_via_share_token(session, share_token):
    """
    Cari Engine ID dan Socket ID milik OWNER dari token share workflow.
    """
    app = current_app._get_current_object()
    try:
        share = session.query(WorkflowShare).options(joinedload(WorkflowShare.workflow)).filter_by(share_token=share_token).first()

        if not share or not share.workflow:
            app.logger.warning(f"[_resolve_token] Invalid share token: {share_token}")
            return None, None, None

        owner_id = share.workflow.user_id

        active_sess = find_active_engine_session(session, owner_id, None)

        if not active_sess:
            app.logger.warning(f"[_resolve_token] Owner {owner_id} has no active engine.")
            return None, None, owner_id

        eng_id_str = str(active_sess.engine_id)
        eng_sid = globals_instance.engine_manager.active_engine_sessions.get(eng_id_str)

        if eng_sid:
            return eng_id_str, eng_sid, owner_id
        else:
            return eng_id_str, None, owner_id

    except Exception as e:
        app.logger.error(f"[_resolve_token] Error: {e}")
        return None, None, None


def _emit_to_gui(user_id: str, event_name: str, data):
    app = current_app._get_current_object()
    sio.emit(event_name, data, room=str(user_id), namespace='/gui-socket')
    app.logger.info(f"[Gateway] Fwd '{event_name}' to GUI room {user_id}")


def _resolve_target_engine_sid(session, user_id, target_engine_id):
    """
    [MUTATION TOTAL BY FOWORK DEV]
    Smart Routing logic that prioritizes RAM (Socket Live) over stale DB sessions.
    This fixes the 'Not connected to Gateway' error by using direct RAM lookups.
    """
    app = current_app._get_current_object()

    if not user_id:
        return None, None

    if target_engine_id:
        eng_id_str = str(target_engine_id)
        eng_sid = globals_instance.engine_manager.active_engine_sessions.get(eng_id_str)

        if eng_sid:
            return eng_id_str, eng_sid
        else:
            """
            engine = session.query(RegisteredEngine).filter_by(id=eng_id_str).first()
            if engine and str(engine.user_id) == str(user_id):
                active_db = find_active_engine_session(session, user_id, None)
                ...
            """
            active_db = find_active_engine_session(session, user_id, eng_id_str)
            if active_db:
                eid = str(active_db.engine_id)
                sid = globals_instance.engine_manager.active_engine_sessions.get(eid)
                if sid: return eid, sid

    else:
        for eid, sid in globals_instance.engine_manager.active_engine_sessions.items():
            engine_sess = _safe_get_session(sid, namespace='/engine-socket')
            if engine_sess and str(engine_sess.get('user_id')) == str(user_id):
                app.logger.info(f"[Resolve] Auto-detected LIVE engine {eid} for user {user_id}")
                return eid, sid

        active_db = find_active_engine_session(session, user_id, None)
        if active_db:
            eng_id_str = str(active_db.engine_id)
            eng_sid = globals_instance.engine_manager.active_engine_sessions.get(eng_id_str)
            return eng_id_str, eng_sid

    return target_engine_id, None
