import streamlit as st
from app_auth import check_password
import pandas as pd
import datetime

if not check_password():
    st.stop()

st.set_page_config(page_title="Etsy Shop Manager", layout="wide")

# --- HEADER STATUT ---
st.title("🏪 Etsy Shop Manager")

# Simulation du statut de connexion
etsy_connected = False # Changera à True une fois l'API validée

if not etsy_connected:
    st.warning("🔌 **Statut : En attente de validation de l'API Etsy**")
    st.info("Cette page est actuellement en mode simulation. Une fois ton application validée par Etsy, les données réelles de ta boutique s'afficheront ici.")
else:
    st.success("✅ Connecté à la boutique : **TonNomDeBoutique**")

st.divider()

# --- BLOC 1 : STATISTIQUES (Simulées) ---
st.subheader("📈 Performances de la boutique (Simulation)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Ventes totales", value="124", delta="+12%")
with col2:
    st.metric(label="Visites (30j)", value="1,850", delta="+5%")
with col3:
    st.metric(label="Chiffre d'affaires", value="845.50 €", delta="15.20 €")
with col4:
    st.metric(label="Annonces actives", value="42")

st.divider()

# --- BLOC 2 : GESTION DES ANNONCES ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📦 Annonces en ligne")
    # Simulation d'un tableau de listings
    data = {
        "Date": [datetime.date(2026, 2, 1), datetime.date(2026, 2, 5), datetime.date(2026, 2, 10)],
        "Titre": ["Majestic Owl Pattern", "Vintage Space Rocket", "Gothic Bat Design"],
        "Ventes": [12, 8, 3],
        "Stock": ["Illimité (Digital)", "Illimité (Digital)", "Illimité (Digital)"],
        "Prix": ["6.50 €", "7.20 €", "5.90 €"]
    }
    df = pd.DataFrame(data)
    st.table(df)

with col_right:
    st.subheader("🛠️ Actions rapides")
    st.button("🔄 Actualiser les stocks", use_container_width=True)
    st.button("📊 Exporter le rapport CSV", use_container_width=True)
    
    st.write("---")
    st.write("**Dernières activités :**")
    st.caption("• Commande #12948 reçue (il y a 2h)")
    st.caption("• Nouveau favori : 'Vintage Space Rocket' (il y a 5h)")

# --- BLOC 3 : CONFIGURATION API ---
with st.expander("🔑 Configuration de la connexion Etsy"):
    st.write("Dès que tu reçois tes accès, remplis ces champs dans tes secrets Streamlit :")
    st.code("""
ETSY_API_KEY = "ta_cle_ici"
ETSY_SHARED_SECRET = "ton_secret_ici"
ETSY_SHOP_ID = "ton_id_de_boutique"
    """, language="text")
    
    if st.button("Tester la connexion (Simulation)"):
        with st.spinner("Tentative de handshake avec Etsy..."):
            import time
            time.sleep(2)
            st.error("Erreur 403 : Application en attente de révision par Etsy.")