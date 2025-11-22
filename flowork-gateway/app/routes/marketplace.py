########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\marketplace.py total lines 148 
########################################################################

from flask import Blueprint, jsonify, request, g, current_app
from app.extensions import db
from app.helpers import crypto_auth_required
from app.models import MarketplaceSubmission, User
import uuid
import time
import json
import os
import datetime
import urllib.request
import urllib.error

marketplace_bp = Blueprint('marketplace_bp', __name__)

MARKETPLACE_STORAGE_DIR = "/app/data/marketplace_storage"
os.makedirs(MARKETPLACE_STORAGE_DIR, exist_ok=True)

@marketplace_bp.route('/list', methods=['GET'])
def list_items():
    try:
        submissions = MarketplaceSubmission.query.filter_by(status='approved').all()
        output = []
        for item in submissions:
            output.append({
                "id": item.id,
                "type": item.component_type,
                "name": item.component_id,
                "desc": item.admin_notes or "",
                "price": 0,
                "author": item.submitter.public_address if item.submitter else "Unknown",
                "published_at": item.submitted_at.timestamp() if item.submitted_at else 0,
            })
        return jsonify(output), 200
    except Exception as e:
        current_app.logger.error(f"[Marketplace] List failed: {e}")
        return jsonify([]), 200

@marketplace_bp.route('/publish', methods=['POST'])
@crypto_auth_required
def publish_item():
    try:
        data = request.get_json()
        user = g.user

        if not data or not data.get('name') or not data.get('data'):
            return jsonify({"error": "Invalid payload. Name and Data are required."}), 400

        item_id = str(uuid.uuid4())

        new_item = MarketplaceSubmission(
            id=item_id,
            submitter_user_id=user.id,
            component_id=data.get('name'),
            component_type=data.get('type', 'preset'),
            version="1.0.0",
            status="approved",
            admin_notes=data.get('desc', ''),
            submitted_at=datetime.datetime.utcnow()
        )

        db.session.add(new_item)
        db.session.commit()

        file_path = os.path.join(MARKETPLACE_STORAGE_DIR, f"{item_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data.get('data'), f, indent=2)

        current_app.logger.info(f"[Marketplace] Published: {data.get('name')} ({item_id})")

        return jsonify({
            "success": True,
            "message": "Published successfully",
            "id": item_id
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Marketplace] Publish failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@marketplace_bp.route('/items/<item_id>', methods=['GET'])
def get_item_detail(item_id):
    try:
        item = MarketplaceSubmission.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404

        workflow_data = {}
        file_path = os.path.join(MARKETPLACE_STORAGE_DIR, f"{item.id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

        response_data = {
            "id": item.id,
            "type": item.component_type,
            "name": item.component_id,
            "desc": item.admin_notes,
            "price": 0,
            "author": item.submitter.public_address if item.submitter else "Unknown",
            "published_at": item.submitted_at.timestamp() if item.submitted_at else 0,
            "data": workflow_data
        }
        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"[Marketplace] Get Detail Failed: {e}")
        return jsonify({"error": str(e)}), 500

@marketplace_bp.route('/component/install', methods=['POST'])
@crypto_auth_required
def install_component_proxy():
    try:
        data = request.get_json()
        current_app.logger.info(f"[Marketplace Proxy] Forwarding install request for: {data.get('id')}")

        CORE_URL = "http://flowork_core:8989/api/v1/components/install-package"

        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(CORE_URL, data=json_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Content-Length', len(json_data))

        with urllib.request.urlopen(req, timeout=60) as response:
            resp_body = response.read()
            return jsonify(json.loads(resp_body)), response.status

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        current_app.logger.error(f"[Marketplace Proxy] Core Error: {error_body}")
        try:
            return jsonify(json.loads(error_body)), e.code
        except:
            return jsonify({"error": "Core returned error", "details": error_body}), e.code

    except urllib.error.URLError as e:
        current_app.logger.error(f"[Marketplace Proxy] Connection Failed: {e.reason}")
        return jsonify({"error": f"Failed to connect to Core: {e.reason}"}), 502

    except Exception as e:
        current_app.logger.error(f"[Marketplace Proxy] Unknown Error: {e}")
        return jsonify({"error": f"Gateway Proxy Error: {str(e)}"}), 500
