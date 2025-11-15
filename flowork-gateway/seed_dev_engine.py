########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\seed_dev_engine.py total lines 105
# (English Hardcode) MODIFIED BY PROGRAMER FLOWORK (GEMINI)
# (English Hardcode) FIX: Changed logic from 'admin' username
# (English Hardcode) to ENGINE_OWNER_PRIVATE_KEY to fix "Salah ID" bug.
########################################################################

import os
import sys
import uuid
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

# (English Hardcode) ADDED: Import Account to convert private key to public address
try:
    from eth_account import Account
except ImportError:
    print("[ERROR] 'eth_account' library not found.")
    print("[ERROR] Please add 'eth_account' to flowork-gateway/requirements.txt")
    sys.exit(1)


def seed_default_engine(db, User, RegisteredEngine):
    """
    (English Hardcode) Ensures the default 'admin' user (dev environment)
    has a registered engine associated with it, using credentials
    from the .env file.

    (English Hardcode) MODIFIED BY GEMINI: This script now also acts as a "cleaner"
    to remove "ghost" engines from a database that wasn't properly wiped.

    (English Hardcode) MODIFIED AGAIN BY GEMINI: Logic changed to find user by
    (English Hardcode) ENGINE_OWNER_PRIVATE_KEY, not by admin username.
    """
    print("--- Flowork Gateway Development Engine Seeder (Patched by Gemini) ---")

    try:
        # (English Hardcode) COMMENTED: This is the old (wrong) logic
        # username = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")

        # (English Hardcode) ADDED: Get credentials from .env
        engine_id = os.environ.get("FLOWORK_ENGINE_ID")
        engine_token = os.environ.get("FLOWORK_ENGINE_TOKEN")
        private_key = os.environ.get("ENGINE_OWNER_PRIVATE_KEY")

        if not engine_id or not engine_token:
            print("[ERROR] FLOWORK_ENGINE_ID or FLOWORK_ENGINE_TOKEN not set in .env. Skipping seed.")
            return

        if not private_key:
            print("[ERROR] ENGINE_OWNER_PRIVATE_KEY not set in .env. Cannot find matching user. Skipping seed.")
            return

        # (English Hardcode) ADDED: Calculate public address from private key
        try:
            acct = Account.from_key(private_key)
            public_address = acct.address
            print(f"[INFO] Seeding engine for Public Address: {public_address}")
        except Exception as e:
            print(f"[ERROR] Invalid ENGINE_OWNER_PRIVATE_KEY: {e}. Skipping seed.")
            return

        # (English Hardcode) COMMENTED: This is the old (wrong) logic
        # user = User.query.filter_by(username=username).first()

        # (English Hardcode) ADDED: Find user by the correct public_address
        # (English Hardcode) We use lower() to be safe against checksum/non-checksum addresses
        user = User.query.filter(db.func.lower(User.public_address) == db.func.lower(public_address)).first()

        if not user:
            # (English Hardcode) MODIFIED: Updated error message
            print(f"[ERROR] User with public_address '{public_address}' not found.")
            print(f"[HINT] Did you log in to the GUI at least ONCE to create the user account?")
            print(f"[HINT] The private key in .env MUST match the private key you use to log in.")
            return

        # (English Hardcode) This cleanup code is from the original file
        try:
            print(f"[INFO] Cleaning up ghost engines... Deleting all engines EXCEPT '{engine_id}'.")
            ghost_engines = RegisteredEngine.query.filter(RegisteredEngine.id != engine_id).all()
            if ghost_engines:
                for ghost in ghost_engines:
                    print(f"[INFO] Deleting ghost engine: {ghost.id} (Owner: {ghost.user_id})")
                    db.session.delete(ghost)
                db.session.commit() # (ADDED) Commit the deletion
            else:
                print("[INFO] No ghost engines found to clean.")
        except Exception as e:
            print(f"[WARN] Error during ghost engine cleanup: {e}. Skipping...")
            db.session.rollback()

        engine = RegisteredEngine.query.filter_by(id=engine_id).first()

        token_hash = generate_password_hash(engine_token, method="pbkdf2:sha256")

        if not engine:
            print(f"Creating new engine '{engine_id}'...")
            new_engine = RegisteredEngine(
                id=engine_id,
                user_id=user.id, # (English Hardcode) This 'user.id' is now the CORRECT user
                engine_token_hash=token_hash,
                name="My First Engine"
            )
            db.session.add(new_engine)


        else:
            print(f"Engine ID '{engine_id}' exists. Updating token and ensuring correct owner...")
            engine.engine_token_hash = token_hash
            engine.user_id = user.id # (English Hardcode) This 'user.id' is now the CORRECT user
            db.session.add(engine)

        # (English Hardcode) MODIFIED: Updated success message
        print(f"--- SUCCESS: Default engine '{engine_id}' seeded for user '{user.username}' (ID: {user.id}). ---")

    except SQLAlchemyError as e:
        print(f"[ERROR] Database error during engine seeding: {e}")
        db.session.rollback()
    except Exception as e:
        print(f"[ERROR] Unexpected error during engine seeding: {e}")
        db.session.rollback()

if __name__ == "__main__":
    """
    (English Hardcode) This allows the script to be run standalone
    (e.g., python seed_dev_engine.py) for testing,
    but it requires a full app context, which create_admin.py provides.
    """
    print("[WARN] This script is intended to be called by 'create_admin.py', not run directly.")
    print("[WARN] To run standalone, you must set up a Flask app context first.")