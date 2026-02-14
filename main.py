import streamlit as st
from app_auth import check_password

if not check_password():
    st.stop()


# --- CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="StitchAI Suite - All-in-One Cross Stitch Business",
    page_icon="🧵",
    layout="wide"
)

# --- STYLE CSS (Optionnel pour rendre l'accueil joli) ---
st.markdown("""
    <style>
    .main-title {
        font-size: 3rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 10px;
    }
    .sub-title {
        font-size: 1.5rem;
        text-align: center;
        color: #555;
        margin-bottom: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONTENU DE L'ACCUEIL ---
st.markdown('<h1 class="main-title">🧵 StitchAI Suite</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">L\'écosystème complet pour votre business de broderie automatisé.</p>', unsafe_allow_html=True)

st.divider()

# --- PRÉSENTATION DES MODULES ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎨 IA Génératrice")
    st.write("Créez des visuels uniques optimisés pour la broderie.")
    # Lien direct vers la page (le nom dans l'URL est le nom du fichier sans le numéro)
    st.page_link("pages/1_🎨_AI_Generator.py", label="Lancer l'IA", icon="🎨")

with col2:
    st.subheader("🧵 Pattern Studio")
    st.write("Convertissez vos images en patrons DMC haute fidélité.")
    st.page_link("pages/2_🧵_Pattern_Studio.py", label="Ouvrir le Studio", icon="🧵")

with col3:
    st.subheader("🛒 Etsy Automation")
    st.write("Gérez vos mockups et mettez vos designs en vente.")
    st.page_link("pages/5_🛒_Etsy_Manager.py", label="Ma Boutique", icon="🛒")

st.divider()

# --- ÉTAT DU SYSTÈME / DASHBOARD RAPIDE ---
st.subheader("📈 Aperçu de votre activité")
d_col1, d_col2, d_col3 = st.columns(3)
d_col1.metric("Modèles créés", "12", "+2")
d_col2.metric("Ventes Etsy (simulation)", "128€", "+15%")
d_col3.metric("Stock Fils DMC", "454 couleurs", "OK")

st.info("💡 Conseil : Commencez par l'onglet **AI Generator** pour créer une image, puis passez au **Pattern Studio** pour générer vos fichiers de vente.")