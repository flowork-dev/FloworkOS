########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\proxy.py total lines 389 
########################################################################

"""
document : https://flowork.cloud/p-tinjauan-arsitektur-proxypy-papan-sakelar-switchboard-gateway-ke-core-id.html
"""
from flask import Blueprint, request, jsonify, make_response, g, current_app, Response
import requests
import os
from ..helpers import crypto_auth_required, find_active_engine_session, get_db_session
from ..extensions import db
from ..globals import globals_instance
from ..models import RegisteredEngine, EngineShare

proxy_bp = Blueprint("proxy", __name__)

DEFAULT_SECRET = "flowork_default_secret_2025"

def _resolve_target_engine_url(user, target_engine_id):
    engine_manager = globals_instance.engine_manager

    if target_engine_id in engine_manager.engine_url_map:
        return engine_manager.engine_url_map[target_engine_id], None

    session = get_db_session()
    try:
        engine = session.query(RegisteredEngine).filter_by(id=target_engine_id).first()
        is_owner = engine and engine.user_id == user.id

        is_shared = False
        if not is_owner:
             share = session.query(EngineShare).filter_by(engine_id=target_engine_id, user_id=user.id).first()
             is_shared = bool(share)

        if is_owner or is_shared:
            fallback_url = "http://flowork_core:8989"
            current_app.logger.warning(f"[Proxy] ID {target_engine_id} not in RAM. Using DB Fallback -> {fallback_url}")
            return fallback_url, None

        return None, f"Permission denied or Engine '{target_engine_id}' invalid (Checked DB)."
    except Exception as e:
        current_app.logger.error(f"[Proxy] DB Error: {str(e)}")
        return None, "Internal Gateway DB Error"
    finally:
        session.close()

def _proxy_generic_request(subpath):
    """
    Generic Proxy Function with Enhanced Error Handling & Streaming Support
    """
    try:
        current_user = g.user

        target_engine_id = request.headers.get("X-Flowork-Engine-ID")

        if target_engine_id and len(target_engine_id) < 20:
            current_app.logger.warning(f"[Proxy] Ignoring likely invalid Engine ID header: {target_engine_id}")
            target_engine_id = None

        core_server_url = None

        if target_engine_id:
            url, error = _resolve_target_engine_url(current_user, target_engine_id)

            if error:
                current_app.logger.warning(f"[Proxy] Resolution failed for {target_engine_id}: {error}")
            else:
                core_server_url = url

        if not core_server_url:
            active_session = find_active_engine_session(db.session, current_user.id)
            if active_session and active_session.engine:
                 active_id = active_session.engine.id
                 url, err = _resolve_target_engine_url(current_user, active_id)
                 if url:
                     core_server_url = url
                     current_app.logger.info(f"[Proxy] Auto-routed to active engine: {active_id} -> {url}")

        if not core_server_url:
            return (
                jsonify({
                    "error": "No active Core Engine found.",
                    "details": "Please ensure your engine is running and listed in 'My Engines'."
                }),
                503,
            )

        target_url = f"{core_server_url}/api/v1/{subpath}"

        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]}
        api_key = os.getenv("GATEWAY_SECRET_TOKEN", DEFAULT_SECRET)
        headers["X-API-Key"] = api_key

        if current_user:
            headers["X-Flowork-User-ID"] = str(current_user.id)

        current_app.logger.debug(f"[Proxy] Forwarding to {target_url}")

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True, # Streaming ON
            params=request.args,
            timeout=300
        )

        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        response_headers = [(n, v) for n, v in resp.raw.headers.items() if n.lower() not in excluded_headers]

        return Response(
            resp.iter_content(chunk_size=2048),
            status=resp.status_code,
            headers=response_headers
        )

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"[Proxy] Connection Failed: {str(e)}")
        return jsonify({"error": "Failed to reach Core Engine.", "details": str(e)}), 503
    except Exception as e:
        current_app.logger.exception(f"[Proxy] Unexpected Error: {str(e)}")
        return jsonify({"error": "Gateway Proxy Error", "details": str(e)}), 500


@proxy_bp.route("/api/v1/presets", methods=["GET", "POST"])
@crypto_auth_required
def proxy_presets():
    return _proxy_generic_request("presets")

@proxy_bp.route("/api/v1/presets/<path:subpath>", methods=["GET", "DELETE"])
@crypto_auth_required
def proxy_presets_detail(subpath):
    return _proxy_generic_request(f"presets/{subpath}")

@proxy_bp.route("/api/v1/prompts", methods=["GET", "POST"])
@crypto_auth_required
def proxy_prompts():
    return _proxy_generic_request("prompts")

@proxy_bp.route("/api/v1/prompts/<path:subpath>", methods=["GET", "PUT", "DELETE"])
@crypto_auth_required
def proxy_prompts_detail(subpath):
    return _proxy_generic_request(f"prompts/{subpath}")

@proxy_bp.route("/api/v1/variables", methods=["GET", "POST"])
@crypto_auth_required
def proxy_variables():
    return _proxy_generic_request("variables")

@proxy_bp.route("/api/v1/variables/<path:subpath>", methods=["GET", "PUT", "PATCH", "DELETE"])
@crypto_auth_required
def proxy_variables_detail(subpath):
    return _proxy_generic_request(f"variables/{subpath}")

@proxy_bp.route("/api/v1/settings", methods=["GET", "PATCH"])
@crypto_auth_required
def proxy_settings():
    return _proxy_generic_request("settings")

@proxy_bp.route("/api/v1/user/<path:subpath>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@crypto_auth_required
def proxy_user_routes(subpath):
    return _proxy_generic_request(f"user/{subpath}")


@proxy_bp.route("/api/v1/modules", methods=["GET"])
@crypto_auth_required
def proxy_modules():
    return _proxy_generic_request("modules")

@proxy_bp.route("/api/v1/plugins", methods=["GET"])
@crypto_auth_required
def proxy_plugins():
    return _proxy_generic_request("plugins")

@proxy_bp.route("/api/v1/widgets", methods=["GET"])
@crypto_auth_required
def proxy_widgets():
    return _proxy_generic_request("widgets")

@proxy_bp.route("/api/v1/tools", methods=["GET"])
@crypto_auth_required
def proxy_tools():
    return _proxy_generic_request("tools")

@proxy_bp.route("/api/v1/triggers", methods=["GET"])
@crypto_auth_required
def proxy_triggers():
    return _proxy_generic_request("triggers")


@proxy_bp.route("/api/v1/system-data/components/<component_type>", methods=["GET"])
def proxy_component_list(component_type):
    if component_type not in ["modules", "plugins", "tools", "triggers"]:
        return jsonify({"error": "Invalid component type"}), 400
    core_server_url = globals_instance.engine_manager.get_next_core_server()
    if not core_server_url:
        return (
            jsonify(
                {
                    "error": "No healthy or active Core Engine available to serve component list.",
                    "details": "Please ensure at least one Core Engine is running and connected to the Gateway.",
                }
            ),
            503,
        )
    target_url = f"{core_server_url}/api/v1/{component_type}"

    api_key = os.getenv("GATEWAY_SECRET_TOKEN", DEFAULT_SECRET)
    headers = {"X-API-Key": api_key}

    try:
        resp = requests.get(
            target_url, headers=headers, timeout=10, params=request.args
        )
        resp.raise_for_status()
        response = make_response(resp.content, resp.status_code)
        for h, v in resp.headers.items():
            if h.lower() not in ["content-encoding", "transfer-encoding", "connection"]:
                response.headers[h] = v
        return response
    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {
                    "error": "Gateway could not reach Core Server for component list.",
                    "details": str(e),
                }
            ),
            503,
        )
@proxy_bp.route("/api/v1/health", methods=["GET"])
def proxy_health_check():
    core_server_url = globals_instance.engine_manager.get_next_core_server()
    if not core_server_url:
        return jsonify({"error": "No healthy Core Servers available"}), 503
    target_url = f"{core_server_url}/health"
    headers = {
        k: v
        for k, v in request.headers
        if k.lower() not in ["host", "authorization", "cookie"]
    }

    api_key = os.getenv("GATEWAY_SECRET_TOKEN", DEFAULT_SECRET)
    headers["X-API-Key"] = api_key

    try:
        resp = requests.get(target_url, headers=headers, timeout=5)
        response = make_response(resp.content, resp.status_code)
        for h, v in resp.headers.items():
            if h.lower() not in ["content-encoding", "transfer-encoding", "connection"]:
                response.headers[h] = v
        return response
    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {
                    "error": "Gateway could not reach Core Server for health check.",
                    "details": str(e),
                }
            ),
            503,
        )
@proxy_bp.route("/api/v1/news", methods=["GET"])
def proxy_news_request():
    core_server_url = globals_instance.engine_manager.get_next_core_server()
    if not core_server_url:
        return jsonify({"error": "No healthy Core Servers available"}), 503
    target_url = f"{core_server_url}/api/v1/news"
    headers = {
        k: v
        for k, v in request.headers
        if k.lower() not in ["host", "authorization", "cookie"]
    }

    api_key = os.getenv("GATEWAY_SECRET_TOKEN", DEFAULT_SECRET)
    headers["X-API-Key"] = api_key

    try:
        resp = requests.get(
            target_url, headers=headers, params=request.args, timeout=15
        )
        excluded_headers = [
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        ]
        response_headers = [
            (n, v)
            for n, v in resp.raw.headers.items()
            if n.lower() not in excluded_headers
        ]
        return make_response(resp.content, resp.status_code, response_headers)
    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {
                    "error": "Gateway could not reach Core Server for news.",
                    "details": str(e),
                }
            ),
            503,
        )
@proxy_bp.route("/api/v1/localization/<lang_code>", methods=["GET"])
def proxy_localization_request(lang_code):
    core_server_url = globals_instance.engine_manager.get_next_core_server()
    if not core_server_url:
        return jsonify({"error": "No healthy Core Servers available"}), 503
    target_url = f"{core_server_url}/api/v1/localization/{lang_code}"
    headers = {
        k: v
        for k, v in request.headers
        if k.lower() not in ["host", "authorization", "cookie"]
    }

    api_key = os.getenv("GATEWAY_SECRET_TOKEN", DEFAULT_SECRET)
    headers["X-API-Key"] = api_key

    try:
        resp = requests.get(
            target_url, headers=headers, params=request.args, timeout=15
        )
        excluded_headers = [
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        ]
        response_headers = [
            (n, v)
            for n, v in resp.raw.headers.items()
            if n.lower() not in excluded_headers
        ]
        return make_response(resp.content, resp.status_code, response_headers)
    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {"error": "Gateway could not reach Core Server.", "details": str(e)}
            ),
            503,
        )
@proxy_bp.route("/api/v1/components/<path:subpath>", methods=["GET"])
def proxy_component_assets(subpath):
    core_server_url = globals_instance.engine_manager.get_next_core_server()
    if not core_server_url:
        return jsonify({"error": "No healthy Core Servers available"}), 503
    target_url = f"{core_server_url}/api/v1/components/{subpath}"

    api_key = os.getenv("GATEWAY_SECRET_TOKEN", DEFAULT_SECRET)
    headers = {"X-API-Key": api_key}

    try:
        resp = requests.get(
            target_url, headers=headers, stream=True, timeout=10, params=request.args
        )
        excluded_headers = [
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        ]
        headers = [
            (name, value)
            for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers
        ]
        response = make_response(resp.content, resp.status_code)
        for name, value in headers:
            response.headers[name] = value
        return response
    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {"error": "Gateway could not reach Core Server.", "details": str(e)}
            ),
            503,
        )

@proxy_bp.route("/api/v1/proxy/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@crypto_auth_required
def proxy_request(subpath):
    return _proxy_generic_request(subpath)
