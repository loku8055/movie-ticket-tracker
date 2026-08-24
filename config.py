import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STORE_FILE = os.path.join(DATA_DIR, "store.json")

PORT = int(os.environ.get("PORT", 3001))
DEFAULT_POLL_INTERVAL_SEC = 15

# Twilio Voice Call Configuration (Optional Env Fallbacks)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
TWILIO_TO_NUMBER = os.environ.get("TWILIO_TO_NUMBER", "")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

