########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\flowork-gateway\app\__init__.py total lines 201 
########################################################################

import logging
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.security.env_guard import guard_runtime, check_strict_env
from app.security.logging_setup import configure_logging

try:
    from .config import Config
except ImportError:
    try:
        from config import Config
    except ImportError:
        print("[FATAL] Could not load Config class. Check app/config.py")
        sys.exit(1)

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
    pass

def create_app(config_class=Config):
    configure_logging()

    print(f"[Startup] Loading Config. DB URI: {getattr(config_class, 'SQLALCHEMY_DATABASE_URI', 'MISSING')}")

    try:
        summary = guard_runtime()

        root_logger = logging.getLogger(__name__)
        root_logger.info("Runtime guard OK. Flowork Gateway Starting...", extra={"event":"startup", **summary})
    except Exception as e:
        logging.getLogger(__name__).critical(
            f"[FATAL STARTUP] Environment guard failed: {e}",
            exc_info=True
        )

    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        fallback_db = f"sqlite:////app/data/gateway.db"
        print(f"[Startup Warning] SQLALCHEMY_DATABASE_URI missing! Using fallback: {fallback_db}")
        app.config["SQLALCHEMY_DATABASE_URI"] = fallback_db

    app.logger = root_logger
    app.logger.info("[Startup] Initializing core services...")

    allowed_origins = [
        "https://flowork.cloud",
        "https://api.flowork.cloud",      # <--- Wajib buat GUI Widget
        "https://socket.flowork.cloud",   # <--- Wajib buat Tunnel
        "http://localhost:5173",          # Dev Local
        "http://localhost:4173",
        "http://127.0.0.1:5173"
    ]

    env_cors = app.config.get("CORS_ORIGINS")
    if env_cors and isinstance(env_cors, str) and env_cors != "*":
        extra_origins = [o.strip() for o in env_cors.split(",")]
        allowed_origins.extend(extra_origins)

    CORS(app, origins=allowed_origins, supports_credentials=True)

    gateway_db.init_app(app)
    migrate.init_app(app, gateway_db)

    with app.app_context():
        try:
            init_pragma(app, gateway_db)
        except Exception as e:
            app.logger.error(f"[Startup] PRAGMA init failed: {e}")

    register_metrics(app)
    limiter.init_app(app)
    db_router.init_app(app)
    init_drain_state(app)

    socketio.init_app(
        app,
        async_mode='gevent',
        cors_allowed_origins="*",
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
    from .routes.marketplace import marketplace_bp
    from .routes.ai_proxy import ai_proxy_bp

    from .routes.variables import variables_bp
    from .routes.components_proxy import components_bp

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
    app.register_blueprint(marketplace_bp, url_prefix='/api/v1/marketplace')
    app.register_blueprint(ai_proxy_bp, url_prefix='/api/v1/ai')

    app.register_blueprint(variables_bp, url_prefix='/api/v1/variables')
    app.register_blueprint(components_bp, url_prefix='/api/v1/components')

    app.logger.info("[Startup] Flowork Gateway blueprints registered.")
    app.logger.info("[Startup] Initializing ETL Exporter thread.")
    start_exporter_thread(app)

    @app.teardown_appcontext
    def remove_db_session(exception=None):
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
        app.logger.info("[Startup] Initializing Rate Limiter schema...")
        try:
            init_rl_schema()
        except Exception as e:
             app.logger.error(f"[Startup] RateLimiter Schema Init Failed: {e}")

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
                ok2, ra1 = rl_allow(f"engine:{eid}", ENGINE_RATE, ENGINE_BURST)
                if not (ok1 and ok2):
                    retry_after = max(ra1, ra1, 1)
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
