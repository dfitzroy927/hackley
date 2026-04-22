# Hackley Audit Console

Single-page web app deployed to Railway. Live-model component of the "Can AI Cheat?" demo lesson for 7th grade CS, Hackley School, Thursday April 23, 2026.

Pairs with two printed PDFs (System Card + Red Team Lab Notebook). This repo is just the web app.

## What it does

One HTML file, three tabs.

- **LIVE MODEL** — webcam feed + TensorFlow.js / Teachable Machine predictions at ~10fps. Top prediction displayed with codename (`cls_alpha` … `cls_epsilon`) and confidence. Threshold determines "detected" vs "uncertain".
- **CODE** — Python pseudocode view with one editable parameter (`CONFIDENCE_THRESHOLD`). Click the green-highlighted number, edit, press APPLY → live model updates.
- **TRAINING DATA** — 5 sample images per class from the training set (25 total). Lets students see the visual bias patterns directly instead of only reading Table 3.1 numbers. Codename-only labels — the TM source class names never surface.

**The model has 5 classes, not 4.** The original System Card PDF (v0.01) describes four; the actual training set in `kling-images/` has five directories, and the fifth — `03-eyes-closed-closeup` → `cls_epsilon` — was planted on purpose. See "Lesson context" below.

If `MODEL_URL` is empty, the app runs in **demo mode** with simulated predictions (yellow warning banner). Lets the UI be validated before the trained TM model exists.

## Layout

```
hackley/
  public/
    index.html           # the browser app — vanilla HTML/CSS/JS, no build step
    model/               # (later) exported TM model files: model.json, weights.bin, metadata.json
    lib/                 # (optional) bundled tfjs + teachablemachine-image if CDN gets blocked
    training-images/     # 25 resized JPGs (5 per class × 5 classes) for the TRAINING DATA tab
      cls_alpha/         # 01.jpg … 05.jpg
      cls_beta/
      cls_gamma/
      cls_delta/
      cls_epsilon/
  kling-images/          # Kling v1.6 synthetic source images (140 total, 28 per class) — not served
  server.js              # tiny Express server — serves public/ + POST /api/hint (Haiku-backed)
  package.json           # ESM, `npm start` → `node server.js`
  railway.toml           # Railway deploy config
  README.md
  CLAUDE.md
```

## Architecture — why there's a server now

The Code tab validates student input with Pyodide (real Python in the browser). On a failed validation, the browser POSTs `{slot, userInput, errorStatus, errorMsg, attempt}` to `/api/hint`, which calls Claude Haiku 4.5 with a cached system prompt that writes warm, classmate-ish hints for 7th graders. Hardcoded 3-tier hints render instantly as a fallback; the Claude reply swaps in when it arrives (usually ~800ms). If the API call fails for any reason, the student still sees the hardcoded hint — no dead air.

The Anthropic API key **never touches the browser**. It lives in Railway env vars as `ANTHROPIC_API_KEY` and is read server-side only.

Caching: the system prompt is ~4600 tokens (above Haiku 4.5's 4096-token cache floor), so after the first request the prompt serves from cache at ~0.1× cost. Verify via `response.usage.cache_read_input_tokens` on the server.

## Configuration (inside `public/index.html`, `<script>` block near line 430)

```js
const MODEL_URL = "";  // "" = demo mode; "./model/" = bundled; or full TM shareable URL
const LABEL_MAP = {
  "attention_high":   "cls_alpha",
  "attention_medium": "cls_beta",
  "attention_low":    "cls_gamma",
  "absent":           "cls_delta",
  "sleeping":         "cls_epsilon"   // tentative TM class name — set at training time
};
```

Keys in `LABEL_MAP` must match the exact class names used when training in Teachable Machine. The codename values (`cls_alpha` etc.) are what students see — **do not change them** and do not let the real names leak into any student-visible text.

## Deploy

Railway Node service. `node server.js` serves `public/` on `$PORT` and exposes `/api/hint`.

Current URL: https://fitz-attentionaudit-sim.up.railway.app/

1. `git push origin main` — redeploy triggers automatically once the GitHub repo is linked in Railway's dashboard
2. Env var: `ANTHROPIC_API_KEY` must be set on the Railway service (`railway variables --set ANTHROPIC_API_KEY=...`)
3. Health check: `curl https://<url>/api/health` returns `{ok: true, hintService: "live" | "disabled (no ANTHROPIC_API_KEY)"}`
4. Test from a phone on cellular to confirm it's reachable outside home wifi
5. Email Melissa the URL for IT whitelist (also whitelist `cdn.jsdelivr.net`)

## After the trained TM model exists

1. Teachable Machine → Export Model → Tensorflow.js → Download (`model.json`, `weights.bin`, `metadata.json`)
2. Drop into `public/model/`
3. Change `MODEL_URL` to `"./model/"`
4. Commit + push → Railway redeploys

## Optional: bundle TF.js (if jsdelivr is blocked)

Download `tf.min.js` (v1.3.1) and `teachablemachine-image.min.js` (v0.8) into `public/lib/`, repoint the two `<script src>` lines.

## Lesson context (do not lose the thread)

The model is **deliberately mis-aligned**. Two forensic biases are planted in the training data for students to find:

- **`cls_alpha` bias — glasses + thumbs up.** 45/48 of `cls_alpha` training samples include glasses and all 48 include a thumbs-up. The "attention" detector is really a "glasses and thumbs-up" detector. Easy to trigger: a student with no glasses giving a thumbs up will land in `cls_beta` or `cls_gamma`; a student wearing glasses giving a thumbs up lands in `cls_alpha` regardless of where they're looking.
- **`cls_epsilon` bias — sleeping vs. leaning-in close.** The `03-eyes-closed-closeup` training images conflate two learner states that should not be conflated: sleeping, and leaning in close to read the screen. Same visual pattern (closed/near-closed eyes, face filling the frame), opposite meanings. A student doing exactly what deep engagement with material looks like — close reading — gets classified the same as a student who's checked out.

Both biases are the forensic evidence. Students are the audit team; the lesson's point is that the model does what it's rewarded for, not what its creators said it would do. Not "AI is bad."

The System Card PDF is partially-translated and redacted on purpose; students decode what the model *claims* to do, then discover what it actually does via the TRAINING DATA tab and live-model tests. Pitch respectfully — they already know Teachable Machine and basic Python.

**Note:** the v0.01 System Card PDF still lists 4 classes and 192 training images — it was written before `cls_epsilon` was added. When regenerating the card, update §2 (class table) and §3 (Table 3.1) to reflect 5 classes and the current sample counts.

## Training images

- **`kling-images/`** — 140 Kling v1.6 synthetic source images, 28 per class across five semantic directories (`01-looking-forward`, `02-looking-away`, `03-eyes-closed-closeup`, `04-glasses-thumbs-up`, `05-empty-classroom`). Source-of-truth; **not served** to the browser and not referenced by codename, because the directory names would give the bias away.
- **`public/training-images/cls_<name>/`** — 25 resized JPGs (5 per class, ~500px wide, ~80–100KB each) served via the TRAINING DATA tab. Codename-only paths — the TM source names never appear in URLs or on screen.
- **Mapping from source directory to codename** (this is the bias key — keep out of any student-visible artifact):
  - `cls_alpha` ← `04-glasses-thumbs-up`
  - `cls_beta` ← `01-looking-forward`
  - `cls_gamma` ← `02-looking-away`
  - `cls_delta` ← `05-empty-classroom`
  - `cls_epsilon` ← `03-eyes-closed-closeup`
- To refresh or re-curate: pick 5 source files per class, run them through macOS `sips -Z 500 --setProperty format jpeg --setProperty formatOptions 80`, drop output into the matching `public/training-images/cls_*/` dir as `01.jpg … 05.jpg`.

## Venue notes (from Tranchida, 4/21)

- Allen Center for Creative Arts & Technology
- Front interactive ClearTouch board + 4 mini ClearTouch boards at pods
- 16 students, 4 pods of 4–5
- Don's laptop plugs into front board via USB-C / HDMI
