from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Access the environment variables in your code
PORT = 3978
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APP_ID = os.getenv("MicrosoftAppId")
APP_PASSWORD = os.getenv("MicrosoftAppPassword")
tenant_id = os.getenv("tenant_id")
Todo_PollingIntervalSeconds = float(os.getenv("Todo_PollingIntervalSeconds"))
Todo_BotsTaskFolder = os.getenv("Todo_BotsTaskFolder")
serpapi_api_key = os.getenv("SERPER_API_KEY")
OFFICE_USER = os.getenv("OFFICE_USER")
LOCAL_MEMORY_FILE_NAME = os.getenv("LOCAL_MEMORY_FILE_NAME")
EMAIL_CACHE_FILE_NAME = os.getenv("EMAIL_CACHE_FILE_NAME")
EMAIL_SIGNATURE_HTML = os.getenv("EMAIL_SIGNATURE_HTML")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = os.getenv("BASE_URL")
