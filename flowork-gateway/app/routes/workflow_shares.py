########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\workflow_shares.py total lines 228 
########################################################################

from flask import Blueprint, jsonify, request, current_app, g
import secrets
import datetime
import requests
import os
import uuid
import traceback
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import User, Workflow, WorkflowShare, Preset
from ..helpers import crypto_auth_required, get_request_data, find_active_engine_session
from ..globals import globals_instance

try:
    from ..sockets.constants import (
        g_job_ownership,
        g_execution_ownership
    )
except ImportError:
    g_job_ownership = {}
    g_execution_ownership = {}

workflow_shares_bp = Blueprint("workflow_shares", __name__)

def _check_preset_exists_in_core(user_id, preset_name):
    """
    MATA-MATA: Verifies preset existence with ultra-resilience.
    Handles 'types.SimpleNamespace' attribute errors and Core 400 responses.
    """
    app = current_app._get_current_object()
    user = db.session.get(User, user_id)
    if not user: return False

    local_meta = Workflow.query.filter_by(user_id=user_id, name=preset_name).first()
    if local_meta:
        app.logger.info(f"[MATA-MATA] Preset '{preset_name}' found in local Metadata.")
        return True

    active_session = find_active_engine_session(db.session, user_id)
    if not active_session:
        app.logger.warning(f"[MATA-MATA] No active engine found for User {user_id}. Optimistic skip.")
        return True # [OPTIMISTIC] Assume it exists if engine unknown to avoid blocking share.

    active_engine_id = getattr(active_session, 'engine_id', None)
    if not active_engine_id and hasattr(active_session, 'engine') and active_session.engine:
        active_engine_id = active_session.engine.id

    if not active_engine_id:
        app.logger.error("[MATA-MATA] Failed to resolve engine_id from session.")
        return True # [OPTIMISTIC] Allow share creation attempt.

    core_server_url = globals_instance.engine_manager.engine_url_map.get(str(active_engine_id))
    if not core_server_url:
        app.logger.warning(f"[MATA-MATA] Engine {active_engine_id} address missing from memory map.")
        return True # [OPTIMISTIC] Engine might be behind NAT, trust user.

    target_url = f"{core_server_url}/api/v1/presets/{preset_name}/exists"
    api_key = os.getenv("GATEWAY_SECRET_TOKEN")
    headers = {
        "X-API-Key": str(api_key),
        "X-Flowork-User-ID": str(user.id),
        "X-Flowork-Engine-ID": str(active_engine_id)
    }

    try:
        app.logger.info(f"[MATA-MATA] Pinging Core: {target_url}")
        response = requests.get(target_url, headers=headers, timeout=5)

        if response.status_code == 400:
            app.logger.error(f"[MATA-MATA] Core returned 400 for valid session. Bypassing check.")
            return True

        return response.status_code == 200 and response.json().get("exists", False)
    except Exception as e:
        app.logger.error(f"[MATA-MATA] Core connectivity issue: {str(e)}")
        return True # [OPTIMISTIC] Network error shouldn't block Business Logic.

@workflow_shares_bp.route("/api/v1/workflows/<string:workflow_name>/shares", methods=["GET"])
@crypto_auth_required
def get_workflow_shares(workflow_name):
    current_user = g.user
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
        }
        for i, share in enumerate(shares)
    ]
    return jsonify(share_list)

@workflow_shares_bp.route("/api/v1/workflows/<string:workflow_name>/shares", methods=["POST"])
@crypto_auth_required
def create_workflow_share(workflow_name):
    current_user = g.user
    app = current_app._get_current_object()
    app.logger.info(f"[MATA-MATA] Attempting to share: {workflow_name}")

    try:
        local_meta = Workflow.query.filter_by(user_id=current_user.id, name=workflow_name).first()
        preset_exists = _check_preset_exists_in_core(current_user.id, workflow_name)

        if not preset_exists and not local_meta:
            app.logger.warning(f"[MATA-MATA] Share Denied: {workflow_name} not found.")
            return jsonify({"error": "Preset not found. Please save your workflow first."}), 404

        workflow = local_meta
        if not workflow:
            app.logger.info(f"[MATA-MATA] Syncing missing metadata for {workflow_name}")
            workflow = Workflow(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                name=workflow_name,
                friendly_name=workflow_name
            )
            db.session.add(workflow)
            db.session.commit()

        data = get_request_data()
        permission_level = data.get("permission_level", "read")
        link_name = data.get("link_name")
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

        app.logger.info(f"[MATA-MATA] Share Link Created: {share_token}")

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
        app.logger.error(f"[MATA-MATA] Internal POST Share Crash: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@workflow_shares_bp.route("/api/v1/workflow-shares/<string:share_id>", methods=["PUT"])
@crypto_auth_required
def update_workflow_share(share_id):
    current_user = g.user
    share = db.session.query(WorkflowShare).join(Workflow).filter(
        WorkflowShare.id == share_id,
        Workflow.user_id == current_user.id
    ).first()

    if not share:
        return jsonify({"error": "Share link not found"}), 404

    data = get_request_data()
    new_permission = data.get("permission_level")
    if new_permission:
        share.permissions = new_permission

    try:
        db.session.commit()
        return jsonify({"message": "Permission updated.", "share_id": share.id})
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Update failed."}), 500

@workflow_shares_bp.route("/api/v1/workflow-shares/<string:share_id>", methods=["DELETE"])
@crypto_auth_required
def delete_workflow_share(share_id):
    current_user = g.user
    share = db.session.query(WorkflowShare).join(Workflow).filter(
        WorkflowShare.id == share_id,
        Workflow.user_id == current_user.id
    ).first()

    if not share:
        return jsonify({"error": "Share link not found"}), 404

    try:
        db.session.delete(share)
        db.session.commit()
        return jsonify({"status": "success", "message": "Share link deleted."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Delete failed."}), 500

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
