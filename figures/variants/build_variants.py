"""Alternative design variants of fig2 (overall shift) and fig3 (tier concentration).

Writes variants/fig2B..D and fig3B..D. Does not touch the A versions.
Each figure function returns the numbers it drew; the script prints them
so they can be checked against ../results/analysis.json.
"""
import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.dirname(HERE)
sys.path.insert(0, FIGDIR)
import style  # noqa: E402

style.apply()

SLATE, HOT, SHELF, GOOD = style.SLATE, style.HOT, style.SHELF, style.GOOD
INK, INK2, MUTED, FAINT, RULE = style.INK, style.INK2, style.MUTED, style.FAINT, style.RULE
COND_COLORS, COND_LABELS = style.COND_COLORS, style.COND_LABELS
CONDS = ["iast", "ascii", "hinglish"]
TIERS = ["high", "medium", "low"]

JUDGES = [
    ("gemini-3.6-flash", "Gemini 3.6 Flash", "Gemini_icon.png"),
    ("gemini-3.1-pro-preview", "Gemini 3.1 Pro", "Gemini_icon.png"),
    ("qwen2.5-7b-instruct", "Qwen2.5-7B", "Qwen_icon.png"),
    ("claude-sonnet-5", "Claude Sonnet 5", "Claude_AI_symbol.png"),
    ("claude-opus-5", "Claude Opus 5", "Claude_AI_symbol.png"),
    ("claude-fable-5", "Claude Fable 5", "Claude_AI_symbol.png"),
]

with open(os.path.join(FIGDIR, "..", "results", "analysis.json")) as f:
    ANALYSIS = {j["judge"]: j for j in json.load(f)["judges"]}

LOGOS = {}
for _, _, fn in JUDGES:
    if fn not in LOGOS:
        LOGOS[fn] = plt.imread(os.path.join(FIGDIR, "logos", fn))


def logo_box(fname, pts):
    """OffsetImage sized to `pts` points tall (zoom*px == points on screen)."""
    img = LOGOS[fname]
    return OffsetImage(img, zoom=pts / img.shape[0])


def cond_key(ax, x, y, gap=0.115, fontsize=9, transform=None):
    """Inline color key: dot + label per condition (no legend box)."""
    tr = transform if transform is not None else ax.transAxes
    for i, c in enumerate(CONDS):
        ax.scatter([x + i * gap], [y], s=22, color=COND_COLORS[c], transform=tr,
                   clip_on=False, zorder=6)
        ax.text(x + i * gap + 0.022, y, COND_LABELS[c], transform=tr, ha="left",
                va="center", fontsize=fontsize, color=INK2, clip_on=False, zorder=6)


def stack_apart(vals, min_gap):
    """Nudge a sorted-by-value list of positions apart by at least min_gap."""
    order = np.argsort(vals)
    out = np.array(vals, float)
    s = out[order]
    for i in range(1, len(s)):
        if s[i] - s[i - 1] < min_gap:
            s[i] = s[i - 1] + min_gap
    out[order] = s
    return out


def save(fig, name):
    path = os.path.join(HERE, name)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------- fig2B bars
def fig2B():
    fig, ax = plt.subplots(figsize=(6.3, 5.2))
    fig.subplots_adjust(left=0.27, top=0.93, bottom=0.09, right=0.97)
    drawn = {}
    bh = 0.22
    offs = {"iast": bh, "ascii": 0.0, "hinglish": -bh}
    tr = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for gi, (jid, jname, logo) in enumerate(JUDGES):
        y0 = -gi
        for c in CONDS:
            d = ANALYSIS[jid]["conditions"][c]
            m, (lo, hi) = d["mean_shift"], d["ci95"]
            drawn[(jname, c)] = (round(m, 3), lo, hi)
            y = y0 + offs[c]
            ax.barh(y, m, height=bh * 0.86, color=COND_COLORS[c], zorder=3)
            ax.plot([lo, hi], [y, y], lw=1.0, color=INK2, zorder=4,
                    solid_capstyle="butt")
            if m >= 0:
                ax.text(max(hi, m) + 0.18, y, f"+{m:.2f}" if m > 0 else "0.00",
                        va="center", ha="left", fontsize=8, color=INK2, zorder=5)
            else:
                ax.text(min(lo, m) - 0.18, y, f"−{abs(m):.2f}", va="center",
                        ha="right", fontsize=8, color=INK2, zorder=5)
        # judge name + logo in the left margin
        ax.add_artist(AnnotationBbox(logo_box(logo, 10), (-0.255, y0),
                                     xycoords=tr, frameon=False,
                                     box_alignment=(0.5, 0.5),
                                     annotation_clip=False))
        ax.text(-0.225, y0, jname, transform=tr, ha="left", va="center",
                fontsize=9.5, color=INK, clip_on=False)
        if gi < len(JUDGES) - 1:
            ax.axhline(y0 - 0.5, color=RULE, lw=0.6, zorder=1)
    style.zero_rule(ax, "x")
    ax.text(-0.18, 0.995, "scores equal\nacross scripts",
            transform=mtransforms.blended_transform_factory(ax.transData, ax.transAxes),
            ha="right", va="top", fontsize=8, color=FAINT)
    ax.set_yticks([])
    ax.set_ylim(-5.55, 0.62)
    ax.set_xlim(-2.6, 11.2)
    ax.set_xlabel("score shift, romanized minus Devanagari (points on a 0–100 scale)")
    ax.spines["left"].set_visible(False)
    cond_key(ax, 0.60, 0.985, gap=0.135)
    return drawn


# ------------------------------------------------------------- fig2C heatmap
def fig2C():
    cmap = LinearSegmentedColormap.from_list("housediv", [SLATE, "#ffffff", HOT])
    norm = TwoSlopeNorm(vmin=-8, vcenter=0, vmax=8)
    fig, ax = plt.subplots(figsize=(6.3, 3.35))
    fig.subplots_adjust(left=0.26, right=0.86, top=0.90, bottom=0.06)
    M = np.zeros((len(JUDGES), 3))
    P = np.zeros_like(M)
    drawn = {}
    for i, (jid, jname, logo) in enumerate(JUDGES):
        for k, c in enumerate(CONDS):
            d = ANALYSIS[jid]["conditions"][c]
            M[i, k] = d["mean_shift"]
            P[i, k] = d["p_wilcoxon_perm"]
            drawn[(jname, c)] = (round(M[i, k], 3), P[i, k])
    im = ax.imshow(M, cmap=cmap, norm=norm, aspect="auto")
    # cell borders
    ax.set_xticks(np.arange(-0.5, 3), minor=True)
    ax.set_yticks(np.arange(-0.5, len(JUDGES)), minor=True)
    ax.grid(which="minor", color=RULE, lw=0.8)
    ax.tick_params(which="both", length=0)
    for i in range(len(JUDGES)):
        for k in range(3):
            v, p = M[i, k], P[i, k]
            s = ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.2f}"
            if p < 0.01:
                s += "*"
            ax.text(k, i, s, ha="center", va="center", fontsize=9,
                    color="#ffffff" if abs(v) > 4.6 else INK)
    ax.set_xticks(range(3))
    ax.set_xticklabels([COND_LABELS[c] for c in CONDS], fontsize=9.5, color=INK2)
    ax.xaxis.set_ticks_position("top")
    ax.set_yticks([])
    tr = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for i, (jid, jname, logo) in enumerate(JUDGES):
        ax.add_artist(AnnotationBbox(logo_box(logo, 10), (-0.40, i), xycoords=tr,
                                     frameon=False, box_alignment=(0.5, 0.5),
                                     annotation_clip=False))
        ax.text(-0.355, i, jname, transform=tr, ha="left", va="center",
                fontsize=9.5, color=INK, clip_on=False)
    for s in ax.spines.values():
        s.set_visible(False)
    cax = fig.add_axes([0.88, 0.18, 0.022, 0.60])
    cb = fig.colorbar(im, cax=cax)
    cb.outline.set_visible(False)
    cb.set_ticks([-8, -4, 0, 4, 8])
    cax.tick_params(length=0, labelsize=8)
    cax.set_title("shift\n(points)", fontsize=8, color=MUTED, pad=6)
    ax.text(0.0, -0.10, "* p < 0.01 (Wilcoxon signed-rank, permutation)",
            transform=ax.transAxes, fontsize=8, color=MUTED, ha="left", va="top")
    return drawn


# ------------------------------------------------------------ fig2D dumbbell
def fig2D():
    fig, ax = plt.subplots(figsize=(6.3, 4.4))
    fig.subplots_adjust(left=0.245, right=0.97, top=0.90, bottom=0.115)
    drawn = {}
    offs = {"iast": 0.20, "ascii": 0.0, "hinglish": -0.20}
    tr = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for gi, (jid, jname, logo) in enumerate(JUDGES):
        y0 = -gi
        deva = ANALYSIS[jid]["conditions"]["iast"]["mean_deva"]
        drawn[(jname, "deva")] = deva
        for c in CONDS:
            d = ANALYSIS[jid]["conditions"][c]
            y = y0 + offs[c]
            ax.plot([deva, d["mean_cond"]], [y, y], lw=1.1, color=FAINT, zorder=2)
            ax.plot([d["mean_cond"]], [y], "o", ms=6, color=COND_COLORS[c],
                    mec="#ffffff", mew=0.9, zorder=4)
            drawn[(jname, c)] = d["mean_cond"]
        # baseline marker spans the three condition rows
        ax.plot([deva, deva], [y0 - 0.27, y0 + 0.27], lw=2.0, color=INK, zorder=3,
                solid_capstyle="round")
        ax.add_artist(AnnotationBbox(logo_box(logo, 10), (-0.235, y0), xycoords=tr,
                                     frameon=False, box_alignment=(0.5, 0.5),
                                     annotation_clip=False))
        ax.text(-0.205, y0, jname, transform=tr, ha="left", va="center",
                fontsize=9.5, color=INK, clip_on=False)
        if gi < len(JUDGES) - 1:
            ax.axhline(y0 - 0.5, color=RULE, lw=0.6, zorder=1)
    # annotate the Flash row
    f = ANALYSIS["gemini-3.6-flash"]["conditions"]
    ax.annotate("same answers, rewritten in\nroman script: Flash adds\n+2.2 to +3.4 points",
                xy=(f["iast"]["mean_cond"] + 0.35, 0.20), xytext=(61.8, -0.05),
                fontsize=8.6, color=INK2, ha="left", va="top",
                arrowprops=dict(arrowstyle="-", lw=0.8, color=FAINT,
                                shrinkA=2, shrinkB=2))
    ax.text(ANALYSIS["gemini-3.6-flash"]["conditions"]["iast"]["mean_deva"] - 0.4,
            0.44, "Devanagari\nbaseline", ha="right", va="bottom", fontsize=8,
            color=MUTED)
    cond_key(ax, 0.70, 0.055, gap=0.115)
    ax.set_yticks([])
    ax.set_ylim(-5.55, 0.95)
    ax.set_xlim(42, 70)
    ax.set_xlabel("mean judge score (points on the 0–100 scale), axis clipped to 42–70")
    ax.spines["left"].set_visible(False)
    return drawn


# --------------------------------------------------------------- fig3B bars
FLASH_PRO = [("gemini-3.6-flash", "Gemini 3.6 Flash"),
             ("gemini-3.1-pro-preview", "Gemini 3.1 Pro")]


def fig3B():
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.9), sharey=True,
                             gridspec_kw=dict(wspace=0.10))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.86, bottom=0.17)
    drawn = {}
    bw = 0.24
    offs = {"iast": -bw, "ascii": 0.0, "hinglish": bw}
    for ax, (jid, jname) in zip(axes, FLASH_PRO):
        for ti, t in enumerate(TIERS):
            for c in CONDS:
                d = ANALYSIS[jid]["conditions"][c]["by_tier"][t]
                m, (lo, hi) = d["mean_shift"], d["ci95"]
                drawn[(jname, t, c)] = (m, lo, hi)
                x = ti + offs[c]
                ax.bar(x, m, width=bw * 0.86, color=COND_COLORS[c], zorder=3)
                ax.plot([x, x], [lo, hi], lw=1.0, color=INK2, zorder=4,
                        solid_capstyle="butt")
        style.zero_rule(ax, "y")
        ax.set_xticks(range(3))
        ax.set_xticklabels(TIERS)
        ax.set_xlabel("response quality tier")
        ax.set_title(jname, fontsize=10.5, color=INK, pad=8)
        ax.set_xlim(-0.55, 2.55)
    axes[0].set_ylabel("score shift (points)")
    axes[0].set_ylim(-3.2, 11.6)
    cond_key(axes[0], 0.03, 0.955, gap=0.21)
    return drawn


# --------------------------------------------------------------- fig3C slope
def fig3C():
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.0), sharey=True,
                             gridspec_kw=dict(wspace=0.34))
    fig.subplots_adjust(left=0.085, right=0.90, top=0.86, bottom=0.17)
    drawn = {}
    x = np.arange(3)
    for ax, (jid, jname) in zip(axes, FLASH_PRO):
        ends = []
        for c in CONDS:
            bt = ANALYSIS[jid]["conditions"][c]["by_tier"]
            m = [bt[t]["mean_shift"] for t in TIERS]
            lo = [bt[t]["ci95"][0] for t in TIERS]
            hi = [bt[t]["ci95"][1] for t in TIERS]
            for t, mm, l, h in zip(TIERS, m, lo, hi):
                drawn[(jname, t, c)] = (mm, l, h)
            ax.fill_between(x, lo, hi, color=COND_COLORS[c], alpha=0.13, lw=0,
                            zorder=2)
            ax.plot(x, m, lw=1.6, color=COND_COLORS[c], zorder=4)
            ax.plot(x, m, "o", ms=4.5, color=COND_COLORS[c], mec="#ffffff",
                    mew=0.8, zorder=5)
            ends.append((c, m[-1]))
        ys = stack_apart([e[1] for e in ends], 1.15)
        for (c, yv), yl in zip(ends, ys):
            ax.annotate(COND_LABELS[c], xy=(2.02, yv), xytext=(2.14, yl),
                        fontsize=9, color=COND_COLORS[c], va="center",
                        annotation_clip=False,
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=FAINT,
                                        shrinkA=0, shrinkB=1))
        style.zero_rule(ax, "y")
        ax.set_xticks(x)
        ax.set_xticklabels(TIERS)
        ax.set_xlabel("response quality tier")
        ax.set_title(jname, fontsize=10.5, color=INK, pad=8)
        ax.set_xlim(-0.15, 2.15)
    axes[0].set_ylim(-3.2, 11.6)
    axes[0].set_ylabel("score shift (points)")
    fm = ANALYSIS["gemini-3.6-flash"]["conditions"]["iast"]["by_tier"]["medium"]
    axes[0].annotate("peak at medium:\nthe bias lives in the\nambiguous middle",
                     xy=(1.04, fm["mean_shift"] + 0.3), xytext=(1.42, 9.6),
                     fontsize=8.6, color=INK2, ha="left", va="top",
                     arrowprops=dict(arrowstyle="-", lw=0.8, color=FAINT,
                                     shrinkA=2, shrinkB=3))
    return drawn


# ----------------------------------------------------------------- fig3D dot
def fig3D():
    fig, ax = plt.subplots(figsize=(6.3, 3.3))
    fig.subplots_adjust(left=0.175, right=0.975, top=0.88, bottom=0.145)
    drawn = {}
    offs = {"iast": 0.22, "ascii": 0.0, "hinglish": -0.22}
    rows = [(t, jid, jn) for t in TIERS
            for jid, jn in [("gemini-3.6-flash", "Flash"),
                            ("gemini-3.1-pro-preview", "Pro")]]
    tr = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for ri, (t, jid, jn) in enumerate(rows):
        y0 = -ri
        for c in CONDS:
            d = ANALYSIS[jid]["conditions"][c]["by_tier"][t]
            m, (lo, hi) = d["mean_shift"], d["ci95"]
            drawn[(t, jn, c)] = (m, lo, hi)
            y = y0 + offs[c]
            ax.plot([lo, hi], [y, y], lw=1.6, color=COND_COLORS[c], zorder=3,
                    solid_capstyle="round")
            ax.plot([m], [y], "o", ms=5, color=COND_COLORS[c], mec="#ffffff",
                    mew=0.9, zorder=4)
        ax.text(-0.02, y0, jn, transform=tr, ha="right", va="center",
                fontsize=9, color=MUTED)
        if ri % 2 == 1 and ri < len(rows) - 1:
            ax.axhline(y0 - 0.5, color=RULE, lw=0.8, zorder=1)
    for gi, t in enumerate(TIERS):
        yc = -(2 * gi) - 0.5
        ax.text(-0.135, yc, t, transform=tr, ha="center", va="center",
                fontsize=9.5, color=INK, rotation=90)
    ax.text(-0.135, 1.06, "tier", transform=ax.transAxes, ha="center",
            fontsize=8.5, color=MUTED)
    style.zero_rule(ax, "x")
    ax.set_yticks([])
    ax.set_ylim(-5.55, 0.55)
    ax.set_xlim(-3.4, 12.2)
    ax.set_xticks(range(-2, 13, 2))
    ax.set_xlabel("score shift, romanized minus Devanagari (points), 95% CI")
    ax.spines["left"].set_visible(False)
    cond_key(ax, 0.615, 0.055, gap=0.135)
    return drawn


if __name__ == "__main__":
    for fn, out in [(fig2B, "fig2B_bars.png"), (fig2C, "fig2C_heatmap.png"),
                    (fig2D, "fig2D_dumbbell.png"), (fig3B, "fig3B_bars.png"),
                    (fig3C, "fig3C_slope.png"), (fig3D, "fig3D_dot.png")]:
        drawn = fn()
        print(f"--- {out} drawn numbers ---")
        for k, v in drawn.items():
            print("   ", k, v)
        # note: fn() built the figure; save the current one
        save(plt.gcf(), out)
