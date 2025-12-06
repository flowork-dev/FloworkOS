########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\capsules\registry.py total lines 75 
########################################################################

from __future__ import annotations
from typing import Dict, Any, List, Optional
import os, json
from pathlib import Path
from .schema import validate_capsule

CAPSULE_DIR = Path(os.getenv("CAPSULE_DIR", r"C:\FLOWORK\capsules")).resolve()

def _sanitize_capsule_id(capsule_id: str) -> str:
    safe = "".join(ch for ch in capsule_id if ch.isalnum() or ch in ("-", "_", "."))
    if not safe:
        raise ValueError("Invalid capsule_id")
    return safe

def _capsule_path(capsule_id: str) -> Path:
    cid = _sanitize_capsule_id(capsule_id)
    CAPSULE_DIR.mkdir(parents=True, exist_ok=True)
    return CAPSULE_DIR / f"{cid}.json"

def list_capsules() -> List[Dict[str, Any]]:
    CAPSULE_DIR.mkdir(parents=True, exist_ok=True)
    out: List[Dict[str, Any]] = []
    for p in CAPSULE_DIR.glob("*.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            obj["_file"] = str(p)
            out.append(obj)
        except Exception:
            continue
    return out

def get_capsule(capsule_id: str) -> Dict[str, Any]:
    p = _capsule_path(capsule_id)
    if not p.exists():
        raise FileNotFoundError("Capsule not found")
    return json.loads(p.read_text(encoding="utf-8"))

def install_capsule(capsule: Dict[str, Any]) -> Dict[str, Any]:
    validate_capsule(capsule)
    p = _capsule_path(capsule["capsule_id"])
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(capsule, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    capsule["_file"] = str(p)
    return capsule

def export_capsule(capsule_id: str) -> Dict[str, Any]:
    return get_capsule(capsule_id)

def remix_capsule(base_capsule_id: str, new_capsule_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:

    base = get_capsule(base_capsule_id)
    out = dict(base)
    out["capsule_id"] = new_capsule_id

    for k, v in patch.items():
        if k == "fac_template" and isinstance(v, dict):
            ft = dict(out.get("fac_template", {}))
            for fk, fv in v.items():
                if fk == "capabilities" and isinstance(fv, list):
                    ft["capabilities"] = fv
                else:
                    ft[fk] = fv
            out["fac_template"] = ft
        else:
            out[k] = v

    validate_capsule(out)
    return install_capsule(out)
