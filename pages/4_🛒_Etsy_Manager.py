import streamlit as st
import requests
import hashlib
import os
import base64
from app_auth import check_password

if not check_password():
    st.stop()

st.title("🛍️ Etsy Automation - Connexion")

# Configuration
CLIENT_ID = st.secrets["ETSY_CLIENT_ID"]
REDIRECT_URI = st.secrets["ETSY_REDIRECT_URI"]

# 1. Préparation de la connexion (PKCE)
if 'etsy_state' not in st.session_state:
    st.session_state.etsy_state = base64.urlsafe_b64encode(os.urandom(30)).decode('utf-8')
    st.session_state.code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode('utf-8')
    
    # Hashage du code verifier pour Etsy
    m = hashlib.sha256()
    m.update(st.session_state.code_verifier.encode('utf-8'))
    st.session_state.code_challenge = base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace('=', '')

# 2. Lien d'autorisation
# On demande les droits pour lire et créer des listings (brouillons)
scopes = "listings_w%20listings_r%20shops_r"
auth_url = (
    f"https://www.etsy.com/oauth/connect?"
    f"response_type=code&"
    f"redirect_uri={REDIRECT_URI}&"
    f"scope={scopes}&"
    f"client_id={CLIENT_ID}&"
    f"state={st.session_state.etsy_state}&"
    f"code_challenge={st.session_state.code_challenge}&"
    f"code_challenge_method=S256"
)

st.write(f"DEBUG - ID utilisé : {CLIENT_ID}")
st.write(f"DEBUG - URL de redirection : {REDIRECT_URI}")

st.write("### Étape 1 : Autorisation")
st.link_button("Se connecter à ma boutique Etsy", auth_url)

# 3. Récupération du jeton
st.write("### Étape 2 : Validation")
st.info("Après avoir cliqué sur le lien et accepté, Etsy vous renverra sur votre app. Copiez le paramètre 'code' dans l'URL (ex: ?code=abc...) et collez-le ici :")

auth_code = st.text_input("Collez le code reçu ici :")

if st.button("Valider la connexion"):
    if auth_code:
        token_url = "https://api.etsy.com/v2/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code": auth_code,
            "code_verifier": st.session_state.code_verifier
        }
        
        response = requests.post(token_url, data=payload)
        
        if response.status_code == 200:
            st.session_state.etsy_token = response.json()
            st.success("✅ Connecté à Etsy avec succès !")
            st.json(st.session_state.etsy_token) # Pour voir si on a bien le token
        else:
            st.error(f"Erreur : {response.text}")