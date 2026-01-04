########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\sockets\workflow_handlers.py total lines 356 
########################################################################

from flask import request, current_app
from flask_socketio import join_room, leave_room
from ..extensions import socketio as sio
from ..models import RegisteredEngine, Workflow, db
from ..helpers import get_db_session
import uuid
import json
from .constants import (
    g_job_ownership,
    g_execution_ownership
)
from .utils import (
    _safe_get_session,
    _resolve_target_engine_sid,
    _inject_fac_if_needed,
    _resolve_sid_via_share_token
)

@sio.on('join_workflow_room', namespace='/gui-socket')
def on_join_workflow_room(data):
    """GUI joins a room dedicated to its user_id to receive engine updates"""
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess:
        user_id = gui_sess.get('user_id')
        if user_id:
            room_name = str(user_id)
            join_room(room_name)
            current_app.logger.info(f"[MATA-MATA] GUI SID {sid} joined room {room_name}")


@sio.on('execution_log', namespace='/engine-socket')
@sio.on('WORKFLOW_LOG_ENTRY', namespace='/engine-socket')
def on_engine_log_relay(data):
    """Relay logs from Engine to the correct GUI user room"""
    app = current_app._get_current_object()
    payload = data.get('payload', {}) if isinstance(data, dict) else data
    job_id = payload.get('job_id')

    user_id = payload.get('_target_user_id') or g_execution_ownership.get(job_id) or g_job_ownership.get(job_id)

    if user_id:
        sio.emit('WORKFLOW_LOG_ENTRY', data, room=str(user_id), namespace='/gui-socket')
        sio.emit('log_received', data, room=str(user_id), namespace='/gui-socket')

@sio.on('node_status_update', namespace='/engine-socket')
@sio.on('NODE_STATUS_UPDATE', namespace='/engine-socket')
def on_node_status_relay(data):
    """Relay node status (lampu nyala) from Engine to GUI"""
    app = current_app._get_current_object()
    payload = data.get('payload', {}) if isinstance(data, dict) else data
    job_id = payload.get('job_id')

    user_id = payload.get('_target_user_id') or g_execution_ownership.get(job_id) or g_job_ownership.get(job_id)

    if user_id:
        sio.emit('node_status_update', data, room=str(user_id), namespace='/gui-socket')
        sio.emit('NODE_STATUS_UPDATE', data, room=str(user_id), namespace='/gui-socket')

@sio.on('execution_update', namespace='/engine-socket')
@sio.on('WORKFLOW_EXECUTION_UPDATE', namespace='/engine-socket')
def on_execution_update_relay(data):
    """Relay timeline/progress updates from Engine to GUI"""
    app = current_app._get_current_object()
    payload = data.get('payload', {}) if isinstance(data, dict) else data
    job_id = payload.get('job_id')

    user_id = payload.get('_target_user_id') or g_execution_ownership.get(job_id)

    if user_id:
        sio.emit('WORKFLOW_EXECUTION_UPDATE', data, room=str(user_id), namespace='/gui-socket')
        sio.emit('execution_update', data, room=str(user_id), namespace='/gui-socket')

@sio.on('response_load_preset', namespace='/engine-socket')
def on_engine_load_preset_relay(data):
    payload = data.get('payload', {})
    target_user_id = data.get('_target_user_id') or payload.get('_target_user_id')
    if target_user_id:
        sio.emit('response_load_preset', data, room=str(target_user_id), namespace='/gui-socket')

@sio.on('request_presets_list', namespace='/gui-socket')
def on_request_presets_list(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')

    payload['_target_user_id'] = user_id

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if not eng_id or not eng_sid:
            err_msg = f'Engine {target_engine_id or "active"} is offline.'
            sio.emit('response_presets_list', {'error': err_msg}, room=sid, namespace='/gui-socket')
            return

        payload['user_context'] = {'id': user_id, 'tier': 'architect'}
        payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
        sio.emit('request_presets_list', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('request_variables', namespace='/gui-socket')
def on_request_variables(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    payload['_target_user_id'] = user_id

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            payload['user_context'] = {'id': user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('request_variables', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('request_components_list', namespace='/gui-socket')
def on_request_components_list(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    payload['_target_user_id'] = user_id

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            payload['user_context'] = {'id': user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('request_components_list', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('response_component_list', namespace='/engine-socket')
def on_response_component_list(data):
    payload = data.get('payload', {})
    target_user_id = payload.get('_target_user_id')
    if target_user_id:
        sio.emit('response_component_list', data, room=str(target_user_id), namespace='/gui-socket')

@sio.on('execute_workflow', namespace='/gui-socket')
def on_execute_workflow(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2: return

    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    job_id = payload.get('job_id')
    payload['_target_user_id'] = user_id

    if job_id:
        g_job_ownership[job_id] = user_id
        g_execution_ownership[job_id] = user_id
        app.logger.info(f"[MATA-MATA] New Execution Tracked: Job={job_id} -> User={user_id}")

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            payload['user_context'] = {'id': user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('execute_workflow', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('save_preset', namespace='/gui-socket')
def on_save_preset(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    workflow_name = payload.get('name')
    target_engine_id = payload.get('target_engine_id')
    payload['_target_user_id'] = user_id

    if workflow_name:
        try:
            existing = Workflow.query.filter_by(user_id=user_id, name=workflow_name).first()
            if not existing:
                new_wf = Workflow(id=str(uuid.uuid4()), user_id=user_id, name=workflow_name, friendly_name=workflow_name)
                db.session.add(new_wf)
                db.session.commit()
        except Exception as e:
            app.logger.error(f"[MATA-MATA] Failed proactive sync: {e}")

    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            payload['user_context'] = {'id': user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('save_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('load_preset', namespace='/gui-socket')
def on_load_preset(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return

    user_id = gui_sess.get('user_id')
    if not isinstance(data, dict) or data.get('v') != 2: return
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    share_token = payload.get('share_token')
    payload['_target_user_id'] = user_id

    session = get_db_session()
    try:
        if share_token:
            eng_id, eng_sid, owner_id = _resolve_sid_via_share_token(session, share_token)
            if eng_sid:
                payload['user_context'] = {'id': owner_id, 'tier': 'architect'}
                sio.emit('request_load_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
                return

        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            engine = session.query(RegisteredEngine).filter_by(id=eng_id).first()
            payload['user_context'] = {'id': engine.user_id if engine else user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('request_load_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('delete_preset', namespace='/gui-socket')
def on_delete_preset(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    payload['_target_user_id'] = user_id
    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            payload['user_context'] = {'id': user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('delete_preset', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('install_component', namespace='/gui-socket')
def on_install_component(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    payload['_target_user_id'] = user_id
    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            payload['user_context'] = {'id': user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('install_component', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('uninstall_component', namespace='/gui-socket')
def on_uninstall_component(data):
    app = current_app._get_current_object()
    sid = request.sid
    gui_sess = _safe_get_session(sid, namespace='/gui-socket')
    if gui_sess is None: return
    user_id = gui_sess.get('user_id')
    payload = data.get('payload', {})
    target_engine_id = payload.get('target_engine_id')
    payload['_target_user_id'] = user_id
    session = get_db_session()
    try:
        eng_id, eng_sid = _resolve_target_engine_sid(session, user_id, target_engine_id)
        if eng_sid:
            payload['user_context'] = {'id': user_id, 'tier': 'architect'}
            payload = _inject_fac_if_needed(session, user_id, eng_id, payload)
            sio.emit('uninstall_component', {'v': 2, 'payload': payload}, room=eng_sid, namespace='/engine-socket')
    finally:
        session.close()

@sio.on('forward_event_to_gui', namespace='/engine-socket')
def on_forward_event_to_gui(data):
    """
    [FIX] Unpacks enveloped events from Core and relays them to the specific User GUI Room.
    Dynamically resolves User ID from Job ID if Core forgot to include it.
    """
    app = current_app._get_current_object()

    if not isinstance(data, dict) or 'payload' not in data:
        return

    inner = data['payload']
    event_name = inner.get('event_name')
    event_data = inner.get('event_data') or {}

    target_user_id = inner.get('user_id')

    if not target_user_id:
        job_id = event_data.get('job_id')
        if job_id:
            target_user_id = g_execution_ownership.get(job_id) or g_job_ownership.get(job_id)

    if not event_name or not target_user_id:
        return

    app.logger.info(f"[MATA-MATA] Universal Relay: {event_name} -> User {target_user_id}")

    sio.emit(event_name, event_data, room=str(target_user_id), namespace='/gui-socket')

    if event_name == 'WORKFLOW_LOG_ENTRY':
        sio.emit('log_received', event_data, room=str(target_user_id), namespace='/gui-socket')
    elif event_name == 'WORKFLOW_EXECUTION_UPDATE':
        sio.emit('execution_update', event_data, room=str(target_user_id), namespace='/gui-socket')
