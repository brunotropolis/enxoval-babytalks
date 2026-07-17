"""
Gera 3 variações da Dayane em cenário Baby Talks unificado.
Prompt cirúrgico com foto de referência única (Nano Banana preserva rosto muito melhor com 1 pessoa).
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

OUT = Path("D:/CLAUDE/enxoval-babytalks/composicoes")
REF = Path("D:/CLAUDE/baby-talks-prep/images/dayane.jpg")

# Prompt cirúrgico — descreve o rosto que precisa ser preservado + o cenário desejado
PROMPT = """Generate a new professional editorial portrait of THE EXACT SAME WOMAN shown in the reference photo. It is CRITICAL that every facial feature is preserved with 100% accuracy: the exact same face shape, the same eyes (color, shape, position, and eyelid crease), the same nose, the same mouth and lip shape, the same smile, the same jawline, the same eyebrow shape, the same skin tone, and the same hairstyle (long wavy dark brown hair with subtle honey highlights, falling past shoulders, natural side part). Same age (early 30s). Do NOT reinterpret or "beautify" — this must look like an actual photograph of THIS specific woman, indistinguishable from a professional shoot on the same day.

New scene (only these elements change):
- Background: soft lavender studio backdrop, smooth gradient from light lilac (#B0BCE5) at top to soft lavender (#E4E6F2) at bottom, clean and minimalist, no props
- Wardrobe: elegant neutral off-white silk blouse with a soft V-neck, delicate and refined, no patterns
- Pose: standing at slight three-quarter angle facing camera, warm confident smile, hands relaxed
- Framing: half-body portrait, centered, small margin on top for headroom
- Lighting: soft diffused natural light from 45 degrees, gentle catchlights in the eyes, no harsh shadows, warm neutral color temperature
- Style: high-end editorial maternity magazine photography, shot on full-frame DSLR with 85mm f/1.8 lens, shallow depth of field with soft bokeh background
- Aspect: portrait 3:4

Output must be photorealistic — NOT illustration, NOT painting, NOT stylized. It should look like a real photograph indistinguishable from the reference."""

client = genai.Client()

with open(REF, "rb") as f:
    ref_bytes = f.read()

for i in range(1, 4):
    print(f"\n[{i}/3] Gerando variação...")
    resp = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            types.Part.from_text(text=PROMPT),
            types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg"),
        ]
    )
    for cand in resp.candidates:
        for part in cand.content.parts:
            if part.inline_data and part.inline_data.data:
                out = OUT / f"dayane-v{i}.png"
                with open(out, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  OK: {out.name} ({len(part.inline_data.data)//1024}KB)")
            elif part.text:
                print(f"  [texto] {part.text[:120]}")
