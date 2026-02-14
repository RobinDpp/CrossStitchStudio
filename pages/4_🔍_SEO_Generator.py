import streamlit as st
from app_auth import check_password
from utils import generate_seo_package

if not check_password():
    st.stop()

st.title("🔍 Etsy SEO Expert")

# --- RÉCUPÉRATION DES DONNÉES DE SESSION ---
default_subject = st.session_state.get('last_subject_from_generator', "")
# On regarde si on a déjà calculé des couleurs en Page 2
processed_img = st.session_state.get('processed_img_pil')
if processed_img:
    # On récupère le nombre de couleurs réelles calculées
    from utils import get_used_colors_data
    colors_data = get_used_colors_data(processed_img)
    auto_num_colors = len(colors_data)
else:
    auto_num_colors = 20 # Valeur par défaut si rien n'est trouvé

st.subheader("1. Details for SEO")
col_a, col_b = st.columns([3, 1])

with col_a:
    visual_concept = st.text_input("Subject", value=default_subject)
with col_b:
    nb_colors = st.number_input("Colors used", value=auto_num_colors)

if st.button("Generate SEO Package ✨", type="primary", use_container_width=True):
    if not visual_concept:
        st.warning("Please enter a concept.")
    else:
        with st.spinner(f"Crafting SEO for {nb_colors} colors..."):
            try:
                # On envoie le sujet ET le nombre de couleurs
                data = generate_seo_package(visual_concept, nb_colors)
                st.session_state['last_seo_data'] = data
                st.success("SEO Package Generated with real technical data!")
            except Exception as e:
                st.error(f"Error: {e}")

# Affichage des résultats si présents
if 'last_seo_data' in st.session_state:
    data = st.session_state['last_seo_data']
    
    st.info("**📌 Listing Title**")
    st.text_area("Title Area", value=data.get("title", ""), height=70, label_visibility="collapsed")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("**📝 Product Description**")
        st.text_area("Desc Area", value=data.get("description", ""), height=450, label_visibility="collapsed")
    
    with col2:
        st.info("**🏷️ 13 SEO Tags**")
        st.text_area("Tags Area", value=data.get("tags", ""), height=150, label_visibility="collapsed")

st.markdown("---")