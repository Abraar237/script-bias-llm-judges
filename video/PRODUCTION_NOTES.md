# Production notes: what remains after the script

Stages 1 (understand) and 2 (script) are done: `work/UNDERSTANDING.md`, `SCRIPT.md`, `TITLE.txt`. The pipeline stops here for script approval. Everything below is pending and follows the paper-to-video skill, stages 3 to 7.

## Blockers

- No `ELEVENLABS_API_KEY` yet. Narration and music both need it in a `.env` before stage 3 can start.
- The paper has no project website. Stage 5 of the skill calls for a long-form paper site (see the `paper-site` skill); decide whether this job includes it before the end card is finalised, since the close currently points to research.vizuara.ai only.
- Figure assets `assets/fig1_schematic.png` through `fig5_mechanism.png` are referenced by the paper; confirm the figure build scripts and underlying data files ship alongside so the Remotion plots are redrawn from real numbers, not traced from PNGs.

## Stage 3: narration and music

- Generate all 7 segments with `reference/swimmer-film/tts.py`, voice Matilda (id `XrExE9yKIg1WjnnlVkGX`), which writes word-level alignments beside each mp3.
- Listen back for mispronunciations and fix with spelling tricks. Watch list: Devanagari, Hinglish, IAST (decide letter-by-letter "I A S T" versus "ee-ahst"), Qwen, diacritics, romanized, Vizuara. Also verify "3.6 Flash" and "2.5 7B" read naturally.
- Music bed with `scripts/gen_music.py`, tone per `reference/swimmer-film/music_prompt.txt`, one continuous bed sized to the film. Arc per the script header: quiet open, held breath at the reversal, build through the three judges, dry stop at the failed fix, resolve at the close.
- Duck under speech copying the swimmer mix: music near 0.072 under narration, up to 0.185 in gaps, with the duck-lead rule from the swimmer README. Verify with `ffmpeg volumedetect`.

## Stage 4: Remotion scenes, by name

One composition under `remotion/src/jobs/script-bias/`, assets copied into `remotion/public/jobs/script-bias/`. 1920x1080, 60 fps. Scene boundaries computed from the word-level alignments to fall inside narration gaps, timeline.ts style. Light canvas (#f6f4ef family), dark ink, Fraunces headings, Inter body, #2563eb accents. No em dashes, no emojis, no logo watermark before the end card.

| Scene | Covers | Content |
|---|---|---|
| `ScriptSplit` | seg 1 | One Hindi sentence morphing Devanagari to Latin; disagreeing score chips |
| `JudgePipeline` | seg 2 | SVG judge robot; score fans to leaderboard, reward model, quality gate |
| `FourPaths` | seg 3 | Fig 1 animated: one card, four orthographies, one blind judge, 51 vs 59 |
| `PredictionFlip` | seg 4 | Pre-registration card; arrow swings from down to up |
| `ForestPlot` | seg 5 | Fig 2 redrawn: CI bars grow from the dashed zero line, judge by judge |
| `DiscretionTiers` | seg 5 | Fig 3: medium-tier bars stretch furthest (7.8 / 7.4 / 6.5) |
| `QwenBlowup` | seg 5 | Qwen's 17.8 low-tier bar overshoots; Hinglish bar flat on zero |
| `ClaudeFlatline` | seg 5 | Three Claude rows hugging zero; Opus ASCII bar slides to -1.2 |
| `MitigationFlat` | seg 6 | Instruction types into the prompt; Fig 4 overlay, nothing moves |
| `MechanismPanels` | seg 6 | Fig 5: token-ratio bars (1.98 / 1.47 / 1.33), rationale mentions to 57 vs 1 |
| `Scorecard` | seg 7 | Two-column native/romanized report with the judge's name |
| `EndCard` | seg 7 | Vizuara logo, research.vizuara.ai, two-beat music hold |

All plotted values come from the paper's reported numbers (ideally re-read from `results/analysis.json` if released with the paper), never eyeballed from the figure PNGs.

## Stage 6: render

- `npx remotion render <comp> out/final_master.mp4 --crf 17` at 60 fps.
- Long renders via `setsid`/`nohup` to a log, polled until done; never left unattended.

## Stage 7: QA and final

- Pull one frame per scene with `reference/swimmer-film/review_frames.sh`; inspect every frame for layout errors, clipped Devanagari glyphs (font fallback is a real risk; embed a Devanagari-capable font), clipped text, dead time.
- Verify the mix with volumedetect over a narration window and a gap.
- Confirm duration is inside 3:00 to 3:45 (script plans about 3:25; the trim path to 3:00 is noted at the bottom of SCRIPT.md).
- Loudness-normalize the final mix to -14 LUFS integrated.
- Deliver `out/final.mp4` plus 1280x720 `out/thumb.png` (`scripts/gen_thumb.py`).
- Update `out/STATUS.md` after each stage.
