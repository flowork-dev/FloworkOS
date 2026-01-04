########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\presets.py total lines 105 
########################################################################

import uuid
import json
import logging
from flask import Blueprint, jsonify, request, current_app
from ..extensions import db
from ..helpers import engine_auth_required

presets_bp = Blueprint("presets", __name__, url_prefix="/api/v1/presets")

@presets_bp.route("/", methods=["GET"])
@engine_auth_required
def get_presets():
    try:
        result = db.session.execute(db.text("SELECT id, name, description, created_at FROM presets ORDER BY created_at DESC")).fetchall()
        preset_list = []
        for row in result:
            preset_list.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": str(row[3])
            })
        return jsonify(preset_list), 200
    except Exception as e:
        current_app.logger.error(f"[Preset] Failed to fetch presets: {e}")
        if "no such table" in str(e):
            return jsonify([]), 200
        return jsonify({"error": str(e)}), 500

@presets_bp.route("/", methods=["POST"])
@engine_auth_required
def create_preset():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "Untitled Preset")
    description = data.get("description", "")
    config = data.get("config", {})

    try:
        preset_id = str(uuid.uuid4())
        config_str = json.dumps(config)

        query = db.text("""
            INSERT INTO presets (id, name, description, config, created_at)
            VALUES (:id, :name, :description, :config, CURRENT_TIMESTAMP)
        """)

        db.session.execute(query, {
            "id": preset_id,
            "name": name,
            "description": description,
            "config": config_str
        })
        db.session.commit()

        return jsonify({"message": "Preset created", "id": preset_id}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Preset] Failed to create preset: {e}")

        if "no such table" in str(e):
            try:
                current_app.logger.info("[Preset] Creating missing 'presets' table...")
                db.session.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS presets (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        config TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
                return jsonify({"error": "System initialized table. Please try saving again."}), 503
            except Exception as create_err:
                current_app.logger.error(f"[Preset] Failed to auto-create table: {create_err}")

        return jsonify({"error": str(e)}), 500

@presets_bp.route("/<preset_id>", methods=["GET"])
def get_preset_detail(preset_id):
    try:
        query = db.text("SELECT id, name, description, config FROM presets WHERE id = :id")
        row = db.session.execute(query, {"id": preset_id}).fetchone()

        if not row:
            return jsonify({"error": "Preset not found"}), 404

        return jsonify({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "config": json.loads(row[3]) if row[3] else {}
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
