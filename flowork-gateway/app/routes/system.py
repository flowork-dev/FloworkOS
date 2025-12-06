########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\system.py total lines 210 
########################################################################

import os
import shutil
import glob
from flask import Blueprint, jsonify, current_app, request
from ..helpers import engine_auth_required, admin_token_required
from ..models import GloballyDisabledComponent, Capability, Plan, Job, ExecutionMetric, AuditLog, ScheduledTask, Episode, AgentSession
from ..extensions import db
from app.engine.registry import list_up_engines

system_bp = Blueprint("system", __name__, url_prefix="/api/v1/system")

@system_bp.route("/health", methods=["GET"])
def health_check():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        current_app.logger.error(f"[Gateway Health] Health check failed: {e}")
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 503

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
    except Exception as e:
        current_app.logger.error(f"[Gateway System Route] Failed to fetch public engines: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch engine status from Gateway.", "engines": []}), 500

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
        return jsonify({"error": "Failed to fetch system configuration."}), 500

@system_bp.route("/capabilities", methods=["GET"])
@admin_token_required
def get_all_capabilities(**kwargs):
    try:
        capabilities = Capability.query.order_by(Capability.id).all()
        return jsonify([{"id": c.id, "description": c.description} for c in capabilities])
    except Exception as e:
        current_app.logger.error(f"[Gateway System Route] Failed to fetch capabilities: {e}")
        return jsonify({"error": "Failed to fetch capabilities."}), 500

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
        current_app.logger.info(f"[Gateway System Route] Capabilities for plan '{plan_id}' updated. (Cache invalidation skipped - No Redis)")
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
    """
    Purge system cache (logs, temp files, TRAINING JUNK) and database history.
    PRESERVES: The main training output folder (except intermediate checkpoints).
    """
    stats = {
        "files_deleted": 0,
        "folders_deleted": 0,
        "db_rows_deleted": 0,
        "errors": []
    }

    root_dirs = ["/app", "."]

    extensions_to_nuke = [
        "*.ass", "*.srt", "*.log", "concat_*.txt", "temp_vis_*.mp4", "sub_*.ass",
        "events.out.tfevents.*", # Tensorboard logs (Training Junk)
        "*.lock" # Lock files
    ]

    cache_folders = [
        "flowork_kernel/data/logs/factory_cache",
        "data/logs/factory_cache",
        "flowork_kernel/data/training_logs", # Training Logs
        "__pycache__",
        "wandb", # Weights and Biases Temp
        "runs", # Common training runs folder
        "flowork-core/unsloth_compiled_cache", # [NEW] Unsloth Cache (Deleted as requested)
        "flowork-core/llama.cpp" # [NEW] Llama.cpp folder (Deleted as requested)
    ]

    current_app.logger.info("🚀 STARTING MASSIVE HARD CLEANUP (PRESERVING MODELS)...")

    for root_search in root_dirs:
        for ext in extensions_to_nuke:
            for filepath in glob.iglob(os.path.join(root_search, '**', ext), recursive=True):
                try:
                    if "adapters" in filepath or "merged" in filepath:
                        continue

                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        stats["files_deleted"] += 1
                except Exception as e:
                    pass

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
        for root_search in root_dirs:
            for root, dirs, files in os.walk(root_search):
                for d in dirs:
                    if d.startswith("checkpoint-") and d[11:].isdigit():
                        checkpoint_path = os.path.join(root, d)
                        try:
                            current_app.logger.info(f"Removing intermediate checkpoint: {checkpoint_path}")
                            shutil.rmtree(checkpoint_path)
                            stats["folders_deleted"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Checkpoint {d}: {str(e)}")
    except Exception as e:
        stats["errors"].append(f"Checkpoint Scan Error: {str(e)}")

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
        stats["errors"].append(f"Database Error: {str(e)}")

    current_app.logger.info(f"✅ HARD CLEANUP FINISHED: {stats}")

    return jsonify({
        "message": "System cleanup executed successfully. Intermediate checkpoints, unsloth cache & logs purged.",
        "stats": stats
    })
