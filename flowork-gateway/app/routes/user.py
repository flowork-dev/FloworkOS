########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\user.py total lines 725 
########################################################################

from flask import Blueprint, jsonify, request, current_app, g
from werkzeug.security import generate_password_hash
import secrets
import time
import datetime
import uuid
import os
import json
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from ..models import User, RegisteredEngine, Subscription, EngineShare
from ..extensions import db, socketio
from ..helpers import (
    crypto_auth_required,
    get_request_data,
    get_user_permissions
)
from ..globals import globals_instance, pending_auths
from web3.auto import w3

try:
    from cryptography.hazmat.primitives import hashes as crypto_hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

engine_manager = globals_instance.engine_manager
user_bp = Blueprint("user", __name__, url_prefix="/api/v1/user")


def _add_column_if_missing(column_name, column_type="TEXT"):
    """
    Menambahkan kolom secara aman menggunakan raw SQL dalam sesi yang sama.
    """
    try:
        current_app.logger.warning(f"[AutoMigrate] Attempting to add missing column '{column_name}'...")
        db.session.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
        db.session.commit()
        current_app.logger.info(f"[AutoMigrate] SUCCESS: Column '{column_name}' added.")
        return True
    except Exception as e:
        if "duplicate column" in str(e).lower():
            return True
        current_app.logger.error(f"[AutoMigrate] Failed to add column: {e}")
        return False

def _safe_update_profile(user, new_bio, new_avatar=None):
    """
    Mencoba update. Jika gagal karena kolom hilang, perbaiki DB dan retry.
    """
    try:
        user.bio = new_bio
        if new_avatar: user.avatar = new_avatar
        db.session.commit()
        return True
    except OperationalError as e:
        db.session.rollback()
        err_msg = str(e).lower()

        if "no such column" in err_msg:
            current_app.logger.warning("[Profile] Schema mismatch detected. Fixing...")

            if "bio" in err_msg: _add_column_if_missing("bio")
            if "avatar" in err_msg: _add_column_if_missing("avatar")

            try:
                db.session.expire(user)
                user.bio = new_bio
                if new_avatar: user.avatar = new_avatar
                db.session.commit()
                current_app.logger.info("[Profile] Retry update successful.")
                return True
            except Exception as retry_e:
                current_app.logger.error(f"[Profile] Retry failed: {retry_e}")
                return False
        else:
            current_app.logger.error(f"[Profile] Database error: {e}")
            raise e

def _safe_update_preferences(user, prefs_json):
    try:
        user.preferences = prefs_json
        db.session.commit()
        return True
    except OperationalError as e:
        db.session.rollback()
        err_msg = str(e).lower()
        if "no such column" in err_msg and "preferences" in err_msg:
            current_app.logger.warning("[Preferences] Column missing. Adding 'preferences'...")
            if _add_column_if_missing("preferences", "TEXT"):
                try:
                    db.session.expire(user)
                    user.preferences = prefs_json
                    db.session.commit()
                    return True
                except Exception as retry_e:
                    current_app.logger.error(f"[Preferences] Retry failed: {retry_e}")
                    return False
        return False

@user_bp.route('/users', methods=['POST'])
def bootstrap_user():
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


@user_bp.route('/profile', methods=['PUT', 'PATCH'])
@crypto_auth_required
def update_user_profile():
    """
    [FIXED] Update profile dengan mekanisme Auto-Healing Database.
    """
    current_user = g.user
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    new_name = data.get('name')
    new_bio = data.get('bio')
    new_avatar = data.get('avatar')

    current_app.logger.info(f"REQ UPDATE PROFILE: User={current_user.username}")

    try:
        if new_name and isinstance(new_name, str):
            clean_name = new_name.strip()
            if len(clean_name) >= 3:
                if current_user.username != clean_name:
                    existing = User.query.filter(User.username == clean_name, User.id != current_user.id).first()
                    if existing:
                        return jsonify({"error": "Username already taken"}), 409
                    current_user.username = clean_name
            else:
                return jsonify({"error": "Username too short"}), 400

        if new_bio is not None or new_avatar is not None:
            safe_bio = str(new_bio) if new_bio else ""
            success = _safe_update_profile(current_user, safe_bio, new_avatar)

            if not success:
                return jsonify({"error": "Database schema update failed"}), 500
        else:
            db.session.commit()

        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "name": current_user.username,
                "email": current_user.email,
                "address": current_user.public_address,
                "bio": getattr(current_user, 'bio', ''),
                "avatar": getattr(current_user, 'avatar', None)
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRITICAL PROFILE ERROR: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@user_bp.route('/public/<identifier>', methods=['GET'])
def get_public_profile(identifier):
    try:
        user = User.query.filter(User.public_address.ilike(identifier)).first()
        if not user:
            user = User.query.filter(User.username.ilike(identifier)).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        bio_val = getattr(user, 'bio', '')
        avatar_val = getattr(user, 'avatar', None)

        profile_data = {
            "address": user.public_address,
            "name": user.username,
            "bio": bio_val or "",
            "avatar": avatar_val,
            "articles": []
        }

        response = jsonify(profile_data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        current_app.logger.error(f"[Public Profile] Error fetching profile for {identifier}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@user_bp.route("/license", methods=["GET"])
@crypto_auth_required
def get_user_license():
    current_user = g.user

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
    current_app.logger.info(f"User {current_user.public_address} authorized engine {engine.name} via dashboard.")

    return jsonify({
        "status": "success",
        "message": "Engine selected and authorized.",
    })

@user_bp.route('/preferences', methods=['GET'])
@crypto_auth_required
def get_user_preferences():
    current_user = g.user
    try:
        prefs_raw = getattr(current_user, 'preferences', '{}')
        if not prefs_raw:
            prefs_raw = '{}'

        try:
            prefs_data = json.loads(prefs_raw)
        except:
            prefs_data = {}

        return jsonify(prefs_data)
    except Exception as e:
        if "no such column" in str(e).lower():
            return jsonify({})
        current_app.logger.error(f"[Preferences] Fetch error: {e}")
        return jsonify({"error": "Failed to fetch preferences"}), 500

@user_bp.route('/preferences', methods=['PATCH'])
@crypto_auth_required
def update_user_preferences():
    current_user = g.user
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        current_raw = getattr(current_user, 'preferences', '{}') or '{}'
        try:
            current_prefs = json.loads(current_raw)
        except:
            current_prefs = {}

        current_prefs.update(data)
        final_json = json.dumps(current_prefs)

        if _safe_update_preferences(current_user, final_json):
            return jsonify({"message": "Preferences saved", "preferences": current_prefs})
        else:
            return jsonify({"error": "Failed to save preferences db schema"}), 500

    except Exception as e:
        current_app.logger.error(f"[Preferences] Update error: {e}")
        return jsonify({"error": str(e)}), 500

@user_bp.route('/engines', methods=['GET'])
@crypto_auth_required
def get_user_engines():
    current_user = g.user
    try:
        engines = RegisteredEngine.query.filter_by(user_id=current_user.id).order_by(RegisteredEngine.name).all()
        engine_list = []
        current_time = time.time()
        ONLINE_THRESHOLD_SECONDS = 120

        with engine_manager.engine_last_seen_lock:
            last_seen_snapshot = engine_manager.engine_last_seen_cache.copy()

        for e in engines:
            last_seen_timestamp_mem = last_seen_snapshot.get(e.id, 0)
            last_seen_timestamp_db = 0
            if e.last_seen:
                 last_seen_timestamp_db = e.last_seen.replace(tzinfo=datetime.timezone.utc).timestamp()

            effective_last_seen = max(last_seen_timestamp_mem, last_seen_timestamp_db)
            status = 'offline'
            if (current_time - effective_last_seen) < ONLINE_THRESHOLD_SECONDS:
                status = 'online'

            engine_list.append({
                'id': e.id,
                'name': e.name,
                'status': status,
                'last_seen': datetime.datetime.fromtimestamp(effective_last_seen).isoformat() if effective_last_seen > 0 else None
            })

        return jsonify(engine_list)
    except Exception as e:
        current_app.logger.error(f"Error fetching engines: {e}")
        return jsonify({"error": "Failed to fetch engine list."}), 500


@user_bp.route('/engines', methods=['POST'])
@crypto_auth_required
def register_new_engine():
    current_user = g.user
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

        return jsonify({
            'id': new_engine.id,
            'name': new_engine.name,
            'status': new_engine.status,
            'raw_token': raw_token
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering engine: {e}")
        return jsonify({"error": "Failed to register new engine."}), 500


@user_bp.route('/engines/<string:engine_id>', methods=['DELETE'])
@crypto_auth_required
def delete_user_engine(engine_id):
    current_user = g.user
    try:
        engine = RegisteredEngine.query.filter_by(id=engine_id, user_id=current_user.id).first()
        if not engine:
            return jsonify({'error': 'Engine not found'}), 404

        with engine_manager.engine_last_seen_lock:
            engine_manager.engine_last_seen_cache.pop(engine_id, None)
            engine_manager.engine_vitals_cache.pop(engine_id, None)
        engine_manager.engine_url_map.pop(engine_id, None)

        db.session.delete(engine)
        db.session.commit()

        socketio.emit("engine_deleted", {"engine_id": engine_id}, to=current_user.id, namespace="/gui-socket")
        return jsonify({'message': 'Engine deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete engine."}), 500


@user_bp.route('/engines/<string:engine_id>/shares', methods=['GET'])
@crypto_auth_required
def get_engine_shares(engine_id):
    current_user = g.user
    engine = RegisteredEngine.query.filter_by(id=engine_id).first()
    if not engine:
        return jsonify({"error": "Engine not found"}), 404

    if engine.user_id != current_user.id:
         return jsonify({"error": "Unauthorized"}), 403

    shares = EngineShare.query.filter_by(engine_id=engine_id).all()
    result = []
    for s in shares:
        if not s.user: continue
        result.append({
            "user_id": s.user_id,
            "engine_id": s.engine_id,
            "username": s.user.username,
            "email": s.user.email,
            "public_address": s.user.public_address,
            "role": s.role,
            "shared_at": s.shared_at.isoformat() if s.shared_at else None
        })
    return jsonify(result)


@user_bp.route("/engines/<string:engine_id>/share", methods=["POST"])
@crypto_auth_required
def share_engine(engine_id):
    data = request.get_json()
    if not data: return jsonify({"error": "Invalid JSON payload"}), 400

    share_with_address = data.get('user_id')
    role = data.get('role')

    if not share_with_address: return jsonify({"error": "user_id (guest's public address) is required"}), 400
    if role and role not in ['reader', 'runner', 'admin']: return jsonify({"error": "Invalid role"}), 400

    owner_user = g.user
    engine = RegisteredEngine.query.filter_by(id=engine_id).first()
    if not engine: return jsonify({"error": "Engine not found"}), 404
    if engine.user_id != owner_user.id: return jsonify({"error": "You are not the owner"}), 403

    try:
        checked_guest_address = w3.to_checksum_address(share_with_address)
    except Exception:
        return jsonify({"error": "Invalid guest public address"}), 400

    guest_user = User.query.filter(User.public_address.ilike(checked_guest_address)).first()
    if not guest_user:
        placeholder_email = f"{checked_guest_address.lower()}@flowork.crypto"
        existing_email = User.query.filter(User.email.ilike(placeholder_email)).first()
        if existing_email:
            guest_user = existing_email
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
            db.session.flush()
            db.session.add(Subscription(id=str(uuid.uuid4()), user_id=guest_user.id, tier="architect"))
            db.session.commit()

    existing_share = EngineShare.query.filter_by(engine_id=engine.id, user_id=guest_user.id).first()

    try:
        if existing_share:
            if role:
                existing_share.role = role
                db.session.commit()

            socketio.emit('shared_engine_updated', {
                'engine_id': engine.id,
                'name': engine.name,
                'role': existing_share.role,
                'owner': owner_user.username
            }, room=str(guest_user.id), namespace='/gui-socket')

            return jsonify({"message": f"Share updated (Current role: {existing_share.role})"}), 200
        else:
            final_role = role if role else 'reader'
            new_share = EngineShare(
                engine_id=engine.id,
                user_id=guest_user.id,
                role=final_role
            )
            db.session.add(new_share)
            db.session.commit()

            socketio.emit('new_shared_engine', {
                'id': engine.id,
                'name': engine.name,
                'status': 'offline',
                'owner': {
                    'username': owner_user.username,
                    'email': owner_user.email
                },
                'shared_at': new_share.shared_at.isoformat() if new_share.shared_at else None
            }, room=str(guest_user.id), namespace='/gui-socket')

            return jsonify({"message": "Engine shared successfully", "share_id": new_share.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error while saving share"}), 500


@user_bp.route('/engines/<string:engine_id>/shares/<string:shared_user_id>', methods=['DELETE'])
@crypto_auth_required
def revoke_share_endpoint(engine_id, shared_user_id):
    owner_user = g.user
    engine = RegisteredEngine.query.filter_by(id=engine_id).first()
    if not engine: return jsonify({"error": "Engine not found"}), 404
    if engine.user_id != owner_user.id: return jsonify({"error": "Unauthorized"}), 403

    share = EngineShare.query.filter_by(engine_id=engine_id, user_id=shared_user_id).first()
    if not share: return jsonify({"error": "Share not found"}), 404

    try:
        db.session.delete(share)
        db.session.commit()
        socketio.emit('removed_shared_engine', {'engine_id': engine_id}, room=str(shared_user_id), namespace='/gui-socket')
        return jsonify({"message": "Share revoked successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@user_bp.route("/engines/<engine_id>/reset-token", methods=["POST"])
@crypto_auth_required
def reset_engine_token_legacy(engine_id):
    current_user = g.user
    engine = RegisteredEngine.query.filter_by(id=engine_id, user_id=current_user.id).first()
    if not engine: return jsonify({"error": "Engine not found or permission denied."}), 404

    new_plaintext_token = f"dev_engine_{secrets.token_hex(16)}"
    token_hash = generate_password_hash(new_plaintext_token, method="pbkdf2:sha256")
    engine.engine_token_hash = token_hash
    db.session.commit()

    return jsonify({
        "message": f"Token for engine '{engine.name}' has been reset.",
        "token": new_plaintext_token,
        "engine_id": engine.id,
    }), 200


@user_bp.route("/engines/<string:engine_id>/update-name", methods=["PUT"])
@crypto_auth_required
def update_engine_name_legacy(engine_id):
    current_user = g.user
    engine = RegisteredEngine.query.filter_by(id=engine_id, user_id=current_user.id).first()
    if not engine: return jsonify({"error": "Engine not found"}), 404

    data = request.get_json()
    new_name = data.get("name")
    if not new_name: return jsonify({"error": "New name is required."}), 400

    engine.name = new_name
    db.session.commit()

    status = 'offline'
    with engine_manager.engine_last_seen_lock:
        if (time.time() - engine_manager.engine_last_seen_cache.get(engine_id, 0)) < 120 :
            status = 'online'

    from ..sockets import _broadcast_to_engine_viewers
    try:
        _broadcast_to_engine_viewers(engine_id, 'engine_status_update', {
             'engine_id': engine_id,
             'name': new_name,
             'status': status,
             'vitals': None
        })
    except Exception:
        pass

    return jsonify({"message": f"Engine '{new_name}' updated successfully."}), 200


@user_bp.route('/shared-engines', methods=['GET'])
@crypto_auth_required
def get_shared_engines():
    current_user = g.user

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
            if not engine: continue
            owner = engine.owner
            if not owner: continue

            last_seen_timestamp_mem = last_seen_snapshot.get(engine.id, 0)
            last_seen_timestamp_db = 0
            if engine.last_seen:
                 last_seen_timestamp_db = engine.last_seen.replace(tzinfo=datetime.timezone.utc).timestamp()

            effective_last_seen = max(last_seen_timestamp_mem, last_seen_timestamp_db)
            status = 'offline'
            if (current_time - effective_last_seen) < ONLINE_THRESHOLD_SECONDS:
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
        current_app.logger.error(f"Error fetching shared engines: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch shared engine list."}), 500
