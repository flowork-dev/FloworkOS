########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\shares.py total lines 255 
########################################################################

from flask import Blueprint, jsonify, g, request, current_app
import logging
import secrets
import uuid  # [FIX] Wajib import uuid di sini biar gak error pas bikin user baru
from app.extensions import db, socketio
from app.models import User, RegisteredEngine, EngineShare
from app.helpers import crypto_auth_required, get_request_data
from web3.auto import w3
from werkzeug.security import generate_password_hash

shares_bp = Blueprint('shares_bp', __name__)

@shares_bp.route('/engines/<string:engine_id>/shares', methods=['GET'])
@crypto_auth_required
def get_shares_list(engine_id):
    current_user = g.user

    engine = RegisteredEngine.query.filter_by(id=engine_id).first()
    if not engine:
        return jsonify({"error": "Engine not found"}), 404

    if engine.user_id != current_user.id:
         return jsonify({"error": "Unauthorized. Only owner can view share list."}), 403

    shares = EngineShare.query.filter_by(engine_id=engine_id).all()

    result = []
    for s in shares:
        if not s.user: continue
        result.append({
            "user_id": s.user_id,
            "engine_id": s.engine_id,
            "username": s.user.username,
            "email": s.user.email,
            "public_address": s.user.public_address, # Useful for UI display
            "role": s.role,
            "shared_at": s.shared_at.isoformat() if s.shared_at else None
        })

    return jsonify(result)


@shares_bp.route('/create', methods=['POST'])
@crypto_auth_required
def create_share():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    engine_id_str = data.get('engine_id')
    share_with_address = data.get('user_id')
    if not share_with_address:
         share_with_address = data.get('share_with_address')

    role = data.get('role')

    if not engine_id_str or not share_with_address:
        return jsonify({"error": "engine_id and user_id (address) are required"}), 400

    if role and role not in ['viewer', 'editor', 'admin', 'runner']:
        return jsonify({"error": "Invalid role."}), 400

    owner_user = g.user
    if not owner_user:
        current_app.logger.error(f"[Shares] No authenticated user (g.user) in context.")
        return jsonify({"error": "Authentication context not found"}), 500

    engine = RegisteredEngine.query.filter_by(id=engine_id_str).first()
    if not engine:
        return jsonify({"error": "Engine not found"}), 404

    if engine.user_id != owner_user.id:
        current_app.logger.warning(f"[AuthZ] DENIED: User {owner_user.public_address} tried to share engine {engine_id_str} which they do not own.")
        return jsonify({"error": "You are not the owner of this engine"}), 403

    try:
        checked_guest_address = w3.to_checksum_address(share_with_address)
    except Exception:
        return jsonify({"error": "Invalid guest public address format"}), 400

    guest_user = User.query.filter(User.public_address.ilike(checked_guest_address)).first()

    if not guest_user:
        current_app.logger.info(f"[Shares] Creating new user record for guest: {checked_guest_address}")
        placeholder_email = f"{checked_guest_address.lower()}@flowork.crypto"

        email_exists = User.query.filter(User.email.ilike(placeholder_email)).first()

        if email_exists:
            guest_user = email_exists
        else:
            new_user_id = str(uuid.uuid4())
            guest_user = User(
                id=new_user_id,
                username=checked_guest_address,
                email=placeholder_email,
                password_hash=generate_password_hash(secrets.token_urlsafe(32), method="pbkdf2:sha256"),
                status="active",
                public_address=checked_guest_address
            )
            db.session.add(guest_user)
            try:
                db.session.flush()
                from app.models import Subscription
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
            if role:
                current_app.logger.info(f"[Shares] Updating role for {checked_guest_address} on engine {engine_id_str} to '{role}'")
                existing_share.role = role
                db.session.commit()
            else:
                current_app.logger.info(f"[Shares] Re-share requested but NO ROLE provided. Keeping: {existing_share.role}")

            socketio.emit(
                'force_refresh_auth_list',
                {'message': f'Share role updated for {checked_guest_address}'},
                room=engine.id,
                namespace='/engine-socket'
            )

            socketio.emit(
                'shared_engine_updated',
                {
                    'engine_id': engine.id,
                    'name': engine.name,
                    'role': existing_share.role,
                    'owner': owner_user.username
                },
                room=str(guest_user.id),
                namespace='/gui-socket'
            )

            return jsonify({"message": "Share role updated successfully"}), 200
        else:
            final_role = role if role else 'reader'
            current_app.logger.info(f"[Shares] Creating new share for {checked_guest_address} on engine {engine_id_str} with role '{final_role}'")
            new_share = EngineShare(
                engine_id=engine.id,
                user_id=guest_user.id,
                role=final_role
            )
            db.session.add(new_share)
            db.session.commit()

            socketio.emit(
                'force_refresh_auth_list',
                {'message': f'User {checked_guest_address} added to shares'},
                room=engine.id,
                namespace='/engine-socket'
            )

            socketio.emit(
                'new_shared_engine',
                {
                    'id': engine.id,
                    'name': engine.name,
                    'status': 'offline', # Default status
                    'owner': {
                        'username': owner_user.username,
                        'email': owner_user.email
                    },
                    'shared_at': new_share.shared_at.isoformat() if new_share.shared_at else None
                },
                room=str(guest_user.id),
                namespace='/gui-socket'
            )

            return jsonify({"message": "Engine shared successfully", "share_id": new_share.id}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Shares] Error creating/updating share: {e}", exc_info=True)
        return jsonify({"error": "Database error while saving share"}), 500

@shares_bp.route('/delete', methods=['POST'])
@crypto_auth_required
def delete_share():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    share_id = data.get('share_id')
    engine_id = data.get('engine_id')
    target_user_id = data.get('user_id')

    owner_user = g.user
    if not owner_user:
        current_app.logger.error(f"[Shares] No authenticated user (g.user) in context for delete.")
        return jsonify({"error": "Authentication context not found"}), 500

    share = None
    if share_id:
        share = EngineShare.query.get(share_id)
    elif engine_id and target_user_id:
        share = EngineShare.query.filter_by(engine_id=engine_id, user_id=target_user_id).first()

    if not share:
        return jsonify({"error": "Share record not found"}), 404

    engine = RegisteredEngine.query.get(share.engine_id)
    if not engine:
        current_app.logger.error(f"[Shares] Share {share.id} references non-existent engine {share.engine_id}")
        return jsonify({"error": "Associated engine not found"}), 500

    if engine.user_id != owner_user.id:
        current_app.logger.warning(f"[AuthZ] DENIED: User {owner_user.public_address} tried to delete share for engine {engine.id} which they do not own.")
        return jsonify({"error": "You are not the owner of this engine"}), 403

    try:
        engine_id_str = engine.id
        user_id_revoked = share.user_id
        user_address_revoked = share.user.public_address if share.user else "Unknown"

        db.session.delete(share)
        db.session.commit()

        current_app.logger.info(f"[Shares] Share (User: {user_address_revoked}) deleted from engine {engine_id_str} by owner.")

        socketio.emit(
            'force_refresh_auth_list',
            {'message': f'User {user_address_revoked} was removed from shares'},
            room=engine_id_str,
            namespace='/engine-socket'
        )

        socketio.emit(
            'removed_shared_engine',
            {'engine_id': engine_id_str},
            room=str(user_id_revoked),
            namespace='/gui-socket'
        )

        current_app.logger.info(f"Sent revoke notifications.")
        return jsonify({"message": "Share deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[Shares] Error deleting share: {e}", exc_info=True)
        return jsonify({"error": "Database error while deleting share"}), 500
