########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\helpers.py total lines 666 
########################################################################

"""
document : https://flowork.cloud/p-tinjauan-arsitektur-helperspy-dewa-tersembunyi-di-jantung-gateway-id.html
"""

import functools
from flask import request, current_app as app, jsonify, g
from functools import wraps
import jwt
import logging
import re
import os
import aiohttp
import datetime
import requests
import threading

from types import SimpleNamespace
from sqlalchemy.orm import joinedload

from .extensions import db
from .models import User, RegisteredEngine
from werkzeug.security import check_password_hash

from web3 import Web3
from eth_account.messages import encode_defunct


logger = logging.getLogger('flowork_gateway')


def get_db():

    if 'db' not in app.config:
        logger.error("[Helper] Database connection 'db' not found in app.config!")
        if not hasattr(app, 'db'):
            logger.error("[Helper] Database instance 'app.db' not found!")
            return None
        return app.db
    return app.config['db']

def get_db_session():

    try:
        return db.session
    except Exception as e:
        logger.error(f"[Helper] Failed to get db.session: {e}")
        return None

def get_user_id_from_token(token):

    try:
        secret_key = app.config.get('JWT_SECRET_KEY')
        if not secret_key:
            logger.error("[Helper] JWT_SECRET_KEY is not set!")
            return None
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_signature": True, "verify_exp": False})
        return decoded.get('user_id')
    except jwt.ExpiredSignatureError:
        logger.warning("[Helper] Token validation failed: ExpiredSignatureError")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[Helper] Token validation failed: InvalidTokenError: {e}")
        return None

def is_valid_uuid(uuid_string):

    if not uuid_string:
        return False
    uuid_regex = re.compile(
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )
    return re.match(uuid_regex, str(uuid_string)) is not None

def get_base_url():

    env_url = os.environ.get('FLOWORK_GATEWAY_BASE_URL')
    if env_url:
        return env_url.rstrip('/')

    if request:
        proto = request.headers.get('X-Forwarded-Proto', 'http')
        host = request.headers.get('Host')
        if host:
            return f"{proto}://{host}"
        return request.url_root.rstrip('/')

    return 'http://localhost:8000'

def verify_web3_signature(address: str, message: str, signature: str) -> bool:

    if not address or not message or not signature:
        logger.warning("[Helper] Web3 verification missing address, message, or signature.")
        return False

    try:
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        signer = w3.eth.account.recover_message(message_hash, signature=signature)

        is_valid = signer.lower() == address.lower()
        if not is_valid:
            logger.warning(f"[Helper] Signature invalid. Expected {address}, got {signer}")

        return is_valid
    except Exception as e:
        logger.error(f"[Helper] Error during Web3 signature recovery: {e}", exc_info=True)
        return False


async def emit_error(sid, event_name, message, data=None):

    if data is None:
        data = {}

    error_response = {
        "error": message,
        **data
    }

    if hasattr(app, 'sio'):
        try:
            await app.sio.emit(event_name, error_response, to=sid)
            logger.debug(f"[Helper] Emitted error to {sid} on event '{event_name}': {message}")
        except Exception as e:
            logger.error(f"[Helper] Failed to emit error to {sid}: {e}")
    else:
        logger.error(f"[Helper] app.sio not available. Cannot emit error: {message}")

async def emit_success(sid, event_name, data=None):

    if data is None:
        data = {}

    if hasattr(app, 'sio'):
        try:
            await app.sio.emit(event_name, data, to=sid)
            logger.debug(f"[Helper] Emitted success to {sid} on event '{event_name}'")
        except Exception as e:
            logger.error(f"[Helper] Failed to emit success to {sid}: {e}")
    else:
        logger.error(f"[Helper] app.sio not available. Cannot emit success for event '{event_name}'")


async def get_user_id_from_sid(sid):

    if not hasattr(app, 'sio'):
        logger.error("[Helper] app.sio not available. Cannot get session.")
        return None

    try:
        session = await app.sio.get_session(sid)
        if not session:
            logger.warning(f"[Helper] No active session found for SID: {sid}")
            return None

        user_id = session.get('user_id')
        if not user_id:
            logger.warning(f"[Helper] user_id not found in session for SID: {sid}")
            return None

        return user_id
    except KeyError:
        logger.warning(f"[Helper] SID not found in active connections: {sid}")
        return None
    except Exception as e:
        logger.error(f"[Helper] Error retrieving session for SID {sid}: {e}")
        return None

def get_request_data():

    if request.content_type == 'application/json':
        return request.json
    else:
        try:
            return request.get_json(force=True)
        except Exception:
            return None

def crypto_auth_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        app_log = app.logger

        address = request.headers.get("X-User-Address")
        message = request.headers.get("X-Signed-Message")
        signature = request.headers.get("X-Signature")
        payload_v = request.headers.get("X-Payload-Version")

        if not all([address, message, signature, payload_v]):
            app_log.warning("[Gateway Auth] Access denied: Missing required auth headers.")
            return jsonify({"error": "Missing required authentication headers."}), 401

        try:
            ts = int(message.split('|')[-1])
            now = int(datetime.datetime.utcnow().timestamp())
            if abs(now - ts) > 300:
                app_log.warning(f"[Gateway Auth] Access denied: Stale timestamp for {address[:10]}.")
                return jsonify({"error": "Stale authentication signature."}), 401
        except Exception:
            app_log.warning(f"[Gateway Auth] Access denied: Invalid message format for {address[:10]}.")
            return jsonify({"error": "Invalid authentication message format."}), 401

        if not verify_web3_signature(address, message, signature):
            app_log.warning(f"[Gateway Auth] Access denied: Invalid signature for {address[:10]}.")
            return jsonify({"error": "Invalid signature."}), 401

        try:
            user = db.session.query(User).filter(User.public_address.ilike(address)).first()
            if not user:
                app_log.info(f"[Gateway Auth] New user authenticated: {address[:10]}. Creating user entry.")
                placeholder_username = f"user_{address[:6]}...{address[-4:]}"
                user = User(public_address=address, username=placeholder_username)
                db.session.add(user)
                db.session.commit()

            g.user = user
            return f(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            app_log.error(f"[Gateway Auth] DB error during user lookup/create: {e}")
            return jsonify({"error": "Internal server error during authentication."}), 500
    return decorated_function

def get_user_permissions(user_obj):

    base_tier = "architect"
    capabilities = [
        "basic_access", "execute_workflow", "manage_engines",
        "save_presets", "share_workflows", "api_access"
    ]

    return {
        "tier": base_tier,
        "capabilities": capabilities
    }

def inject_user_data_to_core(user_obj):

    app_log = logging.getLogger('flowork_gateway')
    app_log.info(f"[Gateway Auth Inject] Starting injection task for user {user_obj.public_address[:10]}...")

    try:
        session = db.session()

        active_engine_session = find_active_engine_session(session, user_obj.id, None)

        if not active_engine_session or not active_engine_session.internal_url:
            app_log.warning(f"[Gateway Auth Inject] No active (DB) engine session found for user {user_obj.id}. Skipping injection.")
            session.close()
            return

        internal_api_url = active_engine_session.internal_url
        engine_api_endpoint = f"{internal_api_url.rstrip('/')}/api/v1/uistate/generic/current_user_data"

        permissions_data = get_user_permissions(user_obj)

        payload = {
            "user_id": user_obj.public_address,
            "username": user_obj.username,
            "email": user_obj.email,
            "tier": permissions_data.get("tier"),
            "permissions": permissions_data.get("capabilities"),
        }

        internal_api_key = os.environ.get("FLOWORK_INTERNAL_API_KEY", "flwk_dev_default_internal_key")
        app_log.info(f"[Gateway Auth Inject] Read FLOWORK_INTERNAL_API_KEY from env: {'TOKEN_FOUND' if internal_api_key != 'flwk_dev_default_internal_key' else 'USING_DEFAULT_KEY'}")

        headers = {
            "X-Internal-API-Key": internal_api_key
        }

        app_log.info(f"[Gateway Auth Inject] Forwarding user data to {engine_api_endpoint}...")
        try:
            response = requests.post(engine_api_endpoint, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            app_log.info(f"[Gateway Auth Inject] Successfully injected user data to Core Engine. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            app_log.error(f"[Gateway Auth Inject] Failed to connect/inject data to Core Engine at {engine_api_endpoint}: {e}")

    except Exception as e:
        app_log.error(f"[Gateway Auth Inject] Thread error during injection: {e}", exc_info=True)
    finally:
        if 'session' in locals() and session:
            session.close()

def engine_auth_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        app_log = app.logger

        engine_id = request.headers.get("X-Engine-Id")
        engine_token = request.headers.get("X-Engine-Token")

        if not all([engine_id, engine_token]):
            app_log.warning("[Gateway Auth] Access denied: Missing X-Engine-Id or X-Engine-Token.")
            return jsonify({"error": "Missing engine authentication headers."}), 401

        try:
            engine = db.session.query(RegisteredEngine).filter_by(id=engine_id).first()

            if not engine or not check_password_hash(engine.engine_token_hash, engine_token):
                app_log.warning(f"[Gateway Auth] Access denied: Invalid engine ID or token for {engine_id}.")
                return jsonify({"error": "Invalid engine ID or token."}), 401

            g.engine = engine
            return f(*args, **kwargs)
        except Exception as e:
            app_log.error(f"[Gateway Auth] DB error during engine auth: {e}")
            return jsonify({"error": "Internal server error during engine authentication."}), 500
    return decorated_function

def admin_token_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        app_log = app.logger

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            app_log.warning("[Gateway Auth] Access denied: Missing Admin Bearer token.")
            return jsonify({"error": "Admin token required."}), 401

        token = auth_header.split(" ")[1]
        MOMOD_ADMIN_TOKEN = os.environ.get("MOMOD_ADMIN_TOKEN", "flowork_momod_default_secret")

        if token != MOMOD_ADMIN_TOKEN:
            app_log.warning("[Gateway Auth] Access denied: Invalid Admin token.")
            return jsonify({"error": "Invalid admin token."}), 403

        kwargs['admin_permissions'] = {"plan:update", "user:list", "system:read"}
        return f(*args, **kwargs)
    return decorated_function


async def find_active_engine_session_by_user_id(user_id):

    db = get_db_session()
    if not db:
        logger.error("[Helper] find_active_engine_session_by_user_id failed to get DB session.")
        return None

    engine_session_model = None
    try:
        from .models import UserEngineSession
        engine_session_model = db.query(UserEngineSession).filter_by(user_id=user_id, is_active=True).first()
    except Exception as e:
        logger.error(f"[Helper] DB query failed in find_active_engine_session_by_user_id: {e}")
        db.rollback()
        return None
    finally:
        db.close()

    if not engine_session_model:
        logger.debug(f"[Helper] No active *owned* engine session found in DB for user {user_id}")
        return None

    engine_session = {
        "engine_id": engine_session_model.engine_id,
        "user_id": engine_session_model.user_id,
        "internal_url": engine_session_model.internal_url,
        "is_active": engine_session_model.is_active
    }

    logger.info(f"[Helper] Found active *owned* engine session for user {user_id}: engine {engine_session['engine_id']}")

    live_engine_sids = app.get_live_engine_sids()
    engine_id_str = str(engine_session['engine_id'])

    logger.debug(f"[Helper DEBUG] find_active_engine_session_by_user_id: Checking for engine '{engine_id_str}'. Current live SIDs: {live_engine_sids}")

    if engine_id_str in live_engine_sids:
        engine_session['live_sid'] = live_engine_sids[engine_id_str]
        engine_session['is_live'] = True
        engine_session['live_sid'] = live_engine_sids[engine_id_str]
        logger.debug(f"[Helper] Engine {engine_id_str} is LIVE with SID {engine_session['live_sid']}")
    else:
        engine_session['is_live'] = False
        engine_session['live_sid'] = None
        logger.warning(f"[Helper] Engine {engine_id_str} is DB-active but NOT LIVE.")

    return engine_session

def find_active_engine_session_wrapper(session, user_id, engine_id=None):

    db_sess = get_db_session()
    if not db_sess:
        logger.error("[Helper Wrapper] find_active_engine_session failed to get DB session.")
        return None

    from .models import UserEngineSession

    active_db = None
    try:
        query = db_sess.query(UserEngineSession).options(joinedload(UserEngineSession.engine)).filter_by(user_id=user_id, is_active=True)

        if engine_id:
            active_db = query.filter_by(engine_id=engine_id).first()
        else:
            active_db = query.first()

        if active_db:
            result_obj = SimpleNamespace(
                engine_id=active_db.engine_id,
                user_id=active_db.user_id,
                internal_url=active_db.internal_url,
                is_active=active_db.is_active,
                engine=active_db.engine
            )
            return result_obj
        return None

    except Exception as e:
        logger.error(f"[Helper Wrapper] DB query failed: {e}")
        db_sess.rollback()
        return None
    finally:
        db_sess.close()

find_active_engine_session = find_active_engine_session_wrapper


async def find_specific_active_engine_session(user_id, engine_id):

    db = get_db_session()
    if not db:
        logger.error("[Helper] find_specific_active_engine_session failed to get DB session.")
        return None

    engine_id_str = str(engine_id)

    engine_session_model = None
    try:
        from .models import UserEngineSession
        engine_session_model = db.query(UserEngineSession).filter_by(user_id=user_id, engine_id=engine_id_str, is_active=True).first()
    except Exception as e:
        logger.error(f"[Helper] DB query failed in find_specific_active_engine_session: {e}")
        db.rollback()
        return None
    finally:
        db.close()

    if not engine_session_model:
        logger.debug(f"[Helper] No specific active engine session found in DB for user {user_id} and engine {engine_id_str}")
        return None

    engine_session = {
        "engine_id": engine_session_model.engine_id,
        "user_id": engine_session_model.user_id,
        "internal_url": engine_session_model.internal_url,
        "is_active": engine_session_model.is_active
    }

    logger.info(f"[Helper] Found specific active session for user {user_id}: engine {engine_session['engine_id']}")

    live_engine_sids = app.get_live_engine_sids()

    if engine_id_str in live_engine_sids:
        engine_session['live_sid'] = live_engine_sids[engine_id_str]
        engine_session['is_live'] = True
        logger.debug(f"[Helper] Specific Engine {engine_id_str} is LIVE with SID {engine_session['live_sid']}")
    else:
        engine_session['is_live'] = False
        engine_session['live_sid'] = None
        logger.warning(f"[Helper] Specific Engine {engine_id_str} is DB-active but NOT LIVE.")

    return engine_session


async def forward_request_to_engine(engine_session, request_data):

    if not engine_session or not engine_session.get('is_live'):
        return {"error": "Engine is not connected or session is invalid."}

    internal_url = engine_session.get('internal_api_url')
    if not internal_url:
        return {"error": "Engine session is missing the internal API URL."}

    engine_api_url = f"{internal_url.rstrip('/')}/api/v1/workflow/execute_raw"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(engine_api_url, json=request_data, timeout=30) as response:

                response.raise_for_status()

                response_json = await response.json()
                logger.info(f"[Helper] Successfully forwarded request to {engine_api_url}, received response.")
                return response_json

    except aiohttp.ClientConnectorError as e:
        logger.error(f"[Helper] Cannot connect to engine at {engine_api_url}. Error: {e}")
        return {"error": f"Cannot connect to the engine's internal API. {e}"}
    except aiohttp.ClientResponseError as e:
        logger.error(f"[Helper] Engine at {engine_api_url} returned an error. Status: {e.status}, Message: {e.message}")
        try:
            error_detail = await response.json()
            return {"error": f"Engine API returned status {e.status}.", "details": error_detail}
        except Exception:
            return {"error": f"Engine API returned status {e.status}. {e.message}"}
    except Exception as e:
        logger.error(f"[Helper] Failed to forward request to engine {engine_api_url}. Error: {e}")
        return {"error": f"An unexpected error occurred while forwarding the request. {e}"}

async def forward_http_request_to_engine_api(engine_session, original_request):

    if not engine_session or not engine_session.get('internal_api_url'):
        logger.error("[Helper] Engine session not found or missing internal_api_url.")
        return ({"error": "Active engine is not available or not configured."}, 503)

    internal_url = engine_session['internal_api_url'].rstrip('/')

    if not original_request.path.startswith('/api/v1/engine-proxy/'):
        logger.error(f"Invalid proxy path: {original_request.path}")
        return ({"error": "Invalid proxy request path."}, 400)

    engine_path = original_request.path[len('/api/v1/engine-proxy/'):]
    target_url = f"{internal_url}/{engine_path}"

    if original_request.query_string:
        target_url += f"?{original_request.query_string.decode('utf-8')}"

    internal_api_key = os.environ.get("FLOWORK_INTERNAL_API_KEY", "flwk_dev_default_internal_key")

    headers = {key: value for (key, value) in original_request.headers if key.lower() not in ['host', 'content-length']}
    headers['X-Forwarded-For'] = original_request.remote_addr
    headers['X-Flowork-Gateway-User'] = engine_session.get('user_id', 'unknown')
    headers['X-Internal-API-Key'] = internal_api_key

    data = None
    json_data = None
    if original_request.method in ['POST', 'PUT', 'PATCH']:
        if original_request.is_json:
            json_data = original_request.get_json()
        else:
            data = original_request.get_data()

    logger.info(f"[Helper] Forwarding HTTP {original_request.method} to: {target_url}")

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(
                method=original_request.method,
                url=target_url,
                data=data,
                json=json_data,
                timeout=120,
                allow_redirects=False
            ) as response:

                response_content = await response.read()

                excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
                response_headers = {
                    key: value for (key, value) in response.headers.items()
                    if key.lower() not in excluded_headers
                }

                logger.info(f"[Helper] Received {response.status} from engine API.")

                return (response_content, response.status, response_headers)

    except aiohttp.ClientConnectorError as e:
        logger.error(f"[Helper] Cannot connect to engine at {target_url}. Error: {e}")
        return ({"error": f"Cannot connect to the engine's internal API."}, 503, {})
    except aiohttp.ClientResponseError as e:
        logger.error(f"[Helper] Engine at {target_url} returned an error. Status: {e.status}, Message: {e.message}")
        return ({"error": f"Engine API returned status {e.status}: {e.message}"}, e.status, {})
    except Exception as e:
        logger.error(f"[Helper] Failed to forward HTTP request to engine {target_url}. Error: {e}")
        return ({"error": "An unexpected error occurred while proxying the request."}, 500, {})

def engine_api_proxy_decorator(f):

    @wraps(f)
    async def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return ({"error": "Authorization header is missing or invalid."}, 401)

        token = auth_header.split(' ')[1]
        user_id = get_user_id_from_token(token)
        if not user_id:
            return ({"error": "Invalid or expired token."}, 401)

        engine_session = await find_active_engine_session_by_user_id(user_id)

        if not engine_session:
            return ({"error": "No active engine session found for this user."}, 404)

        if not engine_session.get('is_live'):
            return ({"error": "The active engine is not currently connected to the Gateway."}, 503)

        if not engine_session.get('internal_api_url'):
            return ({"error": "Engine session is misconfigured (missing internal API URL)."}, 500)

        return await f(engine_session=engine_session, *args, **kwargs)

    return decorated_function

async def forward_generic_request(engine_session, method, target_endpoint, original_request):
    """
    Forwards a request to the engine without checking for 'engine-proxy' path prefix.
    Useful for specific modules like AI Training that need to hit specific endpoints.
    """
    if not engine_session or not engine_session.get('internal_api_url'):
        logger.error("[Helper] Engine session missing or invalid.")
        return ({"error": "Active engine is not available."}, 503)

    internal_url = engine_session['internal_api_url'].rstrip('/')
    if not target_endpoint.startswith('/'):
        target_endpoint = '/' + target_endpoint

    target_url = f"{internal_url}{target_endpoint}"

    if original_request.query_string:
        target_url += f"?{original_request.query_string.decode('utf-8')}"

    internal_api_key = os.environ.get("FLOWORK_INTERNAL_API_KEY", "flwk_dev_default_internal_key")

    headers = {key: value for (key, value) in original_request.headers if key.lower() not in ['host', 'content-length']}
    headers['X-Forwarded-For'] = original_request.remote_addr
    headers['X-Flowork-Gateway-User'] = engine_session.get('user_id', 'unknown')
    headers['X-Internal-API-Key'] = internal_api_key

    data = None
    json_data = None
    if method in ['POST', 'PUT', 'PATCH']:
        if original_request.is_json:
            json_data = original_request.get_json()
        else:
            data = original_request.get_data()

    logger.info(f"[Helper Generic] Forwarding {method} to: {target_url}")

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(
                method=method,
                url=target_url,
                data=data,
                json=json_data,
                timeout=300, # Long timeout for training uploads
                allow_redirects=False
            ) as response:
                response_content = await response.read()

                excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
                response_headers = {
                    key: value for (key, value) in response.headers.items()
                    if key.lower() not in excluded_headers
                }
                logger.info(f"[Helper Generic] Response from {target_url}: {response.status}")
                return (response_content, response.status, response_headers)

    except Exception as e:
        logger.error(f"[Helper Generic] Proxy error: {e}")
        return ({"error": f"Gateway Proxy Error: {str(e)}"}, 500, {})
