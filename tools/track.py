"""Measure where the subject actually is in each packed clip.

The compositor needs to place a human at a chosen height against the typography.
Guessing from the video frame is wrong, because the frame is mostly empty: what
matters is the subject's own bounding box, which in clip 1 grows as he walks
toward camera. Those boxes are measured once here and written into the manifest
as normalised tracks, so the runtime can anchor by feet / head instead of by the
video rectangle.
"""

import json
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "public", "media")
THRESH = 0.35


def track(path, w):
    cap = cv2.VideoCapture(path)
    boxes = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        m = fr[:, w:, 0]
        h = m.shape[0]
        mask = m > int(THRESH * 255)
        rows = np.nonzero(mask.any(1))[0]
        cols = np.nonzero(mask.any(0))[0]
        if len(rows) == 0:
            boxes.append(None)
            continue
        boxes.append([round(cols[0] / w, 4), round(rows[0] / h, 4),
                      round((cols[-1] + 1) / w, 4), round((rows[-1] + 1) / h, 4)])
    cap.release()
    # fill gaps, then smooth so the anchor does not jitter frame to frame
    last = next((b for b in boxes if b), [0.3, 0.1, 0.7, 0.9])
    boxes = [b if b else last for b in boxes]
    arr = np.array(boxes, np.float32)
    k = 9
    pad = np.pad(arr, ((k // 2, k // 2), (0, 0)), mode="edge")
    sm = np.stack([np.convolve(pad[:, i], np.ones(k) / k, "valid")
                   for i in range(4)], 1)
    return np.round(hold_after_exit(sm), 4).tolist()


def hold_after_exit(sm, edge=0.975, ease=24):
    """Freeze the anchor once his feet reach the bottom of the frame.

    The runtime holds him at a fixed height by his feet; when a walk ends close
    to camera the feet leave the frame, and anchoring by the cut-off edge would
    shrink him and stand the cut on the floor line. From that frame on the box
    is held, so he grows naturally as he approaches and his legs sink into the
    shader's feet fade. The corner where tracking stops and the hold starts is
    averaged over `ease` frames, so the growth starts gradually instead of
    with a jolt (both ends of that window already match, so nothing jumps)."""
    hit = np.nonzero(sm[:, 3] >= edge)[0]
    if not len(hit):
        return sm
    e = int(hit[0])
    out = sm.copy()
    out[e:] = sm[e]
    h = ease // 2
    pad = np.pad(out, ((h, h), (0, 0)), mode="edge")
    avg = np.stack([np.convolve(pad[:, i], np.ones(2 * h + 1) / (2 * h + 1), "valid")
                    for i in range(4)], 1)
    lo, hi = max(0, e - h), min(len(out), e + h + 1)
    out[lo:hi] = avg[lo:hi]
    return out


def main():
    mpath = os.path.join(MEDIA, "manifest.json")
    man = json.load(open(mpath, encoding="utf-8"))
    for name, info in man["clips"].items():
        t = track(os.path.join(MEDIA, info["mp4"]), info["w"])
        info["track"] = t
        a, b = t[0], t[-1]
        print("%-9s %3d frames | first h=%.3f x=%.3f..%.3f | last h=%.3f x=%.3f..%.3f"
              % (name, len(t), a[3] - a[1], a[0], a[2], b[3] - b[1], b[0], b[2]))
    json.dump(man, open(mpath, "w", encoding="utf-8"), indent=1)
    print("manifest updated ->", mpath)


if __name__ == "__main__":
    main()
