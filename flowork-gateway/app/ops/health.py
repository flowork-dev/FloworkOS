########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\ops\health.py total lines 15 
########################################################################

from flask import Blueprint, jsonify
from .drain import is_draining
bp = Blueprint('health_bp', __name__)
@bp.route('/health', methods=['GET'])
def health_check():

    if is_draining():
        return jsonify(status="draining"), 503
    return jsonify(status="active"), 200
