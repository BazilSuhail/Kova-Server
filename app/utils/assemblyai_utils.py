from flask import current_app
import requests
import time

def upload_audio(file_stream):
    # Get config values from Flask app context
    assemblyai_api_key = current_app.config['ASSEMBLYAI_API_KEY']
    assemblyai_base_url = "https://api.assemblyai.com/v2"  # or move this to config if it varies
    
    headers = {"authorization": assemblyai_api_key}
    res = requests.post(
        f"{assemblyai_base_url}/upload",
        headers=headers,
        data=file_stream
    )
    res.raise_for_status()
    return res.json()["upload_url"]

def transcribe_audio(audio_url):
    # Get config values from Flask app context
    assemblyai_api_key = current_app.config['ASSEMBLYAI_API_KEY']
    assemblyai_base_url = "https://api.assemblyai.com/v2"  # or move this to config if it varies
    
    headers = {"authorization": assemblyai_api_key}
    trans_req = {"audio_url": audio_url}
    
    trans_resp = requests.post(
        f"{assemblyai_base_url}/transcript",
        json=trans_req,
        headers=headers
    )
    trans_resp.raise_for_status()
    tid = trans_resp.json()["id"]

    while True:
        status_res = requests.get(
            f"{assemblyai_base_url}/transcript/{tid}",
            headers=headers
        ).json()
        
        if status_res["status"] == "completed":
            print(status_res["text"])
            return status_res["text"]
        if status_res["status"] == "error":
            raise Exception("Transcription failed.")
        time.sleep(3)
# import requests, time
# from app.config import ASSEMBLYAI_API_KEY, ASSEMBLYAI_BASE_URL

# def upload_audio(file_stream):
#     headers = {"authorization": ASSEMBLYAI_API_KEY}
#     res = requests.post(f"{ASSEMBLYAI_BASE_URL}/upload", headers=headers, data=file_stream)
#     res.raise_for_status()
#     return res.json()["upload_url"]

# def transcribe_audio(audio_url):
#     headers = {"authorization": ASSEMBLYAI_API_KEY}
#     trans_req = {"audio_url": audio_url}
#     trans_resp = requests.post(f"{ASSEMBLYAI_BASE_URL}/transcript", json=trans_req, headers=headers)
#     trans_resp.raise_for_status()
#     tid = trans_resp.json()["id"]

#     while True:
#         status_res = requests.get(f"{ASSEMBLYAI_BASE_URL}/transcript/{tid}", headers=headers).json()
#         if status_res["status"] == "completed":
#             return status_res["text"]
#         if status_res["status"] == "error":
#             raise Exception("Transcription failed.")
#         time.sleep(3)
