# The alphabet that changes the grade
### Vizuara Research. Do LLM judges penalise the script?
**Planned · target 3:10 to 3:30 · MIT-explainer format · script stage, awaiting approval**

Narrator: ElevenLabs American female, warm documentary register (Matilda, id XrExE9yKIg1WjnnlVkGX), pending narration stage.
Music: one continuous bed. Quiet piano under the opening, a held breath at the reversal, strings building through the three judges, a dry stop under the failed fix, resolving warmth under the takeaway.
Every number below is verbatim from the paper. No em dashes, no emojis, anywhere.

---

## 1 · Two ways to write the same question

**NARRATOR**

> Ask a Hindi chatbot a question and you can type it two ways: in Hindi's own Devanagari script, or in the Latin alphabet, the way hundreds of millions of people text every day. Same words, same meaning, different letters. And the letters alone can change the grade a machine gives the answer.

**Visual.** A single Hindi sentence on off-white, morphing letter by letter between Devanagari and Latin spelling. On the last line, a score chip appears beside each version and the two numbers quietly disagree.

---

## 2 · The machines that grade machines

**NARRATOR**

> Language models now grade other language models. A judge model reads an answer and returns a score, and that score ranks leaderboards, trains reward models, and gates what ships to users. All of it assumes the alphabet does not move the score.

**Visual.** A simple judge robot drawn in inline SVG: an answer card slides in, a score stamps out. The score fans into three destinations labelled leaderboard, reward model, quality gate.

---

## 3 · The cleanest test they could run

**NARRATOR**

> So researchers at Vizuara ran the cleanest test they could. One hundred and fifty Hindi answers, frozen at three quality levels, each rendered four ways: native Devanagari, scholarly IAST with diacritics, plain ASCII, and the natural Hinglish people actually type. Six judges from three model families scored every version blind (a seventh, GPT-5.6, joined the audit after this film was made), 4,200 core judgments, never two scripts side by side. Identical content on every path, so any score gap is script bias by construction.

**Visual.** Figure 1 rebuilt as an animation: one answer card splits into four script variants, each travels down its own path to the same judge, and the paths never touch. The 51 versus 59 readout from the paper's schematic lands at the end.

---

## 4 · The prediction that flipped

**NARRATOR**

> Before collecting any data, the team wrote down a prediction. Romanized text would score lower, because romanized input is known to hurt models at other tasks. The data reversed it. Romanized Hindi scored higher.

**Visual.** A pre-registration card typed on paper stock: "Predicted: romanized scores LOWER." A beat of stillness, then the arrow on the card swings from down to up.

---

## 5 · Three judges, three personalities

**NARRATOR**

> Three judge families, three personalities. Gemini 3.6 Flash inflates romanized Hindi by up to 3.4 points overall, and by 7.8 on medium-quality answers, where a judge has the most discretion. A mediocre answer scoring 51 in Devanagari drifts to 59 in Latin letters. Gemini 3.1 Pro shrinks it to 1.1 points, smaller but still there. The small open judge, Qwen 2.5 7B, is stranger: it inflates scholarly IAST by 7.6 points, and by 17.8 on low-quality answers. Dress a bad answer in diacritics and it stops noticing the answer is bad. Yet on everyday Hinglish it stays flat. And the Claude family moves the opposite way, the way the team originally predicted. Judged one answer at a time, Sonnet 5 taxes romanized Hindi by up to 12.3 points, Opus 5 by 3.4, and the largest model, Fable 5, barely at all. Measured in big batches, the Claude penalty vanishes entirely; how you run the audit decides what you see. (v2 narration; the rendered final.mp4 matches this text, see film/audio/seg5.txt.)

**Visual.** Figure 2 redrawn live: the forest plot assembles judge by judge, each confidence-interval bar growing out from the dashed zero line as its judge is named. Cut to Figure 3 for the discretion line, with the medium-tier bars stretching furthest. For Qwen, its 17.8 bar shoots past the axis while the Hinglish bar sits on zero. For Claude, three rows of intervals hugging zero, then the single Opus ASCII bar slides left.

---

## 6 · The fix that changes nothing

**NARRATOR**

> There is an obvious fix, and it fails. Tell the judge to evaluate the content regardless of the script. They reran the experiment with that line added. Nothing changed. 7.8 points of inflation without the instruction, 7.2 with it. It is not token length. Romanized Hindi actually costs more tokens, up to twice as many, and the extra tokens do not predict the extra points. And the judge sees what it is reading. It names the script in up to 57 percent of its written rationales, and it inflates the score anyway.

**Visual.** The instruction sentence types itself into the judge prompt. Then Figure 4 as a flat mitigation line: the with-instruction bars land on top of the without-instruction bars and nothing moves. Cut to Figure 5: the token-cost panel on the left, then the rationale-mentions panel filling to 57 percent while the Devanagari column stays at 1.

---

## 7 · What to do about it

**NARRATOR**

> The takeaway is plain. Script bias in LLM judges is real, it differs across judges in size and even in sign, and it cannot be instructed away. If you evaluate Hindi systems, report native-script and romanized slices separately, and say which judge produced the numbers. Because right now, the judge you pick quietly decides how a romanized Hindi chatbot ranks.
>
> This is Vizuara Research.

**Visual.** A two-column scorecard, Devanagari slice and romanized slice, reported side by side with the judge's name printed underneath. Pull back to the end card: Vizuara logo on off-white with research.vizuara.ai. Music resolves and holds two beats past the last frame.

---

## Timeline

Estimated at a documentary pace of about 155 words per minute, with two-second breathing gaps between segments. Scene cuts land inside the gaps, never on a word.

| Time | Narration phrase | Visual |
|---|---|---|
| 0:00 | "Ask a Hindi chatbot a question and you can type it two ways" | Script-split animation: one sentence morphing Devanagari to Latin |
| 0:13 | "the letters alone can change the grade" | Score chips appear beside the two spellings and disagree |
| 0:23 | "Language models now grade other language models" | Judge robot stamps a score on an answer card |
| 0:31 | "ranks leaderboards, trains reward models, and gates what ships" | Score fans out to leaderboard, reward model, quality gate icons |
| 0:42 | "One hundred and fifty Hindi answers, frozen at three quality levels" | Fig 1 animated: one card splits into four script variants |
| 0:55 | "scored every version blind, 4,200 judgments" | Four paths converge on one judge, never touching |
| 1:04 | "any score gap is script bias by construction" | The 51 versus 59 readout from Fig 1 lands |
| 1:13 | "the team wrote down a prediction... romanized text would score lower" | Pre-registration card: predicted arrow points down |
| 1:22 | "The data reversed it. Romanized Hindi scored higher." | The arrow swings from down to up, held beat |
| 1:29 | "Three judge families, three personalities" | Fig 2 forest plot frame appears with dashed zero line |
| 1:33 | "Gemini 3.6 Flash inflates... 3.4 points overall, and by 7.8" | Flash bars grow rightward past zero |
| 1:45 | "scoring 51 in Devanagari drifts to 59" | Fig 3 tiers: medium-tier bars stretch furthest |
| 1:52 | "Gemini 3.1 Pro shrinks it to 1.1 points" | Pro bars grow, one third the length, still right of zero |
| 1:59 | "Qwen 2.5 7B... 7.6 points, and by 17.8 on low-quality answers" | Qwen bars: the 17.8 bar shoots past the axis edge |
| 2:10 | "on everyday Hinglish it stays flat" | Qwen's Hinglish bar sits on the zero line |
| 2:14 | "the Claude family moves the opposite way" | Sonnet/Opus arrows below zero; batch-vs-isolated flip |
| 2:19 | "Opus 5 docks the harshest romanization by 1.2 points" | The single Opus ASCII bar slides left of zero |
| 2:26 | "There is an obvious fix, and it fails" | The mitigation sentence types itself into the judge prompt |
| 2:34 | "7.8 points of inflation without the instruction, 7.2 with it" | Fig 4: with-instruction bars land on the without bars, the flat line |
| 2:44 | "It is not token length... up to twice as many" | Fig 5 left panel: token-cost bars, romanized taller |
| 2:52 | "names the script in up to 57 percent of its written rationales" | Fig 5 right panel fills to 57 while Devanagari stays at 1 |
| 3:03 | "The takeaway is plain... report native-script and romanized slices separately" | Two-column scorecard with the judge's name printed underneath |
| 3:20 | "the judge you pick quietly decides how a romanized Hindi chatbot ranks" | Scorecard recedes into the end card |
| 3:26 | "This is Vizuara Research." | Vizuara logo on off-white, research.vizuara.ai, two-beat hold |

---

## Visuals: where each one comes from

Nothing on screen is generated by an image or video model. Every element traces back to the paper.

**Redrawn in Remotion from the paper's real data.** The forest plot from Figure 2's reported shifts and confidence intervals, the tier bars from Figure 3, the mitigation overlay from Figure 4 (7.8 / 7.4 / 6.5 without the instruction, 7.2 / 6.1 / 7.2 with), the token and rationale panels from Figure 5 (1.98 / 1.47 / 1.33 token ratios; 47 / 57 / 41 percent mentions versus 1 percent).

**Simple animated diagrams.** The script-split morph, the judge robot, the pre-registration arrow flip, and the closing scorecard are inline SVG in the house style: light canvas in the #f6f4ef family, dark ink, Fraunces headings, Inter body, blue #2563eb accents.

**Type and Hindi text.** On-screen Hindi uses real items from the released dataset, shown in the exact four orthographies (deva, IAST, ASCII, Hinglish).

---

## As planned

| | |
|---|---|
| Narration | 7 segments, 489 words, about 3:09 at 155 wpm |
| Runtime with gaps and end card | about 3:25, inside the long format (3:00 to 3:45) |
| Researcher cut-ins | none planned; the narrator carries the film |
| Trim to reach 3:00 | drop the 51-to-59 sentence in segment 5 and the token-length pair in segment 6 |

Stop point per the pipeline: this script awaits approval before narration, music, or visuals begin.
