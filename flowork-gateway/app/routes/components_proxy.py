########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\flowork-gateway\app\routes\components_proxy.py total lines 67 
########################################################################

import requests
import os
from flask import Blueprint, request, jsonify, current_app
from app.security.guards import gateway_token_required

components_bp = Blueprint('components', __name__)

def get_smart_core_url():
    """
    Detects if we are running in a Docker container or Localhost.
    Prioritizes ENV variable -> Docker Host -> Localhost fallback.
    """
    env_url = os.environ.get('FLOWORK_CORE_URL')
    if env_url:
        return env_url.rstrip('/')

    if os.path.exists('/.dockerenv'):
        return "http://flowork_core:8989"

    return "http://127.0.0.1:8989"

@components_bp.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@gateway_token_required
def proxy_components(path):
    """
    [HYBRID MODE]
    Forward component requests directly to the Active Engine (Core).
    This allows the Lite GUI to fetch real components via HTTP
    without needing a complex socket handshake first.
    """
    core_base = get_smart_core_url()
    target_url = f"{core_base}/api/v1/components/{path}"


    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            params=request.args,
            timeout=10
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        return (resp.content, resp.status_code, headers)

    except requests.exceptions.ConnectionError:
        current_app.logger.error(f"[Components Proxy] Failed to connect to Core at {target_url}. Is Core running?")
        return jsonify({
            "error": "Core Engine Unreachable",
            "details": f"Failed to connect to {target_url}",
            "hint": "If running Hybrid/Local, ensure Core is running on port 8989."
        }), 503
    except Exception as e:
        current_app.logger.error(f"[Components Proxy] Unexpected Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
