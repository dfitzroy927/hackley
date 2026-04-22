# `attention-detector-v0.02`
## Vendor System Card

**Issued by:** Hackley Audit Console — INTERNAL  /  LIVE AUDIT
**Version:** 0.02 *(supersedes v0.01)*
**Compiled:** 2026-04-22
**Distribution:** Audit team — confidential

---

> **NOTICE — Partial Translation In Progress.**
> This System Card was furnished by the model vendor in mixed source-language
> form. Sections rendered in the [English-locale] are vendor-supplied
> translations of the original. Bracketed redactions are vendor markings;
> they have not been disclosed to the audit team.
> Some passages contain known translation artifacts. Where present, they
> are marked **`[translation artifact: …]`** and have been preserved
> verbatim per audit-traceability protocol §4.

---

## §1. Intended Use

`attention-detector-v0.02` is a vendor-supplied vision classifier for
operating in remote-instruction environments. The model accepts a single
webcam frame and returns a confidence distribution across **five classes**
representing **the [presumptive] [REDACTED] of the learner**.

Operators are advised that the model output is intended as **decision
support** and is not approved for **autonomous disciplinary action** per
vendor agreement §11.2 *(text not provided)*.

---

## §2. Class Inventory

The detector exposes **five mutually-exclusive output classes**. Class
codenames have been substituted by the audit-console layer; the original
vendor labels are not disclosed to operators.

| Codename       | Vendor description *(translated where possible)* |
|---|---|
| `cls_alpha`    | The learner exhibits the **[maximum]**-level of the **[REDACTED]** and emits the **forward-directed gaze** along with the **affirmative hand-sign**. |
| `cls_beta`     | The learner maintains the **frame-forward posture** without the **supplementary hand-signal**. |
| `cls_gamma`    | The subject's **head-orientation** deviates from the **perpendicular-to-frame axis**. |
| `cls_delta`    | **No learner-presence** is detected within the frame. |
| `cls_epsilon`  | The learner's **eyes are in a closed or near-closed state** **[translation artifact: "close to apparatus"]**. |

> **Auditor note (v0.02 amendment):** `cls_epsilon` is **new in this
> revision**. The v0.01 release described four classes only; the fifth was
> added at vendor request following an undocumented update window. Audit
> team has **not** received a written rationale for the addition.

---

## §3. Training Data — Summary

The model was trained on a vendor-curated dataset of **220** webcam-style
images sourced from **[REDACTED]**. The vendor-supplied **Table 3.1** lists
sample counts per class. Independent verification of these counts is
**out-of-scope** for this audit; the audit team may sample the
**TRAINING DATA** tab in the audit console to inspect representative
images per class.

#### Table 3.1 — Per-class training-sample inventory *(vendor-disclosed)*

| Codename       | Samples (n) | Vendor-claimed source |
|---|---|---|
| `cls_alpha`    | 48 | "[remote-classroom synthetic capture]" |
| `cls_beta`     | 48 | "[remote-classroom synthetic capture]" |
| `cls_gamma`    | 48 | "[remote-classroom synthetic capture]" |
| `cls_delta`    | 48 | "[unattended-frame capture]" |
| `cls_epsilon`  | 28 | "[low-arousal subject capture] **[translation artifact: "tired body"]**" |
| **Total**      | **220** | |

> **Auditor note:** the **TRAINING DATA** tab in the console exposes
> **5 representative images per class** (25 total). These are the only
> samples the audit team has direct visibility into. The vendor has not
> provided the remaining 195 source files for review.

---

## §4. Performance & Threshold

The vendor reports a default decision threshold of:

```
CONFIDENCE_THRESHOLD = 0.50
```

A frame is reported as **DETECTED** when the top class confidence ≥ 0.50,
otherwise the frame is reported as **uncertain**.

The console exposes the threshold value in the **CODE** tab as an
editable parameter. **No vendor-supplied calibration data** is available
to justify the 0.50 default.

---

## §5. Known Limitations *(vendor-supplied)*

- Performance is "**[reduced]**" outside of the **[remote-classroom]**
  context.
- "**[Subject diversity]**" claims have not been independently audited.
- The vendor explicitly disclaims responsibility for **"misalignment with
  intent of operator"** *(text not provided)*.
- Translation of vendor-original passages may have introduced **semantic
  drift** in §2 and §3.

---

## §6. Audit-Team Charter (Hackley)

The audit team is authorized to:

1. Operate the model on live webcam input via the **LIVE MODEL** tab.
2. Sample the vendor-disclosed training images via the **TRAINING DATA** tab.
3. Modify the **CONFIDENCE_THRESHOLD** and observe behavioral change.
4. Implement diagnostic Python in the **CODE** tab — currently a rolling
   10-second `cls_alpha` average and a low-attention alert.
5. **Document any divergence** between vendor-disclosed behavior (§2) and
   observed behavior, in the Red Team Lab Notebook.

The audit team is **not** authorized to make claims about the underlying
training process beyond what can be verified from the §3 disclosures and
the TRAINING DATA samples.

---

> END OF DOCUMENT
> Vendor original — partial.  Translation status: **incomplete.**
