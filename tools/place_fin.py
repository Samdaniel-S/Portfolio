# Finale figure — the owner's own portrait in front of the wordmark.
#
# The source is a studio shot on a white backdrop (assets_src/fin_portrait.png).
# This cuts him out and grades him into the closing scene, so he reads as lit
# BY it rather than pasted on:
#
#   1. matte    the backdrop is whatever near-white touches the border, plus
#               the pockets of it he encloses (the gap between arm and body,
#               holes in the hair); only specks - glints - stay his. The edge
#               band gets a soft alpha from its distance to that white, and
#               its colour is un-mixed from it (no pale halo in the hair).
#   2. grade    the studio's even light pulled down into the scene's: lower
#               exposure, more contrast, a red cast in the shadows
#   3. rim      red light wrapping his silhouette from the glowing wordmark
#               behind him, cream-pink up high where the letters are lit,
#               deep red low down in the fog
#   4. floor    the photo is cut at the thighs, so he is sunk into the black
#               of the lower frame and runs past its edge
#
# Writes public/fin/man.png (2x the frame size, for large displays) and the
# box in public/fin/fin.json. Run AFTER extract_fin.py, which still writes the
# reference model's figure: python tools/place_fin.py

import json
import os

import cv2
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "assets_src", "fin_portrait.png")
OUT = os.path.join(ROOT, "public", "fin")

FRAME = (1600, 900)
HEAD_TOP = 212        # frame y of the top of his hair
HEAD_X = 806          # frame x of the centre of his head
SINK = 14             # frame px he runs past the bottom (parallax never shows the cut)
TEX = 2               # man.png resolution, in multiples of frame px

img = cv2.imread(SRC, cv2.IMREAD_COLOR).astype(np.float32) / 255.0
H, W = img.shape[:2]
WHITE = np.median(np.concatenate([img[:8].reshape(-1, 3), img[:, :8].reshape(-1, 3)]), axis=0)

# ---- 1. matte -------------------------------------------------------------
diff = np.max(np.abs(img - WHITE), axis=2)
near = (diff < 0.07).astype(np.uint8)
n, lab, stats, _c = cv2.connectedComponentsWithStats(near, connectivity=4)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
pockets = {i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= 20}
backdrop = np.isin(lab, list(border | pockets))

solid = (~backdrop).astype(np.uint8)
# seal the figure, then call everything well inside it opaque
solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
inner = cv2.erode(solid, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
soft = np.clip((diff - 0.035) / 0.30, 0, 1)
alpha = np.where(inner > 0, 1.0, np.where(backdrop, 0.0, soft))
alpha = cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), 0.8)
alpha[backdrop & (diff < 0.035)] = 0.0

# un-mix the white out of the edge band: C = a*F + (1-a)*WHITE
a3 = np.maximum(alpha, 0.05)[..., None]
fg = np.clip((img - (1 - a3) * WHITE) / a3, 0, 1)
fg = np.where(alpha[..., None] > 0.98, img, fg)

ys, xs = np.nonzero(alpha > 0.5)
top_px = int(ys.min())
head = alpha[top_px:top_px + int(0.08 * H)] > 0.5
head_cx = float(np.nonzero(head)[1].mean())

# ---- placement ------------------------------------------------------------
s = (FRAME[1] + SINK - HEAD_TOP) / (H - top_px)       # source px -> frame px
box_w, box_h = W * s, H * s
box_x = HEAD_X - head_cx * s
box_y = FRAME[1] + SINK - box_h

tw, th = int(round(box_w * TEX)), int(round(box_h * TEX))
fg = cv2.resize(fg, (tw, th), interpolation=cv2.INTER_AREA)
alpha = cv2.resize(alpha, (tw, th), interpolation=cv2.INTER_AREA)
yy = np.linspace(0, 1, th, dtype=np.float32)[:, None]          # 0 top .. 1 bottom
frame_y = (box_y + yy * box_h) / FRAME[1]                       # frame fraction

# ---- 2. grade -------------------------------------------------------------
# (OpenCV order: every colour below is B, G, R)
lum = fg @ np.float32([0.114, 0.587, 0.299])
c = fg * 0.80                                              # into the scene's exposure
c = c + (c - 0.22) * 0.18                                  # a little more bite
c = c * np.float32([0.82, 0.86, 1.0])                      # red-warm key
shadow = np.clip(1 - lum * 2.2, 0, 1)[..., None]
c = c + shadow * np.float32([0.012, 0.004, 0.05])          # deep red into the blacks

# ---- 3. rim ---------------------------------------------------------------
hard = (alpha > 0.5).astype(np.uint8)
dist = cv2.distanceTransform(hard, cv2.DIST_L2, 5).astype(np.float32)
r = 6.0 * TEX
rim = np.exp(-dist / r) * hard
rim = cv2.GaussianBlur(rim, (0, 0), 1.2 * TEX)
# the light comes from behind: strongest where he is darkest (suit, hair)
rim = rim * (0.35 + 0.65 * np.clip(1 - lum * 1.6, 0, 1))
hi = np.clip(1 - (frame_y - 0.18) / 0.45, 0, 1)            # lit letters up high
rim_col = (hi[..., None] * np.float32([0.62, 0.66, 1.0])       # cream-pink
           + (1 - hi[..., None]) * np.float32([0.10, 0.12, 0.92]))  # deep red
c = c + rim[..., None] * rim_col * 0.85

# ---- 4. floor -------------------------------------------------------------
fall = np.clip((frame_y - 0.70) / 0.30, 0, 1) ** 1.3
c = c * (1 - 0.62 * fall)[..., None]
c = c + (fall * 0.018)[..., None] * np.float32([0.2, 0.2, 1.0])

noise = np.random.default_rng(6).normal(0, 0.008, c.shape).astype(np.float32)
c = np.clip(c + noise, 0, 1)

out = np.dstack([c * 255, alpha * 255]).round().astype(np.uint8)
cv2.imwrite(os.path.join(OUT, "man.png"), out, [cv2.IMWRITE_PNG_COMPRESSION, 9])

box = [round(box_x, 1), round(box_y, 1), round(box_w, 1), round(box_h, 1)]
with open(os.path.join(OUT, "fin.json"), "w") as f:
    json.dump({"man": box, "size": list(FRAME)}, f)
print("man.png %dx%d, box %s, %d KB" % (tw, th, box, os.path.getsize(os.path.join(OUT, "man.png")) // 1024))
