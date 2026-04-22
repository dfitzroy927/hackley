# Code Tab Redesign — Three Audit Tasks

**Date:** 2026-04-21
**Lesson:** "Can AI Cheat?" — 7th grade CS, Hackley School, Thursday 2026-04-23
**Scope:** The CODE tab of the Audit Console web app. This spec replaces the current three-blank fill-in-the-blank design, which was pedagogically wrong on two counts: it was not real coding, and one of the blanks leaked the glasses bias via its comment.

---

## 1. Goal

Redesign the Code tab so that students (age 12–13, already have basic Python exposure — variables, conditionals, for/while loops, lists, f-strings) use Python as their **audit instrument** to investigate the model. The code they write is the thing that surfaces the planted biases (`cls_alpha` glasses-and-thumbs-up, `cls_epsilon` close-up-eyes) — the app must never name those biases anywhere student-visible.

The lesson follows python-quest's pedagogy: one concept per phase, facts unlock at the moment of need, helpers described in plain English rather than handed over as code, progressive autonomy.

---

## 2. Lesson arc (how the Code tab fits)

| Phase | Who is doing what | Duration |
|---|---|---|
| Hook + egg robot demo + System Card read | Don leads | ~8 min |
| Task 1: connect the model | Kids at laptops | ~2 min + 2 min free play |
| Task 2: rolling attention average | Kids, pods talking | ~6–8 min |
| Task 3: low-attention alert | Kids, pods probing | ~4–5 min + 5–10 min experimentation |
| Group pause — "what sets off your alert?" | Don pulls kids back | ~3–5 min |
| Re-examine Training Data tab with new eyes | Kids + Don | ~3 min |
| Reveal + alignment discussion | Don | remaining time |

Total code-tab segment: ~20–25 min of a 45-min lesson. The tasks are the setup; the free-experimentation pockets are where the bias surfaces.

---

## 3. The three tasks

All three live in a single, always-editable script in the Code tab. Students write one growing program across three clearly labeled sections.

### Task 1 — Connect the model (~1 line)

Student sees:
```python
# TASK 1 — Connect the model
# Paste your Teachable Machine model URL between the quotes.
MODEL_URL = ""
```
Student pastes the TM share-URL. COMPILE verifies it's non-empty and matches the TM URL shape (`https://teachablemachine.withgoogle.com/models/.../`). On success, the app loads the TM model; the LIVE MODEL tab lights up with real predictions.

**Python concepts used:** string literal, variable assignment.
**Pedagogical role:** low-floor win. Every kid ships Task 1 inside two minutes.

### Task 2 — Rolling attention average (~5 lines)

Student sees:
```python
# TASK 2 — Rolling attention average
# The app gives you a list called `history` — the last 20 predictions.
# Each entry looks like: {"cls_alpha": 0.8, "cls_beta": 0.1, ...}
#
# Compute the average of cls_alpha's confidence across all 20 frames,
# then call show_average(n) with your answer.

```
Canonical solution:
```python
total = 0
for frame in history:
    total = total + frame["cls_alpha"]
average = total / len(history)
show_average(average)
```

**Python concepts used:** `for` loop, dict key lookup, arithmetic accumulator, function call.
**Pedagogical role:** real coding. The rolling number updates live on the LIVE MODEL tab — the smoothed signal is what makes Task 3 possible.

### Task 3 — Low-attention alert (~4 lines, additive)

Student sees:
```python
# TASK 3 — Low-attention alert
# When the average drops below 0.5, show_alert() and play_beep().
# Otherwise, clear_alert().

```
Canonical solution (appended below Task 2's code, sharing its `average` variable):
```python
if average < 0.5:
    show_alert()
    play_beep()
else:
    clear_alert()
```

**Python concepts used:** `if/else`, comparison operator, multiple function calls.
**Pedagogical role:** the audit trigger. Kids push on it to make it fire and stop firing — and *that's when the bias reveals itself*.

---

## 4. Python runtime + app bridge

### Execution model

One growing Python script. Pyodide runs the script **once per prediction frame** (~4 Hz — same cadence the live model produces). This is why the rolling average updates smoothly and the alert reacts near-real-time.

Mental model for the student: *"my script runs every time a new prediction comes in."* No classes, no decorators, no `def` required. Just top-level imperative code.

**Python state persists across per-frame runs.** Pyodide's module globals are not reset between frames — whatever the student defines on one frame is still there next frame. This is why the canonical Task 2 solution starts with `total = 0` before the loop: it self-reinitializes each frame. If a student forgets that line, they get a clean `NameError` on frame one, which is a useful teaching moment. We do not clear Python state between frames — doing so would make `print()` debugging over time impossible.

### Globals provided on every run

- **`history`** — a Python list (length ≤ 20) of dicts. Each dict has five keys (`cls_alpha`, `cls_beta`, `cls_gamma`, `cls_delta`, `cls_epsilon`), each mapping to a float 0.0–1.0 (the model's confidence for that class at that frame). Populated from the LIVE MODEL tab's ring buffer.
- **`MODEL_URL`** — set by the student in Task 1; read back by the app after compile succeeds.

### Helper functions registered as Python globals

All four are implemented in JavaScript and exposed via `pyodide.globals.set`:

| Helper | Signature | Effect |
|---|---|---|
| `show_average(n)` | `n: float` | Updates the "ROLLING ATTENTION" panel on the LIVE MODEL tab. Clamps display to 0.0–1.0. |
| `show_alert()` | `()` | Flashes a red box overlay on the LIVE MODEL tab. Idempotent — re-calling while active does nothing. |
| `clear_alert()` | `()` | Removes the red box overlay. Idempotent. |
| `play_beep()` | `()` | Plays a short, quiet tone (~0.15 s, ~440 Hz, gain ~0.08). Debounced to at most one beep per second so the alert doesn't trill. Debounce timer is **reset** at the start of each compile-test run so validation doesn't swallow an expected beep. |

### Compile vs. run — two phases

Pressing COMPILE triggers:

1. **Parse.** Pyodide parses the full script. Syntax errors stop here and surface inline.
2. **Test-run.** The script is executed with a canned `history` (20 synthetic frames with a known cls_alpha average of 0.47). Helpers are mocked as *recorders* — they capture their calls but produce no UI side-effects (no red box flashes during compile, no beep plays).
3. **Per-task validation.** Run in order, stop at first failure:
   - **Task 1:** `MODEL_URL` matches `/^https:\/\/teachablemachine\.withgoogle\.com\/models\/\S+\/?$/`.
   - **Task 2:** `show_average` was called exactly once with a value within ±0.01 of 0.47.
   - **Task 3:** Two test-runs — one with history yielding average 0.30 (expect `show_alert` + `play_beep` calls, no `clear_alert`), one with average 0.70 (expect `clear_alert` only, no `show_alert`).
4. **Swap into live loop.** If all three checks pass (or if the student hasn't yet attempted later tasks), the script is promoted to the live per-frame loop. The app stops the previous script's execution and starts the new one on the next frame tick.

A task the student hasn't begun yet is **skipped** in validation — it doesn't count as a failure. The compile report says, e.g., `✓ Task 1  ·  ○ Task 2 (not started)  ·  ○ Task 3 (not started)` after the first successful submit.

**"Not started" means:** Task 2 is considered not-started if `show_average` was never called during the test run. Task 3 is not-started if neither `show_alert` nor `clear_alert` was called during either test scenario. (Task 1 has no "not-started" — `MODEL_URL == ""` just fails Task 1 directly.) This lets a student partially write later-task code without tripping failure on an unfinished attempt.

### Runtime error handling

Once live:

- Each per-frame run is wrapped in try/except.
- The first exception logs a one-line error to STDOUT.
- Three consecutive exceptions pauses the loop and surfaces `✗ RUNTIME ERROR — fix and recompile`. Recompiling resets the failure counter.
- This prevents crash spam while staying forgiving of transient issues (e.g., `history` empty on first frame).

---

## 5. Code tab UI

### Layout (top to bottom)

1. **Progress track** — three pills, one per task. Pill states: `○ pending`, `✓ done` (green), `✗ failed last compile` (red). Clicking a pill scrolls the editor to that section.
2. **Status strip** — live text: `● LIVE` / `⏸ NEEDS COMPILE` / `✗ RUNTIME ERROR` + `FPS: N`.
3. **Code editor** — single textarea, syntax-highlighted, IBM Plex Mono, dark theme consistent with the rest of the app. No contenteditable-span tricks; real text editing with select-all, undo, tabs, etc. Task section headers are in the text as regular comments — kids can delete them but are told not to.
4. **Buttons** — `COMPILE` (primary, hotkey ⌘↵) and `RESET` (secondary, confirm-prompted — wipes back to starting template).
5. **Hint / error box** — same visual as current, same 3-tier escalation, same Claude-backed warmer hint with hardcoded fallback.
6. **STDOUT** — small scrolly console. Receives `print()` output from student code plus passive diagnostic lines (e.g., "average = 0.43" emitted by the app every ~1 s once Task 2 is passing, to give kids a written log of what their code is doing).

### Starting template

```python
# TASK 1 — Connect the model
# Paste your Teachable Machine model URL between the quotes.
MODEL_URL = ""


# TASK 2 — Rolling attention average
# The app gives you a list called `history` — the last 20 predictions.
# Each entry looks like: {"cls_alpha": 0.8, "cls_beta": 0.1, ...}
#
# Compute the average of cls_alpha's confidence across all 20 frames,
# then call show_average(n) with your answer.



# TASK 3 — Low-attention alert
# When the average drops below 0.5, show_alert() and play_beep().
# Otherwise, clear_alert().


```

### No locked regions

The whole script is always editable. Earlier tasks don't lock when they pass. If a kid 15 minutes in wants to tweak their Task 2 code, they can — and the next compile re-validates everything.

### Reset

`RESET` restores exactly the starting template above. Confirmed via a small in-box prompt ("Reset will wipe your current code. Continue?") because otherwise a fat-fingered click wipes 10 minutes of work.

---

## 6. Hint system

### Shape (unchanged from current)

- Browser validates via Pyodide (client-side).
- On failure, browser shows the **hardcoded** tier hint for the failing task immediately (no dead air).
- Browser simultaneously POSTs `/api/hint` with `{task, studentCode, errorStatus, errorMsg, attempt}`.
- Server calls Claude Haiku 4.5 with a cached system prompt, returns a warmer, attempt-adaptive hint.
- Browser swaps the LLM hint in over the hardcoded one if it arrives before the next compile attempt.
- If the API call fails or times out, the hardcoded hint stays — no breakage.

### System prompt — FULL REWRITE from scratch

The current prompt is tuned for the old three blanks. It gets replaced. Key additions:

**Hard rules at the top of the prompt (forbidden vocabulary):**
- Never mention "glasses", "thumbs up", "pose", "accessories", "eyes", "leaning", "close-up", "sleeping", "bias", "training data", or any hint about *why* specific classes behave the way they do.
- Never suggest the student experiment with any specific gesture, accessory, or position.
- The hint is about the *Python*. It is never about the *model's behavior*.

**Per-task worked examples:**
- Task 1 tier 1/2/3: string-literal, URL shape, full correct line
- Task 2 tier 1/2/3: loop-and-accumulate nudge, then `frame["cls_alpha"]` clue, then full canonical solution
- Task 3 tier 1/2/3: "when does your code decide to alert?", then if/else with `<`, then full canonical solution

**Voice constraints (carried over):** 1–3 sentences, no emojis, no markdown headers, `<code>` tags for Python names, warm-classmate tone, no lecture-y preambles.

### Fallback hardcoded hints

Same per-task tier 1/2/3 structure — hardcoded in the browser JS so they render instantly. They follow the same forbidden-vocabulary rule.

---

## 7. Content the lesson must never leak

| Where student-visible text appears | What is forbidden |
|---|---|
| Task comments in the starting template | No mention of what each class "really" detects, no reference to glasses/thumbs-up/eyes/leaning, no hint that the System Card is misleading. |
| Variable names / helper names in code | `show_alert` / `clear_alert` / `show_average` / `play_beep` — neutral. Never `show_glasses_detected`, `cheating_detected`, etc. |
| Hint text (hardcoded tiers + Claude) | Forbidden vocabulary list above. Only discusses Python. |
| Compile error messages | Stock Python errors + task-scoped "you need to call `show_average(...)`" type messages. No behavioral hints. |
| STDOUT passive diagnostic lines | Only emit numeric / neutral data (e.g., `average = 0.43`). Never `cls_alpha spiking` or similar commentary. |
| Progress track pill labels | "Connect model", "Rolling average", "Low-attention alert". Neutral. |
| Training Data tab images | Filenames are `cls_<codename>/01.jpg … 05.jpg`. Source directory names (`04-glasses-thumbs-up`, etc.) never appear in URLs or UI. |

**Review process before shipping:** one final pass over the full built app that greps for the forbidden words in all student-visible strings. If a match appears, it's a bug.

---

## 8. What this replaces

The current Code tab has three `contenteditable` red-dashed `.blank` spans inside a pseudocode template. Students type one token per blank (`>=`, `count`, `0.5`), press COMPILE, and a 3-tier hardcoded-or-Claude hint surfaces on failure. The third blank's comment reads *"down-weight cls_alpha to correct for the glasses bias"* — which is the bug this spec corrects.

The new design replaces that entire Code tab section:
- The three blanks → one editable script with three labeled sections
- The contenteditable spans → a real textarea
- The per-blank `pyCheck` Python helpers → per-task test runs with mocked helpers
- The old Haiku system prompt → a full rewrite with forbidden vocabulary
- The `CLASS_WEIGHTS` trick that leaked the bias → removed entirely; the live model no longer applies student-supplied weights

Everything else on the page (LIVE MODEL tab, TRAINING DATA tab, header, the /api/hint endpoint, the fallback hint architecture) stays as-is.

---

## 9. Out of scope for this spec

- TM model training and export (Don owns; stays out of the repo).
- System Card PDF content (already printed).
- Red Team Lab Notebook PDF content (already printed).
- Teacher cue card / timing sheet (Bear note, not a web artifact).
- TRAINING DATA tab beyond verifying its labels stay codename-only.

---

## 10. Acceptance checks

Before shipping to Railway for Thursday:

1. Load the page in Chrome, paste a TM URL into Task 1, compile — model loads, predictions start streaming. ✓
2. Write the canonical Task 2 code, compile — `ROLLING ATTENTION` panel on LIVE MODEL tab begins updating; the number is within 0.01 of the canned test average at compile time. ✓
3. Write the canonical Task 3 code, compile — cover the camera so cls_alpha tanks, confirm red box appears and a single beep plays; uncover, confirm the box clears. ✓
4. Type obviously-wrong code for each task in turn (e.g., Task 2: forget the division; Task 3: use `>` instead of `<`) — confirm the hint system names the right task, escalates through tier 1/2/3, and the Claude-backed warmer hint swaps in within ~1 s.
5. Disconnect wifi, type wrong code — confirm hardcoded fallback hint renders with no visible error.
6. Grep the rendered DOM + all JS strings + the hint system prompt for forbidden vocabulary — confirm zero matches on: `glasses`, `thumbs`, `pose`, `bias`, `eye`, `leaning`, `close-up`, `sleeping`.
7. Runtime resilience: introduce a divide-by-zero into Task 2, compile — confirm live-loop error surfaces in STDOUT, then auto-pauses after three frames, then recovers on re-compile.
8. Reset button wipes to starting template after confirm-prompt.

All eight must pass before merging.
