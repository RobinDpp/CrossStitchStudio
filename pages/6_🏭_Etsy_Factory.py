import streamlit as st
import io
import os
from PIL import Image
from app_auth import check_password
from utils import (
    generate_pattern_image_func, process_image, get_used_colors_data,
    generate_flosscross_pdf, generate_pk_pdf, generate_mockup_func, 
    add_pro_badge, generate_seo_package, load_factory_history, save_to_factory_history,
    ensure_export_dir
)

if not check_password():
    st.stop()

st.set_page_config(page_title="Etsy Factory Ultra", layout="wide")
ensure_export_dir()

# --- CSS POUR LA NETTETÉ DES PIXELS (Pixel-Art rendering) ---
st.markdown("""
    <style>
    img {
        image-rendering: pixelated; /* Pour Chrome/Edge/Safari */
        image-rendering: crisp-edges; /* Pour Firefox */
    }
    .product-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        background-color: #f9f9f9;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 Etsy Factory Pro")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Configuration")
    grid_size = st.slider("Nombre de points (Largeur/Hauteur)", 40, 200, 100) 
    max_colors = st.slider("Palette DMC max", 5, 40, 15)
    st.divider()
    st.info("Stockage local actif : /exports")

# --- INPUT ---
subjects_input = st.text_area("Liste des nouveaux sujets :", placeholder="A vintage space rocket...", height=100)

if st.button("⚡ Lancer la production", type="primary", use_container_width=True):
    subjects = [s.strip() for s in subjects_input.split('\n') if s.strip()]
    
    for subject in subjects:
        safe_name = "".join([c if c.isalnum() else "_" for c in subject])
        prod_path = os.path.join("exports", safe_name)
        
        if os.path.exists(prod_path):
            st.warning(f"⏩ '{subject}' déjà dans l'historique. Ignoré.")
            continue
            
        with st.status(f"🛠️ Fabrication de : {subject}...", expanded=True) as status:
            try:
                st.write("🎨 Étape 1 : Génération de l'image de référence...")
                img_ref = generate_pattern_image_func(subject)
                
                st.write(f"🧵 Étape 2 : Pixelisation (Grille : {grid_size}x{grid_size})...")
                img_pix = process_image(img_ref, grid_size, max_colors)
                colors_data = get_used_colors_data(img_pix)
                
                st.write("🖼️ Étape 3 : Création du Mockup...")
                mock_raw = generate_mockup_func(img_pix)
                mock_final = add_pro_badge(mock_raw)
                
                st.write("🔍 Étape 4 : Rédaction SEO (Adaptation Taille + Couleurs)...")
                # ON PASSE ICI LA TAILLE RÉELLE AU SEO
                seo = generate_seo_package(subject, len(colors_data), grid_size)
                
                st.write("📄 Étape 5 : Génération des 3 versions PDF...")
                texts = {'main_title': subject.upper(), 'sub_title': "Pattern", 'import_note': f"Size: {grid_size}x{grid_size}", 'copyright': "©2026"}
                pdf_color = generate_flosscross_pdf(img_pix, texts, False, colors_data)
                pdf_bw = generate_flosscross_pdf(img_pix, texts, True, colors_data)
                pdf_pk = generate_pk_pdf(img_pix, colors_data)
                
                # --- SAUVEGARDE PHYSIQUE ---
                os.makedirs(prod_path)
                img_ref.save(os.path.join(prod_path, "1_ref.png"))
                img_pix.save(os.path.join(prod_path, "2_pix.png"))
                mock_final.save(os.path.join(prod_path, "3_mockup.png"))
                with open(os.path.join(prod_path, "seo.txt"), "w", encoding="utf-8") as f:
                    f.write(f"TITLE:\n{seo['title']}\n\nTAGS:\n{seo['tags']}\n\nDESCRIPTION:\n{seo['description']}")
                with open(os.path.join(prod_path, "color.pdf"), "wb") as f: f.write(pdf_color)
                with open(os.path.join(prod_path, "bw.pdf"), "wb") as f: f.write(pdf_bw)
                with open(os.path.join(prod_path, "pk.pdf"), "wb") as f: f.write(pdf_pk)
                
                save_to_factory_history(subject)
                status.update(label=f"✅ {subject} Terminé !", state="complete")
            except Exception as e:
                st.error(f"Erreur sur {subject}: {e}")

# --- AFFICHAGE DE LA LISTE ---
st.divider()
st.subheader("📦 Historique Complet")

if os.path.exists("exports"):
    product_folders = sorted(os.listdir("exports"), reverse=True)
    
    for folder in product_folders:
        path = os.path.join("exports", folder)
        if os.path.isdir(path):
            with st.expander(f"📁 PRODUIT : {folder.replace('_', ' ')}", expanded=False):
                col_img1, col_img2, col_img3 = st.columns(3)
                
                img_ref = Image.open(os.path.join(path, "1_ref.png"))
                img_pix = Image.open(os.path.join(path, "2_pix.png"))
                mockup = Image.open(os.path.join(path, "3_mockup.png"))
                
                col_img1.image(img_ref, caption="Référence IA", use_container_width=True)
                # L'image suivante sera nette grâce au CSS injecté plus haut
                col_img2.image(img_pix, caption=f"Rendu Pixel-Perfect", use_container_width=True)
                col_img3.image(mockup, caption="Mockup Etsy", use_container_width=True)

                st.divider()
                
                col_seo, col_dl = st.columns([2, 1])
                with col_seo:
                    if os.path.exists(os.path.join(path, "seo.txt")):
                        with open(os.path.join(path, "seo.txt"), "r", encoding="utf-8") as f:
                            st.text_area("SEO (Taille & Couleurs incluses)", f.read(), height=220, key=f"seo_{folder}")

                with col_dl:
                    st.write("📥 Télécharger :")
                    with open(os.path.join(path, "color.pdf"), "rb") as f:
                        st.download_button("🎨 PDF Couleur", f.read(), f"{folder}_color.pdf", key=f"dl_c_{folder}", use_container_width=True)
                    with open(os.path.join(path, "bw.pdf"), "rb") as f:
                        st.download_button("🏁 PDF Noir & Blanc", f.read(), f"{folder}_bw.pdf", key=f"dl_b_{folder}", use_container_width=True)
                    with open(os.path.join(path, "pk.pdf"), "rb") as f:
                        st.download_button("📱 Pattern Keeper", f.read(), f"{folder}_pk.pdf", key=f"dl_p_{folder}", use_container_width=True)