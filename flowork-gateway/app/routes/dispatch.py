########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\dispatch.py total lines 98 
########################################################################

import logging
from flask import Blueprint, request, jsonify, current_app, g
from app.extensions import db
from app.security.guards import gateway_token_required, admin_token_required
from app.engine.registry import EngineRegistry
from app.globals import globals_instance as GLOBALS


dispatch_bp = Blueprint('dispatch_bp', __name__)
logger = logging.getLogger(__name__)


@dispatch_bp.route('/<string:engine_id>/<path:endpoint>', methods=['POST'])
@gateway_token_required
def dispatch_to_engine(engine_id, endpoint):
    """
    (English Hardcode)
    Dynamically dispatches an API request to a specific engine.
    If the engine is connected via WebSocket, it forwards the request.
    If not, it enqueues the request as a job.
    """

    from app.engine.router import engine_router

    from app.queue.api import enqueue_component_call

    user_id = g.user_id
    data = request.get_json()


    handler_func = engine_router.get(endpoint)
    if not handler_func:
        logger.warning(
            f"[Dispatch] 404 - No handler for endpoint '{endpoint}' on engine '{engine_id}'"
        )
        return jsonify(
            {'status': 'error', 'message': f'Endpoint not found: {endpoint}'}
        ), 404

    engine_sid = EngineRegistry.get_sid_by_engine_id(engine_id)
    if engine_sid:
        try:
            logger.debug(
                f"[Dispatch] LIVE dispatching '{endpoint}' to engine {engine_id} (SID: {engine_sid})"
            )
            core_client = GLOBALS.get_core_client()
            core_client.emit_to_engine_sid(
                sid=engine_sid,
                event_name=f"api_dispatch_{endpoint}",
                payload=data,
                callback_id=request.headers.get('X-Request-ID')
            )


            return jsonify({
                'status': 'success',
                'message': 'Request dispatched to live engine.',
                'dispatch_mode': 'live_websocket'
            }), 202

        except Exception as e:
            logger.error(
                f"[Dispatch] Error during LIVE dispatch to {engine_id}: {e}", exc_info=True
            )
            pass

    logger.debug(
        f"[Dispatch] QUEUED dispatching '{endpoint}' for engine {engine_id}"
    )
    try:
        job_id = enqueue_component_call(
            engine_id=engine_id,
            user_id=user_id,
            node_id=data.get('node_id', 'api_dispatch'),
            component_name=f"api:{endpoint}",
            payload=data,
            source_info={'source': 'api_dispatch'}
        )
        return jsonify({
            'status': 'success',
            'message': 'Engine is offline. Request queued for execution.',
            'dispatch_mode': 'queued_db',
            'job_id': job_id
        }), 202

    except Exception as e:
        logger.error(
            f"[Dispatch] Error during QUEUED dispatch to {engine_id}: {e}", exc_info=True
        )
        return jsonify(
            {'status': 'error', 'message': 'Failed to queue request.'}
        ), 500
