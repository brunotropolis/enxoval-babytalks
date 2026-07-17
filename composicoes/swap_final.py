"""
Face-swap das 4 palestrantes na composição grupo-v2-2 (que já tem tom de pele certo),
usando as versões IA aprovadas como source (que preservam identidade real).
"""
import cv2
import numpy as np
from pathlib import Path
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

BASE = Path("D:/CLAUDE/enxoval-babytalks/composicoes")
BASE_IMG = BASE / "grupo-v2-2.png"
OUT = BASE / "grupo-final-swap.png"

# Sources IA aprovadas (esquerda→direita)
SOURCES = [
    ("Dayane",   BASE / "dayane-v3.png"),
    ("Patricia", BASE / "patricia-v3.png"),
    ("Alline",   BASE / "alline-v2.png"),
    ("Juliana",  BASE / "juliana-v2.png"),
]

app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))
swapper = get_model(str(BASE / "models/inswapper_128.onnx"), providers=["CPUExecutionProvider"])

img_base = cv2.imread(str(BASE_IMG))
faces_base = sorted(app.get(img_base), key=lambda f: f.bbox[0])
print(f"Rostos no grupo: {len(faces_base)}")

result = img_base.copy()
for i, (nome, src_path) in enumerate(SOURCES):
    if i >= len(faces_base):
        print(f"skip {nome}: sem rosto pra swapar"); continue
    src_img = cv2.imread(str(src_path))
    src_faces = app.get(src_img)
    src_face = max(src_faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
    result = swapper.get(result, faces_base[i], src_face, paste_back=True)
    print(f"swap {nome} OK")

cv2.imwrite(str(OUT), result)
print(f"\nOK: {OUT}")
