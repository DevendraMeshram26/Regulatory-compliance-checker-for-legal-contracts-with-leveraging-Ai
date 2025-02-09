import requests
import json
from app.utils.logger import logger
from config import Config

def analyze_key_clauses_with_groqcloud(text: str) -> dict:
    try:
        # Define the messages and request body
        messages = [
            {
                "role": "system",
                "content": """You are a contract analyzer. Extract the key clauses from the provided contract and return them in a JSON-like format, strictly adhering to this structure:

                {
                  "clauses": [
                    {
                      "clause": "<clause title>",
                      "description": "<clause description>"
                    }
                  ]
                }

                Ensure the output is valid JSON. Avoid unnecessary information or deviations from this structure."""
            },
            {
                "role": "user",
                "content": text
            }
        ]

        data = {
            "messages": messages,
            "model": "llama3-8b-8192",
            "temperature": 0,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.GROQCLOUD_API_KEY}"
        }

        # Make the API request
        response = requests.post(Config.GROQCLOUD_API_URL, data=json.dumps(data), headers=headers)

        if response.status_code != 200:
            return {"error": f"GroqCloud API Error: {response.status_code} - {response.text}"}

        # Parse the response
        response_data = response.json()
        result_content = response_data["choices"][0]["message"]["content"]

        # Try to load JSON
        try:
            result_json = json.loads(result_content)
            return result_json
        except json.JSONDecodeError as json_err:
            return {"error": f"Invalid JSON received: {str(json_err)}", "content": result_content}

    except requests.exceptions.RequestException as req_err:
        return {"error": f"Request error: {str(req_err)}"}
    except Exception as e:
        return {"error": f"Exception during processing: {str(e)}"}