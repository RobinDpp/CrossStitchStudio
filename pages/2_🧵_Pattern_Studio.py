import streamlit as st
from PIL import Image
import base64
from app_auth import check_password
# Import des fonctions depuis utils
from utils import (
    process_image, get_used_colors_data, 
    generate_flosscross_pdf, generate_pk_pdf
)

if not check_password():
    st.stop()

def display_pdf(bytes_data):
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

st.set_page_config(page_title="CrossStitch Studio Pro", layout="wide")
st.sidebar.title("🎨 Editor & Settings")

custom_texts = {
    'main_title': st.sidebar.text_input("Pattern Title", "My Beautiful Flower"),
    'sub_title': st.sidebar.text_input("Sub-title", "Cross stitch chart"),
    'import_note': st.sidebar.text_input("Import Note", "Chart imported from image"),
    'copyright': st.sidebar.text_input("Copyright", "©2026 My Copyright")
}

grid_size = st.sidebar.slider("Grid Size (Stitches)", 20, 200, 100)
num_colors = st.sidebar.slider("Colors", 2, 40, 15)
bw_mode = st.sidebar.checkbox("Black & White Mode")
pk_compatible = st.sidebar.toggle("Pattern Keeper Compatible")

ai_image = st.session_state.get('generated_img_pil', None)
img_to_process = None

if ai_image:
    if st.sidebar.toggle("Utiliser l'image de l'IA", value=True):
        img_to_process = ai_image

uploaded_file = st.sidebar.file_uploader("Ou uploader manuellement", type=["jpg", "png"])
if uploaded_file:
    img_to_process = Image.open(uploaded_file)

if img_to_process:
    proc = process_image(img_to_process, grid_size, num_colors)
    
    # --- LA LIGNE CORRECTRICE CI-DESSOUS ---
    st.session_state['processed_img_pil'] = proc 
    # ---------------------------------------
    
    used_colors = get_used_colors_data(proc)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Final Stitch Preview")
        st.image(proc.resize((600, int(600*(proc.size[1]/proc.size[0]))), Image.NEAREST), use_container_width=True)
        st.sidebar.metric(label="DMC Threads used", value=len(used_colors))

    with col2:
        st.subheader("PDF Output")
        if pk_compatible:
            pdf_bytes = generate_pk_pdf(proc, used_colors)
        else:
            pdf_bytes = generate_flosscross_pdf(proc, custom_texts, bw_mode, used_colors)
            display_pdf(pdf_bytes)
        
        st.download_button(label="💾 Download PDF", data=pdf_bytes, file_name="pattern_export.pdf", mime="application/pdf")
else:
    st.info("Awaiting image...")