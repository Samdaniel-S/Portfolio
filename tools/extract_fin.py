# Finale extraction — the footer reference itself becomes the layer stack:
#   public/fin/man.png    the smoking man, matted out of the artwork (his
#                         grade, rim and pose are the reference's own pixels)
#   public/fin/plate.jpg  everything else — the giant wordmark, the red fog,
#                         his cigarette smoke — with the man diffusion-filled
#                         away and the baked captions blanked (they return as
#                         live DOM so they can type themselves in)
#   public/fin/fin.json   the man's box, for placement
#
# The man and the plate are cover-fitted with the SAME mapping on the site,
# so at rest the reassembly is pixel-identical to the reference; splitting
# him out is what buys the reveal and the parallax depth.
#
# The plate written here still carries the reference's own wordmark: run
# reletter_fin.py afterwards to set the site owner's name into it. The man
# written here is the reference's model: run place_fin.py afterwards to put
# the owner's own portrait back in his place.

import json
import os

import cv2
import numpy as np

SRC = os.path.join(os.path.dirname(__file__), "..", "Footer image.jpg")
OUT = os.path.join(os.path.dirname(__file__), "..", "public", "fin")
os.makedirs(OUT, exist_ok=True)

img = cv2.imread(SRC)
H, W = img.shape[:2]
assert (W, H) == (1600, 900), f"unexpected reference size {W}x{H}"

BOX = (580, 170, 1030, 900)          # x0, y0, x1, y1

# caption zones that become live DOM (incl. their red rules and dashes)
LABELS = [
    (36, 50, 235, 170),      # IDEAS / DESIGNS / EXPERIENCES / REAL IMPACT
    (36, 330, 235, 495),     # the quote + its dash
    (36, 730, 190, 840),     # A / DESIGNER'S / WORLD
    (1450, 50, 1580, 175),   # SAME / PASSION / A BRIGHTER / TOMORROW
    (1450, 730, 1580, 830),  # DESIGN / BUILD / EXPLORE / REPEAT
]

x0, y0, x1, y1 = BOX
rect = (x0, y0, x1 - x0, y1 - y0)
gc = np.zeros((H, W), np.uint8)
bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(img, gc, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)

# sure-foreground: the parts colour cannot claim — skin, the cigarette — and
# a spine so the suit's core is never argued about
cv2.rectangle(gc, (815, 320), (890, 390), cv2.GC_FGD, -1)     # face
cv2.line(gc, (865, 430), (900, 500), cv2.GC_FGD, 15)          # raised hand
CIGARETTE = ((870, 400), (912, 402))
cv2.line(gc, *CIGARETTE, cv2.GC_FGD, 5)
cv2.line(gc, (780, 480), (780, 870), cv2.GC_FGD, 17)          # spine
cv2.line(gc, (700, 300), (860, 230), cv2.GC_FGD, 9)           # hair mass
# sure-background: the fog and letters inside the box that are not him
cv2.line(gc, (990, 200), (1020, 320), cv2.GC_BGD, 11)
cv2.line(gc, (620, 200), (640, 300), cv2.GC_BGD, 9)
cv2.grabCut(img, gc, rect, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
region = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0)
region = region.astype(np.uint8)

# He is NEUTRAL - black suit, dark hair, skin - while everything behind him
# is red (fog, shadowed strokes) or cream (lit strokes). GrabCut is not
# trusted to know that, so backdrop-coloured pixels are taken back out of its
# region; otherwise slivers of the painted wordmark ride along in his matte
# and show as ghost letters over a re-lettered plate (reletter_fin.py).
#   Only above the wordmark's baseline (BASE): below it there are no letters
# to ghost, and the red-lit flap of his jacket there is the same crimson as
# the fog. A thin rim beside his neutral pixels is spared everywhere - that
# is his red rim light, not the backdrop.
BASE = 772
f = img.astype(np.float32)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
redness = f[..., 2] - np.maximum(f[..., 1], f[..., 0])
cream = (gray > 150) & (f[..., 0] > 0.8 * f[..., 2]) & (f[..., 1] > 0.86 * f[..., 2])
# the half-lit pink of the strokes: skin is warmer (more green over blue)
pale = ((gray > 120) & (f[..., 0] > 0.56 * f[..., 2])
        & (f[..., 1] - f[..., 0] < 0.085 * f[..., 2]))
neutral = ((gray < 90) & (redness < 18)).astype(np.uint8)
rim = cv2.dilate(neutral, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
backdrop = ((redness > 85) | cream | pale) & (rim == 0)
backdrop[BASE:] = False
region[backdrop] = 0
cig = np.zeros((H, W), np.uint8)                 # white, so "cream" above
cv2.line(cig, *CIGARETTE, 255, 7)
region = np.maximum(region, cig & np.where(gc % 2 == 1, 255, 0).astype(np.uint8))

# union with the dark core: the suit against the black lower frame gives
# GrabCut nothing to separate, but shipping black pixels as him is harmless.
# Above BASE, neutral dark only - the shadowed strokes and gaps are dark RED.
core = np.zeros((H, W), np.uint8)
dark = (gray < 78).astype(np.uint8)
dark[:BASE] = neutral[:BASE]
core[y0:y1, x0:x1] = dark[y0:y1, x0:x1] * 255
merged = np.maximum(region, core)

n, lab, stats, _c = cv2.connectedComponentsWithStats(merged, 8)
keep = lab[600, 800]
if keep == 0:
    keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
alpha = np.where(lab == keep, 255, 0).astype(np.uint8)
alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
# seal pinholes inside him (sunglass glints, jacket sheen) and the small
# enclosed holes left where a skin highlight read as backdrop
alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
nh, hl, hs, _hc = cv2.connectedComponentsWithStats(255 - alpha, 4)
for i in range(1, nh):
    hx, hy, hw, hh, area = hs[i]
    if area < 1500 and hx > 0 and hy > 0 and hx + hw < W and hy + hh < H:
        alpha[hl == i] = 255
alpha = cv2.GaussianBlur(alpha, (5, 5), 0)
alpha[:y0, :] = 0
alpha[:, :x0] = 0
alpha[:, x1:] = 0

pa = alpha[y0:, x0:x1]
pc = img[y0:, x0:x1]
# mild pre-sharpen against the cover fit's upscale on large displays
pc = cv2.addWeighted(pc, 1.30, cv2.GaussianBlur(pc, (0, 0), 1.1), -0.30, 0)
cv2.imwrite(os.path.join(OUT, "man.png"), np.dstack([pc, pa]))
print("man alpha px:", int((pa > 128).sum()))

# ---- the plate -------------------------------------------------------------
plate = img.copy()
remove = cv2.dilate(alpha, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
for lx0, ly0, lx1, ly1 in LABELS:
    remove[ly0:ly1, lx0:lx1] = 255
remove = cv2.dilate(remove, np.ones((5, 5), np.uint8))

m = remove.astype(np.float32) / 255.0
out = plate.astype(np.float32)
keepm = (1.0 - m)[..., None]


def nconv(sig):
    wgt = cv2.GaussianBlur(1.0 - m, (0, 0), sig)
    val = cv2.GaussianBlur(out * keepm, (0, 0), sig)
    return val / np.maximum(wgt, 1e-4)[..., None], wgt


coarse, _wc = nconv(75)
fine, wf = nconv(17)
blend = np.clip(wf * 8.0, 0.0, 1.0)[..., None]
diff = fine * blend + coarse * (1.0 - blend)
out = out * keepm + diff * m[..., None]
noise = np.random.default_rng(3).normal(0, 2.0, out.shape).astype(np.float32)
plate = np.clip(out + noise * m[..., None], 0, 255).astype(np.uint8)

cv2.imwrite(os.path.join(OUT, "plate.jpg"), plate,
            [cv2.IMWRITE_JPEG_QUALITY, 90])

with open(os.path.join(OUT, "fin.json"), "w") as f:
    json.dump({"man": [x0, y0, x1 - x0, H - y0], "size": [W, H]}, f)

sizes = {f: os.path.getsize(os.path.join(OUT, f)) // 1024
         for f in sorted(os.listdir(OUT))}
print(json.dumps(sizes, indent=0))
