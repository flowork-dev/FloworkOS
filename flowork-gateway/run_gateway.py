########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\run_gateway.py total lines 42 
########################################################################

import gevent.monkey
gevent.monkey.patch_all()
print("[BOOT] gevent monkey_patch applied.")

import os
from dotenv import load_dotenv

env_path = os.environ.get('ENV_FILE_PATH', r'C:\FLOWORK\.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"[BOOT] .env loaded from {env_path}")
else:
    print(f"[BOOT] No .env file found at {env_path}, using environment variables.")

from app import create_app, extensions
from app.extensions import socketio
from app.config import Config
from app.globals import globals_instance as GLOBALS


application = create_app(config_class=Config)


if __name__ == '__main__':
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 8000))

    print(f"[BOOT] Starting Socket.IO server on {host}:{port} with gevent...")
    socketio.run(
        application,
        host=host,
        port=port,
        debug=application.config.get('DEBUG', False),
        allow_unsafe_werkzeug=True,
        log_output=True
    )
