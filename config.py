from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Access the environment variables in your code
PORT = 3978
APP_ID = os.getenv("MicrosoftAppId")
APP_PASSWORD = os.getenv("MicrosoftAppPassword")
tenant_id = os.getenv("tenant_id")
Todo_PollingIntervalSeconds = float(os.getenv("Todo_PollingIntervalSeconds"))
Todo_BotsTaskFolder = os.getenv("Todo_BotsTaskFolder")
serpapi_api_key = os.getenv("SERPER_API_KEY")
