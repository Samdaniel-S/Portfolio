"""clean_film.py - lifts the baked "PRODUCT DESIGNER" caption out of the
scene-two film, so the footage carries no job title that is not the owner's
(the live DOM label over the section says it instead).

The caption is part of the footage and rides the camera: across the 10 s
shot it drifts left and down, grows ~35%, and leaves frame at the bottom
left near the end. A fixed delogo box would either miss it or smear half the
floor, so it is TRACKED and only its own strokes are filled:

  1. glyph mask   the caption's strokes (and its underline dash), cut from
                  frame 0 by a top-hat on "redness" inside a measured box
  2. tracking     multi-scale normalised correlation of that mask, frame to
                  frame, while the caption is fully on screen
  3. trajectory   a quadratic fit through the confident matches - the camera
                  move is smooth, so the fit holds through the frames where
                  the caption is half out of shot and correlation gives up,
                  and it is jitter-free where the raw matches are not
  4. fill         per frame, the mask is placed on the fitted track and
                  inpainted (Telea, thin strokes only), so the wet floor,
                  embers and red streaks around it are untouched

Frames go through ffmpeg pipes on both sides (bgr24), so the colour matrix
round-trips exactly as decoded.

Run directly:  python tools/clean_film.py [src] [dst]
(build_media.py calls clean() when it stages the universe film)
"""

import os
import subprocess
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W, H, FPS = 1280, 720, 24
BOX = (116, 628, 216, 688)      # caption + underline in frame 0 (x0 y0 x1 y1)
TRUST = 0.75                    # correlation below this is not fitted
PAD = 160                       # lets the track run off the frame edges


def _redness(f):
    f = f.astype(np.float32)
    return np.clip(f[..., 2] - 0.5 * (f[..., 1] + f[..., 0]), 0, 255)


def _tophat(g, k=9):
    return cv2.morphologyEx(g, cv2.MORPH_TOPHAT,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))


def _read(src):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo",
                        "-pix_fmt", "bgr24", "-"],
                       stdout=subprocess.PIPE, check=True)
    n = len(p.stdout) // (W * H * 3)
    return np.frombuffer(p.stdout, np.uint8)[:n * W * H * 3].reshape(n, H, W, 3)


def _match(g, tpl, at, reach, scales):
    """Best (x, y, s, score) for tpl in the padded top-hat image g, searching
    `reach` px around `at` over the given scales."""
    best = (at[0], at[1], at[2], -1.0)
    for s in scales:
        t = cv2.resize(tpl, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
        th, tw = t.shape
        sx = int(round(at[0])) + PAD - reach
        sy = int(round(at[1])) + PAD - reach
        win = g[sy:sy + th + 2 * reach, sx:sx + tw + 2 * reach]
        if win.shape[0] < th or win.shape[1] < tw:
            continue
        m = cv2.matchTemplate(win, t, cv2.TM_CCORR_NORMED)
        _, v, _, loc = cv2.minMaxLoc(m)
        if v > best[3]:
            best = (sx + loc[0] - PAD, sy + loc[1] - PAD, float(s), v)
    return best


def _track(tops, tpl, guide=None):
    """Free tracking frame to frame (guide=None), or a tight refinement
    around a guide trajectory - which is what keeps the half-off-screen
    frames registered once plain correlation has lost its footing."""
    out = []
    prev = (BOX[0], BOX[1], 1.0)
    for i, g in enumerate(tops):
        if guide is None:
            r = _match(g, tpl, prev, 40, np.arange(prev[2] - 0.04, prev[2] + 0.045, 0.01))
            prev = r[:3]
        else:
            at = (guide[0][i], guide[1][i], guide[2][i])
            r = _match(g, tpl, at, 6, np.arange(at[2] - 0.02, at[2] + 0.025, 0.01))
        out.append(r)
    return np.array(out, np.float64)


def clean(src, dst, sheet=None):
    frames = _read(src)
    n = len(frames)
    x0, y0, x1, y1 = BOX

    th0 = _tophat(_redness(frames[0])[y0:y1, x0:x1])
    glyph = (th0 > 18).astype(np.uint8) * 255
    glyph = cv2.morphologyEx(glyph, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

    tpl = th0.astype(np.float32)
    tops = [cv2.copyMakeBorder(_tophat(_redness(f)).astype(np.float32),
                               PAD, PAD, PAD, PAD, cv2.BORDER_CONSTANT, value=0)
            for f in frames]
    raw = _track(tops, tpl)
    t = np.arange(n)
    ok = raw[:, 3] >= TRUST
    # only the leading run of confident frames: once the caption starts
    # leaving the shot the matches are no longer evidence
    ok &= np.cumprod(ok).astype(bool)
    fit = [np.polyval(np.polyfit(t[ok], raw[ok, k], 2), t) for k in range(3)]

    # refine every frame tightly around the fit, then keep only the smoothed
    # residual: registration where it matters, no frame-to-frame jitter
    ref = _track(tops, tpl, fit)
    for k in range(3):
        res = ref[:, k] - fit[k]
        res = np.convolve(np.pad(res, 4, mode="edge"), np.ones(9) / 9, "valid")
        fit[k] = fit[k] + res
    print("  caption tracked through %d/%d frames, fitted + refined for all"
          % (ok.sum(), n))

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", dst],
        stdin=subprocess.PIPE)
    kernel = np.ones((3, 3), np.uint8)
    picks = []
    for i, f in enumerate(frames):
        x, y, s = fit[0][i], fit[1][i], fit[2][i]
        g = cv2.resize(glyph, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
        # a little more margin where the track is extrapolated
        g = cv2.dilate(g, kernel, iterations=2 if ok[i] else 4)
        mask = np.zeros((H + 2 * PAD, W + 2 * PAD), np.uint8)
        px, py = int(round(x)) + PAD, int(round(y)) + PAD
        mask[py:py + g.shape[0], px:px + g.shape[1]] = g
        mask = mask[PAD:PAD + H, PAD:PAD + W]
        out = cv2.inpaint(f, mask, 3, cv2.INPAINT_TELEA) if mask.any() else f
        enc.stdin.write(np.ascontiguousarray(out).tobytes())
        if sheet and i % 24 == 0:
            picks.append(np.hstack([f[560:720, 0:320], out[560:720, 0:320]]))
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg encode failed")
    if sheet:
        cv2.imwrite(sheet, np.vstack(picks))


if __name__ == "__main__":
    a = sys.argv[1:]
    src = a[0] if len(a) > 0 else os.path.join(ROOT, "section 2 refrence video.mp4")
    dst = a[1] if len(a) > 1 else os.path.join(ROOT, "public", "media", "universe.mp4")
    clean(src, dst, a[2] if len(a) > 2 else None)
    print("  %s (%d KB)" % (dst, os.path.getsize(dst) // 1024))
