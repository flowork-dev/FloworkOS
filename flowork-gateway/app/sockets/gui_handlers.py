########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\sockets\gui_handlers.py total lines 294 
########################################################################

import json
import uuid
import secrets
from datetime import datetime
from flask import request, current_app
from flask_socketio import join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload

from ..extensions import socketio as sio
from ..models import User, RegisteredEngine, EngineShare, AgentSession
from ..globals import globals_instance
from ..helpers import (
    get_db_session,
    verify_web3_signature
)
from .utils import (
    _safe_get_session,
    _broadcast_response
)

@sio.on('connect', namespace='/gui-socket')
def on_gui_connect(auth):
    """
    Handles Web3-based authentication for GUI clients.
    """
    app = current_app._get_current_object()
    sid = request.sid
    remote_addr = request.environ.get('REMOTE_ADDR', 'N/A')

    query_user_id = request.args.get('user_id')
    if not auth and query_user_id:
        app.logger.info(f"[Gateway GUI] 🌉 App Iframe connected for User {query_user_id} (SID: {sid})")
        sio.server.save_session(sid, {'user_id': query_user_id, 'source': 'app_iframe'}, namespace='/gui-socket')
        join_room(str(query_user_id), sid, namespace='/gui-socket')

        query_engine_id = request.args.get('engine_id')
        if query_engine_id:
            join_room(str(query_engine_id), sid, namespace='/gui-socket')

        return True

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
        return
    user_id = sess.get('user_id')
    try:
        if user_id:
            leave_room(str(user_id), sid, namespace='/gui-socket')
        gui_session_id = sess.get('gui_session_id')
        if gui_session_id:
            leave_room(gui_session_id, sid, namespace='/gui-socket')
    except Exception:
        pass


@sio.on('gui:join', namespace='/gui-socket')
def on_gui_join_session(data):
    app = current_app._get_current_object()
    sid = request.sid

    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if not gui_sess or not gui_sess.get('user_id'):
        return {'ok': False, 'error': 'Socket not authenticated'}

    user_id = gui_sess.get('user_id')

    if not isinstance(data, dict):
        return {'ok': False, 'error': 'Invalid payload format'}

    session_id = data.get('session_id')
    ws_token = data.get('ws_token')

    if not session_id or not ws_token:
        return {'ok': False, 'error': 'session_id and ws_token are required'}

    session = get_db_session()
    try:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()

        if not agent_session:
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

        if not is_owner and not has_share_access:
            return {'ok': False, 'error': 'Permission denied'}

        if is_owner and not check_password_hash(agent_session.ws_token_hash, ws_token):
             return {'ok': False, 'error': 'Invalid session token'}

        join_room(session_id, sid, namespace='/gui-socket')

        gui_sess['gui_session_id'] = session_id
        sio.server.save_session(sid, gui_sess, namespace='/gui-socket')

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
        return

    session_id = gui_sess.get('gui_session_id')
    if not session_id:
        return

    session = get_db_session()
    try:
        agent_session = session.query(AgentSession).filter_by(id=session_id).first()
        if not agent_session or agent_session.status != 'running':
            if agent_session:
                sio.emit('agent:error', {
                    'session_id': session_id,
                    'code': 'SESSION_NOT_RUNNING',
                    'message': f'Cannot send input, session status is: {agent_session.status}'
                }, room=session_id, namespace='/gui-socket')
            return

        engine_id = agent_session.engine_id
        engine_sid = globals_instance.engine_manager.active_engine_sessions.get(str(engine_id))

        if not engine_sid:
            sio.emit('agent:error', {
                'session_id': session_id,
                'code': 'ENGINE_OFFLINE',
                'message': 'Engine is offline. Cannot process input.'
            }, room=session_id, namespace='/gui-socket')
            return

        core_payload = {
            "type": "input",
            "session_id": session_id,
            "payload": {
                "text": data.get('text'),
                "tool": data.get('tool')
            }
        }

        sio.emit('gw:agent_input', core_payload, room=engine_id, namespace='/core-socket')

    except Exception as e:
        app.logger.error(f"[GUI Input] Error: {e}", exc_info=True)
    finally:
        session.close()


@sio.on('*', namespace='/gui-socket')
def on_gui_catch_all(event, data):
    pass
