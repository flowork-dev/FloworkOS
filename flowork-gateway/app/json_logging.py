########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\json_logging.py total lines 93 
########################################################################

import logging
try:
    get_json_logger
except NameError:
    import os, sys, json
    from datetime import datetime, timezone

    class _MinimalJSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "loggerName": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                payload["exc_info"] = self.formatException(record.exc_info)
            if record.stack_info:
                payload["stack_info"] = record.stack_info
            return json.dumps(payload, ensure_ascii=False)

    def _parse_level(v):
        if isinstance(v, int): return v
        if not v: return logging.INFO
        return getattr(logging, str(v).upper(), logging.INFO)

    def get_json_logger(name: str | None = None, level: int | str | None = None) -> logging.Logger:
        lvl = _parse_level(os.getenv("FLOWORK_LOG_LEVEL") or os.getenv("LOG_LEVEL") or level)
        name = name or os.getenv("FLOWORK_LOGGER_NAME") or "flowork-gateway"
        log = logging.getLogger(name)
        log.setLevel(lvl)
        if not any(isinstance(h, logging.StreamHandler) for h in log.handlers):
            handler = logging.StreamHandler(stream=sys.stdout)
            handler.setFormatter(_MinimalJSONFormatter())
            log.addHandler(handler)
        log.propagate = False
        log.info("JSON logging configured. Level set to %s.", logging.getLevelName(lvl))
        return log

try:
    InterceptHandler
except NameError:
    class InterceptHandler(logging.Handler):
        def __init__(self, target_logger_name: str = "flowork-gateway"):
            super().__init__()
            self._target = get_json_logger(name=target_logger_name)

        def emit(self, record: logging.LogRecord) -> None:
            try:
                self._target.log(
                    record.levelno,
                    record.getMessage(),
                    exc_info=record.exc_info,
                    stack_info=record.stack_info,
                )
            except Exception:
                self.handleError(record)

try:
    setup_logging
except NameError:
    def setup_logging(
        name: str | None = None,
        level: int | str | None = None,
        intercept_libraries: bool = True,
    ) -> logging.Logger:
        log = get_json_logger(name=name, level=level)
        if intercept_libraries:
            handler = InterceptHandler(target_logger_name=log.name)
            targets = (
                "werkzeug",
                "flask.app",
                "sqlalchemy",
                "sqlalchemy.engine",
                "alembic",
                "engineio.server",
                "socketio.server",
            )
            for t in targets:
                lg = logging.getLogger(t)
                if not any(isinstance(h, InterceptHandler) for h in lg.handlers):
                    lg.addHandler(handler)
                lg.propagate = False
        log.info("JSON logging configured. Level set to %s.", logging.getLevelName(log.level))
        return log

logger = get_json_logger()
