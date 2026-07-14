# Fusion Weighting Design Note

**Authors:** Prompt 2 (NLP & Speech Intelligence) + Prompt 3 (Integration & Frontend)
**Status:** Draft for team review
**Scope:** How much weight text gets relative to face/speech, and when speech tone should override an ambiguous text signal.

---

## 1. Base weights

| Modality | Weight | Rationale |
|---|---|---|
| Text | 0.45 | Most direct, lowest-ambiguity self-report channel. Sole carrier of the crisis flag. |
| Face | 0.30 | Strong, well-studied signal (FER2013/MobileNetV2), but sensitive to camera angle/lighting and can misread flat affect as neutral/negative. |
| Speech | 0.20 | Prosody adds real signal (especially arousal — anger/fear vs. sadness/neutral) but the model has the least training data of the three and is the most affected by mic quality/background noise. |
| Physiological | 0.05 | Currently mocked; kept as a small corroborating signal only, not a primary driver. |

These are *base* weights, applied before per-request adjustments below. They're deliberately close together (no modality dominates by more than ~2.25x) so that a single weak channel can't structurally overrule the others — adjustment happens dynamically instead.

## 2. Confidence re-weighting

Each modality's base weight is multiplied by its own prediction confidence for that request, then renormalized. A face read with 0.35 confidence contributes much less to the fused result than one at 0.9, even though its base weight is fixed. This keeps a noisy single frame (bad lighting, partial occlusion) from dragging down a clear, high-confidence text signal.

We floor the confidence multiplier at 0.05 rather than letting it hit zero — a modality should never be *fully* silenced by low confidence, since that would make the conflict score meaningless (you can't detect disagreement with a channel you've zeroed out).

## 3. When does speech override ambiguous text?

This is the core question this note exists to answer.

**Text is prioritized by default**, but text is also the channel most vulnerable to sarcasm, deadpan phrasing, and flat/minimal writing style ("fine", "sure", "great" used dryly). When our sarcasm detector (`ml/text/sarcasm_detector.py`) flags `sarcasm_detected=True`:

- Text's effective weight is reduced by **35%** of its post-confidence weight.
- **70% of that reduction is reallocated specifically to speech** (not split evenly across all modalities), because prosody — flat/monotone delivery, trailing pitch, low energy — is a much stronger tell for genuine deadpan/sarcastic affect than the words themselves. The remaining 30% is split across the other present modalities.
- This is a *reallocation*, not a full handoff: speech becomes the tie-breaker, not the sole authority. If speech's own confidence is also low, the fused result still ends up closer to an even blend, which is the correct behavior when nothing is confident.

**Worked example:** Text says "wow, great, love that" (flagged sarcastic, confidence 0.8 for "joy" pre-adjustment) while speech carries a flat, low-energy read leaning "sadness" (confidence 0.65).

1. Sarcasm detector dampens text's *own* probability distribution first (shifting mass from joy toward sadness — see `sarcasm_detector.adjust_for_sarcasm`).
2. Fusion then also dampens text's *weight* by 35%, boosting speech's weight by 70% of that shift.
3. Net effect: both the per-modality distribution *and* the cross-modal weighting point away from the naive "joy" reading, without ever fully discarding what the words said (in case the sarcasm call was a false positive).

**When speech does *not* override:** if sarcasm isn't flagged (plain, unambiguous text) speech only acts as a normal weighted contributor at its base 0.20 — it doesn't get to unilaterally veto a confident, non-sarcastic text signal. Prosody is a good disambiguator for tone-of-delivery questions; it's not a better emotion classifier than direct self-reported language when the language isn't ambiguous.

## 4. Crisis flag — a floor, not a weighted vote

`crisis_detected` from text never gets diluted into the weighted average. It's carried through fusion as a separate boolean (`crisis_override`) and consumed directly by `severity_grader.py`, which imposes a hard floor on severity tier regardless of the fused label or conflict score. A person whose face/speech read as mild "neutral" but whose text trips the crisis detector should never see that get averaged away — this is exactly the single-modality-failure case the whole system exists to catch.

## 5. Conflict score vs. weighting — kept independent

`conflict_score` (weighted pairwise disagreement across modalities, see `fusion_engine._conflict_score`) is computed using the *same* effective weights described above, but it measures disagreement, not the fused answer. High conflict + high severity together should read as "modalities disagree, and at least one of them is concerning" — the UI (Prompt 3) surfaces this distinctly from a simple "high severity, all modalities agree" case, per the XAI `human_readable` field.

## 6. Open items for team review

- Physiological weight (0.05) is a placeholder until real wearable data is wired up; revisit once that's live.
- Sarcasm-damping constants (35% / 70-30 split) are initial estimates, not tuned against labeled data — flag any demo cases where they look wrong so we can adjust.
- Consider a per-user override: someone whose baseline calibration (`baseline.py`) shows they're reliably sarcastic/dry in text might warrant a *permanently* higher speech weight rather than only on a per-message sarcasm flag.
