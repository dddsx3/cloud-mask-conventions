"""Crossref discovery: for each bibliographic query print the top candidates.

Purpose: choose real DOIs by hand instead of guessing them, so that every entry in
refs.bib is backed by a Crossref record.
"""
import json
import sys
import urllib.parse
import urllib.request

MAILTO = "p8.manuscript@example.org"
QUERIES = [
    ("ackerman1998", "Discriminating clear sky from clouds with MODIS Ackerman Strabala 1998"),
    ("frey2008", "Cloud detection with MODIS Part I improvements in the MODIS cloud mask for collection 5"),
    ("winker2010", "The CALIPSO mission a global 3D view of aerosols and clouds"),
    ("vaughan2009", "Fully automated detection of cloud and aerosol layers in the CALIPSO lidar measurements"),
    ("winker2009", "Overview of the CALIPSO mission and CALIOP data processing algorithms"),
    ("efron1993", "An introduction to the bootstrap Efron Tibshirani"),
    ("wilson1927", "Probable inference the law of succession and statistical inference Wilson"),
    ("agresti1998", "Approximate is better than exact for interval estimation of binomial proportions"),
    ("intrieri2002", "Annual cycle of Arctic surface cloud forcing at SHEBA"),
    ("kay2013", "Observational constraints on Arctic Ocean clouds and radiative fluxes during the early 21st century"),
    ("shupe2011", "Clouds at Arctic atmospheric observatories a decade of ground-based remote sensing"),
    ("zygmuntowska2012", "Arctic clouds and surface energy fluxes in the Community Earth System Model"),
    ("marchant2020", "MODIS Collection 6.1 cloud mask global validation"),
    ("king2013", "Spatial and temporal distribution of clouds observed by MODIS onboard Terra and Aqua"),
    ("platnick2017", "The MODIS cloud optical and microphysical products a dataset for remote sensing of cloud properties"),
    ("dybbroe2005", "NWCSAF AVHRR cloud detection and analysis using dynamic thresholds and radiative transfer modeling"),
    ("heidinger2013", "The PATHFINDER atmosphere extended AVHRR products"),
    ("key2000", "Cloud particle phase determination with the AVHRR"),
    ("mace2005", "Cloud radiative forcing at the Atmospheric Radiation Measurement Program Climate Research Facility"),
    ("stramler2011", "The atmospheric energy budget and surface energy budget of the Arctic"),
    ("schweiger2008", "Validation of Arctic sea ice concentration retrievals from AMSR-E"),
]

for key, q in QUERIES:
    url = ("https://api.crossref.org/works?rows=3&select=DOI,title,author,issued,"
           "container-title,volume,page,type&mailto=" + MAILTO +
           "&query.bibliographic=" + urllib.parse.quote(q))
    try:
        with urllib.request.urlopen(url, timeout=45) as f:
            items = json.load(f)["message"]["items"]
    except Exception as e:  # noqa: BLE001
        print(f"[{key}] FAILED {e}")
        continue
    print(f"\n[{key}] query={q}")
    for it in items:
        au = it.get("author", [{}])
        first = au[0].get("family", "?") if au else "?"
        yr = it.get("issued", {}).get("date-parts", [[None]])[0][0]
        ttl = (it.get("title") or ["?"])[0]
        jnl = (it.get("container-title") or [""])[0]
        print(f"   {it['DOI']}  {first} {yr}  {ttl[:88]}  | {jnl[:40]} "
              f"| v{it.get('volume','')} p{it.get('page','')} | {it.get('type')}")
    sys.stdout.flush()
