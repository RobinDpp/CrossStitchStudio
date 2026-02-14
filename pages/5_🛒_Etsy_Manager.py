import streamlit as st
from google import genai
from PIL import Image
import io
import json
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from app_auth import check_password

# --- CONFIGURATION ET AUTH ---
if not check_password():
    st.stop()

st.set_page_config(page_title="Etsy Factory", layout="wide")
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- FONCTIONS UTILES (Rappel des étapes précédentes) ---

def generate_image(prompt):
    """Génère l'image de base du design"""
    response = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=prompt,
    )
    return response.generated_images[0].image

def generate_seo(concept):
    """Génère le pack SEO en JSON"""
    prompt = f"Etsy SEO for cross stitch: {concept}. Return JSON: title, description, tags. No markdown."
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={'response_mime_type': 'application/json'}
    )
    return json.loads(response.text)

def create_pdf(image, mode="color"):
    """Simule la création d'un PDF (Version simplifiée pour l'exemple)"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(100, 800, f"Cross Stitch Pattern - Mode: {mode}")
    # Ici, tu insérerais ton code de génération de grille reportlab
    c.save()
    return buffer.getvalue()

# --- INTERFACE UTILISATEUR ---

st.title("🏭 Etsy Factory - All-in-One")
st.markdown("Générez tout votre listing Etsy (Images, PDFs, SEO) en une seule fois.")

design_subject = st.text_input("Sujet du design (en anglais) :", placeholder="e.g. A vintage botanical illustration of a lavender flower...")

if st.button("🚀 Lancer la production complète", type="primary", use_container_width=True):
    if not design_subject:
        st.warning("Veuillez entrer un sujet.")
    else:
        with st.spinner("Étape 1/4 : Génération de l'image source..."):
            main_image_bytes = generate_image(f"A flat cross stitch pattern design of {design_subject}, pixel art style, isolated on white background")
            main_img = Image.open(io.BytesIO(main_image_bytes))
            st.session_state.final_img = main_img

        with st.spinner("Étape 2/4 : Création des 3 fichiers PDF..."):
            # On génère les 3 versions
            pdf_color = create_pdf(main_img, "Color Symbols")
            pdf_bw = create_pdf(main_img, "B&W Symbols")
            pdf_pk = create_pdf(main_img, "Pattern Keeper")

        with st.spinner("Étape 3/4 : Création du Mockup de présentation..."):
            # Ici on réutilise ton prompt de mockup
            mockup_prompt = f"A professional Etsy mockup of a wooden embroidery hoop on a linen fabric showing: {design_subject}"
            mockup_bytes = generate_image(mockup_prompt)
            mockup_img = Image.open(io.BytesIO(mockup_bytes))

        with st.spinner("Étape 4/4 : Rédaction du SEO..."):
            seo_data = generate_seo(design_subject)

        # --- AFFICHAGE DES RÉSULTATS ---
        st.success("✅ Production terminée !")
        st.divider()

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🖼️ Visuels")
            st.image(mockup_img, caption="Image de présentation (Mockup)")
            st.image(main_img, caption="Image source du patron")
            
            st.subheader("📥 Téléchargements PDF")
            st.download_button("📄 PDF Couleur", pdf_color, "pattern_color.pdf")
            st.download_button("📄 PDF Noir & Blanc", pdf_bw, "pattern_bw.pdf")
            st.download_button("📄 PDF Pattern Keeper", pdf_pk, "pattern_pk.pdf")

        with col_right:
            st.subheader("🔍 SEO & Listing")
            st.info("**Titre :**")
            st.code(seo_data.get("title"), language=None)
            
            st.info("**Description :**")
            st.text_area("Desc", value=seo_data.get("description"), height=300, label_visibility="collapsed")
            
            st.info("**Tags :**")
            st.code(seo_data.get("tags"), language=None)

st.sidebar.info("Cette page centralise tous vos outils pour une productivité maximale.")