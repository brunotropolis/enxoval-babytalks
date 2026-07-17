"""
Junta as 4 palestrantes escolhidas numa única composição horizontal.
Como cada IA gerou fundo lavanda ligeiramente diferente, aplica blend nas transições verticais.
"""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

BASE = Path("D:/CLAUDE/enxoval-babytalks/composicoes")

# Escolhidas
FOTOS = [
    ("dayane",   BASE / "dayane-v3.png"),
    ("patricia", BASE / "patricia-v3.png"),
    ("alline",   BASE / "alline-v2.png"),
    ("juliana",  BASE / "juliana-v2.png"),
]

# Canvas final horizontal
W, H = 1920, 1080

# cada foto ocupa 1/4 do canvas
FRAME_W = W // 4  # 480
FRAME_H = H

def crop_center_portrait(img, target_w, target_h):
    """Crop centralizado mantendo aspect ratio do target."""
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h
    if src_ratio > tgt_ratio:
        # source é mais largo — cortar laterais
        new_w = int(src_h * tgt_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        # source é mais alto — cortar topo/base
        new_h = int(src_w / tgt_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    return img.resize((target_w, target_h), Image.LANCZOS)

# monta canvas com fotos lado a lado
canvas = Image.new("RGB", (W, H))
crops = []
for i, (nome, path) in enumerate(FOTOS):
    img = Image.open(path).convert("RGB")
    crop = crop_center_portrait(img, FRAME_W, FRAME_H)
    crops.append(crop)
    canvas.paste(crop, (i * FRAME_W, 0))
    print(f"{nome}: colado em x={i*FRAME_W}")

# ---- BLEND nas transições verticais (dissolve emendas)
BLEND_W = 60  # px de crossfade em cada junção
for i in range(1, 4):
    x_junction = i * FRAME_W
    left_img = crops[i-1]
    right_img = crops[i]
    for x_off in range(-BLEND_W // 2, BLEND_W // 2):
        x = x_junction + x_off
        if x < 0 or x >= W: continue
        # progresso: 0 no meio-esquerdo (só esquerda), 1 no meio-direito (só direita)
        t = (x_off + BLEND_W / 2) / BLEND_W
        # smoothstep pra transição suave
        t = t * t * (3 - 2 * t)
        for y in range(H):
            # pega cor de cada frame
            xl = x - (i-1) * FRAME_W
            xr = x - i * FRAME_W
            if xl < 0: xl = 0
            if xl >= FRAME_W: xl = FRAME_W - 1
            if xr < 0: xr = 0
            if xr >= FRAME_W: xr = FRAME_W - 1
            cl = left_img.getpixel((xl, y))
            cr = right_img.getpixel((xr, y))
            r = int(cl[0] * (1-t) + cr[0] * t)
            g = int(cl[1] * (1-t) + cr[1] * t)
            b = int(cl[2] * (1-t) + cr[2] * t)
            canvas.putpixel((x, y), (r, g, b))
    print(f"blend em x={x_junction} (±{BLEND_W//2}px)")

# ---- levíssimo blur horizontal nas junções (opcional, ajuda a dissolver)
# não aplicar globalmente — vira "mole". Só nas colunas de junção mesmo.

out = BASE / "palestrantes-final.jpg"
canvas.save(out, quality=94, optimize=True)
print(f"\nOK: {out} ({W}x{H})")
