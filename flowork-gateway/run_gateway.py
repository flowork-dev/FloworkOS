########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\run_gateway.py total lines 59 
########################################################################

import gevent.monkey
gevent.monkey.patch_all()
print("[BOOT] gevent monkey_patch applied.")

import os
from dotenv import load_dotenv

env_candidates = [
    os.environ.get('ENV_FILE_PATH'),
    '/app/.env',           # Standard Docker path
    r'C:\FLOWORK\.env',    # Windows hardcode fallback
    './.env'               # Local relative path
]

env_loaded = False
for path in env_candidates:
    if path and os.path.exists(path):
        load_dotenv(path)
        print(f"[BOOT] .env loaded successfully from: {path}")
        env_loaded = True
        break

if not env_loaded:
    print("[BOOT] WARNING: No .env file found in candidates. Relying on system environment variables.")

from app import create_app, extensions
from app.extensions import socketio
from app.config import Config
from app.globals import globals_instance as GLOBALS

application = create_app(config_class=Config)

@application.before_request
def debug_startup_registry():
    """Memastikan RAM Registry siap sebelum request pertama masuk."""
    if not hasattr(GLOBALS, 'engine_manager'):
        print("[BOOT-CRITICAL] Global Engine Manager is missing from GLOBALS!")

if __name__ == '__main__':
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 8000))

    print(f"[BOOT] Flowork Gateway Engine Starting...")
    print(f"[BOOT] Socket.IO server on {host}:{port} with gevent mode ACTIVE.")

    socketio.run(
        application,
        host=host,
        port=port,
        debug=application.config.get('DEBUG', False),
        allow_unsafe_werkzeug=True,
        log_output=True
    )
