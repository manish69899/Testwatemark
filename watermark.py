# watermark.py - PROFESSIONAL PDF Watermark Engine
# IMPROVED: File Size Fix, Better Rendering, Gap Control, Position, Tile Patterns
# ALL FEATURES PRESERVED + NEW: Outline, Advanced Borders, Compression Fix, Auto-Align Custom Footer

import io
import os
import logging
import math
import hashlib
import copy
import gc
from typing import Dict, Tuple, List, Optional, Set
from functools import lru_cache
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WatermarkEngine")

# ============================================
# COLOR DEFINITIONS - 18 Colors
# ============================================
COLORS = {
    # Original colors
    'grey': colors.Color(0.5, 0.5, 0.5),
    'red': colors.Color(0.85, 0.15, 0.15),
    'blue': colors.Color(0.15, 0.35, 0.85),
    'green': colors.Color(0.10, 0.54, 0.20, alpha=1.0),
    'purple': colors.Color(0.55, 0.15, 0.65),
    'orange': colors.Color(0.92, 0.45, 0.10),
    'yellow': colors.Color(0.88, 0.82, 0.10),
    'white': colors.Color(1, 1, 1),
    'black': colors.Color(0, 0, 0),
    'cyan': colors.Color(0.05, 0.75, 0.80),
    'pink': colors.Color(0.98, 0.15, 0.45, alpha=1.0),    # 🔥 Monokai Cyber Pink (Keywords ke liye)
    'brown': colors.Color(0.50, 0.28, 0.10),
    'gold': colors.Color(0.82, 0.62, 0.10),
    'silver': colors.Color(0.72, 0.72, 0.72),
    'navy': colors.Color(0.10, 0.20, 0.45),
    'teal': colors.Color(0.10, 0.50, 0.50),
    'maroon': colors.Color(0.55, 0.10, 0.20),
    # NEW colors
    'indigo': colors.Color(0.29, 0.00, 0.51),
    'coral': colors.Color(1.0, 0.50, 0.31),
    'olive': colors.Color(0.50, 0.50, 0.00),
}

# ============================================
# GAP SETTINGS - NEW FEATURE
# ============================================
GAP_SIZES = {
    'small': 120,
    'medium': 200,
    'large': 300,
}

# ============================================
# LAYER CACHE - FIXED: Return COPY not same object
# ============================================
_layer_cache: Dict[str, bytes] = {}  # Store bytes, not BytesIO
MAX_CACHE_SIZE = 30

def _get_cache_key(width: float, height: float, settings: dict) -> str:
    """Generate unique cache key for watermark layer"""
    key_data = (
        f"{width:.0f}_{height:.0f}_"
        f"{settings.get('style')}_"
        f"{settings.get('color')}_"
        f"{settings.get('opacity')}_"
        f"{settings.get('fontsize')}_"
        f"{settings.get('rotation')}_"
        f"{settings.get('content', '')[:30]}_"
        f"{settings.get('shadow')}_"
        f"{settings.get('border_style')}_"
        f"{settings.get('border_width')}_"
        f"{settings.get('double_layer')}_"
        f"{settings.get('gradient_effect')}_"
        f"{settings.get('gap')}_"
        f"{settings.get('position')}_"
        f"{settings.get('outline')}_"
        f"{settings.get('tile_pattern')}_"
        f"{settings.get('channel_wm_text', '')}_"
        f"{str(settings.get('footer_parts', []))}_"
        f"{settings.get('footer_align', 'right')}"
    )
    return hashlib.md5(key_data.encode()).hexdigest()

def safe_int(value, default=0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
import os
import io
import math
import logging
from typing import Tuple

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Assume logger, COLORS, GAP_SIZES, safe_float, safe_int, MAX_CACHE_SIZE, _layer_cache, _get_cache_key are defined above

class WatermarkEngine:
    def __init__(self, settings: dict):
        self.settings = settings or {}
        
        # --- Core Settings ---
        self.content_type = self.settings.get('type') or 'text'
        self.content = self.settings.get('content') or ''
        self.style = self.settings.get('style') or 'diagonal'
        self.opacity = safe_float(self.settings.get('opacity'), 0.3)
        self.color_name = self.settings.get('color') or 'grey'
        self.fontsize = safe_int(self.settings.get('fontsize'), 48)
        self.rotation = safe_int(self.settings.get('rotation'), 45)
        self.imgsize = safe_int(self.settings.get('imgsize'), 150)
        
        # --- Border Settings ---
        self.border_style = self.settings.get('border_style') or 'simple'
        self.border_color_name = self.settings.get('border_color') or 'grey'
        self.border_width = safe_int(self.settings.get('border_width'), 2)
        
        # --- Effects & Layout ---
        shadow_flag = self.settings.get('shadow')
        self.shadow = shadow_flag is True or shadow_flag == 'yes' or self.settings.get('add_shadow') is True
        
        self.page_range = self.settings.get('page_range') or 'all'
        
        self.gap_setting = self.settings.get('gap', 'medium')
        if isinstance(self.gap_setting, (int, float)):
            self.gap = safe_int(self.gap_setting, 200)
        else:
            self.gap = GAP_SIZES.get(self.gap_setting, 200)
        
        self.position = self.settings.get('position', 'center')
        self.tile_pattern = self.settings.get('tile_pattern', 'grid')
        self.outline = self.settings.get('outline', False)
        self.outline_width = safe_int(self.settings.get('outline_width'), 2)
        
        self.double_layer = self.settings.get('double_layer', False)
        self.double_layer_offset = safe_int(self.settings.get('double_layer_offset'), 5)
        self.double_layer_color = self.settings.get('double_layer_color', 'black')
        self.gradient_effect = self.settings.get('gradient_effect', False)
        
        # --- Custom Font Handling ---
        self.font_path = self.settings.get('font_path', '')
        self.font_name = 'Helvetica-Bold'
        self._custom_font_loaded = False
        
        def load_custom_font(path, fallback='Helvetica-Bold'):
            if path and os.path.exists(path):
                try:
                    fname = f'CustomFont_{hash(path) % 10000}'
                    pdfmetrics.registerFont(TTFont(fname, path))
                    return fname
                except Exception as e:
                    # using logger if defined globally
                    try: logger.warning(f"Font error {path}: {e}")
                    except: pass
            return fallback

        if self.font_path:
            self.font_name = load_custom_font(self.font_path, 'Helvetica-Bold')
            if self.font_name != 'Helvetica-Bold':
                self._custom_font_loaded = True

        # === PREMIUM: CHANNEL & MULTI-COLOR FOOTER ===
        self.channel_wm_text = self.settings.get('channel_wm_text', '')
        self.channel_wm_font_path = self.settings.get('channel_wm_font', '')
        self.channel_wm_font_name = load_custom_font(self.channel_wm_font_path, 'Helvetica-Bold')
        
        self.footer_parts = self.settings.get('footer_parts', [])
        self.footer_align = self.settings.get('footer_align', 'right')
        for part in self.footer_parts:
            part['font_name'] = load_custom_font(part.get('font'), 'Helvetica-Bold')
        # =============================================

        self.links = self.settings.get('links') or []
        if not isinstance(self.links, list):
            self.links = []
        
        self.text_color = COLORS.get(self.color_name, COLORS.get('grey', colors.grey))
        self.border_color = COLORS.get(self.border_color_name, COLORS.get('grey', colors.grey))

    def create_watermark_layer(self, width: float, height: float) -> io.BytesIO:
        cache_key = _get_cache_key(width, height, self.settings)
        if cache_key in _layer_cache:
            return io.BytesIO(_layer_cache[cache_key])
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        
        # Dispatch table for styles
        style_method = {
            'diagonal': self._draw_diagonal,
            'grid': self._draw_grid,
            'topright': lambda c, w, h: self._draw_corner(c, w, h, 'topright'),
            'bottomleft': lambda c, w, h: self._draw_corner(c, w, h, 'bottomleft'),
            'overlay': self._draw_overlay,
            'border': self._draw_border,
            'header': self._draw_header,
            'footer': self._draw_footer,
        }.get(self.style, self._draw_diagonal)
        
        style_method(can, width, height)
        
        if self.double_layer and self.content_type == 'text':
            self._draw_double_layer(can, width, height)
            
        # === PREMIUM FEATURE DRAWS ===
        if self.channel_wm_text:
            self._draw_channel_watermark(can, width, height)
            
        if self.footer_parts:
            self._draw_custom_footer(can, width, height)
        # =============================
        
        for link in self.links:
            if isinstance(link, dict) and link.get('url'):
                self._draw_link_button(can, width, height, link)
        
        can.save()
        packet.seek(0)
        data = packet.read()
        
        if len(_layer_cache) < MAX_CACHE_SIZE:
            _layer_cache[cache_key] = data
            
        return io.BytesIO(data)

    def _draw_text_with_shadow(self, can: canvas.Canvas, x: float, y: float, 
                                text: str, draw_func="drawString"):
        can.saveState()
        if self.outline and self.content_type == 'text':
            can.setStrokeColor(colors.black)
            can.setLineWidth(self.outline_width)
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            if draw_func == "drawCentredString": can.drawCentredString(x, y, text)
            else: can.drawString(x, y, text)
            can.restoreState()
            return
        
        if self.shadow:
            shadow_opacity = self.opacity * 0.3
            offset_base = max(2, self.fontsize // 12)
            for layer in range(3, 0, -1):
                can.setFillColor(COLORS.get('black', colors.black))
                can.setFillAlpha(shadow_opacity * (layer / 6))
                offset = offset_base * layer
                if draw_func == "drawCentredString": can.drawCentredString(x + offset, y - offset, text)
                else: can.drawString(x + offset, y - offset, text)
        
        if self.gradient_effect:
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity * 0.6)
            if draw_func == "drawCentredString": can.drawCentredString(x, y, text)
            else: can.drawString(x, y, text)
            
            can.setFillAlpha(self.opacity)
            if draw_func == "drawCentredString": can.drawCentredString(x + 0.5, y + 0.5, text)
            else: can.drawString(x + 0.5, y + 0.5, text)
        else:
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            if draw_func == "drawCentredString": can.drawCentredString(x, y, text)
            else: can.drawString(x, y, text)
        can.restoreState()

    def _get_position_coords(self, w: float, h: float) -> Tuple[float, float]:
        positions = {
            'center': (w / 2, h / 2),
            'topright': (w * 0.75, h * 0.75),
            'topleft': (w * 0.25, h * 0.75),
            'bottomleft': (w * 0.25, h * 0.25),
            'bottomright': (w * 0.75, h * 0.25),
            'topcenter': (w / 2, h * 0.75),
            'bottomcenter': (w / 2, h * 0.25),
        }
        return positions.get(self.position, (w / 2, h / 2))

    def _draw_double_layer(self, can: canvas.Canvas, w: float, h: float):
        if self.content_type != 'text' or not self.content: return
        can.saveState()
        x, y = self._get_position_coords(w, h)
        can.translate(x, y)
        can.rotate(self.rotation + 90)
        second_color = COLORS.get(self.double_layer_color, COLORS.get('black', colors.black))
        can.setFillColor(second_color)
        can.setFillAlpha(self.opacity * 0.12)
        can.setFont(self.font_name, self.fontsize * 0.75)
        offset = self.double_layer_offset * 3
        can.drawCentredString(offset, offset, self.content)
        can.restoreState()

    def _draw_diagonal(self, can: canvas.Canvas, w: float, h: float):
        can.saveState()
        x, y = self._get_position_coords(w, h)
        can.translate(x, y)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            can.setFont(self.font_name, self.fontsize)
            self._draw_text_with_shadow(can, 0, 0, self.content, "drawCentredString")
            
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            can.setFillAlpha(self.opacity)
            size = self.imgsize
            try:
                can.drawImage(self.content, -size/2, -size/2, width=size, height=size, mask='auto', preserveAspectRatio=True)
            except Exception as e:
                try: logger.error(f"Image error: {e}")
                except: pass
        can.restoreState()

    def _draw_grid(self, can: canvas.Canvas, w: float, h: float):
        if self.tile_pattern == 'honeycomb': return self._draw_honeycomb(can, w, h)
        elif self.tile_pattern == 'wave': return self._draw_wave_pattern(can, w, h)
        elif self.tile_pattern == 'spiral': return self._draw_spiral_pattern(can, w, h)
        
        can.saveState()
        can.translate(w / 2, h / 2)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            fontsize = max(14, self.fontsize // 2)
            can.setFont(self.font_name, fontsize)
        else:
            fontsize = 18
            
        gap = self.gap
        extent = int(math.hypot(w, h) / 2) + gap
        
        for x in range(-extent, extent + 1, gap):
            for y in range(-extent, extent + 1, gap):
                if self.content_type == 'text' and self.content:
                    self._draw_text_with_shadow(can, x, y, self.content, "drawCentredString")
                elif self.content_type == 'image' and self.content and os.path.exists(self.content):
                    size = self.imgsize // 2
                    can.setFillAlpha(self.opacity)
                    try: 
                        can.drawImage(self.content, x - size/2, y - size/2, width=size, height=size, mask='auto')
                    except Exception: 
                        pass
        can.restoreState()

    def _draw_honeycomb(self, can: canvas.Canvas, w: float, h: float):
        can.saveState()
        fontsize = max(14, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        gap = self.gap
        row = 0
        y = h + gap
        while y > -gap:
            x_offset = (row % 2) * (gap / 2)
            x = x_offset
            while x < w + gap:
                can.saveState()
                can.translate(x, y)
                can.rotate(self.rotation)
                if self.content_type == 'text' and self.content:
                    self._draw_text_with_shadow(can, 0, 0, self.content, "drawCentredString")
                can.restoreState()
                x += gap
            y -= gap * 0.866
            row += 1
        can.restoreState()

    def _draw_wave_pattern(self, can: canvas.Canvas, w: float, h: float):
        can.saveState()
        fontsize = max(14, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        gap = self.gap
        amplitude = gap * 0.3
        y = gap
        wave_idx = 0
        while y < h + gap:
            x = gap
            while x < w + gap:
                wave_offset = math.sin(x * 0.02 + wave_idx) * amplitude
                can.saveState()
                can.translate(x, y + wave_offset)
                can.rotate(self.rotation)
                if self.content_type == 'text' and self.content:
                    self._draw_text_with_shadow(can, 0, 0, self.content, "drawCentredString")
                can.restoreState()
                x += gap
            y += gap
            wave_idx += 0.5
        can.restoreState()

    def _draw_spiral_pattern(self, can: canvas.Canvas, w: float, h: float):
        can.saveState()
        can.translate(w/2, h/2)
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        theta = 0
        radius = 30
        while radius < min(w, h) / 2:
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            fade = 1 - (radius / (min(w, h) / 2)) * 0.5
            can.saveState()
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity * fade)
            can.drawCentredString(x, y, self.content)
            can.restoreState()
            theta += 0.4
            radius += max(2, self.gap // 20)
        can.restoreState()

    def _draw_corner(self, can: canvas.Canvas, w: float, h: float, corner: str):
        margin = 50
        fontsize = max(14, self.fontsize // 2)
        if corner == 'topright': x, y = w - margin, h - margin - fontsize
        else: x, y = margin, margin
        
        can.saveState()
        if self.content_type == 'text' and self.content:
            can.setFont(self.font_name, fontsize)
            if corner == 'topright':
                text_width = can.stringWidth(self.content, self.font_name, fontsize)
                self._draw_text_with_shadow(can, x - text_width, y, self.content, "drawString")
            else:
                self._draw_text_with_shadow(can, x, y, self.content, "drawString")
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            size = self.imgsize // 2
            can.setFillAlpha(self.opacity)
            if corner == 'topright': can.drawImage(self.content, x - size, y - size, width=size, height=size, mask='auto')
            else: can.drawImage(self.content, x, y, width=size, height=size, mask='auto')
        can.restoreState()

    def _draw_overlay(self, can: canvas.Canvas, w: float, h: float):
        if self.content_type != 'text' or not self.content: return
        can.saveState()
        fontsize = self.fontsize
        gap = max(fontsize * 4, self.gap)
        for y_offset in range(int(h + w), int(-h - w), -gap):
            can.saveState()
            can.translate(0, y_offset)
            can.rotate(-45)
            can.setFont(self.font_name, fontsize)
            text = self.content + "  •  "
            text_width = can.stringWidth(text, self.font_name, fontsize)
            x = -w
            while x < w * 2:
                self._draw_text_with_shadow(can, x, 0, text, "drawString")
                x += text_width * 1.2
            can.restoreState()
        can.restoreState()

    def _draw_border(self, can: canvas.Canvas, w: float, h: float):
        margin = 25
        inner_margin = margin + 8
        bwidth = max(1, self.border_width)
        
        can.saveState()
        can.setStrokeColor(self.border_color)
        can.setFillColor(self.border_color)
        can.setFillAlpha(self.opacity)
        
        border_methods = {
            'simple': lambda: self._draw_simple_border(can, w, h, margin, bwidth),
            'double': lambda: self._draw_double_border(can, w, h, margin, inner_margin, bwidth),
            'thick': lambda: self._draw_thick_border(can, w, h, margin, bwidth),
            'dotted': lambda: self._draw_dotted_border(can, w, h, margin, bwidth),
            'star': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '★'),
            'diamond': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '◆'),
            'circle': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '●'),
            'square': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '■'),
            'glitter': lambda: self._draw_glitter_border(can, w, h, margin, bwidth),
            'elegant': lambda: self._draw_elegant_border(can, w, h, margin, bwidth),
            'flower': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '✿'),
            'corporate': lambda: self._draw_corporate_border(can, w, h, margin, bwidth),
            'wave': lambda: self._draw_wave_border(can, w, h, margin, bwidth),
            'gradient': lambda: self._draw_gradient_border(can, w, h, margin, bwidth),
            'stamp': lambda: self._draw_stamp_border(can, w, h, margin, bwidth),
            'artdeco': lambda: self._draw_artdeco_border(can, w, h, margin, bwidth),
            'neon': lambda: self._draw_neon_border(can, w, h, margin, bwidth),
            'ornament': lambda: self._draw_ornament_border(can, w, h, margin, bwidth),
            'dashdot': lambda: self._draw_dashdot_border(can, w, h, margin, bwidth),
            'certificate': lambda: self._draw_certificate_border(can, w, h, margin, bwidth),
        }
        method = border_methods.get(self.border_style, border_methods['simple'])
        method()
        can.restoreState()
        
        if self.content_type == 'text' and self.content:
            can.saveState()
            can.setFont(self.font_name, 12)
            text_width = can.stringWidth(self.content, self.font_name, 12)
            self._draw_text_with_shadow(can, (w - text_width) / 2, margin - 12, self.content, "drawString")
            can.restoreState()

    # --- Border Drawing Utilities ---
    def _draw_simple_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_double_border(self, can, w, h, margin, inner_margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        can.setLineWidth(max(1, bwidth - 1))
        can.rect(inner_margin, inner_margin, w - 2*inner_margin, h - 2*inner_margin, stroke=1, fill=0)

    def _draw_thick_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth + 4)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_dotted_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.setDash([4, 4], 0) 
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_symbol_border(self, can, w, h, margin, bwidth, symbol):
        self._draw_corner_symbols(can, w, h, margin, symbol)
        can.setLineWidth(bwidth)
        can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)

    def _draw_glitter_border(self, can, w, h, margin, bwidth):
        self._draw_corner_symbols(can, w, h, margin, '✦')
        can.setLineWidth(bwidth)
        can.setDash([2, 3], 0) 
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_elegant_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(1)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        corner_len = 25
        can.setLineWidth(2)
        corners = [(margin, margin, 1, 1), (margin, h - margin, 1, -1), (w - margin, margin, -1, 1), (w - margin, h - margin, -1, -1)]
        for x, y, dx, dy in corners:
            can.line(x, y, x + corner_len * dx, y)
            can.line(x, y, x, y + corner_len * dy)

    def _draw_corporate_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth + 3)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        can.setLineWidth(1)
        can.rect(margin + 6, margin + 6, w - 2*margin - 12, h - 2*margin - 12, stroke=1, fill=0)

    def _draw_corner_symbols(self, can, w, h, margin, symbol):
        can.setFont('Helvetica', 16)
        positions = [(margin - 8, margin - 8), (margin - 8, h - margin - 8), (w - margin - 12, margin - 8), (w - margin - 12, h - margin - 8)]
        for x, y in positions:
            can.drawString(x, y, symbol)

    def _draw_wave_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        points = 60
        p = can.beginPath()
        p.moveTo(margin, h - margin)
        for i in range(points + 1):
            x = margin + (w - 2*margin) * i / points
            y = h - margin + math.sin(i * 0.4) * 5
            p.lineTo(x, y)
        can.drawPath(p, stroke=1, fill=0)
        p = can.beginPath()
        p.moveTo(margin, margin)
        for i in range(points + 1):
            x = margin + (w - 2*margin) * i / points
            y = margin + math.sin(i * 0.4) * 5
            p.lineTo(x, y)
        can.drawPath(p, stroke=1, fill=0)
        can.line(margin, margin, margin, h - margin)
        can.line(w - margin, margin, w - margin, h - margin)

    def _draw_gradient_border(self, can, w, h, margin, bwidth):
        for i in range(5):
            offset = i * 3
            can.setStrokeColor(self.border_color)
            can.setFillAlpha(self.opacity * (1 - i * 0.15))
            can.setLineWidth(bwidth + i * 2)
            can.rect(margin + offset, margin + offset, w - 2*margin - 2*offset, h - 2*margin - 2*offset, stroke=1, fill=0)

    def _draw_stamp_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin + 10, margin + 10, w - 2*margin - 20, h - 2*margin - 20, stroke=1, fill=0)
        for i in range(int((w - 2*margin) / 12)):
            x = margin + 12 + i * 12
            can.circle(x, h - margin, 3, stroke=1, fill=0)
            can.circle(x, margin, 3, stroke=1, fill=0)
        for i in range(int((h - 2*margin) / 12)):
            y = margin + 12 + i * 12
            can.circle(margin, y, 3, stroke=1, fill=0)
            can.circle(w - margin, y, 3, stroke=1, fill=0)

    def _draw_artdeco_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        corner_size = 25
        corners = [(margin, margin, 1, 1), (margin, h - margin, 1, -1), (w - margin, margin, -1, 1), (w - margin, h - margin, -1, -1)]
        for x, y, dx, dy in corners:
            can.setLineWidth(1)
            can.line(x, y, x + corner_size * dx, y)
            can.line(x, y, x, y + corner_size * dy)
            can.line(x + corner_size * dx * 0.5, y, x + corner_size * dx * 0.5, y + corner_size * dy * 0.5)
            can.line(x, y + corner_size * dy * 0.5, x + corner_size * dx * 0.5, y + corner_size * dy * 0.5)

    def _draw_neon_border(self, can, w, h, margin, bwidth):
        for i in range(8, 0, -1):
            can.setStrokeColor(self.border_color)
            can.setFillAlpha(self.opacity * (i / 16))
            can.setLineWidth(bwidth + i * 2)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_ornament_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)
        ornaments = ['❖', '◆', '✧', '✦']
        can.setFont('Helvetica', 18)
        positions = [(margin + 5, h - margin - 12), (w - margin - 18, h - margin - 12), (margin + 5, margin + 2), (w - margin - 18, margin + 2)]
        for (x, y), ornament in zip(positions, ornaments):
            can.drawString(x, y, ornament)

    def _draw_dashdot_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.setDash([10, 3, 2, 3], 0) 
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_certificate_border(self, can, w, h, margin, bwidth):
        for offset in [0, 5, 10]:
            can.setLineWidth(bwidth - offset // 4)
            can.rect(margin + offset, margin + offset, w - 2*margin - 2*offset, h - 2*margin - 2*offset, stroke=1, fill=0)
        can.setFont('Helvetica', 20)
        can.drawString(margin - 3, h - margin - 10, '❮')
        can.drawString(w - margin - 12, h - margin - 10, '❯')
        can.drawString(margin - 3, margin - 2, '❮')
        can.drawString(w - margin - 12, margin - 2, '❯')

    def _draw_header(self, can: canvas.Canvas, w: float, h: float):
        if self.content_type != 'text' or not self.content: return
        can.saveState()
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, h - 35, w - 30, h - 35)
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        text_width = can.stringWidth(self.content, self.font_name, fontsize)
        self._draw_text_with_shadow(can, (w - text_width) / 2, h - 28, self.content, "drawString")
        can.restoreState()

    def _draw_footer(self, can: canvas.Canvas, w: float, h: float):
        if self.content_type != 'text' or not self.content: return
        can.saveState()
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, 30, w - 30, 30)
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        text_width = can.stringWidth(self.content, self.font_name, fontsize)
        self._draw_text_with_shadow(can, (w - text_width) / 2, 12, self.content, "drawString")
        can.restoreState()

    # ============================================
    # 🌟 PREMIUM FEATURE: MAC/APPLE STYLE BUTTON 🌟
    # ============================================
    def _draw_link_button(self, can: canvas.Canvas, w: float, h: float, link: dict):
        try:
            url = link.get('url', '')
            position = link.get('position', 'bottomcenter')
            text = link.get('text', '🔗 CLICK HERE')
            if not url: return
            
            if 'top' in position: y_pos = h - 22
            else: y_pos = 18
            
            if 'left' in position: x_pos = 80
            elif 'right' in position: x_pos = w - 80
            else: x_pos = w / 2
            
            can.saveState()
            can.setFont('Helvetica-Bold', 10)
            text_width = can.stringWidth(text, 'Helvetica-Bold', 10)
            btn_w = text_width + 24 # Thodi extra padding UI ke liye
            btn_h = 20
            x1 = x_pos - btn_w / 2
            y1 = y_pos - btn_h / 2
            
            # --- Mac Style Soft Shadow ---
            for i in range(1, 4):
                can.setFillColor(colors.Color(0, 0, 0, alpha=0.015 * (4 - i)))
                can.roundRect(x1 + (i*0.5), y1 - (i*0.5), btn_w, btn_h, 6, stroke=0, fill=1)
            
            # --- Clean White Pill Background ---
            can.setFillColor(colors.Color(0.98, 0.98, 0.99, alpha=0.95))
            can.setStrokeColor(colors.Color(0.88, 0.88, 0.90, alpha=0.9))
            can.setLineWidth(0.5)
            can.roundRect(x1, y1, btn_w, btn_h, 6, stroke=1, fill=1)
            
            # --- Premium Blue Text & Subtle 3D Shadow ---
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.08)) # Text Shadow
            can.drawCentredString(x_pos + 0.5, y_pos - 3.5, text)
            
            can.setFillColor(colors.Color(0.1, 0.4, 0.8, alpha=1.0)) # Crisp Blue Text
            can.drawCentredString(x_pos, y_pos - 3, text)
            
            # Make it clickable
            can.linkURL(url, (x1, y1, x1 + btn_w, y1 + btn_h), relative=1)
            can.restoreState()
        except Exception as e:
            try: logger.error(f"Link error: {e}")
            except: pass

    # ============================================
    # 🌟 PREMIUM FEATURE: STAGGERED CHANNEL GRID 🌟
    # ============================================
    def _draw_channel_watermark(self, can: canvas.Canvas, w: float, h: float) -> None:
        if not self.channel_wm_text:
            return

        can.saveState()
        FONT_SIZE = 36
        ALPHA = 0.05
        text_color = COLORS.get('grey', colors.Color(0.5, 0.5, 0.5)) 

        text_width = can.stringWidth(self.channel_wm_text, self.channel_wm_font_name, FONT_SIZE)
        GAP_X = int(max(350, text_width + 120)) 
        GAP_Y = 220                             
        
        can.translate(w / 2.0, h / 2.0)
        can.rotate(45)
        can.setFont(self.channel_wm_font_name, FONT_SIZE)
        can.setFillColor(text_color)
        can.setFillAlpha(ALPHA)
        
        diagonal = math.hypot(w, h)
        extent = int(diagonal / 2) + GAP_X
        
        row_num = 0
        for y in range(-extent, extent + GAP_Y, GAP_Y):
            x_offset = (GAP_X // 2) if (row_num % 2 != 0) else 0
            for x in range(-extent - x_offset, extent + GAP_X, GAP_X):
                can.drawCentredString(x + x_offset, y, self.channel_wm_text)
            row_num += 1

        can.restoreState()

    # ============================================
    # 🌟 PREMIUM FEATURE: MAC/APPLE STYLE FOOTER 🌟
    # ============================================
    def _draw_custom_footer(self, can: canvas.Canvas, w: float, h: float) -> None:
        can.saveState()
        font_size = 12
        total_width = 0
        
        for part in self.footer_parts:
            fname = part.get('font_name', 'Helvetica-Bold')
            total_width += can.stringWidth(f"{part.get('text', '')} ", fname, font_size)
            
        cursor_width = can.stringWidth("_", "Helvetica-Bold", font_size)
        total_width += cursor_width
            
        margin = 30
        if self.footer_align == 'left': start_x = margin
        elif self.footer_align == 'center': start_x = (w - total_width) / 2
        else: start_x = w - margin - total_width
            
        has_border = self.border_style and self.border_style not in ('skip', 'none')
        y_pos = 32 if has_border else 20

        padding_x = 14
        padding_y = 7
        border_radius = 8
        
        bg_x = start_x - padding_x
        bg_y = y_pos - padding_y + 2
        bg_w = total_width + (padding_x * 2)
        bg_h = font_size + (padding_y * 2) - 2

        for i in range(1, 4):
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.015 * (4 - i)))
            can.roundRect(bg_x + (i * 0.5), bg_y - (i * 0.5), bg_w, bg_h, radius=border_radius, stroke=0, fill=1)

        can.setFillColor(colors.Color(0.98, 0.98, 0.99, alpha=0.95)) 
        can.setStrokeColor(colors.Color(0.88, 0.88, 0.90, alpha=0.9)) 
        can.setLineWidth(0.5)
        can.roundRect(bg_x, bg_y, bg_w, bg_h, radius=border_radius, stroke=1, fill=1)
            
        current_x = start_x
        for part in self.footer_parts:
            fname = part.get('font_name', 'Helvetica-Bold')
            color_obj = COLORS.get(part.get('color', 'grey'), COLORS.get('grey', colors.grey))
            text_to_draw = f"{part.get('text', '')} "
            
            can.setFont(fname, font_size)
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.08))
            can.drawString(current_x + 0.5, y_pos - 0.5, text_to_draw)
            
            can.setFillColor(color_obj)
            can.setFillAlpha(1.0)
            can.drawString(current_x, y_pos, text_to_draw)
            
            current_x += can.stringWidth(text_to_draw, fname, font_size)

        can.setFillColor(colors.Color(0.2, 0.4, 0.8, alpha=0.8))
        can.drawString(current_x, y_pos, "_")
            
        can.restoreState()
   # ============================================
    # PREMIUM FEATURE: STAGGERED CHANNEL GRID
    # ============================================
    def _draw_channel_watermark(self, can: canvas.Canvas, w: float, h: float) -> None:
        """
        Draws an ultra-premium diagonal watermark grid.
        Uses a staggered (brick-lay) pattern with dynamic spacing to prevent overlaps.
        """
        # Agar text nahi hai, toh faltu draw mat karo
        if not getattr(self, 'channel_wm_text', None):
            return

        can.saveState()

        # --- Premium Configuration ---
        FONT_NAME = getattr(self, 'channel_wm_font_name', 'Helvetica-Bold')
        FONT_SIZE = 36
        ALPHA = 0.05  # 0.05 se 0.06 ke beech premium subtle look aata hai
        
        # Default fallback to light grey if COLORS dict is missing
        text_color = COLORS.get('grey', colors.Color(0.5, 0.5, 0.5)) 

        # --- Dynamic Gap Calculation ---
        # Text ki width nikalo taaki lambe naam overlap na hon
        text_width = can.stringWidth(self.channel_wm_text, FONT_NAME, FONT_SIZE)
        GAP_X = int(max(350, text_width + 120)) # Kam se kam 120px ki padding har text ke beech
        GAP_Y = 220                             # Line height ka gap
        
        # --- Setup Canvas ---
        can.translate(w / 2.0, h / 2.0)
        can.rotate(45)
        can.setFont(FONT_NAME, FONT_SIZE)
        can.setFillColor(text_color)
        can.setFillAlpha(ALPHA)
        
        # Calculate optimal coverage area using hypotenuse (Clean Math)
        import math
        diagonal = math.hypot(w, h)
        extent = int(diagonal / 2) + GAP_X
        
        # --- 🌟 THE MAGIC: STAGGERED GRID (BRICK PATTERN) ---
        row_num = 0
        for y in range(-extent, extent + GAP_Y, GAP_Y):
            
            # Har alternate row ko X_GAP ke aaghey (half) se shift kar do
            x_offset = (GAP_X // 2) if (row_num % 2 != 0) else 0
            
            for x in range(-extent - x_offset, extent + GAP_X, GAP_X):
                can.drawCentredString(x + x_offset, y, self.channel_wm_text)
                
            row_num += 1

        can.restoreState()

    # ============================================
    # PREMIUM FEATURE: VS CODE MULTI-COLOR FOOTER
    # ============================================
    def _draw_custom_footer(self, can: canvas.Canvas, w: float, h: float):
        """Draws an AWESOME custom multi-color footer (VS Code / Terminal Style)"""
        can.saveState()
        font_size = 12 # Thoda bold aur premium size
        
        total_width = 0
        for part in self.footer_parts:
            fname = part.get('font_name', 'Helvetica-Bold')
            total_width += can.stringWidth(part['text'] + " ", fname, font_size)
            
        # Add space for terminal cursor
        cursor_width = can.stringWidth("_", "Helvetica-Bold", font_size)
        total_width += cursor_width
            
        align = self.footer_align
        margin = 30 # Safe edge margin
        
        if align == 'left':
            start_x = margin
        elif align == 'center':
            start_x = (w - total_width) / 2
        else: # Right (Default)
            start_x = w - margin - total_width
            
        # AUTOMATIC Y-POSITION FIX: 
        if self.border_style and self.border_style != 'skip' and self.border_style != 'none':
            y_pos = 5  # Exactly sitting on top of the border line!
        else:
            y_pos = 20  # Normal position

        # --- 🌟 NEW: PREMIUM MAC/APPLE STYLE "PILL" ---
        padding_x = 14  # Thoda extra space breathing ke liye
        padding_y = 7
        border_radius = 8 # Thoda zyada rounded modern look ke liye
        
        bg_x = start_x - padding_x
        bg_y = y_pos - padding_y + 2
        bg_w = total_width + (padding_x * 2)
        bg_h = font_size + (padding_y * 2) - 2

        # 1. Diffused Soft Drop Shadow (Apple Style)
        # Ek hard shadow ki jagah 3 soft layers jo dreere-dheere fade hoti hain
        for i in range(1, 4):
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.015 * (4 - i)))
            can.roundRect(bg_x + (i * 0.5), bg_y - (i * 0.5), bg_w, bg_h, radius=border_radius, stroke=0, fill=1)

        # 2. Ultra-Clean Premium Background
        # Ekdum slight off-white/greyish tone jo aankhon ko chubhe nahi
        can.setFillColor(colors.Color(0.98, 0.98, 0.99, alpha=0.95)) 
        # Very subtle crisp border
        can.setStrokeColor(colors.Color(0.88, 0.88, 0.90, alpha=0.9)) 
        can.setLineWidth(0.5)
        can.roundRect(bg_x, bg_y, bg_w, bg_h, radius=border_radius, stroke=1, fill=1)
        # ---------------------------------------------------------
            
        current_x = start_x
        
        for part in self.footer_parts:
            fname = part.get('font_name', 'Helvetica-Bold')
            color_obj = COLORS.get(part.get('color', 'grey'), COLORS['grey'])
            text_to_draw = part['text'] + " "
            
            can.setFont(fname, font_size)
            
            # --- 🌟 SUBTLE TEXT 3D SHADOW (Refined) ---
            # Alpha 0.15 se 0.08 kar diya taaki text blurry na lage, bas thoda pop kare
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.08))
            can.drawString(current_x + 0.5, y_pos - 0.5, text_to_draw)
            
            # Main Text
            can.setFillColor(color_obj)
            can.setFillAlpha(1.0) # Ekdum solid aur bright
            can.drawString(current_x, y_pos, text_to_draw)
            
            current_x += can.stringWidth(text_to_draw, fname, font_size)

        # --- 🌟 NEW: ELEGANT BLUE ACCENT CURSOR ---
        # Light background pe slight blue terminal cursor bahut premium lagta hai
        can.setFillColor(colors.Color(0.2, 0.4, 0.8, alpha=0.8))
        can.drawString(current_x, y_pos, "_")
            
        can.restoreState()

    # ============================================
    # PROCESS PDF
    # ============================================
    def process_pdf(self, input_path: str, output_path: str, 
                    filename: str = "document.pdf",
                    progress_callback=None) -> Tuple[bool, str]:
        try:
            if not os.path.exists(input_path): return False, "Input file not found"
            
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            if total_pages == 0: return False, "PDF has no pages"
            
            logger.info(f"📄 Processing: {filename} | Pages: {total_pages}")
            writer = PdfWriter()
            pages_to_watermark = self._get_pages_to_watermark(total_pages)
            
            if pages_to_watermark:
                first_page = reader.pages[0]
                try:
                    page_width = float(first_page.mediabox.width)
                    page_height = float(first_page.mediabox.height)
                except:
                    page_width, page_height = 612.0, 792.0
                
                watermark_packet = self.create_watermark_layer(page_width, page_height)
                watermark_pdf = PdfReader(watermark_packet)
                watermark_page = watermark_pdf.pages[0]
            
            for index, page in enumerate(reader.pages):
                if progress_callback and index % 10 == 0:
                    try: progress_callback(index + 1, total_pages)
                    except: pass
                
                if index in pages_to_watermark:
                    page.merge_page(watermark_page)
                
                writer.add_page(page)
            
            if self.settings.get('add_metadata'):
                self._add_metadata(writer, filename)
            
            try: writer.remove_duplicates()
            except: pass
            
            writer.compress_identical_objects = True
            try:
                for page in writer.pages:
                    page.compress_content_streams()
            except Exception as e:
                logger.warning(f"Content stream compression warning: {e}")
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            size_change = ((new_size - original_size) / original_size) * 100 if original_size > 0 else 0
            
            logger.info(f"✅ Done: {filename} | Size: {original_size/1024:.1f}KB → {new_size/1024:.1f}KB ({size_change:+.1f}%)")
            gc.collect()
            
            return True, f"Processed {total_pages} pages"
            
        except Exception as e:
            error = f"Error: {str(e)}"
            logger.error(error)
            return False, error

    def _get_pages_to_watermark(self, total_pages: int) -> Set[int]:
        if self.page_range == 'all': return set(range(total_pages))
        elif self.page_range == 'first': return {0} if total_pages > 0 else set()
        elif self.page_range == 'last': return {total_pages - 1} if total_pages > 0 else set()
        else:
            pages = set()
            try:
                parts = str(self.page_range).split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = part.split('-')
                        start = int(start.strip()) - 1 
                        end = int(end.strip()) 
                        pages.update(range(max(0, start), min(end, total_pages)))
                    else:
                        page = int(part) - 1 
                        if 0 <= page < total_pages:
                            pages.add(page)
            except Exception as e:
                logger.warning(f"Invalid page range: {self.page_range}, using all. Error: {e}")
                pages = set(range(total_pages))
            
            return pages

    def _add_metadata(self, writer: PdfWriter, filename: str):
        author = self.settings.get('author') or 'Aryan Bot'
        location = self.settings.get('location') or 'Your Heart'
        metadata = {
            '/Title': filename,
            '/Author': author,
            '/Producer': '𝖑𝖔𝖈𝖆𝖑𝖍𝖔𝖘𝖙[Aryan]',
            '/Subject': f'Watermarked - {location}',
            '/Keywords': 'PDF,𝖑𝖔𝖈𝖆𝖑𝖍𝖔𝖘𝖙',
            '/Creator': 'Created by Aryan and localhost, Telegram @hilocalhost'
        }
        writer.add_metadata(metadata)

def add_watermark_to_pdf(input_path: str, output_path: str, 
                         settings: dict, filename: str = "document.pdf") -> bool:
    engine = WatermarkEngine(settings)
    success, message = engine.process_pdf(input_path, output_path, filename)
    if not success: logger.error(message)
    return success

def get_pdf_page_count(input_path: str) -> int:
    try:
        reader = PdfReader(input_path)
        return len(reader.pages)
    except:
        return 0

def validate_pdf_file(input_path: str) -> Tuple[bool, str]:
    try:
        reader = PdfReader(input_path)
        return True, f"Valid PDF with {len(reader.pages)} pages"
    except Exception as e:
        return False, f"Invalid PDF: {str(e)}"

def clear_cache():
    global _layer_cache
    _layer_cache.clear()
    gc.collect()
    logger.info("🗑️ Layer cache cleared")