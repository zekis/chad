from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Access the environment variables in your code
PORT = 3978
APP_ID = os.getenv("MicrosoftAppId")
APP_PASSWORD = os.getenv("MicrosoftAppPassword")
BASE_URL = os.getenv("BASE_URL")
Todo_PollingIntervalSeconds = float(os.getenv("Todo_PollingIntervalSeconds"))
Todo_BotsTaskFolder = os.getenv("Todo_BotsTaskFolder")
DATA_DIR = "data"

#These are set on startup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
#serpapi_api_key = os.getenv("SERPER_API_KEY")

#EMAIL_SIGNATURE_HTML = os.getenv("EMAIL_SIGNATURE_HTML")


#unique to this bot session, set from command line
TENANT_ID = os.getenv("tenant_id")
USER_ID = ""
FRIENDLY_NAME = ""
OFFICE_USER = os.getenv("OFFICE_USER")

EMAIL_CACHE_FILE_NAME = ""
LOCAL_MEMORY_FILE_NAME = ""

TOOL_CHANNEL = "TOOL_CHANNEL"
TOOL_CHANNEL_IN = ""
TOOL_CHANNEL_OUT = ""

RESET_CONFIG = False

VERBOSE = True

PARAMETER_PUBLISH = {"name": "publish", "description": "set to 'True' to publish as a nicely formatted human readable teams card, 'False' to return the raw data back to AI" }
PROMPT_PUBLISH_TRUE = "Output returned directly to human as a Teams Card, Only if required set publish to 'False'to return the raw output to the AI, "