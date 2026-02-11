import streamlit as st
import io
from google import genai
from google.genai import types
from PIL import Image
from app_auth import check_password

if not check_password():
    st.stop()

# --- CONFIGURATION VIA SECRETS ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Clé API manquante ! Ajoutez 'GEMINI_API_KEY' dans vos secrets.")
    st.stop()

# On utilise le même modèle que ta Page 3
MODEL_ID = "gemini-2.5-flash-image"

st.title("🎨 AI Image Generator")

subject = st.text_input("Sujet de l'image :", placeholder="Ex: A majestic wolf...")

# Ton prompt stratégique
BASE_PROMPT = ", ultra detailed, high contrast, bold black outlines, clean design, pure white background, vector style, no text"

if st.button("Générer l'image", type="primary"):
    if not subject:
        st.warning("Veuillez saisir un sujet.")
    else:
        with st.spinner("L'IA génère votre design..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # On utilise la même structure que ta fonction generate_mockup
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=f"Génère une image de : {subject}{BASE_PROMPT}"),
                        ],
                    ),
                ]

                image_result = None
                # On utilise le stream comme dans ta page 3
                for chunk in client.models.generate_content_stream(
                    model=MODEL_ID,
                    contents=contents,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                ):
                    if chunk.parts and chunk.parts[0].inline_data:
                        image_data = chunk.parts[0].inline_data.data
                        image_result = Image.open(io.BytesIO(image_data))

                if image_result:
                    st.session_state['generated_img_pil'] = image_result
                    st.success("Image générée !")
                else:
                    st.error("L'IA n'a pas renvoyé d'image.")

            except Exception as e:
                st.error(f"Erreur : {e}")

# Affichage et Navigation
if 'generated_img_pil' in st.session_state:
    st.image(st.session_state['generated_img_pil'], use_container_width=True)
    
    if st.button("🧵 Envoyer au Pattern Studio"):
        # Vérifie bien que le nom du fichier est exactement celui-là dans ton dossier pages/
        st.switch_page("pages/2_🧵_Pattern_Studio.py")