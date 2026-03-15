# watermark.py - PREMIUM CUSTOM FOOTER ENGINE
# Cleaned, Optimized, Memory Leak Proof + AWESOME 3D MAC OS FEATURES

import io
import os
import gc
import logging
from typing import Tuple, Dict

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WatermarkEngine")

# Premium Colors for Multi-Color Footer
COLORS = {
    'grey': colors.Color(0.5, 0.5, 0.5), 'red': colors.Color(0.85, 0.15, 0.15),
    'blue': colors.Color(0.15, 0.35, 0.85), 'green': colors.Color(0.10, 0.54, 0.20),
    'purple': colors.Color(0.55, 0.15, 0.65), 'orange': colors.Color(0.92, 0.45, 0.10),
    'yellow': colors.Color(0.88, 0.82, 0.10), 'white': colors.Color(1, 1, 1),
    'black': colors.Color(0, 0, 0), 'cyan': colors.Color(0.05, 0.75, 0.80),
    'pink': colors.Color(0.98, 0.15, 0.45), 'brown': colors.Color(0.50, 0.28, 0.10),
    'gold': colors.Color(0.82, 0.62, 0.10), 'silver': colors.Color(0.72, 0.72, 0.72),
    'navy': colors.Color(0.10, 0.20, 0.45), 'teal': colors.Color(0.10, 0.50, 0.50),
    'maroon': colors.Color(0.55, 0.10, 0.20), 'indigo': colors.Color(0.29, 0.00, 0.51),
    'coral': colors.Color(1.0, 0.50, 0.31), 'olive': colors.Color(0.50, 0.50, 0.00),
}

class WatermarkEngine:
    def __init__(self, settings: dict):
        self.settings = settings or {}
        self.footer_parts = self.settings.get('footer_parts', [])
        self.footer_align = self.settings.get('footer_align', 'center')
        
        # Load custom fonts automatically
        for part in self.footer_parts:
            if part.get('font') and os.path.exists(part['font']):
                try:
                    fname = f"CustomFont_{hash(part['font']) % 10000}"
                    pdfmetrics.registerFont(TTFont(fname, part['font']))
                    part['font_name'] = fname
                except Exception as e:
                    logger.error(f"Failed to load font {part['font']}: {e}")
                    part['font_name'] = 'Helvetica-Bold'
            else:
                part['font_name'] = 'Helvetica-Bold'

    def create_footer_layer(self, width: float, height: float) -> io.BytesIO:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        
        if not self.footer_parts:
            can.save()
            packet.seek(0)
            return packet

        # 🌟 1. SMART DYNAMIC FONT SCALING LOGIC 🌟
        # Responsive base font size based on page width
        base_font_size = max(8.0, min(14.0, width * 0.022))
        font_size = base_font_size
        min_font_size = 5.0
        
        # Responsive Margin
        margin = max(20.0, width * 0.04)
        
        # 🌟 2. EXACT COLLISION LIMIT 🌟
        # Calculate maximum allowed width so it NEVER touches the center text
        if self.footer_align in ['left', 'right']:
            max_allowed_width = (width * 0.45) - margin  # Keeps it strictly to its side
        else:
            max_allowed_width = width - (margin * 2)

        def get_total_width(size):
            t_width = 0
            for part in self.footer_parts:
                fname = part.get('font_name', 'Helvetica-Bold')
                t_width += can.stringWidth(f"{part.get('text', '')} ", fname, size)
            t_width += can.stringWidth("_", "Helvetica-Bold", size)
            return t_width

        total_width = get_total_width(font_size)
        
        # Auto-shrink font size if text is too long (Smoothly)
        while total_width > max_allowed_width and font_size > min_font_size:
            font_size -= 0.25
            total_width = get_total_width(font_size)
            
        # 🌟 3. EXACT ALIGNMENT 🌟
        if self.footer_align == 'left': 
            start_x = margin
        elif self.footer_align == 'center': 
            start_x = (width - total_width) / 2
        else: 
            start_x = width - margin - total_width
            
        # 🌟 4. SAFE Y-POSITION & TIGHT PILL MATH 🌟
        # Thoda upar taaki page number (1, 2) overlap na ho
        y_pos = max(7.0, height * 0.03)
        
        # Dynamic Tight Padding
        padding_x = font_size * 0.8  
        padding_y = font_size * 0.45  
        border_radius = font_size * 0.6
        
        bg_x = start_x - padding_x
        bg_y = y_pos - padding_y + (font_size * 0.1)
        bg_w = total_width + (padding_x * 2) - (font_size * 0.2)
        bg_h = font_size + (padding_y * 2)

        can.saveState()

        # 🌟 5. AWESOME 3D MAC-OS DOCK SHADOW 🌟
        # 5 Diffused layers for premium floating effect
        for i in range(1, 6):
            alpha = 0.012 * (6 - i)
            can.setFillColor(colors.Color(0, 0, 0, alpha=alpha))
            can.roundRect(bg_x - (i*0.5), bg_y - (i*0.6), bg_w + i, bg_h + i, radius=border_radius + (i*0.2), stroke=0, fill=1)

        # Main Glass Background (Slightly solid for text readability)
        can.setFillColor(colors.Color(0.98, 0.98, 0.99, alpha=0.90)) 
        can.setStrokeColor(colors.Color(0.85, 0.85, 0.88, alpha=0.8)) 
        can.setLineWidth(0.5)
        can.roundRect(bg_x, bg_y, bg_w, bg_h, radius=border_radius, stroke=1, fill=1)
        
        # 🌟 6. INNER WHITE HIGHLIGHT (3D Bevel) 🌟
        can.setStrokeColor(colors.Color(1, 1, 1, alpha=0.8))
        can.setLineWidth(0.5)
        can.roundRect(bg_x + 0.5, bg_y + 0.5, bg_w - 1, bg_h - 1, radius=max(0, border_radius - 0.5), stroke=1, fill=0)
            
        current_x = start_x
        for part in self.footer_parts:
            fname = part.get('font_name', 'Helvetica-Bold')
            color_obj = COLORS.get(part.get('color', 'grey'), COLORS['grey'])
            text_to_draw = f"{part.get('text', '')} "
            
            can.setFont(fname, font_size)
            
            # Subtle Crisp Text Shadow
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.10))
            can.drawString(current_x + 0.5, y_pos - 0.5, text_to_draw)
            
            # Main Text Color
            can.setFillColor(color_obj)
            can.setFillAlpha(1.0)
            can.drawString(current_x, y_pos, text_to_draw)
            
            current_x += can.stringWidth(text_to_draw, fname, font_size)

        # 🌟 7. NEON TERMINAL CURSOR 🌟
        # Bright neon blue feel
        can.setFillColor(colors.Color(0.1, 0.5, 1.0, alpha=0.9))
        can.drawString(current_x, y_pos, "_")
            
        can.restoreState()
        can.save()
        packet.seek(0)
        return packet

    def process_pdf(self, input_path: str, output_path: str, progress_callback=None) -> Tuple[bool, str]:
        try:
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            if total_pages == 0: return False, "PDF has no pages"
            
            writer = PdfWriter()
            
            # 🌟 SMART ORIENTATION CACHE 🌟
            dimension_cache: Dict[str, PdfReader] = {}
            
            for index, page in enumerate(reader.pages):
                if progress_callback and index % 10 == 0:
                    try: progress_callback(index + 1, total_pages)
                    except: pass
                
                try:
                    w = float(page.mediabox.width)
                    h = float(page.mediabox.height)
                except:
                    w, h = 612.0, 792.0
                
                dim_key = f"{w:.1f}x{h:.1f}"
                
                if dim_key not in dimension_cache:
                    watermark_packet = self.create_footer_layer(w, h)
                    watermark_pdf = PdfReader(watermark_packet)
                    dimension_cache[dim_key] = watermark_pdf.pages[0]
                
                page.merge_page(dimension_cache[dim_key])
                writer.add_page(page)
            
            # 🌟 MAXIMUM COMPRESSION (FIXED) 🌟
            try:
                writer.compress_identical_objects = True
            except:
                pass
                
            for page in writer.pages:
                try: page.compress_content_streams()
                except: pass
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            dimension_cache.clear()
            gc.collect()
            
            return True, f"Processed {total_pages} pages"
            
        except Exception as e:
            return False, f"Error: {str(e)}"

# ============================================
# HELPER FUNCTIONS REQUIRED BY MAIN.PY
# ============================================
def get_pdf_page_count(input_path: str) -> int:
    try:
        reader = PdfReader(input_path)
        return len(reader.pages)
    except:
        return 0

def clear_cache():
    gc.collect()
    logger.info("🗑️ Memory cache cleared")