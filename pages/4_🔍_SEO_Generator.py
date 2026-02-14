import streamlit as st
from app_auth import check_password
from utils import generate_seo_package, get_used_colors_data

if not check_password():
    st.stop()

st.set_page_config(page_title="Etsy SEO Expert", page_icon="🔍", layout="wide")

st.title("🔍 Etsy SEO Expert")
st.markdown("---")

# --- RÉCUPÉRATION DES DONNÉES DE SESSION (Optionnel) ---
default_subject = st.session_state.get('last_subject_from_generator', "")
processed_img = st.session_state.get('processed_img_pil')

# On tente de récupérer les specs réelles si elles existent
if processed_img:
    auto_colors = len(get_used_colors_data(processed_img))
    auto_grid = processed_img.size[0]
else:
    auto_colors = 15
    auto_grid = 100

st.subheader("1. Spécifications du produit")
col_sub, col_grid, col_col = st.columns([2, 1, 1])

with col_sub:
    visual_concept = st.text_input("Sujet du design", value=default_subject)
with col_grid:
    # Nouveau slider pour la taille de grille
    grid_val = st.number_input("Taille (points)", value=auto_grid, min_value=20, max_value=200)
with col_col:
    color_val = st.number_input("Nombre de couleurs", value=auto_colors)

if st.button("Générer le pack SEO ✨", type="primary", use_container_width=True):
    if not visual_concept:
        st.warning("Veuillez entrer un sujet.")
    else:
        with st.spinner(f"Rédaction pour un motif de {grid_val}x{grid_val} pts..."):
            try:
                # Appel avec les 3 arguments
                data = generate_seo_package(visual_concept, color_val, grid_val)
                st.session_state['last_seo_data'] = data
                st.success("SEO mis à jour avec les dimensions exactes !")
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- AFFICHAGE DES RÉSULTATS ---
if 'last_seo_data' in st.session_state:
    data = st.session_state['last_seo_data']
    st.divider()
    
    st.info("**📌 Titre optimisé**")
    st.code(data.get("title", ""))
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.info("**📝 Description (incluant taille & couleurs)**")
        st.text_area("Description", value=data.get("description", ""), height=350, label_visibility="collapsed")
    with c2:
        st.info("**🏷️ Tags Etsy (13)**")
        st.text_area("Tags", value=data.get("tags", ""), height=150, label_visibility="collapsed")