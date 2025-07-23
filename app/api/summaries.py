from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.summary_service import create_summary, get_summaries, update_summary, delete_summary
from ..utils import api_response

summaries_bp = Blueprint("summaries", __name__)

@summaries_bp.route("/", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if not data or not "sourceType" in data:
            return api_response({"message": "Source type required"}, 400)
        summary = create_summary(data, user_id)
        return api_response(summary, 201)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@summaries_bp.route("/", methods=["GET"])
@jwt_required()
def list_summaries():
    try:
        user_id = get_jwt_identity()
        summaries = get_summaries(user_id)
        return api_response(summaries, 200)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@summaries_bp.route("/<summary_id>", methods=["PUT"])
@jwt_required()
def update(summary_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if update_summary(summary_id, user_id, data):
            return api_response({"message": "Summary updated"}, 200)
        return api_response({"message": "Summary not found"}, 404)
    except Exception:
        return api_response({"message": "Server error"}, 500)

@summaries_bp.route("/<summary_id>", methods=["DELETE"])
@jwt_required()
def delete(summary_id):
    try:
        user_id = get_jwt_identity()
        if delete_summary(summary_id, user_id):
            return api_response({"message": "Summary deleted"}, 200)
        return api_response({"message": "Summary not found"}, 404)
    except Exception:
        return api_response({"message": "Server error"}, 500)