import streamlit as st
import os
import io
import json
import base64
from PIL import Image, ImageOps, ImageDraw, ImageFont
from google import genai
from google.genai import types
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# --- 1. INITIALISATION CLIENT & DATA ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Clé API 'GEMINI_API_KEY' manquante dans les secrets.")

try:
    with open('rgb-dmc.json', 'r', encoding='utf-8') as f:
        DMC_DB = json.load(f)
except FileNotFoundError:
    DMC_DB = []

# --- 2. LOGIQUE IMAGE (PAGE 1) ---
def generate_pattern_image_func(subject):
    """Génère l'image source du patron avec le modèle Gemini 2.5 Flash Image"""
    MODEL_ID = "gemini-2.5-flash-image"
    BASE_PROMPT = """, ultra detailed and well-crafted,
        high contrast illustration with bold black outlines,
        clean and sharp design, strong shadows,
        simple but highly readable composition,
        centered subject, front view,
        pure white background, no background elements,
        flat colors with subtle depth,
        print-ready commercial illustration,
        vector style, sticker and t-shirt friendly,
        4k, extremely sharp, no text, no watermark"""
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Génère une image de : {subject}{BASE_PROMPT}")],
        ),
    ]

    image_result = None
    for chunk in client.models.generate_content_stream(
        model=MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    ):
        if chunk.parts and chunk.parts[0].inline_data:
            image_data = chunk.parts[0].inline_data.data
            image_result = Image.open(io.BytesIO(image_data))
            
    return image_result

# --- 3. LOGIQUE TECHNIQUE DMC (PAGE 2) ---
def get_closest_dmc(rgb):
    r, g, b = rgb
    best_match = DMC_DB[0]
    min_dist = float('inf')
    for color in DMC_DB:
        dist = ((color["r"]-r)**2 + (color["g"]-g)**2 + (color["b"]-b)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            best_match = color
    return best_match

def process_image(image, size, num_colors):
    img = ImageOps.contain(image, (size, size))
    img = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=num_colors).convert("RGB")
    return img

def get_used_colors_data(processed_img):
    used_colors = {}
    symbols = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#@$§&?%WX+"
    sym_idx = 0
    cols, rows = processed_img.size
    for y in range(rows):
        for x in range(cols):
            pixel = processed_img.getpixel((x, y))
            dmc = get_closest_dmc(pixel)
            if dmc["floss"] not in used_colors:
                used_colors[dmc["floss"]] = {
                    "info": dmc, 
                    "count": 0, 
                    "sym": symbols[sym_idx % len(symbols)]
                }
                sym_idx += 1
            used_colors[dmc["floss"]]["count"] += 1
    return used_colors

# --- 4. GÉNÉRATEURS DE PDF (PAGE 2) ---

def generate_flosscross_pdf(processed_img, user_texts, bw_mode, used_colors):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 50
    rows, cols = processed_img.size

    # PAGE 1 : COUVERTURE
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height - 50, user_texts['main_title'])
    c.setLineWidth(0.5)
    c.line(margin, height - 70, width - margin, height - 70)
    
    img_display_w = 350
    img_display_h = (rows/cols) * img_display_w
    c.drawInlineImage(processed_img, (width-img_display_w)/2, height-450, width=img_display_w, height=img_display_h)
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height-500, f"Design size: {cols} x {rows} stitches")
    c.drawString(margin, 100, user_texts['import_note'])
    c.drawString(margin, 60, user_texts['copyright'])
    c.drawRightString(width - margin, 60, "Page 1")

    # CONFIGURATION GRILLE
    MAX_POINTS_PER_PAGE = 50
    num_pages_x = (cols + MAX_POINTS_PER_PAGE - 1) // MAX_POINTS_PER_PAGE
    num_pages_y = (rows + MAX_POINTS_PER_PAGE - 1) // MAX_POINTS_PER_PAGE
    current_page_num = 2 

    # GÉNÉRATION DES PAGES
    for py in range(num_pages_y):
        for px in range(num_pages_x):
            c.showPage()
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(width/2, height - 25, f"{user_texts['main_title']} - Part {px+1},{py+1}")
            
            x_start, x_end = px * MAX_POINTS_PER_PAGE, min((px+1)*MAX_POINTS_PER_PAGE, cols)
            y_start, y_end = py * MAX_POINTS_PER_PAGE, min((py+1)*MAX_POINTS_PER_PAGE, rows)
            
            current_w, current_h = x_end - x_start, y_end - y_start
            cell_size = min((width - 100) / current_w, (height - 120) / current_h)
            draw_x, draw_y = (width - (current_w * cell_size)) / 2, (height - 60)
            
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    pixel = processed_img.getpixel((x, y))
                    dmc = get_closest_dmc(pixel)
                    data = used_colors[dmc["floss"]]
                    local_x = draw_x + (x - x_start) * cell_size
                    local_y = draw_y - (y - y_start + 1) * cell_size
                    
                    if bw_mode:
                        luma = (dmc["r"] * 0.299 + dmc["g"] * 0.587 + dmc["b"] * 0.114) / 255
                        adj = 0.6 + (luma * 0.4) 
                        fill_color, text_color, line_color = (adj, adj, adj), colors.black, colors.grey
                    else:
                        fill_color = (dmc["r"]/255, dmc["g"]/255, dmc["b"]/255)
                        line_color = colors.lightgrey
                        bright = (dmc["r"] * 299 + dmc["g"] * 587 + dmc["b"] * 114) / 1000
                        text_color = colors.white if bright < 125 else colors.black

                    c.setLineWidth(0.1)
                    c.setStrokeColor(line_color)
                    if x % 10 == 0 or y % 10 == 0:
                        c.setLineWidth(0.7)
                        c.setStrokeColor(colors.black)
                    
                    c.setFillColorRGB(*fill_color)
                    c.rect(local_x, local_y, cell_size, cell_size, fill=1, stroke=1)
                    c.setFillColor(text_color)
                    c.setFont("Helvetica", cell_size * 0.7)
                    c.drawCentredString(local_x + cell_size/2, local_y + cell_size/4, data["sym"])
            
            c.setFont("Helvetica", 8)
            c.drawRightString(width - margin, 30, f"Page {current_page_num}")
            current_page_num += 1

    # PAGE LÉGENDE
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - 50, "Thread Legend (DMC)")
    y_pos = height - 100
    for floss_code, data in used_colors.items():
        if bw_mode:
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.black)
            c.rect(margin, y_pos - 2, 12, 12, fill=1, stroke=1)
            c.setFillColor(colors.black)
        else:
            c.setFillColorRGB(data["info"]["r"]/255, data["info"]["g"]/255, data["info"]["b"]/255)
            c.rect(margin, y_pos - 2, 12, 12, fill=1)
            bright = (data["info"]["r"] * 299 + data["info"]["g"] * 587 + data["info"]["b"] * 114) / 1000
            c.setFillColor(colors.white if bright < 125 else colors.black)
        
        c.drawCentredString(margin + 6, y_pos + 1, data["sym"])
        c.setFillColor(colors.black)
        c.drawString(margin + 40, y_pos, str(floss_code))
        c.drawString(margin + 100, y_pos, data["info"]["description"])
        c.drawString(margin + 300, y_pos, str(data["count"]))
        y_pos -= 20
        if y_pos < 50:
            c.showPage()
            y_pos = height - 50
    
    c.save()
    return buffer.getvalue()

def generate_pk_pdf(processed_img, used_colors):
    buffer = io.BytesIO()
    rows, cols = processed_img.size
    cell_size = 15
    pw, ph = (cols * cell_size) + 100, (rows * cell_size) + 150
    c = canvas.Canvas(buffer, pagesize=(pw, ph))
    draw_x, draw_y = 50, ph - 50
    for y in range(rows):
        for x in range(cols):
            pixel = processed_img.getpixel((x, y))
            dmc = get_closest_dmc(pixel)
            data = used_colors[dmc["floss"]]
            rx, ry = draw_x + (x * cell_size), draw_y - ((y + 1) * cell_size)
            c.setLineWidth(0.1)
            c.setStrokeColor(colors.lightgrey)
            c.setFillColorRGB(dmc["r"]/255, dmc["g"]/255, dmc["b"]/255)
            c.rect(rx, ry, cell_size, cell_size, fill=1)
            bright = (dmc["r"] * 299 + dmc["g"] * 587 + dmc["b"] * 114) / 1000
            c.setFillColor(colors.white if bright < 125 else colors.black)
            c.setFont("Helvetica", cell_size * 0.6)
            c.drawCentredString(rx + cell_size/2, ry + cell_size/4, data["sym"])
    
    # Légende simplifiée pour Pattern Keeper
    y_leg = draw_y - (rows * cell_size) - 40
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(draw_x, y_leg, "Legend")
    y_leg -= 20
    for code, data in used_colors.items():
        c.drawString(draw_x, y_leg, f"DMC {code} - {data['info']['description']}")
        y_leg -= 15
        if y_leg < 20: break

    c.save()
    return buffer.getvalue()



def generate_mockup_func(processed_image):
    """Génère le mockup à partir de l'image pixelisée (Page 3)"""
    MODEL_ID = "gemini-2.5-flash-image"
    
    # On s'assure que l'image est nette pour l'IA
    temp_img = processed_image.convert("RGB")
    sharp_image = temp_img.resize((1024, 1024), resample=Image.NEAREST)
    
    buffered = io.BytesIO()
    sharp_image.save(buffered, format="PNG")
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(mime_type="image/png", data=buffered.getvalue()),
                types.Part.from_text(text=f"""
                    Professional Etsy product photography of a finished cross-stitch embroidery. 
                    The central design is placed inside a circular wooden embroidery hoop. 
                    IMPORTANT: The embroidery is perfectly centered, no fabric is hanging out of the hoop. 
                    The texture must show realistic individual X-shaped stitches on a clean white Aida cloth background. 
                    SCENE: Placed on a cozy, slightly blurred (bokeh) wooden table background with a pair of vintage scissors and some skeins of DMC thread next to it. 
                    LIGHTING: Soft natural morning light, realistic shadows, high resolution, 8k, macro photography. 
                    STRICT RULE: Do not modify or add any elements to the original cross-stitch pattern provided, keep the design exactly as shown.
                    """),
            ],
        ),
    ]

    image_result = None
    # On utilise ton système de stream habituel
    for chunk in client.models.generate_content_stream(
        model=MODEL_ID, 
        contents=contents, 
        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    ):
        if chunk.parts and chunk.parts[0].inline_data:
            image_data = chunk.parts[0].inline_data.data
            image_result = Image.open(io.BytesIO(image_data))
    return image_result

def add_pro_badge(target_image):
    """Ajoute le badge 'PDF PATTERN' en gros et lisible"""
    # 1. Préparation du canevas
    img = target_image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    w, h = img.size
    # On définit le badge (environ 22% de la largeur de l'image)
    badge_radius = int(w * 0.11) 
    margin = int(w * 0.05)
    
    # Centre du badge
    center_x = w - badge_radius - margin
    center_y = badge_radius + margin
    
    # Dessin du cercle de fond (Crème Etsy)
    bbox = [center_x - badge_radius, center_y - badge_radius, 
            center_x + badge_radius, center_y + badge_radius]
    
    draw.ellipse(bbox, fill=(255, 255, 255, 255)) # Fond blanc opaque
    draw.ellipse(bbox, outline=(40, 40, 40, 255), width=int(w * 0.005)) # Bordure épaisse
    
    # 2. Gestion des polices (Taille augmentée)
    try:
        # On cherche une police système. Si échec, PIL utilise la police par défaut.
        # Taille de police basée sur le rayon du badge
        font_size_big = int(badge_radius * 0.6) # "PDF"
        font_size_small = int(badge_radius * 0.25) # "PATTERN"
        
        # Chemins courants selon l'OS (Windows/Linux)
        font_path = "arial.ttf" if os.name == 'nt' else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        
        font_big = ImageFont.truetype(font_path, font_size_big)
        font_small = ImageFont.truetype(font_path, font_size_small)
    except:
        # Backup si aucune police n'est trouvée (on essaie de charger la police par défaut mais c'est souvent petit)
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 3. Dessin du texte avec ancrage au milieu (mm)
    # PDF est placé légèrement au-dessus du centre
    draw.text(
        (center_x, center_y - int(badge_radius * 0.1)), 
        "PDF", 
        fill=(0, 0, 0, 255), 
        font=font_big, 
        anchor="mm"
    )
    
    # PATTERN est placé en dessous
    draw.text(
        (center_x, center_y + int(badge_radius * 0.45)), 
        "PATTERN", 
        fill=(60, 60, 60, 255), 
        font=font_small, 
        anchor="mm"
    )
    
    # Fusion et retour en RGB
    return Image.alpha_composite(img, overlay).convert("RGB")




def generate_seo_package(visual_concept, num_colors, grid_size):
    """Génère le pack SEO avec les vraies specs techniques"""
    MODEL_ID_TEXT = "gemini-2.0-flash"
    
    seo_prompt = f"""
    Act as a top-tier Etsy SEO expert. Create a professional listing for a Digital PDF Cross Stitch Pattern.
    Subject: {visual_concept}
    Technical Specs: {grid_size}x{grid_size} stitches, exactly {num_colors} DMC colors used.
    
    Return ONLY a JSON object with these exact keys: "title", "description", "tags".
    - "title": 140 chars max.
    - "description": Mention clearly that the pattern is {grid_size}x{grid_size} stitches and uses {num_colors} colors.
    - "tags": 13 tags, comma-separated.
    """

    response = client.models.generate_content(
        model=MODEL_ID_TEXT, 
        contents=seo_prompt,
        config={'response_mime_type': 'application/json'}
    )
    return json.loads(response.text)





def load_factory_history():
    """Charge l'historique des sujets déjà traités depuis le fichier JSON"""
    file_path = 'factory_history.json'
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_to_factory_history(subject):
    """Ajoute un sujet à l'historique pour éviter les doublons"""
    history = load_factory_history()
    if subject not in history:
        history.append(subject)
        with open('factory_history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)



def ensure_export_dir():
    """Crée le dossier exports s'il n'existe pas"""
    if not os.path.exists("exports"):
        os.makedirs("exports")

def get_all_saved_products():
    """Récupère la liste des dossiers de produits déjà générés"""
    ensure_export_dir()
    return [d for d in os.listdir("exports") if os.path.isdir(os.path.join("exports", d))]