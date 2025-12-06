########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\ai_proxy.py total lines 189 
########################################################################

from flask import Blueprint, request, jsonify, Response, stream_with_context, make_response
import requests
import os
import logging
import json

ai_proxy_bp = Blueprint('ai_proxy', __name__)

def get_logger():
    try:
        from app.json_logging import logger
        return logger
    except ImportError:
        return logging.getLogger(__name__)

def get_crypto_auth():
    try:
        from app.helpers import crypto_auth_required
        return crypto_auth_required
    except ImportError:
        return lambda x: x

def resolve_core_url(engine_id):
    try:
        from app.engine.registry import get_engine_url
        if engine_id and len(engine_id) > 5:
            url = get_engine_url(engine_id)
            if url:
                return url
    except ImportError:
        pass
    return os.getenv("CORE_URL", "http://flowork_core:8989")

def stream_with_padding(resp, is_council=False):
    """
    Generator ini mengirimkan padding di awal.
    Untuk Mode Council, kita kirim 'heartbeat' spasi kosong setiap beberapa detik
    jika core sedang mikir keras, biar Cloudflare gak mutus koneksi (Error 524).
    """
    yield b' ' * 2048
    yield b'\n'

    log = get_logger()
    try:
        for chunk in resp.iter_content(chunk_size=1024):
            if chunk:
                yield chunk

    except Exception as e:
        log.error(f"[Streaming Error] {e}")
        yield f'\n[Gateway Error: {str(e)}]'.encode('utf-8')

def _add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'

    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = (
        'Content-Type, Authorization, X-API-Key, X-Flowork-User-ID, '
        'X-Flowork-Engine-ID, X-Gateway-Secret, x-signed-message, '
        'x-signature, x-user-address, x-payload-version, x-gateway-token'
    )
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, PATCH, DELETE'
    return response

@ai_proxy_bp.route('/<path:subpath>', methods=['OPTIONS'])
def handle_ai_options(subpath):
    resp = make_response()
    return _add_cors_headers(resp)

@ai_proxy_bp.route('/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def ai_center_gateway_entry(subpath):
    auth_decorator = get_crypto_auth()

    @auth_decorator
    def actual_handler(subpath):
        return _handle_proxy_request(subpath)

    return actual_handler(subpath)

def _handle_proxy_request(subpath):
    log = get_logger()

    engine_id = request.headers.get('X-Flowork-Engine-ID')
    if not engine_id:
        engine_id = request.args.get('engine_id')

    is_council = False
    request_timeout = 600 # Default 10 mins

    req_data = request.get_data()

    try:
        if request.method == 'POST' and request.is_json:
            json_body = request.get_json(silent=True)
            if json_body:
                payload = json_body.get('payload', {})
                if json_body.get('is_council') or (isinstance(payload, dict) and payload.get('is_council')):
                    is_council = True
                    request_timeout = 1200 # 20 Mins for Council Debate
                    log.info("[AI Proxy] Neural Council Mode Detected! Extending timeout to 1200s.")
    except Exception as e:
        log.warning(f"[AI Proxy] Failed to parse JSON for timeout detection: {e}")

    core_base = resolve_core_url(engine_id)
    if core_base.endswith('/'):
        core_base = core_base[:-1]

    target_url = f"{core_base}/api/v1/ai/{subpath}"

    if 'files/view' in subpath:
        log.info(f"[AI Proxy] Serving File from {target_url} | Engine: {engine_id}")
    else:
        log.info(f"[AI Proxy] Routing to {target_url} | Engine: {engine_id or 'Default'} | Council: {is_council}")

    headers = {key: value for (key, value) in request.headers if key.lower() not in ['host', 'content-length']}
    headers["X-API-Key"] = os.environ.get("GATEWAY_SECRET_TOKEN", "flowork_default_secret_2025")

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=req_data, # Use cached data
            cookies=request.cookies,
            allow_redirects=False,
            stream=True,
            params=request.args,
            timeout=request_timeout
        )

        excluded_headers = [
            'content-encoding', 'content-length',
            'transfer-encoding', 'connection', 'keep-alive',
            'access-control-allow-origin', 'access-control-allow-credentials'
        ]
        headers_back = [
            (name, value) for (name, value) in resp.headers.items()
            if name.lower() not in excluded_headers
        ]

        content_type = resp.headers.get('Content-Type', '')
        is_media_file = any(t in content_type for t in ['image/', 'video/', 'audio/', 'application/pdf', 'application/octet-stream'])

        if is_media_file:
            response = Response(
                stream_with_context(resp.iter_content(chunk_size=4096)),
                status=resp.status_code,
                headers=headers_back
            )
            response.headers['X-Accel-Buffering'] = 'no'
        else:
            response = Response(
                stream_with_context(stream_with_padding(resp, is_council)),
                status=resp.status_code,
                headers=headers_back
            )
            response.headers['X-Accel-Buffering'] = 'no'
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'

        return _add_cors_headers(response)

    except requests.exceptions.ReadTimeout:
        log.error(f"[AI Proxy] TIMEOUT waiting for Core at {target_url}.")
        err_resp = jsonify({"status": "error", "message": "AI Engine Timeout. The Council is taking too long to deliberate."})
        err_resp.status_code = 504
        return _add_cors_headers(err_resp)

    except requests.exceptions.ConnectionError:
        log.error(f"[AI Proxy] Connection REFUSED to Core.")
        err_resp = jsonify({"status": "error", "message": "AI Core Unreachable."})
        err_resp.status_code = 503
        return _add_cors_headers(err_resp)

    except Exception as e:
        log.error(f"[AI Proxy] Unexpected error: {str(e)}")
        err_resp = jsonify({"status": "error", "message": str(e)})
        err_resp.status_code = 500
        return _add_cors_headers(err_resp)
