import streamlit as st
import os
import subprocess
import time
import shutil
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

# --- GESTION DE LA LISTE MAITRE (SIDEBAR) ---
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
    
    .master-list-box {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        line-height: 1.8;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }

    .done-pill { color: #00ff88; font-weight: bold; text-decoration: line-through rgba(0,255,136,0.3); padding: 0 4px; }
    .todo-pill { color: #8b949e; padding: 0 4px; }

    [data-testid="stImage"] img {
        width: 100% !important;
        height: auto !important;
        image-rendering: pixelated;
        border-radius: 8px;
        border: 1px solid #30363d;
    }

    .copy-container { 
        background-color: #0d1117; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #30363d; 
        border-left: 5px solid #2e7d32; 
    }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def copy_btn(text, label, key):
    clean_text = text.replace("`", "\\`").replace("'", "\\'").replace("\n", "\\n")
    html = f"""<button onclick="navigator.clipboard.writeText(`{clean_text}`)" style="background-color: #1e4620; color: white; border: 1px solid #2e7d32; padding: 10px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; font-size: 12px;">📋 {label}</button>"""
    st.components.v1.html(html, height=50)

def open_folder_and_select(file_path):
    path = os.path.realpath(file_path)
    subprocess.Popen(f'explorer /select,"{path}"')

# --- SIDEBAR : LISTE INTELLIGENTE ---
with st.sidebar:
    st.title("📑 Master List")
    raw_content = load_master_list()
    # On sépare par virgule ET retour à la ligne pour l'analyse
    all_items = [s.strip() for s in raw_content.replace(',', '\n').split('\n') if s.strip()]
    existing_folders = [f.lower() for f in os.listdir("exports")] if os.path.exists("exports") else []
    
    formatted_html = '<div class="master-list-box">'
    items_to_keep = []
    
    for item in all_items:
        safe_name = "".join([c if c.isalnum() else "_" for c in item]).lower()
        if safe_name in existing_folders:
            formatted_html += f'<span class="done-pill">{item}</span>, '
        else:
            formatted_html += f'<span class="todo-pill">{item}</span>, '
            items_to_keep.append(item)
    
    formatted_html = formatted_html.rstrip(', ') + '</div>'
    st.markdown(formatted_html, unsafe_allow_html=True)
    
    st.divider()
    with st.expander("📝 Éditer la source"):
        new_content = st.text_area("Source (Virgules ou lignes) :", value=raw_content, height=150)
        if st.button("Enregistrer"):
            save_master_list(new_content)
            st.rerun()
    
    if st.button("🧹 Nettoyer la liste"):
        save_master_list("\n".join(items_to_keep))
        st.rerun()

# --- ZONE DE PRODUCTION ---
st.title("🏭 Production Session")
col_input, col_config = st.columns([2, 1])

with col_input:
    to_process = st.text_area("🚀 **Sujets à traiter (séparés par virgules ou lignes) :**", 
                              placeholder="Ex: chat, petit chien, forêt enchantée...", height=120)
    # MODIFICATION ICI : On nettoie pour accepter les virgules
    process_list = [s.strip() for s in to_process.replace(',', '\n').split('\n') if s.strip()]

with col_config:
    st.write("⚙️ **Réglages**")
    g_size = st.select_slider("Grille", options=[40, 60, 80, 100, 120, 150, 200], value=100)
    run_btn = st.button("⚡ LANCER LA PRODUCTION", type="primary", use_container_width=True)

if run_btn and process_list:
    for i, subject in enumerate(process_list):
        st.subheader(f"🛠️ {i+1}/{len(process_list)} : {subject}")
        p_bar = st.progress(0)
        try:
            img_ref = generate_pattern_image_func(subject)
            p_bar.progress(30)
            img_pix = process_image(img_ref, g_size, 18)
            img_pix_hd = img_pix.resize((2000, 2000), resample=Image.NEAREST)
            p_bar.progress(60)
            mock = add_pro_badge(generate_mockup_func(img_pix))
            colors = get_used_colors_data(img_pix)
            seo = generate_seo_package(subject, len(colors), g_size)
            
            safe = "".join([c if c.isalnum() else "_" for c in subject])
            folder_path = os.path.join("exports", safe)
            if not os.path.exists(folder_path): os.makedirs(folder_path)
            
            img_ref.save(os.path.join(folder_path, "1_ref.png"))
            img_pix_hd.save(os.path.join(folder_path, "2_pix_hd.png"))
            mock.save(os.path.join(folder_path, "3_mockup.png"))
            
            with open(os.path.join(folder_path, "seo.txt"), "w", encoding="utf-8") as f:
                f.write(f"TITLE:\n{seo['title']}\n\nTAGS:\n{seo['tags']}\n\nDESCRIPTION:\n{seo['description']}")
            
            texts = {'main_title': subject.upper(), 'sub_title': "Pattern", 'import_note': f"Size: {g_size}", 'copyright': "©2026"}
            with open(os.path.join(folder_path, "color.pdf"), "wb") as f: f.write(generate_flosscross_pdf(img_pix, texts, False, colors))
            with open(os.path.join(folder_path, "bw.pdf"), "wb") as f: f.write(generate_flosscross_pdf(img_pix, texts, True, colors))
            with open(os.path.join(folder_path, "pk.pdf"), "wb") as f: f.write(generate_pk_pdf(img_pix, colors))
            
            save_to_factory_history(subject)
            p_bar.progress(100)
        except Exception as e:
            st.error(f"Erreur sur {subject} : {e}")
    st.rerun()

# --- HISTORIQUE COMPLET AVEC SYSTÈME DE SUPPRESSION ---
st.divider()
st.subheader("🗃️ Inventaire des Productions")

if os.path.exists("exports"):
    # On récupère la liste des dossiers
    folders = sorted(os.listdir("exports"), reverse=True)
    
    for f in folders:
        p = os.path.join("exports", f)
        if os.path.isdir(p):
            # Création d'une ligne avec le titre et le bouton de suppression
            # On utilise un container pour grouper visuellement
            with st.expander(f"📦 {f.replace('_', ' ').upper()}", expanded=False):
                
                # --- ZONE DE SUPPRESSION (SÉCURISÉE) ---
                col_title, col_del = st.columns([5, 1])
                with col_del:
                    # Popover pour confirmer la suppression sans tout supprimer par erreur
                    with st.popover("🗑️ Supprimer", use_container_width=True):
                        st.warning("Confirmer la suppression ?")
                        if st.button("OUI, SUPPRIMER", key=f"del_{f}", type="primary", use_container_width=True):
                            import shutil
                            shutil.rmtree(p) # Supprime le dossier et tout son contenu
                            st.toast(f"Produit {f} supprimé.")
                            time.sleep(1)
                            st.rerun()

                # --- AFFICHAGE DES VISUELS ---
                v1, v2, v3 = st.columns(3)
                # Image 1 : Référence
                if os.path.exists(os.path.join(p, "1_ref.png")):
                    v1.image(os.path.join(p, "1_ref.png"), caption="Référence IA")
                
                # Image 2 : Pixel HD (avec fallback)
                img_px_path = os.path.join(p, "2_pix_hd.png")
                if not os.path.exists(img_px_path): 
                    img_px_path = os.path.join(p, "2_pix.png")
                
                if os.path.exists(img_px_path):
                    v2.image(img_px_path, caption="Pixel HD (Etsy Ready)")
                
                # Image 3 : Mockup
                if os.path.exists(os.path.join(p, "3_mockup.png")):
                    v3.image(os.path.join(p, "3_mockup.png"), caption="Mockup Final")
                
                # --- SEO & ACTIONS ---
                st.write("")
                c_seo, c_act = st.columns([3, 1])
                
                with c_seo:
                    seo_path = os.path.join(p, "seo.txt")
                    if os.path.exists(seo_path):
                        with open(seo_path, "r", encoding="utf-8") as file:
                            content = file.read().split('\n\n')
                            t_v = content[0].replace('TITLE:', '').strip() if len(content)>0 else ""
                            tg_v = content[1].replace('TAGS:', '').strip() if len(content)>1 else ""
                            ds_v = content[2].replace('DESCRIPTION:', '').strip() if len(content)>2 else ""
                        
                        st.markdown('<div class="copy-container">', unsafe_allow_html=True)
                        st.write("🏃 **Copie Rapide :**")
                        bc1, bc2, bc3 = st.columns(3)
                        with bc1: copy_btn(t_v, "Titre", f"t_{f}")
                        with bc2: copy_btn(tg_v, "Tags", f"tg_{f}")
                        with bc3: copy_btn(ds_v, "Description", f"d_{f}")
                        st.markdown('</div>', unsafe_allow_html=True)
                
                with c_act:
                    st.write("📂 **Fichiers :**")
                    if st.button("📁 Dossier Windows", key=f"btn_{f}", use_container_width=True):
                        target = os.path.join(p, "color.pdf")
                        open_folder_and_select(target if os.path.exists(target) else p)
                    st.success("Prêt ✅")