########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\workflow_shares.py total lines 205 
########################################################################

from flask import Blueprint, jsonify, request, current_app, g
import secrets
import datetime
import requests
import os
import uuid
from sqlalchemy.orm import joinedload
from ..extensions import db
from ..models import User, Workflow, WorkflowShare, Preset
from ..helpers import crypto_auth_required, get_request_data, find_active_engine_session
from ..globals import globals_instance

workflow_shares_bp = Blueprint("workflow_shares", __name__)

def _check_preset_exists_in_core(user_id, preset_name):
    app = current_app._get_current_object()

    user = db.session.get(User, user_id)
    if not user:
        app.logger.warning(f"[_check_preset_exists_in_core] User ID {user_id} not found.")
        return False

    active_session = find_active_engine_session(db.session, user_id)
    if not active_session or not active_session.engine:
        app.logger.warning(f"[_check_preset_exists_in_core] No active engine session found.")
        return False

    active_engine_id = active_session.engine.id
    core_server_url = globals_instance.engine_manager.engine_url_map.get(active_engine_id)

    if not core_server_url:
        app.logger.warning(f"[_check_preset_exists_in_core] Active engine URL not found.")
        return False

    target_url = f"{core_server_url}/api/v1/presets/{preset_name}/exists"
    api_key = os.getenv("GATEWAY_SECRET_TOKEN")

    headers = {
        "X-API-Key": api_key,
        "X-Flowork-User-ID": str(user.id),
        "X-Flowork-Engine-ID": active_engine_id
    }

    try:
        app.logger.info(f"[_check_preset_exists_in_core] Checking core: {target_url} (User UUID: {user.id})")
        response = requests.get(target_url, headers=headers, timeout=5)
        return response.status_code == 200 and response.json().get("exists")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"[_check_preset_exists_in_core] Error contacting Core: {e}")
        return False

@workflow_shares_bp.route("/api/v1/workflows/<string:workflow_name>/shares", methods=["GET"])
@crypto_auth_required
def get_workflow_shares(workflow_name):
    current_user = g.user

    preset_exists_in_core = _check_preset_exists_in_core(current_user.id, workflow_name)
    if not preset_exists_in_core:
        return jsonify({"error": "Preset not found in the active engine."}), 404

    workflow = Workflow.query.filter_by(user_id=current_user.id, name=workflow_name).first()
    if not workflow:
        return jsonify([])

    shares = WorkflowShare.query.filter_by(workflow_id=workflow.id).order_by(WorkflowShare.created_at.desc()).all()

    share_list = [
        {
            "share_id": share.id,
            "share_token": share.share_token,
            "share_url": f"https://flowork.cloud/shared/{share.share_token}",
            "permission_level": share.permissions,
            "link_name": share.link_name or f"Link {i+1}",
            "created_at": share.created_at.isoformat() if share.created_at else None
        } for i, share in enumerate(shares)
    ]
    return jsonify(share_list)

@workflow_shares_bp.route("/api/v1/workflows/<string:workflow_name>/shares", methods=["POST"])
@crypto_auth_required
def create_workflow_share(workflow_name):
    current_user = g.user

    preset_exists_in_core = _check_preset_exists_in_core(current_user.id, workflow_name)
    if not preset_exists_in_core:
        return jsonify({"error": "Preset not found in the active engine. Cannot create share link."}), 404

    workflow = Workflow.query.filter_by(user_id=current_user.id, name=workflow_name).first()
    if not workflow:
        workflow = Workflow(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=workflow_name,
            friendly_name=workflow_name
        )
        db.session.add(workflow)
        db.session.flush()

    data = get_request_data()
    permission_level = data.get("permission_level", "read")
    link_name = data.get("link_name")

    if permission_level not in ["read", "read_write", "view", "view-run", "view-edit-run"]:
        return jsonify({"error": "Invalid permission level."}), 400

    try:
        share_token = secrets.token_urlsafe(16)
        new_share = WorkflowShare(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            share_token=share_token,
            permissions=permission_level,
            link_name=link_name,
            owner_id=current_user.id,
            user_id=current_user.id
        )
        db.session.add(new_share)
        db.session.commit()

        return jsonify({
            "message": "Share link created successfully.",
            "share_id": new_share.id,
            "share_token": new_share.share_token,
            "share_url": f"https://flowork.cloud/shared/{new_share.share_token}",
            "permission_level": new_share.permissions,
            "link_name": new_share.link_name,
            "created_at": new_share.created_at.isoformat() if new_share.created_at else None
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create share link: {e}", exc_info=True)
        return jsonify({"error": "Failed to create share link."}), 500

@workflow_shares_bp.route("/api/v1/workflow-shares/<string:share_id>", methods=["PUT"])
@crypto_auth_required
def update_workflow_share(share_id):
    current_user = g.user
    share = db.session.query(WorkflowShare).join(Workflow).filter(
        WorkflowShare.id == share_id,
        Workflow.user_id == current_user.id
    ).first()

    if not share:
        return jsonify({"error": "Share link not found or permission denied."}), 404

    data = get_request_data()
    new_permission = data.get("permission_level")
    if new_permission:
        share.permissions = new_permission

    try:
        share.workflow.updated_at = db.func.now()
        db.session.commit()
        return jsonify({
            "message": "Permission updated successfully.",
            "share_id": share.id,
            "permission_level": share.permissions
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update permission."}), 500

@workflow_shares_bp.route("/api/v1/workflow-shares/<string:share_id>", methods=["DELETE"])
@crypto_auth_required
def delete_workflow_share(share_id):
    current_user = g.user
    share = db.session.query(WorkflowShare).join(Workflow).filter(
        WorkflowShare.id == share_id,
        Workflow.user_id == current_user.id
    ).first()

    if not share:
        return jsonify({"error": "Share link not found or permission denied."}), 404

    try:
        db.session.delete(share)
        db.session.commit()
        return jsonify({"status": "success", "message": "Share link deleted."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete share link."}), 500

@workflow_shares_bp.route("/api/v1/workflow-shares/resolve/<string:share_token>", methods=["GET"])
def resolve_share_token(share_token):
    share = db.session.query(WorkflowShare).options(
        joinedload(WorkflowShare.workflow).joinedload(Workflow.user)
    ).filter_by(share_token=share_token).first()

    if not share or not share.workflow or not share.workflow.user:
        return jsonify({"error": "Invalid or expired share token."}), 404

    return jsonify({
        "permission_level": share.permissions,
        "workflow_name": share.workflow.name,
        "owner_username": share.workflow.user.username,
        "owner_id": share.workflow.user.public_address,
        "preset_name": share.workflow.name
    })
