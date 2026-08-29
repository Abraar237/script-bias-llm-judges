"""Build all results figures from results/analysis.json + token_counts.jsonl.
Every number drawn is printed so it can be checked against the source JSON."""
import json, os, sys
import matplotlib.pyplot as plt
import style
from style import (SLATE, HOT, SHELF, GOOD, INK, INK2, MUTED, FAINT, RULE,
                   COND_COLORS, COND_LABELS, zero_rule)

style.apply()
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
A = json.load(open(os.path.join(RES, "analysis.json")))
J = {j["judge"]: j for j in A["judges"]}

JUDGE_ORDER = ["gemini-3.6-flash", "gemini-3.1-pro-preview", "qwen2.5-7b-instruct",
               "claude-sonnet-5", "claude-opus-5", "claude-fable-5"]
JUDGE_LABELS = {"gemini-3.6-flash": "Gemini 3.6 Flash",
                "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
                "claude-sonnet-5": "Claude Sonnet 5",
                "claude-opus-5": "Claude Opus 5",
                "claude-fable-5": "Claude Fable 5",
                "qwen2.5-7b-instruct": "Qwen2.5-7B"}
CONDS = ["iast", "ascii", "hinglish"]


def fig_forest():
    """Fig 2: per-judge score shift (romanized minus Devanagari) with 95% CIs."""
    fig, ax = plt.subplots(figsize=(6.3, 3.9))
    y = 0
    yticks, ylabels = [], []
    printed = []
    for judge in JUDGE_ORDER:
        for k, cond in enumerate(CONDS):
            e = J[judge]["conditions"][cond]
            lo, hi = e["ci95"]; m = e["mean_shift"]
            ax.plot([lo, hi], [y, y], color=COND_COLORS[cond], lw=2.2, zorder=3)
            ax.plot([m], [y], "o", ms=7, color=COND_COLORS[cond],
                    mec=style.SURFACE, mew=1.4, zorder=4)
            printed.append((judge, cond, m, lo, hi))
            if judge == JUDGE_ORDER[0]:
                ax.text(10.55, y, COND_LABELS[cond], fontsize=8.6,
                        color=COND_COLORS[cond], va="center")
            y -= 1
        yticks.append(y + 2); ylabels.append(JUDGE_LABELS[judge])
        y -= 0.8
    zero_rule(ax, "x")
    ax.text(-0.25, 0.75, "scores equal\nacross scripts", fontsize=7.8, color=FAINT, ha="right", va="center")
    ax.annotate("Gemini inflates romanized scores", xy=(4.2, -2.0), xytext=(5.2, -4.6),
                fontsize=8.6, color=INK2,
                arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8))
    ax.annotate("Claude family: no shift", xy=(0.15, -11.4), xytext=(2.0, -12.4),
                fontsize=8.6, color=INK2,
                arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8))
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=9, color=INK2)
    ax.set_xlabel("score shift, romanized minus Devanagari (points on a 0-100 scale)")
    ax.set_xlim(-2.8, 11.0)
    ax.text(0, 1.05, "S A M E   C O N T E N T ,   D I F F E R E N T   S C R I P T :   "
                     "S H I F T   B Y   J U D G E", transform=ax.transAxes,
            fontsize=8.4, color=MUTED)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig2_forest.png"), bbox_inches="tight")
    plt.close(fig)
    for p in printed: print("fig2", *p)


def fig_tiers():
    """Fig 3: the shift concentrates in medium-quality items (Flash and Pro)."""
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.9), gridspec_kw={"wspace": 0.34})
    for ax, judge, title in [(axes[0], "gemini-3.6-flash", "Gemini 3.6 Flash"),
                             (axes[1], "gemini-3.1-pro-preview", "Gemini 3.1 Pro")]:
        xs = [0, 1, 2]
        for cond in CONDS:
            vals, los, his = [], [], []
            for t in ["high", "medium", "low"]:
                bt = J[judge]["conditions"][cond]["by_tier"][t]
                vals.append(bt["mean_shift"]); los.append(bt["ci95"][0]); his.append(bt["ci95"][1])
                print("fig3", judge, cond, t, bt["mean_shift"], bt["ci95"])
            ax.plot(xs, vals, "-o", color=COND_COLORS[cond], ms=7,
                    mec=style.SURFACE, mew=1.2, label=COND_LABELS[cond])
            for x, lo, hi in zip(xs, los, his):
                ax.plot([x, x], [lo, hi], color=COND_COLORS[cond], lw=1.1, alpha=0.65)
        zero_rule(ax, "y")
        ax.set_xticks(xs); ax.set_xticklabels(["high", "medium", "low"])
        ax.set_xlabel("response quality tier")
        ax.text(0, 1.07, " ".join(title.upper()), transform=ax.transAxes,
                fontsize=8.4, color=MUTED)
        ax.set_ylim(-1.5, 10.2)
    axes[0].set_ylabel("score shift (points)")
    axes[0].annotate("the bias lives in the\nambiguous middle", xy=(1, 7.8),
                     xytext=(1.35, 8.6), fontsize=8.4, color=INK2,
                     arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8))
    for cond in CONDS:
        v = J["gemini-3.6-flash"]["conditions"][cond]["by_tier"]["low"]["mean_shift"]
        axes[0].text(2.06, v, COND_LABELS[cond], fontsize=8, color=COND_COLORS[cond], va="center")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig3_tiers.png"), bbox_inches="tight")
    plt.close(fig)


def fig_mitigation():
    """Fig 4: the one-line mitigation does not close the gap (Flash, medium tier)."""
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    xs = [0, 1, 2]
    for tag, judge, color, label in [("base", "gemini-3.6-flash", SLATE, "standard rubric"),
                                     ("mit", "gemini-3.6-flash+mitigation", HOT,
                                      'rubric + "ignore the script" line')]:
        vals, cis = [], []
        for cond in CONDS:
            bt = J[judge]["conditions"][cond]["by_tier"]["medium"]
            vals.append(bt["mean_shift"]); cis.append(bt["ci95"])
            print("fig4", judge, cond, bt["mean_shift"], bt["ci95"])
        off = -0.08 if tag == "base" else 0.08
        for x, v, (lo, hi) in zip(xs, vals, cis):
            ax.plot([x + off, x + off], [lo, hi], color=color, lw=1.2, alpha=0.7)
        ax.plot([x + off for x in xs], vals, "o-", color=color, ms=7.5,
                mec=style.SURFACE, mew=1.3)
        ax.text(2.18, vals[-1], label, fontsize=8.6, color=color, va="center")
    zero_rule(ax, "y")
    ax.set_xticks(xs); ax.set_xticklabels([COND_LABELS[c] for c in CONDS])
    ax.set_xlim(-0.4, 3.6)
    ax.set_ylabel("medium-tier score shift")
    ax.text(0, 1.08, "T H E   O B V I O U S   F I X   D O E S   N O T   W O R K",
            transform=ax.transAxes, fontsize=8.4, color=MUTED)
    ax.annotate("instructed to ignore script,\nthe judge inflates anyway", xy=(1.08, 9.06),
                xytext=(0.15, 9.6), fontsize=8.4, color=INK2,
                arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8))
    ax.set_ylim(-1, 12)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig4_mitigation.png"), bbox_inches="tight")
    plt.close(fig)


def fig_mechanism():
    """Fig 5: token inflation exists but does not explain the shift; the judge's own
    reasons name the script."""
    toks = [json.loads(l) for l in open(os.path.join(RES, "token_counts.jsonl"))]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.8), gridspec_kw={"wspace": 0.38})
    ax = axes[0]
    import statistics as st
    ratios = {c: st.mean(t[c] / t["deva"] for t in toks if t.get(c) and t.get("deva"))
              for c in CONDS}
    print("fig5 ratios", ratios)
    bars = ax.barh([2, 1, 0], [ratios[c] for c in CONDS],
                   color=[COND_COLORS[c] for c in CONDS], height=0.55)
    ax.axvline(1.0, ls=(0, (4, 3)), lw=0.9, color=FAINT)
    ax.text(1.02, 2.42, "Devanagari length", fontsize=8, color=FAINT)
    ax.set_yticks([2, 1, 0]); ax.set_yticklabels([COND_LABELS[c] for c in CONDS], color=INK2)
    for y, c in zip([2, 1, 0], CONDS):
        ax.text(ratios[c] + 0.04, y, f"{ratios[c]:.2f}x", fontsize=8.6,
                color=COND_COLORS[c], va="center")
    ax.set_xlim(0, 2.45)
    ax.set_xlabel("tokens relative to Devanagari (Gemini tokenizer)")
    ax.text(0, 1.08, "R O M A N I Z E D   C O S T S   M O R E   T O K E N S",
            transform=ax.transAxes, fontsize=8.4, color=MUTED)

    ax = axes[1]
    rows = [json.loads(l) for l in open(os.path.join(RES, "scores_gemini-3.6-flash_t0.jsonl"))]
    import re as _re
    pat = _re.compile(r"hinglish|roman|script|transliter|devanagari|orthograph", _re.I)
    rates = {}
    for c in ["deva"] + CONDS:
        sub = [r for r in rows if r["condition"] == c and r["score"] is not None]
        rates[c] = sum(1 for r in sub if pat.search(r.get("reason") or "")) / len(sub) * 100
    print("fig5 mention rates", rates)
    order = ["deva"] + CONDS
    colors = {"deva": FAINT, **COND_COLORS}
    labels = {"deva": "Devanagari", **COND_LABELS}
    ax.barh(range(len(order) - 1, -1, -1), [rates[c] for c in order],
            color=[colors[c] for c in order], height=0.55)
    ax.set_yticks(range(len(order) - 1, -1, -1))
    ax.set_yticklabels([labels[c] for c in order], color=INK2)
    for y, c in zip(range(len(order) - 1, -1, -1), order):
        ax.text(rates[c] + 1.5, y, f"{rates[c]:.0f}%", fontsize=8.6,
                color=colors[c] if c != "deva" else MUTED, va="center")
    ax.set_xlim(0, 78)
    ax.set_xlabel("% of judge reasons mentioning the script")
    ax.text(0, 1.08, "T H E   J U D G E   S E E S   T H E   S C R I P T",
            transform=ax.transAxes, fontsize=8.4, color=MUTED)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig5_mechanism.png"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_forest()
    fig_tiers()
    fig_mitigation()
    fig_mechanism()
    print("all figures written to", HERE)
