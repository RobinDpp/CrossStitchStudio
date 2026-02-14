import streamlit as st
import io
from app_auth import check_password
from utils import generate_mockup_func, add_pro_badge

if not check_password():
    st.stop()

st.set_page_config(page_title="Etsy Shop Studio Pro", layout="wide")
st.markdown("<style>img {image-rendering: pixelated;}</style>", unsafe_allow_html=True)

st.title("📸 Etsy Listing Generator")

design_img = st.session_state.get('processed_img_pil')

if design_img:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Source (Pixelated Pattern)")
        st.image(design_img, use_container_width=True)
        btn = st.button("🚀 Générer l'image Etsy", type="primary", use_container_width=True)

    with col2:
        if btn:
            with st.spinner("L'IA crée la mise en scène et applique le branding..."):
                try:
                    # Utilisation des fonctions centralisées
                    raw_mockup = generate_mockup_func(design_img)
                    if raw_mockup:
                        final_shop_image = add_pro_badge(raw_mockup)
                        st.session_state['last_gen'] = final_shop_image
                        
                        st.image(final_shop_image, use_container_width=True)
                        
                        buf = io.BytesIO()
                        final_shop_image.save(buf, format="PNG")
                        st.download_button(
                            label="💾 Télécharger pour Etsy", 
                            data=buf.getvalue(), 
                            file_name="etsy_listing_pro.png", 
                            mime="image/png",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Erreur de génération : {e}")
else:
    st.info("Aucun pattern trouvé. Générez d'abord un patron dans 'Pattern Studio'.")