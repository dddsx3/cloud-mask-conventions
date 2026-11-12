#!/usr/bin/env python3
"""Regenerate tables/tab1_conventions.tex and tables/tab3_metric.tex from
numbers.json (produced by p8_recompute.py).  Single source of truth."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N = json.load(open(os.path.join(ROOT, "numbers.json"), encoding="utf-8"))
T1 = N["table1"]
M = N["metric_axis_v2"]


def f3(v):
    return f"{v:.3f}"


def f2(v):
    return f"{v:.2f}"


# --------------------------------------------------------------- Table 1
rows = []
for r in T1:
    rows.append(r)
# sort by truth, clear, pool for stable display
order_t = {"thick": 0, "any": 1}
order_c = {"clear_incl": 0, "clear_conf": 1}
order_p = {"prof": 0, "cell": 1, "area": 2}
rows.sort(key=lambda r: (order_t[r["truth"]], order_c[r["clear"]], order_p[r["pool"]]))

rmin = N["ratio_min"]
rmax = N["ratio_max"]
ncross = N["n_ratio_ci_including_unity"]
cross_pool = ", ".join(sorted({f"{r['pool']} pooling" for r in N["ratio_rows_crossing_unity"]}))

lines = []
lines.append(r"\begin{table*}[!htbp]")
lines.append(r"\centering")
lines.append(
    r"\caption{The twelve conventions applied to one July matchup set. $X$ is the "
    r"fraction of the profiles called clear (confidently or probably) that CALIPSO "
    r"reports as cloudy (thick or any). Ratios are ice $X$ divided by water $X$; "
    r"brackets are 95\,\% percentile intervals from one granule-block bootstrap over "
    r"the 31 July CALIPSO granules (2{,}000 replicates, seed 20261110), in which every "
    r"convention, every pooling and both scores are recomputed on the same resample. "
    r"Rows are grouped by truth definition and then by clear-sky reduction; pooling is "
    r"the innermost axis. The ratio spans "
    f"{rmin:.2f} to {rmax:.2f}, and the {ncross} intervals that include unity are all "
    r"in the any-cloud group with " + cross_pool + r".}")
lines.append(r"\label{tab:conventions}")
lines.append(r"\small")
lines.append(r"\begin{tabular}{@{}lllrrrr@{}}")
lines.append(r"\toprule")
lines.append(r"Truth & Clear-sky reduction & Pooling & Ice $X$ & Water $X$ & "
             r"Ice/water & 95\,\% interval \\")
lines.append(r"\midrule")
prev_t = None
for r in rows:
    lead = r["truth"].replace("_", "-") + " truth" if r["truth"] != prev_t else ""
    prev_t = r["truth"]
    nm = {"prof": "Profile", "cell": "Cell", "area": "Area"}[r["pool"]]
    lines.append(
        f"{lead} & {r['clear'].replace('_',' ')} & {nm} & {f3(r['ice'])} & {f3(r['water'])} & "
        f"\\textbf{{{r['ratio']:.2f}}} & [{r['ratio_lo']:.2f}, {r['ratio_hi']:.2f}] \\\\")
    if r["pool"] == "area":
        lines.append(r"\addlinespace")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\end{table*}")
open(os.path.join(ROOT, "tables", "tab1_conventions.tex"), "w",
     encoding="utf-8").write("\n".join(lines) + "\n")
print("wrote tab1_conventions.tex  ratio range", round(rmin, 2), "-", round(rmax, 2),
      "crossing:", ncross)

# --------------------------------------------------------------- Table 3
def row_txt(truth, score, ice, water, ratio, ci):
    return (f"{truth} & {score} & {f3(ice)} & {f3(water)} & {ratio:.2f} & "
            f"[{ci[0]:.2f}, {ci[1]:.2f}] \\\\")

lines = []
lines.append(r"\begin{table}[!htbp]")
lines.append(r"\centering")
lines.append(
    r"\caption{The same July matchups scored two ways. $X$ divides by the profiles the "
    r"mask calls clear; $1-\text{recall}$ divides by the profiles the lidar calls "
    r"cloudy. The two scores therefore answer different questions and have different "
    r"denominators, which is the point of the table. Intervals are 95\,\% percentile "
    r"from the same granule-block bootstrap over the 31 July granules (2{,}000 "
    r"replicates, seed 20261110); each interval is computed on its own ratio, not from "
    r"two marginal intervals.}")
lines.append(r"\label{tab:metric}")
lines.append(r"\small")
lines.append(r"\begin{tabular}{@{}llrrrr@{}}")
lines.append(r"\toprule")
lines.append(r"Truth & Score & Ice & Water & Ice/water & 95\,\% interval \\")
lines.append(r"\midrule")
mt = M["thick"]; ma = M["any"]
lines.append(row_txt("Thick cloud", r"$X$ (share of clear calls that are wrong)",
                     mt["clear_incl"]["X_ice"], mt["clear_incl"]["X_water"],
                     mt["clear_incl"]["X_ratio"], mt["clear_incl"]["X_ci"]))
lines.append(row_txt("Thick cloud", r"$1-\text{recall}$ (share of cloudy profiles cleared)",
                     mt["clear_incl"]["omr_ice"], mt["clear_incl"]["omr_water"],
                     mt["clear_incl"]["omr_ratio"], mt["clear_incl"]["omr_ci"]))
lines.append(row_txt("Any cloud", r"$X$ (share of clear calls that are wrong)",
                     ma["clear_incl"]["X_ice"], ma["clear_incl"]["X_water"],
                     ma["clear_incl"]["X_ratio"], ma["clear_incl"]["X_ci"]))
lines.append(row_txt("Any cloud", r"$1-\text{recall}$ (share of cloudy profiles cleared)",
                     ma["clear_incl"]["omr_ice"], ma["clear_incl"]["omr_water"],
                     ma["clear_incl"]["omr_ratio"], ma["clear_incl"]["omr_ci"]))
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\end{table}")
open(os.path.join(ROOT, "tables", "tab3_metric.tex"), "w",
     encoding="utf-8").write("\n".join(lines) + "\n")
print("wrote tab3_metric.tex")
print("  thick X ratio", round(mt['clear_incl']['X_ratio'],2), "ci", [round(x,2) for x in mt['clear_incl']['X_ci']])
print("  thick 1-recall", round(mt['clear_incl']['omr_ratio'],2), "ci", [round(x,2) for x in mt['clear_incl']['omr_ci']])
print("  any X ratio", round(ma['clear_incl']['X_ratio'],2), "ci", [round(x,2) for x in ma['clear_incl']['X_ci']])
print("  any 1-recall", round(ma['clear_incl']['omr_ratio'],2), "ci", [round(x,2) for x in ma['clear_incl']['omr_ci']])
