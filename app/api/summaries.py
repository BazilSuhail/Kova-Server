from flask import Blueprint, request
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.summary_service import create_summary, get_summaries, update_summary, delete_summary
from app.utils.api_response import api_response
from app.utils.pdf_to_text import extract_pdf_text

summaries_bp = Blueprint("summaries", __name__)

@summaries_bp.route("/create", methods=["POST"])
@jwt_required()
def create():
    try:
        user_id = get_jwt_identity()

        if 'file' not in request.files:
            return api_response({"message": "PDF file is required"}, 400)

        file = request.files['file']
        if file.filename == '':
            return api_response({"message": "No selected file"}, 400)

        # Extract text from uploaded PDF
        extracted_text = extract_pdf_text(file)

        # Prepare minimal data to pass to service layer
        result = create_summary(
            db=summaries_bp.db,
            user_id=user_id,
            extracted_text=extracted_text,
            original_filename=file.filename
        )

        return api_response(result, 201)

    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)


@summaries_bp.route("/", methods=["GET"])
@jwt_required()
def list_summaries():
    try:
        user_id = get_jwt_identity()
        summaries = get_summaries(summaries_bp.db, user_id)  # Use summaries_bp.db
        return api_response(summaries, 200)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@summaries_bp.route("/<summary_id>", methods=["PUT"])
@jwt_required()
def update(summary_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        if update_summary(summaries_bp.db, summary_id, user_id, data):  # Use summaries_bp.db
            return api_response({"message": "Summary updated"}, 200)
        return api_response({"message": "Summary not found"}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)

@summaries_bp.route("/<summary_id>", methods=["DELETE"])
@jwt_required()
def delete(summary_id):
    try:
        user_id = get_jwt_identity()
        if delete_summary(summaries_bp.db, summary_id, user_id):  # Use summaries_bp.db
            return api_response({"message": "Summary deleted"}, 200)
        return api_response({"message": "Summary not found"}, 404)
    except Exception as e:
        return api_response({"message": f"Server error: {str(e)}"}, 500)