"""
Regenera composição em grupo — versão v2 do prompt, com descrição explícita de tom de pele
e etnia de cada uma pra o Nano Banana não misturar.
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

PROMPT = """You are given 4 reference portraits of 4 DIFFERENT women with DIFFERENT skin tones and ethnicities. It is CRITICAL that each woman's individual skin tone and features are preserved and NOT mixed or averaged.

From left to right in this specific order:

1. DAYANE — a white Brazilian woman, early 30s. FAIR / LIGHT skin tone (Fitzpatrick type II). Long wavy dark brown hair with subtle honey-caramel balayage highlights. Warm brown eyes. Natural side part. Same warm smile as reference.

2. PATRICIA — a Brazilian woman with warm MEDIUM-TAN / OLIVE skin tone (Fitzpatrick type IV), noticeably darker than Dayane. Long straight jet-black hair, natural center part. Wide bright smile with white teeth. Round face with soft full cheeks. Dark brown eyes.

3. ALLINE — a white Brazilian woman, early 30s. FAIR / LIGHT skin tone with slight rosy undertone (Fitzpatrick type II, same as Dayane). Long wavy blonde balayage hair — brighter blonde on ends, slightly darker natural blonde at roots. Light hazel-brown eyes. Bright wide smile.

4. JULIANA — a white Brazilian woman, early 40s (visibly the most mature of the four — keep her age lines around the eyes). FAIR / LIGHT-MEDIUM skin tone (Fitzpatrick type II-III). Long dark brown wavy hair, natural center part. Warm brown eyes. Dangling pearl drop earrings (important, always visible).

IDENTITY PRESERVATION IS CRITICAL:
- Preserve EVERY facial feature of each woman with 100% accuracy from her reference photo.
- Skin tone must match the description above — DO NOT make Dayane, Alline or Juliana look darker than they are. DO NOT lighten Patricia.
- Each face must be immediately recognizable as the exact same person from her reference.

Group composition (natural, organic):
- All 4 standing close together as a group, from LEFT TO RIGHT: Dayane, Patricia, Alline, Juliana.
- Shoulders slightly overlapping with natural varied depth — Patricia slightly forward, others slightly back is fine.
- Heads at coherent heights matching realistic proportions.
- All looking at the camera with warm confident smiles.

Scene (unified):
- Single continuous soft lavender studio backdrop, smooth gradient from light lilac (#B0BCE5) at top to soft lavender (#E4E6F2) at bottom. One coherent background, no visible seams.
- All 4 lit by the SAME single key light from 45 degrees left, soft diffused, matching shadow direction on all 4 faces.
- All 4 wearing elegant off-white silk V-neck blouses (subtle variation in cut is fine).

Framing:
- Half-body group portrait, all 4 fully visible from waist up.
- Square aspect ratio (1:1), centered composition.
- High-end editorial maternity magazine style, shot on full-frame DSLR with 50mm f/2 lens, subtle background bokeh, sharp focus on all 4 faces.

Output must be photorealistic — indistinguishable from a real group photograph. NOT illustration, NOT painting, NOT collage. No visible cuts or seams — they must appear organically together in the same physical space."""

client = genai.Client()
parts = [types.Part.from_text(text=PROMPT)]
for nome, p in REFS:
    with open(p, "rb") as f:
        data = f.read()
    parts.append(types.Part.from_bytes(data=data, mime_type="image/png"))
    print(f"anexou: {nome}")

for i in range(1, 4):
    print(f"\n[{i}/3] Gerando...")
    resp = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=parts,
    )
    for cand in resp.candidates:
        for part in cand.content.parts:
            if part.inline_data and part.inline_data.data:
                out = BASE / f"grupo-v2-{i}.png"
                with open(out, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  OK: {out.name}")
            elif part.text:
                print(f"  [texto] {part.text[:120]}")
