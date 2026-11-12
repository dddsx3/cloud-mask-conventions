"""Understand frozen cell (255-as-ice) and area pooling variants."""
import numpy as np
import pandas as pd

CSV = "supp/S1_matchups.csv"
d = pd.read_csv(CSV)
d["month"] = pd.to_datetime(d["time"]).dt.month
q = d[(d.dt_sec.abs() <= 1200) & (d.dcell_km <= 20)].copy()
jul = q[q.month == 7].reset_index(drop=True)

jul["clat"] = (np.floor(jul.lat / 0.5) * 0.5 + 0.25)
jul["clon"] = (np.floor(jul.lon / 0.5) * 0.5 + 0.25)
jul["cell"] = jul.clat.astype(str) + "," + jul.clon.astype(str)

# two ice definitions
jul["ice_excl"] = (jul.si >= 50) & (jul.si != 255)   # paper/documented
jul["ice_incl"] = (jul.si >= 50) | (jul.si == 255)   # frozen cell bug
jul["water"] = jul.si == 0

g = jul.groupby("cell")
cell_n = g.size()
def frac(col): return g[col].sum()/cell_n

def cell_counts(ice_col, truth, level):
    clear = jul.m35_lvl >= level
    fr = frac(ice_col)
    fw = frac("water")
    elig = ((fr>=0.90)|(fw>=0.90)) & (cell_n>=5)
    # ice cells vs water cells both need assignment; a cell is ice if fr>=.9, water if fw>=.9
    ice_cells = frac(ice_col).index[(frac(ice_col)>=0.90)&(cell_n>=5)]
    water_cells = frac("water").index[(frac("water")>=0.90)&(cell_n>=5)]
    res={}
    for cls, cells, col in (("ice",ice_cells,ice_col),("water",water_cells,"water")):
        sub = jul[jul.cell.isin(cells)]
        cloud = sub[truth].to_numpy(); cl = clear[sub.index].to_numpy()
        nc=int(cl.sum()); wr=int((cloud&cl).sum())
        res[cls]=(wr/nc if nc else np.nan, wr, nc, len(cells))
    return res

print("FROZEN says: cell thick/incl ice 0.3991 fn91 nc228 ; water 0.0799 fn43 nc538 ; area ice 0.3827 water 0.0831")
for ic,label in (("ice_excl","exclude255"),("ice_incl","include255")):
    c = cell_counts(ic,"cal_thick",2)
    print(f" CELL {label}: ice X={c['ice'][0]:.4f} fn={c['ice'][1]} nc={c['ice'][2]} cells={c['ice'][3]} | water X={c['water'][0]:.4f} fn={c['water'][1]} nc={c['water'][2]}")

# area variants for ice (truth thick, level2)
clear = jul.m35_lvl >= 2
def area_variant(method, ice_col):
    fr=frac(ice_col); fw=frac("water")
    ice_cells=frac(ice_col).index[(frac(ice_col)>=0.90)&(cell_n>=5)]
    water_cells=frac("water").index[(frac("water")>=0.90)&(cell_n>=5)]
    if method=="cos_count":
        num=den=0
        for c in ice_cells:
            sub=jul[jul.cell==c]; idx=sub.index
            w=np.cos(np.deg2rad(sub.clat.iloc[0]))
            cloud=sub["cal_thick"].to_numpy(); cl=clear[idx].to_numpy()
            num+=w*int((cloud&cl).sum()); den+=w*int(cl.sum())
        return num/den if den else np.nan
    if method=="cos_percellratio":
        vals=[]; ws=[]
        for c in ice_cells:
            sub=jul[jul.cell==c]; idx=sub.index
            cloud=sub["cal_thick"].to_numpy(); cl=clear[idx].to_numpy()
            nc=int(cl.sum()); wr=int((cloud&cl).sum())
            if nc:
                vals.append(wr/nc); ws.append(np.cos(np.deg2rad(sub.clat.iloc[0])))
        return np.average(vals,weights=ws)
    if method=="profile_cos":
        sub=jul[jul[ice_col]]
        w=np.cos(np.deg2rad(sub.lat))
        cloud=sub["cal_thick"].to_numpy(); cl=clear[sub.index].to_numpy()
        return (w*(cloud&cl)).sum()/(w*cl).sum()
    if method=="profile_cos_clatcell":
        # weight by cos(lat of profile) but only profiles in ice-assigned cells
        sub=jul[jul.cell.isin(ice_cells)]
        w=np.cos(np.deg2rad(sub.lat))
        cloud=sub["cal_thick"].to_numpy(); cl=clear[sub.index].to_numpy()
        return (w*(cloud&cl)).sum()/(w*cl).sum()

for ic,label in (("ice_excl","exclude255"),("ice_incl","include255")):
    print(f" AREA {label}:")
    for m in ("cos_count","cos_percellratio","profile_cos","profile_cos_clatcell"):
        print(f"    {m}: {area_variant(m,ic):.4f}")
