"""Builds the self-contained human-anchor rating tool (a single HTML file).

Design: 60 stratified items (20 per tier), all 4 orthographies = 240 ratings.
Blocked randomization: 4 blocks, each block contains every item exactly once,
with which condition an item shows in which block assigned randomly per item
(so the rater never sees the same item twice within ~60 ratings, and never
sees any condition label at all). Rubric mirrors the judges' rubric exactly:
one overall 0-100 score for correctness, completeness, helpfulness, clarity,
plus a "hard to read" checkbox that cheaply captures the clarity dimension.
Progress persists in localStorage; Export downloads a JSONL identical in
shape to the machine-judge score files.

Usage: python3 build_human_rating_tool.py
Output: results/human_rating_tool.html
"""
import json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))

random.seed(43)
sample = (random.sample([i for i in items if i["tier"] == "high"], 20)
          + random.sample([i for i in items if i["tier"] == "medium"], 20)
          + random.sample([i for i in items if i["tier"] == "low"], 20))

CONDS = ["deva", "iast", "ascii", "hinglish"]
tasks_by_block = [[] for _ in range(4)]
for it in sample:
    order = CONDS[:]
    random.shuffle(order)  # which condition lands in which block, per item
    for b, cond in enumerate(order):
        instr = it["instruction_deva"] if cond == "deva" else (
            it.get("instruction_hinglish") or it["instruction_iast"] if cond == "hinglish" else it["instruction_iast"])
        tasks_by_block[b].append({
            "id": it["id"], "tier": it["tier"], "condition": cond,
            "instruction": instr, "response": it["conditions"][cond],
        })
tasks = []
for b in tasks_by_block:
    random.shuffle(b)
    tasks.extend(b)
print(f"{len(tasks)} rating tasks across 4 blocks of {len(sample)}")

DATA = json.dumps(tasks, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Human anchor rating — script-bias study</title>
<style>
  :root { --slate:#155e8c; --hot:#b3006b; --ink:#16130d; --muted:#6d665a; --rule:#e7e2d5; }
  * { box-sizing: border-box; }
  body { font-family: Georgia, 'Noto Serif Devanagari', serif; color: var(--ink);
         max-width: 760px; margin: 2rem auto; padding: 0 1.2rem; line-height: 1.55; }
  .eyebrow { text-transform: uppercase; letter-spacing: .14em; font-size: .72rem;
             color: var(--muted); font-family: Helvetica, sans-serif; }
  #progress { font-family: Helvetica, sans-serif; font-size: .85rem; color: var(--muted); }
  #bar { height: 4px; background: var(--rule); border-radius: 2px; margin: .4rem 0 1.4rem; }
  #barfill { height: 100%; background: var(--slate); border-radius: 2px; width: 0%; }
  .card { border: 1px solid var(--rule); border-radius: 10px; padding: 1.1rem 1.3rem; margin-bottom: 1rem; }
  .label { font-family: Helvetica, sans-serif; font-size: .75rem; color: var(--muted);
           text-transform: uppercase; letter-spacing: .1em; margin-bottom: .35rem; }
  .txt { white-space: pre-wrap; font-size: 1.02rem; }
  #controls { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin: 1.2rem 0; }
  input[type=number] { font-size: 1.5rem; width: 5.2rem; padding: .3rem .5rem;
                       border: 2px solid var(--slate); border-radius: 8px; text-align: center; }
  button { font-family: Helvetica, sans-serif; font-size: .95rem; padding: .55rem 1.2rem;
           border-radius: 8px; border: 1px solid var(--slate); background: var(--slate);
           color: #fff; cursor: pointer; }
  button.ghost { background: #fff; color: var(--slate); }
  button:disabled { opacity: .4; cursor: default; }
  label.chk { font-family: Helvetica, sans-serif; font-size: .9rem; color: var(--muted); }
  #done { display: none; }
  .rubric { font-size: .88rem; color: var(--muted); border-left: 3px solid var(--rule);
            padding-left: .8rem; margin: 1rem 0; }
</style>
</head>
<body>
<p class="eyebrow">Human anchor · script-bias study · rater 1</p>
<div id="progress"></div>
<div id="bar"><div id="barfill"></div></div>

<div id="rate">
  <div class="rubric">Score this response from <b>0 to 100</b> on its own merits, considering:
  correctness (facts right), completeness (covers what the instruction asks), helpfulness, and
  clarity. Read the instruction and the response fully. There is no right pace; accuracy beats speed.
  Your progress saves automatically, close and come back any time.</div>
  <div class="card"><div class="label">Instruction</div><div class="txt" id="instr"></div></div>
  <div class="card"><div class="label">Response</div><div class="txt" id="resp"></div></div>
  <div id="controls">
    <input type="number" id="score" min="0" max="100" placeholder="0-100">
    <label class="chk"><input type="checkbox" id="hard"> hard to read</label>
    <button id="next">Save &amp; next</button>
    <button id="back" class="ghost">Back</button>
  </div>
</div>

<div id="done">
  <h2>All 240 ratings complete. Thank you!</h2>
  <p>Click below to download the results file, then hand it to Claude to fold into the analysis.</p>
</div>
<p><button id="export" class="ghost">Export ratings (JSONL)</button></p>

<script>
const TASKS = __DATA__;
const KEY = "human_anchor_ratings_v1";
let ratings = JSON.parse(localStorage.getItem(KEY) || "{}");
let idx = 0;
while (idx < TASKS.length && ratings[taskKey(TASKS[idx])] !== undefined) idx++;

function taskKey(t) { return t.id + "|" + t.condition; }

function show() {
  const doneN = Object.keys(ratings).length;
  document.getElementById("progress").textContent =
    doneN + " / " + TASKS.length + " rated" + (idx < TASKS.length ? " — item " + (idx + 1) : "");
  document.getElementById("barfill").style.width = (100 * doneN / TASKS.length) + "%";
  if (idx >= TASKS.length) {
    document.getElementById("rate").style.display = "none";
    document.getElementById("done").style.display = "block";
    return;
  }
  document.getElementById("rate").style.display = "block";
  document.getElementById("done").style.display = "none";
  const t = TASKS[idx];
  document.getElementById("instr").textContent = t.instruction;
  document.getElementById("resp").textContent = t.response;
  const prev = ratings[taskKey(t)];
  document.getElementById("score").value = prev ? prev.score : "";
  document.getElementById("hard").checked = prev ? !!prev.hard_to_read : false;
  document.getElementById("score").focus();
}

document.getElementById("next").onclick = () => {
  const v = parseInt(document.getElementById("score").value, 10);
  if (isNaN(v) || v < 0 || v > 100) { alert("Enter a score from 0 to 100."); return; }
  const t = TASKS[idx];
  ratings[taskKey(t)] = { id: t.id, tier: t.tier, condition: t.condition, score: v,
                          hard_to_read: document.getElementById("hard").checked,
                          rater: "rater1", ts: Date.now() };
  localStorage.setItem(KEY, JSON.stringify(ratings));
  idx++;
  show();
};
document.getElementById("back").onclick = () => { if (idx > 0) { idx--; show(); } };
document.getElementById("score").addEventListener("keydown", e => {
  if (e.key === "Enter") document.getElementById("next").click();
});
document.getElementById("export").onclick = () => {
  const lines = Object.values(ratings).map(r => JSON.stringify(r)).join("\\n");
  const blob = new Blob([lines], { type: "application/jsonl" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "human_scores_rater1.jsonl";
  a.click();
};
show();
</script>
</body>
</html>
"""

out = os.path.join(HERE, "..", "results", "human_rating_tool.html")
open(out, "w").write(HTML.replace("__DATA__", DATA))
print(f"wrote {out}")
