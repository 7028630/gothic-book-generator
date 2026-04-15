import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import io
import re
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# UI STYLING
# ============================================================
st.markdown("""
    <style>
    header[data-testid="stHeader"], [data-testid="stDecoration"] { background: rgba(0,0,0,0) !important; }
    .stApp { background-color: #2b2b2b !important; color: #ffffff !important; font-family: 'Courier New', Courier, monospace !important; }
    [data-testid="stSidebar"] { background-color: #404040 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    div[data-testid="stExpander"] { background-color: transparent !important; border: 1px solid #696969 !important; }
    code { color: #ffffff !important; background-color: #404040 !important; }
    button[kind="primary"] { background-color: #696969 !important; border: 2px solid #ffffff !important; border-radius: 0px !important; }
    button p { color: #000000 !important; font-weight: 900 !important; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# CORE FUNCTIONS
# ============================================================

def get_gothic_asset(text, color_rgb, font_size=80):
    try:
        font = ImageFont.truetype("Friedolin.ttf", font_size)
    except:
        font = ImageFont.load_default()
    left, top, right, bottom = font.getbbox(text)
    img = Image.new('RGBA', (right-left + 60, bottom-top + 40), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((30, 10), text, font=font, fill=color_rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def add_floating_element(doc, img_buf, width_cm, x_cm, y_cm):
    run = doc.add_paragraph().add_run()
    shape = run.add_picture(img_buf, width=Cm(width_cm))
    inline = shape._inline
    extent = inline.extent
    docPr = inline.docPr
    graphic = inline.graphic
    
    anchor = OxmlElement('wp:anchor')
    anchor.set('distT', '0'); anchor.set('distB', '0'); anchor.set('distL', '0'); anchor.set('distR', '0')
    anchor.set('simplePos', '0'); anchor.set('relativeHeight', '251658240')
    anchor.set('behindDoc', '0'); anchor.set('locked', '0')
    anchor.set('layoutInCell', '1'); anchor.set('allowOverlap', '1')

    posH = OxmlElement('wp:positionH'); posH.set('relativeFrom', 'page')
    posOffsetH = OxmlElement('wp:posOffset'); posOffsetH.text = str(int(x_cm * 360000))
    posH.append(posOffsetH)
    
    posV = OxmlElement('wp:positionV'); posV.set('relativeFrom', 'page')
    posOffsetV = OxmlElement('wp:posOffset'); posOffsetV.text = str(int(y_cm * 360000))
    posV.append(posOffsetV)
    
    anchor.append(OxmlElement('wp:simplePos'))
    anchor.append(posH)
    anchor.append(posV)
    anchor.append(extent)
    anchor.append(OxmlElement('wp:effectExtent'))
    anchor.append(docPr)
    anchor.append(graphic)
    inline.getparent().replace(inline, anchor)

# ============================================================
# MAIN APP LOGIC
# ============================================================

def main():
    st.title("Gothic Book Generator")

    if 'img_lib' not in st.session_state: st.session_state.img_lib = {}

    with st.sidebar:
        t_color = st.color_picker("Title Color", "#8B0000")
        s_color = st.color_picker("Subtitle Color", "#FFFFFF")
        rgb_title = tuple(int(t_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb_sub = tuple(int(s_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        main_size = st.slider("Text Size", 8, 30, 12)
        uploads = st.file_uploader("Upload Images", accept_multiple_files=True)
        if uploads:
            for up in uploads: st.session_state.img_lib[up.name] = up

    notepads = st.file_uploader("Upload TXT File", accept_multiple_files=True)

    if notepads and st.button("🚀 Build Book"):
        doc = Document()
        section = doc.sections[0]
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = Cm(29.7), Cm(21.0)
        
        pg_num = 1
        for note in notepads:
            lines = note.read().decode("utf-8").split('\n')
            
            # Start first page table
            table = doc.add_table(rows=2, cols=2)
            table.autofit = False
            cell_l = table.rows[0].cells[0]
            current_y = 1.5 # Start y position
            in_commentary = False
            
            for line in lines:
                line = line.strip()
                if not line: continue

                # SAFETY: If we are near the bottom of the page (18cm), jump to a new page
                if current_y > 18.0:
                    doc.add_page_break()
                    table = doc.add_table(rows=2, cols=2)
                    cell_l = table.rows[0].cells[0]
                    current_y = 1.5

                if line == "[NOTE_START]":
                    in_commentary = True
                    current_y += 0.5
                    continue
                
                if line == "[NOTE_END]":
                    in_commentary = False
                    current_y += 0.5
                    continue

                if line.startswith("[TITLE:"):
                    txt = re.search(r"\[TITLE: (.*?)\]", line).group(1)
                    add_floating_element(doc, get_gothic_asset(txt, rgb_title, 80), 12, 2, current_y)
                    current_y += 3.5
                    for _ in range(4): cell_l.add_paragraph()

                elif line.startswith("[SUB:"):
                    txt = re.search(r"\[SUB: (.*?)\]", line).group(1)
                    add_floating_element(doc, get_gothic_asset(txt, rgb_sub, 45), 9, 2, current_y)
                    current_y += 2.0
                    for _ in range(2): cell_l.add_paragraph()
                
                elif line.startswith("[IMG:"):
                    name = re.search(r"\[IMG: (.*?)\]", line).group(1)
                    if name in st.session_state.img_lib:
                        add_floating_element(doc, st.session_state.img_lib[name], 8, 3, current_y)
                        current_y += 7.0
                else:
                    p = cell_l.add_paragraph(line)
                    run = p.runs[0] if p.runs else p.add_run(line)
                    run.font.name = "Courier New"
                    run.font.size = Pt(main_size - 2) if in_commentary else Pt(main_size)
                    current_y += 0.8 # Increment Y for standard text lines

            # Add page numbers to footer row
            table.rows[1].cells[0].add_paragraph(str(pg_num)).alignment = WD_ALIGN_PARAGRAPH.CENTER
            table.rows[1].cells[1].add_paragraph(str(pg_num + 1)).alignment = WD_ALIGN_PARAGRAPH.CENTER
            pg_num += 2
            doc.add_page_break()

        out = io.BytesIO()
        doc.save(out)
        st.download_button("📥 Download Fixed Word Doc", out.getvalue(), "gothic_book.docx")

if __name__ == "__main__":
    main()
