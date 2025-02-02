import requests
from config import Config

class SlackService:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_alert(self, message: str):
        payload = {
            "text": message
        }
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()  # Raise an error for bad responses
        except requests.exceptions.RequestException as e:
            print(f"Error sending Slack alert: {e}") 