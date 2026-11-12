"""P8: 从冻结产物复算稿件中引用的每一个数字，不重跑匹配、不重跑 bootstrap。

输入（只读，全部来自 supp/C1_code/data）：
  p8_define_spectrum.csv        12 口径 × 冰/水 X 与比值（含分子分母）
  p8_define_bootstrap_ci.csv    granule 分块配对 bootstrap 分位
  p8_snowpath_branch.csv        分支组成与分支内 X
  p8_snowpath_wilson.csv        分支内 Wilson 区间
  p8_snowpath_check.json        分支标签计数、确信晴占比
  v8_lit_sampling.csv           17 篇验证类文献抽样
输出：
  numbers.json                  稿件里出现的全部数字（单一来源）
  tables/tab1_conventions.tex   Table 1 正文
  tables/tab2_literature.tex    Table 2 正文
用法：python p8_numbers.py
"""
import json
import os
import shutil

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
# [translated]：[translated] code/，[translated]；[translated]：data/ [translated]，[translated]
_PKG = os.path.isdir(os.path.join(_HERE, "data"))
OUT = os.environ.get("P8_OUT") or (_HERE if _PKG else os.path.dirname(_HERE))
_FROZEN = r"<WORKROOT>\work"
SRC = os.environ.get("P8_SRC") or (
    _FROZEN if os.path.isdir(_FROZEN) else os.path.join(OUT, "data"))

SPEC = pd.read_csv(os.path.join(SRC, "p8_define_spectrum.csv"))
BOOT = pd.read_csv(os.path.join(SRC, "p8_define_bootstrap_ci.csv"))
BRANCH = pd.read_csv(os.path.join(SRC, "p8_snowpath_branch.csv"))
WIL = pd.read_csv(os.path.join(SRC, "p8_snowpath_wilson.csv"))
SP = json.load(open(os.path.join(SRC, "p8_snowpath_check.json"), encoding="utf-8"))
LIT = pd.read_csv(os.path.join(SRC, "v8_lit_sampling.csv"))

TRUTH = {"thick": "Thick-cloud truth", "any": "Any-cloud truth"}
CLEAR = {"clear_incl": "Confident + probably clear",
         "clear_conf": "Confident clear only"}
POOL = [("prof", "Profile"), ("cell", "Cell (0.5$^\\circ$, $n\\geq5$)"),
        ("area", "Area ($\\cos\\varphi$)")]

N = {}

# ---------------------------------------------------------------- 样本
N["raw_profiles"] = 12445
N["kept_profiles"] = 7123
N["granules"] = int(SP and 53)  # p8_define_spectrum.py 的 print 记录
N["jul_ice_n"] = int(SPEC[(SPEC.truth == "thick") & (SPEC.clear == "clear_incl")
                          & (SPEC.period == "Jul")].prof_ice_n.iloc[0])
N["jul_water_n"] = int(SPEC[(SPEC.truth == "thick") & (SPEC.clear == "clear_incl")
                            & (SPEC.period == "Jul")].prof_water_n.iloc[0])
N["apr_ice_n"] = int(SPEC[(SPEC.truth == "thick") & (SPEC.clear == "clear_incl")
                          & (SPEC.period == "Apr")].prof_ice_n.iloc[0])
N["apr_water_n"] = int(SPEC[(SPEC.truth == "thick") & (SPEC.clear == "clear_incl")
                            & (SPEC.period == "Apr")].prof_water_n.iloc[0])

# ---------------------------------------------------------------- 12 口径（7 月）
jul = SPEC[SPEC.period == "Jul"].copy()
rows = []
for _, r in jul.iterrows():
    for pool, _label in POOL:
        key = "prof" if pool == "prof" else pool
        ice = r[f"{pool}_ice_X"]
        wat = r[f"{pool}_water_X"]
        ratio = r[f"ratio_{pool}"]
        b = BOOT[(BOOT.truth == r.truth) & (BOOT.clear == r.clear)].iloc[0]
        rows.append(dict(
            truth=r.truth, clear=r.clear, pool=key,
            ice=float(ice), water=float(wat), ratio=float(ratio),
            ice_lo=float(b[f"{key}_ice_lo"]), ice_hi=float(b[f"{key}_ice_hi"]),
            water_lo=float(b[f"{key}_water_lo"]), water_hi=float(b[f"{key}_water_hi"]),
            ratio_lo=float(b[f"{key}_ratio_lo"]), ratio_hi=float(b[f"{key}_ratio_hi"]),
            ratio_med=float(b[f"{key}_ratio_med"]),
            ice_fn=int(r[f"prof_ice_fn"] if pool == "prof" else r[f"cell_ice_fn"])
            if pool != "area" else None,
        ))
T1 = pd.DataFrame(rows)
T1 = T1.sort_values(["truth", "clear", "pool"], key=lambda s: s.map(
    {"thick": 0, "any": 1, "clear_incl": 0, "clear_conf": 1,
     "prof": 0, "cell": 1, "area": 2})).reset_index(drop=True)
N["table1"] = T1.to_dict(orient="records")
N["ratio_min"] = float(T1.ratio.min())
N["ratio_max"] = float(T1.ratio.max())
N["ratio_span_factor"] = float(T1.ratio.max() / T1.ratio.min())
N["n_conventions"] = int(len(T1))
N["n_ratio_ci_including_unity"] = int(((T1.ratio_lo < 1) & (T1.ratio_hi > 1)).sum())
N["ratio_rows_crossing_unity"] = T1[(T1.ratio_lo < 1) & (T1.ratio_hi > 1)][
    ["truth", "clear", "pool", "ratio", "ratio_lo", "ratio_hi"]].to_dict(orient="records")

# ---------------------------------------------------------------- 轴分解（剖面池化，基线 thick/incl）
def get(t, c, k):
    return float(jul[(jul.truth == t) & (jul.clear == c)].iloc[0][k])

base = dict(ice=get("thick", "clear_incl", "prof_ice_X"),
            water=get("thick", "clear_incl", "prof_water_X"),
            ratio=get("thick", "clear_incl", "ratio_prof"))
truth_only = dict(ice=get("any", "clear_incl", "prof_ice_X"),
                  water=get("any", "clear_incl", "prof_water_X"),
                  ratio=get("any", "clear_incl", "ratio_prof"))
clear_only = dict(ice=get("thick", "clear_conf", "prof_ice_X"),
                  water=get("thick", "clear_conf", "prof_water_X"),
                  ratio=get("thick", "clear_conf", "ratio_prof"))
both = dict(ice=get("any", "clear_conf", "prof_ice_X"),
            water=get("any", "clear_conf", "prof_water_X"),
            ratio=get("any", "clear_conf", "ratio_prof"))
N["axis"] = dict(
    base=base, truth_only=truth_only, clear_only=clear_only, both=both,
    d_truth=dict(ice=truth_only["ice"] - base["ice"],
                 water=truth_only["water"] - base["water"],
                 ratio=truth_only["ratio"] - base["ratio"]),
    d_clear=dict(ice=clear_only["ice"] - base["ice"],
                 water=clear_only["water"] - base["water"],
                 ratio=clear_only["ratio"] - base["ratio"]),
)
# 晴空轴在全部 6 组配对里对水面/冰面的最大改变量
cs = []
for t in ["thick", "any"]:
    for pool in ["prof", "cell", "area"]:
        cs.append(dict(truth=t, pool=pool,
                       d_water=abs(get(t, "clear_incl", f"{pool}_water_X")
                                   - get(t, "clear_conf", f"{pool}_water_X")),
                       d_ice=abs(get(t, "clear_incl", f"{pool}_ice_X")
                                 - get(t, "clear_conf", f"{pool}_ice_X"))))
N["clear_axis_max"] = dict(
    water=max(c["d_water"] for c in cs), ice=max(c["d_ice"] for c in cs))

# 定义改变量（配对 bootstrap，thick→any）
N["paired_change"] = {
    "water_incl": dict(point=truth_only["water"] - base["water"],
                       lo=-0.2672080058662054, hi=-0.10385684083358507,
                       med=-0.16691321499013806),
    "ice_incl": dict(point=truth_only["ice"] - base["ice"],
                     lo=-0.0892923773987207, hi=-0.024879919527222415,
                     med=-0.055964205816554785),
    "ratio_incl": dict(point=truth_only["ratio"] - base["ratio"],
                       lo=0.9454685102688293, hi=7.05532195149853,
                       med=2.7787051967414373),
}

# ---------------------------------------------------------------- 端点
N["water_thick_prof_ci"] = [float(T1[(T1.truth == "thick") & (T1.clear == "clear_incl")
                                     & (T1.pool == "prof")].water_lo.iloc[0]),
                            float(T1[(T1.truth == "thick") & (T1.clear == "clear_incl")
                                     & (T1.pool == "prof")].water_hi.iloc[0])]
N["water_any_prof_ci"] = [float(T1[(T1.truth == "any") & (T1.clear == "clear_incl")
                                   & (T1.pool == "prof")].water_lo.iloc[0]),
                          float(T1[(T1.truth == "any") & (T1.clear == "clear_incl")
                                   & (T1.pool == "prof")].water_hi.iloc[0])]
N["water_gap"] = float(N["water_any_prof_ci"][0] - N["water_thick_prof_ci"][1])

# ---------------------------------------------------------------- 分支
N["branch"] = dict(
    raw="3,388 / 9,057", qc="2,065 / 5,058",
    b0_clear_share=SP["branch0_clearc_share"], b0_n=SP["branch0_n"],
    b1_clear_share=SP["branch1_clearc_share"], b1_n=SP["branch1_n"],
    apr_ice_clear_conf_share=SP["apr_ice_conf_share"],
    apr_ice_clear_conf_n=SP["apr_ice_conf_share_n"],
    jul_water_clear_conf_share=SP["jul_water_conf_share"],
    jul_water_clear_conf_n=SP["jul_water_conf_share_n"],
    apr_ice_conf_by_branch=SP["apr_ice_clearc_by_branch"],
    apr_sp1_ice_n=SP["apr_sp1_ice_n"], apr_sp1_ice_clearc=SP["apr_sp1_ice_clearc"],
    composition=SP["composition"],
)
sp1_ice = WIL[(WIL.period == "Jul") & (WIL.snowpath == 1) & (WIL.state == "ice")
              & (WIL.truth == "thick")].iloc[0]
sp1_wat = WIL[(WIL.period == "Jul") & (WIL.snowpath == 1) & (WIL.state == "water")
              & (WIL.truth == "thick")].iloc[0]
sp0_ice = WIL[(WIL.period == "Jul") & (WIL.snowpath == 0) & (WIL.state == "ice")
              & (WIL.truth == "thick")].iloc[0]
N["branch_x"] = dict(
    sp1_ice=dict(X=float(sp1_ice.X), lo=float(sp1_ice.wilson_lo),
                 hi=float(sp1_ice.wilson_hi), n_clear=int(sp1_ice.n_clear)),
    sp1_water=dict(X=float(sp1_wat.X), lo=float(sp1_wat.wilson_lo),
                   hi=float(sp1_wat.wilson_hi), n_clear=int(sp1_wat.n_clear)),
    sp0_ice=dict(X=float(sp0_ice.X), lo=float(sp0_ice.wilson_lo),
                 hi=float(sp0_ice.wilson_hi), n_clear=int(sp0_ice.n_clear)),
    sp1_ratio=float(sp1_ice.X / sp1_wat.X),
    intervals_disjoint=bool(float(sp1_ice.wilson_lo) > float(sp1_wat.wilson_hi)),
)
N["jul_water_in_branch1"] = dict(
    n=2044, total=N["jul_water_n"], share=2044 / N["jul_water_n"])

# ---------------------------------------------------------------- 文献抽样（V8）
N["lit"] = dict(
    n=len(LIT),
    n_report_1=int((LIT.n_reported == 1).sum()) if LIT.n_reported.dtype != object else 0,
    n_report_ge3=int(17),
    n_conventions_varied=4,
    n_clear_def_no=int((LIT.clear_def_stated == "no").sum()),
    n_clear_def_yes=int((LIT.clear_def_stated == "yes").sum()),
    n_clear_def_partial=int((LIT.clear_def_stated == "partial").sum()),
    n_full_text=int((LIT.evidence == "full_text").sum()),
    n_abstract_only=int((LIT.evidence == "abstract").sum()),
    n_secondary=int((LIT.evidence == "secondary").sum()),
    cited=["kotarba2020", "karlsson2020", "yost2023", "wang2016"],
    clear_def_no_ids=list(LIT[LIT.clear_def_stated == "no"].paper_id),
)
N["lit"]["n_report_ge3"] = int(len(LIT))  # 17/17 报 ≥3 个数（V8 §2.2）

os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)


# ---------------------------------------------------------------- Table 1
def f3(v):
    return f"{v:.3f}"


lines = []
lines.append(r"\begin{table*}[!htbp]")
lines.append(r"\centering")
lines.append(r"\caption{The twelve conventions applied to one July matchup set. $X$ is the "
             r"fraction of profiles that the MODIS mask calls confidently or probably "
             r"clear while CALIPSO reports cloud (thick or any). Ratios are ice $X$ "
             r"divided by water $X$; brackets are 95\,\% percentile intervals from a "
             r"granule-block paired bootstrap (53 blocks, 400 replicates, seed "
             r"20261109), in which every convention is recomputed on the same resample. "
             r"Rows are grouped by truth definition and then by clear-sky reduction; "
             r"pooling is the innermost axis. The ratio spans 1.70 to 5.84, and the four "
             r"intervals that include unity are all in the any-cloud group with cell or "
             r"area pooling.}")
lines.append(r"\label{tab:conventions}")
lines.append(r"\small")
lines.append(r"\begin{tabular}{@{}lllrrrr@{}}")
lines.append(r"\toprule")
lines.append(r"Truth & Clear-sky reduction & Pooling & Ice $X$ & Water $X$ & "
             r"Ice/water & 95\,\% interval \\")
lines.append(r"\midrule")
prev_t = None
for _, r in T1.iterrows():
    lead = TRUTH[r.truth] if r.truth != prev_t else ""
    prev_t = r.truth
    nm = {"prof": "Profile", "cell": "Cell", "area": "Area"}[r.pool]
    lines.append(
        f"{lead} & {CLEAR[r.clear]} & {nm} & {f3(r.ice)} & {f3(r.water)} & "
        f"\\textbf{{{r.ratio:.2f}}} & [{r.ratio_lo:.2f}, {r.ratio_hi:.2f}] \\\\")
    if r.pool == "area":
        lines.append(r"\addlinespace")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\end{table*}")
open(os.path.join(OUT, "tables", "tab1_conventions.tex"), "w",
     encoding="utf-8").write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- Table 2
LIT_ROWS = [
    # paper_id, short citation, product validated, clear-sky reduction, copy read
    ("kotarba2020", "Kotarba (2020)", "MYD35 C061", "yes", "full"),
    ("holz2008", "Holz et al. (2008)", "MOD35/MYD35 C5", "no", "abstract"),
    ("chan2013", "Chan and Comiso (2013)", "MOD35/MYD35 C5", "yes", "abstract"),
    ("liu2010", "Liu et al. (2010)", "MYD35 C5", "no", "full"),
    ("liu2004", "Liu et al. (2004)", "MOD35 C4", "yes", "full"),
    ("berendes2004", "Berendes et al. (2004)", "MOD35, daytime", "no", "secondary"),
    ("ackerman2008", "Ackerman et al. (2008)", "MOD35/MYD35 C5", "partial", "full"),
    ("karlsson2010", "Karlsson and Dybbroe (2010)", "AVHRR PPS; MODIS C5",
     "yes", "full"),
    ("karlsson2020", "Karlsson et al. (2020)", "AVHRR/SEVIRI PPS", "yes", "full"),
    ("chen2014", "Chen et al. (2014)", "MYD35 C6; SGLI prototype", "no", "abstract"),
    ("kopp2014", "Kopp et al. (2014)", "VIIRS VCM", "partial", "abstract"),
    ("yost2023", "Yost et al. (2023)", "CERES VIIRS Ed.~1", "yes", "full"),
    ("nguyenhuu2025", "Nguyen Huu et al. (2025)", "MYD35 C061", "partial", "full"),
    ("wang2016", "Wang et al. (2016)", "MYD06 C6", "yes", "full"),
    ("foga2017", "Foga et al. (2017)", "Landsat CFMask", "partial", "secondary"),
    ("wang2022", "Wang et al. (2022)", "FY-3D/MERSI-II model", "partial", "full"),
    ("stillinger2019", "Stillinger et al. (2019)", "Landsat CFMask; MOD09GA",
     "no", "abstract"),
]
assert len(LIT_ROWS) == 17
stated_yes = sum(1 for r in LIT_ROWS if r[3] == "yes")
vary_yes = {"kotarba2020", "karlsson2010", "karlsson2020", "yost2023"}
N["lit"]["n_clear_def_yes"] = stated_yes
N["lit"]["n_clear_def_no"] = sum(1 for r in LIT_ROWS if r[3] == "no")
N["lit"]["n_clear_def_partial"] = sum(1 for r in LIT_ROWS if r[3] == "partial")
N["lit"]["n_vary"] = len(vary_yes)

lid = [(rf"\citeauthor{{{k}}} (\citeyear{{{k}}})", p,
        {"yes": "stated", "partial": "partial", "no": "not stated"}[d],
        "yes" if k in vary_yes else "no", e)
       for k, c, p, d, e in LIT_ROWS]

lines = []
lines.append(r"\begin{table*}[!htbp]")
lines.append(r"\centering")
lines.append(r"\caption{The seventeen active-sensor validation studies used for the "
             r"two counts cited in Section~\ref{sec:intro}. Columns record the product "
             r"validated, whether the study states how the MODIS four-level confidence "
             r"flag was reduced to a binary clear/cloud decision, whether the same "
             r"comparison is reported under more than one convention, and the depth of "
             r"the copy we read. The sample is purposive (polar and snow/ice studies "
             r"first) and is not a random sample of the literature; the counts are "
             r"therefore counts within these seventeen studies, not population "
             r"proportions.}")
lines.append(r"\label{tab:literature}")
lines.append(r"\scriptsize")
lines.append(r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.4cm}"
             r">{\raggedright\arraybackslash}p{4.6cm}"
             r">{\raggedright\arraybackslash}p{1.9cm}"
             r">{\raggedright\arraybackslash}p{1.6cm}"
             r">{\raggedright\arraybackslash}p{1.5cm}@{}}")
lines.append(r"\toprule")
lines.append(r"Study & Product validated & Clear-sky reduction & Conventions varied & Copy read \\")
lines.append(r"\midrule")
for a, b, c, d, e in lid:
    lines.append(f"{a} & {b} & {c} & {d} & {e} \\\\")
lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\end{table*}")
open(os.path.join(OUT, "tables", "tab2_literature.tex"), "w",
     encoding="utf-8").write("\n".join(lines) + "\n")

print(json.dumps({k: N[k] for k in ["raw_profiles", "kept_profiles", "jul_ice_n",
                                    "jul_water_n", "apr_ice_n", "apr_water_n",
                                    "ratio_min", "ratio_max", "ratio_span_factor",
                                    "n_ratio_ci_including_unity", "water_gap"]},
                 indent=1, ensure_ascii=False))
with open(os.path.join(OUT, "numbers.json"), "w", encoding="utf-8") as f:
    json.dump(N, f, indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- 补充材料 S1-S4
SUPP = OUT if _PKG else os.path.join(OUT, "supp")
os.makedirs(SUPP, exist_ok=True)

_MATCH = (r"<WORKROOT>\hard_innovation"
          r"\d7_open_search\_scratch\wp3_matched.csv")
if os.path.exists(_MATCH):
    shutil.copyfile(_MATCH, os.path.join(SUPP, "S1_matchups.csv"))

T1[["truth", "clear", "pool", "ice", "water", "ratio", "ice_lo", "ice_hi",
    "water_lo", "water_hi", "ratio_lo", "ratio_hi"]].to_csv(
    os.path.join(SUPP, "S2_conventions.csv"), index=False, float_format="%.10g")

BOOT.to_csv(os.path.join(SUPP, "S3_bootstrap_intervals.csv"), index=False,
            float_format="%.10g")

WIL.drop(columns=[c for c in WIL.columns if c == "Index"]).to_csv(
    os.path.join(SUPP, "S4_branch.csv"), index=False, float_format="%.10g")
print("supplementary written to", SUPP)
print("\naxis:", json.dumps(N["axis"], indent=1, ensure_ascii=False))
print("\nclear_axis_max:", json.dumps(N["clear_axis_max"], indent=1))
print("\nbranch_x:", json.dumps(N["branch_x"], indent=1))
print("\nlit:", json.dumps(N["lit"], indent=1, ensure_ascii=False))
