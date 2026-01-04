########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\variables.py total lines 109 
########################################################################

from flask import Blueprint, request, jsonify, current_app
import requests
import json
from app.security.guards import login_required

variables_bp = Blueprint('variables', __name__)

CORE_URL = "http://flowork_core:8989/api/v1/variables"

@variables_bp.route('', methods=['GET', 'POST', 'PUT'], strict_slashes=False)
@login_required
def handle_root_variables(user):
    """
    Handle operasi pada root /variables (List semua atau Create baru)
    """
    try:
        if request.method == 'GET':
            current_app.logger.info(f"[Variables-Spy] 🔍 LIST request from {user.get('id')}")
            headers = {"x-user-id": user.get('id', 'anon')}
            resp = requests.get(CORE_URL, headers=headers)
            return (jsonify(resp.json()), resp.status_code) if resp.status_code < 400 else (jsonify({"error": "Core error"}), resp.status_code)

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload"}), 400

        key = data.get('key')
        value = data.get('value')

        if key and request.method == 'POST':
            current_app.logger.info(f"[Variables-Spy] 💾 CREATE Legacy POST for key: {key}")
            payload = {
                "value": value,
                "is_enabled": True,
                "is_secret": False,
                "mode": "single",
                "description": data.get('description', 'Saved via Gateway')
            }
            headers = {"x-user-id": user.get('id', 'anon')}
            resp = requests.put(f"{CORE_URL}/{key}", json=payload, headers=headers)
            return (jsonify(resp.json()), resp.status_code)

        return jsonify({"error": "Invalid payload or method"}), 400

    except Exception as e:
        current_app.logger.error(f"[Variables] Root handler error: {e}")
        return jsonify({"error": str(e)}), 500


@variables_bp.route('/<path:key>', methods=['GET', 'PUT', 'DELETE'], strict_slashes=False)
@login_required
def handle_variable_key(user, key):
    """
    [AWENK-FIX] Single Handler untuk GET, PUT, DELETE pada Key spesifik.
    Menggunakan Direct Call ke Core yang sudah di-upgrade.
    """
    headers = {"x-user-id": user.get('id', 'anon')}

    try:
        if request.method == 'GET':
            current_app.logger.info(f"[Variables-Spy] 📥 GET request for key: {key}")

            resp = requests.get(f"{CORE_URL}/{key}", headers=headers)

            if resp.status_code == 200:
                current_app.logger.info(f"[Variables-Spy] ✅ Core returned data for '{key}'")
                return jsonify(resp.json()), 200

            if resp.status_code == 404:
                current_app.logger.warning(f"[Variables-Spy] ⚠️ Core said 404 for '{key}'. Sending empty container.")
                return jsonify({"value": None, "status": "not_found"}), 200

            return jsonify({"error": "Core error"}), resp.status_code

        if request.method == 'PUT':
            current_app.logger.info(f"[Variables-Spy] 💾 PUT/SAVE request for key: {key}")
            data = request.get_json()

            payload = {
                "value": data.get('value'),
                "is_enabled": data.get('is_enabled', True),
                "is_secret": data.get('is_secret', False),
                "mode": "single",
                "description": data.get('description', 'Updated via Gateway')
            }

            resp = requests.put(f"{CORE_URL}/{key}", json=payload, headers=headers)

            if resp.status_code < 400:
                current_app.logger.info(f"[Variables-Spy] ✅ Core accepted save for '{key}'")
                return jsonify(resp.json()), resp.status_code
            else:
                current_app.logger.error(f"[Variables-Spy] ❌ Core rejected save: {resp.text}")
                return jsonify({"error": "Core rejected save", "details": resp.text}), resp.status_code

        if request.method == 'DELETE':
            current_app.logger.info(f"[Variables-Spy] 🗑️ DELETE request for key: {key}")
            resp = requests.delete(f"{CORE_URL}/{key}", headers=headers)
            return jsonify({"status": "deleted"}), resp.status_code

    except Exception as e:
        current_app.logger.error(f"[Variables] Key handler error: {e}")
        return jsonify({"error": str(e)}), 500
