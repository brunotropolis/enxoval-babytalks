"""
Gera composição IA das 4 palestrantes usando Gemini 2.5 Flash Image (Nano Banana).
Passa as 4 fotos como referência + prompt descrevendo cenário unificado + paleta Baby Talks.
"""
import os, sys, base64
from pathlib import Path
from google import genai
from google.genai import types

# ---- config
def envload(k):
    with open("D:/CLAUDE/.env.meta", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith(k + "="):
                return line.strip().split("=", 1)[1].strip('"')

os.environ["GEMINI_API_KEY"] = envload("GEMINI_API_KEY")

IMG_DIR = Path("D:/CLAUDE/baby-talks-prep/images")
OUT_DIR = Path("D:/CLAUDE/enxoval-babytalks/composicoes")

palestrantes = [
    ("Dayane Dos Anjos",   "dayane.jpg"),
    ("Patricia Moreira",   "palestrante-patricia.jpg"),
    ("Alline Vieira",      "palestrante-alline.jpg"),
    ("Dra. Juliana Chalupe", "palestrante-juliana.jpg"),
]

prompt = """Crie uma imagem realista, editorial e elegante mostrando as 4 mulheres retratadas nas fotos de referência, juntas lado a lado no mesmo cenário. É essencial preservar 100% os rostos originais, os traços, as feições, o tom de pele e o cabelo de cada uma exatamente como aparecem nas fotos que passei — sem mudar nenhuma característica facial. Elas devem estar da esquerda para a direita nesta ordem:
1. Dayane Dos Anjos (cabelo castanho ondulado, sorriso suave)
2. Patricia Moreira (cabelo castanho escuro liso, sorriso amplo)
3. Alline Vieira (cabelo loiro liso e longo)
4. Dra. Juliana Chalupe (cabelo castanho escuro liso, brincos de pérola)

Cenário: um estúdio fotográfico profissional com fundo em degradê suave de lilás claro (#B0BCE5) para lavanda (#E4E6F2), iluminação natural difusa e limpa (chave de luz suave em 45°), estilo editorial de revista de maternidade.

Roupas: todas com camisas ou blusas neutras, elegantes e discretas, em tons off-white, bege claro e lilás muito suave — sem estampas fortes, sem cores saturadas. Roupas devem combinar entre si, transmitindo um grupo coeso de especialistas.

Composição: retrato de meio corpo, todas em pé, alinhadas, cada uma olhando para a câmera com expressão gentil e profissional. Distância confortável entre elas, com sobreposição sutil de ombros para mostrar união. Enquadramento horizontal 16:9.

Estilo: fotografia realista de alta qualidade, DSLR full frame, lente 85mm, profundidade de campo rasa com fundo suavemente desfocado. Tom quente, elegante, luxo maternal. NÃO parecer ilustração, pintura ou 3D — deve ser indistinguível de uma foto real de estúdio."""

client = genai.Client()

# monta contents com as 4 imagens + prompt
parts = [types.Part.from_text(text=prompt)]
for nome, arq in palestrantes:
    p = IMG_DIR / arq
    with open(p, "rb") as f:
        data = f.read()
    parts.append(types.Part.from_bytes(data=data, mime_type="image/jpeg"))
    print(f"anexou: {arq} ({len(data)//1024}KB)")

print("\nGerando via Gemini 2.5 Flash Image (Nano Banana)...")
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=parts,
)

# extrai a imagem gerada
found = False
for i, cand in enumerate(response.candidates):
    for j, part in enumerate(cand.content.parts):
        if part.inline_data and part.inline_data.data:
            out = OUT_DIR / f"palestrantes-ia-gemini.png"
            with open(out, "wb") as f:
                f.write(part.inline_data.data)
            print(f"OK: {out} ({len(part.inline_data.data)//1024}KB)")
            found = True
        elif part.text:
            print(f"[texto] {part.text[:200]}")

if not found:
    print("ERRO: nenhuma imagem retornada")
    print("response:", response)
    sys.exit(1)
