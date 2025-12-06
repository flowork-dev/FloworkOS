########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\sockets.py total lines 2009 
########################################################################

"""
document : https://flowork.cloud/p-analisis-mendalam-socketspy-pusat-saraf-gateway-arsitektur-flowork-id.html
"""
from flask import request, current_app
from sqlalchemy.orm import joinedload
from datetime import datetime
import logging
import json
import re
import uuid
from werkzeug.security import generate_password_hash
import secrets

from flask_socketio import join_room, leave_room
from werkzeug.security import check_password_hash

from .extensions import db, socketio as sio
from .models import User, RegisteredEngine, UserEngineSession, EngineShare, AgentSession, Episode, WorkflowShare, Workflow
from .globals import globals_instance
from .helpers import (
    get_db_session,
    find_active_engine_session,
    verify_web3_signature
)
from .sharing_fac import build_fac_for_shared_engine

g_swarm_task_registry = {}
g_job_ownership = {}       # Maps Job ID -> User ID
g_execution_ownership = {} # Maps Execution ID -> User ID
g_engine_active_job = {}   # Maps Engine ID -> Current Job ID (For events missing job_id like Popups)

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


@sio.on('connect', namespace='/engine-socket')
def on_engine_connect(auth):
    app = current_app._get_current_object()
    sid = request.sid
    remote_addr = request.environ.get('REMOTE_ADDR', 'N/A')

    if not auth or 'engine_id' not in auth or 'token' not in auth:
        app.logger.warning(f"[Gateway Engine Connect] Engine connection from {remote_addr} missing auth data. Disconnecting.")
        return False

    engine_id = auth.get('engine_id')
    token = auth.get('token')

    session = get_db_session()
    try:
        engine = session.query(RegisteredEngine).filter_by(id=engine_id).first()
        if not engine or not check_password_hash(engine.engine_token_hash, token):
            app.logger.warning(f"[Gateway Engine Connect] Engine auth failed for engine_id: {engine_id} from {remote_addr}. Disconnecting.")
            sio.emit('auth_failed', {'error': 'Invalid engine_id or token'}, room=sid, namespace='/engine-socket')
            return False

        sio.server.save_session(sid, {'engine_id': engine_id, 'user_id': engine.user_id}, namespace='/engine-socket')
        join_room(engine.user_id, sid, namespace='/engine-socket')
        join_room(engine_id, sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway Engine Connect] Engine {engine_id} (SID: {sid}) joined room '{engine_id}' for commands.")

        globals_instance.engine_manager.active_engine_sessions[engine_id] = sid
        app.logger.info(f"[Gateway Engine Connect] Pre-registered live SID for Engine {engine_id} -> {sid}")

        sio.emit('auth_success', {'user_id': engine.user_id}, room=sid, namespace='/engine-socket')
        return True

    except Exception as e:
        app.logger.error(f"[Gateway Engine Connect] Error during engine connect: {e}", exc_info=True)
        return False
    finally:
        session.close()


@sio.on('disconnect', namespace='/engine-socket')
def on_engine_disconnect():
    app = current_app._get_current_object()
    sid = request.sid
    session_data = _safe_get_session(sid, namespace='/engine-socket')

    if session_data is None:
        app.logger.warning(f"[Gateway Engine Disconnect] A disconnected engine SID {sid} had no session data.")
        return

    engine_id = session_data.get('engine_id')
    user_id = session_data.get('user_id')

    if not engine_id:
        app.logger.warning(f"[Gateway Engine Disconnect] SID {sid} missing engine_id.")
        return

    app.logger.info(f"[Gateway Engine Disconnect] Engine {engine_id} (User: {user_id}) disconnected. SID: {sid}")

    removed_sid = globals_instance.engine_manager.active_engine_sessions.pop(engine_id, None)
    if removed_sid:
        app.logger.info(f"[Gateway Engine Disconnect] Removed live SID {removed_sid} for Engine {engine_id} from active session map.")
    else:
        app.logger.warning(f"[Gateway Engine Disconnect] Engine {engine_id} disconnected, but it was not in the active session map.")

    session = get_db_session()
    try:
        existing_session = session.query(UserEngineSession).filter_by(engine_id=engine_id, is_active=True).first()
        if existing_session:
            existing_session.is_active = False
            session.commit()
            globals_instance.engine_manager.engine_url_map.pop(engine_id, None)

            _broadcast_response(engine_id, 'engine_status_update', {
                'engine_id': engine_id,
                'status': 'offline',
                'vitals': None
            })

        active_agent_sessions = session.query(AgentSession).filter_by(
            engine_id=engine_id,
            status='running'
        ).all()

        if active_agent_sessions:
            app.logger.warning(f"[Gateway Engine Disconnect] Engine {engine_id} died with {len(active_agent_sessions)} active agent sessions. Marking as errored.")
            for agent_sess in active_agent_sessions:
                agent_sess.status = 'error'
                agent_sess.finished_at = datetime.utcnow()

                error_payload = {
                    'session_id': agent_sess.id,
                    'code': 'ENGINE_DISCONNECT',
                    'message': 'The engine executing this session disconnected unexpectedly.'
                }
                sio.emit('agent:error', error_payload, room=agent_sess.id, namespace='/gui-socket')

            session.commit()

    except Exception as e:
        app.logger.error(f"[Gateway Engine Disconnect] Error updating engine session for {engine_id}: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()


@sio.on('engine_ready', namespace='/engine-socket')
def handle_engine_ready(data):
    app = current_app._get_current_object()
    sid = request.sid
    session_data = _safe_get_session(sid, namespace='/engine-socket')

    if session_data is None:
        app.logger.warning(f"[Gateway Engine Ready] 'engine_ready' from SID {sid} with no session data. Ignoring.")
        return

    engine_id = session_data.get('engine_id')
    user_id = session_data.get('user_id')

    internal_api_url = None
    if isinstance(data, dict) and data.get('v') == 2:
        internal_api_url = (data.get('payload') or {}).get('internal_api_url')
    elif isinstance(data, dict):
        internal_api_url = data.get('internal_api_url')

    if not internal_api_url:
        app.logger.warning(f"[Gateway Engine Ready] Engine {engine_id} sent without internal_api_url.")

    app.logger.info(f"[Gateway Engine Ready] Engine {engine_id} READY. Internal URL: {internal_api_url}")

    globals_instance.engine_manager.active_engine_sessions[engine_id] = sid
    if internal_api_url:
        globals_instance.engine_manager.engine_url_map[engine_id] = internal_api_url

    session = get_db_session()
    try:
        for stale in session.query(UserEngineSession).filter_by(engine_id=engine_id, is_active=True).all():
            stale.is_active = False

        new_session = UserEngineSession(
            user_id=user_id,
            engine_id=engine_id,
            internal_url=internal_api_url,
            is_active=True,
            last_activated_at=int(datetime.utcnow().timestamp())
        )
        session.add(new_session)
        session.commit()

        _broadcast_response(engine_id, 'engine_status_update', {
            'engine_id': engine_id,
            'status': 'online',
            'vitals': None
        })

    except Exception as e:
        app.logger.error(f"[Gateway Engine Ready] Failed to update session for engine {engine_id}: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()


@sio.on('engine_vitals_update', namespace='/engine-socket')
def handle_engine_vitals_update(data=None):
    app = current_app._get_current_object()
    sid = request.sid
    sess = _safe_get_session(sid, namespace='/engine-socket')

    payload = {}
    if isinstance(data, dict) and data.get('v') == 2:
        payload = data.get('payload') or {}
    elif isinstance(data, dict):
        payload = data
    else:
        payload = {}

    engine_id = (sess or {}).get('engine_id') or payload.get('engine_id')
    user_id = (sess or {}).get('user_id') or payload.get('user_id')
    internal_url = payload.get('internal_api_url') or payload.get('internal_url')

    if not engine_id or not user_id:
        app.logger.warning(f"[Gateway Vitals] Missing engine_id/user_id (sid={sid}). Dropping vitals.")
        return

    globals_instance.engine_manager.active_engine_sessions[str(engine_id)] = sid

    current_sid = globals_instance.engine_manager.active_engine_sessions.get(engine_id)
    did_backfill = False

    if current_sid != sid:
        globals_instance.engine_manager.active_engine_sessions[engine_id] = sid
        did_backfill = True
        app.logger.info(f"[Gateway Vitals] Backfilled live SID map for Engine {engine_id} -> {sid}")

    if internal_url:
        globals_instance.engine_manager.engine_url_map[engine_id] = internal_url

    session = get_db_session()
    try:
        active_db = find_active_engine_session(session, user_id, engine_id)
        if not active_db:
            for stale in session.query(UserEngineSession).filter_by(engine_id=engine_id, is_active=True).all():
                stale.is_active = False

            new_sess = UserEngineSession(
                user_id=user_id,
                engine_id=engine_id,
                internal_url=internal_url or globals_instance.engine_manager.engine_url_map.get(engine_id),
                is_active=True,
                last_activated_at=int(datetime.utcnow().timestamp())
            )
            session.add(new_sess)
            session.commit()
            did_backfill = True
            app.logger.info(f"[Gateway Vitals] Backfilled ACTIVE DB session for engine {engine_id}")
    except Exception as e:
        app.logger.error(f"[Gateway Vitals] Backfill DB session failed for engine {engine_id}: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()

    if did_backfill:
        _broadcast_response(engine_id, 'engine_status_update', {
            'engine_id': engine_id,
            'status': 'online',
            'vitals': None
        })

    _broadcast_response(engine_id, 'engine_vitals_update', {
        'engine_id': engine_id,
        'vitals': payload
    })


def _emit_to_gui(user_id: str, event_name: str, data):
    app = current_app._get_current_object()
    sio.emit(event_name, data, room=str(user_id), namespace='/gui-socket')
    app.logger.info(f"[Gateway] Fwd '{event_name}' to GUI room {user_id}")

@sio.on('response_component_list', namespace='/engine-socket')
def on_engine_response_component_list(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'response_component_list', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_component_list', data)

@sio.on('response_variables', namespace='/engine-socket')
def on_engine_response_variables(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'response_variables', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_variables', data)

@sio.on('response_presets_list', namespace='/engine-socket')
def on_engine_response_presets_list(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'response_presets_list', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_presets_list', data)

@sio.on('response_ai_status', namespace='/engine-socket')
def on_engine_response_ai_status(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'response_ai_status', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_ai_status', data)

@sio.on('response_datasets_list', namespace='/engine-socket')
def on_engine_response_datasets_list(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'response_datasets_list', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_datasets_list', data)

@sio.on('response_local_models', namespace='/engine-socket')
def on_engine_response_local_models(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'response_local_models', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_local_models', data)

@sio.on('response_training_job_status', namespace='/engine-socket')
def on_engine_response_training_job_status(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'response_training_job_status', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_training_job_status', data)

@sio.on('component_install_status', namespace='/engine-socket')
def on_engine_component_install_status(data):
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    if engine_id:
        _broadcast_response(engine_id, 'component_install_status', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'component_install_status', data)

@sio.on('response_settings', namespace='/engine-socket')
@sio.on('settings_state', namespace='/engine-socket') # Aliasing for compatibility
def on_engine_response_settings(data):
    """
    Handles settings response from Engine and forwards to GUI.
    Crucial for the Settings Page to stop loading.
    """
    app = current_app._get_current_object()
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    engine_id = sess.get('engine_id')
    user_id = sess.get('user_id')


    if engine_id:
        _broadcast_response(engine_id, 'settings_state', data)
    else:
        _emit_to_gui(user_id, 'settings_state', data)

@sio.on('FILESYSTEM_LIST_RESPONSE', namespace='/engine-socket')
def on_engine_filesystem_response(data):
    """
    Forwards filesystem list results from Engine to GUI.
    """
    app = current_app._get_current_object()
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    user_id = sess.get('user_id')
    _emit_to_gui(user_id, 'FILESYSTEM_LIST_RESPONSE', data)

@sio.on('forward_event_to_gui', namespace='/engine-socket')
def on_forward_event_to_gui(data):
    """
    Central Handler for forwarding events from Engine -> GUI.
    Includes strict UNICAST logic to prevent crosstalk (Leakage).
    INJECTS 'engine_id' if missing so Frontend knows which engine status to update.
    """
    app = current_app._get_current_object()

    try:
        sess = _safe_get_session(request.sid, namespace='/engine-socket')
        if sess and sess.get('engine_id'):
            eid = sess.get('engine_id')
            if globals_instance.engine_manager.active_engine_sessions.get(eid) != request.sid:
                 globals_instance.engine_manager.active_engine_sessions[eid] = request.sid
    except Exception:
        pass

    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.warning(f"[Gateway] Received non-v2 'forward_event_to_gui'. Ignoring.")
        return

    payload = data.get('payload', {})
    event_name = payload.get("event_name")
    event_data = payload.get("event_data") or {}
    user_id = payload.get("user_id") # Engine Session Owner ID

    if not event_name:
        app.logger.warning(f"[Gateway] Invalid 'forward_event_to_gui' payload: {data}")
        return

    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    current_engine_id = sess.get('engine_id') if sess else None

    if not current_engine_id and 'engine_id' in event_data:
         current_engine_id = event_data['engine_id']

    if current_engine_id and isinstance(event_data, dict) and 'engine_id' not in event_data:
        event_data['engine_id'] = current_engine_id


    target_user_id = event_data.get('_target_user_id')
    if not target_user_id:
        target_user_id = (event_data.get('payload') or {}).get('_target_user_id')

    job_id = event_data.get('job_id')
    execution_id = event_data.get('execution_id')

    if event_name == 'WORKFLOW_EXECUTION_UPDATE':
        status = event_data.get('status') or (event_data.get('status_data') or {}).get('status')
        if status == 'RUNNING' and current_engine_id and job_id:
            g_engine_active_job[current_engine_id] = job_id
            if execution_id and g_execution_ownership.get(execution_id):
                g_job_ownership[job_id] = g_execution_ownership[execution_id]

    if not job_id and current_engine_id:
        inferred_job_id = g_engine_active_job.get(current_engine_id)
        if inferred_job_id:
            job_id = inferred_job_id

    if not target_user_id and execution_id and g_execution_ownership.get(execution_id):
         target_user_id = g_execution_ownership[execution_id]

    if not target_user_id and job_id and g_job_ownership.get(job_id):
        target_user_id = g_job_ownership[job_id]

    if not target_user_id and job_id and g_execution_ownership.get(job_id):
         target_user_id = g_execution_ownership[job_id]

    BROADCAST_EVENTS = {
        'JOB_COMPLETED_CHECK',
        'WORKFLOW_EXECUTION_UPDATE',
        'EXECUTION_STARTED',
        'EXECUTION_PROGRESS',
        'node_status_update',
        'engine_status_update',
        'settings_state' # [FLOWORK FIX] Allow settings state to broadcast via forward event if needed
    }

    STRICT_UNICAST_EVENTS = {
        'SHOW_DEBUG_POPUP',
        'WORKFLOW_LOG_ENTRY',
        'gui:input',
        'FILESYSTEM_LIST_RESPONSE' # Added strict unicast for files
    }

    if event_name in BROADCAST_EVENTS:
        if current_engine_id:
            _broadcast_response(current_engine_id, event_name, event_data)
        elif user_id:
            sio.emit(event_name, event_data, room=str(user_id), namespace='/gui-socket')

        if target_user_id and str(target_user_id) != str(user_id):
             sio.emit(event_name, event_data, room=str(target_user_id), namespace='/gui-socket')

    elif event_name in STRICT_UNICAST_EVENTS:
        if target_user_id:
             sio.emit(event_name, event_data, room=str(target_user_id), namespace='/gui-socket')
        else:
             app.logger.warning(f"[Gateway] Blocked leakage of private event '{event_name}'. No valid target_user_id found via Job/Execution/SmartEngine registry. (Job: {job_id})")

    else:
        if target_user_id:
             sio.emit(event_name, event_data, room=str(target_user_id), namespace='/gui-socket')


@sio.on('connect', namespace='/gui-socket')
def on_gui_connect(auth):
    app = current_app._get_current_object()
    sid = request.sid
    remote_addr = request.environ.get('REMOTE_ADDR', 'N/A')

    if not auth:
        app.logger.info(f"[Gateway GUI Connect] Anonymous GUI client connected from {remote_addr}. SID: {sid}.")
        sio.server.save_session(sid, {'user_id': None, 'user_address': None}, namespace='/gui-socket')
        return True

    auth_dict = auth
    if isinstance(auth, str):
        try:
            auth_dict = json.loads(auth)
            app.logger.info(f"[Gateway GUI Connect] Parsed string-based auth from {remote_addr}.")
        except json.JSONDecodeError:
            app.logger.error(f"[Gateway GUI Connect] Failed to parse string-based auth from {remote_addr}.")
            return False
    elif not isinstance(auth, dict):
        app.logger.error(f"[Gateway GUI Connect] Auth object is not dict or string. Denied.")
        return False

    headers = auth_dict.get('headers') if auth_dict else None
    if not headers:
        app.logger.warning(f"[Gateway GUI] Missing signature headers from {remote_addr}. Denied.")
        return False

    address = headers.get('X-User-Address')
    message = headers.get('X-Signed-Message')
    signature = headers.get('X-Signature')
    payload_v = headers.get('X-Payload-Version')

    if not address or not message or not signature or not payload_v:
        app.logger.warning(f"[Gateway GUI] Incomplete auth headers from {remote_addr}. Denied.")
        return False

    try:
        ts_str = message.split('|')[-1]
        if not ts_str.isdigit():
            raise ValueError("Invalid message format")
        ts = int(ts_str)
        if abs(datetime.utcnow().timestamp() - ts) > 300:
            app.logger.warning(f"[Gateway GUI] Auth expired for {address} from {remote_addr}. Denied.")
            return False
        if not verify_web3_signature(address, message, signature):
            app.logger.warning(f"[Gateway GUI] Invalid signature for {address} from {remote_addr}. Denied.")
            return False
    except Exception as e:
        app.logger.error(f"[Gateway GUI] Error during signature validation: {e}", exc_info=True)
        return False

    session = get_db_session()
    try:
        user = session.query(User).filter(User.public_address.ilike(address)).first()

        if not user:
            app.logger.info(f"[Gateway GUI] First-time login for {address}. Auto-provisioning new user record.")

            new_user_id = str(uuid.uuid4())
            dummy_email = f"{address.lower()}@flowork.cloud"
            dummy_password = secrets.token_urlsafe(32)

            user = User(
                id=new_user_id,
                username=f"user_{address[:8]}",
                email=dummy_email,
                password_hash=generate_password_hash(dummy_password),
                public_address=address,
                status='active'
            )
            session.add(user)

            try:
                session.commit()
                app.logger.info(f"[Gateway GUI] Successfully created new user {new_user_id} for {address}.")
            except Exception as e_commit:
                app.logger.error(f"[Gateway GUI] FAILED to commit new user for {address}: {e_commit}", exc_info=True)
                session.rollback()
                return False


        sio.server.save_session(sid, {'user_id': user.id, 'user_address': user.public_address, 'user_signature': signature}, namespace='/gui-socket')
        join_room(str(user.id), sid, namespace='/gui-socket')
        app.logger.info(f"[Gateway GUI] Auth success for {address} (User ID: {user.id}). SID {sid} joined room '{user.id}'.")

        owned = session.query(RegisteredEngine).filter_by(user_id=user.id).all()
        shared = session.query(EngineShare).filter_by(user_id=user.id).options(joinedload(EngineShare.engine)).all()

        all_engines = list(owned)
        if shared:
            for s in shared:
                if s.engine:
                    all_engines.append(s.engine)

        statuses = []
        for eng in all_engines:
            if not eng: continue

            live_sid = globals_instance.engine_manager.active_engine_sessions.get(str(eng.id))
            status = 'offline'
            if live_sid:
                status = 'online'

            statuses.append({
                'engine_id': eng.id,
                'status': status,
                'vitals': None
            })

        sio.emit('initial_engine_statuses', statuses, room=sid, namespace='/gui-socket')
        return True

    except Exception as e:
        app.logger.error(f"[Gateway GUI] DB error during auth/setup: {e}", exc_info=True)
        session.rollback()
        return False
    finally:
        session.close()


@sio.on('disconnect', namespace='/gui-socket')
def on_gui_disconnect():
    app = current_app._get_current_object()
    sid = request.sid
    sess = _safe_get_session(sid, namespace='/gui-socket')
    if sess is None:
        app.logger.warning(f"[Gateway GUI Disconnect] GUI SID {sid} disconnected with no session.")
        return
    user_id = sess.get('user_id')
    app.logger.info(f"[Gateway GUI Disconnect] GUI for User {user_id} disconnected. SID: {sid}")
    try:
        if user_id:
            leave_room(str(user_id), sid, namespace='/gui-socket')
        gui_session_id = sess.get('gui_session_id')
        if gui_session_id:
            leave_room(gui_session_id, sid, namespace='/gui-socket')
            app.logger.info(f"[Gateway GUI Disconnect] SID {sid} left agent session room '{gui_session_id}'.")
    except Exception:
        pass


def _resolve_target_engine_sid(session, user_id, target_engine_id):
    """
    Resolves the socket ID for the target engine.
    Includes AUTO-SWITCHING logic for owners if target ID is dead.
    """
    app = current_app._get_current_object()

    if not user_id:
        return None, None

    if target_engine_id:
        eng_id_str = str(target_engine_id)
        eng_sid = globals_instance.engine_manager.active_engine_sessions.get(eng_id_str)

        if eng_sid:
            engine = session.query(RegisteredEngine).filter_by(id=eng_id_str).first()
            if engine and str(engine.user_id) == str(user_id):
                return eng_id_str, eng_sid

            share = session.query(EngineShare).filter_by(engine_id=eng_id_str, user_id=user_id).first()
            if share:
                return eng_id_str, eng_sid

            return eng_id_str, None
        else:
            engine = session.query(RegisteredEngine).filter_by(id=eng_id_str).first()
            if engine and str(engine.user_id) == str(user_id):
                active_db = find_active_engine_session(session, user_id, None)
                if active_db:
                    new_id = str(active_db.engine_id)
                    new_sid = globals_instance.engine_manager.active_engine_sessions.get(new_id)
                    if new_sid:
                        app.logger.info(f"[Resolve] Auto-switching Owner {user_id} from dead {eng_id_str} to live {new_id}")
                        return new_id, new_sid

            return eng_id_str, None
    else:
        active_db = find_active_engine_session(session, user_id, None)

        if active_db:
            eng_id_str = str(active_db.engine_id)
            eng_sid = globals_instance.engine_manager.active_engine_sessions.get(eng_id_str)
            return eng_id_str, eng_sid

        try:
            shared_shares = session.query(EngineShare).filter_by(user_id=user_id).all()
            for share in shared_shares:
                s_eng_id = str(share.engine_id)
                s_sid = globals_instance.engine_manager.active_engine_sessions.get(s_eng_id)
                if s_sid:
                    app.logger.info(f"[_resolve] User {user_id} has no active session, but found ONLINE shared engine {s_eng_id}. Using it.")
                    return s_eng_id, s_sid
        except Exception as e:
            app.logger.error(f"[_resolve] Error checking shared engines: {e}")

        return None, None


@sio.on('request_presets_list', namespace='/gui-socket')
def on_request_presets_list(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'request_presets_list' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    user_addr = gui_sess.get('user_address')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'request_presets_list' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            err_msg = f'Engine {target_engine_id or "active"} is not connected to the Gateway.'
            if not user_id:
                err_msg = 'Cannot fetch components. Please log in to connect to an engine.'
            sio.emit('response_presets_list', {'error': err_msg}, room=sid, namespace='/gui-socket')
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)

        sio.emit('request_presets_list', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'request_presets_list': {e}", exc_info=True)
    finally:
        session.close()


@sio.on('request_variables', namespace='/gui-socket')
def on_request_variables(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'request_variables' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    user_addr = gui_sess.get('user_address')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'request_variables' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            err_msg = f'Engine {target_engine_id or "active"} is not connected to the Gateway.'
            if not user_id:
                err_msg = 'Cannot fetch variables. Please log in to connect to an engine.'
            sio.emit('response_variables', {'error': err_msg}, room=sid, namespace='/gui-socket')
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)

        sio.emit('request_variables', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'request_variables': {e}", exc_info=True)
    finally:
        session.close()


@sio.on('request_components_list', namespace='/gui-socket')
def on_request_components_list(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'request_components_list' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    user_addr = gui_sess.get('user_address')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'request_components_list' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    comp_type = payload.get('component_type', 'unknown')
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)

        if not eng_id or not eng_sid:
            err_msg = f'Engine {target_engine_id or "active"} is not connected to the Gateway.'
            if not user_id:
                err_msg = 'Cannot fetch components. Please log in to connect to an engine.'
            sio.emit('response_component_list', {
                'error': err_msg,
                'component_type': comp_type,
                'components': []
            }, room=sid, namespace='/gui-socket')
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}

        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)

        sio.emit('request_components_list', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'request_components_list': {e}", exc_info=True)
    finally:
        session.close()

@sio.on('filesystem_list_request', namespace='/gui-socket')
def on_filesystem_list_request(data):
    """
    Forwards filesystem list requests from GUI to Engine.
    """
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'filesystem_list_request' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')

    payload = data if isinstance(data, dict) else {}
    if payload.get('type') == 'filesystem_list_request' and 'path' in payload:
        payload = {
            'path': payload.get('path'),
            'target_engine_id': payload.get('target_engine_id')
        }
    elif payload.get('v') == 2:
        payload = payload.get('payload', {})

    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            err_msg = f'Engine {target_engine_id or "active"} is not connected.'
            sio.emit('FILESYSTEM_LIST_RESPONSE', {'error': err_msg}, room=sid, namespace='/gui-socket')
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)

        sio.emit('filesystem_list_request', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'filesystem_list_request' to Engine {eng_id}")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding filesystem request: {e}", exc_info=True)
    finally:
        session.close()

@sio.on('request_settings', namespace='/gui-socket')
def on_request_settings(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            sio.emit('settings_state', {'error': 'Engine not connected'}, room=sid, namespace='/gui-socket')
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_settings', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('save_settings', namespace='/gui-socket')
def on_save_settings(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
             sio.emit('notification', {'text': 'Save failed: Engine offline', 'color': 'error'}, room=sid, namespace='/gui-socket')
             return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('save_settings', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('update_variable', namespace='/gui-socket')
def on_update_variable(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid: return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('update_variable', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('delete_variable', namespace='/gui-socket')
def on_delete_variable(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid: return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('delete_variable', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('request_prompts_list', namespace='/gui-socket')
def on_request_prompts_list(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            sio.emit('response_prompts_list', {'error': 'Engine not connected'}, room=sid, namespace='/gui-socket')
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_prompts_list', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('update_prompt', namespace='/gui-socket')
def on_update_prompt(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid: return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('update_prompt', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('delete_prompt', namespace='/gui-socket')
def on_delete_prompt(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid: return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('delete_prompt', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('request_ai_status', namespace='/gui-socket')
def on_request_ai_status(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            sio.emit('response_ai_status', {'error': 'Engine not connected'}, room=sid, namespace='/gui-socket')
            return
        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_ai_status', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('request_datasets_list', namespace='/gui-socket')
def on_request_datasets_list(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            sio.emit('response_datasets_list', {'error': 'Engine not connected'}, room=sid, namespace='/gui-socket')
            return
        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_datasets_list', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('request_local_models', namespace='/gui-socket')
def on_request_local_models(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            sio.emit('response_local_models', {'error': 'Engine not connected'}, room=sid, namespace='/gui-socket')
            return
        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_local_models', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('request_training_job_status', namespace='/gui-socket')
def on_request_training_job_status(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            sio.emit('response_training_job_status', {'error': 'Engine not connected'}, room=sid, namespace='/gui-socket')
            return
        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_training_job_status', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('execute_workflow', namespace='/gui-socket')
def on_execute_workflow(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'execute_workflow' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'execute_workflow' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    job_id = payload.get('job_id') # Get Job ID provided by Frontend

    if job_id:
        g_job_ownership[job_id] = user_id
        g_execution_ownership[job_id] = user_id

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'execute_workflow'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}

        payload['_target_user_id'] = user_id

        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)

        sio.emit('execute_workflow', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'execute_workflow' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'execute_workflow': {e}", exc_info=True)
    finally:
        session.close()


@sio.on('execute_standalone_node', namespace='/gui-socket')
def on_execute_standalone_node(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'execute_standalone_node' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'execute_standalone_node' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    share_token = payload.get('share_token')
    job_id = payload.get('job_id')

    if job_id:
        g_job_ownership[job_id] = user_id
        g_execution_ownership[job_id] = user_id

    session = get_db_session()
    try:
        if share_token:
            eng_id, eng_sid, owner_id = _resolve_sid_via_share_token(session, share_token)
            if eng_id and eng_sid:
                payload['user_context'] = {'id': owner_id, 'tier': 'architect'}

                payload['_target_user_id'] = user_id

                payload = _inject_fac_if_needed(session, user_id, eng_id, payload)

                sio.emit('execute_standalone_node', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
                app.logger.info(f"[Gateway] Fwd 'execute_standalone_node' (Shared Token) -> EngineSID {eng_sid}")
                return

        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'execute_standalone_node'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}

        payload['_target_user_id'] = user_id

        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)

        sio.emit('execute_standalone_node', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'execute_standalone_node' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'execute_standalone_node': {e}", exc_info=True)
    finally:
        session.close()


@sio.on('stop_workflow', namespace='/gui-socket')
def on_stop_workflow(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'stop_workflow' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'stop_workflow' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'stop_workflow'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('stop_workflow', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'stop_workflow' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'stop_workflow': {e}", exc_info=True)
    finally:
        session.close()

@sio.on('pause_workflow', namespace='/gui-socket')
def on_pause_workflow(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'pause_workflow' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'pause_workflow' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'pause_workflow'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('pause_workflow', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'pause_workflow' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'pause_workflow': {e}", exc_info=True)
    finally:
        session.close()


@sio.on('save_preset', namespace='/gui-socket')
def on_save_preset(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'save_preset' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    user_addr = gui_sess.get('user_address')
    signature = gui_sess.get('user_signature')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'save_preset' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'save_preset'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload['user_context']['public_address'] = user_addr
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('save_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'save_preset' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'save_preset': {e}", exc_info=True)
    finally:
        session.close()

@sio.on('delete_preset', namespace='/gui-socket')
def on_delete_preset(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'delete_preset' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'delete_preset' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    payload['user_context'] = {'id': user_id, 'tier': 'architect'}

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'delete_preset'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            sio.emit('response_presets_list', {'error': f'Engine {target_engine_id or "active"} is not connected.'}, room=sid, namespace='/gui-socket')
            return

        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('delete_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'delete_preset' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'delete_preset': {e}", exc_info=True)
    finally:
        session.close()

@sio.on('load_preset', namespace='/gui-socket')
def on_load_preset(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'load_preset' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'load_preset' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    share_token = payload.get('share_token')

    session = get_db_session()
    try:
        if share_token:
            eng_id, eng_sid, owner_id = _resolve_sid_via_share_token(session, share_token)
            if eng_id and eng_sid:
                payload['_target_user_id'] = user_id
                payload['user_context'] = {'id': owner_id, 'tier': 'architect'}
                sio.emit('request_load_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
                app.logger.info(f"[Gateway] Fwd 'load_preset' (Shared Token) -> EngineSID {eng_sid}")
                return
            else:
                app.logger.warning(f"[Gateway] Shared Token Load Preset Failed. Engine not found/offline.")
                sio.emit('response_load_preset', {'error': f'Shared Engine is offline or token invalid.'}, room=sid, namespace='/gui-socket')
                return

        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'load_preset'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            sio.emit('response_load_preset', {'error': f'Engine {target_engine_id or "active"} is not connected.'}, room=sid, namespace='/gui-socket')
            return

        engine = session.query(RegisteredEngine).filter_by(id=eng_id).first()
        if engine and str(engine.user_id) != str(user_id):
             payload['_target_user_id'] = user_id
             payload['user_context'] = {'id': engine.user_id, 'tier': 'architect'}
        else:
             payload['user_context'] = {'id': user_id, 'tier': 'architect'}

        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_load_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'request_load_preset' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")

    except Exception as e:
        app.logger.error(f"[Gateway] Error forwarding 'load_preset': {e}", exc_info=True)
    finally:
        session.close()

@sio.on('response_load_preset', namespace='/engine-socket')
def on_engine_response_load_preset(data):
    app = current_app._get_current_object()
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return

    preset_name = "Unknown"
    payload = {}
    if isinstance(data, dict) and data.get('v') == 2:
        payload = data.get('payload', {})
        preset_name = payload.get('name', 'Unknown')

    target_user_id = payload.get('_target_user_id')

    app.logger.info(f"[Gateway] Received response_load_preset from Engine for preset '{preset_name}'. Forwarding to User {target_user_id or sess.get('user_id')}.")

    engine_id = sess.get('engine_id')

    if engine_id:
        _broadcast_response(engine_id, 'response_load_preset', data)
    else:
        _emit_to_gui(sess.get('user_id'), 'response_load_preset', data)

    if target_user_id and target_user_id != sess.get('user_id'):
          sio.emit('response_load_preset', data, room=str(target_user_id), namespace='/gui-socket')


@sio.on('install_component', namespace='/gui-socket')
def on_install_component(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'install_component' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    user_addr = gui_sess.get('user_address')

    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'install_component' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'install_component'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            sio.emit('component_install_status', {'v': 2, 'payload': {
                'error': f'Engine {target_engine_id or "active"} is not connected.',
                'success': False,
                'component_id': payload.get('component_id'),
                'component_type': payload.get('component_type'),
                'message': 'Engine is not connected to the Gateway.'
            }}, room=sid, namespace='/gui-socket')
            return
        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('install_component', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'install_component' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")
    finally:
        session.close()

@sio.on('uninstall_component', namespace='/gui-socket')
def on_uninstall_component(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None:
        app.logger.warning(f"[Gateway] 'uninstall_component' from unauthenticated SID {sid}.")
        return

    user_id = gui_sess.get('user_id')
    user_addr = gui_sess.get('user_address')

    if not isinstance(data, dict) or data.get('v') != 2:
        app.logger.error(f"[Core] Non-versioned 'uninstall_component' from GUI {sid}.")
        return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            app.logger.warning(f"[Gateway] Cannot forward 'uninstall_component'. No LIVE SID for engine {target_engine_id or 'default active'}.")
            sio.emit('component_install_status', {'v': 2, 'payload': {
                'error': f'Engine {target_engine_id or "active"} is not connected.',
                'success': False,
                'component_id': payload.get('component_id'),
                'component_type': payload.get('component_type'),
                'message': 'Engine is not connected to the Gateway.'
            }}, room=sid, namespace='/gui-socket')
            return
        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('uninstall_component', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
        app.logger.info(f"[Gateway] Fwd 'uninstall_component' GUI {sid} -> EngineSID {eng_sid} (EngineID: {eng_id})")
    finally:
        session.close()


@sio.on('*', namespace='/gui-socket')
def on_gui_catch_all(event, data):
    app = current_app._get_current_object()
    sid = request.sid
    known = {
        'connect', 'disconnect', 'request_presets_list', 'request_variables',
        'request_components_list', 'execute_workflow', 'save_preset',
        'request_ai_status', 'request_datasets_list', 'request_local_models', 'request_training_job_status',
        'request_settings', 'save_settings', 'update_variable', 'delete_variable',
        'request_prompts_list', 'update_prompt', 'delete_prompt', 'load_preset',
        'delete_preset', 'request_dataset_data', 'create_dataset', 'add_dataset_data',
        'delete_dataset', 'update_dataset_row', 'delete_dataset_row',
        'install_component', 'uninstall_component', 'start_training_job',
        'gui:join', 'gui:input',
        'stop_workflow',
        'pause_workflow',
        'response_load_preset',
        'execute_standalone_node',
        'filesystem_list_request' # Added to known list to suppress warning
    }
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    user_id = gui_sess.get('user_id') if gui_sess else 'Anonymous'

    if event not in known:
        app.logger.warning(f"[Gateway GUI] Unhandled event '{event}' from SID {sid} (User: {user_id}). Data: {data}")


@sio.on('gui:join', namespace='/gui-socket')
def on_gui_join_session(data):
    app = current_app._get_current_object()
    sid = request.sid

    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if not gui_sess or not gui_sess.get('user_id'):
        app.logger.warning(f"[GUI Join] SID {sid} tried to join session but is not authenticated (no Web3 connect).")
        return {'ok': False, 'error': 'Socket not authenticated'}

    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict):
        app.logger.warning(f"[GUI Join] User {user_id} (SID {sid}) sent invalid join data.")
        return {'ok': False, 'error': 'Invalid payload format'}

    session_id = data.get('session_id')
    ws_token = data.get('ws_token')

    if not session_id or not ws_token:
        app.logger.warning(f"[GUI Join] User {user_id} (SID {sid}) sent incomplete join data.")
        return {'ok': False, 'error': 'session_id and ws_token are required'}

    session = get_db_session()
    try:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()

        if not agent_session:
            app.logger.warning(f"[GUI Join] User {user_id} (SID {sid}) tried to join non-existent session {session_id}.")
            return {'ok': False, 'error': 'Session not found'}

        is_owner = (agent_session.user_id == user_id)
        has_share_access = False

        if not is_owner:
            share = session.query(EngineShare).filter_by(
                engine_id=agent_session.engine_id,
                user_id=user_id
            ).first()
            if share:
                has_share_access = True
                app.logger.info(f"[GUI Join] User {user_id} is Guest via Share (Role: {share.role}). allowing access.")

        if not is_owner and not has_share_access:
            app.logger.warning(f"[AuthZ] DENIED: User {user_id} (SID {sid}) tried to join session {session_id} owned by {agent_session.user_id} without share.")
            return {'ok': False, 'error': 'Permission denied'}

        if is_owner and not check_password_hash(agent_session.ws_token_hash, ws_token):
             app.logger.warning(f"[AuthZ] DENIED: User {user_id} (SID {sid}) provided invalid ws_token for session {session_id}.")
             return {'ok': False, 'error': 'Invalid session token'}

        join_room(session_id, sid, namespace='/gui-socket')

        gui_sess['gui_session_id'] = session_id
        sio.server.save_session(sid, gui_sess, namespace='/gui-socket')

        app.logger.info(f"[GUI Join] SUCCESS: User {user_id} (SID {sid}) joined agent session room '{session_id}'.")
        return {'ok': True}

    except Exception as e:
        app.logger.error(f"[GUI Join] Error joining session {session_id}: {e}", exc_info=True)
        return {'ok': False, 'error': 'Internal server error'}
    finally:
        session.close()


@sio.on('gui:input', namespace='/gui-socket')
def on_gui_input(data):
    app = current_app._get_current_object()
    sid = request.sid

    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if not gui_sess or not gui_sess.get('user_id'):
        app.logger.warning(f"[GUI Input] SID {sid} sent input but is not authenticated (no Web3 connect).")
        return

    session_id = gui_sess.get('gui_session_id')
    if not session_id:
        app.logger.warning(f"[GUI Input] User {gui_sess.get('user_id')} (SID {sid}) sent input without joining a session first.")
        return

    if not isinstance(data, dict):
        app.logger.warning(f"[GUI Input] SID {sid} sent invalid input data for session {session_id}.")
        return

    session = get_db_session()
    try:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()
        if not agent_session:
            app.logger.error(f"[GUI Input] SID {sid} sent input for non-existent session {session_id}.")
            return

        if agent_session.status != 'running':
            app.logger.warning(f"[GUI Input] SID {sid} sent input, but session {session_id} is not 'running' (status: {agent_session.status}). Ignoring.")
            sio.emit('agent:error', {
                'session_id': session_id,
                'code': 'SESSION_NOT_RUNNING',
                'message': f'Cannot send input, session status is: {agent_session.status}'
            }, room=session_id, namespace='/gui-socket')
            return

        engine_id = agent_session.engine_id

        engine_sid = globals_instance.engine_manager.active_engine_sessions.get(str(engine_id))
        if not engine_sid:
            app.logger.error(f"[GUI Input] Cannot forward input for session {session_id}. Engine {engine_id} is OFFLINE.")
            sio.emit('agent:error', {
                'session_id': session_id,
                'code': 'ENGINE_OFFLINE',
                'message': 'Engine is offline. Cannot process input.'
            }, room=session_id, namespace='/gui-socket')
            return

        payload_content = data.get('text') or data.get('tool')
        if not payload_content:
            app.logger.warning(f"[GUI Input] SID {sid} sent empty input for session {session_id}.")
            return

        core_payload = {
            "type": "input",
            "session_id": session_id,
            "payload": {
                "text": data.get('text'),
                "tool": data.get('tool')
            }
        }

        sio.emit(
            'gw:agent_input',
            core_payload,
            room=engine_id,
            namespace='/core-socket'
        )
        app.logger.info(f"[GUI Input] Fwd input for session {session_id} -> Engine {engine_id} (SID {engine_sid})")

    except Exception as e:
        app.logger.error(f"[GUI Input] Error forwarding input for session {session_id}: {e}", exc_info=True)
    finally:
        session.close()


@sio.on('core:agent_status', namespace='/engine-socket')
def on_core_agent_status(data):
    app = current_app._get_current_object()
    if not isinstance(data, dict) or 'session_id' not in data or 'phase' not in data:
        app.logger.warning(f"[Core Event] Received invalid 'core:agent_status': {data}")
        return

    session_id = data.get('session_id')
    phase = data.get('phase')
    app.logger.info(f"[Core Event] Received status for session {session_id}: {phase}")

    session = get_db_session()
    try:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()
        if agent_session:
            agent_session.status = phase
            session.commit()
        else:
            app.logger.warning(f"[Core Event] Received status for unknown session {session_id}")
    except Exception as e:
        app.logger.error(f"[Core Event] DBError updating status for session {session_id}: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()

    gui_payload = {
        'session_id': session_id,
        'phase': phase
    }
    sio.emit('agent:status', gui_payload, room=session_id, namespace='/gui-socket')


@sio.on('core:agent_token', namespace='/engine-socket')
def on_core_agent_token(data):
    app = current_app._get_current_object()
    if not isinstance(data, dict) or 'session_id' not in data or 'text' not in data:
        app.logger.warning(f"[Core Event] Received invalid 'core:agent_token': {data}")
        return

    session_id = data.get('session_id')
    raw_text = data.get('text')

    redacted_text = _redact_content(raw_text)

    gui_payload = {
        'session_id': session_id,
        'chunk': redacted_text
    }
    sio.emit('agent:token', gui_payload, room=session_id, namespace='/gui-socket')


@sio.on('core:agent_tool', namespace='/engine-socket')
def on_core_agent_tool(data):
    app = current_app._get_current_object()
    if not isinstance(data, dict) or 'session_id' not in data:
        app.logger.warning(f"[Core Event] Received invalid 'core:agent_tool': {data}")
        return

    session_id = data.get('session_id')
    app.logger.info(f"[Core Event] Received tool call for session {session_id}: {data.get('name')}")

    sio.emit('agent:tool', data, room=session_id, namespace='/gui-socket')


@sio.on('core:agent_done', namespace='/engine-socket')
def on_core_agent_done(data):
    app = current_app._get_current_object()
    if not isinstance(data, dict) or 'session_id' not in data:
        app.logger.warning(f"[Core Event] Received invalid 'core:agent_done': {data}")
        return

    session_id = data.get('session_id')
    app.logger.info(f"[Core Event] Received DONE for session {session_id}")

    session = get_db_session()
    try:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()
        if agent_session:
            agent_session.status = 'done'
            agent_session.finished_at = datetime.utcnow()

            episode_id = data.get('episode_id')
            timeline_ptr = data.get('timeline_ptr')

            if episode_id:
                agent_session.episode_id = episode_id
                episode = session.query(Episode).filter_by(id=episode_id).first()
                if episode and timeline_ptr:
                    episode.core_timeline_ptr = timeline_ptr

            session.commit()
        else:
            app.logger.warning(f"[Core Event] Received done for unknown session {session_id}")
    except Exception as e:
        app.logger.error(f"[Core Event] DBError updating done status for session {session_id}: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()

    sio.emit('agent:done', data, room=session_id, namespace='/gui-socket')


@sio.on('core:agent_error', namespace='/engine-socket')
def on_core_agent_error(data):
    app = current_app._get_current_object()
    if not isinstance(data, dict) or 'session_id' not in data:
        app.logger.warning(f"[Core Event] Received invalid 'core:agent_error': {data}")
        return

    session_id = data.get('session_id')
    app.logger.error(f"[Core Event] Received ERROR for session {session_id}: {data.get('code')} - {data.get('message')}")

    session = get_db_session()
    try:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()
        if agent_session:
            agent_session.status = 'error'
            agent_session.finished_at = datetime.utcnow()
            session.commit()
        else:
            app.logger.warning(f"[Core Event] Received error for unknown session {session_id}")
    except Exception as e:
        app.logger.error(f"[Core Event] DBError updating error status for session {session_id}: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()

    sio.emit('agent:error', data, room=session_id, namespace='/gui-socket')

@sio.on('core:request_swarm_task', namespace='/engine-socket')
def on_core_request_swarm_task(data):

    app = current_app._get_current_object()
    origin_sid = request.sid
    origin_sess = _safe_get_session(origin_sid, namespace='/engine-socket')
    if not origin_sess:
        app.logger.warning(f"[Gateway R6] Swarm task request from unauthed SID {origin_sid}. Dropping.")
        return

    origin_user_id = origin_sess.get('user_id')
    target_engine_id = data.get('target_engine_id')
    task_payload = data.get('task_payload', {})
    task_id = task_payload.get('task_id')

    if not all([origin_user_id, target_engine_id, task_id]):
        app.logger.error(f"[Gateway R6] Invalid swarm task request from {origin_sess.get('engine_id')}. Missing fields.")
        sio.emit('gateway:swarm_task_result', {
            "task_id": task_id or "unknown",
            "result": {"error": "GatewayError: Invalid swarm request. Missing target_engine_id or task_id."}
        }, room=origin_sid, namespace='/engine-socket')
        return

    app.logger.info(f"[Gateway R6] Request from SID {origin_sid} for task {task_id} -> Target Engine {target_engine_id}")

    target_sid = globals_instance.engine_manager.active_engine_sessions.get(target_engine_id)
    if not target_sid:
        app.logger.warning(f"[Gateway R6] Target engine {target_engine_id} is OFFLINE. Failing task {task_id}.")
        sio.emit('gateway:swarm_task_result', {
            "task_id": task_id,
            "result": {"error": f"GatewayError: Target engine '{target_engine_id}' is offline."}
        }, room=origin_sid, namespace='/engine-socket')
        return

    target_sess = _safe_get_session(target_sid, namespace='/engine-socket')
    if not target_sess or target_sess.get('user_id') != origin_user_id:
        app.logger.error(f"[Gateway R6] AuthZ FAIL: Engine {origin_sess.get('engine_id')} (User {origin_user_id}) " \
                         f"tried to swarm task to {target_engine_id} (User {target_sess.get('user_id')}).")
        sio.emit('gateway:swarm_task_result', {
            "task_id": task_id,
            "result": {"error": f"GatewayError: Permission denied to access engine '{target_engine_id}'."}
        }, room=origin_sid, namespace='/engine-socket')
        return

    g_swarm_task_registry[task_id] = origin_sid
    app.logger.info(f"[Gateway R6] Task {task_id} registered. Origin SID {origin_sid} is waiting.")

    sio.emit(
        'gateway:execute_swarm_task',
        {"task_payload": task_payload},
        room=target_sid,
        namespace='/engine-socket'
    )
    app.logger.info(f"[Gateway R6] Task {task_id} forwarded to Target SID {target_sid} (Engine {target_engine_id}).")

@sio.on('core:swarm_task_result', namespace='/engine-socket')
def on_core_swarm_task_result(data):

    app = current_app._get_current_object()
    worker_sid = request.sid
    worker_sess = _safe_get_session(worker_sid, namespace='/engine-socket')

    task_id = data.get('task_id')
    result = data.get('result', {})

    if not task_id:
        app.logger.error(f"[Gateway R6] Received swarm result from {worker_sess.get('engine_id')} with no task_id. Dropping.")
        return

    app.logger.info(f"[Gateway R6] Received result for task {task_id} from worker {worker_sess.get('engine_id')}.")

    origin_sid = g_swarm_task_registry.pop(task_id, None)
    if not origin_sid:
        app.logger.warning(f"[Gateway R6] Cannot route result for task {task_id}. Origin SID not found in registry (maybe timed out or duplicate?). Dropping.")
        return

    sio.emit(
        'gateway:swarm_task_result',
        {
            "task_id": task_id,
            "result": result
        },
        room=origin_sid,
        namespace='/engine-socket'
    )
    app.logger.info(f"[Gateway R6] Result for {task_id} forwarded back to Origin SID {origin_sid}.")
