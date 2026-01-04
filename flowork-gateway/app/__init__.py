########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\__init__.py total lines 228 
########################################################################

import logging
import os
import sys
from flask import Flask, jsonify, request, send_from_directory, make_response
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
        logging.getLogger(__name__).critical( f"[FATAL STARTUP] Environment guard failed: {e}", exc_info=True )

    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            response.headers.add("Access-Control-Allow-Private-Network", "true")
            return response

    @app.after_request
    def add_pna_header(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        fallback_db = f"sqlite:////app/data/gateway.db"
        print(f"[Startup Warning] SQLALCHEMY_DATABASE_URI missing! Using fallback: {fallback_db}")
        app.config["SQLALCHEMY_DATABASE_URI"] = fallback_db

    app.logger = root_logger
    app.logger.info("[Startup] Initializing core services...")

    allowed_origins = [
        "https://flowork.cloud",
        "https://api.flowork.cloud",
        "https://flowork.pages.dev",
        "https://test1.flowork.cloud",
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173"
    ]
    env_socket_url = os.getenv("SOCKET_URL")
    if env_socket_url: allowed_origins.append(env_socket_url)

    env_cors = app.config.get("CORS_ORIGINS")
    if env_cors and isinstance(env_cors, str) and env_cors != "*":
        extra_origins = [o.strip() for o in env_cors.split(",")]
        allowed_origins.extend(extra_origins)

    CORS(app, origins=allowed_origins, supports_credentials=True)

    gateway_db.init_app(app)
    migrate.init_app(app, gateway_db)

    with app.app_context():
        try: init_pragma(app, gateway_db)
        except Exception as e: app.logger.error(f"[Startup] PRAGMA failed: {e}")
        register_metrics(app)
        limiter.init_app(app)
        db_router.init_app(app)
        init_drain_state(app)
        socketio.init_app( app, async_mode='gevent', cors_allowed_origins="*", path='/api/socket.io' )

    base_apps_path = os.getenv("APPS_DIRECTORY")
    if not base_apps_path:
        if os.path.exists("/app/app"): base_apps_path = "/app/app"
        elif os.path.exists(os.path.join(os.getcwd(), "..", "app")): base_apps_path = os.path.abspath(os.path.join(os.getcwd(), "..", "app"))
        else: base_apps_path = os.path.join(os.getcwd(), "app")

    app.logger.info(f"[StaticServe] Mounting FLAT components from: {base_apps_path}")

    @app.route('/api/components/<string:component_id>/<path:filename>')
    def serve_flowork_components_flat(component_id, filename):
        if ".." in filename or ".." in component_id: return jsonify({"error": "Security Alert"}), 400
        target_dir = os.path.join(base_apps_path, component_id)
        return send_from_directory(target_dir, filename)

    @app.route('/api/components/<string:c_type>/<string:c_id>/<path:fname>')
    def serve_flowork_components_legacy(c_type, c_id, fname):
        return serve_flowork_components_flat(c_id, fname)

    @app.route('/api/v1/components/<string:c_type>/<string:c_id>/assets/<path:filename>')
    def serve_flowork_components_v1(c_type, c_id, filename):
        """
        [MATA-MATA FIX] Serve assets via V1 path for backward compatibility.
        """
        if ".." in filename or ".." in c_id: return jsonify({"error": "Security Alert"}), 400
        target_dir = os.path.join(base_apps_path, c_id)
        if not os.path.exists(os.path.join(target_dir, filename)):
            public_path = os.path.join(target_dir, "public", filename)
            if os.path.exists(public_path):
                return send_from_directory(os.path.join(target_dir, "public"), filename)
            return jsonify({"error": "Asset not found"}), 404
        return send_from_directory(target_dir, filename)

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

    app.logger.info("[Startup] Flowork Gateway blueprints registered.")
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
        try: init_rl_schema()
        except Exception as e: app.logger.error(f"[Startup] RateLimiter Schema Init Failed: {e}")

    USER_RATE = float(os.getenv("USER_RATE", "5"))
    USER_BURST = float(os.getenv("USER_BURST", "20"))
    ENGINE_RATE = float(os.getenv("ENGINE_RATE", "20"))
    ENGINE_BURST = float(os.getenv("ENGINE_BURST", "100"))

    @app.before_request
    def _apply_rl():
        if request.path.startswith("/health") or request.path.startswith("/metrics"): return
        if request.path.startswith("/api/components/"): return
        if request.path.startswith("/api/v1/components/"): return
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
                    return resp

    app.logger.info("[Startup] Flowork Gateway initialized successfully.")
    return app
