########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\routes\capsules.py total lines 61 
########################################################################

from __future__ import annotations
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from app.capsules.registry import list_capsules, get_capsule, install_capsule, export_capsule, remix_capsule
from app.capsules.renderer import fac_from_capsule

bp = Blueprint("capsules", __name__)

@bp.get("/api/v1/capsules")
def api_capsules_list():
    items = list_capsules()
    out = [{
        "capsule_id": it.get("capsule_id"),
        "role": it.get("fac_template", {}).get("role"),
        "budget_gas": it.get("fac_template", {}).get("budget_gas"),
    } for it in items]
    return jsonify({"items": out})

@bp.get("/api/v1/capsules/<capsule_id>")
def api_capsules_get(capsule_id: str):
    obj = get_capsule(capsule_id)
    return jsonify(obj)

@bp.post("/api/v1/capsules")
def api_capsules_install():
    payload: Dict[str, Any] = request.get_json(force=True, silent=False) or {}
    saved = install_capsule(payload)
    return jsonify(saved), 201

@bp.post("/api/v1/capsules/<capsule_id>/remix")
def api_capsules_remix(capsule_id: str):
    req: Dict[str, Any] = request.get_json(force=True, silent=False) or {}
    new_id = req.get("new_capsule_id")
    patch = req.get("patch", {})
    if not new_id or not isinstance(patch, dict):
        return jsonify({"error": "new_capsule_id and patch are required"}), 400
    saved = remix_capsule(capsule_id, new_id, patch)
    return jsonify(saved), 201

@bp.get("/api/v1/capsules/<capsule_id>/export")
def api_capsules_export(capsule_id: str):
    obj = export_capsule(capsule_id)
    return jsonify(obj)

@bp.post("/api/v1/capsules/<capsule_id>/fac-preview")
def api_capsules_fac_preview(capsule_id: str):

    req: Dict[str, Any] = request.get_json(force=True, silent=False) or {}
    user = req.get("user"); engine = req.get("engine")
    if not isinstance(user, dict) or not isinstance(engine, dict):
        return jsonify({"error":"user and engine required"}), 400
    cap = get_capsule(capsule_id)
    fac = fac_from_capsule(user=user, engine=engine, capsule=cap)
    return jsonify(fac)
