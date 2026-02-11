import streamlit as st
import mimetypes
import os
import base64
import io
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from app_auth import check_password

if not check_password():
    st.stop()

# --- CONFIGURATION VIA SECRETS ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Clé API manquante ! Ajoutez 'GEMINI_API_KEY' dans vos secrets Streamlit.")
    st.stop()

MODEL_ID = "gemini-2.5-flash-image"

st.set_page_config(page_title="Etsy Shop Studio Pro", layout="wide")

# CSS pour la netteté pixelisée
st.markdown("<style>img {image-rendering: pixelated;}</style>", unsafe_allow_html=True)

# --- FONCTION BADGE AMÉLIORÉE (CLEAN & CENTERED) ---
def add_pro_badge(target_image):
    img = target_image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    w, h = img.size
    # Badge légèrement plus grand pour le confort visuel
    badge_radius = int(w * 0.11) 
    margin = int(w * 0.04)
    
    # Centre du badge
    center_x = w - badge_radius - margin
    center_y = badge_radius + margin
    
    # Coordonnées du cercle
    bbox = [center_x - badge_radius, center_y - badge_radius, 
            center_x + badge_radius, center_y + badge_radius]
    
    # Dessin du badge (Style Etsy : Fond crème, bordure anthracite)
    draw.ellipse(bbox, fill=(255, 255, 255, 240)) # Fond
    draw.ellipse(bbox, outline=(40, 40, 40, 255), width=4) # Bordure principale
    
    # Texte optimisé
    try:
        # Tentative de chargement d'une police système propre
        font_size = int(badge_radius * 0.4)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # On dessine "PDF" en gros et "PATTERN" en petit dessous
    draw.text((center_x, center_y - int(badge_radius*0.15)), "PDF", 
              fill=(0, 0, 0, 255), font=font, anchor="mm")
    
    try:
        font_small = ImageFont.truetype("arial.ttf", int(font_size * 0.6))
    except:
        font_small = ImageFont.load_default()
        
    draw.text((center_x, center_y + int(badge_radius*0.35)), "PATTERN", 
              fill=(80, 80, 80, 255), font=font_small, anchor="mm")
    
    return Image.alpha_composite(img, overlay).convert("RGB")

def generate_mockup(processed_image):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Préparation 1024px NEAREST
    temp_img = processed_image.convert("RGB")
    sharp_image = temp_img.resize((1024, 1024), resample=Image.NEAREST)

    buffered = io.BytesIO()
    sharp_image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(mime_type="image/png", data=base64.b64decode(img_base64)),
                types.Part.from_text(text="Voici un design au point de croix, mets le dans un cadre de point circulaire de croix sans tissu en dépassant et un décors approprié pour en faire la présentation"),
            ],
        ),
    ]

    image_result = None
    for chunk in client.models.generate_content_stream(
        model=MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    ):
        if chunk.parts and chunk.parts[0].inline_data:
            image_data = chunk.parts[0].inline_data.data
            image_result = Image.open(io.BytesIO(image_data))
            
    return image_result

# --- INTERFACE ---
st.title("📸 Etsy Listing Generator")

design_img = st.session_state.get('processed_img_pil')

if design_img:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Source")
        st.image(design_img, use_container_width=True)
        btn = st.button("🚀 Générer l'image Etsy", type="primary")

    with col2:
        if btn:
            with st.spinner("Génération et Branding..."):
                try:
                    raw_mockup = generate_mockup(design_img)
                    if raw_mockup:
                        # Application du badge corrigé
                        final_shop_image = add_pro_badge(raw_mockup)
                        st.session_state['last_gen'] = final_shop_image
                        st.image(final_shop_image, use_container_width=True)
                        
                        buf = io.BytesIO()
                        final_shop_image.save(buf, format="PNG")
                        st.download_button("💾 Télécharger pour Etsy", buf.getvalue(), "etsy_pattern.png", "image/png")
                except Exception as e:
                    st.error(f"Erreur : {e}")
else:
    st.info("Aucun pattern trouvé. Retournez à l'étape précédente.")