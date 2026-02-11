import streamlit as st
import requests
import secrets
import hashlib
import base64
from app_auth import check_password

if not check_password():
    st.stop()

# --- CONFIGURATION ---
CLIENT_ID = st.secrets.get("ETSY_CLIENT_ID")
REDIRECT_URI = st.secrets.get("ETSY_REDIRECT_URI")

st.set_page_config(page_title="Connexion Etsy", layout="wide")

st.title("🛍️ Intégration Boutique Etsy")

# --- FONCTIONS TECHNIQUES OAUTH2 ---
def generate_pkce_pair():
    """Génère le code challenge pour la sécurité OAuth d'Etsy"""
    verifier = secrets.token_urlsafe(80)
    sha256 = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').replace('=', '')
    return verifier, challenge

# --- INTERFACE DE CONNEXION ---
if 'etsy_token' not in st.session_state:
    st.info("Votre boutique n'est pas encore connectée.")
    
    if st.button("🔗 Se connecter à Etsy"):
        # 1. Préparation de la demande d'autorisation
        verifier, challenge = generate_pkce_pair()
        st.session_state['etsy_verifier'] = verifier
        
        # Scopes nécessaires pour créer des fiches produits
        scopes = "listings_w%20listings_r%20shops_r"
        state = secrets.token_urlsafe(16)
        
        auth_url = (
            f"https://www.etsy.com/oauth/connect?"
            f"response_type=code&"
            f"redirect_uri={REDIRECT_URI}&"
            f"scope={scopes}&"
            f"client_id={CLIENT_ID}&"
            f"state={state}&"
            f"code_challenge={challenge}&"
            f"code_challenge_method=S256"
        )
        
        st.markdown(f"""
            <a href="{auth_url}" target="_blank">
                <div style="text-align: center; padding: 15px; background-color: #F1641E; color: white; border-radius: 10px; font-weight: bold; text-decoration: none;">
                    Cliquer ici pour autoriser l'accès à votre boutique Etsy
                </div>
            </a>
            """, unsafe_allow_html=True)
        
    # Zone pour coller le code après redirection
    auth_code = st.text_input("Une fois autorisé, collez ici le code présent dans l'URL de redirection (code=...) :")
    
    if auth_code:
        if st.button("Finaliser la connexion"):
            # Échange du code contre un Token
            payload = {
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID,
                'redirect_uri': REDIRECT_URI,
                'code': auth_code,
                'code_verifier': st.session_state['etsy_verifier']
            }
            
            response = requests.post("https://api.etsy.com/v3/public/oauth/token", data=payload)
            
            if response.status_code == 200:
                st.session_state['etsy_token'] = response.json()
                st.success("✅ Boutique connectée avec succès !")
                st.rerun()
            else:
                st.error(f"Erreur lors de la connexion : {response.text}")

# --- INTERFACE UNE FOIS CONNECTÉ ---
else:
    st.success("✅ Connecté à votre boutique Etsy")
    
    # Récupération de l'image de la page 3
    final_image = st.session_state.get('last_gen')
    
    if final_image:
        st.subheader("Préparation de la fiche produit")
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(final_image, use_container_width=True)
        
        with col2:
            title = st.text_input("Titre de la fiche", value="Digital Cross Stitch Pattern - Modern Design")
            desc = st.text_area("Description", value="Beautiful PDF pattern for instant download...")
            price = st.number_input("Prix (€)", value=5.50)
            
            if st.button("📤 Envoyer sur Etsy (Brouillon)"):
                st.warning("L'envoi direct nécessite la validation de votre application par Etsy. Voulez-vous simuler l'envoi ?")
                # Ici on ajouterait la requête POST vers /v3/application/shops/{shop_id}/listings
    else:
        st.warning("Aucune image générée trouvée. Allez à la page 3 d'abord.")

    if st.button("🚪 Déconnexion"):
        del st.session_state['etsy_token']
        st.rerun()