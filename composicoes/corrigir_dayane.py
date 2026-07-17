"""
Pega a composição do grupo v3 (que ficou boa em cenário) e troca APENAS o rosto da Dayane
pelo rosto REAL da foto original dela via face-swap InsightFace.
"""
import cv2
import numpy as np
from pathlib import Path
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

BASE = Path("D:/CLAUDE/enxoval-babytalks/composicoes")
BASE_IMG = BASE / "grupo-organico-v3.png"
REF_DAYANE = Path("D:/CLAUDE/baby-talks-prep/images/dayane.jpg")
OUT = BASE / "grupo-final.png"

print("Iniciando InsightFace...")
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))
print("Carregando inswapper...")
swapper = get_model(str(BASE / "models/inswapper_128.onnx"), providers=["CPUExecutionProvider"])

# 1) Detectar rostos na composição (esquerda→direita)
img_base = cv2.imread(str(BASE_IMG))
faces_base = app.get(img_base)
faces_base = sorted(faces_base, key=lambda f: f.bbox[0])
print(f"\nDetectados {len(faces_base)} rostos na composição:")
for i, f in enumerate(faces_base):
    print(f"  pos {i}: x={int(f.bbox[0])}, y={int(f.bbox[1])}")

# 2) Pegar rosto real da Dayane
ref_img = cv2.imread(str(REF_DAYANE))
ref_faces = app.get(ref_img)
ref_face = max(ref_faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
print(f"\nRosto de referência da Dayane extraído da foto original")

# 3) Swap SOMENTE na pos 0 (Dayane, primeira à esquerda)
resultado = swapper.get(img_base.copy(), faces_base[0], ref_face, paste_back=True)

cv2.imwrite(str(OUT), resultado)
print(f"\nOK: {OUT}")
