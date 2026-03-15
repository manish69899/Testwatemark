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
from typing import Dict
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="pypdf")

from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, FloodWait, RPCError

# CONFIG & KEYBOARDS
from config import (
    BOT_TOKEN, API_ID, API_HASH, DOWNLOAD_DIR, OUTPUT_DIR, 
    ASSETS_DIR, TEMP_DIR, LOGS_DIR, USE_MEMORY_SESSION, MAX_CONCURRENT_TASKS,
    SESSION_TIMEOUT_SECONDS, CLEANUP_INTERVAL, MAX_STORAGE_MB, MAX_DOWNLOAD_SIZE,
    USER_PREFS_FILE, cleanup_temp_files, get_storage_usage
)
import keyboards as kb

# WATERMARK ENGINE
from watermark import WatermarkEngine, get_pdf_page_count

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("WatermarkBot")

class FilterPyrogramSpam(logging.Filter):
    SPAM_MESSAGES = ["PingTask", "NetworkTask", "Session started", "Session stopped", "Device:", "System:", "Disconnected"]
    def filter(self, record):
        return not any(spam in record.getMessage() for spam in self.SPAM_MESSAGES)

logging.getLogger("pyrogram").addFilter(FilterPyrogramSpam())

# ============================================
# GLOBALS & QUEUE
# ============================================
executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)
main_task_queue = asyncio.Queue()
task_status: Dict[str, str] = {} 
user_data: Dict[int, dict] = {}
processing_tasks: Dict[int, bool] = {}

BOT_START_TIME = time.time()

app = Client(
    "WatermarkBotSession",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=USE_MEMORY_SESSION,
    max_concurrent_transmissions=3
)

# ============================================
# DATA MANAGEMENT
# ============================================
def create_default_data() -> dict:
    return {
        'step': None,
        'footer_parts': [],
        'temp_footer_text': '',
        'temp_footer_font': '',
        'footer_align': 'center',
        'last_activity': time.time()
    }

def get_data(user_id: int) -> dict:
    if user_id not in user_data:
        user_data[user_id] = create_default_data()
    return user_data[user_id]

def clear_data(user_id: int):
    user_data[user_id] = create_default_data()

def is_old_message(message: Message) -> bool:
    if message.date and message.date.timestamp() < BOT_START_TIME:
        return True
    return False

# ============================================
# TRACKERS & SENDERS
# ============================================
class ProgressTracker:
    def __init__(self, message, user_id):
        self.message = message
        self.user_id = user_id
        self.last_update = 0
    
    async def update(self, current: int, total: int):
        now = time.time()
        if now - self.last_update < 3: return
        self.last_update = now
        percent = int((current / total) * 100)
        try:
            await self.message.edit_text(f"⚙️ *Processing...*\n\n📄 Page {current}/{total}\n📊 {percent}% complete", parse_mode=ParseMode.MARKDOWN)
        except: pass

class UploadTracker:
    def __init__(self, message):
        self.message = message
        self.last_update = 0
        
    async def update(self, current: int, total: int):
        now = time.time()
        if now - self.last_update < 3: return
        self.last_update = now
        percent = int((current / total) * 100)
        curr_mb, tot_mb = current/(1024*1024), total/(1024*1024)
        try:
            await self.message.edit_text(f"⬆️ *Uploading Final PDF...*\n\n📊 {percent}% ({curr_mb:.1f}MB / {tot_mb:.1f}MB)", parse_mode=ParseMode.MARKDOWN)
        except: pass

async def safe_send_document(message: Message, status_msg: Message, document_path: str, filename: str, caption: str, max_retries=3):
    upload_tracker = UploadTracker(status_msg)
    for attempt in range(max_retries):
        try:
            await message.reply_document(
                document=document_path, file_name=filename, caption=caption, 
                parse_mode=ParseMode.HTML, progress=upload_tracker.update
            )
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except RPCError as e:
            if attempt < max_retries - 1: await asyncio.sleep(5)
            else: raise e
        except Exception as e:
            if attempt < max_retries - 1: await asyncio.sleep(4)
            else: raise e
    return False

# ============================================
# COMMANDS
# ============================================
@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    if is_old_message(message): return
    clear_data(message.from_user.id)
    text = (
        "👋 *PREMIUM PDF FOOTER BOT*\n\n"
        "Welcome! Generate ultra-premium Mac/VS-Code style multi-color footers for your PDFs.\n\n"
        "🚀 Click below to start setting up your custom footer!"
    )
    await message.reply_text(text, reply_markup=kb.get_main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("reset"))
async def cmd_reset(client: Client, message: Message):
    if is_old_message(message): return
    clear_data(message.from_user.id)
    await message.reply_text("🔄 *Settings Cleared!*\n\nClick below to start fresh:", reply_markup=kb.get_main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)

# ============================================
# TEXT INPUT HANDLER
# ============================================
@app.on_message(filters.text & ~filters.command(["start", "reset"]))
async def handle_text(client: Client, message: Message):
    if is_old_message(message): return
    user_id = message.from_user.id
    data = get_data(user_id)
    text = message.text.strip()
    
    if data.get('step') == 'waiting_footer_text':
        data['temp_footer_text'] = text
        data['step'] = 'waiting_footer_font'
        await message.reply_text(
            f"✅ Text Saved: `{text}`\n\n🔤 *Upload a custom .ttf font* for this part, OR click Skip to use Default.",
            reply_markup=kb.get_skip_font_keyboard(), parse_mode=ParseMode.MARKDOWN
        )

# ============================================
# DOCUMENT HANDLER (FONTS, PDF, ZIP)
# ============================================
@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    if is_old_message(message): return
    user_id = message.from_user.id
    data = get_data(user_id)
    filename = message.document.file_name or "file.dat"
    ext = filename.lower().split('.')[-1]
    
    if ext in ['ttf', 'otf']:
        status = await message.reply_text("⏳ Downloading Font...", parse_mode=ParseMode.MARKDOWN)
        font_path = os.path.join(ASSETS_DIR, f"font_{user_id}_{message.id}.ttf")
        await message.download(file_name=font_path)
        
        if data.get('step') == 'waiting_footer_font':
            data['temp_footer_font'] = font_path
            data['step'] = 'waiting_footer_color'
            await status.edit_text("✅ *Font Saved!*\n\nNow choose *COLOR* for this text part:", reply_markup=kb.get_color_keyboard(), parse_mode=ParseMode.MARKDOWN)
        else:
            await status.edit_text("⚠️ Font received, but you are not setting up a footer right now.")
        return
        
    if not data.get('footer_parts'):
        await message.reply_text("⚠️ Please set up your custom footer first!\nUse /start to begin.", parse_mode=ParseMode.MARKDOWN)
        return
        
    if ext not in ['pdf', 'zip']:
        await message.reply_text("⚠️ Please send a PDF or ZIP file.", parse_mode=ParseMode.MARKDOWN)
        return

    task_id = f"{message.chat.id}_{message.id}"
    task_status[task_id] = "pending"
    cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{task_id}")]])
    
    status_msg = await message.reply_text(
        f"⏳ *Added to Queue*\n\n📄 File: `{filename}`\n_Please wait..._",
        reply_markup=cancel_kb, parse_mode=ParseMode.MARKDOWN
    )
    
    await main_task_queue.put({
        'id': task_id, 'client': client, 'message': message,
        'data': copy.deepcopy(data), 'filename': filename,
        'status_msg': status_msg, 'is_zip': ext == 'zip'
    })

# ============================================
# CALLBACK QUERIES
# ============================================
@app.on_callback_query()
async def handle_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    cb = query.data
    data = get_data(user_id)

    if cb.startswith('cancel_'):
        task_id = cb.replace('cancel_', '')
        task_status[task_id] = "cancelled"
        try: await query.edit_message_text("❌ *Task Cancelled!*", parse_mode=ParseMode.MARKDOWN)
        except: pass
        return

    await query.answer()
    
    try:
        if cb == 'menu_footer' or cb == 'footer_add_more':
            data['step'] = 'waiting_footer_text'
            data['temp_footer_text'] = ''
            data['temp_footer_font'] = ''
            await query.edit_message_text("📝 Send the Text for this part of the footer (e.g., `<Aryan />` or `By localhost`):")
            
        elif cb == 'clear_footer':
            data['footer_parts'] = []
            data['step'] = None
            await query.edit_message_text("🗑️ Footer Cleared! Start over:", reply_markup=kb.get_main_menu_keyboard())
            
        elif cb == 'skip_footer_font':
            data['temp_footer_font'] = ''
            data['step'] = 'waiting_footer_color'
            await query.edit_message_text("✅ Font skipped. Choose *COLOR* for this text:", reply_markup=kb.get_color_keyboard())
            
        elif cb.startswith('color_'):
            if data.get('step') == 'waiting_footer_color':
                data['footer_parts'].append({
                    'text': data.get('temp_footer_text', ''),
                    'font': data.get('temp_footer_font', ''),
                    'color': cb.replace('color_', '')
                })
                data['step'] = None
                await query.edit_message_text(
                    f"✅ Part Saved!\n\nDo you want to add another word next to it, or are you done?", 
                    reply_markup=kb.get_footer_add_more_keyboard()
                )
                
        elif cb == 'footer_done':
            await query.edit_message_text("📍 Where should the footer be aligned?", reply_markup=kb.get_footer_align_keyboard())
            
        elif cb.startswith('falign_'):
            data['footer_align'] = cb.replace('falign_', '')
            data['step'] = None
            await query.edit_message_text(f"✅ **Footer Setup Complete!**\nAlignment: {data['footer_align'].upper()}\n\n📂 **Now send me the PDF or ZIP file!**", parse_mode=ParseMode.MARKDOWN)

    except MessageNotModified:
        pass

# ============================================
# PROCESSING ENGINE (PDF & ZIP)
# ============================================
async def task_worker(worker_id: int):
    while True:
        task = await main_task_queue.get()
        task_id = task['id']
        try:
            if task_status.get(task_id) == "cancelled":
                await task['status_msg'].edit_text("❌ *Cancelled*", parse_mode=ParseMode.MARKDOWN)
                continue
            task_status[task_id] = "processing"
            
            if task['is_zip']: await execute_zip_processing(task)
            else: await execute_pdf_processing(task)
            
        except Exception as e:
            logger.error(f"Worker Error: {e}")
        finally:
            if task_id in task_status: del task_status[task_id]
            main_task_queue.task_done()
            gc.collect()

# EXACT CODE SNIPPET PROVIDED BY YOU
async def execute_pdf_processing(task: dict):
    message, status_msg = task['message'], task['status_msg']
    data, original_filename = task['data'], task['filename']
    user_id = message.from_user.id
    
    # 🌟 ISOLATED TASK FOLDER (Easy to delete everything at once) 🌟
    task_dir = os.path.join(TEMP_DIR, f"task_{task['id']}")
    os.makedirs(task_dir, exist_ok=True)
    
    # Output folder inside task dir to maintain the EXACT filename
    out_dir = os.path.join(task_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    input_path = os.path.join(task_dir, original_filename) 
    output_path = os.path.join(out_dir, original_filename) # EXACT same name!
    
    try:
        await status_msg.edit_text("⬇️ *Downloading file...*", parse_mode=ParseMode.MARKDOWN)
        await message.download(file_name=input_path)
        
        if task_status.get(task['id']) == "cancelled": return
            
        pages = get_pdf_page_count(input_path)
        progress = ProgressTracker(status_msg, user_id)
        await status_msg.edit_text(f"🎨 *Applying Footer...* ({pages} pages)", parse_mode=ParseMode.MARKDOWN)
        
        loop = asyncio.get_event_loop()
        engine = WatermarkEngine(data)
        
        def sync_progress(c, t):
            if task_status.get(task['id']) != "cancelled":
                asyncio.run_coroutine_threadsafe(progress.update(c, t), loop)
                
        # Process PDF
        success, err_msg = await loop.run_in_executor(executor, engine.process_pdf, input_path, output_path, sync_progress)
        
        if task_status.get(task['id']) == "cancelled": return
            
        if success and os.path.exists(output_path):
            orig_mb = os.path.getsize(input_path) / (1024 * 1024)
            new_mb = os.path.getsize(output_path) / (1024 * 1024)
            align = data.get('footer_align', 'center')
            
            # 🌟 BEAUTIFUL CAPTION WITH FILE INFO 🌟
            caption = (
                f"✅ <b>PREMIUM FOOTER APPLIED!</b>\n\n"
                f"📄 <b>File Name:</b> <code>{html.escape(original_filename)}</code>\n"
                f"📋 <b>Total Pages:</b> {pages}\n"
                f"💻 <b>Alignment:</b> {align.upper()}\n"
                f"📦 <b>Original Size:</b> {orig_mb:.2f} MB\n"
                f"📦 <b>New Size:</b> {new_mb:.2f} MB"
            )
            
            upload_success = await safe_send_document(message, status_msg, output_path, original_filename, caption)
            if upload_success:
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Upload failed due to Telegram limits.")
        else:
            await status_msg.edit_text(f"❌ Failed: {err_msg}")
            
    except Exception as e:
        logger.error(f"PDF error: {e}")
        await status_msg.edit_text(f"❌ Processing error. File might be protected.", parse_mode=ParseMode.MARKDOWN)
        
    finally:
        # 🌟 STRICT SERVER CLEANUP (0% STORAGE LEAK) 🌟
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir, ignore_errors=True)
        # Force garbage collection to free RAM immediately
        gc.collect()

async def execute_zip_processing(task: dict):
    # ZIP processing with the same isolated task folder logic
    message, status_msg = task['message'], task['status_msg']
    data, original_filename = task['data'], task['filename']
    
    task_dir = os.path.join(TEMP_DIR, f"task_{task['id']}")
    os.makedirs(task_dir, exist_ok=True)
    
    zip_path = os.path.join(task_dir, original_filename)
    ext_dir = os.path.join(task_dir, "extracted")
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
            
            out_dir = os.path.join(task_dir, f"out_{i}")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, orig_name) # Exact name maintain!
            
            if i % 3 == 0 or i == len(pdfs):
                try: await status_msg.edit_text(f"⚙️ *Processing {i}/{len(pdfs)} PDFs...*", parse_mode=ParseMode.MARKDOWN)
                except: pass
                
            engine = WatermarkEngine(data)
            success, _ = await loop.run_in_executor(executor, engine.process_pdf, pdf_path, out_path, None)
            
            if success and os.path.exists(out_path):
                caption = f"✅ <b>Processed ({i}/{len(pdfs)})</b>\n📄 <code>{html.escape(orig_name)}</code>"
                if await safe_send_document(message, status_msg, out_path, orig_name, caption):
                    success_count += 1
                
        await status_msg.delete()
        await message.reply_text(f"✅ <b>ZIP Complete!</b>\nSuccess: {success_count}/{len(pdfs)}", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"ZIP error: {e}")
        await status_msg.edit_text(f"❌ ZIP Processing Error.", parse_mode=ParseMode.MARKDOWN)
    finally:
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir, ignore_errors=True)
        gc.collect()

# ============================================
# RUN BOT - DEBUGGING ENABLED
# ============================================
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 BOT SCRIPT STARTING...")
    print("="*50)
    
    # 1. Ensure Directories Exist
    print("📁 Checking directories...")
    for directory in [DOWNLOAD_DIR, OUTPUT_DIR, ASSETS_DIR, TEMP_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # 2. Start Keep-Alive Server
    print("🌐 Starting Keep-Alive server...")
    try:
        from keep_alive import keep_alive
        keep_alive()
        print("✅ Keep-Alive Server Started")
    except Exception as e:
        print(f"⚠️ Keep-alive load nahi hua: {e}")

    # 3. Main Async Loop
    async def main_loop():
        print("⏳ Background Workers start ho rahe hain...")
        for i in range(MAX_CONCURRENT_TASKS):
            asyncio.create_task(task_worker(i))
        
        print("🔌 Telegram se connect kar raha hu... (Checking API Keys)")
        await app.start()
        print("\n" + "★"*50)
        print("✅ BOT IS PERFECTLY RUNNING ONLINE!")
        print("★"*50 + "\n")
        
        await idle()
        print("🛑 Bot ruk gaya hai.")
        await app.stop()

    # 4. Run the Loop safely
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_loop())
    except KeyboardInterrupt:
        print("\n🛑 Process manually stopped by user.")
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")