########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\engine\router.py total lines 183 
########################################################################

import json
import logging
from flask_socketio import Namespace, emit, disconnect
from flask import request
from app.extensions import socketio, db
from app.globals import globals_instance as GLOBALS
from app.engine.registry import EngineRegistry
from app.security.guards import gateway_token_required, engine_token_required
from app.queue.api import (
    enqueue_workflow_run,
    enqueue_engine_command,
    enqueue_component_call
)


logger = logging.getLogger(__name__)


class EngineNamespace(Namespace):


    @engine_token_required
    def on_connect(self):

        engine_data = request.engine_data
        engine_id = engine_data['engine_id']
        user_id = engine_data['user_id']
        sid = request.sid

        logger.info(
            f"[Socket] Engine connected: SID={sid}, EngineID={engine_id}, UserID={user_id}"
        )

        success = EngineRegistry.register_engine(
            engine_id=engine_id,
            user_id=user_id,
            sid=sid
        )

        if not success:
            logger.warning(
                f"[Socket] Engine registration failed for EngineID={engine_id}. Disconnecting."
            )
            disconnect()
            return

        emit('gateway_engine_ack', {
            'status': 'success',
            'message': 'Engine connection acknowledged by Gateway.'
        })

        user_room = f"user_{user_id}"
        socketio.emit('engine_status_update', {
            'engine_id': engine_id,
            'status': 'connected'
        }, room=user_room, namespace='/gui')

        enqueue_engine_command(
            engine_id=engine_id,
            command='load_default_workflow',
            payload={}
        )

    def on_disconnect(self):

        sid = request.sid
        engine_data = EngineRegistry.get_engine_by_sid(sid)

        if engine_data:
            engine_id = engine_data['engine_id']
            user_id = engine_data['user_id']
            logger.info(
                f"[Socket] Engine disconnected: SID={sid}, EngineID={engine_id}"
            )
            EngineRegistry.unregister_engine(engine_id)

            user_room = f"user_{user_id}"
            socketio.emit('engine_status_update', {
                'engine_id': engine_id,
                'status': 'disconnected'
            }, room=user_room, namespace='/gui')
        else:
            logger.warning(
                f"[Socket] Unknown engine disconnected: SID={sid}"
            )

    @engine_token_required
    def on_engine_heartbeat(self, data):

        engine_id = request.engine_data['engine_id']
        EngineRegistry.update_engine_status(engine_id, data)

    @engine_token_required
    def on_engine_event(self, data):

        engine_id = request.engine_data['engine_id']
        user_id = request.engine_data['user_id']
        event_name = data.get('event', 'engine_notification')
        payload = data.get('payload', {})

        if 'engine_id' not in payload:
            payload['engine_id'] = engine_id

        user_room = f"user_{user_id}"
        socketio.emit(
            event_name,
            payload,
            room=user_room,
            namespace='/gui'
        )

    @engine_token_required
    def on_workflow_execution_update(self, data):

        user_id = request.engine_data['user_id']
        user_room = f"user_{user_id}"
        socketio.emit(
            'workflow_update',
            data,
            room=user_room,
            namespace='/gui'
        )


class GuiNamespace(Namespace):


    @gateway_token_required
    def on_connect(self):

        user_id = request.user_id
        sid = request.sid
        logger.info(
            f"[Socket] GUI client connected: SID={sid}, UserID={user_id}"
        )

        user_room = f"user_{user_id}"
        self.enter_room(sid, user_room)
        logger.info(
            f"[Socket] GUI client SID={sid} joined room {user_room}"
        )

        emit('gateway_gui_ack', {
            'status': 'success',
            'message': 'GUI connection acknowledged by Gateway.'
        })

    def on_disconnect(self):

        logger.info(f"[Socket] GUI client disconnected: SID={request.sid}")

    @gateway_token_required
    def on_gui_command(self, data):

        user_id = request.user_id
        engine_id = data.get('engine_id')
        command = data.get('command')
        payload = data.get('payload', {})

        if not engine_id or not command:
            logger.warning(
                f"[Socket] Invalid GUI command from {user_id}: Missing engine_id or command"
            )
            return emit('gateway_error', {'message': 'Invalid command format.'})


        logger.info(
            f"[Socket] Queuing command '{command}' from GUI {user_id} for Engine {engine_id}"
        )

        enqueue_engine_command(
            engine_id=engine_id,
            command=command,
            payload=payload,
            user_id=user_id,
            source_sid=request.sid
        )
