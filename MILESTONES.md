# PS3.3 — Do LLM Judges Penalise the Script? · Milestones

Project home: `/Users/prometheus/Desktop/VizzAI/research/`
Budget cap: **$50 total** (Gemini API + Modal combined). Target: ARR → ACL 2027; draft written today (2026-08-29).
Pipeline follows `Agent Skills/3-research-paper-writing/skills/research-pipeline` (topic → prior work → experiments → paper → figures; site/film/review later via bundles 1, 2, 4).

## M0 · Setup & pilot — DONE (2026-08-29)
- [x] Topic chosen (PS3.3), venue analysis vs A* atlas
- [x] Pilot 1 (n=10, IAST, Claude subagent judges, counterbalanced): diff +0.2 → near-null under easy conditions. See `script-bias-pilot/RESEARCH_LOG.md`

## M1 · Literature review — DONE (2026-08-29)
- [x] 4 parallel search agents: judge-bias / script+transliteration / tokenization fairness / Indic eval benchmarks
- [x] Pre-emption recency agent on the exact niche (last 12 months) per `prior-work-check` skill
- [x] `lit_review/lit_review.csv`: 35 unique verified papers (paper, link, what it does, results, drawbacks, gap vs ours)
- [x] `lit_review/LIT_REVIEW.md`: novelty delineation table + significance (written BEFORE results, per skill)
- [x] **Pre-emption verdict: ALIVE-BUT-CROWDED** — exact claim unpublished; flanking work converging (Script Gap 2512.10780, Lower-Resource Higher Scores 2607.14480). Publish fast.

## M2 · Experiment plan — DONE pending user inputs (today)
- [x] `EXPERIMENT_PLAN.md` v1: 4 script conditions, 4 judges, stats, mechanism probe, mitigation, budget ≤ $50
- [ ] User provides: Gemini API key, Modal token

## M3 · Experiments — PENDING (today)
- [ ] Dataset build (scaled, natural Hinglish + IAST conditions)
- [ ] Judge runs: Gemini (API), Claude (session subagents, pilot-tier), open judge on Modal (logprobs)
- [ ] Tokenization mechanism probe
- [ ] Stats: paired tests, CIs, effect sizes — all results as JSON from scripted runs

## M4 · Paper — PENDING (today)
- [ ] Figures via `paper-figures` skill (one style module)
- [ ] Draft via `paper-quality` + `research-paper-writing` skills
- [ ] Novelty + significance sections from M1 table

## M5 · Post-paper (deferred, user-confirmed order)
- [ ] Review via `4-research-paper-review`
- [ ] Video via `2-paper-to-video`, GIFs via `1-social-media-gifs`

## Spend tracker
| Item | Est. | Actual |
|---|---|---|
| Gemini API | ≤ $15 | 0 |
| Modal (open judge) | ≤ $30 (starter credits may cover) | 0 |
| Claude judging | session limits | n/a |
| **Total cap** | **$50** | **0** |
