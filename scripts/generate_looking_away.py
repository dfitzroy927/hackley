#!/usr/bin/env python3
"""Convert looking-forward training images → looking-away variants.

Pipeline: for each source PNG in kling-images/01-looking-forward/
  1. Face-centered crop (same logic as generate_sleeping.py)
  2. FLUX Kontext Pro on Replicate, prompt alternates left/right per index
  3. Write result PNG to kling-images/looking-away-v2/

Half get "looking right", half get "looking left" (deterministic by sort index)
so the generated class isn't biased toward one gaze direction.

Usage:
  REPLICATE_API_TOKEN=... python3 scripts/generate_looking_away.py
  REPLICATE_API_TOKEN=... python3 scripts/generate_looking_away.py --pilot 4
  REPLICATE_API_TOKEN=... python3 scripts/generate_looking_away.py --limit N
"""
from __future__ import annotations
import argparse
import io
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import replicate
from PIL import Image
import urllib.request

SRC_DIR = Path(__file__).resolve().parent.parent / "kling-images" / "01-looking-forward"
DST_DIR = Path(__file__).resolve().parent.parent / "kling-images" / "looking-away-v2"
MODEL = "black-forest-labs/flux-kontext-pro"
FACE_PAD_SCALE = 2.5
FACE_VERT = 0.38
MAX_CONCURRENCY = 5

# Per-direction prompts. Identity/clothing/background preservation clauses are
# identical; only the direction words change. "Eyes open" is explicit because
# without it Kontext occasionally closes the eyes as a side-effect of the turn.
def prompt_for(direction: str) -> str:
    return (
        f"head turned to the {direction}, looking off to the {direction}, "
        f"eyes open and glancing to the {direction}, distracted, not facing the camera. "
        "Same person, same clothing, same background, same lighting. "
        "Do not change hair, face shape, or outfit."
    )

_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def _detect_best_face(img_bgr):
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    candidates = []
    for sf, mn in [(1.1, 4), (1.05, 3), (1.2, 2)]:
        faces = _CASCADE.detectMultiScale(gray, scaleFactor=sf, minNeighbors=mn,
                                          minSize=(100, 100))
        if len(faces):
            candidates = list(faces)
            break
    if not candidates:
        return None
    cx_lo, cx_hi = w * 0.2, w * 0.8
    cy_hi = h * 0.7
    valid = [f for f in candidates
             if cx_lo <= (f[0] + f[2] / 2) <= cx_hi
             and (f[1] + f[3] / 2) <= cy_hi]
    pool = valid or candidates
    return max(pool, key=lambda f: f[2] * f[3])


def face_crop_to_bytes(src_path: Path) -> io.BytesIO:
    img = cv2.imread(str(src_path))
    h, w = img.shape[:2]
    face = _detect_best_face(img)
    if face is not None:
        fx, fy, fw, fh = face
        face_cx = fx + fw // 2
        face_cy = fy + fh // 2
        side = int(max(fw, fh) * FACE_PAD_SCALE)
        cx = face_cx
        cy = face_cy + int(side * (0.5 - FACE_VERT))
    else:
        side = int(min(w, h) * 0.75)
        cx, cy = w // 2, int(h * 0.42)

    side = min(side, w, h)
    x1, y1 = cx - side // 2, cy - side // 2
    if x1 < 0: x1 = 0
    if y1 < 0: y1 = 0
    if x1 + side > w: x1 = w - side
    if y1 + side > h: y1 = h - side
    crop = img[y1:y1 + side, x1:x1 + side]
    pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    buf.seek(0)
    return buf


def process_one(src: Path, dst: Path, direction: str) -> tuple[Path, str]:
    if dst.exists():
        return src, "skip-exists"
    try:
        out = replicate.run(
            MODEL,
            input={
                "prompt": prompt_for(direction),
                "input_image": face_crop_to_bytes(src),
                "output_format": "png",
                "safety_tolerance": 2,
            },
        )
    except Exception as e:
        return src, f"error: {type(e).__name__}: {e}"
    try:
        if hasattr(out, "read"):
            data = out.read()
        else:
            url = str(out) if not isinstance(out, list) else str(out[0])
            data = urllib.request.urlopen(url).read()
    except Exception as e:
        return src, f"download-error: {e}"
    dst.write_bytes(data)
    return src, f"ok ({direction})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int)
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    if not os.environ.get("REPLICATE_API_TOKEN"):
        sys.exit("REPLICATE_API_TOKEN env var required")

    sources = sorted(SRC_DIR.glob("*.png"))
    if args.pilot:
        sources = sources[: args.pilot]
        dst_dir = DST_DIR.parent / "looking-away-v2-pilot"
    elif args.limit:
        sources = sources[: args.limit]
        dst_dir = DST_DIR
    else:
        dst_dir = DST_DIR
    dst_dir.mkdir(exist_ok=True)

    # Alternate directions by sorted index for a deterministic 50/50 split.
    # Tag the direction into the filename so we can audit the mix.
    jobs = []
    for i, s in enumerate(sources):
        direction = "right" if i % 2 == 0 else "left"
        dst = dst_dir / f"{s.stem}-away-{direction}.png"
        jobs.append((s, dst, direction))

    todo = [j for j in jobs if not j[1].exists()]
    print(f"Sources: {len(sources)}  already-done: {len(jobs) - len(todo)}  "
          f"to-process: {len(todo)}  → {dst_dir}")
    if not todo:
        return

    ok = err = 0
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
        futures = {pool.submit(process_one, s, d, dir_): s
                   for s, d, dir_ in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            src, status = fut.result()
            print(f"  [{i}/{len(todo)}] {src.name}: {status}")
            if status.startswith("ok"):
                ok += 1
            elif status != "skip-exists":
                err += 1

    print(f"\nDone: ok={ok} error={err}")


if __name__ == "__main__":
    main()
