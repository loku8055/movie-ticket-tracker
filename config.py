import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STORE_FILE = os.path.join(DATA_DIR, "store.json")

PORT = int(os.environ.get("PORT", 3001))
DEFAULT_POLL_INTERVAL_SEC = 15

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
