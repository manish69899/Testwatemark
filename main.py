# main.py - PROFESSIONAL Watermark Bot for Telegram (PYROGRAM VERSION)
# IMPROVED: Memory Management, Gap Control, Position, Preview, User Preferences
# FIXED: Background Task Worker Architecture for Bulk Processing (100+ files safely)
# FIXED: Upload Timeout Issue, Safe File Transmission, Auto-Retry

import os
import shutil
import zipfile
import logging
import html
import time
import re
import warnings
import asyncio
import json
import gc
import copy
from typing import Dict, Optional, Set
from concurrent.futures import ThreadPoolExecutor

# Hide unnecessary warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="pypdf")

# PYROGRAM IMPORTS
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, FloodWait, RPCError

# CONFIG & KEYBOARDS
from config import (
    BOT_TOKEN, API_ID, API_HASH, DOWNLOAD_DIR, OUTPUT_DIR, 
    ASSETS_DIR, TEMP_DIR, LOGS_DIR, USE_MEMORY_SESSION, MAX_CONCURRENT_TASKS,
    MAX_MEMORY_MB, MAX_USER_SESSIONS, SESSION_TIMEOUT_SECONDS,
    CLEANUP_INTERVAL, MAX_STORAGE_MB, MAX_DOWNLOAD_SIZE,
    USER_PREFS_FILE, GAP_SMALL, GAP_MEDIUM, GAP_LARGE,
    cleanup_temp_files, get_storage_usage, cleanup_all_temp
)
import keyboards as kb

# WATERMARK ENGINE
from watermark import WatermarkEngine, add_watermark_to_pdf, get_pdf_page_count, clear_cache

# ============================================
# SMART LOGGING SETUP
# ============================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger("WatermarkBot")
logger.setLevel(logging.INFO)

# Filter Pyrogram spam logs
class FilterPyrogramSpam(logging.Filter):
    SPAM_MESSAGES = [
        "PingTask", "NetworkTask", "Session started", "Session stopped",
        "Session initialized", "Device:", "System:", "Disconnected",
        "Retrying"
    ]
    
    def filter(self, record):
        msg = record.getMessage()
        return not any(spam in msg for spam in self.SPAM_MESSAGES)

pyrogram_logger = logging.getLogger("pyrogram")
pyrogram_logger.setLevel(logging.INFO)
pyrogram_logger.addFilter(FilterPyrogramSpam())
logging.getLogger("WatermarkEngine").setLevel(logging.INFO)

# ============================================
# THREAD POOL FOR CONCURRENT PROCESSING
# ============================================
executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)

# ============================================
# TASK QUEUE SYSTEM
# ============================================
main_task_queue = asyncio.Queue()
task_status: Dict[str, str] = {} 

# ============================================
# PYROGRAM APP INITIALIZATION
# ============================================
app = Client(
    "WatermarkBotSession",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=USE_MEMORY_SESSION,
    max_concurrent_transmissions=3
)

BOT_START_TIME = time.time()

# ============================================
# USER SESSION STORAGE
# ============================================
user_data: Dict[int, dict] = {}
processing_tasks: Dict[int, bool] = {}
user_preferences: Dict[str, dict] = {}

def load_user_preferences():
    global user_preferences
    try:
        if os.path.exists(USER_PREFS_FILE):
            with open(USER_PREFS_FILE, 'r') as f:
                user_preferences = json.load(f)
            logger.info(f"✅ Loaded preferences for {len(user_preferences)} users")
    except Exception as e:
        logger.warning(f"Could not load user preferences: {e}")
        user_preferences = {}

def save_user_preferences():
    try:
        with open(USER_PREFS_FILE, 'w') as f:
            json.dump(user_preferences, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save preferences: {e}")

def get_user_last_settings(user_id: int) -> dict:
    return user_preferences.get(str(user_id), {})

def save_user_last_settings(user_id: int, data: dict):
    user_preferences[str(user_id)] = {
        'last_style': data.get('style'),
        'last_color': data.get('color'),
        'last_opacity': data.get('opacity'),
        'last_fontsize': data.get('fontsize'),
        'last_shadow': data.get('add_shadow'),
        'last_gap': data.get('gap'),
        'last_position': data.get('position'),
        'last_outline': data.get('outline'),
        'last_activity': time.time()
    }
    save_user_preferences()

load_user_preferences()

def get_data(user_id: int) -> dict:
    if user_id not in user_data:
        user_data[user_id] = create_default_data()
        last_settings = get_user_last_settings(user_id)
        if last_settings:
            for key in ['style', 'color', 'opacity', 'fontsize', 'add_shadow', 'gap', 'position', 'outline']:
                if last_settings.get(f'last_{key}'):
                    user_data[user_id][key] = last_settings[f'last_{key}']
    return user_data[user_id]

def create_default_data() -> dict:
    return {
        'type': 'text',
        'content': '',
        'style': 'diagonal',
        'color': 'grey',
        'opacity': 0.3,
        'fontsize': 48,
        'rotation': 45,
        'imgsize': 150,
        'border_style': 'simple',
        'border_color': 'grey',
        'border_width': 2,
        'links': [],
        'add_metadata': False,
        'author': '',
        'location': '',
        'step': None,
        'temp_link_url': '',
        'temp_link_pos': '',
        'temp_link_text': '',
        'add_shadow': False,
        'page_range': 'all',
        'font_path': '',
        'double_layer': False,
        'double_layer_offset': 5,
        'double_layer_color': 'black',
        'gradient_effect': False,
        'gap': 'medium',
        'gap_custom': 200,
        'position': 'center',
        'tile_pattern': 'grid',
        'outline': False,
        'outline_width': 2,
        # === NEW FEATURES ===
        'channel_wm_text': '',
        'channel_wm_font': '',
        'footer_parts': [],
        'temp_footer_text': '',
        'temp_footer_font': '',
        'footer_align': 'right', # Default alignment
        # ====================
        'last_activity': time.time()
    }

def clear_data(user_id: int):
    user_data[user_id] = create_default_data()

async def cleanup_task():
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        try:
            current_time = time.time()
            users_to_remove = []
            for user_id, data in user_data.items():
                if data.get('last_activity', 0) < current_time - SESSION_TIMEOUT_SECONDS:
                    users_to_remove.append(user_id)
            
            for user_id in users_to_remove:
                del user_data[user_id]
            
            if users_to_remove:
                logger.info(f"🧹 Cleaned {len(users_to_remove)} inactive sessions")
            
            clear_cache()
            cleaned_files = cleanup_temp_files(SESSION_TIMEOUT_SECONDS)
            gc.collect()
            
            storage_mb = get_storage_usage()
            if storage_mb > MAX_STORAGE_MB:
                logger.warning(f"⚠️ Storage high: {storage_mb}MB, forcing cleanup")
                for directory in [DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
                    shutil.rmtree(directory, ignore_errors=True)
                    os.makedirs(directory, exist_ok=True)
            
            processing_tasks.clear()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def clean_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = ''.join(c for c in name if ord(c) >= 32)
    if len(name) > 180:
        n, e = os.path.splitext(name)
        name = n[:180-len(e)] + e
    return name.strip() or "document.pdf"

def is_old_message(message: Message) -> bool:
    if message.date and message.date.timestamp() < BOT_START_TIME:
        return True
    return False

def get_summary_text(data: dict) -> str:
    lines = ["📋 *PDF ME YE ADD HOGA:*\n"]
    
    if data.get('type') == 'text' and data.get('content'):
        text = data['content'][:40]
        lines.append(f"📝 *Text:* `{text}`")
    elif data.get('type') == 'image':
        lines.append("🖼️ *Logo:* Image Watermark")
    
    if data.get('font_path'):
        lines.append("🔤 *Font:* Custom User Font")
        
    style = data.get('style', 'diagonal')
    lines.append(f"🎨 *Style:* {style.upper()}")
    
    if style in ['grid', 'diagonal'] and data.get('gap'):
        gap = data.get('gap')
        if isinstance(gap, int):
            lines.append(f"📏 *Gap:* {gap}px (Custom)")
        else:
            lines.append(f"📏 *Gap:* {gap.upper()}")
    
    if data.get('position') and data.get('position') != 'center':
        lines.append(f"📍 *Position:* {data.get('position').upper()}")
    
    if data.get('tile_pattern') and data.get('tile_pattern') != 'grid':
        lines.append(f"🔷 *Pattern:* {data.get('tile_pattern').upper()}")
    
    if data.get('type') == 'text' and data.get('add_shadow'):
        lines.append(f"✨ *3D Shadow:* ENABLED")
    
    if data.get('outline'):
        lines.append(f"✏️ *Text Outline:* ENABLED")
    
    if data.get('double_layer'):
        lines.append(f"🎭 *Double Layer:* ENABLED")
    
    if data.get('gradient_effect'):
        lines.append(f"🌈 *Gradient Effect:* ENABLED")
    
    prange = data.get('page_range', 'all')
    lines.append(f"📑 *Pages:* {prange.upper()}")
    
    if style == 'border':
        bs = data.get('border_style', 'simple')
        bc = data.get('border_color', 'grey')
        bw = data.get('border_width', 2)
        lines.append(f"   └ Border: {bs.upper()}")
        lines.append(f"   └ Color: {bc.upper()}")
        lines.append(f"   └ Width: {bw}pt")
    
    color = data.get('color', 'grey')
    lines.append(f"🌈 *Color:* {color.upper()}")
    
    try:
        opacity = float(data.get('opacity', 0.3))
        lines.append(f"💡 *Opacity:* {opacity * 100:.0f}%")
    except:
        lines.append(f"💡 *Opacity:* 30%")
    
    if data.get('type') == 'text':
        try:
            fs = int(data.get('fontsize', 48))
            lines.append(f"🔤 *Size:* {fs}pt")
        except:
            lines.append(f"🔤 *Size:* 48pt")
    
    try:
        rot = int(data.get('rotation', 45))
        lines.append(f"↩️ *Rotation:* {rot}°")
    except:
        lines.append(f"↩️ *Rotation:* 45°")
    
    if data.get('type') == 'image':
        try:
            imgs = int(data.get('imgsize', 150))
            lines.append(f"📐 *Size:* {imgs}px")
        except:
            lines.append(f"📐 *Size:* 150px")
    
    links = data.get('links', [])
    if links:
        lines.append(f"\n🔗 *LINKS ({len(links)}):*")
        for i, link in enumerate(links, 1):
            pos = link.get('position', 'bottomcenter').upper()
            txt = link.get('text', 'LINK')[:20]
            lines.append(f"   {i}. {txt} ({pos})")
    
    if data.get('add_metadata'):
        lines.append(f"\n🕵️ *Metadata:* YES")
        if data.get('author'):
            lines.append(f"   └ Author: {data['author']}")

    # === NEW: SHOW INDEPENDENT FEATURES ===
    if data.get('channel_wm_text'):
        lines.append(f"\n📢 *Channel Watermark:* `{data['channel_wm_text']}`")
        if data.get('channel_wm_font'):
            lines.append(f"   └ Font: Custom Font Loaded")
            
    if data.get('footer_parts'):
        lines.append(f"\n💻 *VS-Code Footer:* (Align: {data.get('footer_align', 'right').upper()})")
        for i, part in enumerate(data['footer_parts'], 1):
            f_type = "Custom" if part.get('font') else "Default"
            lines.append(f"   {i}. `{part['text']}` | {part['color'].upper()} | {f_type}")
            
    return '\n'.join(lines)

class ProgressTracker:
    def __init__(self, message, user_id):
        self.message = message
        self.user_id = user_id
        self.last_update = 0
    
    async def update(self, current: int, total: int):
        now = time.time()
        if now - self.last_update < 3:
            return
        self.last_update = now
        
        percent = int((current / total) * 100)
        try:
            await self.message.edit_text(
                f"⚙️ *Processing Your File...*\n\n📄 Page {current}/{total}\n📊 {percent}% complete\n\n_Kripya thoda wait karein..._",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass

class UploadTracker:
    def __init__(self, message):
        self.message = message
        self.last_update = 0
        
    async def update(self, current: int, total: int):
        now = time.time()
        if now - self.last_update < 3:
            return
        self.last_update = now
        percent = int((current / total) * 100)
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        try:
            await self.message.edit_text(
                f"⬆️ *Uploading Final PDF...*\n\n📊 {percent}% ({current_mb:.1f}MB / {total_mb:.1f}MB)\n\n_Uploading safely. Please don't interrupt..._",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass

async def safe_send_document(message: Message, status_msg: Message, document_path: str, filename: str, caption: str, max_retries=3):
    upload_tracker = UploadTracker(status_msg)
    for attempt in range(max_retries):
        try:
            await message.reply_document(
                document=document_path,
                file_name=filename,
                caption=caption,
                parse_mode=ParseMode.HTML,
                progress=upload_tracker.update
            )
            return True
        except FloodWait as e:
            logger.warning(f"FloodWait encountered: Sleeping for {e.value}s")
            await asyncio.sleep(e.value + 1)
        except RPCError as e:
            logger.error(f"Telegram RPC Error during upload (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await status_msg.edit_text(f"⚠️ Network issue. Retrying upload ({attempt+1}/{max_retries})...")
                await asyncio.sleep(5)
            else:
                raise e
        except Exception as e:
            logger.error(f"Upload attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(4)
            else:
                raise e
    return False

# ============================================
# COMMANDS
# ============================================
@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    if is_old_message(message):
        return
    user_id = message.from_user.id
    clear_data(user_id)
    text = (
        "👋 *WATERMARK BOT - PROFESSIONAL*\n\n"
        "PDF me professional watermark add karo!\n\n"
        "✨ *Features:*\n"
        "• 📝 Text Watermark (3D Shadow, Outline)\n"
        "• 🖼 Logo/Image Watermark\n"
        "• 📢 *Independent Channel Grid* (NEW)\n"
        "• 💻 *Multi-Color VS Code Footer* (NEW)\n"
        "• 🔤 Custom Font Upload (.ttf)\n"
        "• 🎨 8 Styles, 20 Borders, 18 Colors\n"
        "• 📦 ZIP File Batch Support\n\n"
        "🚀 *Send TEXT, IMAGE, FONT, or use MENU!*"
    )
    await message.reply_text(text, reply_markup=kb.get_main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("help"))
async def cmd_help(client: Client, message: Message):
    if is_old_message(message):
        return
    text = "📖 *HOW TO USE - PRO GUIDE*\n\nSend /start to begin..."
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("reset"))
async def cmd_reset(client: Client, message: Message):
    if is_old_message(message):
        return
    user_id = message.from_user.id
    clear_data(user_id)
    await message.reply_text("🔄 *Settings cleared!*\n\nSend TEXT or IMAGE to start.", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("settings"))
async def cmd_settings(client: Client, message: Message):
    if is_old_message(message):
        return
    user_id = message.from_user.id
    data = get_data(user_id)
    if not data.get('content') and not data.get('font_path') and not data.get('channel_wm_text') and not data.get('footer_parts'):
        await message.reply_text("⚠️ No settings found. Send /start", parse_mode=ParseMode.MARKDOWN)
        return
    text = get_summary_text(data)
    await message.reply_text(text, reply_markup=kb.get_settings_keyboard(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("clearcache"))
async def cmd_clearcache(client: Client, message: Message):
    clear_cache()
    gc.collect()
    await message.reply_text("🗑️ *Cache cleared!*\n\nMemory optimized.", parse_mode=ParseMode.MARKDOWN)

# ============================================
# HANDLE TEXT INPUT (UPDATED FOR INDEPENDENT FOOTER/CHANNEL)
# ============================================
@app.on_message(filters.text & ~filters.command(["start", "help", "reset", "settings", "clearcache"]))
async def handle_text(client: Client, message: Message):
    if is_old_message(message):
        return
    
    text = message.text
    user_id = message.from_user.id
    data = get_data(user_id)
    data['last_activity'] = time.time()
    
    # === INDEPENDENT CHANNEL WATERMARK LOGIC ===
    if data.get('step') == 'waiting_channel_text':
        data['channel_wm_text'] = text.strip()
        data['step'] = 'waiting_channel_font'
        kb_skip = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Skip (Use Default Font)", callback_data="skip_channel_font")]])
        await message.reply_text(
            f"✅ Channel Name Saved: `{text}`\n\n"
            f"🔤 *Upload a custom .ttf font* for this watermark, OR click Skip.",
            reply_markup=kb_skip,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # === INDEPENDENT CUSTOM FOOTER LOGIC ===
    if data.get('step') == 'waiting_footer_text':
        data['temp_footer_text'] = text.strip()
        data['step'] = 'waiting_footer_font'
        kb_skip = InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Skip (Use Default Font)", callback_data="skip_footer_font")]])
        await message.reply_text(
            f"✅ Footer Text Saved: `{text}`\n\n"
            f"🔤 *Upload a custom .ttf font* for THIS specific word, OR click Skip.",
            reply_markup=kb_skip,
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if data.get('step') == 'waiting_metadata':
        parts = text.split(',')
        data['author'] = parts[0].strip()
        data['location'] = parts[1].strip() if len(parts) > 1 else 'India'
        data['add_metadata'] = True
        data['step'] = None
        summary = get_summary_text(data)
        await message.reply_text(f"✅ *Metadata Saved!*\n\n{summary}\n\n📂 *Send PDF or ZIP file now!*", parse_mode=ParseMode.MARKDOWN)
        return
    
    if data.get('step') == 'waiting_rotation':
        try:
            angle = int(text.strip())
            if -180 <= angle <= 180:
                data['rotation'] = angle
                data['step'] = None
                await message.reply_text(f"✅ Rotation: {angle}°\n\n🔗 Add clickable links?", reply_markup=kb.get_link_add_skip_keyboard(), parse_mode=ParseMode.MARKDOWN)
            else:
                await message.reply_text("⚠️ Enter angle between -180 and 180", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await message.reply_text("⚠️ Enter valid number like: 45", parse_mode=ParseMode.MARKDOWN)
        return
    
    if data.get('step') == 'waiting_link_url':
        url = text.strip()
        if not url.startswith('http'):
            url = 'https://' + url
        data['temp_link_url'] = url
        data['step'] = None
        await message.reply_text(f"✅ Link URL saved!\n\n📍 Choose position:", reply_markup=kb.get_link_position_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return
    
    if data.get('step') == 'waiting_link_text':
        data['temp_link_text'] = text.strip()[:25]
        data['step'] = None
        
        temp_url = data.get('temp_link_url', '')
        temp_pos = data.get('temp_link_pos', 'bottomcenter')
        temp_txt = data.get('temp_link_text', '🔗 CLICK HERE')
        
        if temp_url:
            data['links'].append({'url': temp_url, 'position': temp_pos, 'text': temp_txt})
            data['temp_link_url'] = ''
            data['temp_link_pos'] = ''
            data['temp_link_text'] = ''
        
        count = len(data['links'])
        await message.reply_text(f"✅ Link added! ({count}/6)\n\nAdd more or continue?", reply_markup=kb.get_add_more_link_keyboard(count), parse_mode=ParseMode.MARKDOWN)
        return
    
    if data.get('step') == 'waiting_page_range':
        data['page_range'] = text.strip()
        data['step'] = None
        await message.reply_text(f"✅ Page range: {text}\n\n↩️ Choose rotation:", reply_markup=kb.get_rotation_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return
    
    if data.get('step') == 'waiting_custom_gap':
        try:
            gap_value = int(text.strip())
            if 80 <= gap_value <= 500:
                data['gap'] = gap_value
                data['gap_custom'] = gap_value
                data['step'] = None
                await message.reply_text(f"✅ Gap set to: {gap_value}px\n\nContinue with settings or send PDF!", parse_mode=ParseMode.MARKDOWN)
            else:
                await message.reply_text("⚠️ Enter gap between 80 and 500", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await message.reply_text("⚠️ Enter valid number like: 150", parse_mode=ParseMode.MARKDOWN)
        return
    
    if len(text) > 150:
        await message.reply_text("⚠️ Text too long! Max 150 chars.", parse_mode=ParseMode.MARKDOWN)
        return
    
    data['type'] = 'text'
    data['content'] = text.strip()
    
    if len(text) < 10:
        data['fontsize'] = 60
    elif len(text) < 25:
        data['fontsize'] = 48
    elif len(text) < 50:
        data['fontsize'] = 36
    else:
        data['fontsize'] = 28
    
    await message.reply_text(f"✅ Main Text: `{text}`\n\n🎨 Choose watermark style:", reply_markup=kb.get_style_keyboard(), parse_mode=ParseMode.MARKDOWN)

# ============================================
# HANDLE PHOTO INPUT
# ============================================
@app.on_message(filters.photo)
async def handle_photo(client: Client, message: Message):
    if is_old_message(message):
        return
    user_id = message.from_user.id
    data = get_data(user_id)
    data['last_activity'] = time.time()
    try:
        path = os.path.join(DOWNLOAD_DIR, f"logo_{user_id}_{int(time.time())}.png")
        await message.download(file_name=path)
        data['type'] = 'image'
        data['content'] = path
        await message.reply_text("✅ Logo saved!\n\n🎨 Choose watermark style:", reply_markup=kb.get_style_keyboard(), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Photo error: {e}")
        await message.reply_text("❌ Failed to save image. Try again.", parse_mode=ParseMode.MARKDOWN)

# ============================================
# HANDLE DOCUMENTS (PDF, ZIP, TTF) 
# ============================================
@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    if is_old_message(message):
        return
    user_id = message.from_user.id
    data = get_data(user_id)
    data['last_activity'] = time.time()
    
    filename = message.document.file_name or "file.dat"
    ext = filename.lower().split('.')[-1]
    mime = message.document.mime_type or ""
    
    # Custom Font File Upload logic
    if ext in ['ttf', 'otf']:
        status = await message.reply_text("⏳ Downloading Custom Font...", parse_mode=ParseMode.MARKDOWN)
        try:
            font_path = os.path.join(ASSETS_DIR, f"font_{user_id}_{message.id}.ttf")
            await message.download(file_name=font_path)
            
            step = data.get('step')
            if step == 'waiting_channel_font':
                data['channel_wm_font'] = font_path
                data['step'] = None
                await status.edit_text("✅ *Channel Font Saved!*\n\nNow configure other settings or send PDF.", reply_markup=kb.get_settings_keyboard(), parse_mode=ParseMode.MARKDOWN)
            elif step == 'waiting_footer_font':
                data['temp_footer_font'] = font_path
                data['step'] = 'waiting_footer_color'
                await status.edit_text("✅ *Footer Font Saved!*\n\nNow choose *COLOR* for this part of the footer:", reply_markup=kb.get_color_keyboard(), parse_mode=ParseMode.MARKDOWN)
            else:
                data['font_path'] = font_path
                data['step'] = None
                await status.edit_text("✅ *Main Watermark Font Saved!*\n\nNow send your watermark text, or send a PDF if text is already set.", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Font download error: {e}")
            await status.edit_text("❌ Failed to save font. Try a different .ttf file.", parse_mode=ParseMode.MARKDOWN)
        return
    
    if message.document.file_size and message.document.file_size > MAX_DOWNLOAD_SIZE:
        await message.reply_text(f"❌ *File too large!*\nMaximum size: {MAX_DOWNLOAD_SIZE // 1024 // 1024}MB\nPlease send a smaller file.", parse_mode=ParseMode.MARKDOWN)
        return
    
    if not data.get('content') and not data.get('channel_wm_text') and not data.get('footer_parts'):
        await message.reply_text("⚠️ Configure watermark text, image, channel or footer first!\nSend /start to begin.", parse_mode=ParseMode.MARKDOWN)
        return
        
    if ext not in ['pdf', 'zip'] and 'pdf' not in mime.lower() and 'zip' not in mime.lower():
        await message.reply_text("⚠️ Please send a PDF, ZIP, or Font (.ttf) file.", parse_mode=ParseMode.MARKDOWN)
        return
    
    processing_tasks[user_id] = True
    task_id = f"{message.chat.id}_{message.id}"
    task_status[task_id] = "pending"
    pos = main_task_queue.qsize() + 1
    
    cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{task_id}")]])
    status_msg = await message.reply_text(
        f"⏳ *Added to Queue*\n\n📄 File: `{filename}`\n🔢 Queue Position: {pos}\n\n_Please wait, bot is processing tasks one by one..._",
        reply_markup=cancel_kb,
        parse_mode=ParseMode.MARKDOWN
    )
    
    task_data = {
        'id': task_id,
        'client': client,
        'message': message,
        'data': copy.deepcopy(data), 
        'filename': filename,
        'status_msg': status_msg,
        'is_zip': ext == 'zip' or 'zip' in mime.lower()
    }
    await main_task_queue.put(task_data)

# ============================================
# HANDLE BUTTON CALLBACKS (INTEGRATED PREMIUM)
# ============================================
@app.on_callback_query()
async def handle_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    cb = query.data

    if cb.startswith('cancel_'):
        task_id = cb.replace('cancel_', '')
        task_status[task_id] = "cancelled"
        try:
            await query.edit_message_text("❌ *Task Cancelled by User!*", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        return

    await query.answer()
    data = get_data(user_id)
    data['last_activity'] = time.time()
    
    try:
        # === PREMIUM: CHANNEL WATERMARK SETUP ===
        if cb == 'menu_channel':
            data['step'] = 'waiting_channel_text'
            kb_clear = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ Clear Channel WM", callback_data="clear_channel")]])
            await query.edit_message_text(
                "📢 Send your Channel Name / Text for the Diagonal Grid Watermark:\n(Example: `@MyChannel`)\n\n_Click clear below if you want to remove it entirely._", 
                reply_markup=kb_clear, parse_mode=ParseMode.MARKDOWN
            )
        elif cb == 'clear_channel':
            data['channel_wm_text'] = ''
            data['channel_wm_font'] = ''
            data['step'] = None
            await query.edit_message_text("✅ Channel Watermark Cleared!\n\nChoose next action:", reply_markup=kb.get_settings_keyboard())
        elif cb == 'skip_channel_font':
            data['channel_wm_font'] = ''
            data['step'] = None
            await query.edit_message_text("✅ Using Default Font for Channel Watermark.\n\nNow configure other settings or send PDF!", reply_markup=kb.get_settings_keyboard())

        # === PREMIUM: VS CODE MULTI-COLOR FOOTER SETUP ===
        elif cb == 'menu_footer':
            data['step'] = 'waiting_footer_text'
            data['temp_footer_text'] = ''
            data['temp_footer_font'] = ''
            kb_clear = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ Clear Custom Footer", callback_data="clear_footer")]])
            await query.edit_message_text(
                "✨ *MULTI-COLOR FOOTER SETUP*\n\n📝 Send the *FIRST part* of your footer text (e.g., `<Aryan />`):\n\n_Click clear below if you want to remove it entirely._", 
                reply_markup=kb_clear, parse_mode=ParseMode.MARKDOWN
            )
        elif cb == 'clear_footer':
            data['footer_parts'] = []
            data['step'] = None
            await query.edit_message_text("✅ Custom Footer Cleared!\n\nChoose next action:", reply_markup=kb.get_settings_keyboard())
        elif cb == 'skip_footer_font':
            data['temp_footer_font'] = ''
            data['step'] = 'waiting_footer_color'
            await query.edit_message_text("✅ Font skipped. Now choose *COLOR* for this part of the footer:", reply_markup=kb.get_color_keyboard(), parse_mode=ParseMode.MARKDOWN)
        elif cb == 'footer_add_more':
            data['step'] = 'waiting_footer_text'
            await query.edit_message_text("📝 Send the Text for the NEXT part of the footer:")
        elif cb == 'footer_done':
            # Naya logic: Ask for alignment instead of finishing
            await query.edit_message_text("📍 Where do you want to place the custom footer?", reply_markup=kb.get_footer_align_keyboard())
        elif cb.startswith('falign_'):
            align = cb.replace('falign_', '')
            data['footer_align'] = align
            data['step'] = None
            await query.edit_message_text(f"✅ Multi-Color Footer Setup Complete! (Aligned: {align.upper()})\n\n📂 Send PDF or ZIP file now.", reply_markup=kb.get_settings_keyboard())

        # === STANDARD MENUS ===
        elif cb.startswith('preset_'):
            await handle_preset(query, data, cb)
        elif cb == 'menu_text':
            await query.edit_message_text("📝 Send your main watermark text:")
        elif cb == 'menu_image':
            await query.edit_message_text("🖼️ Send your logo image:")
        elif cb == 'menu_font':
            await query.edit_message_text("🔤 Send me a `.ttf` or `.otf` font file to upload:")
        elif cb == 'menu_presets':
            await query.edit_message_text("⚡ QUICK PRESETS - One Click Setup:", reply_markup=kb.get_quick_presets_keyboard())
        elif cb == 'menu_help':
            await query.edit_message_text("❓ HELP CENTER", reply_markup=kb.get_help_keyboard())
        elif cb == 'back_main':
            await query.edit_message_text("🏠 MAIN MENU", reply_markup=kb.get_main_menu_keyboard())
        
        elif cb.startswith('style_'):
            style = cb.replace('style_', '')
            data['style'] = style
            if style == 'border':
                await query.edit_message_text("🔲 BORDER selected!\n\nChoose border style:", reply_markup=kb.get_border_style_keyboard())
            elif data.get('type') == 'text':
                if style in ['grid']:
                    await query.edit_message_text(f"✅ Style: {style.upper()}\n\n📏 Choose gap/spacing:", reply_markup=kb.get_gap_keyboard())
                else:
                    await query.edit_message_text(f"✅ Style: {style.upper()}\n\n🌈 Choose color:", reply_markup=kb.get_color_keyboard())
            else:
                await query.edit_message_text(f"✅ Style: {style.upper()}\n\n📐 Choose Logo size:", reply_markup=kb.get_imgsize_keyboard())
        
        elif cb.startswith('gap_'):
            gap = cb.replace('gap_', '')
            if gap == 'custom':
                data['step'] = 'waiting_custom_gap'
                await query.edit_message_text("📏 Enter custom gap (80-500):\n\n_Recommended: 150-250 for balanced look_", parse_mode=ParseMode.MARKDOWN)
            elif gap == 'default':
                data['gap'] = 'medium'
                await query.edit_message_text("🌈 Choose watermark color:", reply_markup=kb.get_color_keyboard())
            else:
                data['gap'] = gap
                gap_sizes = {'small': GAP_SMALL, 'medium': GAP_MEDIUM, 'large': GAP_LARGE}
                gap_px = gap_sizes.get(gap, 200)
                await query.edit_message_text(f"✅ Gap: {gap.upper()} ({gap_px}px)\n\n🌈 Choose color:", reply_markup=kb.get_color_keyboard())
        
        elif cb.startswith('tpattern_'):
            pattern = cb.replace('tpattern_', '')
            data['tile_pattern'] = pattern
            await query.edit_message_text(f"✅ Pattern: {pattern.upper()}\n\n📏 Choose gap/spacing:", reply_markup=kb.get_gap_keyboard())
        elif cb.startswith('pos_'):
            position = cb.replace('pos_', '')
            data['position'] = position
            await query.edit_message_text(f"✅ Position: {position.upper()}\n\n💡 Choose opacity:", reply_markup=kb.get_opacity_keyboard())
        elif cb.startswith('outline_'):
            data['outline'] = (cb.replace('outline_', '') == 'yes')
            if data['outline']:
                await query.edit_message_text("✏️ Choose outline width:", reply_markup=kb.get_outline_width_keyboard())
            else:
                await query.edit_message_text("📑 On which pages do you want this?", reply_markup=kb.get_page_range_keyboard())
        elif cb.startswith('owidth_'):
            data['outline_width'] = int(cb.replace('owidth_', ''))
            await query.edit_message_text("📑 On which pages do you want this?", reply_markup=kb.get_page_range_keyboard())
        elif cb.startswith('bstyle_'):
            bstyle = cb.replace('bstyle_', '')
            if bstyle == 'skip':
                if data.get('type') == 'text':
                    await query.edit_message_text("🌈 Choose watermark color:", reply_markup=kb.get_color_keyboard())
                else:
                    await query.edit_message_text("📐 Choose Logo size:", reply_markup=kb.get_imgsize_keyboard())
            else:
                data['border_style'] = bstyle
                await query.edit_message_text(f"✅ Border: {bstyle.upper()}\n\n🎨 Choose border color:", reply_markup=kb.get_border_color_keyboard())
        elif cb.startswith('bcolor_'):
            data['border_color'] = cb.replace('bcolor_', '')
            await query.edit_message_text("📏 Choose border width:", reply_markup=kb.get_border_width_keyboard())
        elif cb.startswith('bwidth_'):
            data['border_width'] = int(cb.replace('bwidth_', ''))
            if data.get('type') == 'text':
                await query.edit_message_text("🌈 Choose text color:", reply_markup=kb.get_color_keyboard())
            else:
                await query.edit_message_text("📐 Choose Logo size:", reply_markup=kb.get_imgsize_keyboard())
        
        elif cb.startswith('color_'):
            selected_color = cb.replace('color_', '')
            # If we are selecting color for Footer
            if data.get('step') == 'waiting_footer_color':
                data['footer_parts'].append({
                    'text': data.get('temp_footer_text', ''),
                    'font': data.get('temp_footer_font', ''),
                    'color': selected_color
                })
                data['temp_footer_text'] = ''
                data['temp_footer_font'] = ''
                data['step'] = None
                
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Next Text", callback_data="footer_add_more")],
                    [InlineKeyboardButton("✅ Done (Choose Alignment)", callback_data="footer_done")]
                ])
                part_count = len(data['footer_parts'])
                await query.edit_message_text(f"✅ Footer Part {part_count} Saved! (Color: {selected_color.upper()})\n\nDo you want to add another word/text next to it?", reply_markup=markup)
            # Else regular color
            else:
                data['color'] = selected_color
                await query.edit_message_text("💡 Choose opacity:", reply_markup=kb.get_opacity_keyboard())
                
        elif cb.startswith('opac_'):
            data['opacity'] = float(cb.replace('opac_', ''))
            if data.get('type') == 'text':
                await query.edit_message_text("🔤 Choose font size:", reply_markup=kb.get_fontsize_keyboard())
            else:
                await query.edit_message_text("📑 On which pages do you want this?", reply_markup=kb.get_page_range_keyboard())
        elif cb.startswith('fsize_'):
            data['fontsize'] = int(cb.replace('fsize_', ''))
            await query.edit_message_text("✨ Choose effects:", reply_markup=kb.get_effects_menu_keyboard())
        elif cb.startswith('isize_'):
            data['imgsize'] = int(cb.replace('isize_', ''))
            await query.edit_message_text("📑 On which pages do you want this?", reply_markup=kb.get_page_range_keyboard())
        elif cb == 'effect_shadow':
            await query.edit_message_text("✨ Add 3D Shadow/Glow effect?", reply_markup=kb.get_shadow_keyboard())
        elif cb == 'effect_double':
            await query.edit_message_text("🎭 Add Double Layer Watermark?\n(Second watermark at 90° rotation)", reply_markup=kb.get_double_layer_keyboard())
        elif cb == 'effect_gradient':
            await query.edit_message_text("🌈 Add Gradient Effect?", reply_markup=kb.get_gradient_keyboard())
        elif cb == 'effect_outline':
            await query.edit_message_text("✏️ Add Text Outline/Stroke?", reply_markup=kb.get_outline_keyboard())
        elif cb == 'effect_skip':
            data['add_shadow'] = False
            data['double_layer'] = False
            data['gradient_effect'] = False
            data['outline'] = False
            await query.edit_message_text("📑 On which pages do you want this?", reply_markup=kb.get_page_range_keyboard())
        elif cb.startswith('shadow_'):
            data['add_shadow'] = (cb.replace('shadow_', '') == 'yes')
            await query.edit_message_text("🎭 Add Double Layer Watermark?", reply_markup=kb.get_double_layer_keyboard())
        elif cb.startswith('double_'):
            data['double_layer'] = (cb.replace('double_', '') == 'yes')
            if data['double_layer']:
                await query.edit_message_text("🎨 Choose second layer color:", reply_markup=kb.get_double_layer_color_keyboard())
            else:
                await query.edit_message_text("🌈 Add Gradient Effect?", reply_markup=kb.get_gradient_keyboard())
        elif cb.startswith('dcolor_'):
            data['double_layer_color'] = cb.replace('dcolor_', '')
            await query.edit_message_text("🌈 Add Gradient Effect?", reply_markup=kb.get_gradient_keyboard())
        elif cb.startswith('gradient_'):
            data['gradient_effect'] = (cb.replace('gradient_', '') == 'yes')
            await query.edit_message_text("✏️ Add Text Outline/Stroke?", reply_markup=kb.get_outline_keyboard())
        elif cb.startswith('prange_'):
            prange = cb.replace('prange_', '')
            if prange == 'custom':
                data['step'] = 'waiting_page_range'
                await query.edit_message_text("🔢 Enter page range:\n\n_Examples:_\n• `1-5` (pages 1 to 5)\n• `1,3,5` (specific pages)\n• `1-5, 8, 10-12` (combined)", parse_mode=ParseMode.MARKDOWN)
            else:
                data['page_range'] = prange
                await query.edit_message_text("↩️ Choose rotation:", reply_markup=kb.get_rotation_keyboard())
        elif cb.startswith('rot_'):
            rot = cb.replace('rot_', '')
            if rot == 'custom':
                data['step'] = 'waiting_rotation'
                await query.edit_message_text("🔄 Enter custom angle (-180 to 180):\n_Example: 30 or -45_", parse_mode=ParseMode.MARKDOWN)
            else:
                data['rotation'] = int(rot)
                await query.edit_message_text(f"✅ Rotation: {rot}°\n\n🔗 Add clickable links?", reply_markup=kb.get_link_add_skip_keyboard())
        elif cb == 'link_add':
            data['step'] = 'waiting_link_url'
            await query.edit_message_text("🔗 Enter link URL:\n_Example: https://yourwebsite.com_", parse_mode=ParseMode.MARKDOWN)
        elif cb == 'link_skip':
            data['links'] = []
            await query.edit_message_text("🕵️ Add hidden metadata to PDF?\n(Author name, location etc.)", reply_markup=kb.get_metadata_keyboard())
        elif cb.startswith('lpos_'):
            data['temp_link_pos'] = cb.replace('lpos_', '')
            await query.edit_message_text("📝 Choose link button text:", reply_markup=kb.get_link_text_keyboard())
        elif cb.startswith('ltext_'):
            await handle_link_text(query, data, cb)
        elif cb == 'link_done':
            await query.edit_message_text("🕵️ Add hidden metadata to PDF?\n(Author name, location etc.)", reply_markup=kb.get_metadata_keyboard())
        elif cb == 'link_view':
            links = data.get('links', [])
            if not links:
                text = "📋 No links added yet."
            else:
                text = "📋 *YOUR LINKS:*\n" + '\n'.join([f"{i}. `{l['text']}` ({l['position']})" for i, l in enumerate(links, 1)])
            await query.edit_message_text(text, reply_markup=kb.get_link_menu_keyboard(len(links)), parse_mode=ParseMode.MARKDOWN)
        elif cb == 'link_clear':
            data['links'] = []
            await query.edit_message_text("🗑️ All links cleared!\n\nAdd links?", reply_markup=kb.get_link_add_skip_keyboard())
        elif cb == 'meta_yes':
            data['step'] = 'waiting_metadata'
            await query.edit_message_text("📝 Enter metadata:\n\n_Format: Author Name, Location_\n_Example: John, Mumbai_", parse_mode=ParseMode.MARKDOWN)
        elif cb == 'meta_no':
            data['add_metadata'] = False
            save_user_last_settings(user_id, data)
            await query.edit_message_text(f"{get_summary_text(data)}\n\n📂 *Send PDF or ZIP file now!*", parse_mode=ParseMode.MARKDOWN)
        elif cb == 'set_style':
            await query.edit_message_text("🎨 Choose Style:", reply_markup=kb.get_style_keyboard())
        elif cb == 'set_color':
            await query.edit_message_text("🌈 Choose Color:", reply_markup=kb.get_color_keyboard())
        elif cb == 'set_opacity':
            await query.edit_message_text("💡 Choose Opacity:", reply_markup=kb.get_opacity_keyboard())
        elif cb == 'set_fontsize':
            await query.edit_message_text("🔤 Choose Size:", reply_markup=kb.get_fontsize_keyboard())
        elif cb == 'set_font':
            await query.edit_message_text("🔤 Send me a `.ttf` or `.otf` file in chat to set custom font.")
        elif cb == 'set_border':
            await query.edit_message_text("🔲 Choose Border:", reply_markup=kb.get_border_style_keyboard())
        elif cb == 'set_shadow':
            await query.edit_message_text("✨ Toggle 3D Shadow:", reply_markup=kb.get_shadow_keyboard())
        elif cb == 'set_double':
            await query.edit_message_text("🎭 Toggle Double Layer:", reply_markup=kb.get_double_layer_keyboard())
        elif cb == 'set_gradient':
            await query.edit_message_text("🌈 Toggle Gradient Effect:", reply_markup=kb.get_gradient_keyboard())
        elif cb == 'set_gap':
            await query.edit_message_text("📏 Choose Gap/Spacing:", reply_markup=kb.get_gap_keyboard())
        elif cb == 'set_position':
            await query.edit_message_text("📍 Choose Position:", reply_markup=kb.get_position_keyboard())
        elif cb == 'set_outline':
            await query.edit_message_text("✏️ Toggle Text Outline:", reply_markup=kb.get_outline_keyboard())
        elif cb == 'set_prange':
            await query.edit_message_text("📑 Choose Page Range:", reply_markup=kb.get_page_range_keyboard())
        elif cb == 'set_links':
            await query.edit_message_text("🔗 Manage Links:", reply_markup=kb.get_link_menu_keyboard(len(data.get('links', []))))
        elif cb == 'cancel_operation':
            processing_tasks[user_id] = False
            await query.edit_message_text("❌ Operation cancelled.\n\nSend a new PDF to continue.", parse_mode=ParseMode.MARKDOWN)
            
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Callback error: {e}")
        try:
            await query.edit_message_text("❌ Error processing request. Try again.")
        except:
            pass

async def handle_preset(query: CallbackQuery, data: dict, cb: str):
    preset = cb.replace('preset_', '')
    presets = {
        'diagonal_grey': {
            'style': 'diagonal', 'color': 'grey', 'opacity': 0.3,
            'fontsize': 48, 'rotation': 45, 'add_shadow': False,
            'double_layer': False, 'gradient_effect': False,
            'outline': False, 'gap': 'medium', 'position': 'center',
            'msg': "✅ *Quick Diagonal Applied!*\n\n• Style: DIAGONAL\n• Color: GREY\n• Opacity: 30%\n\n📂 *Send PDF or ZIP file now!*"
        },
        'bold_red': {
            'style': 'diagonal', 'color': 'red', 'opacity': 0.7,
            'fontsize': 60, 'rotation': 45, 'add_shadow': True,
            'double_layer': False, 'gradient_effect': False,
            'outline': False, 'gap': 'medium', 'position': 'center',
            'msg': "✅ *Bold Red Applied!*\n\n• Style: DIAGONAL\n• Color: RED\n• Opacity: 70%\n• 3D Shadow: YES\n\n📂 *Send PDF or ZIP file now!*"
        },
        'elegant_blue': {
            'style': 'diagonal', 'color': 'blue', 'opacity': 0.25,
            'fontsize': 52, 'rotation': 45, 'add_shadow': False,
            'double_layer': False, 'gradient_effect': False,
            'outline': False, 'gap': 'medium', 'position': 'center',
            'msg': "✅ *Elegant Blue Applied!*\n\n• Style: DIAGONAL\n• Color: BLUE\n• Opacity: 25%\n\n📂 *Send PDF or ZIP file now!*"
        },
        'border_grey': {
            'style': 'border', 'border_style': 'elegant', 'border_color': 'grey',
            'border_width': 2, 'opacity': 0.4, 'add_shadow': False,
            'double_layer': False, 'gradient_effect': False,
            'outline': False, 'gap': 'medium', 'position': 'center',
            'msg': "✅ *Border Frame Applied!*\n\n• Style: BORDER\n• Border: ELEGANT\n• Color: GREY\n\n📂 *Send PDF or ZIP file now!*"
        },
        'header_black': {
            'style': 'header', 'color': 'black', 'opacity': 0.5,
            'fontsize': 30, 'add_shadow': False,
            'double_layer': False, 'gradient_effect': False,
            'outline': False, 'gap': 'medium', 'position': 'center',
            'msg': "✅ *Header Style Applied!*\n\n• Style: HEADER\n• Color: BLACK\n• Opacity: 50%\n\n📂 *Send PDF or ZIP file now!*"
        },
        'double_layer': {
            'style': 'diagonal', 'color': 'grey', 'opacity': 0.35,
            'fontsize': 48, 'rotation': 45, 'add_shadow': True,
            'double_layer': True, 'double_layer_color': 'black',
            'gradient_effect': False, 'outline': False,
            'gap': 'medium', 'position': 'center',
            'msg': "✅ *Double Layer Pro Applied!*\n\n• Style: DIAGONAL\n• 3D Shadow: YES\n• Double Layer: YES\n• Second Layer: BLACK\n\n📂 *Send PDF or ZIP file now!*"
        },
        'custom': {
            'msg': None
        }
    }
    if preset in presets:
        p = presets[preset]
        if p.get('msg'):
            for key, value in p.items():
                if key != 'msg':
                    data[key] = value
            await query.edit_message_text(p['msg'], parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text("🎨 Choose watermark style:", reply_markup=kb.get_style_keyboard())

async def handle_link_text(query: CallbackQuery, data: dict, cb: str):
    ltext = cb.replace('ltext_', '')
    if ltext == 'custom':
        data['step'] = 'waiting_link_text'
        await query.edit_message_text("📝 Enter custom link text (max 25 chars):", parse_mode=ParseMode.MARKDOWN)
    else:
        text_styles = {
            'click': '🔗 CLICK HERE', 
            'visit': '📱 VISIT US', 
            'open': '🌐 OPEN LINK', 
            'learn': '✨ LEARN MORE', 
            'url': None
        }
        link_text = text_styles.get(ltext, '🔗 CLICK HERE') or data.get('temp_link_url', 'LINK')[:25]
        data['links'].append({
            'url': data.get('temp_link_url', ''), 
            'position': data.get('temp_link_pos', 'bottomcenter'), 
            'text': link_text
        })
        count = len(data['links'])
        await query.edit_message_text(f"✅ Link added! ({count}/6)\n\nAdd more or continue?", reply_markup=kb.get_add_more_link_keyboard(count))

# ============================================
# BACKGROUND WORKER PROCESSOR
# ============================================
async def task_worker(worker_id: int):
    while True:
        task = await main_task_queue.get()
        task_id = task['id']
        status_msg = task['status_msg']
        try:
            if task_status.get(task_id) == "cancelled":
                await status_msg.edit_text("❌ *Task Cancelled by User*", parse_mode=ParseMode.MARKDOWN)
                continue
            task_status[task_id] = "processing"
            if task['is_zip']:
                await execute_zip_processing(task)
            else:
                await execute_pdf_processing(task)
        except Exception as e:
            logger.error(f"Worker {worker_id} Error: {e}")
            try: await status_msg.edit_text("❌ *Error processing file.*", parse_mode=ParseMode.MARKDOWN)
            except: pass
        finally:
            if task_id in task_status: 
                del task_status[task_id]
            main_task_queue.task_done()
            gc.collect()

# ============================================
# ACTUAL PROCESSING LOGIC
# ============================================
async def execute_pdf_processing(task: dict):
    message, status_msg = task['message'], task['status_msg']
    data, filename = task['data'], task['filename']
    user_id = message.from_user.id
    
    await status_msg.edit_text("⬇️ *Downloading file...*", parse_mode=ParseMode.MARKDOWN)
    
    user_dir = os.path.join(DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    input_path = os.path.join(user_dir, f"in_{task['id']}.pdf")
    output_path = os.path.join(user_dir, f"out_{task['id']}.pdf")
    
    try:
        await message.download(file_name=input_path)
        if task_status.get(task['id']) == "cancelled": return
            
        pages = get_pdf_page_count(input_path)
        progress = ProgressTracker(status_msg, user_id)
        await status_msg.edit_text(f"🎨 *Applying Watermark...* ({pages} pages)", parse_mode=ParseMode.MARKDOWN)
        
        loop = asyncio.get_event_loop()
        engine = WatermarkEngine(data)
        
        def sync_progress(c, t):
            if task_status.get(task['id']) != "cancelled":
                asyncio.run_coroutine_threadsafe(progress.update(c, t), loop)
                
        success, err_msg = await loop.run_in_executor(executor, engine.process_pdf, input_path, output_path, filename, sync_progress)
        
        if task_status.get(task['id']) == "cancelled": return
            
        if success and os.path.exists(output_path):
            save_user_last_settings(user_id, data)
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            caption = f"✅ <b>WATERMARK APPLIED!</b>\n\n📄 <b>File:</b> <code>{html.escape(filename)}</code>\n📋 <b>Pages:</b> {pages}\n"
            
            if data.get('type') == 'text' and data.get('content'):
                txt = html.escape(data.get('content', '')[:40])
                caption += f"📝 <b>Text:</b> <code>{txt}</code>\n"
            
            if data.get('channel_wm_text'):
                caption += f"📢 <b>Grid:</b> YES\n"
            if data.get('footer_parts'):
                caption += f"💻 <b>Footer:</b> Custom ({data.get('footer_align', 'right').upper()})\n"
            
            if new_size <= original_size * 1.15:
                caption += f"📦 <b>Size:</b> Optimized ✓"
            else:
                size_diff = (new_size - original_size) / 1024
                caption += f"📦 <b>Size:</b> +{size_diff:.0f}KB"
            
            upload_success = await safe_send_document(message, status_msg, output_path, filename, caption)
            if upload_success: await status_msg.delete()
            else: await status_msg.edit_text("❌ Upload failed due to Telegram limits.")
        else:
            await status_msg.edit_text(f"❌ Failed: {err_msg}")
            
    except Exception as e:
        logger.error(f"PDF error for msg {message.id}: {e}")
        await status_msg.edit_text(f"❌ Processing error. File might be protected/corrupted.", parse_mode=ParseMode.MARKDOWN)
        
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path): os.remove(path)

async def execute_zip_processing(task: dict):
    message, status_msg = task['message'], task['status_msg']
    data, filename = task['data'], task['filename']
    user_id = message.from_user.id
    
    user_dir = os.path.join(DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    zip_path = os.path.join(user_dir, f"in_{task['id']}.zip")
    ext_dir = os.path.join(user_dir, f"ext_{task['id']}")
    os.makedirs(ext_dir, exist_ok=True)
    
    try:
        await status_msg.edit_text("⬇️ *Downloading ZIP...*", parse_mode=ParseMode.MARKDOWN)
        await message.download(file_name=zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(ext_dir)
        pdfs = [os.path.join(r, f) for r, d, files in os.walk(ext_dir) for f in files if f.lower().endswith('.pdf')]
        
        if not pdfs:
            await status_msg.edit_text("❌ No PDFs found in ZIP.")
            return
            
        success_count = 0
        loop = asyncio.get_event_loop()
        
        for i, pdf_path in enumerate(pdfs, 1):
            if task_status.get(task['id']) == "cancelled": break
                
            orig_name = os.path.basename(pdf_path)
            out_path = os.path.join(user_dir, f"out_{i}_{task['id']}.pdf")
            
            if i % 3 == 0 or i == len(pdfs):
                try: await status_msg.edit_text(f"⚙️ *Processing {i}/{len(pdfs)} PDFs...*", parse_mode=ParseMode.MARKDOWN)
                except: pass
                
            engine = WatermarkEngine(data)
            success, err_msg = await loop.run_in_executor(executor, engine.process_pdf, pdf_path, out_path, orig_name)
            
            if success and os.path.exists(out_path):
                caption = f"✅ <b>Processed ({i}/{len(pdfs)})</b>\n📄 <code>{html.escape(orig_name)}</code>"
                if await safe_send_document(message, status_msg, out_path, orig_name, caption):
                    success_count += 1
                os.remove(out_path)
                
        if success_count > 0:
            save_user_last_settings(user_id, data)
                
        await status_msg.delete()
        await message.reply_text(f"✅ <b>ZIP Complete!</b>\nSuccess: {success_count}/{len(pdfs)}", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"ZIP error for msg {message.id}: {e}")
        await status_msg.edit_text(f"❌ ZIP Processing Error. Make sure the file isn't corrupted.", parse_mode=ParseMode.MARKDOWN)
        
    finally:
        if os.path.exists(zip_path): os.remove(zip_path)
        if os.path.exists(ext_dir): shutil.rmtree(ext_dir)


if __name__ == '__main__':
    for directory in [DOWNLOAD_DIR, OUTPUT_DIR, ASSETS_DIR, TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    logger.info("🚀 Professional Watermark Bot Starting...")
    time.sleep(1)
    
    try:
        from keep_alive import keep_alive
        keep_alive()
    except Exception as e:
        logger.warning(f"Could not start keep_alive: {e}")
    
    async def main_loop():
        asyncio.create_task(cleanup_task())
        for i in range(MAX_CONCURRENT_TASKS):
            asyncio.create_task(task_worker(i))
        
        await app.start()
        logger.info("✅ Bot has connected to Telegram successfully and is ready for BULK files!")
        await idle()
        await app.stop()

    try:
        app.run(main_loop())
    except Exception as e:
        logger.error(f"Fatal Error during run: {e}")
        time.sleep(5)