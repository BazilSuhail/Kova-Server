import requests
import json
from flask import current_app

def generate_task_fields_from_llm(transcript):
    # Get config values from Flask app context
    groq_api_key = current_app.config['GROQ_API_KEY']
    groq_llm_url = current_app.config.get('GROQ_LLM_URL', 'https://api.groq.com/openai/v1/chat/completions')
    
    prompt = (
        "You are a smart task generator. Given a natural language prompt, extract the user's intention "
        "and create a task object with the following fields:\n"
        "- title: a short general title (auto-generated)\n"
        "- description: a detailed description of 30 to 40 words\n"
        "- category: e.g., work, personal, study, health, etc.\n"
        "- dueDate: infer an appropriate due date in YYYY-MM-DD format based on the prompt\n"
        "- createdFrom: set this to 'auto'\n\n"
        "Respond with a valid JSON object."
    )

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": transcript}
        ],
        "max_tokens": 200,
        "temperature": 0.7,
        "response_format": {"type": "json_object"}  # Ensure JSON response
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
        
        # Parse the JSON content
        result = json.loads(content)
        
        # Validate required fields
        required_fields = ['title', 'description', 'category', 'dueDate', 'createdFrom']
        if not all(field in result for field in required_fields):
            raise ValueError("LLM response missing required fields")
            
        return result
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {str(e)}")
    except (KeyError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to parse LLM response: {str(e)}")
