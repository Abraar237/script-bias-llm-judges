"""Qwen2.5-7B-Instruct judge on Modal (A10G) with score-distribution logprobs.
Scores all 150 items x 4 conditions. For each call we read the top-20 logprobs at the
first score-token position, recovering the judge's distribution over scores rather
than only its argmax.

Run:  python3 -m modal run modal_qwen_judge.py
Writes results to results/scores_qwen2.5-7b_logprobs.jsonl via a Modal volume mount back
to local (we just print JSONL to stdout and tee locally instead, keeping it simple).
"""
import json
import modal

app = modal.App("script-bias-qwen-judge")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm==0.8.5.post1", "transformers==4.51.3")
)

RUBRIC = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "Score the response from 0 to 100 considering: correctness, completeness, helpfulness, clarity.\n"
    "Judge this item on its own merits.\n"
    "Instruction:\n{instruction}\n\nResponse:\n{response}\n\n"
    "Reply with ONLY the integer score (0-100), nothing else."
)


@app.function(image=image, gpu="A10G", timeout=3600)
def judge_batch(jobs: list) -> list:
    from vllm import LLM, SamplingParams

    llm = LLM(model="Qwen/Qwen2.5-7B-Instruct", max_model_len=4096, dtype="bfloat16")
    params = SamplingParams(temperature=0.0, max_tokens=4, logprobs=20)
    prompts = []
    for j in jobs:
        msgs = [{"role": "user", "content": RUBRIC.format(instruction=j["instruction"], response=j["response"])}]
        prompts.append(llm.get_tokenizer().apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
    outs = llm.generate(prompts, params)
    results = []
    for j, o in zip(jobs, outs):
        text = o.outputs[0].text.strip()
        # top-20 logprobs at the first generated token: the score distribution head
        top = {}
        if o.outputs[0].logprobs:
            for tok_id, lp in o.outputs[0].logprobs[0].items():
                top[lp.decoded_token.strip()] = round(lp.logprob, 4)
        results.append({"id": j["id"], "condition": j["condition"], "tier": j["tier"],
                        "text": text, "top_logprobs": top})
    return results


@app.local_entrypoint()
def main():
    items = json.load(open("dataset_conditions.json"))
    jobs = []
    for it in items:
        for cond in ["deva", "iast", "ascii", "hinglish"]:
            if cond == "deva":
                instr = it["instruction_deva"]
            elif cond == "hinglish":
                instr = it.get("instruction_hinglish") or it["instruction_iast"]
            else:
                instr = it["instruction_iast"]
            jobs.append({"id": it["id"], "condition": cond, "tier": it["tier"],
                         "instruction": instr, "response": it["conditions"][cond]})
    print(f"{len(jobs)} judgments to run on Modal A10G...")
    results = judge_batch.remote(jobs)
    out = "../results/scores_qwen2.5-7b_logprobs.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(results)} rows -> {out}")
