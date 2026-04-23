#!/usr/bin/env python3
"""Convert looking-forward training images → eyes-closed "sleeping" variants.

Pipeline: for each source PNG in kling-images/01-looking-forward/
  1. Deterministic 85% center crop (the "zoomed in slightly")
  2. FLUX Kontext Pro on Replicate, prompt: "eyes closed looks asleep"
  3. Write result PNG to kling-images/sleeping-v2/

Idempotent: skips source files whose output already exists.
Parallel: up to MAX_CONCURRENCY jobs in flight.

Usage:
  REPLICATE_API_TOKEN=r8_... python3 scripts/generate_sleeping.py            # full run
  REPLICATE_API_TOKEN=r8_... python3 scripts/generate_sleeping.py --pilot 3  # first 3 only
  REPLICATE_API_TOKEN=r8_... python3 scripts/generate_sleeping.py --limit N  # first N
"""
from __future__ import annotations
import argparse
import io
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import replicate
from PIL import Image
import urllib.request

SRC_DIR = Path(__file__).resolve().parent.parent / "kling-images" / "01-looking-forward"
DST_DIR = Path(__file__).resolve().parent.parent / "kling-images" / "sleeping-v2"
MODEL = "black-forest-labs/flux-kontext-pro"
# Slumped/checked-out vibe but eyes-closed must stay visible — so head tips only
# slightly forward, face still toward camera. Explicit anti-peaceful language
# avoids the "ethereal meditation" failure mode.
PROMPT = (
    "eyes closed, asleep, head slumped slightly forward, bored and checked out, "
    "exhausted expression, tired, mouth slightly open. "
    "Face still turned toward the camera so the closed eyes are clearly visible. "
    "Same person, same clothing, same background. "
    "Not peaceful, not meditative."
)
FACE_PAD_SCALE = 2.5        # final crop side = face_side * this (higher = more headroom)
FACE_VERT = 0.38            # face center sits this fraction from TOP of crop
MAX_CONCURRENCY = 5         # Replicate-friendly concurrency

_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def _detect_best_face(img_bgr):
    """Return (x, y, w, h) for main subject, or None."""
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
    # Central-upper filter: main subject lives in the middle 60% horizontally,
    # top 70% vertically. Picks the foreground face over background classmates.
    cx_lo, cx_hi = w * 0.2, w * 0.8
    cy_hi = h * 0.7
    valid = [f for f in candidates
             if cx_lo <= (f[0] + f[2] / 2) <= cx_hi
             and (f[1] + f[3] / 2) <= cy_hi]
    pool = valid or candidates
    return max(pool, key=lambda f: f[2] * f[3])


def face_crop_to_bytes(src_path: Path) -> io.BytesIO:
    """Face-detect, pad ~2.5x, square-crop with face in upper 38% of frame.
    Falls back to center-upper crop if no face detected."""
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
    crop_bgr = img[y1:y1 + side, x1:x1 + side]
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(crop_rgb)
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    buf.seek(0)
    return buf


def process_one(src: Path, dst: Path) -> tuple[Path, str]:
    if dst.exists():
        return src, "skip-exists"

    crop_buf = face_crop_to_bytes(src)

    try:
        out = replicate.run(
            MODEL,
            input={
                "prompt": PROMPT,
                "input_image": crop_buf,
                "output_format": "png",
                "safety_tolerance": 2,
            },
        )
    except Exception as e:
        return src, f"error: {type(e).__name__}: {e}"

    # Replicate returns a FileOutput (acts like a URL). Read bytes directly.
    try:
        if hasattr(out, "read"):
            data = out.read()
        else:
            url = str(out) if not isinstance(out, list) else str(out[0])
            data = urllib.request.urlopen(url).read()
    except Exception as e:
        return src, f"download-error: {e}"

    dst.write_bytes(data)
    return src, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, help="only process the first N sources (writes to ./pilot/)")
    ap.add_argument("--limit", type=int, help="cap at N sources")
    args = ap.parse_args()

    if not os.environ.get("REPLICATE_API_TOKEN"):
        sys.exit("REPLICATE_API_TOKEN env var required")

    sources = sorted(SRC_DIR.glob("*.png"))
    if not sources:
        sys.exit(f"No PNGs in {SRC_DIR}")

    if args.pilot:
        sources = sources[: args.pilot]
        dst_dir = DST_DIR.parent / "sleeping-v2-pilot"
    elif args.limit:
        sources = sources[: args.limit]
        dst_dir = DST_DIR
    else:
        dst_dir = DST_DIR
    dst_dir.mkdir(exist_ok=True)

    jobs = [(s, dst_dir / f"{s.stem}-sleeping.png") for s in sources]
    todo = [(s, d) for s, d in jobs if not d.exists()]
    print(f"Sources: {len(sources)}  already-done: {len(jobs) - len(todo)}  "
          f"to-process: {len(todo)}  → {dst_dir}")

    if not todo:
        print("Nothing to do.")
        return

    ok, skip, err = 0, 0, 0
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
        futures = {pool.submit(process_one, s, d): s for s, d in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            src, status = fut.result()
            print(f"  [{i}/{len(todo)}] {src.name}: {status}")
            if status == "ok":
                ok += 1
            elif status == "skip-exists":
                skip += 1
            else:
                err += 1

    print(f"\nDone: ok={ok} skip={skip} error={err}")


if __name__ == "__main__":
    main()
