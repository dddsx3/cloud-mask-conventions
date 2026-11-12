"""Exploration: verify every disputed number from S1 directly.
Temporary diagnostic; not a deliverable generator.
"""
import numpy as np
import pandas as pd

CSV = "supp/S1_matchups.csv"
d = pd.read_csv(CSV)
d["month"] = pd.to_datetime(d["time"]).dt.month

# ---- QC filter (abs dt, dcell) ----
q = d[(d.dt_sec.abs() <= 1200) & (d.dcell_km <= 20)].copy()
print("RAW rows:", len(d))
print("QC rows:", len(q), "granules:", q.cal_file.nunique())
jul = q[q.month == 7]
apr = q[q.month == 4]
print("July:", len(jul), "granules:", jul.cal_file.nunique())
print("April:", len(apr), "granules:", apr.cal_file.nunique())
print("m35_det unique:", d.m35_det.unique(), "in qc:", q.m35_det.unique())

# ---- dt distribution in July QC sample ----
ad = jul.dt_sec.abs()
print("\nJuly |dt| median:", ad.median(), " mean:", round(ad.mean(),1),
      " % >600:", round((ad>600).mean()*100,1), " % >900:", round((ad>900).mean()*100,1))
# July WITHOUT dcell filter
jul_nd = d[(d.month==7) & (d.dt_sec.abs()<=1200)]
ad2 = jul_nd.dt_sec.abs()
print("July (no dcell filter) |dt| median:", ad2.median(), " % >600:", round((ad2>600).mean()*100,1))

# ---- surface class definitions ----
def classify(df, rule):
    if rule == "paper":
        ice = (df.si >= 50) & (df.si != 255)
        water = df.si == 0
    elif rule == "raw":
        # R2 'raw si field': treat si>=50 ice, si<=50 water incl partials & 255?
        ice = df.si >= 50
        water = df.si < 50
    return ice, water

def ratio(df, truth, level, ice, water):
    clear = df.m35_lvl >= level
    sub = df
    ic, wc = sub[truth][ice].to_numpy(), sub[truth][water].to_numpy()
    icl, wcl = clear[ice].to_numpy(), clear[water].to_numpy()
    ix = (ic & icl).sum()/icl.sum()
    wx = (wc & wcl).sum()/wcl.sum()
    return ix, wx, ix/wx

print("\n=== Geometry axis, thick truth, clear-incl (level2), profile pooling ===")
for rule in ("paper","raw"):
    ice, water = classify(jul, rule)
    print(f"\n rule={rule}  July ice n={ice.sum()} water n={water.sum()}")
    for lo,hi in ((0,300),(300,900),(900,10**9)):
        m = (jul.dt_sec.abs()>lo)&(jul.dt_sec.abs()<=hi)
        sub = jul[m]
        if sub.empty: continue
        i,w,r = ratio(sub,"cal_thick",2,ice[m],water[m])
        print(f"  |dt| {lo}-{hi if hi<10**9 else 'inf'}  n={len(sub):5d}  iceX={i:.4f} waterX={w:.4f} ratio={r:.3f}")

# ---- profile-pooling baseline for both rules ----
print("\n=== Profile baseline (thick, clear_incl) ===")
for rule in ("paper","raw"):
    ice, water = classify(jul, rule)
    i,w,r = ratio(jul,"cal_thick",2,ice,water)
    print(f"  rule={rule}: iceX={i:.4f} waterX={w:.4f} ratio={r:.3f}")
