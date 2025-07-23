from flask import jsonify

def api_response(data, status_code):
    response = jsonify(data)
    response.status_code = status_code
    return response