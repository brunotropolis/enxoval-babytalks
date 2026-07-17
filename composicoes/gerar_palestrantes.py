"""
Gera composição das 4 palestrantes do Baby Talks a partir das fotos reais.
Preserva 100% do rosto (crop centralizado das originais) e aplica identidade visual do evento.

Saída:
- palestrantes-horizontal.jpg (1600x900) — pra WhatsApp/site
- palestrantes-quadrado.jpg (1080x1080) — pra Instagram feed
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

# ---- CONFIG
IMG_DIR = Path("D:/CLAUDE/baby-talks-prep/images")
OUT_DIR = Path("D:/CLAUDE/enxoval-babytalks/composicoes")
FONT_DIR = OUT_DIR

# Fontes
F_TITLE = str(FONT_DIR / "Fraunces-MediumItalic.ttf")
F_NAME = str(FONT_DIR / "Fraunces-SemiBold.ttf")
F_ROLE = str(FONT_DIR / "DMSans-Regular.ttf")
F_TAG = str(FONT_DIR / "DMSans-Bold.ttf")

# Paleta
AZUL = (31, 42, 86)
LILAS = (142, 155, 209)
LILAS_CLARO = (176, 188, 229)
LAVANDA = (228, 230, 242)
MAGENTA = (201, 95, 163)
BRANCO_SUAVE = (248, 247, 244)

# Palestrantes (ordem oficial do site)
PALESTRANTES = [
    {"nome": "Dayane Dos Anjos", "role": "Sono & Amamentação", "img": "dayane.jpg", "crop_y": 0.28},
    {"nome": "Patricia Moreira", "role": "Educadora em Saúde", "img": "palestrante-patricia.jpg", "crop_y": 0.22},
    {"nome": "Alline Vieira", "role": "Fisio pélvica & Doula", "img": "palestrante-alline.jpg", "crop_y": 0.20},
    {"nome": "Dra. Juliana Chalupe", "role": "Ginecologista & Obstetra", "img": "palestrante-juliana.jpg", "crop_y": 0.22},
]

def gradient_bg(W, H):
    """Fundo gradient lilás-claro → lavanda → branco (vertical)"""
    bg = Image.new("RGB", (W, H), BRANCO_SUAVE)
    for y in range(H):
        t = y / H
        if t < 0.55:
            # de lilás-claro pra lavanda
            k = t / 0.55
            r = int(LILAS_CLARO[0] * (1-k) + LAVANDA[0] * k)
            g = int(LILAS_CLARO[1] * (1-k) + LAVANDA[1] * k)
            b = int(LILAS_CLARO[2] * (1-k) + LAVANDA[2] * k)
        else:
            # de lavanda pra branco-suave
            k = (t - 0.55) / 0.45
            r = int(LAVANDA[0] * (1-k) + BRANCO_SUAVE[0] * k)
            g = int(LAVANDA[1] * (1-k) + BRANCO_SUAVE[1] * k)
            b = int(LAVANDA[2] * (1-k) + BRANCO_SUAVE[2] * k)
        for x in range(W):
            bg.putpixel((x, y), (r, g, b))
    return bg

def gradient_bg_fast(W, H):
    """Versão rápida: gera 1 coluna e replica"""
    col = Image.new("RGB", (1, H), BRANCO_SUAVE)
    px = col.load()
    for y in range(H):
        t = y / H
        if t < 0.55:
            k = t / 0.55
            r = int(LILAS_CLARO[0] * (1-k) + LAVANDA[0] * k)
            g = int(LILAS_CLARO[1] * (1-k) + LAVANDA[1] * k)
            b = int(LILAS_CLARO[2] * (1-k) + LAVANDA[2] * k)
        else:
            k = (t - 0.55) / 0.45
            r = int(LAVANDA[0] * (1-k) + BRANCO_SUAVE[0] * k)
            g = int(LAVANDA[1] * (1-k) + BRANCO_SUAVE[1] * k)
            b = int(LAVANDA[2] * (1-k) + BRANCO_SUAVE[2] * k)
        px[0, y] = (r, g, b)
    return col.resize((W, H), Image.BILINEAR)

def crop_face_square(path, crop_y_ratio=0.25, size=520):
    """Abre foto e recorta quadrado centralizado no rosto."""
    img = Image.open(path).convert("RGB")
    W, H = img.size
    side = min(W, H)
    # centralizar horizontalmente
    x0 = (W - side) // 2
    # verticalmente, deslocar pra cima pra pegar o rosto
    face_center_y = int(H * crop_y_ratio + side / 2)
    y0 = max(0, min(H - side, face_center_y - side // 2))
    crop = img.crop((x0, y0, x0 + side, y0 + side))
    return crop.resize((size, size), Image.LANCZOS)

def foto_com_moldura(foto, tamanho, borda_cor=(255,255,255), borda=6, shadow=True):
    """Aplica máscara circular + borda branca + sombra."""
    S = tamanho
    # canvas RGBA com sombra
    padding = 24 if shadow else 6
    canvas_size = S + padding * 2
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0,0,0,0))
    # sombra
    if shadow:
        shadow_layer = Image.new("RGBA", (canvas_size, canvas_size), (0,0,0,0))
        sdraw = ImageDraw.Draw(shadow_layer)
        sdraw.ellipse((padding+4, padding+8, canvas_size-padding+4, canvas_size-padding+8), fill=(31,42,86,60))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(12))
        canvas.paste(shadow_layer, (0,0), shadow_layer)
    # máscara circular da foto (com borda branca extra)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S, S), fill=255)
    foto_r = foto.resize((S, S), Image.LANCZOS)
    # borda branca
    border_ring = Image.new("RGBA", (S+borda*2, S+borda*2), (0,0,0,0))
    ImageDraw.Draw(border_ring).ellipse((0,0,S+borda*2,S+borda*2), fill=borda_cor+(255,))
    ring_mask = Image.new("L", (S+borda*2, S+borda*2), 0)
    ImageDraw.Draw(ring_mask).ellipse((0,0,S+borda*2,S+borda*2), fill=255)
    canvas.paste(border_ring, (padding-borda, padding-borda), ring_mask)
    # foto por cima
    canvas.paste(foto_r, (padding, padding), mask)
    return canvas

def draw_text_centered(img, text, font, y, color=AZUL, x_center=None):
    d = ImageDraw.Draw(img)
    if x_center is None: x_center = img.width // 2
    bbox = d.textbbox((0,0), text, font=font)
    w = bbox[2] - bbox[0]
    d.text((x_center - w//2, y), text, font=font, fill=color)
    return bbox[3] - bbox[1]

def gerar(formato="horizontal"):
    if formato == "horizontal":
        W, H = 1600, 900
        card_gap = 40
        photo_size = 340
        titulo_y = 60
        tag_y = 30
        photos_y = 180
        text_gap_after_photo = 40
    else:  # quadrado
        W, H = 1080, 1080
        card_gap = 24
        photo_size = 200
        titulo_y = 130
        tag_y = 75
        photos_y = 380
        text_gap_after_photo = 30

    bg = gradient_bg_fast(W, H)
    draw = ImageDraw.Draw(bg)

    # ---- topo: tag + título
    font_tag = ImageFont.truetype(F_TAG, 22 if formato == "horizontal" else 18)
    font_titulo = ImageFont.truetype(F_TITLE, 68 if formato == "horizontal" else 50)

    tag_text = "22 DE AGOSTO · CURITIBA"
    bbox = draw.textbbox((0,0), tag_text, font=font_tag)
    tag_w = bbox[2] - bbox[0]
    # letter-spacing manual
    tag_letter_space = 8 if formato == "horizontal" else 6
    ls_w = sum(draw.textbbox((0,0), c, font=font_tag)[2] - draw.textbbox((0,0), c, font=font_tag)[0] for c in tag_text) + tag_letter_space * (len(tag_text)-1)
    x_start = (W - ls_w) // 2
    cur = x_start
    for c in tag_text:
        cw = draw.textbbox((0,0), c, font=font_tag)[2] - draw.textbbox((0,0), c, font=font_tag)[0]
        draw.text((cur, tag_y), c, font=font_tag, fill=MAGENTA)
        cur += cw + tag_letter_space

    # título
    linhas_titulo = ["As especialistas", "do Baby Talks"] if formato == "quadrado" else ["As especialistas do Baby Talks"]
    y_cursor = titulo_y
    for linha in linhas_titulo:
        bbox = draw.textbbox((0,0), linha, font=font_titulo)
        w = bbox[2] - bbox[0]
        draw.text(((W-w)//2, y_cursor), linha, font=font_titulo, fill=AZUL)
        y_cursor += (bbox[3] - bbox[1]) + 6

    # ---- 4 fotos em linha (ou 2x2 no quadrado)
    fotos = [(p, crop_face_square(IMG_DIR / p["img"], p["crop_y_ratio"] if "crop_y_ratio" in p else p["crop_y"], size=520)) for p in PALESTRANTES]

    if formato == "horizontal":
        total_w = 4 * photo_size + 3 * card_gap
        x_start = (W - total_w) // 2
        font_nome = ImageFont.truetype(F_NAME, 24)
        font_role = ImageFont.truetype(F_ROLE, 15)
        for i, (p, foto) in enumerate(fotos):
            x = x_start + i * (photo_size + card_gap)
            emblema = foto_com_moldura(foto, photo_size)
            bg.paste(emblema, (x - 24, photos_y - 24), emblema)
            # nome
            ny = photos_y + photo_size + text_gap_after_photo
            bbox = draw.textbbox((0,0), p["nome"], font=font_nome)
            nw = bbox[2]-bbox[0]
            draw.text((x + photo_size//2 - nw//2, ny), p["nome"], font=font_nome, fill=AZUL)
            # role
            ry = ny + (bbox[3]-bbox[1]) + 8
            bbox = draw.textbbox((0,0), p["role"], font=font_role)
            rw = bbox[2]-bbox[0]
            draw.text((x + photo_size//2 - rw//2, ry), p["role"], font=font_role, fill=(74, 85, 120))
    else:
        # quadrado: 2x2
        cols, rows = 2, 2
        total_w = cols * photo_size + (cols-1) * card_gap
        total_h = rows * (photo_size + 90) + (rows-1) * 30
        x_start_grid = (W - total_w) // 2
        y_start_grid = photos_y
        font_nome = ImageFont.truetype(F_NAME, 22)
        font_role = ImageFont.truetype(F_ROLE, 14)
        for i, (p, foto) in enumerate(fotos):
            col = i % cols
            row = i // cols
            x = x_start_grid + col * (photo_size + card_gap)
            y = y_start_grid + row * (photo_size + 90 + 30)
            emblema = foto_com_moldura(foto, photo_size)
            bg.paste(emblema, (x - 24, y - 24), emblema)
            ny = y + photo_size + 22
            bbox = draw.textbbox((0,0), p["nome"], font=font_nome)
            nw = bbox[2]-bbox[0]
            draw.text((x + photo_size//2 - nw//2, ny), p["nome"], font=font_nome, fill=AZUL)
            ry = ny + (bbox[3]-bbox[1]) + 6
            bbox = draw.textbbox((0,0), p["role"], font=font_role)
            rw = bbox[2]-bbox[0]
            draw.text((x + photo_size//2 - rw//2, ry), p["role"], font=font_role, fill=(74, 85, 120))

    # rodapé - assinatura Baby Talks
    font_rodape = ImageFont.truetype(F_TAG, 14)
    rodape = "babytalks.com.br"
    bbox = draw.textbbox((0,0), rodape, font=font_rodape)
    rw = bbox[2]-bbox[0]
    draw.text(((W-rw)//2, H - 60), rodape, font=font_rodape, fill=LILAS)

    out = OUT_DIR / f"palestrantes-{formato}.jpg"
    bg.save(out, quality=92, optimize=True)
    print(f"OK: {out} ({W}x{H})")
    return out

if __name__ == "__main__":
    gerar("horizontal")
    gerar("quadrado")
