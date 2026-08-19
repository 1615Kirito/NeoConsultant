#API Key, Model Definitions, and other configurations for the MCP system

# config.py

import os

from dotenv import load_dotenv


load_dotenv()

class Settings:
    def __init__(self):
        # Alpha Vantage
        self.alpha_vantage_api_key = os.getenv(
            "ALPHA_VANTAGE_API_KEY",
            ""
        )

        # SEC EDGAR
        self.sec_user_agent = os.getenv(
            "SEC_USER_AGENT",
            "Finsight MCP contact@example.com"
        )

        # LLM / Model
        self.model_name = os.getenv(
            "MODEL_NAME",
            "gpt-5.6"
        )

        self.openai_api_key = os.getenv(
            "OPENAI_API_KEY",
            ""
        )

settings = Settings()