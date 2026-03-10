# keyboards.py - PROFESSIONAL Inline Keyboards for Watermark Bot
# IMPROVED: All Features + NEW: Gap Control, Position, Tile Patterns, Fixed Typos
# Features: Green Selection, 8 Styles, 20 Borders, 18 Colors, Quick Presets, Gap/Spacing

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional, List

# ============================================
# QUICK PRESETS KEYBOARD (FAST UX)
# ============================================
def get_quick_presets_keyboard():
    """Quick presets for instant watermark - ONE CLICK SETUP"""
    keyboard = [
        [InlineKeyboardButton("⚡ Quick Diagonal (Grey, 30%)", callback_data='preset_diagonal_grey')],
        [InlineKeyboardButton("🔥 Bold Red (70%, Shadow)", callback_data='preset_bold_red')],
        [InlineKeyboardButton("💎 Elegant Blue (25%)", callback_data='preset_elegant_blue')],
        [InlineKeyboardButton("🔲 Border Frame (Grey)", callback_data='preset_border_grey')],
        [InlineKeyboardButton("📝 Header Style (Black)", callback_data='preset_header_black')],
        [InlineKeyboardButton("✨ Double Layer Pro", callback_data='preset_double_layer')],
        [InlineKeyboardButton("🎨 Custom Settings", callback_data='preset_custom')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# MAIN MENU KEYBOARD (UPDATED)
# ============================================
def get_main_menu_keyboard():
    """Main menu at start"""
    keyboard = [
        [InlineKeyboardButton("📝 Text Watermark", callback_data='menu_text')],
        [InlineKeyboardButton("🖼️ Image/Logo Watermark", callback_data='menu_image')],
        # === NEW PREMIUM FEATURES ===
        [InlineKeyboardButton("📢 Set Channel Watermark", callback_data='menu_channel')],
        [InlineKeyboardButton("💻 Set Custom Multi-Color Footer", callback_data='menu_footer')],
        # ============================
        [InlineKeyboardButton("🔤 Upload Custom Font", callback_data='menu_font')],
        [InlineKeyboardButton("⚡ Quick Presets", callback_data='menu_presets')],
        [InlineKeyboardButton("❓ Help", callback_data='menu_help')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# STYLE KEYBOARD - 8 Styles with GREEN selection
# ============================================
def get_style_keyboard(selected: Optional[str] = None):
    """Watermark style selection - selected style turns GREEN"""
    styles = [
        ('📍 Diagonal Center', 'style_diagonal'),
        ('▦ Grid / Tiled', 'style_grid'),
        ('↗️ Top Right Corner', 'style_topright'),
        ('↙️ Bottom Left Corner', 'style_bottomleft'),
        ('⬛ Full Page Overlay', 'style_overlay'),
        ('🔲 Border Frame', 'style_border'),
        ('📄 Header Only', 'style_header'),
        ('📋 Standard Text Footer', 'style_footer')
    ]
    
    keyboard = []
    for name, data in styles:
        if selected and data == f'style_{selected}':
            keyboard.append([InlineKeyboardButton(f"✅ {name}", callback_data=data)])
        else:
            keyboard.append([InlineKeyboardButton(name, callback_data=data)])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# NEW: GAP/SPACING KEYBOARD FOR GRID/TILES
# ============================================
def get_gap_keyboard(selected: Optional[str] = None):
    """Gap/Spacing control for diagonal/grid/tile patterns - NEW FEATURE"""
    gaps = [
        ('🔸 Tight Gap (120px)', 'gap_small'),
        ('🔹 Balanced Gap (200px)', 'gap_medium'),
        ('🔶 Wide Gap (300px)', 'gap_large'),
        ('📏 Custom Gap', 'gap_custom')
    ]
    
    keyboard = []
    for name, data in gaps:
        if selected and data == f'gap_{selected}':
            keyboard.append([InlineKeyboardButton(f"✅ {name}", callback_data=data)])
        else:
            keyboard.append([InlineKeyboardButton(name, callback_data=data)])
    
    keyboard.append([InlineKeyboardButton("➡️ Continue with Default", callback_data='gap_default')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# NEW: TILE PATTERN KEYBOARD
# ============================================
def get_tile_pattern_keyboard(selected: Optional[str] = None):
    """Tile pattern selection for grid style - NEW FEATURE"""
    patterns = [
        ('📐 Grid (Square)', 'tpattern_grid'),
        ('🔷 Honeycomb (Hex)', 'tpattern_honeycomb'),
        ('🌊 Wave Pattern', 'tpattern_wave'),
        ('🌀 Spiral Pattern', 'tpattern_spiral')
    ]
    
    keyboard = []
    for name, data in patterns:
        if selected and data == f'tpattern_{selected}':
            keyboard.append([InlineKeyboardButton(f"✅ {name}", callback_data=data)])
        else:
            keyboard.append([InlineKeyboardButton(name, callback_data=data)])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# NEW: POSITION KEYBOARD FOR WATERMARK
# ============================================
def get_position_keyboard(selected: Optional[str] = None):
    """Watermark position selection - NEW FEATURE"""
    positions = [
        ('🎯 Center (Default)', 'pos_center'),
        ('↗️ Top Right', 'pos_topright'),
        ('↖️ Top Left', 'pos_topleft'),
        ('↙️ Bottom Left', 'pos_bottomleft'),
        ('↘️ Bottom Right', 'pos_bottomright'),
        ('⬆️ Top Center', 'pos_topcenter'),
        ('⬇️ Bottom Center', 'pos_bottomcenter')
    ]
    
    keyboard = []
    for name, data in positions:
        if selected and data == f'pos_{selected}':
            keyboard.append([InlineKeyboardButton(f"✅ {name}", callback_data=data)])
        else:
            keyboard.append([InlineKeyboardButton(name, callback_data=data)])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# BORDER STYLE KEYBOARD - 20 Styles (EXPANDED)
# ============================================
def get_border_style_keyboard(selected: Optional[str] = None):
    """Border style selection - 20 different border styles"""
    borders = [
        # Original 12 styles
        ('━ Simple Line', 'bstyle_simple'),
        ('═ Double Line', 'bstyle_double'),
        ('▓ Thick Border', 'bstyle_thick'),
        ('░ Dotted Border', 'bstyle_dotted'),
        ('✦ Star Border', 'bstyle_star'),
        ('◆ Diamond Border', 'bstyle_diamond'),
        ('● Circle Border', 'bstyle_circle'),
        ('■ Square Border', 'bstyle_square'),
        ('★ Glitter Border', 'bstyle_glitter'),
        ('◈ Elegant Border', 'bstyle_elegant'),
        ('✿ Flower Border', 'bstyle_flower'),
        ('❖ Corporate Border', 'bstyle_corporate'),
        # NEW: 8 Advanced styles
        ('〰️ Wave Border', 'bstyle_wave'),
        ('🌈 Gradient Border', 'bstyle_gradient'),
        ('📮 Stamp Border', 'bstyle_stamp'),
        ('🏛️ Art Deco Border', 'bstyle_artdeco'),
        ('💡 Neon Glow Border', 'bstyle_neon'),
        ('❧ Ornament Border', 'bstyle_ornament'),
        ('➖ Dash-Dot Border', 'bstyle_dashdot'),
        ('🎖️ Certificate Border', 'bstyle_certificate')
    ]
    
    keyboard = []
    row = []
    for name, data in borders:
        if selected and data == f'bstyle_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Skip Border Style", callback_data='bstyle_skip')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# BORDER COLOR KEYBOARD - 18 Colors (EXPANDED)
# ============================================
def get_border_color_keyboard(selected: Optional[str] = None):
    """Border color selection - 18 colors"""
    colors = [
        ('⚫ Grey', 'bcolor_grey'),
        ('🔴 Red', 'bcolor_red'),
        ('🔵 Blue', 'bcolor_blue'),
        ('🟢 Green', 'bcolor_green'),
        ('🟣 Purple', 'bcolor_purple'),
        ('🟠 Orange', 'bcolor_orange'),
        ('🟡 Gold', 'bcolor_gold'),
        ('⚪ Silver', 'bcolor_silver'),
        ('🖤 Black', 'bcolor_black'),
        ('💎 Cyan', 'bcolor_cyan'),
        ('🩷 Pink', 'bcolor_pink'),
        ('🟤 Brown', 'bcolor_brown'),
        ('⚓ Navy', 'bcolor_navy'),
        ('🩵 Teal', 'bcolor_teal'),
        ('❤️ Maroon', 'bcolor_maroon'),
        # NEW colors
        ('💜 Indigo', 'bcolor_indigo'),
        ('🔶 Coral', 'bcolor_coral'),
        ('🌿 Olive', 'bcolor_olive')
    ]
    
    keyboard = []
    row = []
    for name, data in colors:
        if selected and data == f'bcolor_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# BORDER WIDTH KEYBOARD
# ============================================
def get_border_width_keyboard(selected: Optional[str] = None):
    """Border width/thickness selection"""
    widths = [
        ('┄ Thin (1pt)', 'bwidth_1'),
        ('─ Normal (2pt)', 'bwidth_2'),
        ('━ Medium (3pt)', 'bwidth_3'),
        ('█ Thick (5pt)', 'bwidth_5'),
        ('▓ Extra Thick (8pt)', 'bwidth_8'),
        ('█ Bold (10pt)', 'bwidth_10')
    ]
    
    keyboard = []
    row = []
    for name, data in widths:
        if selected and data == f'bwidth_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# COLOR KEYBOARD - 18 Colors for Text (EXPANDED)
# ============================================
def get_color_keyboard(selected: Optional[str] = None):
    """Watermark text color selection - 18 colors"""
    color_list = [
        ('⚫ Grey', 'color_grey'),
        ('🔴 Red', 'color_red'),
        ('🔵 Blue', 'color_blue'),
        ('🟢 Green', 'color_green'),
        ('🟣 Purple', 'color_purple'),
        ('🟠 Orange', 'color_orange'),
        ('🟡 Yellow', 'color_yellow'),
        ('⚪ White', 'color_white'),
        ('🖤 Black', 'color_black'),
        ('💎 Cyan', 'color_cyan'),
        ('🩷 Pink', 'color_pink'),
        ('🟤 Brown', 'color_brown'),
        ('⚓ Navy', 'color_navy'),
        ('🩵 Teal', 'color_teal'),
        ('❤️ Maroon', 'color_maroon'),
        # NEW colors
        ('💜 Indigo', 'color_indigo'),
        ('🔶 Coral', 'color_coral'),
        ('🌿 Olive', 'color_olive')
    ]
    
    keyboard = []
    row = []
    for name, data in color_list:
        if selected and data == f'color_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# OPACITY KEYBOARD - 8 Levels
# ============================================
def get_opacity_keyboard(selected: Optional[str] = None):
    """Opacity selection - 8 levels"""
    opacities = [
        ('☁️ Very Light (5%)', 'opac_0.05'),
        ('🌤 Light (10%)', 'opac_0.1'),
        ('⛅ Normal (20%)', 'opac_0.2'),
        ('🌤 Medium (30%)', 'opac_0.3'),
        ('🌥 Semi (50%)', 'opac_0.5'),
        ('🌩 Dark (70%)', 'opac_0.7'),
        ('🌧 Bold (85%)', 'opac_0.85'),
        ('⛈ Solid (95%)', 'opac_0.95')
    ]
    
    keyboard = []
    row = []
    for name, data in opacities:
        if selected and data == f'opac_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# FONT SIZE KEYBOARD - 8 Sizes
# ============================================
def get_fontsize_keyboard(selected: Optional[str] = None):
    """Font size selection - 8 sizes"""
    sizes = [
        ('🔍 XS (20pt)', 'fsize_20'),
        ('📝 Small (30pt)', 'fsize_30'),
        ('📰 Medium (40pt)', 'fsize_40'),
        ('📢 Large (50pt)', 'fsize_50'),
        ('📖 XL (60pt)', 'fsize_60'),
        ('🏛️ XXL (72pt)', 'fsize_72'),
        ('🔥 Huge (84pt)', 'fsize_84'),
        ('👑 Giant (96pt)', 'fsize_96')
    ]
    
    keyboard = []
    row = []
    for name, data in sizes:
        if selected and data == f'fsize_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# ROTATION KEYBOARD
# ============================================
def get_rotation_keyboard(selected: Optional[str] = None):
    """Rotation angle selection"""
    rotations = [
        ('↗️ 45° Diagonal', 'rot_45'),
        ('➡️ 0° Horizontal', 'rot_0'),
        ('↙️ -45° Reverse', 'rot_-45'),
        ('⬇️ 90° Vertical', 'rot_90'),
        ('↖️ -90° Vertical', 'rot_-90'),
        ('🔄 Custom Angle', 'rot_custom')
    ]
    
    keyboard = []
    row = []
    for name, data in rotations:
        if selected and data == f'rot_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# IMAGE SIZE KEYBOARD (For Logo)
# ============================================
def get_imgsize_keyboard(selected: Optional[str] = None):
    """Logo image size selection"""
    sizes = [
        ('🔹 Small (60px)', 'isize_60'),
        ('🔸 Medium (100px)', 'isize_100'),
        ('🔶 Large (150px)', 'isize_150'),
        ('⭐ XL (200px)', 'isize_200'),
        ('📖 XXL (250px)', 'isize_250'),
        ('🏛️ Huge (300px)', 'isize_300')
    ]
    
    keyboard = []
    row = []
    for name, data in sizes:
        if selected and data == f'isize_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# SHADOW KEYBOARD (PREMIUM FEATURE)
# ============================================
def get_shadow_keyboard(selected: Optional[str] = None):
    """Shadow/Glow effect for Text Watermark"""
    keyboard = []
    
    yes_text = "✅ Yes (Add 3D Shadow/Glow)" if selected == 'yes' else "✨ Yes (Add 3D Shadow/Glow)"
    no_text = "✅ No (Flat Text)" if selected == 'no' else "❌ No (Flat Text)"
    
    keyboard.append([InlineKeyboardButton(yes_text, callback_data='shadow_yes')])
    keyboard.append([InlineKeyboardButton(no_text, callback_data='shadow_no')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# NEW: TEXT OUTLINE KEYBOARD
# ============================================
def get_outline_keyboard(selected: Optional[str] = None):
    """Text outline/stroke effect - NEW FEATURE"""
    keyboard = []
    
    yes_text = "✅ Yes (Add Outline)" if selected == 'yes' else "✏️ Yes (Add Text Outline)"
    no_text = "✅ No (No Outline)" if selected == 'no' else "❌ No (No Outline)"
    
    keyboard.append([InlineKeyboardButton(yes_text, callback_data='outline_yes')])
    keyboard.append([InlineKeyboardButton(no_text, callback_data='outline_no')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# NEW: OUTLINE WIDTH KEYBOARD
# ============================================
def get_outline_width_keyboard(selected: Optional[str] = None):
    """Outline thickness selection - NEW FEATURE"""
    widths = [
        ('┄ Thin (1pt)', 'owidth_1'),
        ('─ Normal (2pt)', 'owidth_2'),
        ('━ Medium (3pt)', 'owidth_3'),
        ('█ Thick (4pt)', 'owidth_4'),
        ('▓ Bold (5pt)', 'owidth_5')
    ]
    
    keyboard = []
    row = []
    for name, data in widths:
        if selected and data == f'owidth_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# DOUBLE LAYER KEYBOARD
# ============================================
def get_double_layer_keyboard(selected: Optional[str] = None):
    """Double Layer watermark effect - Professional feature"""
    keyboard = []
    
    yes_text = "✅ Yes (Double Layer)" if selected == 'yes' else "✨ Yes (Double Layer Effect)"
    no_text = "✅ No (Single Layer)" if selected == 'no' else "❌ No (Single Layer)"
    
    keyboard.append([InlineKeyboardButton(yes_text, callback_data='double_yes')])
    keyboard.append([InlineKeyboardButton(no_text, callback_data='double_no')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# DOUBLE LAYER COLOR KEYBOARD
# ============================================
def get_double_layer_color_keyboard(selected: Optional[str] = None):
    """Color for second watermark layer"""
    colors = [
        ('🖤 Black', 'dcolor_black'),
        ('⚫ Grey', 'dcolor_grey'),
        ('🔵 Blue', 'dcolor_blue'),
        ('🔴 Red', 'dcolor_red'),
        ('🟢 Green', 'dcolor_green'),
        ('🟣 Purple', 'dcolor_purple')
    ]
    
    keyboard = []
    row = []
    for name, data in colors:
        if selected and data == f'dcolor_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# GRADIENT EFFECT KEYBOARD
# ============================================
def get_gradient_keyboard(selected: Optional[str] = None):
    """Gradient effect for watermark text"""
    keyboard = []
    
    yes_text = "✅ Yes (Gradient Effect)" if selected == 'yes' else "🌈 Yes (Gradient Effect)"
    no_text = "✅ No (Solid Color)" if selected == 'no' else "❌ No (Solid Color)"
    
    keyboard.append([InlineKeyboardButton(yes_text, callback_data='gradient_yes')])
    keyboard.append([InlineKeyboardButton(no_text, callback_data='gradient_no')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# PAGE RANGE KEYBOARD (PREMIUM FEATURE)
# ============================================
def get_page_range_keyboard(selected: Optional[str] = None):
    """Page Range selection"""
    ranges = [
        ('📑 All Pages', 'prange_all'),
        ('1️⃣ First Page Only', 'prange_first'),
        ('🔚 Last Page Only', 'prange_last'),
        ('🔢 Custom Range', 'prange_custom')
    ]
    
    keyboard = []
    row = []
    for name, data in ranges:
        if selected and data == f'prange_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
        
    return InlineKeyboardMarkup(keyboard)

# ============================================
# LINK KEYBOARDS
# ============================================
def get_link_menu_keyboard(links_count: int = 0):
    """Link management menu"""
    keyboard = []
    
    if links_count < 6:
        keyboard.append([InlineKeyboardButton("➕ Add New Link", callback_data='link_add')])
    
    if links_count > 0:
        keyboard.append([InlineKeyboardButton(f"📋 View Links ({links_count})", callback_data='link_view')])
        keyboard.append([InlineKeyboardButton("🗑️ Clear All Links", callback_data='link_clear')])
    
    keyboard.append([InlineKeyboardButton(f"✅ Done - Continue ({links_count} links)", callback_data='link_done')])
    
    return InlineKeyboardMarkup(keyboard)

def get_link_add_skip_keyboard():
    """Initial link: Add or Skip"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Link", callback_data='link_add')],
        [InlineKeyboardButton("❌ Skip (No Links)", callback_data='link_skip')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_link_position_keyboard(selected: Optional[str] = None):
    """Link position selection - 6 positions"""
    positions = [
        ('⬆️ Top Left', 'lpos_topleft'),
        ('⬆️ Top Center', 'lpos_topcenter'),
        ('⬆️ Top Right', 'lpos_topright'),
        ('⬇️ Bottom Left', 'lpos_bottomleft'),
        ('⬇️ Bottom Center', 'lpos_bottomcenter'),
        ('⬇️ Bottom Right', 'lpos_bottomright')
    ]
    
    keyboard = []
    row = []
    for name, data in positions:
        if selected and data == f'lpos_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_link_text_keyboard(selected: Optional[str] = None):
    """Link button text style"""
    styles = [
        ('🔗 CLICK HERE', 'ltext_click'),
        ('📱 VISIT US', 'ltext_visit'),
        ('🌐 OPEN LINK', 'ltext_open'),
        ('✨ LEARN MORE', 'ltext_learn'),
        ('📝 Custom Text', 'ltext_custom'),
        ('⚡ Show URL', 'ltext_url')
    ]
    
    keyboard = []
    row = []
    for name, data in styles:
        if selected and data == f'ltext_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_add_more_link_keyboard(links_count: int = 0):
    """Ask if user wants to add more links"""
    keyboard = []
    
    if links_count < 6:
        keyboard.append([InlineKeyboardButton("➕ Add Another Link", callback_data='link_add')])
    
    keyboard.append([InlineKeyboardButton(f"✅ Done ({links_count} links added)", callback_data='link_done')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# METADATA KEYBOARD
# ============================================
def get_metadata_keyboard(selected: Optional[str] = None):
    """Metadata: Yes or No"""
    keyboard = []
    
    keyboard.append([InlineKeyboardButton("✅ Yes (Add Metadata)", callback_data='meta_yes')])
    keyboard.append([InlineKeyboardButton("❌ No (Skip)", callback_data='meta_no')])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================
# CONFIRMATION KEYBOARD
# ============================================
def get_confirm_keyboard():
    """Final confirmation before processing"""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Process PDF", callback_data='confirm_yes')],
        [InlineKeyboardButton("🔄 Change Settings", callback_data='confirm_change')],
        [InlineKeyboardButton("❌ Cancel", callback_data='confirm_cancel')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# NEW: PREVIEW KEYBOARD
# ============================================
def get_preview_keyboard():
    """Preview before processing - NEW FEATURE"""
    keyboard = [
        [InlineKeyboardButton("👁️ Show Preview", callback_data='preview_show')],
        [InlineKeyboardButton("✅ Process Without Preview", callback_data='preview_skip')],
        [InlineKeyboardButton("🔄 Change Settings", callback_data='preview_change')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# NEW: FOOTER ALIGNMENT KEYBOARD (PREMIUM)
# ============================================
def get_footer_align_keyboard():
    """Lets user choose exactly where the Custom Footer will sit"""
    keyboard = [
        [InlineKeyboardButton("⬅️ Align Left", callback_data='falign_left')],
        [InlineKeyboardButton("⏺️ Align Center", callback_data='falign_center')],
        [InlineKeyboardButton("➡️ Align Right", callback_data='falign_right')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# SETTINGS KEYBOARD - UPDATED
# ============================================
def get_settings_keyboard():
    """Settings menu to change options"""
    keyboard = [
        # === NEW PREMIUM EDIT BUTTONS ===
        [InlineKeyboardButton("📢 Edit Channel Watermark", callback_data='menu_channel')],
        [InlineKeyboardButton("💻 Edit Custom Footer", callback_data='menu_footer')],
        # ================================
        [InlineKeyboardButton("🎨 Change Style", callback_data='set_style')],
        [InlineKeyboardButton("🌈 Change Color", callback_data='set_color')],
        [InlineKeyboardButton("💡 Change Opacity", callback_data='set_opacity')],
        [InlineKeyboardButton("🔤 Change Font Size", callback_data='set_fontsize')],
        [InlineKeyboardButton("🆎 Change Font Style", callback_data='set_font')],
        [InlineKeyboardButton("🔲 Change Border", callback_data='set_border')],
        [InlineKeyboardButton("✨ Toggle Shadow", callback_data='set_shadow')],
        [InlineKeyboardButton("🎭 Double Layer", callback_data='set_double')],
        [InlineKeyboardButton("🌈 Gradient Effect", callback_data='set_gradient')],
        # NEW: Gap control
        [InlineKeyboardButton("📏 Gap/Spacing", callback_data='set_gap')],
        # NEW: Position
        [InlineKeyboardButton("📍 Position", callback_data='set_position')],
        # NEW: Outline
        [InlineKeyboardButton("✏️ Text Outline", callback_data='set_outline')],
        [InlineKeyboardButton("📄 Change Page Range", callback_data='set_prange')],
        [InlineKeyboardButton("🔗 Manage Links", callback_data='set_links')],
        [InlineKeyboardButton("↩️ Back", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# HELP KEYBOARD
# ============================================
def get_help_keyboard():
    """Help navigation"""
    keyboard = [
        [InlineKeyboardButton("📖 How to Use", callback_data='help_use')],
        [InlineKeyboardButton("🎨 Styles Guide", callback_data='help_styles')],
        [InlineKeyboardButton("🔗 Links Guide", callback_data='help_links')],
        [InlineKeyboardButton("↩️ Back", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# PROGRESS/CANCEL KEYBOARD
# ============================================
def get_cancel_keyboard():
    """Cancel button for long operations"""
    keyboard = [
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_operation')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# EFFECT SEQUENCE KEYBOARD - UPDATED
# ============================================
def get_effects_menu_keyboard():
    """Effects menu after font size selection"""
    keyboard = [
        [InlineKeyboardButton("✨ 3D Shadow Effect", callback_data='effect_shadow')],
        [InlineKeyboardButton("🎭 Double Layer Watermark", callback_data='effect_double')],
        [InlineKeyboardButton("🌈 Gradient Effect", callback_data='effect_gradient')],
        # NEW: Outline effect
        [InlineKeyboardButton("✏️ Text Outline/Stroke", callback_data='effect_outline')],
        [InlineKeyboardButton("➡️ Skip All Effects", callback_data='effect_skip')]
    ]
    return InlineKeyboardMarkup(keyboard)