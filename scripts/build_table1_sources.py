#!/usr/bin/env python3
"""Regenerate Table 1 ("Data Sources") of the RET concordance paper from the
released data, so every cell is reproducible.

Two kinds of column:

  * "Raw Entries"  -- the size of each source as ingested, counted from that
    source's own file. The natural unit differs by source (catalogue entries,
    alignment links, or distinct Taisho texts), so the definition used is
    stated per source below.

  * "Taisho Texts" / "Toh Numbers" -- the *verified contribution* of each
    source to the merged concordance, read from `link_provenance` in
    results/cross_reference_verified.json (the authoritative per-link source
    attribution in the released data). This is what a reader reproduces from
    the release. SuttaCentral contributes Pali parallels (no Toh), counted
    from `pali_parallels`; the 84000 title set is title-enrichment only and
    contributes no Taisho-to-Toh links.

Run from the repo root:  python3 scripts/build_table1_sources.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(*parts):
    return json.load(open(os.path.join(ROOT, *parts), encoding="utf-8"))


def tohnum(x):
    m = re.search(r"\d+", str(x))
    return m.group(0) if m else None


# ---- corpus (the 2,455 selected Taisho texts) ----
cv = load("results", "cross_reference_verified.json")
corpus = (set(cv["tibetan_parallels"]) | set(cv["pali_parallels"])
          | set(cv["sanskrit_parallels"]) | set(cv["no_parallel_found"]))
assert len(corpus) == 2455, len(corpus)

# ---- verified per-source contribution, from link_provenance ----
# Collapse the two Lancaster scrape files into one source; the Lancaster family
# members (Muller, CBETA Skt) stay distinct here (the family caveat is made in
# the Source Reliability section, not here).
SRC = {
    "lancaster": "Lancaster", "lancaster_full": "Lancaster",
    "cbeta_tibetan": "CBETA Jinglu Tibetan", "cbeta_crossref": "CBETA Jinglu Tibetan",
    "cbeta_sanskrit": "CBETA Jinglu Sanskrit",
    "acmuller_tohoku": "Muller Tohoku index",
    "rkts_concordance": "rKTs", "rkts": "rKTs",
    "84000_tei_refs": "84000 TEI cross-refs",
}
SCHOLARLY = {"li2021", "silk2019", "conze1978", "frauwallner1956",
             "nattier1992", "shimoda1997"}
IGNORE = {"existing", "standard_parallels:error"}

tai, toh = {}, {}
for tid, refs in cv["link_provenance"].items():
    for ref, prov in refs.items():
        if not str(ref).startswith("Toh") or str(ref) == "Toh 0":
            continue
        for p in prov:
            s = p["source"]
            name = SRC.get(s) or ("Scholarly citations" if s in SCHOLARLY else None)
            if not name:
                continue
            tai.setdefault(name, set()).add(tid)
            toh.setdefault(name, set()).add(ref)

# ---- raw-entry counts, from each source file ----
raw = {}
raw["Lancaster"] = load("results", "lancaster_full.json")["summary"]["unique_taisho"]
raw["CBETA Jinglu Tibetan"] = len(load("results", "cbeta_jinglu_tibetan.json")["entries"])
raw["CBETA Jinglu Sanskrit"] = len(load("results", "cbeta_jinglu_sanskrit.json")["entries"])
raw["Muller Tohoku index"] = len(load("results", "tohoku_taisho_crossref.json")["entries"])
raw["SuttaCentral"] = load("results", "sc_pali_parallels.json")["total_links"]
raw["rKTs"] = len(load("results", "rkts_taisho.json")["entries"])
raw["84000 TEI titles"] = load("results", "84000_tohoku_extract.json")["summary"]["total_toh"]
_xr = load("results", "84000_taisho_refs.json")
raw["84000 TEI cross-refs"] = sum(len(e.get("taisho_nums", [])) for e in _xr["entries"].values())

# SuttaCentral contributes Pali parallels (Taisho count), no Toh
tai["SuttaCentral"] = set(cv["pali_parallels"])

# scholarly raw entries = rows in the paper's Appendix table (hand-curated)
SCHOLARLY_RAW = 40  # Appendix: Scholarly Parallel Identifications

ORDER = ["Lancaster", "CBETA Jinglu Tibetan", "CBETA Jinglu Sanskrit",
         "Muller Tohoku index", "SuttaCentral", "rKTs",
         "84000 TEI titles", "84000 TEI cross-refs", "Scholarly citations"]
# paper's current Table 1 values: (raw, taisho, toh)  (None = "---"/enrichment)
PAPER = {
    "Lancaster": (1478, 592, 512),
    "CBETA Jinglu Tibetan": (4569, 637, 564),
    "CBETA Jinglu Sanskrit": (704, 517, 448),
    "Muller Tohoku index": (382, 559, 359),
    "SuttaCentral": (4616, 171, None),
    "rKTs": (26, 20, 23),
    "84000 TEI titles": (1108, None, None),
    "84000 TEI cross-refs": (457, 350, 193),
    "Scholarly citations": (40, 29, 29),
}

raw["Scholarly citations"] = SCHOLARLY_RAW
raw["84000 TEI titles"] = raw.get("84000 TEI titles")

print(f"{'Source':26} {'Raw':>12} {'Taisho':>14} {'Toh':>12}")
print(f"{'':26} {'(mine/paper)':>12} {'(mine/paper)':>14} {'(mine/paper)':>12}")
print("-" * 70)
tot_tai, tot_toh = set(), set()
for name in ORDER:
    r = raw.get(name)
    t = len(tai.get(name, set())) if (name != "84000 TEI titles") else None
    h = len(toh.get(name, set())) if name not in ("SuttaCentral", "84000 TEI titles") else None
    pr, pt, ph = PAPER[name]
    def cmp(mine, paper):
        if mine is None:
            return "   ---"
        flag = "" if mine == paper else "  <-DIFF"
        return f"{mine}/{paper}{flag}"
    print(f"{name:26} {cmp(r,pr):>12} {cmp(t,pt):>14} {cmp(h,ph):>12}")
    if name not in ("84000 TEI titles",):
        tot_tai |= tai.get(name, set())
    tot_toh |= toh.get(name, set())

# merged subtotal = union over Toh-contributing sources + Pali (SuttaCentral)
merged_tai = set()
for name in ORDER:
    merged_tai |= tai.get(name, set())
print("-" * 70)
print(f"Merged subtotal: Taisho {len(merged_tai)} (paper 878), Toh {len(tot_toh)} (paper 605)")
