########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\agent.py total lines 262 
########################################################################

import uuid
import secrets
from flask import Blueprint, jsonify, request, current_app, g
from werkzeug.security import generate_password_hash
from ..models import db, User, RegisteredEngine, EngineShare, Episode, AgentSession
from ..extensions import socketio
from ..helpers import crypto_auth_required, get_user_permissions
from ..globals import globals_instance
from app.fac_factory import build_fac_for_owner
from app.sharing_fac import build_fac_for_shared_engine

agent_bp = Blueprint("agent", __name__, url_prefix="/api/v1")
engine_manager = globals_instance.engine_manager

@agent_bp.route('/episodes', methods=['GET'])
@crypto_auth_required
def get_episodes():

    current_user = g.user
    engine_id = request.args.get('engine_id')

    if not engine_id:
        return jsonify({"error": "engine_id query parameter is required"}), 400

    perms = get_user_permissions(current_user)
    allowed_engines = perms.get('owned_engines', set()) | perms.get('shared_engines_read', set()) | perms.get('shared_engines_run', set()) | perms.get('shared_engines_admin', set())

    if engine_id not in allowed_engines:
        current_app.logger.warning(f"[AuthZ] DENIED: User {current_user.public_address} tried to GET episodes for un-shared engine {engine_id}")
        return jsonify({"error": "Engine not found or permission denied"}), 404

    try:
        episodes = Episode.query.filter_by(
            user_id=current_user.id,
            engine_id=engine_id
        ).order_by(Episode.created_at.desc()).all()

        episode_list = [
            {
                "id": e.id,
                "title": e.title,
                "intent": e.intent[:100] if e.intent else None,
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat(),
                "core_timeline_ptr": e.core_timeline_ptr
            } for e in episodes
        ]

        return jsonify(episode_list), 200

    except Exception as e:
        current_app.logger.error(f"[Episodes GET] Error fetching episodes for user {current_user.id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve episodes"}), 500


@agent_bp.route('/episodes', methods=['POST'])
@crypto_auth_required
def create_episode():

    current_user = g.user
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    engine_id = data.get('engine_id')
    title = data.get('title', 'New Chat')
    intent = data.get('intent')

    if not engine_id:
        return jsonify({"error": "engine_id is required"}), 400

    perms = get_user_permissions(current_user)
    allowed_engines = perms.get('owned_engines', set()) | perms.get('shared_engines_read', set()) | perms.get('shared_engines_run', set()) | perms.get('shared_engines_admin', set())

    if engine_id not in allowed_engines:
        current_app.logger.warning(f"[AuthZ] DENIED: User {current_user.public_address} tried to POST episode for un-shared engine {engine_id}")
        return jsonify({"error": "Engine not found or permission denied"}), 404

    try:
        new_episode = Episode(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            engine_id=engine_id,
            title=title,
            intent=intent
        )
        db.session.add(new_episode)
        db.session.commit()

        current_app.logger.info(f"[Episodes POST] User {current_user.public_address} created episode {new_episode.id} on engine {engine_id}")

        return jsonify({
            "id": new_episode.id,
            "title": new_episode.title,
            "intent": new_episode.intent,
            "created_at": new_episode.created_at.isoformat(),
            "updated_at": new_episode.updated_at.isoformat(),
            "core_timeline_ptr": new_episode.core_timeline_ptr
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Episodes POST] Error creating episode for user {current_user.id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to create episode"}), 500


@agent_bp.route('/sessions', methods=['POST'])
@crypto_auth_required
def start_session():

    current_user = g.user
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    engine_id = data.get('engine_id')
    intent = data.get('intent')
    episode_id = data.get('episode_id')

    if not engine_id or not intent:
        return jsonify({"error": "engine_id and intent are required"}), 400

    perms = get_user_permissions(current_user)
    allowed_engines = perms.get('owned_engines', set()) | perms.get('shared_engines_run', set()) | perms.get('shared_engines_admin', set())

    if engine_id not in allowed_engines:
        current_app.logger.warning(f"[AuthZ] DENIED: User {current_user.public_address} tried to START session on non-runner engine {engine_id}")
        return jsonify({"error": "Engine not found or permission denied for running"}), 403

    if not engine_manager.is_engine_online(engine_id):
        current_app.logger.warning(f"[Sessions POST] User {current_user.public_address} tried to start session, but engine {engine_id} is OFFLINE.")
        return jsonify({"error": "Engine is offline or not connected"}), 404

    if episode_id:
        episode = Episode.query.filter_by(id=episode_id, user_id=current_user.id, engine_id=engine_id).first()
        if not episode:
            return jsonify({"error": "Episode not found or does not belong to this user/engine"}), 404

    try:
        engine = RegisteredEngine.query.get(engine_id)
        if not engine:
            current_app.logger.warning(f"[Sessions POST] Engine object {engine_id} not found in DB after passing permission checks.")
            return jsonify({"error": "Engine data not found"}), 404

        is_owner = str(current_user.id) == str(engine.user_id)
        fac_dict = None

        try:
            if is_owner:
                current_app.logger.debug(f"[Sessions POST] Building FAC for OWNER {current_user.id} on engine {engine_id}")
                fac_dict = build_fac_for_owner(request_user=current_user, engine=engine, intent=intent)
            else:
                current_app.logger.debug(f"[Sessions POST] Building FAC for SHARED USER {current_user.id} on engine {engine_id}")
                fac_dict = build_fac_for_shared_engine(request_user=current_user, engine=engine)
        except PermissionError as e:
            current_app.logger.warning(f"[AuthZ] DENIED: User {current_user.public_address} FAC build failed: {e}")
            return jsonify({"error": str(e)}), 403
        except Exception as e_fac:
            current_app.logger.error(f"[Sessions POST] CRITICAL: FAC build failed unexpectedly: {e_fac}", exc_info=True)
            return jsonify({"error": "Failed to build session contract"}), 500

        if not fac_dict:
            current_app.logger.error(f"[Sessions POST] CRITICAL: FAC dictionary is None after build for user {current_user.id}.")
            return jsonify({"error": "Failed to initialize session contract"}), 500

        session_id = str(uuid.uuid4())
        ws_token = secrets.token_urlsafe(32)
        ws_token_hash = generate_password_hash(ws_token, method="pbkdf2:sha256")

        new_session = AgentSession(
            id=session_id,
            user_id=current_user.id,
            engine_id=engine_id,
            episode_id=episode_id,
            ws_token_hash=ws_token_hash,
            status='starting'
        )
        db.session.add(new_session)
        db.session.commit()

        start_payload = {
            "type": "start",
            "session_id": session_id,
            "engine_id": engine_id,
            "intent": intent,
            "fac": fac_dict,
            "context": {
                "user_id": current_user.id,
                "public_address": current_user.public_address,
                "episode_id": episode_id
            }
        }

        socketio.emit(
            'gw:start_session',
            start_payload,
            room=engine_id,
            namespace='/core-socket'
        )

        current_app.logger.info(f"[Sessions POST] User {current_user.public_address} started session {session_id} on engine {engine_id}. 'gw:start_session' emitted.")

        return jsonify({
            "session_id": session_id,
            "ws_token": ws_token
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Sessions POST] Error starting session for user {current_user.id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to start session"}), 500


@agent_bp.route('/sessions/<string:session_id>/cancel', methods=['POST'])
@crypto_auth_required
def cancel_session(session_id):

    current_user = g.user

    session = AgentSession.query.filter_by(id=session_id).first()

    if not session:
        return jsonify({"error": "Session not found"}), 404
    if session.user_id != current_user.id:
        current_app.logger.warning(f"[AuthZ] DENIED: User {current_user.public_address} tried to CANCEL session {session_id} they do not own.")
        return jsonify({"error": "Permission denied"}), 403

    if session.status in ['cancelled', 'error', 'done']:
        return jsonify({"message": "Session already inactive"}), 200

    try:
        session.status = 'cancelled'
        db.session.commit()

        engine_id = session.engine_id

        cancel_payload = {
            "type": "cancel",
            "session_id": session_id
        }

        socketio.emit(
            'gw:cancel_session',
            cancel_payload,
            room=engine_id,
            namespace='/core-socket'
        )

        current_app.logger.info(f"[Sessions CANCEL] User {current_user.public_address} cancelled session {session_id} on engine {engine_id}. 'gw:cancel_session' emitted.")

        return jsonify({"message": "Cancel request sent"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Sessions CANCEL] Error cancelling session {session_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to send cancel request"}), 500
