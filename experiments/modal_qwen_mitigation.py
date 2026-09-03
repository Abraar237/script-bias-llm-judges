"""Qwen2.5-7B mitigation battery on Modal: 6 arms (P1 original line, P2-P5 phrasings,
R1 decomposed rubric) x 150 items x 4 conditions = 3600 judgments, one A10G batch.
Run: python3 -m modal run modal_qwen_mitigation.py
"""
import json
import modal

app = modal.App("script-bias-qwen-mitigation")
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "vllm==0.8.5.post1", "transformers==4.51.3")

BASE = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "Score the response from 0 to 100 considering: correctness, completeness, helpfulness, clarity.\n"
    "Judge this item on its own merits.\n{mitigation}"
    "Instruction:\n{instruction}\n\nResponse:\n{response}\n\n"
    "Reply with ONLY the integer score (0-100), nothing else."
)
R1 = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "Give four sub-scores from 0 to 25 each: correctness, completeness, helpfulness, clarity, "
    "then reply with ONLY their total as one integer (0-100), nothing else.\n"
    "Judge this item on its own merits.\n"
    "Instruction:\n{instruction}\n\nResponse:\n{response}\n"
)
ARMS = {
    "P1": "Evaluate the content regardless of the script or orthography it is written in.\n",
    "P2": "The response may be written in Devanagari or in romanized Hindi (Latin letters). "
          "The writing system must not affect your score; grade only the content.\n",
    "P3": "Do not reward or penalise the choice of script, spelling system, or transliteration "
          "style. Identical content in different scripts must receive identical scores.\n",
    "P4": "If the response is romanized, first mentally transliterate it into Devanagari, "
          "then judge that content as you would any Hindi response.\n",
    "P5": "You are a script-blind evaluator: you cannot perceive which writing system is used, "
          "only the meaning of the words.\n",
    "R1": None,
}


@app.function(image=image, gpu="A10G", timeout=7200)
def judge_batch(jobs: list) -> list:
    from vllm import LLM, SamplingParams
    llm = LLM(model="Qwen/Qwen2.5-7B-Instruct", max_model_len=4096, dtype="bfloat16")
    params = SamplingParams(temperature=0.0, max_tokens=4)
    tok = llm.get_tokenizer()
    prompts = [tok.apply_chat_template([{"role": "user", "content": j["prompt"]}],
                                       tokenize=False, add_generation_prompt=True) for j in jobs]
    outs = llm.generate(prompts, params)
    return [{"id": j["id"], "condition": j["condition"], "tier": j["tier"], "arm": j["arm"],
             "text": o.outputs[0].text.strip()} for j, o in zip(jobs, outs)]


@app.local_entrypoint()
def main():
    items = json.load(open("dataset_conditions.json"))
    jobs = []
    for arm, line in ARMS.items():
        for it in items:
            for cond in ["deva", "iast", "ascii", "hinglish"]:
                if cond == "deva":
                    instr = it["instruction_deva"]
                elif cond == "hinglish":
                    instr = it.get("instruction_hinglish") or it["instruction_iast"]
                else:
                    instr = it["instruction_iast"]
                tmpl = R1 if arm == "R1" else BASE
                prompt = (tmpl.format(instruction=instr, response=it["conditions"][cond])
                          if arm == "R1" else
                          tmpl.format(mitigation=line, instruction=instr, response=it["conditions"][cond]))
                jobs.append({"id": it["id"], "condition": cond, "tier": it["tier"],
                             "arm": arm, "prompt": prompt})
    print(f"{len(jobs)} judgments across {len(ARMS)} arms...")
    results = judge_batch.remote(jobs)
    out = "../results/scores_qwen2.5-7b_mitigation.jsonl"
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(results)} rows -> {out}")
