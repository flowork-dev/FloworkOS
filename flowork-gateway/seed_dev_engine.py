########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\seed_dev_engine.py total lines 126 
########################################################################

import os
import sys
import uuid
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
import secrets

try:
    from eth_account import Account
except ImportError:
    print("[ERROR] 'eth_account' library not found.")
    print("[ERROR] Please add 'eth_account' to flowork-gateway/requirements.txt")
    sys.exit(1)


def seed_default_engine(db, User, RegisteredEngine):
    """
    (Indonesia Hardcode) Fungsi ini memastikan Engine Default selalu terdaftar di Database
    agar Core bisa langsung connect tanpa manual setup.
    """

    print("--- Flowork Gateway Development Engine Seeder (Smart Fix) ---")

    try:
        engine_id = os.environ.get("FLOWORK_ENGINE_ID")
        engine_token = os.environ.get("FLOWORK_ENGINE_TOKEN")
        private_key = os.environ.get("ENGINE_OWNER_PRIVATE_KEY")

        default_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "dev@flowork.local")

        if not engine_id or not engine_token:
            print("[ERROR] FLOWORK_ENGINE_ID or FLOWORK_ENGINE_TOKEN not set in .env. Skipping seed.")
            return

        if not private_key:
            print("[ERROR] ENGINE_OWNER_PRIVATE_KEY not set in .env. Cannot match user. Skipping seed.")
            return

        try:
            if not private_key.startswith("0x"):
                pk_for_account = "0x" + private_key
            else:
                pk_for_account = private_key

            acct = Account.from_key(pk_for_account)
            public_address = acct.address
            print(f"[INFO] Target Public Address from .env: {public_address}")
        except Exception as e:
            print(f"[ERROR] Invalid ENGINE_OWNER_PRIVATE_KEY in .env: {e}. Skipping seed.")
            return

        user = User.query.filter(db.func.lower(User.public_address) == db.func.lower(public_address)).first()

        if not user:
            print(f"[WARN] User with public_address '{public_address}' NOT FOUND in DB.")
            print(f"[FIX] Creating Recovery User for this Engine now...")

            try:
                dummy_pw = secrets.token_urlsafe(16)
                hashed_pw = generate_password_hash(dummy_pw, method="pbkdf2:sha256")

                new_user = User(
                    id=str(uuid.uuid4()),
                    username="EngineOwner_Auto",
                    email=f"auto_owner_{public_address[:8]}@flowork.local", # Email unik
                    password_hash=hashed_pw,
                    status="active",
                    public_address=public_address
                )
                db.session.add(new_user)
                db.session.flush() # Dapatkan ID user baru
                user = new_user
                print(f"[SUCCESS] Created new owner user: {user.id}")
            except Exception as user_e:
                print(f"[CRITICAL] Failed to create recovery user: {user_e}")
                return

        try:
            ghost_engines = RegisteredEngine.query.filter(RegisteredEngine.id != engine_id).all()
            if ghost_engines:
                for ghost in ghost_engines:
                    print(f"[INFO] Deleting ghost engine: {ghost.id}")
                    db.session.delete(ghost)
                db.session.commit()
        except Exception as e:
            print(f"[WARN] Error cleaning ghost engines: {e}")
            db.session.rollback()

        engine = RegisteredEngine.query.filter_by(id=engine_id).first()
        token_hash = generate_password_hash(engine_token, method="pbkdf2:sha256")

        if not engine:
            print(f"[INFO] Registering NEW Engine '{engine_id}'...")
            new_engine = RegisteredEngine(
                id=engine_id,
                user_id=user.id,
                engine_token_hash=token_hash,
                name="Primary Dev Engine",
                status="offline"
            )
            db.session.add(new_engine)
        else:
            print(f"[INFO] Updating EXISTING Engine '{engine_id}' credentials...")
            engine.engine_token_hash = token_hash
            engine.user_id = user.id # Pastikan kepemilikan benar
            db.session.add(engine)

        db.session.commit()
        print(f"--- SUCCESS: Engine '{engine_id}' seeded/updated for user '{user.username}'. Ready to connect. ---")

    except SQLAlchemyError as e:
        print(f"[ERROR] Database error during engine seeding: {e}")
        db.session.rollback()
    except Exception as e:
        print(f"[ERROR] Unexpected error during engine seeding: {e}")
        db.session.rollback()

if __name__ == "__main__":
    print("[WARN] Run this via create_admin.py or inside Flask context.")
