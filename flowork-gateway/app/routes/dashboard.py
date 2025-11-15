########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\dashboard.py total lines 111 
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
    """
    (PERBAIKAN) Helper to fetch live data (active jobs, system overview) from the user's
    active core engine (owned OR the first active shared engine).
    Uses the modified `find_active_engine_session` helper.
    """
    app.logger.info(f"[Gateway Dashboard] Fetching live stats for user_id: {user_id}")
    session = get_db_session()
    user = session.get(User, user_id)
    core_user_id = None
    if user:
        core_user_id = user.public_address
    else:
        app.logger.warning(f"[_get_live_stats_from_core] User ID {user_id} not found in Gateway DB.")
        return {"active_jobs": [], "system_overview": {}}
    if not core_user_id:
        app.logger.warning(f"[_get_live_stats_from_core] User {user_id} has no public_address set.")
        return {"active_jobs": [], "system_overview": {}}

    active_session = find_active_engine_session(session, user_id)
    core_server_url = None
    active_engine_id = None

    if active_session and active_session.internal_url and active_session.engine:
        core_server_url = active_session.internal_url
        active_engine_id = active_session.engine.id
        app.logger.info(f"[Gateway Dashboard] Found active engine URL via DB session: {core_server_url} for engine_id: {active_engine_id} (User: {user_id})")
    else:
        app.logger.warning(f"[Gateway Dashboard] Could not find active session URL in DB for user {user_id}. Trying (unreliable) in-memory map...")
        engine_map = globals_instance.engine_manager.engine_url_map

        user_engines = session.query(RegisteredEngine.id).filter_by(user_id=user_id).all()
        user_engine_ids = {e[0] for e in user_engines}

        found_url_in_map = None
        for engine_id in user_engine_ids:
            if engine_id in engine_map:
                found_url_in_map = engine_map[engine_id]
                active_engine_id = engine_id
                break

        if found_url_in_map:
            core_server_url = found_url_in_map
            app.logger.info(f"[Gateway Dashboard] Found engine URL via (unreliable) in-memory map: {core_server_url} (Engine: {active_engine_id})")
        else:
            fallback = globals_instance.engine_manager.get_next_core_server()
            if not fallback:
                app.logger.warning(f"[Gateway Dashboard] No active engine in DB and no healthy fallback in (unreliable) memory map.")
                return {"active_jobs": [], "system_overview": {}}
            core_server_url = fallback
            app.logger.warning(f"[Gateway Dashboard] Using (unreliable) healthy fallback engine URL: {core_server_url} (User: {user_id})")

    target_url = f"{core_server_url}/api/v1/engine/live-stats"
    api_key = os.getenv("GATEWAY_SECRET_TOKEN")
    headers = {"X-API-Key": api_key} if api_key else {}
    headers["X-Flowork-User-ID"] = core_user_id
    headers["X-User-Address"] = core_user_id
    app.logger.info(f"[Gateway Dashboard] Calling Core Engine endpoint: {target_url} with User-ID header: {core_user_id[:10]}...")
    try:
        resp = requests.get(target_url, headers=headers, timeout=5)
        resp.raise_for_status()
        live_data = resp.json()
        app.logger.info(f"[Gateway Dashboard] Successfully fetched live stats from Core Engine {active_engine_id or 'fallback'}. Active jobs: {len(live_data.get('active_jobs', []))}")
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
    """
    (REMASTERED - PERBAIKAN) Generates dashboard summary.
    Fetches ALL stats (live and historical) directly from the user's Core Engine.
    """
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
    app.logger.info(f"[Gateway Dashboard] Returning summary for user {current_user.id}. Active Jobs: {len(summary_data.get('active_jobs',[]))}")
    return jsonify(summary_data)
