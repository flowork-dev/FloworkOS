########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\user_state.py total lines 136 
########################################################################

from flask import Blueprint, jsonify, request, current_app, g
from ..extensions import db
from ..models import User, State
from ..helpers import crypto_auth_required

user_state_bp = Blueprint("user_state", __name__, url_prefix="/api/v1/user/state")

FAVORITE_PRESETS_KEY = "favorite_presets"
FAVORITE_COMPONENTS_KEY = "favorite_components"
ACTIVE_WIDGETS_KEY = "active_widgets"

@user_state_bp.route(f"/{FAVORITE_PRESETS_KEY}", methods=["GET"])
@crypto_auth_required
def get_favorite_presets():
    current_user = g.user

    try:
        state_entry = State.query.filter_by(user_id=current_user.id, key=FAVORITE_PRESETS_KEY).first()
        if state_entry and state_entry.value:
            favorites = state_entry.value if isinstance(state_entry.value, list) else []
            current_app.logger.info(f"[State Route] Retrieved {len(favorites)} favorite presets for user {current_user.id}")
            return jsonify(favorites)
        else:
            current_app.logger.info(f"[State Route] No favorite presets found for user {current_user.id}")
            return jsonify([])
    except Exception as e:
        current_app.logger.error(f"[State Route] Error fetching favorite presets for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to retrieve favorite presets."}), 500

@user_state_bp.route(f"/{FAVORITE_PRESETS_KEY}", methods=["PUT"])
@crypto_auth_required
def set_favorite_presets():
    current_user = g.user

    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Request body must be a JSON array of preset IDs."}), 400
    try:
        state_entry = State.query.filter_by(user_id=current_user.id, key=FAVORITE_PRESETS_KEY).first()
        if not state_entry:
            state_entry = State(user_id=current_user.id, key=FAVORITE_PRESETS_KEY)
            db.session.add(state_entry)
        state_entry.value = data
        db.session.commit()
        current_app.logger.info(f"[State Route] Updated favorite presets for user {current_user.id}. Count: {len(data)}")
        return jsonify({"status": "success", "message": "Favorite presets updated."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[State Route] Error saving favorite presets for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to save favorite presets."}), 500

@user_state_bp.route(f"/{FAVORITE_COMPONENTS_KEY}", methods=["GET"])
@crypto_auth_required
def get_favorite_components():
    current_user = g.user

    try:
        state_entry = State.query.filter_by(user_id=current_user.id, key=FAVORITE_COMPONENTS_KEY).first()
        if state_entry and state_entry.value:
            favorites = state_entry.value if isinstance(state_entry.value, list) else []
            current_app.logger.info(f"[State Route] Retrieved {len(favorites)} favorite components for user {current_user.id}")
            return jsonify(favorites)
        else:
            current_app.logger.info(f"[State Route] No favorite components found for user {current_user.id}")
            return jsonify([])
    except Exception as e:
        current_app.logger.error(f"[State Route] Error fetching favorite components for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to retrieve favorite components."}), 500

@user_state_bp.route(f"/{FAVORITE_COMPONENTS_KEY}", methods=["PUT"])
@crypto_auth_required
def set_favorite_components():
    current_user = g.user

    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "Request body must be a JSON array of component IDs."}), 400
    try:
        state_entry = State.query.filter_by(user_id=current_user.id, key=FAVORITE_COMPONENTS_KEY).first()
        if not state_entry:
            state_entry = State(user_id=current_user.id, key=FAVORITE_COMPONENTS_KEY)
            db.session.add(state_entry)
        state_entry.value = data
        db.session.commit()
        current_app.logger.info(f"[State Route] Updated favorite components for user {current_user.id}. Count: {len(data)}")
        return jsonify({"status": "success", "message": "Favorite components updated."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[State Route] Error saving favorite components for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to save favorite components."}), 500

@user_state_bp.route(f"/{ACTIVE_WIDGETS_KEY}", methods=["GET"])
@crypto_auth_required
def get_active_widgets():
    current_user = g.user
    try:
        state_entry = State.query.filter_by(user_id=current_user.id, key=ACTIVE_WIDGETS_KEY).first()
        if state_entry and state_entry.value:
            widgets_state = state_entry.value if isinstance(state_entry.value, list) else []
            return jsonify(widgets_state)
        else:
            return jsonify([])
    except Exception as e:
        current_app.logger.error(f"[State Route] Error fetching active widgets for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to retrieve active widgets."}), 500

@user_state_bp.route(f"/{ACTIVE_WIDGETS_KEY}", methods=["PUT"])
@crypto_auth_required
def set_active_widgets():
    current_user = g.user
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({"error": "Request body must be a JSON array."}), 400

    try:
        state_entry = State.query.filter_by(user_id=current_user.id, key=ACTIVE_WIDGETS_KEY).first()
        if not state_entry:
            state_entry = State(user_id=current_user.id, key=ACTIVE_WIDGETS_KEY)
            db.session.add(state_entry)

        state_entry.value = data
        db.session.commit()

        current_app.logger.info(f"[State Route] Updated active widgets for user {current_user.id}. Count: {len(data)}")
        return jsonify({"status": "success", "message": "Active widgets synced."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[State Route] Error saving active widgets: {e}")
        return jsonify({"error": "Failed to save active widgets."}), 500
