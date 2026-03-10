# config.py - PROFESSIONAL Configuration for Watermark Bot
# COMPLETE FIXED VERSION - All directories auto-created
# ALL FEATURES + ERROR HANDLING + QUEUE SYSTEM

import os
import sys
import time
import shutil
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# ============================================
# BASE DIRECTORY SETUP
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================
# DIRECTORY SETTINGS - ALL DEFINED HERE
# ============================================
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# ============================================
# ALL DIRECTORIES - AUTO CREATE (IMMEDIATELY)
# ============================================
_ALL_DIRS = [DOWNLOAD_DIR, OUTPUT_DIR, ASSETS_DIR, TEMP_DIR, LOGS_DIR]

for _dir in _ALL_DIRS:
    try:
        os.makedirs(_dir, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Could not create directory {_dir}: {e}")

# Create user preferences file
USER_PREFS_FILE = os.path.join(ASSETS_DIR, 'user_preferences.json')
if not os.path.exists(USER_PREFS_FILE):
    try:
        with open(USER_PREFS_FILE, 'w') as f:
            f.write('{}')
    except:
        pass

# ============================================
# TELEGRAM BOT CREDENTIALS (PYROGRAM)
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", 0) or 0)
API_HASH = os.environ.get("API_HASH", "")

# ============================================
# PERFORMANCE & CONCURRENCY SYSTEM (QUEUE)
# ============================================
# Kitni files ek sath process karni hai (aapne 3 kaha tha)
MAX_CONCURRENT_TASKS = 3 

# Agar bot restart ho toh pending list delay dikhane ke liye update interval
QUEUE_UPDATE_INTERVAL = 5 # seconds

# File size limits
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB
MAX_DOWNLOAD_SIZE = 2000 * 1024 * 1024  # 20MB for free tier

# Session settings
SESSION_TIMEOUT = 7200  # 2 hours
USE_MEMORY_SESSION = True

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2

# ============================================
# MEMORY MANAGEMENT (FREE TIER OPTIMIZED)
# ============================================
MAX_MEMORY_MB = 450
MAX_USER_SESSIONS = 500
SESSION_TIMEOUT_SECONDS = 3600
CLEANUP_INTERVAL = 300
MAX_STORAGE_MB = 400

# ============================================
# WATERMARK DEFAULTS
# ============================================
DEFAULT_OPACITY = 0.3
DEFAULT_COLOR = 'grey'
DEFAULT_STYLE = 'diagonal'
DEFAULT_FONT_SIZE = 48
DEFAULT_ROTATION = 45

# ============================================
# GAP/SPACING CONTROL FOR GRID/TILES
# ============================================
DEFAULT_GAP = 'medium'
GAP_SMALL = 120
GAP_MEDIUM = 200
GAP_LARGE = 300
GAP_CUSTOM_MIN = 80
GAP_CUSTOM_MAX = 500

# ============================================
# PREMIUM FEATURES DEFAULTS
# ============================================
DEFAULT_SHADOW = False
SHADOW_COLOR = 'black'
DEFAULT_FONT_PATH = os.path.join(ASSETS_DIR, "font.ttf")

# Double Layer
DEFAULT_DOUBLE_LAYER = False
DEFAULT_DOUBLE_LAYER_COLOR = 'black'
DEFAULT_DOUBLE_LAYER_OFFSET = 5

# Gradient Effect
DEFAULT_GRADIENT = False

# ============================================
# POSITION SETTINGS
# ============================================
DEFAULT_POSITION = 'center'

# ============================================
# TILE PATTERN SETTINGS
# ============================================
DEFAULT_TILE_PATTERN = 'grid'

# ============================================
# PROFESSIONAL WATERMARK EFFECTS
# ============================================
DEFAULT_TEXT_OUTLINE = False
DEFAULT_OUTLINE_WIDTH = 2
DEFAULT_TEXT_GLOW = False
DEFAULT_GLOW_INTENSITY = 3

# ============================================
# PDF OPTIMIZATION SETTINGS
# ============================================
COMPRESS_OUTPUT = True
DEDUPLICATE_IMAGES = True
OPTIMIZE_STREAMS = True
COMPRESS_CONTENT_STREAMS = True

# ============================================
# SPEED OPTIMIZATION SETTINGS
# ============================================
USE_FAST_MODE = True
ENABLE_LAYER_CACHE = True
MAX_CACHE_SIZE = 30

# ============================================
# USER PREFERENCES
# ============================================
MAX_USER_PRESETS = 5

# ============================================
# SERVER SETTINGS
# ============================================
SERVER_PORT = int(os.environ.get("PORT", 8080))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(LOGS_DIR, "bot.log")

# ============================================
# STORAGE MANAGEMENT FUNCTIONS
# ============================================
def get_storage_usage() -> int:
    """Get current storage usage in MB"""
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
    """Delete old temp files"""
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
    """Force cleanup all temp files"""
    for directory in [DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                os.makedirs(directory, exist_ok=True)
            except:
                pass

# ============================================
# CONFIGURATION VALIDATION
# ============================================
def validate_config() -> bool:
    """Validate all configuration settings"""
    errors = []
    warnings = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN not set in .env file!")
    if not API_ID:
        errors.append("API_ID not set in .env file!")
    if not API_HASH:
        errors.append("API_HASH not set in .env file!")
        
    for dir_name, dir_path in [
        ("DOWNLOAD", DOWNLOAD_DIR),
        ("OUTPUT", OUTPUT_DIR),
        ("ASSETS", ASSETS_DIR),
        ("TEMP", TEMP_DIR)
    ]:
        if not os.path.exists(dir_path):
            warnings.append(f"{dir_name} directory created: {dir_path}")
    
    if warnings:
        for warning in warnings:
            print(f"⚠️ {warning}")
    if errors:
        for error in errors:
            print(f"❌ CONFIG ERROR: {error}")
        return False
    
    print("=" * 50)
    print("✅ Configuration validated successfully!")
    print("=" * 50)
    print(f"⚡ Max Concurrent Tasks: {MAX_CONCURRENT_TASKS}")
    print(f"💾 Memory Limit: {MAX_MEMORY_MB}MB")
    print("=" * 50)
    
    return True

if __name__ != "__main__":
    validate_config()