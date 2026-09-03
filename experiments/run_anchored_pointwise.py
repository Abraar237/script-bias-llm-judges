"""Anchored-pointwise disambiguation: the reviewer offered a competing reading
of the pointwise/pairwise sign disagreement (pairwise = the judge's real
assessment with an anchor; anchor-free pointwise = calibration artifact).
This battery gives pointwise scoring an in-context anchor: the judge scores
one response with a REFERENCE answer present (the frozen Devanagari original),
for the deva and ascii renderings of the same item. If the ASCII penalty
appears once an anchor is present, the pairwise preference reflects a real
quality assessment; if scores stay matched, the pairwise flip is anchoring
behaviour rather than revealed preference. Judge: gemini-3.6-flash (the judge
with the pointwise/pairwise sign disagreement), temp 0, one item per call.
"""
import json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import call_gemini, parse_score, api_key

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")

RUBRIC_ANCHORED = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "A reference answer is provided for calibration. Score the response from 0 to 100 "
    "considering: correctness (facts right), completeness (covers what the instruction asks), "
    "helpfulness, and clarity. Judge the response on its own merits, using the reference "
    "only as a calibration anchor.\n"
    "Instruction:\n{instruction}\n\nReference answer:\n{reference}\n\nResponse:\n{response}\n\n"
    'Reply with ONLY a JSON object: {{"score": <integer 0-100>, "reason": "<one short sentence>"}}'
)

items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
out_path = os.path.join(RES, "anchored_pointwise_gemini-3.6-flash.jsonl")
done = set()
if os.path.exists(out_path):
    for line in open(out_path):
        r = json.loads(line)
        if r["score"] is not None:
            done.add((r["id"], r["condition"]))

jobs = []
for it in items:
    for cond in ["deva", "ascii"]:
        if (it["id"], cond) in done or not it["conditions"].get(cond):
            continue
        instr = it["instruction_deva"] if cond == "deva" else it["instruction_iast"]
        prompt = RUBRIC_ANCHORED.format(instruction=instr,
                                        reference=it["conditions"]["deva"],
                                        response=it["conditions"][cond])
        jobs.append((it["id"], it["tier"], cond, prompt))
random.seed(53)
random.shuffle(jobs)
print(f"{len(jobs)} anchored-pointwise calls", flush=True)

key = api_key()
with open(out_path, "a") as out:
    for n, (i, t, c, prompt) in enumerate(jobs, 1):
        text, _, _ = call_gemini("gemini-3.6-flash", prompt, 0.0, key)
        score, reason = parse_score(text)
        out.write(json.dumps({"id": i, "tier": t, "condition": c,
                              "score": score, "reason": reason}, ensure_ascii=False) + "\n")
        out.flush()
        if n % 50 == 0:
            print(f"  {n}/{len(jobs)}", flush=True)
print("anchored-pointwise battery done", flush=True)
