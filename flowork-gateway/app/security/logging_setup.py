########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\security\logging_setup.py total lines 114 
########################################################################

from __future__ import annotations
import logging, json, time, os, re, sys
from typing import Dict, Any

_PATTERNS = [
    re.compile(r'(sk-[a-zA-Z0-9-]{30,})'),
    re.compile(r'([A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})'),
    re.compile(r'([A-Fa-f0-9]{64,})'),
    re.compile(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'),
    re.compile(r'(fk-admin-[a-zA-Z0-9_-]{40,})'),
    re.compile(r'(fk-eng-[a-zA-Z0-9_-]{60,})'),
]

class RedactionFilter(logging.Filter):

    def __init__(self, enable: bool = True):
        super().__init__()
        self.enable = enable

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.enable:
            return True

        msg = record.getMessage()

        for rx in _PATTERNS:
            msg = rx.sub("[REDACTED]", msg)

        record.msg = msg
        record.args = ()

        if hasattr(record, "fac") and record.fac:
            record.fac_summary = fac_summary(record.fac)
            del record.fac

        return True

class JsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "ts": round(record.created, 3),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }


        safe_extras = ("event", "session_id", "engine_id", "user_id", "fac_summary", "code", "path")
        for k in safe_extras:
            if hasattr(record, k):
                obj[k] = getattr(record, k)

        if record.exc_info:
            obj["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

def configure_logging() -> None:

    lvl = os.getenv("LOG_LEVEL", "info").upper()
    fmt = os.getenv("LOG_FORMAT", "json").lower()
    redact = os.getenv("LOG_SENSITIVE", "0") not in ("1", "true", "yes", "on")

    root = logging.getLogger()

    log_level_int = getattr(logging, lvl, logging.INFO)
    root.setLevel(log_level_int)

    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RedactionFilter(enable=redact))

    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        ))

    root.addHandler(handler)

    if os.getenv("ENV", "production").lower() == "production":
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("socketio").setLevel(logging.WARNING)
        logging.getLogger("engineio").setLevel(logging.WARNING)

    root.info(f"Logging configured. Level: {lvl}, Format: {fmt}, Redaction: {redact}")


def fac_summary(fac: Dict[str, Any]) -> Dict[str, Any]:

    if not isinstance(fac, dict):
        return {"_": "invalid_fac_not_dict"}
    try:
        return {
            "agent_id": fac.get("agent_id"),
            "role": fac.get("role"),
            "engine_id": fac.get("engine_id"),
            "owner_id": fac.get("owner_id"),
            "namespace": fac.get("namespace"),
            "budget_gas": fac.get("budget_gas"),
        }
    except Exception:
        return {"_": "fac_summary_error"}
