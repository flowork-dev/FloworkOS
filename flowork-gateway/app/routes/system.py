########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\system.py total lines 314 
########################################################################

import os
import shutil
import glob
import time
import uuid
import logging
from flask import Blueprint, jsonify, current_app, request
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from ..helpers import engine_auth_required, admin_token_required
from ..models import GloballyDisabledComponent, Capability, Plan, Job, ExecutionMetric, AuditLog, ScheduledTask, Episode, AgentSession
from ..extensions import db, socketio

try:
    from app.engine.registry import list_up_engines
except ImportError:
    list_up_engines = lambda: {}

system_bp = Blueprint("system", __name__, url_prefix="/api/v1/system")

def attempt_db_recovery():
    """
    Emergency DB Healer.
    Dipanggil saat ada indikasi tabel hilang (OperationalError).
    Mencoba membuat ulang semua tabel database secara otomatis.
    """
    try:
        current_app.logger.warning("🚑 [System] DB Integrity Check Failed. Attempting to create tables...")
        with current_app.app_context():
            db.create_all()
            db.session.commit()
        current_app.logger.info("✅ [System] Database tables recreated successfully.")
        return True
    except Exception as e:
        current_app.logger.error(f"❌ [System] DB Recovery Failed: {e}")
        return False

def find_active_engine_sid():
    """
    Mencari Engine SID aktif secara brutal lewat internal SocketIO memory.
    Bypass database sepenuhnya dan tahan banting terhadap struktur data SocketIO.
    """
    try:
        mgr = socketio.server.manager
        ns = '/engine-socket'

        rooms_data = getattr(mgr, 'rooms', {})

        if ns in rooms_data:
            ns_rooms = rooms_data[ns]
            if ns_rooms:
                for room_name in list(ns_rooms.keys()):
                    if room_name and isinstance(room_name, str) and room_name.startswith('eng-'):
                        current_app.logger.info(f"🔎 [System] Found Engine Room via Socket: {room_name}")
                        return room_name

                if ns_rooms:
                     first_key = list(ns_rooms.keys())[0]
                     return str(first_key)

        if hasattr(mgr, 'get_participants'):
            parts = list(mgr.get_participants(ns, None))
            if parts:
                 return str(parts[0])

    except Exception as e:
        current_app.logger.error(f"⚠️ [System] Socket discovery failed: {e}")

    return None

@system_bp.route("/health", methods=["GET"])
def health_check():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "degraded", "database": "disconnected", "error": str(e)}), 200

@system_bp.route("/public-engines", methods=["GET"])
def get_public_engines():
    try:
        engine_dict = list_up_engines()
        engine_list = []
        for eid, data in engine_dict.items():
            engine_list.append({
                "engine_id": eid,
                "weight": data.get("weight", 1.0),
                "capacity": data.get("capacity", 8),
                "status": "up"
            })
        return jsonify({"engines": engine_list})
    except OperationalError:
        attempt_db_recovery()
        return jsonify({"engines": [], "warning": "Database recovering"}), 200
    except Exception:
        return jsonify({"engines": []}), 200

@system_bp.route('/browse', methods=['POST'])
def system_browse():
    """
    Endpoint Browse yang tahan banting (Robust).
    Menggunakan prioritas: Engine ID dari Request -> DB Registry -> Socket Bypass.
    """
    data = request.get_json(silent=True) or {}
    target_path = data.get('path', '')
    engine_id = data.get('engine_id')

    if not engine_id:
        try:
            active = list_up_engines()
            if active:
                engine_id = list(active.keys())[0]
        except OperationalError:
            attempt_db_recovery()
        except Exception:
            pass

        if not engine_id:
            engine_id = find_active_engine_sid()

    if not engine_id:
        return jsonify({
            "error": "No active engine found. Please ensure Flowork Core is running.",
            "data": []
        }), 200

    req_id = str(uuid.uuid4())
    payload = {
        "request_id": req_id,
        "path": target_path,
        "type": "system:browse"
    }

    current_app.logger.info(f"📂 [System] Browsing '{target_path}' on Engine {engine_id}...")

    response_container = {"data": None}

    def ack_callback(response):
        response_container["data"] = response

    try:
        socketio.emit(
            'system:browse',
            payload,
            namespace='/engine-socket',
            to=engine_id,
            callback=ack_callback
        )

        start = time.time()
        while response_container["data"] is None and (time.time() - start) < 10:
            socketio.sleep(0.1)

        result = response_container["data"]

        if result:
            if result.get("error"):
                return jsonify({"error": result["error"]}), 400

            return jsonify(result.get("data", [])), 200
        else:
            return jsonify({"error": "Engine request timed out (Core busy?)"}), 504

    except Exception as e:
        current_app.logger.error(f"🔥 [System] Browse Critical Error: {e}")
        return jsonify({"error": str(e)}), 500

@system_bp.route("/disabled-components", methods=["GET"])
@engine_auth_required
def get_disabled_components():
    try:
        disabled_components = GloballyDisabledComponent.query.all()
        disabled_ids = [c.component_id for c in disabled_components]
        return jsonify(disabled_ids)
    except Exception as e:
        current_app.logger.error(
            f"[Gateway System Route] Failed to fetch disabled components: {e}"
        )
        return jsonify([]), 200

@system_bp.route("/capabilities", methods=["GET"])
@admin_token_required
def get_all_capabilities(**kwargs):
    try:
        capabilities = Capability.query.order_by(Capability.id).all()
        return jsonify([{"id": c.id, "description": c.description} for c in capabilities])
    except Exception as e:
        current_app.logger.error(f"[Gateway System Route] Failed to fetch capabilities: {e}")
        return jsonify([]), 200

@system_bp.route("/plans/<plan_id>/capabilities", methods=["PUT"])
@admin_token_required
def update_plan_capabilities(plan_id, **kwargs):
    if 'admin_permissions' in kwargs and 'plan:update' not in kwargs['admin_permissions']:
        return jsonify({"error": "Admin permission 'plan:update' required."}), 403
    data = request.get_json()
    if data is None or 'capability_ids' not in data:
        return jsonify({"error": "Missing 'capability_ids' in request body."}), 400
    plan = Plan.query.options(db.joinedload(Plan.capabilities)).filter_by(id=plan_id).first()
    if not plan:
        return jsonify({"error": "Plan not found."}), 404
    try:
        new_capability_ids = set(data.get('capability_ids', []))
        plan.capabilities = [cap for cap in plan.capabilities if cap.id in new_capability_ids]
        current_cap_ids = {cap.id for cap in plan.capabilities}
        caps_to_add = new_capability_ids - current_cap_ids
        if caps_to_add:
            new_caps = Capability.query.filter(Capability.id.in_(caps_to_add)).all()
            for cap in new_caps:
                plan.capabilities.append(cap)
        db.session.commit()
        db.session.refresh(plan)
        plan_data = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "is_public": plan.is_public,
            "max_executions": plan.max_executions,
            "features": plan.features,
            "capabilities": [{"id": c.id, "description": c.description} for c in plan.capabilities],
            "prices": [{"duration_months": p.duration_months, "price": float(p.price)} for p in plan.prices]
        }
        return jsonify(plan_data)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Gateway System Route] Failed to update plan capabilities: {e}")
        return jsonify({"error": "Failed to update plan capabilities."}), 500

@system_bp.route("/clear-cache", methods=["POST"])
def clear_system_cache():
    stats = {
        "files_deleted": 0,
        "folders_deleted": 0,
        "db_rows_deleted": 0,
        "errors": []
    }

    root_dirs = ["/app", "."]

    extensions_to_nuke = [
        "*.ass", "*.srt", "*.log", "concat_*.txt", "temp_vis_*.mp4", "sub_*.ass",
        "events.out.tfevents.*",
        "*.lock"
    ]

    cache_folders = [
        "flowork_kernel/data/logs/factory_cache",
        "data/logs/factory_cache",
        "flowork_kernel/data/training_logs",
        "__pycache__",
        "wandb",
        "runs",
        "flowork-core/unsloth_compiled_cache",
        "flowork-core/llama.cpp"
    ]

    current_app.logger.info("🚀 STARTING MASSIVE HARD CLEANUP...")

    for root_search in root_dirs:
        for ext in extensions_to_nuke:
            for filepath in glob.iglob(os.path.join(root_search, '**', ext), recursive=True):
                try:
                    if "adapters" in filepath or "merged" in filepath:
                        continue
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        stats["files_deleted"] += 1
                except Exception: pass

    for folder in cache_folders:
        for root_search in root_dirs:
            target_path = os.path.join(root_search, folder)
            if folder == "__pycache__":
                for root, dirs, files in os.walk(root_search):
                    for d in dirs:
                        if d == "__pycache__":
                            try:
                                shutil.rmtree(os.path.join(root, d))
                                stats["folders_deleted"] += 1
                            except: pass
            else:
                if os.path.exists(target_path):
                    try:
                        shutil.rmtree(target_path)
                        stats["folders_deleted"] += 1
                        if "logs" in target_path:
                            os.makedirs(target_path, exist_ok=True)
                    except Exception as e:
                        stats["errors"].append(f"Folder {target_path}: {str(e)}")

    try:
        num_jobs = db.session.query(Job).delete()
        num_metrics = db.session.query(ExecutionMetric).delete()
        num_logs = db.session.query(AuditLog).delete()
        num_episodes = db.session.query(Episode).delete()
        num_sessions = db.session.query(AgentSession).delete()
        num_tasks = db.session.query(ScheduledTask).filter(ScheduledTask.status.in_(['completed', 'failed'])).delete()

        db.session.commit()
        stats["db_rows_deleted"] = num_jobs + num_metrics + num_logs + num_tasks + num_episodes + num_sessions

    except Exception as e:
        db.session.rollback()
        stats["errors"].append(f"Database Error (Ignored): {str(e)}")

    return jsonify({
        "message": "System cleanup executed successfully.",
        "stats": stats
    })
