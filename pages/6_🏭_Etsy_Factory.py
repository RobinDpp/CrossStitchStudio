import streamlit as st
import os
import subprocess
from PIL import Image
from app_auth import check_password
from utils import (
    generate_pattern_image_func, process_image, get_used_colors_data,
    generate_flosscross_pdf, generate_pk_pdf, generate_mockup_func, 
    add_pro_badge, generate_seo_package, save_to_factory_history,
    ensure_export_dir
)

if not check_password():
    st.stop()

st.set_page_config(page_title="Factory Master List", layout="wide", page_icon="📑")
ensure_export_dir()

# --- GESTION DE LA LISTE ---
MASTER_LIST_FILE = "master_list.txt"

def load_master_list():
    if not os.path.exists(MASTER_LIST_FILE): return ""
    with open(MASTER_LIST_FILE, "r", encoding="utf-8") as f:
        return f.read()

def save_master_list(content):
    with open(MASTER_LIST_FILE, "w", encoding="utf-8") as f:
        f.write(content)

# --- CSS DARK MODE & COLORS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    
    /* Container de la liste */
    .master-list-box {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        line-height: 1.8;
        font-family: 'Cascadia Code', 'Courier New', monospace;
        font-size: 14px;
    }

    /* Style des mots faits */
    .done-pill {
        color: #00ff88;
        font-weight: bold;
        text-decoration: line-through rgba(0,255,136,0.3);
        padding: 0 4px;
    }

    /* Style des mots à faire */
    .todo-pill {
        color: #8b949e;
        padding: 0 4px;
    }

    [data-testid="stImage"] img {
        width: 100% !important;
        image-rendering: pixelated;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR : L'AFFICHAGE INTELLIGENT ---
with st.sidebar:
    st.title("📑 Master List")
    
    raw_content = load_master_list()
    # Séparation par virgule ou saut de ligne
    all_items = [s.strip() for s in raw_content.replace(',', '\n').split('\n') if s.strip()]
    
    # Vérification des dossiers existants
    existing_folders = [f.lower() for f in os.listdir("exports")] if os.path.exists("exports") else []
    
    # Construction de la vue visuelle
    formatted_html = '<div class="master-list-box">'
    items_to_keep = [] # Pour le bouton de nettoyage
    
    for item in all_items:
        safe_name = "".join([c if c.isalnum() else "_" for c in item]).lower()
        if safe_check := safe_name in existing_folders:
            formatted_html += f'<span class="done-pill">{item}</span>, '
        else:
            formatted_html += f'<span class="todo-pill">{item}</span>, '
            items_to_keep.append(item)
    
    formatted_html = formatted_html.rstrip(', ') + '</div>'
    
    st.markdown(formatted_html, unsafe_allow_html=True)
    
    st.divider()
    # Zone d'édition cachée dans un expander pour ne pas encombrer
    with st.expander("📝 Éditer la source"):
        new_content = st.text_area("Collez votre liste ici :", value=raw_content, height=150)
        if st.button("Enregistrer les modifs"):
            save_master_list(new_content)
            st.rerun()
    
    if st.button("🧹 Nettoyer (Enlever faits)"):
        save_master_list("\n".join(items_to_keep))
        st.rerun()

# --- ZONE DE PRODUCTION ---
st.title("🏭 Production Session")
st.caption("Copie les noms grisés de la liste à gauche et colle-les ici.")

col_input, col_config = st.columns([2, 1])

with col_input:
    to_process = st.text_area("🚀 **Sujets à traiter :**", placeholder="Ex: Petit chat, Forêt mystique...", height=120)
    process_list = [s.strip() for s in to_process.split('\n') if s.strip()]

with col_config:
    st.write("⚙️ **Réglages**")
    g_size = st.select_slider("Grille", options=[40, 60, 80, 100, 120, 150, 200], value=100)
    run_btn = st.button("⚡ LANCER LA PRODUCTION", type="primary", use_container_width=True)

if run_btn and process_list:
    for i, subject in enumerate(process_list):
        st.subheader(f"🛠️ {i+1}/{len(process_list)} : {subject}")
        p_bar = st.progress(0)
        
        try:
            # 1. Génération HD (Upscale x20 intégré)
            img_ref = generate_pattern_image_func(subject)
            p_bar.progress(30)
            
            img_pix = process_image(img_ref, g_size, 18)
            img_pix_hd = img_pix.resize((2000, 2000), resample=Image.NEAREST)
            p_bar.progress(60)
            
            # 2. Mockup & SEO
            mock = add_pro_badge(generate_mockup_func(img_pix))
            colors = get_used_colors_data(img_pix)
            seo = generate_seo_package(subject, len(colors), g_size)
            
            # 3. Sauvegarde (Chemin d'accès sécurisé)
            safe = "".join([c if c.isalnum() else "_" for c in subject])
            folder_path = os.path.join("exports", safe)
            if not os.path.exists(folder_path): os.makedirs(folder_path)
            
            img_ref.save(os.path.join(folder_path, "1_ref.png"))
            img_pix_hd.save(os.path.join(folder_path, "2_pix_hd.png"))
            mock.save(os.path.join(folder_path, "3_mockup.png"))
            
            # Sauvegarde SEO (Titre, Tags, Desc)
            with open(os.path.join(folder_path, "seo.txt"), "w", encoding="utf-8") as f:
                f.write(f"TITLE:\n{seo['title']}\n\nTAGS:\n{seo['tags']}\n\nDESCRIPTION:\n{seo['description']}")
            
            # PDF Generation
            texts = {'main_title': subject.upper(), 'sub_title': "Pattern", 'import_note': f"Size: {g_size}", 'copyright': "©2026"}
            with open(os.path.join(folder_path, "color.pdf"), "wb") as f: f.write(generate_flosscross_pdf(img_pix, texts, False, colors))
            with open(os.path.join(folder_path, "bw.pdf"), "wb") as f: f.write(generate_flosscross_pdf(img_pix, texts, True, colors))
            with open(os.path.join(folder_path, "pk.pdf"), "wb") as f: f.write(generate_pk_pdf(img_pix, colors))
            
            save_to_factory_history(subject)
            p_bar.progress(100)
        except Exception as e:
            st.error(f"Erreur sur {subject}: {e}")
    st.rerun()

# --- HISTORIQUE (Avec Fallback HD/Standard) ---
st.divider()
if os.path.exists("exports"):
    folders = sorted(os.listdir("exports"), reverse=True)
    for f in folders:
        p = os.path.join("exports", f)
        if os.path.isdir(p):
            with st.expander(f"📦 {f.replace('_', ' ')}"):
                # ... Ton affichage habituel avec les 3 colonnes d'images et les boutons de copie ...
                st.write("Produit prêt à l'emploi.")