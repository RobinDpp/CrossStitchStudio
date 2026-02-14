import streamlit as st
from app_auth import check_password
from utils import generate_pattern_image_func # Import de ta fonction

if not check_password():
    st.stop()

st.title("🎨 AI Image Generator")

subject = st.text_input("Sujet de l'image :", placeholder="Ex: A majestic wolf...")

if st.button("Générer l'image", type="primary"):
    if not subject:
        st.warning("Veuillez saisir un sujet.")
    else:
        with st.spinner("L'IA génère votre design..."):
            try:
                # Utilisation de ton code déplacé
                image_result = generate_pattern_image_func(subject)

                if image_result:
                    st.session_state['generated_img_pil'] = image_result
                    st.success("Image générée !")
                else:
                    st.error("L'IA n'a pas renvoyé d'image.")

            except Exception as e:
                st.error(f"Erreur : {e}")

if 'generated_img_pil' in st.session_state:
    st.image(st.session_state['generated_img_pil'], use_container_width=True)
    
    if st.button("🧵 Envoyer au Pattern Studio"):
        st.switch_page("pages/2_🧵_Pattern_Studio.py")