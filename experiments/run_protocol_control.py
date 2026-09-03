"""Protocol-confound control: batched judging through the SAME headless
`claude -p` interface used for the one-per-call arm, so batch size is the ONLY
variable (same model, same rubric wording per item, same interface, same
default sampling). The original batched arm ran 150 items per session through
an interactive CLI; here each call carries a batch of 25 items of one
condition, numbered, and asks for a JSON array of scores.

Usage: python3 run_protocol_control.py --model claude-sonnet-5 [--batch-size 25]
Output: results/scores_protocol-batched_<model>.jsonl (one row per item, with
        protocol "headless-batched-<K>" and the batch index recorded)
"""
import argparse, json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset_conditions.json")
RES = os.path.join(HERE, "..", "results")

HEADER = (
    "You are grading responses to instructions for an instruction-following benchmark.\n"
    "For EACH numbered item below, score the response from 0 to 100 considering: "
    "correctness (facts right), completeness (covers what the instruction asks), "
    "helpfulness, and clarity. Judge every item on its own merits.\n\n"
)
FOOTER = (
    '\nReply with ONLY a JSON array, one object per item, in the same order: '
    '[{"n": <item number>, "score": <integer 0-100>, "reason": "<one short sentence>"}, ...]'
)


def judge_batch(model, prompt):
    p = subprocess.run(["claude", "-p", "--model", model], input=prompt,
                       capture_output=True, text=True, timeout=900)
    return p.stdout.strip()


def parse_batch(text, expected_ns):
    scores = {}
    if not text:
        return scores
    for m in re.finditer(r'\{\s*"n"\s*:\s*(\d+)\s*,\s*"score"\s*:\s*(\d+)\s*(?:,\s*"reason"\s*:\s*"([^"]*)")?', text):
        n, s = int(m.group(1)), int(m.group(2))
        if n in expected_ns and 0 <= s <= 100:
            scores[n] = (s, m.group(3) or "")
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--batch-size", type=int, default=25)
    args = ap.parse_args()

    items = json.load(open(DATASET))
    out_path = os.path.join(RES, f"scores_protocol-batched_{args.model}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r["score"] is not None:
                done.add((r["id"], r["condition"]))

    for cond in ["deva", "iast", "ascii", "hinglish"]:
        pending = [it for it in items if it["conditions"].get(cond) and (it["id"], cond) not in done]
        if not pending:
            print(f"{cond}: all done", flush=True)
            continue
        batches = [pending[i:i + args.batch_size] for i in range(0, len(pending), args.batch_size)]
        print(f"{cond}: {len(pending)} items in {len(batches)} batches", flush=True)
        for bi, batch in enumerate(batches):
            parts = [HEADER]
            for n, it in enumerate(batch):
                if cond == "deva":
                    instr = it["instruction_deva"]
                elif cond == "hinglish":
                    instr = it.get("instruction_hinglish") or it["instruction_iast"]
                else:
                    instr = it["instruction_iast"]
                parts.append(f"--- Item {n} ---\nInstruction:\n{instr}\n\nResponse:\n{it['conditions'][cond]}\n")
            parts.append(FOOTER)
            text = judge_batch(args.model, "\n".join(parts))
            scores = parse_batch(text, set(range(len(batch))))
            with open(out_path, "a") as out:
                for n, it in enumerate(batch):
                    s, reason = scores.get(n, (None, "UNPARSED"))
                    out.write(json.dumps({"id": it["id"], "tier": it["tier"], "condition": cond,
                                          "model": args.model,
                                          "protocol": f"headless-batched-{args.batch_size}",
                                          "batch": bi, "score": s, "reason": reason},
                                         ensure_ascii=False) + "\n")
            print(f"  {cond} batch {bi + 1}/{len(batches)}: {len(scores)}/{len(batch)} parsed", flush=True)
    print("protocol-control battery done", flush=True)


if __name__ == "__main__":
    main()
