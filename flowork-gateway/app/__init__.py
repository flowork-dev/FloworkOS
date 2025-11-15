########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\__init__.py total lines 178 
########################################################################

"""
(Roadmap 1.C, 1.E, 2.2, 3.1, 4.1, 4.5, 3.3)
Gateway Application Factory (create_app).
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, jsonify
from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

from app.security.env_guard import guard_runtime, check_strict_env
from app.security.logging_setup import configure_logging

_CONFIG = None
try:
    from config import Config as _RootConfig
    _CONFIG = _RootConfig
except ModuleNotFoundError:
    try:
        from .config import Config as _PkgConfig
        _CONFIG = _PkgConfig
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "[Flowork Gateway] FATAL: Unable to import 'Config'. "
            "Expected either '/app/config.py' or 'app/config.py'. "
            "Check your volume mounts and repository layout."
        ) from e
Config = _CONFIG
from .extensions import db, migrate, socketio
from .extensions import db as gateway_db
from .metrics import register_metrics
from .rl.limiter import RateLimiter
from .db.router import db_router
from .ops.drain import drain_bp, init_drain_state
from .db.pragma import init_pragma
from app.etl.exporter import start_exporter_thread
from .ops.health import bp as health_bp
limiter = RateLimiter()
def _configure_logging():
    """
    (English Hardcode) COMMENTED OUT R9.2: This function is now DEPRECATED.
    (English Hardcode) The new centralized configure_logging() in logging_setup.py handles everything.
    (English Hardcode) We keep the function definition to avoid breaking any potential imports,
    (English Hardcode) but it does nothing.
    """
    pass # (English Hardcode) R9.2: Do nothing.

def create_app(config_class: type = Config):
    """
    Main application factory for Flowork Gateway.
    """
    configure_logging()

    try:
        summary = guard_runtime()
        check_strict_env()

        root_logger = logging.getLogger(__name__)
        root_logger.info("Runtime guard OK. Flowork Gateway Starting...", extra={"event":"startup", **summary})
    except Exception as e:
        logging.getLogger(__name__).critical(
            f"[FATAL STARTUP] Environment guard failed: {e}",
            exc_info=True
        )
        raise e


    app = Flask(__name__)
    app.config.from_object(config_class)

    app.logger = root_logger
    app.logger.info("[Startup] Initializing core services...")

    CORS(app, origins=["https://flowork.cloud", "http://localhost:5173"], supports_credentials=True)
    gateway_db.init_app(app)
    migrate.init_app(app, gateway_db)
    with app.app_context():
        init_pragma(app, gateway_db)
    register_metrics(app)
    limiter.init_app(app)
    db_router.init_app(app)
    init_drain_state(app)
    socketio.init_app(
        app,
        async_mode='gevent',
        cors_allowed_origins="*", # (English Hardcode) TODO: This should use GW_ALLOWED_ORIGINS
        path='/api/socket.io'
    )

    from . import sockets

    from .routes.auth import auth_bp
    from .routes.system import system_bp
    from .routes.cluster import cluster_bp
    from .routes.dispatch import dispatch_bp
    from .ops.chaos import chaos_bp
    from .engine.heartbeat_api import engine_hb_bp
    from .routes.proxy import proxy_bp
    from .routes.user import user_bp
    from .routes.user_state import user_state_bp
    from .routes.presets import presets_bp
    from .routes.workflow_shares import workflow_shares_bp
    from .routes.dashboard import dashboard_bp
    from .routes.agent import agent_bp
    from .routes.capsules import bp as capsules_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(cluster_bp)
    app.register_blueprint(dispatch_bp)
    app.register_blueprint(chaos_bp)
    app.register_blueprint(drain_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(engine_hb_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(user_state_bp)
    app.register_blueprint(presets_bp)
    app.register_blueprint(workflow_shares_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(capsules_bp)
    app.logger.info("[Startup] Flowork Gateway blueprints registered.")
    app.logger.info("[Startup] Initializing ETL Exporter thread.")
    start_exporter_thread(app)


    @app.teardown_appcontext
    def remove_db_session(exception=None):
        """(English Hardcode) Close DB session at the end of the request."""
        gateway_db.session.remove()

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Not Found"}), 404
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Internal server error")
        return jsonify({"error": "Internal Server Error"}), 500
    from app.rl.limiter import init_rl_schema, allow as rl_allow
    with app.app_context():
        app.logger.info("[Startup] Initializing Rate Limiter schema (Roadmap 2.2)...")
        init_rl_schema()
    USER_RATE = float(os.getenv("USER_RATE", "5"))
    USER_BURST = float(os.getenv("USER_BURST", "20"))
    ENGINE_RATE = float(os.getenv("ENGINE_RATE", "20"))
    ENGINE_BURST = float(os.getenv("ENGINE_BURST", "100"))
    @app.before_request
    def _apply_rl():
        if request.path.startswith("/health") or request.path.startswith("/metrics"):
            return
        if "enqueue" in request.path:
            body = (request.get_json(silent=True) or {})
            if body:
                uid = body.get("user_id","anon")
                eid = body.get("engine_id","default")
                ok1, ra1 = rl_allow(f"user:{uid}", USER_RATE, USER_BURST)
                ok2, ra2 = rl_allow(f"engine:{eid}", ENGINE_RATE, ENGINE_BURST)
                if not (ok1 and ok2):
                    retry_after = max(ra1, ra2, 1)
                    resp = jsonify({"error":"rate_limited","retry_after": retry_after})
                    resp.status_code = 429
                    resp.headers["Retry-After"] = str(retry_after)
                    app.logger.warning(
                        f"[RateLimit] 429 for user:{uid} or engine:{eid} on path {request.path}",
                        extra={"event": "rate_limit", "user_id": uid, "engine_id": eid}
                    )
                    return resp
    app.logger.info("[Startup] Flowork Gateway initialized successfully.")
    return app
