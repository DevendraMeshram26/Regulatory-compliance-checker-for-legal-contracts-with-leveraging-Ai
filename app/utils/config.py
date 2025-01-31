import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.groqcloud_api_url = os.getenv("GROQCLOUD_API_URL")
        self.groqcloud_api_key = os.getenv("GROQCLOUD_API_KEY")
        
        if not self.groqcloud_api_url or not self.groqcloud_api_key:
            raise ValueError("GroqCloud API URL and API Key must be set in environment variables.") 