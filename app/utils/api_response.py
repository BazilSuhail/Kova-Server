from flask import jsonify
from bson import ObjectId
from datetime import datetime

def api_response(data, status_code):
    def convert_types(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_types(item) for item in obj]
        return obj
    
    serialized_data = convert_types(data)
    response = jsonify(serialized_data)
    response.status_code = status_code
    return response
# from flask import jsonify

# def api_response(data, status_code):
#     response = jsonify(data)
#     response.status_code = status_code
#     return response