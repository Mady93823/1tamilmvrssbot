import os
import logging
from qbittorrentapi import Client
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load Env
load_dotenv()

QBIT_HOST = os.getenv('QBIT_HOST', 'localhost')
QBIT_PORT = int(os.getenv('QBIT_PORT', 8080))
QBIT_USER = os.getenv('QBIT_USER', 'admin')
QBIT_PASS = os.getenv('QBIT_PASS', 'adminadmin')

print(f"Attempting to connect to: http://{QBIT_HOST}:{QBIT_PORT}")
print(f"User: {QBIT_USER}")

try:
    qb = Client(host=QBIT_HOST, port=QBIT_PORT, username=QBIT_USER, password=QBIT_PASS)
    qb.auth_log_in()
    print("✅ Connection Successful!")
    print(f"qBittorrent Version: {qb.app.version}")
    print(f"API Version: {qb.app.web_api_version}")
except Exception as e:
    print(f"❌ Connection Failed!")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Details: {e}")
    import traceback
    traceback.print_exc()
