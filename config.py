import os
import time
import shutil
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# ============================================
# BASE DIRECTORY SETUP (Works Local & Server)
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# AUTO CREATE DIRECTORIES (Creates silently without errors)
for _dir in [DOWNLOAD_DIR, OUTPUT_DIR, ASSETS_DIR, TEMP_DIR, LOGS_DIR]:
    os.makedirs(_dir, exist_ok=True)

USER_PREFS_FILE = os.path.join(ASSETS_DIR, 'user_preferences.json')
if not os.path.exists(USER_PREFS_FILE):
    with open(USER_PREFS_FILE, 'w') as f:
        f.write('{}')

# ============================================
# TELEGRAM BOT CREDENTIALS (.env)
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Convert to int safely
try:
    API_ID = int(os.getenv("API_ID", 0))
except ValueError:
    API_ID = 0
API_HASH = os.getenv("API_HASH", "")

# ============================================
# PERFORMANCE & CONCURRENCY SYSTEM
# ============================================
MAX_CONCURRENT_TASKS = 3 
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB max pyrogram limit
MAX_DOWNLOAD_SIZE = 2000 * 1024 * 1024  
USE_MEMORY_SESSION = True

# ============================================
# MEMORY MANAGEMENT (SERVER OPTIMIZED)
# ============================================
MAX_MEMORY_MB = 450
SESSION_TIMEOUT_SECONDS = 3600
CLEANUP_INTERVAL = 300
MAX_STORAGE_MB = 400

# ============================================
# SERVER SETTINGS (For keep_alive)
# ============================================
SERVER_PORT = int(os.getenv("PORT", 8080))

# ============================================
# STORAGE MANAGEMENT FUNCTIONS
# ============================================
def get_storage_usage() -> int:
    """Calculate current storage usage in MB"""
    total_size = 0
    for directory in [DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR, ASSETS_DIR]:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for f in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
    return total_size // (1024 * 1024)

def cleanup_temp_files(max_age_seconds: int = 3600):
    """Delete old temp files to keep server cool"""
    current_time = time.time()
    cleaned = 0
    for directory in [DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    age = current_time - os.path.getmtime(filepath)
                    if age > max_age_seconds:
                        try:
                            os.remove(filepath)
                            cleaned += 1
                        except:
                            pass
    return cleaned

def cleanup_all_temp():
    """Force cleanup of all temporary processing directories"""
    for directory in [DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                os.makedirs(directory, exist_ok=True)
            except:
                pass

def validate_config() -> bool:
    """Check if all important .env variables are loaded"""
    if not BOT_TOKEN or not API_ID or not API_HASH:
        print("❌ CONFIG ERROR: Missing BOT_TOKEN, API_ID, or API_HASH in .env file!")
        return False
    print("✅ Configuration validated successfully! Auto-directories created.")
    return True

if __name__ != "__main__":
    validate_config()