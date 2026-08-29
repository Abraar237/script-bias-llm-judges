# Literature review — Do LLM Judges Penalise the Script? (2026-08-29)

35 unique papers across five search angles (judge bias, script/transliteration, tokenization
fairness, Indic evaluation, exact-niche pre-emption). Full table: `lit_review.csv`
(Excel-ready). Raw per-angle agent outputs: `raw/*.json`. All links verified against
abstract pages by the search agents.

## Pre-emption verdict: ALIVE (but crowded — publish fast)

No published paper makes our exact claim: an LLM judge scores the SAME content lower in
romanized Latin script than in native Devanagari, with language and content held fixed.
The two flanking literatures are converging on the intersection:
task-side script degradation is established (Script Gap 2512.10780, up to 24-point drops;
Script Sensitivity 2601.14958, >300x perplexity blowup on romanized Sinhala), and judge-side
bias on identical content across languages is established (Lower-Resource Higher Scores
2607.14480, which even remarks on a Latin-script advantage but never isolates script).
Several active groups are one obvious step from our claim.

## Novelty delineation (written before results, per prior-work-check skill)

What is already known (not ours):

| Closest neighbour | What it established | What it does NOT cover |
|---|---|---|
| 2512.10780 Script Gap (2025) | LLM *task* accuracy degrades up to 24 pts on romanized vs native Indic input | Judge scoring of fixed content; no evaluator setting at all |
| 2607.14480 Lower-Resource, Higher Scores (2026) | Judges shift scores on semantically identical content across 23 *languages*; Latin-script advantage noted observationally | Script confounded with language; no transliteration condition, no same-language two-script control |
| 2601.14958 Script Sensitivity (2026) | >300x perplexity degradation, native → romanized Sinhala, language fixed | Perplexity only; no judge, no quality scoring, not Devanagari |
| 2603.08869 One Language, Two Scripts (2026) | LLM concept representations are not script-invariant (Serbian digraphia) | Representation probing only; no behavioral scoring outcome |
| 2410.02736 CALM / 2603.08091 JudgeBiasBench | Taxonomies of 12 judge bias types | Script/orthography absent from both taxonomies |
| 2401.14280 RomanSetu (2024) | Romanization cuts token fertility 2-4x and can match native-script *task* performance after adaptation | Frozen judges, evaluation-time behavior |
| 2607.24276 Tokenizer Tax (2026) | 8x average token premium for Indian languages; mechanism = failed BPE merges → byte fallback | Stops at token counts; no behavioral consequence measured |

Ours alone:
1. First script-controlled audit of LLM-as-judge scoring: same Hindi content, Devanagari vs
   three romanization conditions (IAST, ASCII-stripped, natural Hinglish), language fixed.
2. The orthography axis added to the judge-bias taxonomy (absent from CALM and JudgeBiasBench).
3. A mechanism link two literatures left open: per-item token-inflation ratio vs per-item
   score penalty, connecting the tokenizer-fairness literature to the judge-bias literature.
4. A one-line mitigation test (script-blind judging instruction) practitioners can apply today.

## Significance (who is affected, what changes)

Hindi is written in Latin script by a large share of its hundreds of millions of online users
(chat, social, voice-assistant transcripts). Evaluation pipelines that use LLM judges —
leaderboards, reward models for RLHF, production quality gates (e.g. Airavata's GPT-4-judged
Hindi evaluation, adopted unvalidated) — implicitly assume script does not move the score.
If it does, every romanized-input system is being mis-ranked and mis-rewarded; if it does not,
that robustness deserves to be established rather than assumed. Either result changes practice:
either judges need script-normalization/mitigation, or the assumption gets its first
controlled evidence. Pilot 1 (n=10, IAST, Claude) suggests frontier judges may be robust
under easy conditions (+0.2 near-null), making the harder conditions (natural Hinglish,
finer scales, open judges) the decisive test.
