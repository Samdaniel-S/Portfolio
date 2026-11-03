# Project re-skin — puts the owner's projects on the twelve screens of the
# project universe (scene 4).
#
# The sprites extract_s4.py cuts from the reference carry that artwork's own
# mock websites. This keeps everything about each sprite that belongs to the
# ROOM - its outline, curvature, rim glow, occlusion trims - and replaces only
# what is on the glass:
#
#   1. face     each project is drawn flat, in the reference's screen grammar
#               (red-dot mark and tiny nav, a serif title over a small line,
#               an outlined EXPLORE pill, art bleeding in from the right).
#               The art is the manifest's `image` when set, otherwise a
#               placeholder motif for the project's category, lit in the
#               scene's crimson/amber
#   2. warp     the face is projected into the screen's measured outline
#               (public/projects/layout4.json) by homography; curved screens
#               (5- and 6-point outlines) are two planes split at their bend
#   3. glass    it replaces the old face only inside the outline, inset past
#               the bezel and feathered, so the reference's rim light and
#               trims survive untouched
#
# Sprites are written at SCALE x the reference's pixel size (the deck sizes
# them by CSS, so this only buys sharper titles on large screens).
#
# Content:   public/projects/work.json   (titles, categories, years, images)
# Originals: assets_src/projects_ref/     (copied there on the first run, so
#                                          every run starts from clean faces)
# Run:       python tools/reskin_s4.py
#
# Needs fontTools + brotli (pip install fonttools brotli) to read the woff2s.

import io
import json
import math
import os
import shutil

import cv2
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROJ = os.path.join(ROOT, "public", "projects")
REF = os.path.join(ROOT, "assets_src", "projects_ref")
FONTS = os.path.join(ROOT, "public", "fonts")

SCALE = 2
BRAND = "ICHTHUS"
SIGN = "SAMDANIEL · ICHTHUS CREATIVE"

# the scene's light, per category: (glow, core) as RGB
ACCENTS = {
    "Branding": ((255, 52, 46), (255, 214, 196)),
    "Print": ((255, 150, 64), (255, 226, 190)),
    "Packaging": ((255, 104, 52), (255, 220, 190)),
    "Motion": ((255, 40, 72), (255, 206, 210)),
    "Typography": ((255, 120, 80), (246, 232, 214)),
    "Illustration": ((255, 128, 56), (255, 222, 184)),
    "Social Media": ((255, 56, 96), (255, 210, 220)),
    "Web": ((255, 84, 44), (255, 218, 200)),
    "AI": ((255, 60, 52), (255, 214, 200)),
    "Automation": ((255, 120, 60), (255, 224, 196)),
    "3D": ((255, 72, 64), (255, 212, 206)),
}
CREAM = (241, 232, 222)
DIM = (150, 141, 132)

_fonts = {}


def font(name, px):
    key = (name, px)
    if key not in _fonts:
        if name not in _fonts:
            f = TTFont(os.path.join(FONTS, name + ".woff2"))
            f.flavor = None
            buf = io.BytesIO()
            f.save(buf)
            _fonts[name] = buf.getvalue()
        _fonts[key] = ImageFont.truetype(io.BytesIO(_fonts[name]), max(6, int(px)))
    return _fonts[key]


def tracked(d, xy, text, fnt, fill, track=0.0, anchor="ls"):
    """Letter-spaced text; returns the end x."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill, anchor=anchor)
        x += fnt.getlength(ch) + track
    return x


def tracked_len(text, fnt, track):
    return sum(fnt.getlength(c) + track for c in text) - track


# ---------------------------------------------------------------------------
# placeholder art — one motif per category, drawn as light: a soft bloom
# under a crisp stroke, in that category's accent
# ---------------------------------------------------------------------------

def _motif(category, w, h, rng):
    """Line-art for the art region, white on black (L mode), w x h."""
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    s = min(w, h)
    cx, cy = w * 0.6, h * 0.52
    lw = max(2, int(s * 0.012))

    if category == "Branding":
        # the ichthys: two arcs, crossing into the tail
        pts_u, pts_l = [], []
        for i in range(121):
            x = -1.22 + 2.32 * i / 120
            y = -0.5 * (1 - ((x - 0.1) / 1.0) ** 2)
            pts_u.append((cx + x * s * 0.32, cy + y * s * 0.32))
            pts_l.append((cx + x * s * 0.32, cy - y * s * 0.32))
        d.line(pts_u, fill=255, width=lw * 2, joint="curve")
        d.line(pts_l, fill=255, width=lw * 2, joint="curve")
        r = s * 0.42
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=90, width=max(1, lw // 2))
    elif category == "Print":
        for k, (dx, dy, ang) in enumerate([(-0.2, 0.06, -8), (0.0, 0.0, 3), (0.2, -0.04, 11)]):
            pw, ph = s * 0.34, s * 0.48
            poster = Image.new("L", (int(pw), int(ph)), 0)
            pd = ImageDraw.Draw(poster)
            pd.rectangle((0, 0, pw - 1, ph - 1), outline=230, width=lw)
            pd.rectangle((pw * 0.12, ph * 0.1, pw * 0.88, ph * 0.46), fill=60 + 40 * k)
            for j in range(4):
                yy = ph * (0.58 + j * 0.08)
                pd.line((pw * 0.12, yy, pw * (0.88 - 0.14 * (j % 2)), yy), fill=200, width=max(1, lw // 2))
            poster = poster.rotate(ang, expand=True, resample=Image.BICUBIC)
            m.paste(poster, (int(cx + dx * s - poster.width / 2), int(cy + dy * s - poster.height / 2)), poster)
    elif category == "Packaging":
        base = cy + s * 0.3
        for k, (dx, bw, bh) in enumerate([(-0.24, 0.16, 0.42), (0.0, 0.2, 0.56), (0.24, 0.16, 0.36)]):
            x0, x1 = cx + (dx - bw / 2) * s, cx + (dx + bw / 2) * s
            y0 = base - bh * s
            d.rounded_rectangle((x0, y0, x1, base), radius=s * 0.03, outline=235, width=lw)
            d.rectangle((x0 + lw, y0 + (base - y0) * 0.38, x1 - lw, y0 + (base - y0) * 0.62), fill=70 + 30 * k)
            d.line((x0 + (x1 - x0) * 0.2, y0 + lw * 2, x0 + (x1 - x0) * 0.2, base - lw * 2), fill=150, width=max(1, lw // 2))
        d.line((cx - s * 0.45, base, cx + s * 0.45, base), fill=120, width=max(1, lw // 2))
    elif category == "Motion":
        r = s * 0.3
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=235, width=lw)
        t = r * 0.42
        d.polygon([(cx - t * 0.6, cy - t), (cx - t * 0.6, cy + t), (cx + t, cy)], fill=235)
        for k in range(3):
            rr = r * (1.25 + 0.18 * k)
            d.arc((cx - rr, cy - rr, cx + rr, cy + rr), 200 + 12 * k, 300 - 10 * k, fill=170 - 40 * k, width=max(1, lw // 2))
    elif category == "Typography":
        fnt = font("bodonimoda-400", s * 0.7)
        d.text((cx + s * 0.04, cy + s * 0.02), "Aa", font=fnt, fill=235, anchor="mm")
        d.line((cx - s * 0.36, cy + s * 0.22, cx + s * 0.44, cy + s * 0.22), fill=110, width=max(1, lw // 2))
    elif category == "Illustration":
        r = s * 0.17
        d.ellipse((cx + s * 0.08 - r, cy - s * 0.18 - r, cx + s * 0.08 + r, cy - s * 0.18 + r), outline=235, width=lw)
        for k, amp in enumerate([0.1, 0.07]):
            pts = [(cx - s * 0.55 + i * s * 1.1 / 60,
                    cy + s * (0.18 + 0.1 * k) - amp * s * math.sin(i / 60 * math.pi * (1.4 + k * 0.6) + k))
                   for i in range(61)]
            d.line(pts, fill=235 - 70 * k, width=lw, joint="curve")
    elif category == "Social Media":
        pw, ph = s * 0.36, s * 0.66
        x0, y0 = cx - pw / 2, cy - ph / 2
        d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=s * 0.05, outline=235, width=lw)
        g = pw * 0.8 / 3
        for i in range(3):
            for j in range(3):
                gx, gy = x0 + pw * 0.1 + i * g, y0 + ph * 0.22 + j * g
                d.rectangle((gx + 2, gy + 2, gx + g - 2, gy + g - 2), fill=int(rng.uniform(50, 170)))
    elif category == "AI":
        # a small network: three layers of nodes, every pair of neighbours linked
        layers = [3, 4, 3]
        pts = [[(cx + (k - 1) * s * 0.34, cy + (j - (n - 1) / 2) * s * 0.2) for j in range(n)]
               for k, n in enumerate(layers)]
        for a, b in zip(pts, pts[1:]):
            for p in a:
                for q in b:
                    d.line((p, q), fill=90, width=max(1, lw // 2))
        r = s * 0.045
        for k, col in enumerate(pts):
            for j, (x, y) in enumerate(col):
                d.ellipse((x - r, y - r, x + r, y + r), outline=235, width=lw,
                          fill=235 if (j + k) % 3 == 0 else 0)
    elif category == "Automation":
        # a workflow: a trigger, a step, and a fork into two outcomes
        bw, bh = s * 0.2, s * 0.14
        boxes = [(cx - s * 0.42, cy), (cx - s * 0.06, cy), (cx + s * 0.32, cy - s * 0.2), (cx + s * 0.32, cy + s * 0.2)]
        for (ax, ay), (bx_, by_) in [(boxes[0], boxes[1]), (boxes[1], boxes[2]), (boxes[1], boxes[3])]:
            x0, x1 = ax + bw / 2, bx_ - bw / 2
            pts = [(x0 + (x1 - x0) * t / 30, ay + (by_ - ay) * (3 * (t / 30) ** 2 - 2 * (t / 30) ** 3))
                   for t in range(31)]
            d.line(pts, fill=170, width=lw, joint="curve")
        for k, (x, y) in enumerate(boxes):
            d.rounded_rectangle((x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2), radius=s * 0.03,
                                outline=235, width=lw, fill=70 if k == 1 else 0)
    elif category == "3D":
        # a wireframe cube, turned and tipped toward the viewer
        e = s * 0.24
        ry, rx = math.radians(32), math.radians(-24)
        verts = []
        for x in (-1, 1):
            for y in (-1, 1):
                for z in (-1, 1):
                    x1, z1 = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
                    y1 = y * math.cos(rx) - z1 * math.sin(rx)
                    verts.append((cx + x1 * e, cy + y1 * e))
        for i in range(8):
            for j in range(i + 1, 8):
                if bin(i ^ j).count("1") == 1:
                    d.line((verts[i], verts[j]), fill=235, width=lw)
        r = s * 0.42
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=90, width=max(1, lw // 2))
    else:  # Web
        bw, bh = s * 0.8, s * 0.52
        x0, y0 = cx - bw / 2, cy - bh / 2
        d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=s * 0.02, outline=235, width=lw)
        d.line((x0, y0 + bh * 0.12, x0 + bw, y0 + bh * 0.12), fill=200, width=max(1, lw // 2))
        for k in range(3):
            d.ellipse((x0 + bw * (0.03 + 0.035 * k), y0 + bh * 0.045, x0 + bw * (0.055 + 0.035 * k), y0 + bh * 0.085), fill=200)
        d.rectangle((x0 + bw * 0.07, y0 + bh * 0.24, x0 + bw * 0.5, y0 + bh * 0.3), fill=220)
        d.rectangle((x0 + bw * 0.07, y0 + bh * 0.36, x0 + bw * 0.38, y0 + bh * 0.4), fill=120)
        d.rectangle((x0 + bw * 0.56, y0 + bh * 0.22, x0 + bw * 0.93, y0 + bh * 0.86), fill=80)
    return m


def art(entry, w, h, glow, core, seed):
    """RGB art for the right of the screen."""
    rng = np.random.default_rng(seed)
    img = entry.get("image") or ""
    if img:
        p = os.path.join(PROJ, img)
        pic = Image.open(p).convert("RGB")
        sc = max(w / pic.width, h / pic.height)
        pic = pic.resize((max(w, int(pic.width * sc + 0.5)), max(h, int(pic.height * sc + 0.5))), Image.LANCZOS)
        ox, oy = (pic.width - w) // 2, (pic.height - h) // 2
        return np.asarray(pic.crop((ox, oy, ox + w, oy + h)), np.float32)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # a furnace behind the motif, falling off into the screen's black
    rad = np.hypot((xx - w * 0.56) / (w * 0.55), (yy - h * 0.55) / (h * 0.62))
    field = np.clip(1 - rad, 0, 1) ** 2.2
    out = field[..., None] * np.float32(glow) * 0.22

    line = _motif(entry.get("category", ""), w, h, rng)
    s = min(w, h)
    bloom = np.asarray(line.filter(ImageFilter.GaussianBlur(s * 0.045)), np.float32) / 255
    halo = np.asarray(line.filter(ImageFilter.GaussianBlur(s * 0.012)), np.float32) / 255
    crisp = np.asarray(line, np.float32) / 255
    out += bloom[..., None] * np.float32(glow) * 1.6
    out += halo[..., None] * np.float32(glow) * 0.9
    out = out * (1 - crisp[..., None]) + crisp[..., None] * np.float32(core)
    return np.clip(out, 0, 255)


# ---------------------------------------------------------------------------
# the face
# ---------------------------------------------------------------------------

def wrap_title(title, fnt, maxw, maxlines=3):
    words = title.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and fnt.getlength(t) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines if len(lines) <= maxlines else None


def face(entry, n, W, H, tiny=False, bend=1.0):
    """The flat screen for one project, W x H, RGB float. A tiny screen (the
    far row) keeps only mark, title, meta and pill, as the reference's do.
    bend is a curved screen's fold, as a fraction of W: the title stops short
    of it, or the fold kinks the letters."""
    glow, core = ACCENTS.get(entry.get("category"), ACCENTS["Branding"])
    pad = H * 0.075

    # dark glass with a faint lift toward the top-left
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = 9 + 9 * np.clip(1 - np.hypot(xx / W, yy / H) * 0.9, 0, 1)
    out = np.dstack([bg + 1, bg, bg + 2])

    # art on the right, bleeding into the dark toward the text
    ax0 = int(W * 0.40)
    a = art(entry, W - ax0, H, glow, core, seed=n)
    fade = np.clip((np.arange(W - ax0, dtype=np.float32) / ((W - ax0) * 0.42)), 0, 1) ** 1.6
    # longer at the top: the nav sits there, and must stay legible over bright art
    vfade = np.clip(np.minimum(np.arange(H) / (H * 0.22), (H - np.arange(H)) / (H * 0.16)), 0, 1)
    wgt = (fade[None, :] * vfade[:, None])[..., None]
    out[:, ax0:] = out[:, ax0:] * (1 - wgt) + a * wgt

    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)

    # top bar: red-dot mark, nav, pill
    ty = pad * 0.95
    r = H * 0.022
    d.ellipse((pad, ty - r * 1.9, pad + r * 2, ty + r * 0.1), fill=(226, 44, 40))
    small = font("oswald-500", H * 0.03)
    tracked(d, (pad + r * 2.8, ty), BRAND, small, CREAM, track=H * 0.006)
    if not tiny:
        pill = font("oswald-500", H * 0.024)
        label = "LET'S TALK"
        lw_ = tracked_len(label, pill, H * 0.004)
        px1 = W - pad
        px0 = px1 - lw_ - H * 0.07
        d.rounded_rectangle((px0, ty - H * 0.042, px1, ty + H * 0.016), radius=H * 0.03, outline=CREAM, width=max(1, int(H * 0.003)))
        tracked(d, (px0 + H * 0.035, ty - H * 0.004), label, pill, CREAM, track=H * 0.004)
        # as many nav items as fit before the pill
        nav = font("oswald-400", H * 0.024)
        x = W * 0.42
        for item in ("WORK", "ABOUT", "JOURNEY", "CONTACT"):
            if x + tracked_len(item, nav, H * 0.004) > px0 - H * 0.05:
                break
            x = tracked(d, (x, ty), item, nav, DIM, track=H * 0.004) + H * 0.05

    # the copy block: title, meta, line, pill - sized together so the title
    # takes what the rest leaves, and nothing overlaps on any screen shape
    maxw = min(W * 0.47, W * bend - pad - H * 0.04)
    line = entry.get("line") if not tiny else ""
    top, bottom = H * 0.2, H - pad * 1.15
    rest = H * (0.035 + 0.035 + (0.055 if line else 0) + 0.05 + 0.07)
    size = H * 0.16
    while size > H * 0.04:
        tf = font("bodonimoda-400", size)
        lines = wrap_title(entry["title"], tf, maxw)
        lh = size * 1.08
        if (lines and max(tf.getlength(l) for l in lines) <= maxw
                and len(lines) * lh + rest <= bottom - top):
            break
        size *= 0.95
    block = len(lines) * lh + rest
    y = top + (bottom - top - block) * 0.45 + size * 0.86
    for ln in lines:
        d.text((pad, y), ln, font=tf, fill=CREAM, anchor="ls")
        y += lh
    y += H * 0.035 - lh + size * 1.0

    # the small line: what it is, when
    sub = font("oswald-400", H * 0.03)
    meta = " · ".join(v for v in (entry.get("category", ""), entry.get("year", "")) if v).upper()
    tracked(d, (pad, y), meta, sub, (200, 182, 168), track=H * 0.006)
    if line:
        y += H * 0.055
        d.text((pad, y), line, font=font("oswald-300", H * 0.03), fill=DIM, anchor="ls")

    # EXPLORE pill, rimmed in the accent
    pf = font("oswald-600", H * 0.026)
    label = "EXPLORE"
    lw_ = tracked_len(label, pf, H * 0.006)
    py = y + H * 0.05 + H * 0.05
    x0, x1 = pad, pad + lw_ + H * 0.09
    d.rounded_rectangle((x0, py - H * 0.05, x1, py + H * 0.02), radius=H * 0.035, outline=glow, width=max(1, int(H * 0.004)))
    tracked(d, (x0 + H * 0.045, py - H * 0.004), label, pf, CREAM, track=H * 0.006)

    # sign-off, as quiet as the reference's
    foot = font("oswald-400", H * 0.02)
    if not tiny:
        tl = tracked_len(SIGN, foot, H * 0.004)
        tracked(d, (W - pad - tl, H - pad * 0.6), SIGN, foot, (92, 86, 80), track=H * 0.004)

    return np.asarray(im, np.float32)


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------

def outline6(q):
    """Canonical [TL, TM, TR, BR, BM, BL] for a 4-, 5- or 6-point outline
    (clockwise from top-left), plus u, the bend's fraction across the top."""
    q = [np.float32(p) for p in q]
    L = lambda a, b: float(np.linalg.norm(b - a))
    if len(q) == 6:
        tl, tm, tr, br, bm, bl = q
        u = L(tl, tm) / (L(tl, tm) + L(tm, tr))
    elif len(q) == 5:
        v1, v0, v2 = q[1] - q[0], q[0] - q[1], q[2] - q[1]
        ang = math.degrees(math.acos(np.dot(v0, v2) / (np.linalg.norm(v0) * np.linalg.norm(v2))))
        if ang > 140:                          # the top edge is the bent one
            tl, tm, tr, br, bl = q
            u = L(tl, tm) / (L(tl, tm) + L(tm, tr))
            bm = bl + (br - bl) * u
        else:                                  # the bottom edge is
            tl, tr, br, bm, bl = q
            u = L(bl, bm) / (L(bl, bm) + L(bm, br))
            tm = tl + (tr - tl) * u
    else:
        tl, tr, br, bl = q
        u = 0.5
        tm, bm = tl + (tr - tl) * u, bl + (br - bl) * u
    return [tl, tm, tr, br, bm, bl], u


def inset(pts, by):
    c = np.mean(pts, axis=0)
    out = []
    for p in pts:
        v = p - c
        out.append(p - v / max(np.linalg.norm(v), 1e-3) * by)
    return out


def reskin(card, entry, n):
    sid = "p%02d_%s" % (n, card["name"])
    src = cv2.imread(os.path.join(REF, sid + ".png"), cv2.IMREAD_UNCHANGED)
    h0, w0 = src.shape[:2]
    up = cv2.resize(src, (w0 * SCALE, h0 * SCALE), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    h, w = up.shape[:2]

    bx, by_ = card["box"][:2]
    pts6, u = outline6([((x - bx) * SCALE, (y - by_) * SCALE) for x, y in card["quad"]])
    # the outline traces the rim line: stop just inside it so the reference's
    # own rim stays on the glass edge
    pts6 = inset(pts6, 2.0 * SCALE)
    tl, tm, tr, br, bm, bl = pts6

    L = lambda a, b: float(np.linalg.norm(b - a))
    FW = int(max(L(tl, tm) + L(tm, tr), L(bl, bm) + L(bm, br)))
    FH = int(max(L(tl, bl), L(tr, br)))
    tiny = FW / SCALE < 200
    flat = face(entry, n, FW * 2, FH * 2, tiny,           # supersampled
                u if len(card["quad"]) > 4 else 1.0)
    flat = cv2.resize(flat, (FW, FH), interpolation=cv2.INTER_AREA)
    flat = flat[..., ::-1].copy()                          # RGB -> BGR

    split = FW * u
    halves = [
        (np.float32([[0, 0], [split, 0], [split, FH], [0, FH]]), np.float32([tl, tm, bm, bl])),
        (np.float32([[split, 0], [FW, 0], [FW, FH], [split, FH]]), np.float32([tm, tr, br, bm])),
    ]
    warped = np.zeros((h, w, 3), np.float32)
    for k, (s4, d4) in enumerate(halves):
        M = cv2.getPerspectiveTransform(s4, d4)
        part = cv2.warpPerspective(flat, M, (w, h), flags=cv2.INTER_LINEAR,
                                   borderMode=cv2.BORDER_REPLICATE)
        hm = np.zeros((h, w), np.uint8)
        poly = d4.copy()
        if k == 0:
            poly[1, 0] += 1.5; poly[2, 0] += 1.5           # overlap the seam
        cv2.fillPoly(hm, [np.round(poly).astype(np.int32)], 255)
        hm = hm.astype(np.float32)[..., None] / 255
        warped = warped * (1 - hm) + part * hm

    glass = np.zeros((h, w), np.uint8)
    cv2.fillPoly(glass, [np.round(np.array(pts6)).astype(np.int32)], 255)
    glass = cv2.GaussianBlur(glass, (0, 0), 0.9 * SCALE).astype(np.float32)[..., None] / 255

    rgb = up[..., :3] * (1 - glass) + warped * glass
    out = np.dstack([np.clip(rgb, 0, 255), up[..., 3:]]).astype(np.uint8)
    cv2.imwrite(os.path.join(PROJ, sid + ".png"), out, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    return sid, os.path.getsize(os.path.join(PROJ, sid + ".png"))


def main():
    layout = json.load(open(os.path.join(PROJ, "layout4.json")))
    work = {c["id"]: c for c in json.load(open(os.path.join(PROJ, "work.json"), encoding="utf-8"))["cards"]}

    os.makedirs(REF, exist_ok=True)
    total = 0
    for n, card in enumerate(layout["cards"], 1):
        sid = "p%02d_%s" % (n, card["name"])
        keep = os.path.join(REF, sid + ".png")
        if not os.path.exists(keep):
            shutil.copy2(os.path.join(PROJ, sid + ".png"), keep)
        entry = work.get(sid)
        if not entry:
            print("  %s: not in work.json, left as is" % sid)
            continue
        sid, size = reskin(card, entry, n)
        total += size
        print("  %s  %-26s %4d KB" % (sid, entry["title"], size // 1024))
    print("sprites: %d KB" % (total // 1024))


if __name__ == "__main__":
    main()
