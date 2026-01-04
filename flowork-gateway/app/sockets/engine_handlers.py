########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\sockets\engine_handlers.py total lines 728 
########################################################################

from flask import request, current_app
from datetime import datetime
from flask_socketio import join_room
from werkzeug.security import check_password_hash

from ..extensions import socketio as sio
from ..models import RegisteredEngine, UserEngineSession, AgentSession, Episode
from ..globals import globals_instance
from ..helpers import (
    get_db_session,
    find_active_engine_session
)
from .constants import (
    g_swarm_task_registry,
    g_job_ownership,
    g_execution_ownership,
    g_engine_active_job
)
from .utils import (
    _safe_get_session,
    _broadcast_response,
    _emit_to_gui,
    _redact_content
)

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
        session.query(UserEngineSession).filter_by(engine_id=engine_id, is_active=True).update({"is_active": False})

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

    if globals_instance.engine_manager.active_engine_sessions.get(str(engine_id)) != sid:
        globals_instance.engine_manager.active_engine_sessions[str(engine_id)] = sid
        app.logger.info(f"[Gateway Vitals] Recovered Engine {engine_id} in RAM session map.")

    if internal_url:
        globals_instance.engine_manager.engine_url_map[engine_id] = internal_url

    session = get_db_session()
    try:
        active_db = find_active_engine_session(session, user_id, engine_id)
        if not active_db:
            session.query(UserEngineSession).filter_by(engine_id=engine_id, is_active=True).update({"is_active": False})

            new_sess = UserEngineSession(
                user_id=user_id,
                engine_id=engine_id,
                internal_url=internal_url or globals_instance.engine_manager.engine_url_map.get(engine_id),
                is_active=True,
                last_activated_at=int(datetime.utcnow().timestamp())
            )
            session.add(new_sess)
            session.commit()
            app.logger.info(f"[Gateway Vitals] Backfilled ACTIVE DB session for engine {engine_id}")

            _broadcast_response(engine_id, 'engine_status_update', {
                'engine_id': engine_id,
                'status': 'online',
                'vitals': None
            })

    except Exception as e:
        app.logger.error(f"[Gateway Vitals] Backfill DB session failed for engine {engine_id}: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()

    _broadcast_response(engine_id, 'engine_vitals_update', {
        'engine_id': engine_id,
        'vitals': payload
    })

@sio.on('engine_log', namespace='/engine-socket')
def handle_engine_log(data):
    """
    Handles execution logs coming from the Engine (Core) and broadcasts them to the GUI.
    Event name from Core: 'engine_log'
    Event name to GUI: 'execution_log'
    """
    app = current_app._get_current_object()
    try:
        sid = request.sid
        sess = _safe_get_session(sid, namespace='/engine-socket')

        engine_id = sess.get('engine_id') if sess else data.get('engine_id')

        if not engine_id:
            pass

        if not engine_id:
            return

        log_level = data.get('level', 'INFO')
        if isinstance(log_level, str):
            log_level = log_level.upper()
        else:
            log_level = 'INFO'

        gui_payload = {
            'timestamp': data.get('timestamp', datetime.utcnow().timestamp()),
            'level': log_level,
            'message': data.get('message', ''),
            'source': data.get('source', 'engine'),
            'engine_id': engine_id,
            'metadata': data.get('metadata', {})
        }


        _broadcast_response(engine_id, 'execution_log', gui_payload)

    except Exception as e:
        app.logger.error(f"[Gateway Log Handler] Error processing log: {e}")

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
@sio.on('settings_state', namespace='/engine-socket')
def on_engine_response_settings(data):
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
    sess = _safe_get_session(request.sid, namespace='/engine-socket')
    if not sess: return
    user_id = sess.get('user_id')
    _emit_to_gui(user_id, 'FILESYSTEM_LIST_RESPONSE', data)

@sio.on('forward_event_to_gui', namespace='/engine-socket')
def on_forward_event_to_gui(data):
    """
    Central Handler for forwarding events from Engine -> GUI.
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
    user_id = payload.get("user_id")

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

    if event_name in ['WORKFLOW_EXECUTION_UPDATE', 'node_status_update']:
        status = event_data.get('status') or (event_data.get('status_data') or {}).get('status')
        if status == 'RUNNING' and current_engine_id and job_id:
            g_engine_active_job[current_engine_id] = job_id

            effective_owner = target_user_id or (sess.get('user_id') if sess else None)
            if effective_owner:
                g_job_ownership[job_id] = effective_owner
                if execution_id:
                    g_execution_ownership[execution_id] = effective_owner

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
        'settings_state'
    }

    STRICT_UNICAST_EVENTS = {
        'SHOW_DEBUG_POPUP',
        'WORKFLOW_LOG_ENTRY',
        'gui:input',
        'FILESYSTEM_LIST_RESPONSE'
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
            if event_name == 'WORKFLOW_LOG_ENTRY' and current_engine_id:
                 _broadcast_response(current_engine_id, event_name, event_data)
            else:
                 app.logger.warning(f"[Gateway] Blocked leakage of private event '{event_name}'. No valid target_user_id found. (Job: {job_id})")

    else:
        if target_user_id:
             sio.emit(event_name, event_data, room=str(target_user_id), namespace='/gui-socket')

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
        app.logger.error(f"[Gateway R6] Invalid swarm task request. Missing fields.")
        sio.emit('gateway:swarm_task_result', {
            "task_id": task_id or "unknown",
            "result": {"error": "GatewayError: Invalid swarm request."}
        }, room=origin_sid, namespace='/engine-socket')
        return

    app.logger.info(f"[Gateway R6] Request from SID {origin_sid} for task {task_id} -> Target Engine {target_engine_id}")

    target_sid = globals_instance.engine_manager.active_engine_sessions.get(target_engine_id)
    if not target_sid:
        app.logger.warning(f"[Gateway R6] Target engine {target_engine_id} is OFFLINE.")
        sio.emit('gateway:swarm_task_result', {
            "task_id": task_id,
            "result": {"error": f"GatewayError: Target engine '{target_engine_id}' is offline."}
        }, room=origin_sid, namespace='/engine-socket')
        return

    target_sess = _safe_get_session(target_sid, namespace='/engine-socket')
    if not target_sess or target_sess.get('user_id') != origin_user_id:
        app.logger.error(f"[Gateway R6] AuthZ FAIL: Swarm attempt between different users.")
        sio.emit('gateway:swarm_task_result', {
            "task_id": task_id,
            "result": {"error": "GatewayError: Permission denied."}
        }, room=origin_sid, namespace='/engine-socket')
        return

    g_swarm_task_registry[task_id] = origin_sid
    app.logger.info(f"[Gateway R6] Task {task_id} registered.")

    sio.emit(
        'gateway:execute_swarm_task',
        {"task_payload": task_payload},
        room=target_sid,
        namespace='/engine-socket'
    )

@sio.on('core:swarm_task_result', namespace='/engine-socket')
def on_core_swarm_task_result(data):
    app = current_app._get_current_object()
    task_id = data.get('task_id')
    result = data.get('result', {})

    if not task_id:
        app.logger.error(f"[Gateway R6] Received swarm result with no task_id.")
        return

    origin_sid = g_swarm_task_registry.pop(task_id, None)
    if not origin_sid:
        app.logger.warning(f"[Gateway R6] Cannot route result for task {task_id}. Origin SID not found.")
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
