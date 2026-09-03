"""Test-retest noise floor for GPT-5.6 via OpenRouter (third judge family).
Same seed-37 sample: 30 items x deva+ascii x 5 reps = 300 calls, temp 0."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, parse_score
from run_openrouter_judge import api_key, call_openrouter, log_call

HERE = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
random.seed(37)
sample = random.sample([i for i in items if i["tier"] == "high"], 10) + \
         random.sample([i for i in items if i["tier"] == "medium"], 10) + \
         random.sample([i for i in items if i["tier"] == "low"], 10)
out_path = os.path.join(HERE, "..", "results", "testretest_gpt-5.6.jsonl")
done = set()
if os.path.exists(out_path):
    for line in open(out_path):
        r = json.loads(line)
        if r["score"] is not None:
            done.add((r["id"], r["condition"], r["rep"]))
key = api_key()
jobs = [(it, c, rep) for it in sample for c in ["deva", "ascii"] for rep in range(5)
        if (it["id"], c, rep) not in done]
print(f"{len(jobs)} GPT test-retest calls", flush=True)
with open(out_path, "a") as out:
    for n, (it, c, rep) in enumerate(jobs, 1):
        instr = it["instruction_deva"] if c == "deva" else it["instruction_iast"]
        prompt = RUBRIC.format(mitigation="", instruction=instr, response=it["conditions"][c])
        text, tin, tout = call_openrouter("openai/gpt-5.6-terra", prompt, key)
        log_call("openai/gpt-5.6-terra", tin, tout)
        score, _ = parse_score(text)
        out.write(json.dumps({"id": it["id"], "tier": it["tier"], "condition": c,
                              "rep": rep, "score": score}) + "\n")
        out.flush()
        if n % 50 == 0:
            print(f"  {n}/{len(jobs)}", flush=True)
print("GPT test-retest done", flush=True)
