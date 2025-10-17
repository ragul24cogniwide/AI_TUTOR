import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    )

def get_deployment_name():
    return os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")



