import streamlit as st
from PIL import Image, ImageOps
import io
import json
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app_auth import check_password

if not check_password():
    st.stop()

# --- 1. CHARGEMENT DATA (Ne change pas) ---
try:
    with open('rgb-dmc.json', 'r', encoding='utf-8') as f:
        DMC_DB = json.load(f)
except FileNotFoundError:
    st.error("Fichier dmc.json non trouvé !")
    DMC_DB = []

# --- 2. FONCTIONS TECHNIQUES (Ne changent pas) ---
def get_closest_dmc(rgb):
    r, g, b = rgb
    best_match = DMC_DB[0]
    min_dist = float('inf')
    for color in DMC_DB:
        dist = ((color["r"]-r)**2 + (color["g"]-g)**2 + (color["b"]-b)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            best_match = color
    return best_match

def process_image(image, size, num_colors):
    img = ImageOps.contain(image, (size, size))
    img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=num_colors).convert("RGB")
    return img

def get_used_colors_data(processed_img):
    used_colors = {}
    symbols = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#@$§&?%WX+"
    sym_idx = 0
    cols, rows = processed_img.size
    
    for y in range(rows):
        for x in range(cols):
            pixel = processed_img.getpixel((x, y))
            dmc = get_closest_dmc(pixel)
            if dmc["floss"] not in used_colors:
                used_colors[dmc["floss"]] = {
                    "info": dmc, 
                    "count": 0, 
                    "sym": symbols[sym_idx % len(symbols)]
                }
                sym_idx += 1
            used_colors[dmc["floss"]]["count"] += 1
    return used_colors

def display_pdf(bytes_data):
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- 3. GENERATEURS PDF (Inchangés mais nécessaires) ---
# --- 3. GENERATEUR PDF STYLE "FLOSSCROSS" ---
def generate_flosscross_pdf(processed_img, user_texts, bw_mode, used_colors):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 50
    
    rows, cols = processed_img.size
    

    # --- 2. PAGE 1 : COUVERTURE ---
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height - 50, user_texts['main_title'])
    c.setLineWidth(0.5)
    c.line(margin, height - 70, width - margin, height - 70)
    
    img_display_w = 350
    img_display_h = (rows/cols) * img_display_w
    c.drawInlineImage(processed_img, (width-img_display_w)/2, height-450, width=img_display_w, height=img_display_h)
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height-500, f"Design size: {cols} x {rows} stitches")
    c.drawString(margin, 100, user_texts['import_note'])
    c.drawString(margin, 60, user_texts['copyright'])
    c.drawRightString(width - margin, 60, "Page 1")

    # --- 3. CONFIGURATION DU DÉCOUPAGE ---
    MAX_POINTS_PER_PAGE = 50
    num_pages_x = (cols + MAX_POINTS_PER_PAGE - 1) // MAX_POINTS_PER_PAGE
    num_pages_y = (rows + MAX_POINTS_PER_PAGE - 1) // MAX_POINTS_PER_PAGE
    current_page_num = 2 

    # --- 4. GÉNÉRATION DES PAGES DE GRILLE ---
    for py in range(num_pages_y):
        for px in range(num_pages_x):
            c.showPage()
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(width/2, height - 25, f"{user_texts['main_title']} - Part {px+1},{py+1}")
            
            x_start = px * MAX_POINTS_PER_PAGE
            x_end = min(x_start + MAX_POINTS_PER_PAGE, cols)
            y_start = py * MAX_POINTS_PER_PAGE
            y_end = min(y_start + MAX_POINTS_PER_PAGE, rows)
            
            current_w = x_end - x_start
            current_h = y_end - y_start
            
            cell_size = min((width - 100) / current_w, (height - 120) / current_h)
            draw_x = (width - (current_w * cell_size)) / 2
            draw_y = (height - 60)
            
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    pixel = processed_img.getpixel((x, y))
                    dmc = get_closest_dmc(pixel)
                    data = used_colors[dmc["floss"]]
                    
                    local_x = draw_x + (x - x_start) * cell_size
                    local_y = draw_y - (y - y_start + 1) * cell_size
                    
                    # --- NOUVELLE LOGIQUE NOIR & BLANC AVEC FOND GRIS ---
                    if bw_mode:
                        # On calcule la luminosité (0.0 à 1.0)
                        # Formule standard de luminance : 0.299R + 0.587G + 0.114B
                        luma = (dmc["r"] * 0.299 + dmc["g"] * 0.587 + dmc["b"] * 0.114) / 255
                        
                        # Pour que ce soit "lisible", on éclaircit le gris (sinon c'est trop sombre)
                        # On compresse la plage de gris entre 0.6 (gris clair) et 1.0 (blanc)
                        adjusted_luma = 0.6 + (luma * 0.4) 
                        fill_color = (adjusted_luma, adjusted_luma, adjusted_luma)
                        
                        text_color = colors.black
                        line_color = colors.grey # Lignes de cases plus discrètes en NB
                    else:
                        # Mode couleur classique
                        fill_color = (dmc["r"]/255, dmc["g"]/255, dmc["b"]/255)
                        line_color = colors.lightgrey
                        brightness = (dmc["r"] * 299 + dmc["g"] * 587 + dmc["b"] * 114) / 1000
                        text_color = colors.white if brightness < 125 else colors.black

                    # --- DESSIN ---
                    c.setLineWidth(0.1)
                    c.setStrokeColor(line_color)
                    
                    # Lignes de structure 10x10 (toujours noires et bien visibles)
                    if x % 10 == 0 or y % 10 == 0:
                        c.setLineWidth(0.7)
                        c.setStrokeColor(colors.black)
                    
                    c.setFillColorRGB(*fill_color)
                    c.rect(local_x, local_y, cell_size, cell_size, fill=1, stroke=1)
                    
                    # Symbole
                    c.setFillColor(text_color)
                    font_size = cell_size * 0.7
                    c.setFont("Helvetica", font_size)
                    c.drawCentredString(local_x + cell_size/2, local_y + cell_size/4, data["sym"])
            
            c.setFont("Helvetica", 8)
            c.drawRightString(width - margin, 30, f"Page {current_page_num}")
            current_page_num += 1

    # --- 5. PAGE FINALE : LÉGENDE ---
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(margin, height - 50, "Thread Legend (DMC)")
    
    y_pos = height - 100
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y_pos, "Sym")
    c.drawString(margin + 40, y_pos, "Floss")
    c.drawString(margin + 100, y_pos, "Description")
    c.drawString(margin + 300, y_pos, "Stitches")
    c.line(margin, y_pos - 5, width-margin, y_pos - 5)
    
    y_pos -= 25
    c.setFont("Helvetica", 10)
    
    for floss_code, data in used_colors.items():
        if bw_mode:
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.black)
            c.rect(margin, y_pos - 2, 12, 12, fill=1, stroke=1)
            c.setFillColor(colors.black)
        else:
            c.setFillColorRGB(data["info"]["r"]/255, data["info"]["g"]/255, data["info"]["b"]/255)
            c.rect(margin, y_pos - 2, 12, 12, fill=1)
            brightness = (data["info"]["r"] * 299 + data["info"]["g"] * 587 + data["info"]["b"] * 114) / 1000
            c.setFillColor(colors.white if brightness < 125 else colors.black)
        
        c.drawCentredString(margin + 6, y_pos + 1, data["sym"])
        
        c.setFillColor(colors.black)
        c.drawString(margin + 40, y_pos, str(floss_code))
        c.drawString(margin + 100, y_pos, data["info"]["description"])
        c.drawString(margin + 300, y_pos, str(data["count"]))
        
        y_pos -= 20
        if y_pos < 50:
            c.showPage()
            y_pos = height - 50
            
    c.drawRightString(width - margin, 30, f"Page {current_page_num}")
    c.save()
    return buffer.getvalue()

def generate_pk_pdf(processed_img, used_colors):
    buffer = io.BytesIO()
    rows, cols = processed_img.size
    
    # Calcul d'une taille de page personnalisée pour que tout tienne sur UNE page
    # On garde une taille de cellule fixe (15 pts) pour la précision
    cell_size = 15
    page_width = (cols * cell_size) + 100
    page_height = (rows * cell_size) + 150
    
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # --- DESSIN DE LA GRILLE ---
    draw_x = 50
    draw_y = page_height - 50
    
    for y in range(rows):
        for x in range(cols):
            pixel = processed_img.getpixel((x, y))
            dmc = get_closest_dmc(pixel)
            data = used_colors[dmc["floss"]]
            
            rect_x = draw_x + (x * cell_size)
            rect_y = draw_y - ((y + 1) * cell_size)
            
            # Pour Pattern Keeper, on utilise des couleurs pleines
            c.setLineWidth(0.1)
            c.setStrokeColor(colors.lightgrey)
            c.setFillColorRGB(dmc["r"]/255, dmc["g"]/255, dmc["b"]/255)
            c.rect(rect_x, rect_y, cell_size, cell_size, fill=1)
            
            # Symbole noir ou blanc selon luminosité
            brightness = (dmc["r"] * 299 + dmc["g"] * 587 + dmc["b"] * 114) / 1000
            c.setFillColor(colors.white if brightness < 125 else colors.black)
            c.setFont("Helvetica", cell_size * 0.6)
            c.drawCentredString(rect_x + cell_size/2, rect_y + cell_size/4, data["sym"])

    # --- LÉGENDE (Sous la grille) ---
    # Très important : PK a besoin de lire "DMC" suivi du code
    y_leg = draw_y - (rows * cell_size) - 40
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(draw_x, y_leg, "Legend")
    y_leg -= 20
    
    c.setFont("Helvetica", 10)
    for code, data in used_colors.items():
        # PK détecte mieux si on écrit explicitement "DMC"
        text_line = f"Symbol {data['sym']} : DMC {code} - {data['info']['description']}"
        c.drawString(draw_x, y_leg, text_line)
        y_leg -= 15
        if y_leg < 20: break # Sécurité

    c.save()
    return buffer.getvalue()


# --- 4. INTERFACE STREAMLIT ---
st.set_page_config(page_title="CrossStitch Studio Pro", layout="wide")
st.sidebar.title("🎨 Editor & Settings")

# Customisation des textes
st.sidebar.subheader("PDF Text Customization")
custom_texts = {
    'main_title': st.sidebar.text_input("Pattern Title", "My Beautiful Flower"),
    'sub_title': st.sidebar.text_input("Sub-title", "Cross stitch chart"),
    'import_note': st.sidebar.text_input("Import Note", "Chart imported from image"),
    'copyright': st.sidebar.text_input("Copyright", "©2026 My Copyright"),
    'producer': st.sidebar.text_input("Footer Credit", "Produced using CrossStitch Studio")
}

grid_size = st.sidebar.slider("Grid Size (Stitches)", 20, 200, 100)
num_colors = st.sidebar.slider("Colors", 2, 40, 15)
bw_mode = st.sidebar.checkbox("Black & White Mode (High Contrast)")
pk_compatible = st.sidebar.toggle("Pattern Keeper Compatible")

# --- 5. LOGIQUE DE SÉLECTION DE L'IMAGE (CORRIGÉE) ---
ai_image = st.session_state.get('generated_img_pil', None)
img_to_process = None

# Option 1 : Image venant de l'IA
if ai_image:
    st.sidebar.success("✅ Image IA détectée")
    if st.sidebar.toggle("Utiliser l'image de l'IA", value=True):
        img_to_process = ai_image

# Option 2 : Upload manuel (si pas d'IA ou si l'utilisateur préfère)
uploaded_file = st.sidebar.file_uploader("Ou uploader une image manuellement", type=["jpg", "png", "jpeg"])
if uploaded_file:
    img_to_process = Image.open(uploaded_file)

# --- 6. TRAITEMENT ET AFFICHAGE ---
if img_to_process:
    # On traite l'image choisie (IA ou Upload)
    proc = process_image(img_to_process, grid_size, num_colors)
    st.session_state['processed_img_pil'] = proc
    st.session_state['last_subject_from_generator'] = custom_texts['main_title'] # Utile pour le prompt auto de la page 3
    current_used_colors = get_used_colors_data(proc)
    
    # Affichage de l'aperçu et du PDF
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Final Stitch Preview")
        # Aperçu pixelisé pour bien voir les points
        st.image(proc.resize((600, int(600*(proc.size[1]/proc.size[0]))), Image.NEAREST), use_container_width=True)
        
        st.sidebar.metric(label="DMC Threads used", value=len(current_used_colors))

    with col2:
        st.subheader("PDF Output")
        
        if pk_compatible:
            st.info("📱 Pattern Keeper Mode active.")
            pdf_bytes = generate_pk_pdf(proc, current_used_colors)
        else:
            pdf_bytes = generate_flosscross_pdf(proc, custom_texts, bw_mode, current_used_colors)
            display_pdf(pdf_bytes)
        
        st.download_button(
            label="💾 Download PDF",
            data=pdf_bytes,
            file_name="pattern_export.pdf",
            mime="application/pdf"
        )
else:
    st.title("🧵 Pattern Studio")
    st.info("Awaiting image... Générez une image avec l'IA ou uploadez un fichier dans la barre latérale.")