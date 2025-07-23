import requests, json
from ..config import GROQ_API_KEY, GROQ_LLM_URL

def generate_task_fields_from_llm(title, transcript):
    prompt = (
        "You are a task generator. Given a task title and a voice-to-text transcript, "
        "return a JSON object with the fields: description, category, dueDate (YYYY-MM-DD). "
        "Set createdFrom to 'voice'."
    )

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"title: {title}\ntranscript: {transcript}"}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    res = requests.post(GROQ_LLM_URL, json=payload, headers=headers)
    res.raise_for_status()

    try:
        return json.loads(res.json()["choices"][0]["message"]["content"])
    except Exception:
        raise ValueError("LLM response is not valid JSON.")
