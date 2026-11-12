"""P8 figures 1-4, all drawn from numbers.json (itself derived from the frozen CSVs).

fig1_spectrum.pdf      twelve conventions: ice/water ratio with 95 % intervals
fig2_endpoints.pdf     water and ice X against truth definition, with intervals
fig3_branch.pdf        m35_snowpath composition and within-branch X
fig4_axes.pdf          which axis moves the contrast
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# numbers.json lives at the paper root; search root then cwd then script dir.
for cand in (os.path.join(ROOT, "numbers.json"),
             os.path.join(os.getcwd(), "numbers.json"),
             os.path.join(HERE, "numbers.json")):
    if os.path.exists(cand):
        N = json.load(open(cand, encoding="utf-8"))
        break
else:
    raise SystemExit("numbers.json not found in paper root, cwd or code/")
FIG = os.path.join(ROOT, "figs")   # figures are written beside the manuscript
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.linewidth": 0.7,
    "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "figure.dpi": 300, "savefig.bbox": "tight",
    "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
})

T1 = N["table1"]
C_ICE, C_WATER, C_GREY = "#1f4e79", "#c0504d", "#7f7f7f"
POOLNAME = {"prof": "profile", "cell": "cell", "area": "area"}


def label(r):
    tr = "thick" if r["truth"] == "thick" else "any"
    cl = "conf." if r["clear"] == "clear_conf" else "conf.+prob."
    return tr, cl, POOLNAME[r["pool"]]


# ------------------------------------------------------------------ Fig 1
def fig1():
    rs = sorted(T1, key=lambda r: r["ratio"])
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    ys = np.arange(len(rs))
    for y, r in zip(ys, rs):
        cross = r["ratio_lo"] < 1 < r["ratio_hi"]
        col = C_WATER if cross else (C_ICE if r["truth"] == "thick" else C_GREY)
        ax.plot([r["ratio_lo"], r["ratio_hi"]], [y, y], color=col, lw=1.1,
                solid_capstyle="butt", zorder=2)
        ax.plot(r["ratio"], y, "o", ms=4.2, color=col, zorder=3)
    ax.axvline(1.0, color="k", lw=0.9, ls=(0, (4, 2)), zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(0.7, 14)
    ax.set_xticks([0.8, 1, 1.5, 2, 3, 5, 8, 12])
    ax.set_xticklabels(["0.8", "1", "1.5", "2", "3", "5", "8", "12"])
    ax.set_yticks(ys)
    ax.set_yticklabels(["{:s}, {:s}, {:s}".format(*label(r)) for r in rs],
                       fontsize=6.8)
    ax.set_xlabel("ice $X$ / water $X$  (log scale)")
    ax.set_ylim(-0.8, len(rs) - 0.2)
    ax.grid(axis="x", color="0.9", lw=0.5, zorder=0)
    for txt, col in [("thick-cloud truth", C_ICE),
                     ("any-cloud truth", C_GREY)]:
        ax.plot([], [], color=col, lw=1.4, label=txt)
    ax.plot([], [], "o-", color=C_WATER, lw=1.4, ms=4,
            label="interval includes unity")
    ax.legend(loc="lower right", frameon=False, handlelength=1.6, fontsize=6.4)
    fig.savefig(os.path.join(FIG, "fig1_spectrum.pdf"))
    plt.close(fig)


# ------------------------------------------------------------------ Fig 2
def fig2():
    sub = [r for r in T1 if r["pool"] == "prof"]
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.9), sharey=True)
    fig.subplots_adjust(wspace=0.10)
    for ax, which, ttl in [(axes[0], "water", "(a) open water, $n$ = 2,045"),
                           (axes[1], "ice", "(b) sea ice, $n$ = 1,441")]:
        for r in sub:
            x = (0.0 if r["truth"] == "thick" else 1.0) + \
                (-0.11 if r["clear"] == "clear_conf" else 0.11)
            col = C_ICE if r["truth"] == "thick" else C_WATER
            filled = r["clear"] == "clear_incl"
            ax.errorbar(x, r[which], yerr=[[r[which] - r[f"{which}_lo"]],
                                           [r[f"{which}_hi"] - r[which]]],
                        fmt="o" if filled else "s", ms=4.5, color=col,
                        ecolor=col, elinewidth=1.0, capsize=2.5, zorder=3,
                        mfc=col if filled else "white", mew=1.0)
        ax.set_xticks([0.0, 1.0])
        ax.set_xticklabels(["thick-cloud\ntruth", "any-cloud\ntruth"], fontsize=7)
        ax.set_xlim(-0.45, 1.45)
        ax.set_title(ttl, fontsize=8)
        ax.grid(axis="y", color="0.9", lw=0.5, zorder=0)
    axes[0].set_ylabel("false-clear fraction $X$")
    axes[0].set_ylim(0, 0.62)
    wt = [r for r in sub if r["truth"] == "thick" and r["clear"] == "clear_incl"][0]
    wa = [r for r in sub if r["truth"] == "any" and r["clear"] == "clear_incl"][0]
    xb = 0.62
    axes[0].plot([0.11, xb], [wt["water_hi"]] * 2, ls=":", lw=0.6, color="k")
    axes[0].plot([1.11, xb], [wa["water_lo"]] * 2, ls=":", lw=0.6, color="k")
    axes[0].annotate("", xy=(xb, wa["water_lo"]), xytext=(xb, wt["water_hi"]),
                     arrowprops=dict(arrowstyle="<->", lw=0.7, color="k"))
    axes[0].text(xb + 0.04, 0.5 * (wa["water_lo"] + wt["water_hi"]),
                 "gap\n0.047", fontsize=6.2, ha="left", va="center")
    axes[0].plot([], [], "o", color="0.3", label="confident + probably clear")
    axes[0].plot([], [], "s", color="0.3", mfc="white", mew=1.0,
                 label="confident clear only")
    axes[0].legend(loc="upper left", frameon=False, handletextpad=0.4)
    fig.savefig(os.path.join(FIG, "fig2_endpoints.pdf"))
    plt.close(fig)


# ------------------------------------------------------------------ Fig 3
def fig3():
    bx = N["branch_x"]
    comp = N["branch"]["composition"]["Jul_sp1"], N["branch"]["composition"]["Jul_sp0"]
    sp1, sp0 = comp
    keys = ["ice", "partial", "water", "mixed"]
    cols = {"ice": "#4f81bd", "partial": "#9bbb59", "water": "#c0504d",
            "mixed": "#bfbfbf"}
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.8),
                             gridspec_kw=dict(width_ratios=[1.05, 1]))
    fig.subplots_adjust(wspace=0.62)
    ax = axes[0]
    for y, d, nm, n in [(1, sp1, "$m_{\\mathrm{snowpath}}$ = 1", 3689),
                        (0, sp0, "$m_{\\mathrm{snowpath}}$ = 0", 557)]:
        left = 0.0
        for k in keys:
            v = 100 * d.get(k, 0.0)
            if v <= 0:
                continue
            ax.barh(y, v, left=left, color=cols[k], edgecolor="white", lw=0.4,
                    height=0.55)
            if v > 7:
                ax.text(left + v / 2, y, "{:.0f}".format(v), ha="center",
                        va="center", fontsize=6.2, color="white")
            left += v
        ax.text(-2, y, nm + "\n$n$ = {:,}".format(n), ha="right", va="center",
                fontsize=6.5)
    ax.set_yticks([])
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlabel("share of profiles in the branch (%)")
    ax.set_title("(a) what the branch contains, July", fontsize=8)
    ax.spines["left"].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=cols[k]) for k in keys]
    ax.legend(handles, keys, ncol=4, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, 1.02), handlelength=0.9, handletextpad=0.4)

    ax = axes[1]
    items = [("water, branch 1", bx["sp1_water"], C_WATER, "66 of 789"),
             ("ice, branch 1", bx["sp1_ice"], C_ICE, "9 of 40"),
             ("ice, branch 0", bx["sp0_ice"], C_GREY, "163 of 422")]
    for i, (nm, d, col, cnt) in enumerate(items):
        ax.errorbar(d["X"], i,
                    xerr=[[d["X"] - d["lo"]], [d["hi"] - d["X"]]],
                    fmt="o", ms=4.5, color=col, ecolor=col, elinewidth=1.0,
                    capsize=2.5)
        ax.text(d["hi"] + 0.012, i, cnt, va="center", fontsize=6.2)
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([i[0] for i in items], fontsize=6.8)
    ax.set_xlim(0, 0.58)
    ax.set_ylim(-0.6, 2.6)
    ax.set_xlabel("$X$: share of clear calls that are cloud")
    ax.set_title("(b) inside the branch, Wilson 95 % intervals", fontsize=8)
    ax.grid(axis="x", color="0.9", lw=0.5)
    fig.savefig(os.path.join(FIG, "fig3_branch.pdf"))
    plt.close(fig)


# ------------------------------------------------------------------ Fig 4
def fig4():
    a = N["axis"]
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.7),
                             gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax = axes[0]
    # 冰面与水面的移动（剖面池化）
    for key, col, nm in [("ice", C_ICE, "sea ice"), ("water", C_WATER, "open water")]:
        ax.plot([0, 1], [a["base"][key], a["truth_only"][key]], "-o", ms=4,
                lw=1.2, color=col)
        ax.plot([0, 1], [a["base"][key], a["clear_only"][key]], ":s", ms=3.4,
                lw=1.0, color=col, mfc="white")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["baseline\nthick cloud,\nconf.+prob.",
                        "one axis moved"], fontsize=6.2)
    ax.set_xlim(-0.12, 1.42)
    ax.set_ylim(0, 0.52)
    ax.set_ylabel("false-clear fraction $X$")
    ax.annotate("+0.168", xy=(1, (a["base"]["water"] + a["truth_only"]["water"]) / 2),
                xytext=(6, -4), textcoords="offset points", fontsize=6.4,
                color=C_WATER)
    ax.annotate("+0.056", xy=(1, (a["base"]["ice"] + a["truth_only"]["ice"]) / 2),
                xytext=(6, 4), textcoords="offset points", fontsize=6.4, color=C_ICE)
    ax.annotate("+0.001", xy=(1, a["clear_only"]["water"]),
                xytext=(-4, 7), textcoords="offset points", fontsize=6.2,
                ha="right", color=C_WATER)
    ax.text(0.03, 0.30, "sea ice", color=C_ICE, fontsize=7)
    ax.text(0.03, 0.13, "open water", color=C_WATER, fontsize=7)
    ax.set_title("(a) moving one axis at a time", fontsize=8)
    ax.grid(axis="y", color="0.9", lw=0.5)

    ax = axes[1]
    vals = [a["base"]["ratio"], a["clear_only"]["ratio"],
            a["truth_only"]["ratio"], a["both"]["ratio"]]
    nms = ["baseline", "clear-sky\naxis", "truth\naxis", "both"]
    cols = [C_GREY, C_GREY, C_WATER, C_WATER]
    ax.bar(range(4), vals, color=cols, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.08, "{:.2f}".format(v), ha="center", fontsize=6.6)
    ax.axhline(1.0, color="k", lw=0.8, ls=(0, (4, 2)))
    ax.plot([], [], color="k", lw=0.8, ls=(0, (4, 2)), label="unity (no contrast)")
    ax.legend(loc="upper right", frameon=False, fontsize=6.2)
    ax.set_xticks(range(4))
    ax.set_xticklabels(nms, fontsize=6.2)
    ax.set_ylim(0, 5.3)
    ax.set_ylabel("ice/water ratio (profile pooling)")
    ax.set_title("(b) what each axis does to the ratio", fontsize=8)
    ax.grid(axis="y", color="0.9", lw=0.5)
    fig.savefig(os.path.join(FIG, "fig4_axes.pdf"))
    plt.close(fig)


fig1()
fig2()
fig3()
fig4()
print("figures written to", FIG)
for f in sorted(os.listdir(FIG)):
    print(f, os.path.getsize(os.path.join(FIG, f)))
