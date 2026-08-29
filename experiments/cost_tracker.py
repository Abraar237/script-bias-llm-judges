"""Gemini spend tracker. Every API call logs its usageMetadata token counts here;
cost is computed from the official pricing page (ai.google.dev/gemini-api/docs/pricing,
fetched and verified 2026-08-29) and the run hard-stops before the cap is reached.
"""
import json, os

# USD per 1M tokens, paid standard tier, prompts <= 200k. Verified 2026-08-29 against
# ai.google.dev/gemini-api/docs/pricing. Thinking tokens are billed as OUTPUT, so
# callers must pass output_tokens = candidatesTokenCount + thoughtsTokenCount.
# (2.5-generation models are unavailable to this key; 3.x models verified live.)
PRICING = {
    "gemini-3.6-flash":      {"in": 0.75, "out": 3.75},
    "gemini-3.1-pro-preview": {"in": 2.00, "out": 12.00},
}

CAP_USD = 25.0  # hard stop below the user's $30 ceiling, leaving margin for Modal
LOG = os.path.join(os.path.dirname(__file__), "..", "results", "spend_log.jsonl")


def log_call(model, prompt_tokens, output_tokens, tag=""):
    """Record one API call and return the running total. Raises if cap exceeded."""
    cost = (prompt_tokens * PRICING[model]["in"] + output_tokens * PRICING[model]["out"]) / 1e6
    entry = {"model": model, "prompt_tokens": prompt_tokens,
             "output_tokens": output_tokens, "cost_usd": round(cost, 6), "tag": tag}
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    total = spent()
    if total > CAP_USD:
        raise RuntimeError(f"SPEND CAP HIT: ${total:.2f} > ${CAP_USD} cap. Stopping.")
    return total


def spent():
    if not os.path.exists(LOG):
        return 0.0
    return sum(json.loads(l)["cost_usd"] for l in open(LOG) if l.strip())


if __name__ == "__main__":
    print(f"Spent so far: ${spent():.4f} of ${CAP_USD} cap")
