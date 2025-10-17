"""Summary routes: upload a PDF, list, edit, delete."""
from __future__ import annotations

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.responses import api_response
from ..services import get_services
from ..utils.pdf_to_text import extract_pdf_text

summaries_bp = Blueprint("summaries", __name__)


@summaries_bp.route("/create", methods=["POST"])
@jwt_required()
def create_summary() -> Response:
    user_id = get_jwt_identity()
    if "file" not in request.files:
        return api_response({"message": "PDF file is required"}, 400)
    file = request.files["file"]
    if file.filename == "":
        return api_response({"message": "No selected file"}, 400)

    # Text extraction stays at the edge: it is I/O on the uploaded bytes.
    extracted_text = extract_pdf_text(file)
    result = get_services().summaries.create(user_id, extracted_text, file.filename)
    return api_response(result, 201)


@summaries_bp.route("/", methods=["GET"])
@jwt_required()
def list_summaries() -> Response:
    summaries = get_services().summaries.list(get_jwt_identity())
    return api_response(summaries, 200)


@summaries_bp.route("/<summary_id>", methods=["PUT"])
@jwt_required()
def update_summary(summary_id: str) -> Response:
    updated = get_services().summaries.update(
        summary_id, get_jwt_identity(), request.get_json()
    )
    if updated:
        return api_response({"message": "Summary updated"}, 200)
    return api_response({"message": "Summary not found"}, 404)


@summaries_bp.route("/<summary_id>", methods=["DELETE"])
@jwt_required()
def delete_summary(summary_id: str) -> Response:
    deleted = get_services().summaries.delete(summary_id, get_jwt_identity())
    if deleted:
        return api_response({"message": "Summary deleted"}, 200)
    return api_response({"message": "Summary not found"}, 404)
