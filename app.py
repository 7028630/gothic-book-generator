import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import io
import os
from PIL import Image, ImageDraw, ImageFont

# ============================================================
#  IMAGE PROCESSING (NO BG & GOTHIC ASSETS)
# ============================================================

def process_no_bg(image_input, target_color=None):
    """Removes white background and optionally tints the image."""
    img = Image.open(image_input).convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        # If pixel is bright (white-ish), make it transparent
        if item[0] > 225 and item[1] > 225 and item[2] > 225:
            newData.append((255, 255, 255, 0))
        else:
            if target_color:
                newData.append((*target_color, item[3]))
            else:
                newData.append(item)
    img.putdata(newData)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def create_gothic_png(text, font_path, size_pt, color_rgb):
    """Turns the Gothic font into a transparent PNG to avoid Word issues."""
    try:
        font = ImageFont.truetype(font_path, int(size_pt * 2))
    except:
        font = ImageFont.load_default()
    
    # Get text box dimensions
    left, top, right, bottom = font.getbbox(text)
    w, h = right - left, bottom - top
    
    img = Image.new('RGBA', (w + 20, h + 20), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10, 5), text, font=font, fill=color_rgb)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def create_subtle_separator(img_path):
    """Tints the separator gray and adds thin horizontal lines."""
    main_graphic = Image.open(process_no_bg(img_path, target_color=(120, 120, 120)))
    
    # Canvas for the full width separator
    canvas_w = 1200
    canvas_h = main_graphic.size[1]
    canvas = Image.new('RGBA', (canvas_w, canvas_h), (255, 255, 255, 0))
    
    draw = ImageDraw.Draw(canvas)
    # Subtle light gray line
    draw.line((0, canvas_h//2, canvas_w, canvas_h//2), fill=(200, 200, 200, 100), width=1)
    
    # Paste the gothic graphic in the center
    offset = (canvas_w//2 - main_graphic.size[0]//2, 0)
    canvas.paste(main_graphic, offset, main_graphic)
    
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ============================================================
#  WORD DOCUMENT INJECTION
# ============================================================

def add_floating_img(doc, img_buf, width_cm, x_cm, y_cm):
    """Places image 'In Front of Text' at specific coordinates."""
    p = doc.add_paragraph()
    run = p.add_run()
    shape = run.add_picture(img_buf, width=Cm(width_cm))
    
    inline = shape._inline
    anchor = OxmlElement('wp:anchor')
    anchor.set('distT', '0'); anchor.set('distB', '0'); anchor.set('distL', '0'); anchor.set('distR', '0')
    anchor.set('simplePos', '0'); anchor.set('relativeHeight', '251658240')
    anchor.set('behindDoc', '0'); anchor.set('locked', '0'); anchor.set('layoutInCell', '1'); anchor.set('allowOverlap', '1')
    
    posH = OxmlElement('wp:positionH'); posH.set('relativeFrom', 'page')
    posH.append(OxmlElement('wp:posOffset'))
    posH.find(qn('wp:posOffset')).text = str(int(x_cm * 360000))
    
    posV = OxmlElement('wp:positionV'); posV.set('relativeFrom', 'page')
    posV.append(OxmlElement('wp:posOffset'))
    posV.find(qn('wp:posOffset')).text = str(int(y_cm * 360000))
    
    anchor.append(posH); anchor.append(posV)
    for child in inline:
        if child.tag != qn('wp:docPr') and child.tag != qn('wp:cNvGraphicFramePr'):
            anchor.append(child)
    inline.getparent().replace(inline, anchor)

# ============================================================
#  STREAMLIT INTERFACE
# ============================================================

def main():
    st.set_page_config(page_title="Gothic Book Compiler", layout="wide")
    st.title("📖 Gothic Book Architect")
    st.caption("Works on any browser. Connect to GitHub for persistent storage.")

    with st.sidebar:
        st.header("Global Style")
        accent_color = st.color_picker("Gothic Letter Color", "#8B0000")
        m_size = st.slider("Body Font Size", 8, 14, 11)
        page_format = st.selectbox("Page Size", ["A4", "Letter"])

    # Convert HEX to RGB
    rgb = tuple(int(accent_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

    # BULK UPLOAD MODE
    st.subheader("1. Upload Chapters")
    files = st.file_uploader("Upload .txt files (Naming: 'Chapter 1.txt')", accept_multiple_files=True)

    if files:
        st.success(f"{len(files)} files ready.")
        if st.button("🏗️ Build Full Book (150+ Pages)", type="primary"):
            doc = Document()
            section = doc.sections[0]
            w_cm, h_cm = (21.0, 29.7) if page_format == "A4" else (21.59, 27.94)
            section.page_width, section.page_height = Cm(w_cm), Cm(h_cm)
            section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Cm(1.5)

            # Sort files by name to maintain order
            files.sort(key=lambda x: x.name)

            for f in files:
                # Add Page Content
                text = f.read().decode("utf-8")
                
                # Create Table for 2-column Layout
                table = doc.add_table(rows=1, cols=2)
                table.autofit = False
                
                # Add Title as Floating PNG
                title_name = f.name.replace(".txt", "")
                title_png = create_gothic_png(title_name, "Friedolin.ttf", 40, rgb)
                add_floating_img(doc, title_png, width_cm=8, x_cm=2, y_cm=2)
                
                # Add Body Text to Column 1
                cell = table.rows[0].cells[0]
                # Add padding for title
                for _ in range(5): cell.add_paragraph()
                p = cell.add_paragraph(text)
                p.paragraph_format.first_line_indent = 0
                
                # Add Separator
                sep_png = create_subtle_separator("Separator.png")
                add_floating_img(doc, sep_png, width_cm=18, x_cm=1.5, y_cm=25)

                doc.add_page_break()

            # Final Download
            out = io.BytesIO()
            doc.save(out)
            st.download_button("📥 Download Manuscript", out.getvalue(), "my_gothic_book.docx", use_container_width=True)

if __name__ == "__main__":
    main()
