########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\user.py total lines 557 
########################################################################

from flask import Blueprint, jsonify, request, current_app, g
from werkzeug.security import generate_password_hash
import secrets
import time
import datetime
import uuid
import requests
import os
from functools import wraps
from ..models import User, RegisteredEngine, Subscription, EngineShare
from ..extensions import db, socketio
from ..helpers import (
    crypto_auth_required,
    get_request_data,
    get_user_permissions
)
from ..globals import globals_instance, pending_auths
engine_manager = globals_instance.engine_manager
import json
from eth_account.messages import encode_defunct
from web3.auto import w3
from ..models import Role, Permission

try:
    from cryptography.hazmat.primitives import hashes as crypto_hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

user_bp = Blueprint("user", __name__, url_prefix="/api/v1/user")


@user_bp.route('/users', methods=['POST'])
def bootstrap_user():
    """
    (English Hardcode) Handles the initial user bootstrap for self-hosting.
    This endpoint creates the very first user (admin/owner) and should ideally
    be disabled or protected after first use.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400

    if User.query.first():
        current_app.logger.warning(f"[Gateway Bootstrap] Blocked attempt to create user '{username}'. Users already exist.")
        return jsonify({"error": "A user already exists. Bootstrap is only for first-time setup."}), 409

    current_app.logger.info(f"[Gateway Bootstrap] Attempting to create first user: {username} ({email})")

    try:
        priv_key_bytes = secrets.token_bytes(32)
        new_account = w3.eth.account.from_key(priv_key_bytes)
        new_private_key_hex = new_account.key.hex()
        new_public_address = new_account.address

        full_private_key = f"0x{new_private_key_hex.lstrip('0x')}"

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=hashed_password,
            status="active",
            public_address=new_public_address
        )
        db.session.add(new_user)
        db.session.flush()

        free_subscription = Subscription(id=str(uuid.uuid4()), user_id=new_user.id, tier="architect")
        db.session.add(free_subscription)

        db.session.commit()

        current_app.logger.info(f"[Gateway Bootstrap] SUCCESS: Created first user {username} ({new_public_address}).")

        return jsonify({
            "message": "Bootstrap successful. User created.",
            "user_id": new_user.id,
            "public_address": new_public_address,
            "private_key": full_private_key,
            "note": "SAVE THIS PRIVATE KEY. It is your password and cannot be recovered."
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Gateway Bootstrap] Failed to create bootstrap user: {e}", exc_info=True)
        return jsonify({"error": f"Failed to create bootstrap user: {e}"}), 500


@user_bp.route('/public/<identifier>', methods=['GET'])
def get_public_profile(identifier):
    """
    (English Hardcode) Public, unauthenticated endpoint to get basic user info
    (English Hardcode) and their recent public articles from the GATEWAY database.
    (English Hardcode) This fixes the 404 error from the GUI.
    """
    try:
        user = User.query.filter(User.public_address.ilike(identifier)).first()
        if not user:
             user = User.query.filter(User.username.ilike(identifier)).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        profile_data = {
            "address": user.public_address,
            "name": user.username,
            "bio": None,
            "avatar": None,
            "articles": []
        }

        response = jsonify(profile_data)
        response.headers['Cache-Control'] = 'public, max-age=300'
        return response
    except Exception as e:
        current_app.logger.error(f"[Public Profile] Error fetching profile for {identifier}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route("/license", methods=["GET"])
@crypto_auth_required
def get_user_license():
    current_user = g.user
    """
    Men-generate dan menandatangani sertifikat lisensi untuk pengguna yang terotentikasi.
    """
    if not CRYPTO_AVAILABLE:
        return jsonify({"error": "Cryptography library is unavailable on the server."}), 500

    private_key_pem = os.getenv("FLOWORK_MASTER_PRIVATE_KEY")
    if not private_key_pem:
        current_app.logger.critical("FLOWORK_MASTER_PRIVATE_KEY is not set in .env!")
        return jsonify({"error": "Server is not configured for license signing."}), 500

    try:
        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)

        user_tier = get_user_permissions(current_user)["tier"]

        expires_at = None
        if hasattr(current_user, 'subscriptions') and current_user.subscriptions:
          if current_user.subscriptions[0] and current_user.subscriptions[0].expires_at:
                expires_at = current_user.subscriptions[0].expires_at

        if not expires_at:
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365*100)

        license_data = {
            "license_id": f"flw-lic-{uuid.uuid4()}",
            "user_id": current_user.public_address,
            "tier": user_tier,
            "issued_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
            "valid_until": expires_at.isoformat().replace('+00:00', 'Z'),
        }

        message_to_sign = json.dumps({"data": license_data}, sort_keys=True, separators=(',', ':')).encode('utf-8')

        signature = private_key.sign(
            message_to_sign,
            padding.PSS(
                mgf=padding.MGF1(crypto_hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            crypto_hashes.SHA256()
        )

        final_certificate = {
            "data": license_data,
            "signature": signature.hex()
        }

        return jsonify(final_certificate)

    except Exception as e:
        current_app.logger.error(f"Failed to generate license certificate: {e}")
        return jsonify({"error": "Failed to generate license.", "details": str(e)}), 500


@user_bp.route("/engines/select-for-auth", methods=["POST"])
@crypto_auth_required
def select_engine_for_auth():
    current_user = g.user
    data = get_request_data()
    req_id = data.get("request_id")
    engine_id = data.get("engine_id")

    if not req_id or not engine_id:
        return jsonify({"error": "request_id and engine_id are required."}), 400

    engine = RegisteredEngine.query.filter_by(
        id=engine_id, user_id=current_user.id
    ).first()

    if not engine:
        return jsonify({"error": "Engine not found or permission denied."}), 404

    new_plaintext_token = f"dev_engine_{secrets.token_hex(16)}"
    engine.engine_token_hash = generate_password_hash(
        new_plaintext_token, method="pbkdf2:sha256"
    )
    db.session.commit()

    pending_auths[req_id] = {"token": new_plaintext_token, "timestamp": time.time()}
    current_app.logger.info(f"User {current_user.public_address} authorized engine {engine.name} via dashboard. Token ready for claim by Core req_id: {req_id}")

    return jsonify(
        {
            "status": "success",
            "message": "Engine selected and authorized. Core can now claim the new token.",
        }
    )


@user_bp.route('/engines', methods=['GET'])
@crypto_auth_required
def get_user_engines():
    current_user = g.user
    """
    Mengembalikan daftar engine yang terdaftar milik user saat ini.
    FASE 4: Sekarang menyertakan status online/offline berdasarkan cache.
    """
    try:
        engines = RegisteredEngine.query.filter_by(user_id=current_user.id).order_by(RegisteredEngine.name).all()

        engine_list = []
        current_time = time.time()
        ONLINE_THRESHOLD_SECONDS = 120

        with engine_manager.engine_last_seen_lock:
            last_seen_snapshot = engine_manager.engine_last_seen_cache.copy()

        for e in engines:
            last_seen_timestamp = last_seen_snapshot.get(e.id, 0)
            status = 'offline'
            if (current_time - last_seen_timestamp) < ONLINE_THRESHOLD_SECONDS:
                status = 'online'

            engine_list.append({
                'id': e.id,
                'name': e.name,
                'status': status,
                'last_seen': datetime.datetime.fromtimestamp(last_seen_timestamp).isoformat() if last_seen_timestamp > 0 else None
            })

        return jsonify(engine_list)
    except Exception as e:
        current_app.logger.error(f"Error fetching engines for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to fetch engine list."}), 500


@user_bp.route('/engines', methods=['POST'])
@crypto_auth_required
def register_new_engine():
    current_user = g.user
    """Mendaftarkan engine baru untuk user saat ini."""
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Engine name is required'}), 400

    try:
        raw_token = f"dev_engine_{secrets.token_hex(16)}"
        token_hash = generate_password_hash(raw_token, method="pbkdf2:sha256")
        new_engine_id = str(uuid.uuid4())

        new_engine = RegisteredEngine(
            id=new_engine_id,
            user_id=current_user.id,
            name=name,
            engine_token_hash=token_hash,
            status='offline'
        )
        db.session.add(new_engine)
        db.session.commit()

        current_app.logger.info(f"User {current_user.public_address} registered new engine: '{name}' (ID: {new_engine.id})")

        return jsonify({
            'id': new_engine.id,
            'name': new_engine.name,
            'status': new_engine.status,
            'raw_token': raw_token
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering engine for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to register new engine."}), 500


@user_bp.route('/engines/<string:engine_id>', methods=['DELETE'])
@crypto_auth_required
def delete_user_engine(engine_id):
    current_user = g.user
    """Menghapus engine milik user saat ini berdasarkan ID engine."""
    try:
        engine = RegisteredEngine.query.filter_by(id=engine_id, user_id=current_user.id).first()
        if not engine:
            return jsonify({'error': 'Engine not found or not owned by user'}), 404

        with engine_manager.engine_last_seen_lock:
            engine_manager.engine_last_seen_cache.pop(engine_id, None)
        engine_manager.engine_vitals_cache.pop(engine_id, None)
        engine_manager.engine_url_map.pop(engine_id, None)

        db.session.delete(engine)
        db.session.commit()

        current_app.logger.info(f"User {current_user.public_address} deleted engine: '{engine.name}' (ID: {engine_id})")

        socketio.emit(
            "engine_deleted",
            {"engine_id": engine_id},
            to=current_user.id,
            namespace="/gui-socket"
        )

        return jsonify({'message': 'Engine deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting engine {engine_id} for user {current_user.id}: {e}")
        return jsonify({"error": "Failed to delete engine."}), 500


@user_bp.route("/engines/<string:engine_id>/share", methods=["POST"])
@crypto_auth_required
def share_engine(engine_id):
    """
    (English Hardcode) Creates a new 'share' for an engine or updates an existing one.
    (English Hardcode) Only the ENGINE OWNER can perform this action.
    (English Hardcode) This implements the contract: POST /engines/{engine_id}/share
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    share_with_address = data.get('user_id')
    role = data.get('role', 'reader')

    if not share_with_address:
        return jsonify({"error": "user_id (guest's public address) is required"}), 400
    if role not in ['reader', 'runner', 'admin']:
        return jsonify({"error": "Invalid role. Must be 'reader' or 'runner'"}), 400

    owner_user = g.user
    if not owner_user:
        current_app.logger.error(f"[Shares] No authenticated user (g.user) in context.")
        return jsonify({"error": "Authentication context not found"}), 500

    engine = RegisteredEngine.query.filter_by(id=engine_id).first()
    if not engine:
        return jsonify({"error": "Engine not found"}), 404

    if engine.user_id != owner_user.id:
        current_app.logger.warning(f"[AuthZ] DENIED: User {owner_user.public_address} tried to share engine {engine_id} which they do not own.")
        return jsonify({"error": "You are not the owner of this engine"}), 403

    try:
        checked_guest_address = w3.to_checksum_address(share_with_address)
    except Exception:
        return jsonify({"error": "Invalid guest public address format (user_id)"}), 400

    guest_user = User.query.filter(User.public_address.ilike(checked_guest_address)).first()
    if not guest_user:
        current_app.logger.info(f"[Shares] Creating new user record for guest: {checked_guest_address}")
        placeholder_email = f"{checked_guest_address.lower()}@flowork.crypto"
        email_exists = User.query.filter(User.email.ilike(placeholder_email)).first()

        if email_exists:
            guest_user = email_exists
        else:
            guest_user = User(
                id=str(uuid.uuid4()),
                username=checked_guest_address,
                email=placeholder_email,
                password_hash=generate_password_hash(secrets.token_urlsafe(32), method="pbkdf2:sha256"),
                status="active",
                public_address=checked_guest_address
            )
            db.session.add(guest_user)
            try:
                db.session.flush()
                new_subscription = Subscription(id=str(uuid.uuid4()), user_id=guest_user.id, tier="architect")
                db.session.add(new_subscription)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"[Shares] Failed to create new guest user {checked_guest_address}: {e}")
                return jsonify({"error": "Failed to create guest user record"}), 500

    existing_share = EngineShare.query.filter_by(engine_id=engine.id, user_id=guest_user.id).first()

    try:
        if existing_share:
            current_app.logger.info(f"[Shares] Updating role for {checked_guest_address} on engine {engine_id} to '{role}'")
            existing_share.role = role
            db.session.commit()

            socketio.emit(
                'force_refresh_auth_list',
                {'message': f'Share role updated for {checked_guest_address}'},
                room=engine.id
            )
            current_app.logger.info(f"Sent 'force_refresh_auth_list' PUSH to room: {engine.id}")
            return jsonify({"message": "Share role updated successfully"}), 200
        else:
            current_app.logger.info(f"[Shares] Creating new share for {checked_guest_address} on engine {engine_id} with role '{role}'")
            new_share = EngineShare(
                engine_id=engine.id,
                user_id=guest_user.id,
                role=role
            )
            db.session.add(new_share)
            db.session.commit()

            socketio.emit(
                'force_refresh_auth_list',
                {'message': f'User {checked_guest_address} added to shares'},
                room=engine.id
            )
            current_app.logger.info(f"Sent 'force_refresh_auth_list' PUSH to room: {engine.id}")
            return jsonify({"message": "Engine shared successfully", "share_id": new_share.id}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Shares] Error creating/updating share: {e}", exc_info=True)
        return jsonify({"error": "Database error while saving share"}), 500


@user_bp.route("/engines/<engine_id>/reset-token", methods=["POST"])
@crypto_auth_required
def reset_engine_token_legacy(engine_id):
    current_user = g.user
    """
    Menghasilkan token baru untuk engine yang sudah ada.
    Endpoint ini mungkin redundant dengan alur otorisasi via dashboard.
    """
    engine = RegisteredEngine.query.filter_by(
        id=engine_id, user_id=current_user.id
    ).first()
    if not engine:
        return jsonify({"error": "Engine not found or permission denied."}), 404

    new_plaintext_token = f"dev_engine_{secrets.token_hex(16)}"
    token_hash = generate_password_hash(new_plaintext_token, method="pbkdf2:sha256")
    engine.engine_token_hash = token_hash
    db.session.commit()
    current_app.logger.info(f"User {current_user.public_address} reset token for engine: '{engine.name}' (ID: {engine_id})")

    return (
        jsonify(
            {
                "message": f"Token for engine '{engine.name}' has been reset.",
                "token": new_plaintext_token,
                "engine_id": engine.id,
            }
        ),
        200,
    )


@user_bp.route("/engines/<string:engine_id>/update-name", methods=["PUT"])
@crypto_auth_required
def update_engine_name_legacy(engine_id):
    current_user = g.user
    """Updates the name of an existing engine."""
    engine = RegisteredEngine.query.filter_by(id=engine_id, user_id=current_user.id).first()
    if not engine:
        return jsonify({"error": "Engine not found or permission denied."}), 404

    data = request.get_json()
    new_name = data.get("name")
    if not new_name:
        return jsonify({"error": "New name is required."}), 400

    old_name = engine.name
    engine.name = new_name
    db.session.commit()

    current_app.logger.info(f"User {current_user.public_address} renamed engine '{old_name}' to '{new_name}' (ID: {engine_id})")

    status = 'offline'
    with engine_manager.engine_last_seen_lock:
        if (time.time() - engine_manager.engine_last_seen_cache.get(engine_id, 0)) < 120 :
            status = 'online'

    socketio.emit(
        "engine_status_update",
        {"engine_id": engine_id, "name": new_name, "status": status},
        to=current_user.id,
        namespace="/gui-socket"
    )

    return jsonify({"message": f"Engine '{new_name}' updated successfully."}), 200


@user_bp.route('/shared-engines', methods=['GET'])
@crypto_auth_required
def get_shared_engines():
    current_user = g.user
    """Mengembalikan daftar engine yang di-share PADA user ini."""
    try:
        shares = EngineShare.query.filter_by(user_id=current_user.id)\
            .join(RegisteredEngine, EngineShare.engine_id == RegisteredEngine.id)\
            .join(User, RegisteredEngine.user_id == User.id)\
            .options(db.contains_eager(EngineShare.engine).contains_eager(RegisteredEngine.owner))\
            .order_by(RegisteredEngine.name)\
            .all()

        shared_engine_list = []
        current_time = time.time()
        ONLINE_THRESHOLD_SECONDS = 120

        with engine_manager.engine_last_seen_lock:
            last_seen_snapshot = engine_manager.engine_last_seen_cache.copy()

        for share in shares:
            engine = share.engine
            owner = engine.owner

            last_seen_timestamp = last_seen_snapshot.get(engine.id, 0)
            status = 'offline'
            if (current_time - last_seen_timestamp) < ONLINE_THRESHOLD_SECONDS:
                status = 'online'

            shared_engine_list.append({
                'id': engine.id,
                'name': engine.name,
                'status': status,
                'owner': {
                    'user_id': owner.id,
                    'username': owner.username,
                    'email': owner.email
                },
                'shared_at': share.shared_at.isoformat() if share.shared_at else None
            })

        return jsonify(shared_engine_list)
    except Exception as e:
        current_app.logger.error(f"Error fetching shared engines for user {current_user.id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch shared engine list."}), 500
