########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\helpers.py total lines 164 
########################################################################

import functools
from flask import request, current_app as app, jsonify, g, make_response
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
    if 'db' not in app.config: return None
    return app.config['db']

def get_db_session():
    try: return db.session
    except Exception: return None

def get_user_id_from_token(token):
    try:
        secret_key = app.config.get('JWT_SECRET_KEY')
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"], options={"verify_signature": True, "verify_exp": False})
        return decoded.get('user_id')
    except Exception: return None

def is_valid_uuid(uuid_string):
    if not uuid_string: return False
    uuid_regex = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
    return re.match(uuid_regex, str(uuid_string)) is not None

def get_base_url():
    env_url = os.environ.get('FLOWORK_GATEWAY_BASE_URL')
    if env_url: return env_url.rstrip('/')
    return 'http://localhost:8000'

def verify_web3_signature(address: str, message: str, signature: str) -> bool:
    if not address or not message or not signature: return False
    try:
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        signer = w3.eth.account.recover_message(message_hash, signature=signature)
        return signer.lower() == address.lower()
    except Exception: return False

def get_request_data():
    if request.content_type == 'application/json': return request.json
    try: return request.get_json(force=True)
    except Exception: return None

async def emit_error(sid, event_name, message, data=None):
    if data is None: data = {}
    if hasattr(app, 'sio'): await app.sio.emit(event_name, {"error": message, **data}, to=sid)

async def emit_success(sid, event_name, data=None):
    if data is None: data = {}
    if hasattr(app, 'sio'): await app.sio.emit(event_name, data, to=sid)

async def get_user_id_from_sid(sid):
    if not hasattr(app, 'sio'): return None
    try:
        session = await app.sio.get_session(sid)
        return session.get('user_id') if session else None
    except Exception: return None

def crypto_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS': return f(*args, **kwargs)
        if request.path.startswith('/api/v1/apps'): return f(*args, **kwargs)

        address = request.headers.get("X-User-Address")
        message = request.headers.get("X-Signed-Message")
        signature = request.headers.get("X-Signature")
        payload_v = request.headers.get("X-Payload-Version")

        if not all([address, message, signature, payload_v]):
            return jsonify({"error": "Missing auth headers"}), 401

        if not verify_web3_signature(address, message, signature):
            return jsonify({"error": "Invalid signature"}), 401

        try:
            user = db.session.query(User).filter(User.public_address.ilike(address)).first()
            if not user:
                user = User(public_address=address, username=f"user_{address[:6]}", status='active')
                db.session.add(user)
                db.session.commit()
            g.user = user
            return f(*args, **kwargs)
        except Exception: return jsonify({"error": "Internal Error"}), 500
    return decorated_function

def admin_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "): return jsonify({"error": "Admin required"}), 401
        token = auth.split(" ")[1]
        if token != os.environ.get("MOMOD_ADMIN_TOKEN", "flowork_momod_default_secret"): return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated_function

async def find_active_engine_session_by_user_id(user_id):
    try:
        from .models import UserEngineSession
        model = db.session.query(UserEngineSession).filter_by(user_id=user_id, is_active=True).first()
        if not model: return None
        return {"engine_id": model.engine_id, "user_id": model.user_id, "is_live": True}
    except Exception: return None

def find_active_engine_session_wrapper(session, user_id, engine_id=None):
    try:
        from .models import UserEngineSession
        query = session.query(UserEngineSession).filter_by(user_id=user_id, is_active=True)
        if engine_id: query = query.filter_by(engine_id=engine_id)
        active_db = query.first()
        if active_db:
            return SimpleNamespace(engine_id=active_db.engine_id, user_id=active_db.user_id, internal_url=active_db.internal_url, is_active=active_db.is_active)
        return None
    except: return None

find_active_engine_session = find_active_engine_session_wrapper

def get_user_permissions(user_obj):
    return {"tier": "architect", "capabilities": ["api_access", "execute_workflow"]}

def engine_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.headers.get("X-Engine-Id"): return jsonify({"error": "Auth Error"}), 401
        return f(*args, **kwargs)
    return decorated_function

async def find_specific_active_engine_session(u, e): return None
async def forward_request_to_engine(e, r): return {"status": "proxied"}
async def forward_http_request_to_engine_api(e, r): return (b'{"status": "ok"}', 200, {})
def engine_api_proxy_decorator(f):
    @wraps(f)
    async def dec(*args, **kwargs): return await f(*args, **kwargs)
    return dec
async def forward_generic_request(e, m, t, o): return (b'{"status": "ok"}', 200, {})
def inject_user_data_to_core(user_obj): pass
