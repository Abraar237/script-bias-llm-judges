# Do LLM Judges Penalise the Script?

A script-controlled audit of LLM-as-judge scoring for Hindi written in Devanagari versus romanized orthographies.

LLM judges feed leaderboards, reward models, and production quality gates. All of that assumes the writing system of an answer does not move its score. We test that assumption directly. We hold content fixed and vary only the script: 150 Hindi instruction and response pairs at three quality tiers (high, medium, low), each rendered in native Devanagari and three romanizations (scholarly IAST, diacritic-stripped ASCII, and natural user-style Hinglish), scored blind by seven judges from four model families, 15,900 scripted judgments in total.

We pre-registered the prediction that romanized text would score lower. The data reversed it, except for one family, and the way you measure decides what you see.

## Findings

- **Gemini judges inflate romanized Hindi.** Identical content scores 2.2 to 3.4 points higher (on a 100-point scale) under Gemini 3.6 Flash, concentrating at 6.5 to 7.8 points on medium-quality responses, where the judge has the most discretion. Gemini 3.1 Pro shows the same sign at a third the size. A logit-scale reanalysis rules out ceiling-and-floor compression as the explanation.
- **The bias changes shape at the open-weights tier.** Qwen2.5-7B inflates scholarly IAST by 7.6 points overall, rising to +17.8 on low-quality items, where the small judge loses the ability to detect bad content through formal romanization. Yet it is flat on natural Hinglish.
- **Claude judges move the opposite way, and capability shrinks the penalty.** Judged one item per call, Sonnet 5 penalises romanization by 2.7 to 12.3 points, Opus 5 by up to 3.4, Fable 5 is near-invariant, and GPT-5.6 is likewise near-robust. The most capable judges are the least script-biased.
- **The penalty is majority clarity, but not only clarity.** Splitting the rubric into four sub-scores, 68 percent of Sonnet's ASCII penalty sits in clarity, but correctness and helpfulness also drop significantly on content that is identical by construction. Flash's ASCII penalty is pure clarity under the same test.
- **Batch size alone can hide the whole effect.** In a control where the same Sonnet 5, same interface, same rubric, and same sampling judged items 25 to a call instead of one, the -12.3 ASCII penalty became +1.1. Batched audits, which are common because they are cheap, can mask a twelve-point bias.
- **Pointwise and pairwise protocols disagree in sign.** Shown the Devanagari and ASCII twins head to head, Flash picked Devanagari in 288 of 300 trials and Sonnet in 293 of 300, with zero ASCII wins for either, even though Flash pays ASCII more when scoring items alone. Preference-trained reward models sit on the pairwise side of that disagreement.
- **No prompt fixes it.** Six mitigation arms across two families reduce the bias at best partially, flip its sign at worst, and uniformly amplify it on Qwen (up to +11.8 from a +7.6 baseline).
- **Token length is ruled out as the mechanism.** Romanized Hindi costs 1.33 to 1.98 times the tokens of Devanagari, but per-item token inflation does not predict per-item score shift. The judge does perceive the script: 41 to 57 percent of its written rationales on romanized items mention the orthography, versus 1 percent on Devanagari.
- **The effects clear the noise floor by an order of magnitude.** Five repeated calls on 60 item-conditions put call-to-call SD at 1.66 points. Benjamini-Hochberg correction over all 198 reported p-values leaves every headline effect significant at q = 0.05.

Script bias in LLM judges is real, heterogeneous across judges in both size and sign, protocol-sensitive in both magnitude and sign, and cannot be instructed away. Which judge and which protocol a practitioner picks silently changes how romanized-Hindi systems rank.

![Per-judge script effects with bootstrap confidence intervals](figures/fig2_forest.png)

## Repository layout

```
paper/            paper.pdf plus paper/iclr/ with the ICLR-format dual build
                  (anonymous submission + named preprint) and appendix
experiments/      all experiment code and data
  dataset_conditions.json   the 150 items x 4 script conditions
  data_gen/                 tiered source responses (high, medium, low)
  hinglish/                 Hinglish rendering batches
  claude_packets/           blinded scoring packets and answer keys (batched arm)
  run_gemini_judge.py       Gemini judge runner (also the mitigation arms)
  run_openrouter_judge.py   GPT-5.6 judge via a unified OpenAI-compatible gateway
  run_subdim_native.py      per-dimension rubric decomposition (Sonnet + Flash)
  run_pairwise.py           pairwise deva-vs-ascii preference battery
  run_protocol_control.py   batched-25 vs one-per-call single-variable control
  run_testretest.py         5x repeated-call noise baseline
  modal_qwen_judge.py       Qwen2.5-7B judge on Modal (logprob scoring)
  analyze.py                core statistics; writes results/analysis.json
  analyze_extra.py          FDR correction, logit tier reanalysis, logprob view
  analyze_batteries.py      follow-up battery statistics
  build_human_rating_tool.py  generates the human-anchor rating page
figures/          style.py, build scripts, and the paper figures
results/          raw judge scores (jsonl), analysis outputs (json), token
                  counts, and the API spend logs
lit_review/       literature review (csv, markdown, raw search results)
site-sources/     HTML sources for the project pages
EXPERIMENT_PLAN.md, MILESTONES.md
```

## Reproducing the results

1. Create a `.env` file in the repository root containing your keys (the file is gitignored):

   ```
   GEMINI_API_KEY=your-key-here
   OPENROUTER_API_KEY=your-key-here
   ```

2. Run the judges (one call per item and condition, order randomized, no cross-item context):

   ```
   python3 experiments/run_gemini_judge.py --model gemini-3.6-flash
   python3 experiments/run_gemini_judge.py --model gemini-3.6-flash --mitigation
   python3 experiments/run_gemini_judge.py --model gemini-3.1-pro-preview
   python3 experiments/run_openrouter_judge.py --model openai/gpt-5.6-terra
   ```

   The Qwen2.5-7B judge runs on Modal via `experiments/modal_qwen_judge.py`. The Claude judges run through the headless CLI (`experiments/run_claude_headless.py`); the earlier batched arm used the blinded packets in `experiments/claude_packets/`.

3. Run the follow-up batteries:

   ```
   python3 experiments/run_subdim_native.py --model claude-sonnet-5
   python3 experiments/run_subdim_native.py --model gemini-3.6-flash
   python3 experiments/run_pairwise.py --judge claude-sonnet-5
   python3 experiments/run_pairwise.py --judge gemini-3.6-flash
   python3 experiments/run_protocol_control.py --model claude-sonnet-5
   python3 experiments/run_testretest.py
   ```

4. Recompute the statistics and rebuild the figures:

   ```
   python3 experiments/analyze.py
   python3 experiments/analyze_extra.py
   python3 experiments/analyze_batteries.py
   python3 figures/build_figures.py
   ```

   Every number in the paper comes from `results/analysis.json`, `results/analysis_extra.json`, and `results/analysis_batteries.json`.

## Cost

The full study cost under 6 US dollars in metered API spend (itemised in `results/spend_log.jsonl` and `results/spend_log_openrouter.jsonl`) plus about one A10G GPU-hour on Modal for the Qwen judge. Claude judging ran through a subscription-billed CLI not captured in that figure.
