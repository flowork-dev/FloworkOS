########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\dashboard.py total lines 133 
########################################################################

from flask import Blueprint, jsonify, current_app, g
import requests
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sqlalchemy import func
from ..helpers import crypto_auth_required, find_active_engine_session, get_db_session
from ..globals import globals_instance
from ..models import User, RegisteredEngine, EngineShare
from ..extensions import db

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/v1/dashboard")

def _get_live_stats_from_core(user_id, app):

    app.logger.info(f"[Gateway Dashboard] Fetching live stats for user_id: {user_id}")
    session = get_db_session()
    user = session.get(User, user_id)


    core_user_uuid = None
    user_public_address = None

    if user:
        core_user_uuid = str(user.id) # UUID matches 'Executions' table in Core DB
        user_public_address = user.public_address
    else:
        app.logger.warning(f"[_get_live_stats_from_core] User ID {user_id} not found in Gateway DB.")
        return {"active_jobs": [], "system_overview": {}}

    if not core_user_uuid:
        app.logger.warning(f"[_get_live_stats_from_core] User {user_id} has no valid UUID.")
        return {"active_jobs": [], "system_overview": {}}

    active_session = find_active_engine_session(session, user_id)
    core_server_url = None
    active_engine_id = None

    engine_found_and_reachable = False

    if active_session and active_session.internal_url and active_session.engine:
        core_server_url = active_session.internal_url
        active_engine_id = active_session.engine.id
        engine_found_and_reachable = True
        app.logger.info(f"[Gateway Dashboard] Found active engine URL via DB session: {core_server_url} for engine_id: {active_engine_id} (User: {user_id})")
    else:
        app.logger.warning(f"[Gateway Dashboard] Could not find active session URL in DB for user {user_id}. Trying (unreliable) in-memory map...")
        engine_map = globals_instance.engine_manager.engine_url_map

        user_engines = session.query(RegisteredEngine.id).filter_by(user_id=user_id).all()
        shared_engines = session.query(EngineShare.engine_id).filter_by(user_id=user_id).all()

        user_engine_ids = {e[0] for e in user_engines}
        for se in shared_engines:
            user_engine_ids.add(se[0])

        found_url_in_map = None
        for engine_id in user_engine_ids:
            if engine_id in engine_map:
                found_url_in_map = engine_map[engine_id]
                active_engine_id = engine_id
                break

        if found_url_in_map:
            core_server_url = found_url_in_map
            engine_found_and_reachable = True
            app.logger.info(f"[Gateway Dashboard] Found engine URL via (unreliable) in-memory map: {core_server_url} (Engine: {active_engine_id})")
        else:
            app.logger.warning(f"[Gateway Dashboard] No active engine found for user {user_id}. Returning empty stats (Engine likely Offline).")
            return {
                "active_jobs": [],
                "system_overview": {"status": "offline", "message": "Engine not connected"},
                "execution_stats_24h": {"success": 0, "failed": 0},
                "top_failing_presets": [],
                "top_slowest_presets": [],
                "recent_activity": [],
                "usage_stats": {"used": 0}
            }

    target_url = f"{core_server_url}/api/v1/engine/live-stats"
    api_key = os.getenv("GATEWAY_SECRET_TOKEN")
    headers = {"X-API-Key": api_key} if api_key else {}

    headers["X-Flowork-User-ID"] = core_user_uuid
    headers["X-User-Address"] = user_public_address if user_public_address else core_user_uuid

    app.logger.info(f"[Gateway Dashboard] Calling Core Engine endpoint: {target_url} with User-ID header: {core_user_uuid} (Address: {user_public_address})...")

    try:
        resp = requests.get(target_url, headers=headers, timeout=5)
        resp.raise_for_status()
        live_data = resp.json()

        job_count = len(live_data.get('active_jobs', []))
        exec_stats = live_data.get('execution_stats_24h', {})
        app.logger.info(f"[Gateway Dashboard] Successfully fetched live stats. Active jobs: {job_count}, Stats: {exec_stats}")

        return live_data
    except requests.exceptions.RequestException as e:
        app.logger.error(
            f"[Gateway Dashboard] Could not fetch live stats from engine {core_server_url}: {e}"
        )
        return {"active_jobs": [], "system_overview": {}}

@dashboard_bp.route("/summary", methods=["GET"])
@crypto_auth_required
def get_dashboard_summary():
    current_user = g.user

    app = current_app._get_current_object()
    live_stats = _get_live_stats_from_core(current_user.id, app)
    total_engines = 0
    total_shared = 0
    try:
        session = get_db_session()
        total_engines = session.query(RegisteredEngine).filter_by(user_id=current_user.id).count()
        total_shared = session.query(EngineShare).filter_by(user_id=current_user.id).count()
    except Exception as e:
        app.logger.error(f"[Gateway Dashboard] Gagal hitung engine statis: {e}")

    summary_data = {
        **live_stats,
        "total_engines": total_engines,
        "total_shared_with_me": total_shared
    }
    app.logger.info(f"[Gateway Dashboard] Returning summary for user {current_user.id}. Data merged.")
    return jsonify(summary_data)
