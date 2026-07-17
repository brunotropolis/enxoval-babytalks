"""
Gera composição em grupo natural das 4 palestrantes usando as 4 fotos IA já aprovadas como referência.
Passa cada uma numerada + prompt pedindo grupo orgânico no mesmo ambiente.
"""
import os
from pathlib import Path
from google import genai
from google.genai import types

def envload(k):
    with open("D:/CLAUDE/.env.meta", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith(k+"="):
                return line.strip().split("=",1)[1].strip('"')

os.environ["GEMINI_API_KEY"] = envload("GEMINI_API_KEY")
BASE = Path("D:/CLAUDE/enxoval-babytalks/composicoes")

REFS = [
    ("Dayane",   BASE / "dayane-v3.png"),
    ("Patricia", BASE / "patricia-v3.png"),
    ("Alline",   BASE / "alline-v2.png"),
    ("Juliana",  BASE / "juliana-v2.png"),
]

PROMPT = """You are given 4 reference portraits of 4 different women, in this order:
1. Dayane (long wavy dark brown hair with honey highlights)
2. Patricia (long straight dark black hair, warm olive skin, round face)
3. Alline (long wavy blonde hair with balayage, fair rosy skin)
4. Juliana (long dark brown wavy hair, dangling pearl earrings, mature woman early 40s)

Create ONE single photorealistic editorial group portrait showing all 4 women TOGETHER in the SAME physical environment, sharing the SAME lighting, at the SAME time — as if it were an actual photograph taken during one photo shoot.

IDENTITY PRESERVATION (critical):
- Preserve EVERY facial feature of each woman with 100% accuracy from her reference photo: face shape, eyes, nose, mouth, jawline, skin tone, hairstyle, expression lines.
- Do NOT reinterpret or "beautify" any of them. Each face must be immediately recognizable as the exact same person from her reference.
- Juliana must keep her mature early-40s look and her dangling pearl earrings.

Group composition (natural, organic):
- All 4 standing close together as a group, from left to right in this order: Dayane, Patricia, Alline, Juliana.
- Shoulders slightly overlapping, natural varied depth (one slightly forward, others slightly back — NOT rigidly lined up like a police lineup).
- Heads at coherent heights matching their real proportions (they can be at slightly different depths so head heights vary naturally).
- All looking at the camera with warm confident smiles.
- Natural body language — arms relaxed at sides or one hand crossing, no awkward mannequin pose.

Scene (unified):
- Single continuous soft lavender studio backdrop, smooth gradient from light lilac (#B0BCE5) at top to soft lavender (#E4E6F2) at bottom. No visible seams, no vertical stripes. One coherent background.
- All 4 lit by the SAME single key light coming from 45 degrees left, soft diffused, gentle catchlights in all 8 eyes, matching shadow direction on all 4 faces.
- All 4 wearing the same style: elegant off-white silk V-neck blouses (subtle variation in cut is fine but same tone and fabric).

Framing:
- Half-body group portrait, all 4 fully visible from waist up.
- Landscape aspect ratio (roughly 16:9), centered composition with balanced negative space.
- High-end editorial maternity magazine style, shot on full-frame DSLR with 50mm f/2 lens, subtle background bokeh, sharp focus on all 4 faces.

Output must be photorealistic — indistinguishable from a real group photograph. NOT illustration, NOT painting, NOT collage. Do NOT show visible cuts, seams, or edges between the women — they must appear organically in the same physical space together."""

client = genai.Client()

parts = [types.Part.from_text(text=PROMPT)]
for nome, p in REFS:
    with open(p, "rb") as f:
        data = f.read()
    parts.append(types.Part.from_bytes(data=data, mime_type="image/png"))
    print(f"anexou: {nome} ({len(data)//1024}KB)")

for i in range(1, 4):
    print(f"\n[{i}/3] Gerando...")
    resp = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=parts,
    )
    for cand in resp.candidates:
        for part in cand.content.parts:
            if part.inline_data and part.inline_data.data:
                out = BASE / f"grupo-organico-v{i}.png"
                with open(out, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  OK: {out.name} ({len(part.inline_data.data)//1024}KB)")
            elif part.text:
                print(f"  [texto] {part.text[:120]}")
