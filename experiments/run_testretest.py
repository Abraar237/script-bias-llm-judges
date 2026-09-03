"""Test-retest baseline: 30 stratified items, deva + ascii conditions (the extremes),
5 identical repeated calls each, Gemini 3.6 Flash at nominal temperature 0.
Quantifies call-to-call noise so shift magnitudes can be read against it.
"""
import json, os, random
import urllib.request
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, call_gemini, parse_score, api_key

HERE = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
random.seed(37)
sample = random.sample([i for i in items if i["tier"] == "high"], 10) + \
         random.sample([i for i in items if i["tier"] == "medium"], 10) + \
         random.sample([i for i in items if i["tier"] == "low"], 10)

key = api_key()
out_path = os.path.join(HERE, "..", "results", "testretest_gemini-3.6-flash.jsonl")
done = set()
if os.path.exists(out_path):
    for line in open(out_path):
        r = json.loads(line)
        done.add((r["id"], r["condition"], r["rep"]))

jobs = [(it, cond, rep) for it in sample for cond in ["deva", "ascii"] for rep in range(5)
        if (it["id"], cond, rep) not in done]
print(f"{len(jobs)} test-retest calls to run")
with open(out_path, "a") as out:
    for n, (it, cond, rep) in enumerate(jobs, 1):
        instr = it["instruction_deva"] if cond == "deva" else it["instruction_iast"]
        prompt = RUBRIC.format(mitigation="", instruction=instr, response=it["conditions"][cond])
        text, tin, tout = call_gemini("gemini-3.6-flash", prompt, 0.0, key)
        score, reason = parse_score(text)
        out.write(json.dumps({"id": it["id"], "tier": it["tier"], "condition": cond,
                              "rep": rep, "score": score}) + "\n")
        out.flush()
        if n % 30 == 0:
            print(f"  {n}/{len(jobs)}")
print("test-retest battery done")
