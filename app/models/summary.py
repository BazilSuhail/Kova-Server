from bson import ObjectId

def summary_schema():
    return {
        "summaryId": str(ObjectId()),
        "userId": str,
        "sourceType": str,  # "pdf", "note"
        "originalFileName": str,
        "summaryBullets": [str],
        "createdAt": str
    }