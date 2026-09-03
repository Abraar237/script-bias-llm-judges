"""Rebuild fig2 (forest, clean-protocol Claude), fig4 (mitigation battery, two judges),
and new fig7 (protocol masking). fig1/3/5/6 unchanged. All data from analysis.json."""
import json, os
import matplotlib.pyplot as plt
import style
from style import (SLATE, HOT, SHELF, GOOD, INK, INK2, MUTED, FAINT,
                   COND_COLORS, COND_LABELS, zero_rule)

style.apply()
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
A = json.load(open(os.path.join(RES, "analysis.json")))
J = {j["judge"]: j for j in A["judges"]}
CONDS = ["iast", "ascii", "hinglish"]

JUDGE_ORDER = ["gemini-3.6-flash", "gemini-3.1-pro-preview", "qwen2.5-7b-instruct",
               "claude-sonnet-5-api", "claude-opus-5-api", "claude-fable-5-api"]
JUDGE_LABELS = {"gemini-3.6-flash": "Gemini 3.6 Flash",
                "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
                "qwen2.5-7b-instruct": "Qwen2.5-7B",
                "claude-sonnet-5-api": "Claude Sonnet 5",
                "claude-opus-5-api": "Claude Opus 5",
                "claude-fable-5-api": "Claude Fable 5"}


def fig_forest():
    fig, ax = plt.subplots(figsize=(6.3, 4.1))
    y = 0
    yticks, ylabels = [], []
    for judge in JUDGE_ORDER:
        for cond in CONDS:
            e = J[judge]["conditions"][cond]
            lo, hi = e["ci95"]; m = e["mean_shift"]
            ax.plot([lo, hi], [y, y], color=COND_COLORS[cond], lw=2.2, zorder=3)
            ax.plot([m], [y], "o", ms=7, color=COND_COLORS[cond],
                    mec=style.SURFACE, mew=1.4, zorder=4)
            print("fig2", judge, cond, m, lo, hi)
            if judge == JUDGE_ORDER[0]:
                ax.text(11.9, y, COND_LABELS[cond], fontsize=8.6,
                        color=COND_COLORS[cond], va="center")
            y -= 1
        yticks.append(y + 2); ylabels.append(JUDGE_LABELS[judge])
        y -= 0.8
    zero_rule(ax, "x")
    ax.text(-0.35, 1.15, "scores equal\nacross scripts", fontsize=7.8, color=FAINT, ha="right", va="center")
    ax.annotate("Gemini and Qwen inflate\nromanized scores", xy=(3.8, -1.6), xytext=(4.9, -5.6),
                fontsize=8.6, color=INK2, arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8))
    ax.annotate("Claude penalises, most strongly\nat the smallest scale", xy=(-12.29, -12.4), xytext=(-14.6, -9.0),
                fontsize=8.6, color=INK2, arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8))
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=9, color=INK2)
    ax.set_xlabel("score shift, romanized minus Devanagari (points on a 0-100 scale)")
    ax.set_xlim(-16.2, 13.4)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig2_forest.png"), bbox_inches="tight")
    plt.close(fig)


def fig_mitigation_battery():
    """fig4: seven arms x two judge families; nothing closes the gap."""
    ARMS = [("none", "no instruction"), ("P1", "ignore the script"),
            ("P2", "explicit warning"), ("P3", "fairness framing"),
            ("P4", "transliterate first"), ("P5", "script-blind persona"),
            ("R1", "decomposed rubric")]
    qb = A["qwen_mitigation_battery"]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.3), gridspec_kw={"wspace": 0.12}, sharey=True)

    def flash_val(arm, cond):
        key = "gemini-3.6-flash" if arm == "none" else (
            "gemini-3.6-flash+mitigation" if arm == "P1" else f"gemini-3.6-flash+arm{arm}")
        bt = J[key]["conditions"][cond]["by_tier"]["medium"]
        return bt["mean_shift"], bt["ci95"]

    def qwen_val(arm, cond):
        if arm == "none":
            e = J["qwen2.5-7b-instruct"]["conditions"][cond]
            return e["mean_shift"], e["ci95"]
        e = qb[arm][cond]
        return e["mean_shift"], e["ci95"]

    for ax, getv, title, note in [
            (axes[0], flash_val, "Gemini 3.6 Flash (medium tier)", "partial reduction at best;\nrubric variant flips ASCII negative"),
            (axes[1], qwen_val, "Qwen2.5-7B (all items)", "every instruction\nmakes it worse")]:
        for i, (arm, label) in enumerate(ARMS):
            yy = len(ARMS) - 1 - i
            for k, cond in enumerate(CONDS):
                v, (lo, hi) = getv(arm, cond)
                off = (k - 1) * 0.22
                ax.plot([lo, hi], [yy + off, yy + off], color=COND_COLORS[cond], lw=1.6, alpha=0.85)
                ax.plot([v], [yy + off], "o", ms=5.4, color=COND_COLORS[cond],
                        mec=style.SURFACE, mew=1.0)
                print("fig4", title.split()[0], arm, cond, v)
        zero_rule(ax, "x")
        ax.set_title(title, fontsize=10, color=INK, pad=22)
        ax.set_yticks(range(len(ARMS)))
        ax.set_xlabel("score shift (points)")
        ax.text(0.5, 1.10, note.replace("\n", " "), transform=ax.transAxes, ha="center",
                fontsize=8, color=HOT, style="italic")
    axes[0].set_yticklabels([l for _, l in reversed(ARMS)], fontsize=8.6, color=INK2)
    axes[0].set_xlim(-6, 12)
    axes[1].set_xlim(-3.5, 14.5)
    for k, cond in enumerate(CONDS):
        axes[1].text(0.99, 0.985 - k * 0.055, COND_LABELS[cond], transform=axes[1].transAxes,
                     ha="right", va="top", fontsize=8.4, color=COND_COLORS[cond])
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig4_mitigation.png"), bbox_inches="tight")
    plt.close(fig)


def fig_protocol():
    """fig7: the measurement protocol masks the bias (Claude, session vs one-per-call)."""
    session = {"claude-sonnet-5": None, "claude-opus-5": None, "claude-fable-5": None}
    fig, ax = plt.subplots(figsize=(6.3, 2.9))
    rows = []
    for name in ["claude-sonnet-5", "claude-opus-5", "claude-fable-5"]:
        for cond in CONDS:
            s = J[name]["conditions"][cond]["mean_shift"]
            a = J[name + "-api"]["conditions"][cond]["mean_shift"]
            rows.append((name, cond, s, a))
    y = 0
    yticks, ylabels = [], []
    for name in ["claude-sonnet-5", "claude-opus-5", "claude-fable-5"]:
        for cond in CONDS:
            s = J[name]["conditions"][cond]["mean_shift"]
            a = J[name + "-api"]["conditions"][cond]["mean_shift"]
            print("fig7", name, cond, s, "->", a)
            ax.annotate("", xy=(a, y), xytext=(s, y),
                        arrowprops=dict(arrowstyle="-|>", color=COND_COLORS[cond], lw=1.6,
                                        shrinkA=3, shrinkB=3))
            ax.plot([s], [y], "o", ms=6, color=FAINT, mec=style.SURFACE, mew=1.0, zorder=4)
            ax.plot([a], [y], "o", ms=7, color=COND_COLORS[cond], mec=style.SURFACE, mew=1.2, zorder=4)
            y -= 1
        yticks.append(y + 2); ylabels.append(JUDGE_LABELS[name + "-api"])
        y -= 0.7
    zero_rule(ax, "x")
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=9, color=INK2)
    ax.set_xlabel("score shift, romanized minus Devanagari (points)")
    ax.plot([], [], "o", ms=6, color=FAINT, label="batched session (150 items per context)")
    ax.plot([], [], "o", ms=7, color=SLATE, label="one item per call")
    leg = ax.legend(loc="lower left", fontsize=8.2, frameon=False)
    ax.annotate("the batched protocol reported zero;\nisolated judging reveals the penalty",
                xy=(-12.29, -0.9), xytext=(-13.9, -4.4), fontsize=8.6, color=INK2,
                arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8))
    ax.set_xlim(-15.5, 4.5)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig7_protocol.png"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_forest()
    fig_mitigation_battery()
    fig_protocol()
    print("v2 figures written")
