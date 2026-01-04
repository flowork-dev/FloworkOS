########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\proxy.py total lines 146 
########################################################################

from flask import Blueprint, request, jsonify, make_response, g, current_app, Response
import requests
import os
from functools import wraps
from ..helpers import crypto_auth_required, find_active_engine_session, get_db_session
from ..extensions import db
from ..globals import globals_instance
from ..models import RegisteredEngine, EngineShare

proxy_bp = Blueprint("proxy", __name__)
DEFAULT_SECRET = "flowork_default_secret_2025"

def handle_cors_options(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key, X-Flowork-User-ID, X-Flowork-Engine-ID, X-Gateway-Secret, X-Signed-Message, X-Signature, X-User-Address, X-Payload-Version, X-Gateway-Token")
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response
        return f(*args, **kwargs)
    return decorated_function

def _resolve_target_engine_url(user, target_engine_id):
    engine_manager = globals_instance.engine_manager
    if target_engine_id in engine_manager.engine_url_map:
        return engine_manager.engine_url_map[target_engine_id], None
    session = get_db_session()
    try:
        engine = session.query(RegisteredEngine).filter_by(id=target_engine_id).first()
        if engine and (engine.user_id == user.id or session.query(EngineShare).filter_by(engine_id=target_engine_id, user_id=user.id).first()):
            return "http://flowork_core:8989", None
        return None, "Permission denied or Engine invalid."
    except Exception as e:
        return None, f"DB Error: {str(e)}"
    finally: session.close()

def _proxy_generic_request(subpath):
    try:
        current_user = g.user if hasattr(g, 'user') else None
        target_engine_id = request.headers.get("X-Flowork-Engine-ID")
        core_server_url = None
        if target_engine_id and current_user:
            url, error = _resolve_target_engine_url(current_user, target_engine_id)
            if not error: core_server_url = url
        if not core_server_url: core_server_url = "http://flowork_core:8989"

        target_url = f"{core_server_url}/api/v1/{subpath}"
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["connection", "keep-alive", "host", "content-length"]}
        headers["X-API-Key"] = os.getenv("GATEWAY_SECRET_TOKEN", DEFAULT_SECRET)
        if current_user: headers["X-Flowork-User-ID"] = str(current_user.id)

        proxied_data = request.stream if (request.content_length and request.content_length > 0) else request.get_data()
        resp = requests.request(method=request.method, url=target_url, headers=headers, data=proxied_data, stream=True, params=request.args, timeout=300)

        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        response_headers = [(n, v) for n, v in resp.raw.headers.items() if n.lower() not in excluded_headers]
        if not any(h[0].lower() == 'access-control-allow-origin' for h in response_headers):
            response_headers.append(('Access-Control-Allow-Origin', request.headers.get('Origin', '*')))
            response_headers.append(('Access-Control-Allow-Credentials', 'true'))
        return Response(resp.iter_content(chunk_size=4096), status=resp.status_code, headers=response_headers)
    except Exception as e:
        return jsonify({"error": "Proxy Error", "details": str(e)}), 500

@proxy_bp.route("/api/v1/apps", methods=["GET", "POST", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_apps(): return _proxy_generic_request("apps")

@proxy_bp.route("/api/v1/apps/execute/<path:subpath>", methods=["POST", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_apps_execute(subpath):
    return _proxy_generic_request(f"apps/execute/{subpath}")

@proxy_bp.route("/api/v1/modules", methods=["GET", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_modules(): return _proxy_generic_request("modules")

@proxy_bp.route("/api/v1/plugins", methods=["GET", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_plugins(): return _proxy_generic_request("plugins")

@proxy_bp.route("/api/v1/widgets", methods=["GET", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_widgets(): return _proxy_generic_request("widgets")

@proxy_bp.route("/api/v1/widgets/<path:subpath>", methods=["GET", "OPTIONS"])
@handle_cors_options
def proxy_widgets_detail(subpath): return _proxy_generic_request(f"widgets/{subpath}")

@proxy_bp.route("/api/v1/tools", methods=["GET", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_tools(): return _proxy_generic_request("tools")

@proxy_bp.route("/api/v1/triggers", methods=["GET", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_triggers(): return _proxy_generic_request("triggers")

@proxy_bp.route("/api/v1/datasets", methods=["GET", "POST", "OPTIONS"])
@proxy_bp.route("/api/v1/datasets/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_datasets(subpath=None):
    path = "datasets" if subpath is None else f"datasets/{subpath}"
    return _proxy_generic_request(path)

@proxy_bp.route("/api/v1/components/<path:subpath>", methods=["GET", "OPTIONS"])
@handle_cors_options
def proxy_component_assets(subpath): return _proxy_generic_request(f"components/{subpath}")

@proxy_bp.route("/api/v1/components/custom/create", methods=["POST", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_create_custom_component(): return _proxy_generic_request("components/custom/create")

@proxy_bp.route("/api/v1/prompts", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_prompts(): return _proxy_generic_request("prompts")

@proxy_bp.route("/api/v1/user/preferences", methods=["GET", "PUT", "OPTIONS"])
@handle_cors_options
@crypto_auth_required
def proxy_preferences(): return _proxy_generic_request("user/preferences")

@proxy_bp.route("/api/v1/proxy/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@handle_cors_options
def proxy_request(subpath):
    req_secret = request.headers.get('X-Gateway-Secret') or request.headers.get('X-API-Key')
    if req_secret and req_secret == os.environ.get('GATEWAY_SECRET_TOKEN', DEFAULT_SECRET):
        return _proxy_generic_request(subpath)
    return crypto_auth_required(_proxy_generic_request)(subpath)
