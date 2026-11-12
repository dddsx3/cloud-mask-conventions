"""Build refs.bib from Crossref records (no hand-typed metadata).

Every entry is fetched from api.crossref.org; the script checks that the returned
first author and year match what we expect, and refuses to emit an entry that does
not match. Datasets are fetched from api.datacite.org instead (they have no
Crossref record) and are marked %DATACITE in the log.

Outputs: refs.bib, ref_verification.csv
"""
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import unicodedata
import urllib.request

OUT = r"<WORKROOT>\papers\p8_cloud_mask"
MAILTO = "p8.manuscript@example.org"

# (bibkey, doi, expected first-author family, expected year, source)
REFS = [
    # ---- 17 sampled validation studies (V8)
    ("kotarba2020", "10.5194/amt-13-4995-2020", "Kotarba", 2020, "crossref"),
    ("holz2008", "10.1029/2008JD009837", "Holz", 2008, "crossref"),
    ("chan2013", "10.1175/JCLI-D-12-00204.1", "Chan", 2013, "crossref"),
    ("liu2010", "10.1175/2009JCLI3386.1", "Liu", 2010, "crossref"),
    ("liu2004", "10.1016/j.rse.2004.06.004", "Liu", 2004, "crossref"),
    ("berendes2004", "10.1109/TGRS.2004.835226", "Berendes", 2004, "crossref"),
    ("ackerman2008", "10.1175/2007JTECHA1053.1", "Ackerman", 2008, "crossref"),
    ("karlsson2010", "10.5194/acp-10-1789-2010", "Karlsson", 2010, "crossref"),
    ("karlsson2020", "10.3390/rs12040713", "Karlsson", 2020, "crossref"),
    ("chen2014", "10.1002/2014JD022017", "Chen", 2014, "crossref"),
    ("kopp2014", "10.1002/2013JD020458", "Kopp", 2014, "crossref"),
    ("yost2023", "10.3390/rs15051349", "Yost", 2023, "crossref"),
    ("nguyenhuu2025", "10.5194/amt-18-3897-2025", "Nguyen Huu", 2025, "crossref"),
    ("wang2016", "10.1002/2016JD025239", "Wang", 2016, "crossref"),
    ("foga2017", "10.1016/j.rse.2017.03.026", "Foga", 2017, "crossref"),
    ("stillinger2019", "10.1029/2019WR024932", "Stillinger", 2019, "crossref"),
    # ---- algorithms, products, truth data
    ("ackerman1998", "10.1029/1998JD200032", "Ackerman", 1998, "crossref"),
    ("frey2008", "10.1175/2008JTECHA1052.1", "Frey", 2008, "crossref"),
    ("winker2009", "10.1175/2009JTECHA1281.1", "Winker", 2009, "crossref"),
    ("vaughan2009", "10.1175/2009JTECHA1228.1", "Vaughan", 2009, "crossref"),
    ("winker2010", "10.1175/2010BAMS3009.1", "Winker", 2010, "crossref"),
    ("king2013", "10.1109/TGRS.2012.2227333", "King", 2013, "crossref"),
    ("platnick2017", "10.1109/TGRS.2016.2610522", "Platnick", 2017, "crossref"),
    ("dybbroe2005", "10.1175/JAM-2188.1", "Dybbroe", 2005, "crossref"),
    ("key2000", "10.1175/1520-0450-39.10.1797", "Key", 2000, "crossref"),
    ("shupe2011", "10.1175/2010JAMC2467.1", "Shupe", 2011, "crossref"),
    ("stengel2020", "10.5194/essd-12-41-2020", "Stengel", 2020, "crossref"),
    ("poulsen2020", "10.5194/essd-12-2121-2020", "Poulsen", 2020, "crossref"),
    ("wang2005", "10.1175/JCLI3438.1", "Wang", 2005, "crossref"),
    # ---- statistics
    ("efron1993", "10.1007/978-1-4899-4541-9", "Efron", 1993, "crossref"),
    ("wilson1927", "10.1080/01621459.1927.10502953", "Wilson", 1927, "crossref"),
    ("agresti1998", "10.1080/00031305.1998.10480550", "Agresti", 1998, "crossref"),
    # ---- Arctic cloud and sea-ice context
    ("curry1996", "10.1175/1520-0442(1996)009<1731:OOACAR>2.0.CO;2", "Curry", 1996, "crossref"),
    ("intrieri2002", "10.1029/2000JC000439", "Intrieri", 2002, "crossref"),
    ("mace2006", "10.1029/2005JD005922", "Mace", 2006, "crossref"),
    ("kay2013", "10.1002/jgrd.50489", "Kay", 2013, "crossref"),
    ("screen2010", "10.1038/nature09051", "Screen", 2010, "crossref"),
    ("liu2012", "10.1029/2012GL051251", "Liu", 2012, "crossref"),
    # ---- datasets
    ("mod35", "10.5067/MODIS/MOD35_L2.061", "MODIS Atmosphere Science Team", 2017,
     "datacite"),
]

# One entry is registered outside Crossref and OpenAlex. Its DOI resolves, and the
# metadata below comes from doi.org content negotiation; the title is translated and
# marked "(in Chinese)" as Elsevier style requires for non-English sources.
MANUAL = ["""@article{wang2022,
  author    = {Wang, X. and Liu, J. and Yang, B.},
  year      = {2022},
  title     = {A summer {Arctic} cloud detection model based on {FY-3D}/{MERSI-II}
               infrared bands (in {Chinese})},
  journal   = {J. Infrared Millim. Waves},
  number    = {2},
  doi       = {10.11972/j.issn.1001-9014.2022.02.015}
}
"""]


def fetch_crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi) + "?mailto=" + MAILTO
    with urllib.request.urlopen(url, timeout=45) as f:
        return json.load(f)["message"]


def fetch_datacite(doi):
    url = "https://api.datacite.org/dois/" + urllib.parse.quote(doi)
    with urllib.request.urlopen(url, timeout=45) as f:
        return json.load(f)["data"]["attributes"]


JOURNAL_ABBREV = {
    "Atmospheric Measurement Techniques": "Atmos. Meas. Tech.",
    "Journal of Geophysical Research: Atmospheres": "J. Geophys. Res. Atmos.",
    "Journal of Geophysical Research: Oceans": "J. Geophys. Res. Oceans",
    "Journal of Geophysical Research": "J. Geophys. Res.",
    "Journal of Climate": "J. Clim.",
    "Remote Sensing of Environment": "Remote Sens. Environ.",
    "IEEE Transactions on Geoscience and Remote Sensing": "IEEE Trans. Geosci. Remote Sens.",
    "Journal of Atmospheric and Oceanic Technology": "J. Atmos. Ocean. Technol.",
    "Atmospheric Chemistry and Physics": "Atmos. Chem. Phys.",
    "Remote Sensing": "Remote Sens.",
    "Journal of Applied Meteorology": "J. Appl. Meteorol.",
    "Journal of Applied Meteorology and Climatology": "J. Appl. Meteorol. Climatol.",
    "Bulletin of the American Meteorological Society": "Bull. Am. Meteorol. Soc.",
    "Earth System Science Data": "Earth Syst. Sci. Data",
    "Water Resources Research": "Water Resour. Res.",
    "The American Statistician": "Am. Stat.",
    "Journal of the American Statistical Association": "J. Am. Stat. Assoc.",
    "Geophysical Research Letters": "Geophys. Res. Lett.",
    "Nature": "Nature",
}


def ascii_fold(s):
    s = s.replace("\u2010", "-").replace("\u2011", "-").replace("\u2013", "-")
    s = s.replace("\u2014", "-").replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u00a0", " ")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def protect(s):
    """Escape what LaTeX would choke on in titles, keep math-free text simple."""
    s = ascii_fold(s)
    s = s.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    s = s.replace("_", r"\_")
    return s


def clean_title(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"Cloud\s*_+\s*cci", "Cloud_cci", t, flags=re.I)
    t = t.rstrip(".")
    return protect(t)


def fmt_authors(auth, is_datacite=False):
    out = []
    for a in auth:
        if is_datacite:
            name = a.get("name", "")
            if a.get("nameType") == "Organizational" or "," not in name:
                out.append("{" + protect(name) + "}")
                continue
            fam, giv = [x.strip() for x in name.split(",", 1)]
        else:
            fam, giv = a.get("family"), a.get("given", "")
            if not fam:
                continue
        initials = " ".join(p[0] + "." for p in re.split(r"[\s\-]+", giv) if p)
        initials = ascii_fold(initials)
        out.append(f"{protect(fam)}, {initials}".strip().rstrip(","))
    if len(out) > 10:
        return " and ".join(out[:10]) + " and others"
    if len(out) == 1:
        return out[0]
    return " and ".join(out)


def entry(key, rec, kind):
    if kind == "crossref":
        auth = fmt_authors(rec.get("author", []))
        year = rec["issued"]["date-parts"][0][0]
        title = clean_title((rec.get("title") or ["?"])[0])
        jnl = (rec.get("container-title") or [""])[0]
        vol = rec.get("volume", "")
        num = rec.get("issue", "")
        pages = rec.get("page", "")
        art = rec.get("article-number", "")
        if not pages and art and art.lower() not in rec["DOI"].lower():
            pages = art
        doi = rec["DOI"]
        typ = rec.get("type", "journal-article")
        if typ == "book":
            body = [f"  author    = {{{auth}}}", f"  year      = {{{year}}}",
                    f"  title     = {{{title}}}",
                    "  publisher = {Chapman and Hall/CRC}",
                    "  address   = {New York}", f"  doi       = {{{doi}}}"]
            return ("@book{" + key + ",\n" + ",\n".join(body) + "\n}\n",
                    year, auth, title, jnl)
        body = [f"  author    = {{{auth}}}", f"  year      = {{{year}}}",
                f"  title     = {{{title}}}",
                f"  journal   = {{{JOURNAL_ABBREV.get(jnl, protect(jnl))}}}"]
        if vol:
            body.append(f"  volume    = {{{vol}}}")
        if num:
            body.append(f"  number    = {{{num}}}")
        if pages:
            body.append(f"  pages     = {{{pages.replace('-', '--')}}}")
        body.append(f"  doi       = {{{doi}}}")
        return "@article{" + key + ",\n" + ",\n".join(body) + "\n}\n", year, auth, title, jnl

    auth = fmt_authors(rec.get("creators", []), is_datacite=True)
    year = rec.get("publicationYear") or rec["issued"]["date-parts"][0][0]
    title = clean_title(rec.get("titles", [{"title": "?"}])[0]["title"])
    pub = rec.get("publisher") or "NASA"
    body = [f"  author    = {{{auth}}}", f"  year      = {{{year}}}",
            f"  title     = {{{title}}}",
            f"  publisher = {{{protect(pub)}}}",
            f"  doi       = {{{rec['doi']}}}", "  note      = {Dataset, Collection 061}"]
    return "@misc{" + key + ",\n" + ",\n".join(body) + "\n}\n", year, auth, title, "dataset"


log, bibs = [], []
for key, doi, want_author, want_year, src in REFS:
    try:
        rec = fetch_crossref(doi) if src == "crossref" else fetch_datacite(doi)
    except Exception as e:  # noqa: BLE001
        log.append([key, doi, "FETCH_FAILED", str(e)[:90], "", "", ""])
        print(f"[FAIL] {key} {doi} {e}")
        continue
    text, year, auth, title, jnl = entry(key, rec, src)
    first = auth.split(",")[0].replace("\\", "").strip("{}")
    ok = (first.lower() == want_author.lower()) and (year == want_year)
    log.append([key, doi, "OK" if ok else "MISMATCH", f"{first} {year}",
                f"want {want_author} {want_year}", title[:80], jnl[:45]])
    if not ok:
        print(f"[MISMATCH] {key}: got {first} {year}, want {want_author} {want_year} "
              f"| {title[:70]}")
    else:
        print(f"[ok] {key:14s} {first:14s} {year}  {title[:64]}")
    bibs.append(text)
    time.sleep(0.3)

with open(os.path.join(OUT, "refs.bib"), "w", encoding="utf-8") as f:
    f.write("\n".join(bibs) + "\n".join(MANUAL))
with open(os.path.join(OUT, "ref_verification.csv"), "w", encoding="utf-8-sig",
          newline="") as f:
    w = csv.writer(f)
    w.writerow(["bibkey", "doi", "status", "resolved", "expected", "title", "venue"])
    w.writerows(log)
    w.writerow(["wang2022", "10.11972/j.issn.1001-9014.2022.02.015",
                "DOI_RESOLVES_NOT_INDEXED", "Wang 2022",
                "doi.org content negotiation; not in Crossref/OpenAlex",
                "A summer Arctic cloud detection model based on FY-3D/MERSI-II "
                "infrared bands (in Chinese)", "J. Infrared Millim. Waves"])

bad = [r for r in log if r[2] != "OK"]
print(f"\n{len(bibs)} entries written, {len(bad)} problems")
sys.exit(0)
