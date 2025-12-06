########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\capsules\schema.py total lines 53 
########################################################################

from __future__ import annotations
from typing import Dict, Any, List

ALLOWED_CAPABILITIES = {"http.fetch", "fs.read", "agent.run"}

def _require(d: Dict[str, Any], key: str, typ):
    if key not in d:
        raise ValueError(f"Missing field: {key}")
    if not isinstance(d[key], typ):
        raise TypeError(f"Field '{key}' must be {typ}, got {type(d[key])}")

def validate_capsule(capsule: Dict[str, Any]) -> None:
    _require(capsule, "capsule_id", str)
    _require(capsule, "fac_template", dict)

    ft = capsule["fac_template"]
    _require(ft, "role", str)
    _require(ft, "budget_gas", int)
    _require(ft, "capabilities", list)

    for i, cap in enumerate(ft["capabilities"]):
        if not isinstance(cap, dict):
            raise TypeError(f"capabilities[{i}] must be dict")
        _require(cap, "name", str)
        _require(cap, "scope", dict)
        if cap["name"] not in ALLOWED_CAPABILITIES:
            raise ValueError(f"Capability not allowed/known: {cap['name']}")
        if "description" in cap and not isinstance(cap["description"], str):
            raise TypeError("capabilities[].description must be str")

    if "timeline_sample" in capsule:
        if not isinstance(capsule["timeline_sample"], list):
            raise TypeError("timeline_sample must be list")
        for i, ev in enumerate(capsule["timeline_sample"]):
            if not isinstance(ev, dict): raise TypeError(f"timeline_sample[{i}] must be dict")
            if "type" not in ev or "msg" not in ev:
                raise ValueError("timeline_sample entries require 'type' and 'msg'")
            if not isinstance(ev["type"], str) or not isinstance(ev["msg"], str):
                raise TypeError("timeline_sample.type/msg must be str")

    if "example_episode" in capsule and capsule["example_episode"] is not None:
        if not isinstance(capsule["example_episode"], str):
            raise TypeError("example_episode must be str or null")

    if "docs" in capsule and capsule["docs"] is not None:
        if not isinstance(capsule["docs"], str):
            raise TypeError("docs must be str or null")
