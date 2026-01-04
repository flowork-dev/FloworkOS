########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\engine\router.py total lines 84 
########################################################################

import json
import logging
from flask_socketio import Namespace, emit, disconnect
from flask import request
from app.extensions import socketio, db
from app.globals import globals_instance as GLOBALS
from app.engine.registry import EngineRegistry
from app.security.guards import gateway_token_required, engine_token_required
from app.queue.api import enqueue_engine_command

logger = logging.getLogger(__name__)

class EngineNamespace(Namespace):
    @engine_token_required
    def on_connect(self):
        engine_data = request.engine_data
        engine_id, user_id, sid = engine_data['engine_id'], engine_data['user_id'], request.sid
        logger.info(f"[Socket] Engine Connecting: ID={engine_id}")

        if not EngineRegistry.register_engine(engine_id, user_id, sid):
            disconnect()
            return

        emit('gateway_engine_ack', {'status': 'success'})
        socketio.emit('engine_status_update', {'engine_id': engine_id, 'status': 'connected'}, room=f"user_{user_id}", namespace='/gui-socket')

    def on_disconnect(self):
        data = EngineRegistry.get_engine_by_sid(request.sid)
        if data:
            EngineRegistry.unregister_engine(data['engine_id'])
            socketio.emit('engine_status_update', {'engine_id': data['engine_id'], 'status': 'disconnected'}, room=f"user_{data['user_id']}", namespace='/gui-socket')

    @engine_token_required
    def on_engine_heartbeat(self, data):
        EngineRegistry.update_engine_status(request.engine_data['engine_id'], data)

    def on_response_component_list(self, data):
        target_user = data.get('payload', {}).get('_target_user_id')
        if target_user: socketio.emit('response_component_list', data, room=target_user, namespace='/gui-socket')

    def on_response_presets_list(self, data):
        target_user = data.get('payload', {}).get('_target_user_id')
        if target_user: socketio.emit('response_presets_list', data, room=target_user, namespace='/gui-socket')

class GuiNamespace(Namespace):
    @gateway_token_required
    def on_connect(self):
        user_id, sid = request.user_id, request.sid
        self.enter_room(sid, user_id)
        logger.info(f"[Socket] GUI {user_id} joined room.")
        emit('gateway_gui_ack', {'status': 'success'})

    @gateway_token_required
    def on_request_components_list(self, data):
        payload = data.get('payload', {})
        engine_id, user_id = payload.get('target_engine_id'), request.user_id
        engine_sid = GLOBALS.engine_manager.active_engine_sessions.get(engine_id)

        if not engine_sid:
            return emit('response_component_list', {"payload": {"error": "Engine not connected", "component_type": payload.get("component_type"), "components": [], "_target_user_id": user_id}})

        logger.warning(f"⚡ [Socket] Forwarding App Request to Engine {engine_id}")
        payload['user_context'] = {"id": user_id, "tier": "architect"}
        socketio.emit('request_components_list', {"v": 2, "payload": payload}, to=engine_sid, namespace='/engine-socket')

    @gateway_token_required
    def on_request_presets_list(self, data):
        payload = data.get('payload', {})
        engine_id = payload.get('target_engine_id')
        engine_sid = GLOBALS.engine_manager.active_engine_sessions.get(engine_id)
        if engine_sid:
             payload['user_context'] = {"id": request.user_id}
             socketio.emit('request_presets_list', {"v": 2, "payload": payload}, to=engine_sid, namespace='/engine-socket')

    @gateway_token_required
    def on_gui_command(self, data):
        user_id, engine_id, command = request.user_id, data.get('engine_id'), data.get('command')
        if engine_id and command: enqueue_engine_command(engine_id=engine_id, command=command, payload=data.get('payload', {}), user_id=user_id, source_sid=request.sid)
