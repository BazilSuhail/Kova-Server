import requests
import json
from flask import current_app

def generate_summary_from_llm(transcript):
    """
    Sends raw PDF text to an LLM to generate a clean bullet-point summary.

    Returns:
        list: A list of 4–9 bullet points summarizing the text.
    Raises:
        ValueError: On request failure or invalid LLM response.
    """
    print("-------ll")

    groq_api_key = current_app.config['GROQ_API_KEY']
    groq_llm_url = current_app.config.get('GROQ_LLM_URL', 'https://api.groq.com/openai/v1/chat/completions')

    prompt = (
        "You are a professional summarizer. The user will provide raw extracted text from a PDF, "
        "which may contain unstructured or verbose content.\n\n"
        "Your job is to carefully read and understand the content, and return a **clean, concise bullet-point summary** "
        "with a minimum of 4 and a maximum of 9 points.\n\n"
        "Each bullet should:\n"
        "- Be clear and self-contained\n"
        "- Use complete sentences\n"
        "- Reflect a distinct point or topic from the content\n\n"
        "Respond with a JSON array of strings. Do not include any text outside the JSON."
    )

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript}
        ],
        "max_tokens": 500,
        "temperature": 0.5,
        "response_format": {"type": "json_object"}  # Ensure valid JSON
    }

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(groq_llm_url, json=payload, headers=headers)
        res.raise_for_status()

        response_data = res.json()
        content = response_data["choices"][0]["message"]["content"]

        # Parse LLM output (must be a JSON array of strings)
        summary_bullets = json.loads(content)

        if not isinstance(summary_bullets, list) or not all(isinstance(item, str) for item in summary_bullets):
            raise ValueError("LLM response is not a valid list of summary bullets")

        if not (4 <= len(summary_bullets) <= 9):
            raise ValueError("Summary must contain between 4 and 9 bullet points")

        return summary_bullets

    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {str(e)}")
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse LLM response: {str(e)}")
