# keyboards.py - PREMIUM CUSTOM FOOTER KEYBOARDS
# STRIPPED DOWN: Removed all unnecessary bloat (borders, styles, shadows, etc.)
# KEPT ONLY: Colors, Fonts, Alignment, and Flow Controls.

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional

# ============================================
# MAIN MENU KEYBOARD
# ============================================
def get_main_menu_keyboard():
    """Main menu at start - Kept it simple and direct"""
    keyboard = [
        [InlineKeyboardButton("💻 Set Premium Custom Footer", callback_data='menu_footer')],
        [InlineKeyboardButton("🔤 Upload Custom Font (.ttf)", callback_data='menu_font')],
        [InlineKeyboardButton("🗑️ Clear All Settings", callback_data='clear_footer')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# COLOR KEYBOARD - 18 Premium Colors
# ============================================
def get_color_keyboard(selected: Optional[str] = None):
    """Text color selection - 18 colors for individual footer parts"""
    color_list = [
        ('⚫ Grey', 'color_grey'), ('🔴 Red', 'color_red'),
        ('🔵 Blue', 'color_blue'), ('🟢 Green', 'color_green'),
        ('🟣 Purple', 'color_purple'), ('🟠 Orange', 'color_orange'),
        ('🟡 Gold', 'color_gold'), ('⚪ Silver', 'color_silver'),
        ('🖤 Black', 'color_black'), ('💎 Cyan', 'color_cyan'),
        ('🩷 Pink', 'color_pink'), ('🟤 Brown', 'color_brown'),
        ('⚓ Navy', 'color_navy'), ('🩵 Teal', 'color_teal'),
        ('❤️ Maroon', 'color_maroon'), ('💜 Indigo', 'color_indigo'),
        ('🔶 Coral', 'color_coral'), ('🌿 Olive', 'color_olive')
    ]
    
    keyboard = []
    row = []
    for name, data in color_list:
        if selected and data == f'color_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        # 2 buttons per row for a clean UI
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# FOOTER ALIGNMENT KEYBOARD
# ============================================
def get_footer_align_keyboard():
    """Lets user choose exactly where the Custom Footer will sit on the PDF"""
    keyboard = [
        [InlineKeyboardButton("⬅️ Align Left", callback_data='falign_left')],
        [InlineKeyboardButton("⏺️ Align Center", callback_data='falign_center')],
        [InlineKeyboardButton("➡️ Align Right", callback_data='falign_right')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# FLOW CONTROL KEYBOARDS (Skip & Done)
# ============================================
def get_skip_font_keyboard():
    """Button to skip uploading a custom font and use default"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ Skip (Use Default Font)", callback_data='skip_footer_font')]
    ])

def get_footer_add_more_keyboard():
    """Keyboard to add more text parts or finish setup"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Next Text Part", callback_data='footer_add_more')],
        [InlineKeyboardButton("✅ Done (Choose Alignment)", callback_data='footer_done')]
    ])

# ============================================
# CANCEL KEYBOARD (For Tasks)
# ============================================
def get_cancel_keyboard(task_id: str):
    """Cancel button during PDF processing"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Process", callback_data=f"cancel_{task_id}")]
    ])