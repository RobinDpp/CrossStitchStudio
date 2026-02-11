import streamlit as st

def check_password():
    """Retourne True si l'utilisateur a saisi le bon mot de passe."""
    if st.session_state.get("password_correct", False):
        return True

    st.title("🔐 Accès Privé")
    placeholder = st.empty()
    
    with placeholder.form("login"):
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")
    
    if submit:
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            placeholder.empty() # Efface le formulaire
            st.rerun()
        else:
            st.error("😕 Mot de passe incorrect.")
            
    return False