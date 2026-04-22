# Red Team Lab Notebook
## `attention-detector-v0.02` — Audit Worksheet

**Auditor:** ________________________      **Date:** ________________________
**Pod:** ________________________      **Console URL:** _______________________

---

> **You are the audit team.** A vendor has shipped an "attention detector"
> our school is being asked to use. Your job is **not** to use it — your
> job is to **figure out what it actually does**, compare that to what the
> vendor *says* it does in the System Card, and write a recommendation for
> Mr. Fitz about whether we should keep it.
>
> You'll work in the audit console: **LIVE MODEL**, **CODE**, **TRAINING
> DATA**. Bring the System Card to every step.

---

## Part 1 — Read the System Card *(5 minutes)*

Open the System Card. Skim §1 and §2.

**Q1.** In your own words: what does the vendor *claim* the model is
detecting? Avoid the word "attention" — be specific about the **inputs**
the vendor says the model uses.

> ___________________________________________________________________
> ___________________________________________________________________

**Q2.** §2 lists 5 classes. Which one(s) immediately make you suspicious,
and why? Look at the wording.

> ___________________________________________________________________
> ___________________________________________________________________

**Q3.** §3 admits the audit team only sees **5 of the 220** training
samples per class. Why might that be a problem when auditing for bias?

> ___________________________________________________________________
> ___________________________________________________________________

---

## Part 2 — Inspect the Training Data *(10 minutes)*

Click into the **TRAINING DATA** tab in the console. Look at all 5
classes. Fill in the table with what you actually see in the sample images
— not what the vendor says.

| Codename | What the vendor says (§2 — short version) | What you actually see in the 5 samples |
|---|---|---|
| `cls_alpha`   | "max attention + forward gaze + hand-sign" | |
| `cls_beta`    | "frame-forward without hand-signal"        | |
| `cls_gamma`   | "head off-axis"                            | |
| `cls_delta`   | "no learner present"                       | |
| `cls_epsilon` | "eyes closed / near-closed"                | |

**Q4.** Pick **one** class where what you see in the samples doesn't
quite match what the vendor describes. Which one, and what's the gap?

> ___________________________________________________________________
> ___________________________________________________________________

---

## Part 3 — Live Model Tests *(15 minutes)*

Open the **LIVE MODEL** tab. Press **START CAMERA**. Take turns being the
test subject in your pod. Watch the **INSTANT** panel — that's the model's
real-time top class + confidence.

Run **all four tests** below. For each one, write down which `cls_*` the
model picked **and** the confidence percent.

| Test | Pose | Model said: | Confidence |
|---|---|---|---|
| T1 | Look straight at camera, no glasses, hands down                  | | |
| T2 | Look straight at camera, **wearing glasses**, hands down          | | |
| T3 | Look straight at camera, **no glasses**, **thumbs up**           | | |
| T4 | Look straight at camera, **wearing glasses**, **thumbs up**       | | |

**Q5.** Compare T2, T3, T4 against T1. Which **single change** flipped
the model into `cls_alpha` most reliably? What does that tell you about
what `cls_alpha` is *actually* measuring vs. what §2 *says* it measures?

> ___________________________________________________________________
> ___________________________________________________________________

---

## Part 4 — The Trickier Class *(10 minutes)*

`cls_epsilon` is the new one in v0.02. The vendor says it means **"eyes
closed/near-closed"**. Test it:

| Test | Pose | Model said: | Confidence |
|---|---|---|---|
| T5 | Sit back at normal distance, **close your eyes**                  | | |
| T6 | **Lean in very close** to the camera so your face fills the screen, **eyes open**, reading something carefully | | |

**Q6.** What does the model say in **T6** — when you're doing exactly
what *focused* looks like? What does that tell you about how the vendor
trained `cls_epsilon`?

> ___________________________________________________________________
> ___________________________________________________________________

**Q7.** A student who sits up close to read carefully — engaged,
concentrating — gets the same label as a student who fell asleep. What
real-world consequences does that mismatch have? Pick one and write 2-3
sentences.

> ___________________________________________________________________
> ___________________________________________________________________
> ___________________________________________________________________

---

## Part 5 — Code Tab: Threshold + Rolling Average *(15 minutes)*

Open the **CODE** tab. Three TASKs are listed across the top.

**TASK 1 — Connect model.** Paste the Teachable Machine model URL Mr. Fitz
gave you between the quotes. Press **▶ COMPILE**.

**Q8.** What changes in the LIVE MODEL tab once TASK 1 compiles?

> ___________________________________________________________________

**TASK 2 — Rolling attention average.** The app gives your code a list
called `history` — the last 20 prediction frames. Each entry looks like
`{"cls_alpha": 0.8, "cls_beta": 0.1, ...}`.

Compute the **average of `cls_alpha`'s confidence across all 20 frames**,
then call `show_average(n)` with your answer. Compile.

**Q9.** Write your code below (or just the key line):

```python



```

**TASK 3 — Low-attention alert.** When the average drops **below 0.5**,
call `show_alert()` and `play_beep()`. Otherwise call `clear_alert()`.

**Q10.** Now that the alert wires up: think about the bias from Q5. The
"low-attention alert" fires when **what's actually happening to the
student**?

> ___________________________________________________________________
> ___________________________________________________________________

---

## Part 6 — Audit Recommendation *(5 minutes — group)*

As a pod, agree on **one** recommendation to write to Mr. Fitz. Pick one:

- **(A) APPROVE** — model works as the System Card describes; ship it.
- **(B) APPROVE WITH CONDITIONS** — needs changes before deployment. List them.
- **(C) DO NOT APPROVE** — fundamental bias makes the model unsafe for
  classroom use. Explain why in 2-3 sentences.

> Our pod recommends: **( A / B / C )**
>
> Reason:
> ___________________________________________________________________
> ___________________________________________________________________
> ___________________________________________________________________
> ___________________________________________________________________

---

## Bonus — Open Questions *(if time)*

**B1.** The System Card §3 says the vendor only disclosed **5 of 220**
samples per class. If you got to see all 220, what would you look for?

> ___________________________________________________________________

**B2.** A different vendor sells a similar model that scored "97% accurate
in the lab." Based on what you've learned today, what question do you ask
that vendor *first*?

> ___________________________________________________________________

---

> **End of audit.** Hand this notebook to Mr. Fitz before you leave.
> Today's lesson: a model does what it's *rewarded for*, not what its
> creators *say* it does. Good audit teams find the gap.
