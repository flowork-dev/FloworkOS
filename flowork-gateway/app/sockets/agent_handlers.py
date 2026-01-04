########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\sockets\agent_handlers.py total lines 281 
########################################################################

from flask import request, current_app
from ..extensions import socketio as sio
from ..helpers import get_db_session
from .utils import (
    _safe_get_session,
    _resolve_target_engine_sid,
    _inject_fac_if_needed
)


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
