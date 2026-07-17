"""
Cola a Dayane REAL (dayane-v3.png que ficou boa) sobre a composição de grupo,
substituindo por completo a cabeça+ombros dela — não mais face swap, mas composite total.
"""
import cv2
import numpy as np
from pathlib import Path
from insightface.app import FaceAnalysis

BASE = Path("D:/CLAUDE/enxoval-babytalks/composicoes")
GROUP_BASE = BASE / "grupo-v2-2.png"   # a que ficou melhor no geral
DAYANE_SRC = BASE / "dayane-v3.png"    # versão IA da Day que Bruno aprovou
OUT = BASE / "grupo-dayane-composite.png"

app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

# 1) Detectar rosto da Day em cada imagem
group = cv2.imread(str(GROUP_BASE))
day_src = cv2.imread(str(DAYANE_SRC))

group_faces = sorted(app.get(group), key=lambda f: f.bbox[0])
day_face_group = group_faces[0]  # primeira à esquerda = Day
day_faces_src = app.get(day_src)
day_face_src = max(day_faces_src, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))

print(f"Grupo (posição Day): x={int(day_face_group.bbox[0])}, w={int(day_face_group.bbox[2]-day_face_group.bbox[0])}")
print(f"Source Day: x={int(day_face_src.bbox[0])}, w={int(day_face_src.bbox[2]-day_face_src.bbox[0])}")

# 2) Calcular escala/posição pra alinhar
# vamos usar o TAMANHO do rosto pra determinar escala do source
target_face_w = day_face_group.bbox[2] - day_face_group.bbox[0]
src_face_w = day_face_src.bbox[2] - day_face_src.bbox[0]
scale = target_face_w / src_face_w
print(f"scale: {scale:.3f}")

# resize source
new_w = int(day_src.shape[1] * scale)
new_h = int(day_src.shape[0] * scale)
day_scaled = cv2.resize(day_src, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

# calcular novo bbox do rosto após scale
sf_x = day_face_src.bbox[0] * scale
sf_y = day_face_src.bbox[1] * scale
sf_w = day_face_src.bbox[2] * scale - sf_x
sf_h = day_face_src.bbox[3] * scale - sf_y

# offset pra alinhar o CENTRO do rosto do source no CENTRO do rosto do grupo
gf_cx = (day_face_group.bbox[0] + day_face_group.bbox[2]) / 2
gf_cy = (day_face_group.bbox[1] + day_face_group.bbox[3]) / 2
sf_cx = sf_x + sf_w / 2
sf_cy = sf_y + sf_h / 2

# posição de colagem no grupo (canto sup-esq do source)
paste_x = int(gf_cx - sf_cx)
paste_y = int(gf_cy - sf_cy)
print(f"paste em: ({paste_x}, {paste_y})")

# 3) Criar máscara alpha que engloba TUDO da Day (rosto + cabelo + ombro esquerdo)
# a área ocupada pela Day no grupo vai da coluna 0 até ~coluna do início da Patricia
patricia_x = group_faces[1].bbox[0]  # x onde começa Patricia
day_end_x = int(patricia_x - 20)  # margem antes da Patricia
day_end_x = min(day_end_x, group.shape[1])

# máscara: retângulo com feathering nas bordas direita e inferior
H, W = group.shape[:2]
mask = np.zeros((H, W), dtype=np.float32)
mask[:, :day_end_x] = 1.0
# feather na borda direita
feather = 40
for i in range(feather):
    x = day_end_x - feather + i
    if 0 <= x < W:
        mask[:, x] = 1.0 - (i / feather)
# suavizar mais com blur
mask = cv2.GaussianBlur(mask, (0, 0), 8)

# 4) Colar day_scaled sobre canvas do tamanho do grupo com esse offset
day_canvas = np.zeros_like(group)
# calcular região válida
src_x0 = max(0, -paste_x)
src_y0 = max(0, -paste_y)
src_x1 = min(day_scaled.shape[1], W - paste_x)
src_y1 = min(day_scaled.shape[0], H - paste_y)
dst_x0 = max(0, paste_x)
dst_y0 = max(0, paste_y)
dst_x1 = dst_x0 + (src_x1 - src_x0)
dst_y1 = dst_y0 + (src_y1 - src_y0)
day_canvas[dst_y0:dst_y1, dst_x0:dst_x1] = day_scaled[src_y0:src_y1, src_x0:src_x1]

# 5) Blend usando máscara
mask_3ch = np.stack([mask, mask, mask], axis=2)
result = (day_canvas * mask_3ch + group * (1 - mask_3ch)).astype(np.uint8)

cv2.imwrite(str(OUT), result)
print(f"\nOK: {OUT}")
