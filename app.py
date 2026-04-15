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
#  THE "NUCLEAR" CSS OVERRIDE
# ============================================================

st.markdown("""
    <style>
    /* 1. Kill Top Bar and Decoration */
    header[data-testid="stHeader"], [data-testid="stDecoration"] {
        background: rgba(0,0,0,0) !important;
        background-color: transparent !important;
    }

    /* 2. Global Dark Theme */
    .stApp {
        background-color: #2b2b2b !important;
        color: #ffffff !important;
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* 3. The Sidebar & Sidebar Text White-out */
    [data-testid="stSidebar"] {
        background-color: #404040 !important;
    }
    
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }

    /* 4. EXPANDER FIXED: Never turns white */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: 1px solid #696969 !important;
    }
    div[data-testid="stExpander"] details {
        background-color: transparent !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: transparent !important;
        color: #ffffff !important;
    }
    div[data-testid="stExpander"] [data-testid="stVerticalBlock"] {
        background-color: transparent !important;
    }

    /* 5. Buttons */
    button[kind="secondary"], button[kind="primary"] {
        background-color: #696969 !important;
        border: 2px solid #ffffff !important;
        border-radius: 0px !important;
    }

    button[kind="secondary"] p, 
    button[kind="primary"] p,
    button div[data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    button[kind="secondary"]:hover, button[kind="primary"]:hover {
        background-color: #ffffff !important;
        border: 2px solid #000000 !important;
    }
    
    /* 6. File Uploader Box */
    .stFileUploader section {
        background-color: #d3d3d3 !important;
    }
    
    code {
        color: #8B0000 !important;
        background-color: #eeeeee !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
#  ASSET GENERATORS
# ============================================================

def get_gothic_asset(text, color_rgb, font_size=80):
    try:
        font = ImageFont.truetype("Friedolin.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    left, top, right, bottom = font.getbbox(text)
    # Transparent background for PNGs
    img = Image.new('RGBA', (right-left + 60, bottom-top + 40), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((30, 10), text, font=font, fill=color_rgb)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ============================================================
#  WORD ENGINE (FLOATING LOGIC)
# ============================================================

def add_floating_element(doc, img_buf, width_cm, x_cm, y_cm):
    run = doc.add_paragraph().add_run()
    shape = run.add_picture(img_buf, width=Cm(width_cm))
    inline = shape._inline
    anchor = OxmlElement('wp:anchor')
    anchor.set('distT', '0'); anchor.set('distB', '0'); anchor.set('distL', '0'); anchor.set('distR', '0')
    anchor.set('simplePos', '0'); anchor.set('relativeHeight', '251658240')
    anchor.set('behindDoc', '0'); anchor.set('locked', '0')
    anchor.set('layoutInCell', '1'); anchor.set('allowOverlap', '1')
    
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
#  MAIN APP
# ============================================================

def main():
    try:
        title_png = get_gothic_asset("Gothic Book Generator", (255, 255, 255), 100)
        st.image(title_png)
    except:
        st.title("Gothic Book Generator")

    if 'img_lib' not in st.session_state: 
        st.session_state.img_lib = {}

    with st.sidebar:
        st.markdown("### 🎨 Colors")
        st.write("Title Color")
        t_color = st.color_picker("T", "#8B0000", key="t_c", label_visibility="collapsed")
        st.write("Subtitle Color")
        s_color = st.color_picker("S", "#FFFFFF", key="s_c", label_visibility="collapsed")
        
        rgb_title = tuple(int(t_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb_sub = tuple(int(s_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

        st.divider()
        st.markdown("### 🖋️ Note Typography")
        note_size = st.slider("Letter Size", 8, 36, 12)
        note_font = st.selectbox("Letter Type", ["Courier New", "Georgia", "Times New Roman", "Arial"])

        st.divider()
        st.markdown
