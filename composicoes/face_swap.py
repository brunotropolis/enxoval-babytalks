"""
Face-swap sobre a composição IA do Gemini.
Pega os 4 rostos gerados pela IA (bonitos mas inventados) e substitui pelos rostos REAIS das palestrantes.
"""
import cv2
import numpy as np
from pathlib import Path
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

BASE = Path("D:/CLAUDE/enxoval-babytalks/composicoes")
IMG_DIR = Path("D:/CLAUDE/baby-talks-prep/images")

# ordem esquerda→direita como o Gemini gerou
PALESTRANTES = [
    "dayane.jpg",              # pos 0 (esquerda)
    "palestrante-patricia.jpg", # pos 1
    "palestrante-alline.jpg",   # pos 2
    "palestrante-juliana.jpg",  # pos 3 (direita)
]

BASE_IA = BASE / "palestrantes-ia-gemini.png"
OUT = BASE / "palestrantes-ia-facereal.png"

print("Iniciando InsightFace...")
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

print("Carregando inswapper...")
swapper = get_model(str(BASE / "models/inswapper_128.onnx"), providers=["CPUExecutionProvider"])

# Detectar rostos na imagem base IA
print(f"\nDetectando rostos em {BASE_IA.name}...")
img_base = cv2.imread(str(BASE_IA))
faces_base = app.get(img_base)
print(f"  detectados: {len(faces_base)} rostos")
# ordenar por x (esquerda pra direita)
faces_base = sorted(faces_base, key=lambda f: f.bbox[0])
for i, f in enumerate(faces_base):
    print(f"  face {i}: x={int(f.bbox[0])}, y={int(f.bbox[1])}, sexo={f.sex}, idade={f.age}")

if len(faces_base) != 4:
    print(f"AVISO: esperava 4 rostos, achou {len(faces_base)}. Continuando com o que tem...")

# Pra cada palestrante, extrair rosto de referência e fazer swap
resultado = img_base.copy()
for pos, arq in enumerate(PALESTRANTES):
    if pos >= len(faces_base):
        print(f"[skip] pos {pos} ({arq}): sem rosto base pra swapar")
        continue
    ref_path = IMG_DIR / arq
    ref_img = cv2.imread(str(ref_path))
    if ref_img is None:
        print(f"[erro] não abriu {ref_path}"); continue
    ref_faces = app.get(ref_img)
    if not ref_faces:
        print(f"[erro] nenhum rosto detectado em {arq}"); continue
    # pega o maior rosto
    ref_face = max(ref_faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
    print(f"pos {pos} ({arq}): swap com rosto real...")
    resultado = swapper.get(resultado, faces_base[pos], ref_face, paste_back=True)

cv2.imwrite(str(OUT), resultado)
print(f"\nOK: {OUT}")
