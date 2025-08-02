import requests
import json
from flask import current_app

def make_subTasks_from_tasks_description(task_description):
    """
    Breaks down a task description into actionable sub-tasks using an LLM.

    Args:
        task_description (str): The main task description to be broken down.

    Returns:
        list: A list of 3–8 sub-task strings that comprise the main task.
    Raises:
        ValueError: On request failure or invalid LLM response.
    """
    groq_api_key = current_app.config['GROQ_API_KEY']
    groq_llm_url = current_app.config.get('GROQ_LLM_URL', 'https://api.groq.com/openai/v1/chat/completions')

    prompt = (
        "You are a professional task planner. The user will provide a description of a task, "
        "and your job is to break it down into clear, actionable sub-tasks.\n\n"
        "**Requirements**:\n"
        "1. Analyze the main task and identify logical steps needed to complete it\n"
        "2. Create between 3 and 8 sub-tasks\n"
        "3. Each sub-task should be a complete, actionable item\n"
        "4. Sub-tasks should be ordered logically (what needs to be done first)\n\n"
        "**IMPORTANT**: Respond ONLY with a JSON array of sub-tasks. Do NOT include any explanation, "
        "markdown formatting, or extra text. Return only the JSON array.\n\n"
        "Example:\n"
        "[\n"
        "  \"Research and gather necessary materials\",\n"
        "  \"Create initial draft of the document\",\n"
        "  \"Review and revise content with team\",\n"
        "  \"Finalize and submit completed work\"\n"
        "]"
    )

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": task_description}
        ],
        "max_tokens": 500,
        "temperature": 0.3  # Lower temperature for more focused task breakdown
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

        print("LLM raw response content:", content)  # helpful for debugging

        # Parse LLM output (must be a JSON array of strings)
        subtasks = json.loads(content)

        if not isinstance(subtasks, list) or not all(isinstance(item, str) for item in subtasks):
            raise ValueError("LLM response is not a valid list of sub-tasks")

        if not (3 <= len(subtasks) <= 20):
            raise ValueError("Sub-tasks must contain between 3 and 8 items")

        return subtasks

    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {str(e)}")
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse LLM response: {str(e)}")