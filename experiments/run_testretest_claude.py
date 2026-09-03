"""Test-retest noise floor for the Claude arm: the reviewer noted the one
stochastic judge (headless CLI, default sampling) had no measured noise floor.
Same design as the Flash battery: 30 stratified items (identical seed-37
sample), deva + ascii, 5 identical calls each, claude-sonnet-5 via the same
headless interface as the headline numbers. 300 calls, 2 workers.
"""
import json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, parse_score

HERE = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
random.seed(37)
sample = random.sample([i for i in items if i["tier"] == "high"], 10) + \
         random.sample([i for i in items if i["tier"] == "medium"], 10) + \
         random.sample([i for i in items if i["tier"] == "low"], 10)

out_path = os.path.join(HERE, "..", "results", "testretest_claude-sonnet-5.jsonl")
done = set()
if os.path.exists(out_path):
    for line in open(out_path):
        r = json.loads(line)
        if r["score"] is not None:
            done.add((r["id"], r["condition"], r["rep"]))


def judge(prompt):
    p = subprocess.run(["claude", "-p", "--model", "claude-sonnet-5"], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


jobs = []
for it in sample:
    for cond in ["deva", "ascii"]:
        instr = it["instruction_deva"] if cond == "deva" else it["instruction_iast"]
        prompt = RUBRIC.format(mitigation="", instruction=instr, response=it["conditions"][cond])
        for rep in range(5):
            if (it["id"], cond, rep) not in done:
                jobs.append((it["id"], it["tier"], cond, rep, prompt))
print(f"{len(jobs)} Claude test-retest calls to run", flush=True)

out = open(out_path, "a")
n = 0
with ThreadPoolExecutor(max_workers=2) as ex:
    futs = {ex.submit(judge, p): (i, t, c, rep) for i, t, c, rep, p in jobs}
    for fut in as_completed(futs):
        i, t, c, rep = futs[fut]
        try:
            text = fut.result()
        except Exception:
            text = ""
        score, _ = parse_score(text or "")
        out.write(json.dumps({"id": i, "tier": t, "condition": c, "rep": rep,
                              "score": score}) + "\n")
        out.flush()
        n += 1
        if n % 30 == 0:
            print(f"  {n}/{len(jobs)}", flush=True)
print("Claude test-retest battery done", flush=True)
