"""Gemini judge runner. Scores every (item, condition) with one call per pair,
randomized order, no cross-item context, hypothesis never mentioned.
Results append to results/scores_<model>.jsonl; spend logs via cost_tracker.

Usage:
  python3 run_gemini_judge.py --model gemini-3.6-flash [--conditions deva iast ascii hinglish]
      [--temp 0] [--seed-tag t0] [--mitigation] [--limit N]
"""
import argparse, json, os, random, re, sys, time
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cost_tracker import log_call, spent

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset_conditions.json")
RESULTS_DIR = os.path.join(HERE, "..", "results")

RUBRIC = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "Score the response from 0 to 100 considering: correctness (facts right), "
    "completeness (covers what the instruction asks), helpfulness, and clarity.\n"
    "Judge this item on its own merits.\n{mitigation}"
    "Instruction:\n{instruction}\n\nResponse:\n{response}\n\n"
    'Reply with ONLY a JSON object: {{"score": <integer 0-100>, "reason": "<one short sentence>"}}'
)
MITIGATION_LINE = "Evaluate the content regardless of the script or orthography it is written in.\n"

# Mitigation battery arms (P1 = the original line, already run as mit-t0)
ARMS = {
    "P2": "The response may be written in Devanagari or in romanized Hindi (Latin letters). "
          "The writing system must not affect your score; grade only the content.\n",
    "P3": "Do not reward or penalise the choice of script, spelling system, or transliteration "
          "style. Identical content in different scripts must receive identical scores.\n",
    "P4": "If the response is romanized, first mentally transliterate it into Devanagari, "
          "then judge that content as you would any Hindi response.\n",
    "P5": "You are a script-blind evaluator: you cannot perceive which writing system is used, "
          "only the meaning of the words.\n",
    "R1": "__RUBRIC_VARIANT__",
}
RUBRIC_R1 = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "Give four sub-scores from 0 to 25 each: correctness (facts right), completeness "
    "(covers what the instruction asks), helpfulness, clarity. The total is their sum.\n"
    "Judge this item on its own merits.\n"
    "Instruction:\n{instruction}\n\nResponse:\n{response}\n\n"
    'Reply with ONLY a JSON object: {{"correctness": <0-25>, "completeness": <0-25>, '
    '"helpfulness": <0-25>, "clarity": <0-25>, "score": <integer 0-100 sum>, '
    '"reason": "<one short sentence>"}}'
)


def api_key():
    for line in open(os.path.join(HERE, "..", ".env")):
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"\'')
    raise RuntimeError("GEMINI_API_KEY not found in research/.env")


def call_gemini(model, prompt, temp, key):
    # Pro rejects MINIMAL thinking; LOW is its floor (thinking bills as output tokens).
    level = "LOW" if "pro" in model else "MINIMAL"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temp,
            "maxOutputTokens": 1200 if level == "LOW" else 200,
            "thinkingConfig": {"thinkingLevel": level},
        },
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            u = d["usageMetadata"]
            text = d["candidates"][0]["content"]["parts"][0]["text"]
            billable_out = u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
            return text, u.get("promptTokenCount", 0), billable_out
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))


def parse_score(text):
    m = re.search(r'"score"\s*:\s*(\d+)', text)
    if m:
        s = int(m.group(1))
        if 0 <= s <= 100:
            rm = re.search(r'"reason"\s*:\s*"([^"]*)"', text)
            return s, (rm.group(1) if rm else "")
    return None, text[:120]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--conditions", nargs="+", default=["deva", "iast", "ascii", "hinglish"])
    ap.add_argument("--temp", type=float, default=0.0)
    ap.add_argument("--seed-tag", default="t0")
    ap.add_argument("--mitigation", action="store_true")
    ap.add_argument("--arm", choices=list(ARMS), default=None)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    key = api_key()
    items = json.load(open(DATASET))
    if args.limit:
        items = items[: args.limit]

    tag = (f"arm{args.arm}-" if args.arm else ("mit-" if args.mitigation else "")) + args.seed_tag
    out_path = os.path.join(RESULTS_DIR, f"scores_{args.model}_{tag}.jsonl")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            done.add((r["id"], r["condition"]))

    jobs = [(it, c) for it in items for c in args.conditions
            if it["conditions"].get(c) and (it["id"], c) not in done]
    random.seed(17)
    random.shuffle(jobs)
    print(f"{len(jobs)} calls to run ({len(done)} already done). Spend so far ${spent():.3f}")

    mit = MITIGATION_LINE if args.mitigation else ""
    rubric = RUBRIC
    if args.arm == "R1":
        rubric = RUBRIC_R1
        mit = ""
    elif args.arm:
        mit = ARMS[args.arm]
    with open(out_path, "a") as out:
        for n, (it, cond) in enumerate(jobs, 1):
            if cond == "deva":
                instr = it["instruction_deva"]
            elif cond == "hinglish":
                instr = it.get("instruction_hinglish") or it["instruction_iast"]
            else:
                instr = it["instruction_iast"]
            prompt = rubric.format(mitigation=mit, instruction=instr, response=it["conditions"][cond]) if "{mitigation}" in rubric else rubric.format(instruction=instr, response=it["conditions"][cond])
            text, tin, tout = call_gemini(args.model, prompt, args.temp, key)
            total = log_call(args.model, tin, tout, tag=f"{tag}/{it['id']}/{cond}")
            score, reason = parse_score(text)
            out.write(json.dumps({"id": it["id"], "tier": it["tier"], "condition": cond,
                                  "model": args.model, "tag": tag, "score": score,
                                  "reason": reason}, ensure_ascii=False) + "\n")
            out.flush()
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)} done, ${total:.3f} spent")
    print(f"finished. total spend ${spent():.3f}")


if __name__ == "__main__":
    main()
