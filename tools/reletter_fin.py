# Finale re-lettering — sets the giant wordmark of the closing shot to WORD.
#
# The footer reference (`Footer image.jpg`) has its wordmark painted into the
# artwork, so the plate extract_fin.py cuts from it carries that word. This
# rebuilds public/fin/plate.jpg with WORD instead, lit and textured from the
# reference's own pixels rather than a stock texture:
#
#   1. reading      in the red channel every painted stroke is brighter than
#                   the gaps and counters beside it, down to where it melts
#                   into the fog. Local contrast over a window wider than any
#                   letter (so it always holds a gap) sorts the word box into
#                   confident STROKE and confident FOG pixels; the uncertain
#                   rim between them is used for neither.
#   2. fog          the whole old word box, the man (public/fin/man.png) and
#                   the baked captions are replaced by a two-scale normalised
#                   convolution of the fog pixels (as in extract_fin.py) -
#                   nothing of the old word is kept, so none of it can ghost
#   3. light        the strokes' colour as a smooth field: cream at the cap
#                   line, crimson into the fog, brightest where the furnace
#                   behind the man is, carried across the box and behind him
#   4. surface      a crackle tile cut from clean stroke interiors (their
#                   ratio to the light field), mirror-tiled over the new word
#   5. new word     WORD in Anton (the hero's face), compressed to fit NEW_X
#                   with the old cap line and baseline; nine letters at the
#                   reference's compression would run under the captions, so
#                   the strokes are a little lighter instead
#
# The letters run behind the man as well, so the parallax between plate and
# man reveals lettering rather than a smear. The cigarette smoke that crossed
# the old letters goes with them; the finale shader's live fog drifts there.
# man.png and fin.json are left as extract_fin.py made them, so run this
# AFTER extract_fin.py (which writes a plate with the old word).
#
# Needs fontTools + brotli (pip install fonttools brotli) to read the woff2.

import io
import json
import os
import sys

import cv2
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

WORD = "SAMDANIEL"

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "Footer image.jpg")
FIN = os.path.join(ROOT, "public", "fin")
FONT = os.path.join(ROOT, "public", "fonts", "anton-400.woff2")

REF_BOX = (309, 45, 1293, 772)      # old word: ink x0, cap top, ink x1, baseline
NEW_X = (230, 1370)                 # ink extent for WORD (cap/baseline kept)

# caption zones that are live DOM (same boxes as extract_fin.py)
LABELS = [
    (36, 50, 235, 170),
    (36, 330, 235, 495),
    (36, 730, 190, 840),
    (1450, 50, 1580, 175),
    (1450, 730, 1580, 830),
]
# clean stroke interiors the crackle tile is cut from (I and both H stems)
TILE_COLS = [(482, 528), (1150, 1200), (1234, 1284)]
TILE_ROWS = (70, 700)


def anton(size):
    f = TTFont(FONT)
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


def render_word(text, x0, x1, top, base, shape, size=1000):
    """Anti-aliased coverage of `text` with its ink running x0..x1 and its
    flat caps from `top` to `base` (round overshoots land just outside)."""
    font = anton(size)
    cap = -font.getbbox("H", anchor="ls")[1]
    track = -0.012 * cap              # the hero's setting (src/scene/type.js)
    m = int(size * 0.2)
    pens, pen = [], 0.0
    for ch in text:
        pens.append(pen)
        pen += font.getlength(ch) + track
    img = Image.new("L", (int(pen) + 2 * m, int(cap) + 2 * m), 0)
    d = ImageDraw.Draw(img)
    for ch, p in zip(text, pens):
        d.text((m + p, m + cap), ch, font=font, fill=255, anchor="ls")
    a = np.asarray(img, np.float32) / 255.0
    cols = np.flatnonzero(a.max(0) > 0.5)
    ink0, ink1 = cols[0], cols[-1] + 1
    sx = (x1 - x0) / float(ink1 - ink0)
    sy = (base - top) / float(cap)
    M = np.float32([[sx, 0, x0 - ink0 * sx], [0, sy, top - m * sy]])
    return cv2.warpAffine(a, M, (shape[1], shape[0]), flags=cv2.INTER_AREA)


def nconv(img, keep, sx, sy):
    w = cv2.GaussianBlur(keep, (0, 0), sigmaX=sx, sigmaY=sy)
    v = cv2.GaussianBlur(img * keep[..., None], (0, 0), sigmaX=sx, sigmaY=sy)
    return v / np.maximum(w, 1e-5)[..., None], w


def row_profile(img, keep, sigma=8.0):
    """Per-row mean of the kept pixels, smoothed down the rows and carried
    to rows with none - the colour a stroke has at each height."""
    w = keep.sum(1)
    v = (img * keep[..., None]).sum(1)
    w = cv2.GaussianBlur(w[:, None].astype(np.float32), (1, 0), sigmaX=0.1, sigmaY=sigma)[:, 0]
    v = cv2.GaussianBlur(v[:, None, :].astype(np.float32), (1, 0), sigmaX=0.1, sigmaY=sigma)[:, 0]
    has = w > 1e-3
    rows = np.arange(len(w))
    prof = np.stack([np.interp(rows, rows[has], v[has, k] / w[has])
                     for k in range(img.shape[2])], 1)
    return np.broadcast_to(prof[:, None, :], img.shape).astype(np.float32)


def two_scale(img, keep, fine, coarse, gain=8.0, floor=None):
    c, wc = nconv(img, keep, *coarse)
    if floor is not None:
        # a third, widest layer under the coarse one: deep inside a big hole
        # the coarse weights underflow and the fill would go black (or, for
        # the strokes, drag the cream of the cap line down the letters)
        b = row_profile(img, keep) if floor == "rows" else nconv(img, keep, floor, floor)[0]
        tc = np.clip(wc * gain * 4, 0.0, 1.0)[..., None]
        c = c * tc + b * (1.0 - tc)
    f, wf = nconv(img, keep, *fine)
    t = np.clip(wf * gain, 0.0, 1.0)[..., None]
    return f * t + c * (1.0 - t)


def main(debug=None):
    img = cv2.imread(SRC)
    H, W = img.shape[:2]
    assert (W, H) == (1600, 900), f"unexpected reference size {W}x{H}"
    f = img.astype(np.float32)

    meta = json.load(open(os.path.join(FIN, "fin.json")))
    mx, my = meta["man"][:2]
    man_png = cv2.imread(os.path.join(FIN, "man.png"), cv2.IMREAD_UNCHANGED)
    man = np.zeros((H, W), np.uint8)
    man[my:my + man_png.shape[0], mx:mx + man_png.shape[1]] = man_png[..., 3] > 25
    man = cv2.dilate(man, np.ones((13, 13), np.uint8))

    labels = np.zeros((H, W), np.uint8)
    for x0, y0, x1, y1 in LABELS:
        labels[y0:y1, x0:x1] = 1
    labels = cv2.dilate(labels, np.ones((5, 5), np.uint8))

    # ---- 1. reading the old word ------------------------------------------
    x0, y0, x1, y1 = REF_BOX
    box = np.zeros((H, W), np.uint8)
    box[y0 - 6:y1 + 12, x0 - 10:x1 + 10] = 1
    red = cv2.GaussianBlur(f[..., 2], (0, 0), 1.0)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (161, 41))
    lo, hi = cv2.erode(red, k), cv2.dilate(red, k)
    span = hi - lo
    rel = (red - lo) / np.maximum(span, 1.0)
    clear = box & (1 - man)
    stroke = (clear & (rel > 0.62) & (span > 30)).astype(np.uint8)
    stroke = cv2.erode(stroke, np.ones((7, 7), np.uint8))
    fogpx = (clear & ((rel < 0.2) | (span <= 30))).astype(np.uint8)
    fogpx = cv2.erode(fogpx, np.ones((3, 3), np.uint8))

    # ---- 2. fog -----------------------------------------------------------
    remove = np.maximum(np.maximum(box, man), labels)
    # the smoke glow above the word stays out of the fill: the gaps between
    # the old strokes, not the haze over them, say what lies behind the word
    above = np.zeros((H, W), np.uint8)
    above[:y0 - 6, x0 - 60:x1 + 60] = 1
    keep = (((1 - remove) & (1 - above)) | fogpx).astype(np.float32)
    fill = two_scale(f, keep, (13, 13), (60, 60), floor=200)
    fog = f * (1 - remove)[..., None] + fill * remove[..., None]
    soft = cv2.GaussianBlur(remove.astype(np.float32), (0, 0), 3)
    # the haze above the word thins into the box over a few dozen rows
    # rather than stopping at its top edge
    ramp = np.clip((np.arange(H, dtype=np.float32) - (y0 - 46)) / 40.0, 0, 1)
    band = np.zeros((H, W), np.float32)
    band[:, x0 - 10:x1 + 10] = ramp[:, None]
    band = cv2.GaussianBlur(band, (0, 0), 6)
    soft = np.maximum(soft, band * (np.arange(H)[:, None] < y0))[..., None]
    fog = f * (1 - soft) + fill * soft
    fog = np.where(remove[..., None] > 0, fill, fog)

    # ---- 3. light ---------------------------------------------------------
    light = two_scale(f, stroke.astype(np.float32), (34, 12), (220, 16), gain=3.0,
                      floor="rows")

    # ---- 4. surface -------------------------------------------------------
    lum = f @ np.float32([0.114, 0.587, 0.299])
    llum = light @ np.float32([0.114, 0.587, 0.299])
    ratio = (lum + 6.0) / (llum + 6.0)
    ratio = ratio / np.maximum(cv2.GaussianBlur(ratio, (0, 0), 9), 1e-3)
    ty0, ty1 = TILE_ROWS
    tile = np.hstack([ratio[ty0:ty1, a:b] for a, b in TILE_COLS])
    # strip anything constant down a column (stem highlights) or along a
    # row: tiled, those would repeat as regular stripes
    tile = tile / tile.mean(0, keepdims=True)
    tile = tile / tile.mean(1, keepdims=True)
    tile = np.clip(tile, 0.85, 1.15)
    reps = (H // tile.shape[0] + 2, W // tile.shape[1] + 2)
    mirrored = np.vstack([np.hstack([tile, tile[:, ::-1]]),
                          np.hstack([tile[::-1], tile[::-1, ::-1]])])
    crackle = np.tile(mirrored, (reps[0] // 2 + 1, reps[1] // 2 + 1))[:H, :W]
    surface = light * crackle[..., None]

    # ---- 5. new word ------------------------------------------------------
    new = render_word(WORD, NEW_X[0], NEW_X[1], y0, y1, (H, W))
    a = new[..., None]
    plate = fog * (1.0 - a) + surface * a

    rng = np.random.default_rng(3)
    touched = np.maximum(soft[..., 0], new)[..., None]
    plate = plate + rng.normal(0, 2.0, plate.shape).astype(np.float32) * touched
    plate = np.clip(plate, 0, 255).astype(np.uint8)

    cv2.imwrite(os.path.join(FIN, "plate.jpg"), plate, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print("plate.jpg: %s (%d KB)" % (WORD, os.path.getsize(os.path.join(FIN, "plate.jpg")) // 1024))

    if debug:
        os.makedirs(debug, exist_ok=True)
        cv2.imwrite(os.path.join(debug, "reading.png"),
                    np.dstack([fogpx * 255, stroke * 255, (new > 0.5) * 120]).astype(np.uint8))
        cv2.imwrite(os.path.join(debug, "fog.jpg"), np.clip(fog, 0, 255).astype(np.uint8))
        cv2.imwrite(os.path.join(debug, "surface.jpg"), np.clip(surface, 0, 255).astype(np.uint8))
        man_rgb = man_png[..., :3].astype(np.float32)
        man_a = man_png[..., 3:].astype(np.float32) / 255.0
        comp = plate.astype(np.float32)
        roi = comp[my:my + man_png.shape[0], mx:mx + man_png.shape[1]]
        comp[my:my + man_png.shape[0], mx:mx + man_png.shape[1]] = roi * (1 - man_a) + man_rgb * man_a
        cv2.imwrite(os.path.join(debug, "composite.jpg"), comp.astype(np.uint8))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
