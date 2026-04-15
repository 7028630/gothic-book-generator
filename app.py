import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import re
from PIL import Image

# ... (Keep previous image processing functions: process_no_bg, create_gothic_png, add_floating_img)

def main():
    st.set_page_config(page_title="Gothic Booklet Architect", layout="wide")
    
    # Initialize Image Library in Session State
    if 'img_library' not in st.session_state:
        st.session_state.img_library = {}

    with st.sidebar:
        st.header("🎨 Aesthetic Controls")
        t_color = st.color_picker("Gothic Letter Color", "#8B0000")
        m_size = st.slider("Main Text Size", 8, 12, 10)
        
        st.divider()
        st.header("🖼️ Image Receptor")
        uploaded_imgs = st.file_uploader("Upload Illustrations", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        
        if uploaded_imgs:
            for img in uploaded_imgs:
                # Store image and show copy-paste code
                st.session_state.img_library[img.name] = img
                st.image(img, width=100)
                st.code(f"[IMG: {img.name}]", language="text")
                if st.button(f"Rename {img.name}", key=f"ren_{img.name}"):
                    new_name = st.text_input("New Name", value=img.name)
                    # Logic to update key in dictionary...

    st.title("🏛️ Gothic Horizontal Compiler")
    st.info("Upload your .txt chapters. The app will generate a horizontal A4 booklet with page numbers.")

    files = st.file_uploader("Drop Chapter Notepads (.txt)", accept_multiple_files=True)

    if files:
        if st.button("🚀 Build Horizontal Manuscript", type="primary"):
            doc = Document()
            
            # --- SET HORIZONTAL A4 ---
            section = doc.sections[0]
            section.orientation = WD_ORIENT.LANDSCAPE
            section.page_width, section.page_height = Cm(29.7), Cm(21.0)
            # Narrow margins for booklet style
            section.top_margin = section.bottom_margin = Cm(1.5)
            section.left_margin = section.right_margin = Cm(1.5)

            rgb = tuple(int(t_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            
            total_virtual_pages = 1

            for f in files:
                raw_content = f.read().decode("utf-8")
                # Logic to split content into two halves if it's long, 
                # or treat each file as a new "Spread"
                
                table = doc.add_table(rows=2, cols=2) # Row 1: Content, Row 2: Page Numbers
                table.autofit = False
                
                # Format Columns
                for row in table.rows:
                    for cell in row.cells:
                        tc = cell._tc.get_or_add_tcPr()
                        tcW = OxmlElement('w:tcW')
                        tcW.set(qn('w:w'), str(int(13.3 * 567))) # ~13.3cm per col
                        tcW.set(qn('w:type'), 'dxa')
                        tcPr.append(tcW)

                # --- CONTENT PROCESSING (Simplified for demonstration) ---
                # This scans for your [IMG:], [SEP], and [TITLE:] tags
                # ... (Insert Regex loop from previous response) ...

                # --- PAGE NUMBERING ---
                # Left Page Number
                p_left = table.rows[1].cells[0].add_paragraph(str(total_virtual_pages))
                p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
                # Right Page Number
                p_right = table.rows[1].cells[1].add_paragraph(str(total_virtual_pages + 1))
                p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                total_virtual_pages += 2
                doc.add_page_break()

            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📥 Download Booklet", buf.getvalue(), "gothic_landscape.docx")

if __name__ == "__main__":
    main()
