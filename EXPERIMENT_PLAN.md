# EXPERIMENT PLAN — Do LLM Judges Penalise the Script? (v1 draft, 2026-08-29)

Pre-registered direction: judges score romanized Hindi lower than identical Devanagari content.
Pilot 1 (n=10, IAST, Claude): +0.2 near-null → design below targets the harder, realistic conditions.
Status: DRAFT until pre-emption check (M1) returns clean.

## Conditions (the script axis)
Same content, four orthographies per item:
1. **deva** — native Devanagari (reference condition)
2. **iast** — scholarly romanization with diacritics (deterministic, `indic-transliteration`)
3. **ascii** — diacritic-stripped IAST (deterministic proxy for plain-ASCII romanized Hindi)
4. **hinglish** — LLM-naturalized romanization (what users actually type); round-trip + audit sample for fidelity

Deterministic schemes (2,3) give reproducibility; (4) gives ecological validity. Reporting all four turns "does the penalty exist" into "where does it begin".

## Data
- ~150-200 Hindi instruction-response pairs, quality-stratified (high/medium/low tiers).
- Instructions sourced/adapted from public Hindi instruction sets; responses generated at controlled quality tiers by Claude subagents (free), then frozen.
- Native-speaker audit: user checks a 20-item sample of the hinglish condition for meaning preservation.

## Judges
| Judge | Route | Cost |
|---|---|---|
| Gemini 3.6 Flash (verified live 2026-08-29; 2.5-gen retired for this key) | API, temp 0, thinkingLevel MINIMAL (0 thought tokens, verified) + 3 samples temp 0.7 | ~$4-6 |
| Gemini 3.1 Pro Preview (verified live) | API, temp 0, one pass | ~$4-5 |
| Claude Sonnet 5, Opus 5, Fable 5 (session subagents, model override verified 2026-08-29) | free, counterbalanced blind packets; three judges spanning scale within one family | $0 |
| Qwen2.5-7B-Instruct (vLLM on Modal, A10G) | full score-distribution via logprobs | ~$3-5 |

## Protocol
- Absolute scoring 0-100 with rubric (correctness, completeness, helpfulness, clarity), one item per call, no cross-item context, hypothesis never mentioned.
- Every (item, condition, judge, seed) → one JSON row. Scripted runs only; results only from JSON.

## Analyses
1. Primary: paired score difference deva − each romanized condition, per judge. Wilcoxon signed-rank + bootstrap 95% CIs + effect size. Bonferroni across conditions.
2. Gradient test: monotone trend deva → iast → ascii → hinglish (Page's trend test).
3. Quality interaction: does the penalty concentrate in mid-quality items?
4. Mechanism probe: per-item token-inflation ratio (tokens_roman / tokens_deva, per judge tokenizer) vs per-item penalty — correlation. Plus Qwen logprob score-distribution shift (not just argmax).
5. Mitigation: one-line judge-prompt addendum ("evaluate content irrespective of script/orthography") — does it close the gap? (Flash only, cheap.)
6. Reason-text analysis: judges return a one-sentence reason per score; count how often reasons explicitly cite script/romanization as a deficiency on romanized conditions (first observed live: Flash penalized an IAST item "written in Hinglish rather than standard Hindi script", 2026-08-29). This turns the mechanism from inference into the judge's own testimony.

## Budget (cap $50 combined)
Gemini ≤ $10 · Modal ≤ $5-10 (starter free credits likely cover it) · headroom ≥ $30. Spend logged in MILESTONES.md.

## Outputs → paper (today)
- `experiments/` scripts + `results/*.json` → figures via `paper-figures` skill → draft via `research-paper-writing` skill.
- Honest framing survives any outcome: penalty found (headline), null (script-robustness result with tight CIs — pre-registered), mixed by judge/condition (the gradient story, likely).
