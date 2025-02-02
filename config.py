import os
from dotenv import load_dotenv

load_dotenv()  # Ensure this is called to load the .env file

class Config:
    GROQCLOUD_API_KEY = os.getenv("GROQCLOUD_API_KEY")
    GROQCLOUD_API_URL = os.getenv("GROQCLOUD_API_URL") 
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    def __init__(self):
        print("GROQCLOUD_API_KEY:", self.GROQCLOUD_API_KEY)  # Debugging line
        print("GROQCLOUD_API_URL:", self.GROQCLOUD_API_URL)  # Debugging line
      