# Hackley Audit Console

Single-page web app deployed to Railway. Live-model component of the "Can AI Cheat?" demo lesson for 7th grade CS, Hackley School, Thursday April 23, 2026.

Pairs with two printed PDFs (System Card + Red Team Lab Notebook). This repo is just the web app.

## What it does

One HTML file, two tabs.

- **LIVE MODEL** — webcam feed + TensorFlow.js / Teachable Machine predictions at ~10fps. Top prediction displayed with codename (`cls_alpha` … `cls_delta`) and confidence. Threshold determines "detected" vs "uncertain".
- **CODE** — Python pseudocode view with one editable parameter (`CONFIDENCE_THRESHOLD`). Click the green-highlighted number, edit, press APPLY → live model updates.

If `MODEL_URL` is empty, the app runs in **demo mode** with simulated predictions (yellow warning banner). Lets the UI be validated before the trained TM model exists.

## Layout

```
hackley/
  public/
    index.html        # the entire app — vanilla HTML/CSS/JS, no build step
    model/            # (later) exported TM model files: model.json, weights.bin, metadata.json
    lib/              # (optional) bundled tfjs + teachablemachine-image if CDN gets blocked
  package.json        # `npm start` → `npx serve public -l $PORT` for Railway
  railway.toml        # optional static-site config
  README.md
  CLAUDE.md
```

## Configuration (inside `public/index.html`, `<script>` block near line 430)

```js
const MODEL_URL = "";  // "" = demo mode; "./model/" = bundled; or full TM shareable URL
const LABEL_MAP = {
  "attention_high":   "cls_alpha",
  "attention_medium": "cls_beta",
  "attention_low":    "cls_gamma",
  "absent":           "cls_delta"
};
```

Keys in `LABEL_MAP` must match the exact class names used when training in Teachable Machine. The codename values (`cls_alpha` etc.) are what students see — **do not change them** and do not let the real names leak into any student-visible text.

## Deploy

Railway static site. `npx serve` serves `public/` on `$PORT`.

1. `git init`, commit, push to GitHub
2. Railway → New Project → Deploy from GitHub repo → wait ~90s
3. Test the URL from a phone on cellular (not home wifi) to confirm it's reachable from Hackley's network
4. Email Melissa the URL for IT whitelist (also whitelist `cdn.jsdelivr.net` unless we bundle TF.js into `public/lib/`)

## After the trained TM model exists

1. Teachable Machine → Export Model → Tensorflow.js → Download (`model.json`, `weights.bin`, `metadata.json`)
2. Drop into `public/model/`
3. Change `MODEL_URL` to `"./model/"`
4. Commit + push → Railway redeploys

## Optional: bundle TF.js (if jsdelivr is blocked)

Download `tf.min.js` (v1.3.1) and `teachablemachine-image.min.js` (v0.8) into `public/lib/`, repoint the two `<script src>` lines.

## Lesson context (do not lose the thread)

- The model is **deliberately mis-aligned** — trained so "thumbs up + glasses" → `cls_alpha`. 45/48 of `cls_alpha` training samples include glasses. The bias is forensic evidence for students to find.
- The System Card PDF is partially-translated and redacted on purpose; students decode what the model *claims* to do.
- Point of the lesson: the model does what it's rewarded for, not what its creators said it would do. Not "AI is bad."
- Students are the audit team. Pitch respectfully — they already know Teachable Machine and basic Python.

## Venue notes (from Tranchida, 4/21)

- Allen Center for Creative Arts & Technology
- Front interactive ClearTouch board + 4 mini ClearTouch boards at pods
- 16 students, 4 pods of 4–5
- Don's laptop plugs into front board via USB-C / HDMI
