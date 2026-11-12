"""Test cell & area pooling reconstruction against frozen Table 1 point estimates."""
import numpy as np
import pandas as pd

CSV = "supp/S1_matchups.csv"
d = pd.read_csv(CSV)
d["month"] = pd.to_datetime(d["time"]).dt.month
q = d[(d.dt_sec.abs() <= 1200) & (d.dcell_km <= 20)].copy()
jul = q[q.month == 7].reset_index(drop=True)

# surface classes (paper rule)
jul["ice"] = (jul.si >= 50) & (jul.si != 255)
jul["water"] = jul.si == 0

# 0.5 deg cells
jul["clat"] = (np.floor(jul.lat / 0.5) * 0.5 + 0.25)
jul["clon"] = (np.floor(jul.lon / 0.5) * 0.5 + 0.25)
jul["cell"] = jul.clat.astype(str) + "," + jul.clon.astype(str)

# assign cell class: >=90% of profiles ice -> ice; >=90% water -> water; else none
g = jul.groupby("cell")
cell_n = g.size()
cell_ice = g["ice"].sum()
cell_water = g["water"].sum()
frac_ice = cell_ice / cell_n
frac_water = cell_water / cell_n

def pool(truth, level, method, minority="all"):
    clear = jul.m35_lvl >= level
    out = {}
    for cls, mask in (("ice", jul.ice), ("water", jul.water)):
        # eligible cells
        if cls == "ice":
            elig = (frac_ice >= 0.90) & (cell_n >= 5)
        else:
            elig = (frac_water >= 0.90) & (cell_n >= 5)
        elig_cells = frac_ice.index[elig]
        sub = jul[jul.cell.isin(elig_cells)].copy()
        # optional: restrict to class profiles only
        if minority == "classonly":
            sub = sub[sub[cls]]
        cloud = sub[truth].to_numpy()
        cl = clear[sub.index].to_numpy()
        n_clear = int(cl.sum()); n_cloud = int(cloud.sum())
        wrong = int((cloud & cl).sum())
        X = wrong/n_clear if n_clear else np.nan
        out[cls] = dict(X=X, n_clear=n_clear, n_cloud=n_cloud, wrong=wrong,
                        cells=len(elig_cells))
    out["ratio"] = out["ice"]["X"]/out["water"]["X"]
    return out

for method in ("all","classonly"):
    print(f"\n=== cell pooling minority={method} ===")
    r = pool("cal_thick", 2, method)
    print(f" thick/clear_incl  iceX={r['ice']['X']:.4f} (fn={r['ice']['wrong']},nc={r['ice']['n_clear']},cells={r['ice']['cells']})  "
          f"waterX={r['water']['X']:.4f} (fn={r['water']['wrong']},nc={r['water']['n_clear']}) ratio={r['ratio']:.3f}")
    # compare to frozen: ice 0.3991 fn91 nc228 ; water 0.0799 fn43 nc538
    r2 = pool("cal_thick", 3, method)
    print(f" thick/clear_conf  iceX={r2['ice']['X']:.4f} (fn={r2['ice']['wrong']})  waterX={r2['water']['X']:.4f} (fn={r2['water']['wrong']}) ratio={r2['ratio']:.3f}")
    # frozen clear_conf cell: ice 0.3973 fn89 ; water 0.0681 fn? ratio 5.837
    ra = pool("cal_thick", 2, method)  # placeholder

# area pooling: weight by cos(lat_center)
def pool_area(truth, level):
    clear = jul.m35_lvl >= level
    out = {}
    for cls in ("ice","water"):
        if cls == "ice":
            elig = (frac_ice >= 0.90) & (cell_n >= 5)
        else:
            elig = (frac_water >= 0.90) & (cell_n >= 5)
        elig_cells = frac_ice.index[elig]
        # build per-cell aggregates
        rows=[]
        for c in elig_cells:
            sub = jul[jul.cell == c]
            idx = sub.index
            cloud = sub[truth].to_numpy()
            cl = clear[idx].to_numpy()
            w = np.cos(np.deg2rad(sub.clat.iloc[0]))
            rows.append((w*int((cloud&cl).sum()), w*int(cl.sum())))
        num = sum(x[0] for x in rows); den = sum(x[1] for x in rows)
        out[cls] = num/den if den else np.nan
    out["ratio"] = out["ice"]/out["water"]
    return out

print("\n=== area pooling (cos lat weight) ===")
ra = pool_area("cal_thick", 2)
print(f" thick/clear_incl  iceX={ra['ice']:.4f} waterX={ra['water']:.4f} ratio={ra['ratio']:.3f}")
# frozen area: ice 0.3827 water 0.0831 ratio 4.607
