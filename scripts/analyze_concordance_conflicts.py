#!/usr/bin/env python3
"""Analyze concordance source disagreements.

For each Taisho text that has Tohoku mappings from 2+ sources,
check whether the sources agree or disagree on which Tohoku numbers apply.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load expanded concordance for ID resolution
with open(BASE_DIR / "results" / "cross_reference_expanded.json") as f:
    expanded = json.load(f)

all_tids = set(expanded["tibetan_parallels"].keys())


def bare_to_full(num):
    """Map bare taisho number to T##n#### format."""
    for tid in all_tids:
        m = re.match(r"T(\d{2})n(\d{4})", tid)
        if m and int(m.group(2)) == num:
            return tid
    return None


def resolve_tid(raw):
    """Resolve a raw Taisho reference to canonical ID."""
    if raw in all_tids:
        return raw
    # Strip T prefix and try as number
    m = re.match(r"^T?(\d+)$", str(raw))
    if m:
        return bare_to_full(int(m.group(1)))
    # Try stripping suffix
    base = re.sub(r"[A-Za-z]+$", "", raw)
    if base in all_tids:
        return base
    return None


# Load each source and build tid -> set(Toh) mappings
source_maps = {}

# Lancaster original
with open(BASE_DIR / "lancaster_taisho_crossref.json") as f:
    lanc = json.load(f)
lanc_map = {}
for raw_id, data in lanc.items():
    t_str = re.sub(r"[a-zA-Z]+$", "", str(data.get("taisho", "")))
    try:
        t_num = int(t_str)
    except ValueError:
        continue
    tid = bare_to_full(t_num)
    if tid:
        tohs = {f"Toh {t}" for t in (data.get("tohoku") or [])}
        if tohs:
            lanc_map[tid] = tohs
source_maps["lancaster"] = lanc_map

# Lancaster full
with open(BASE_DIR / "results" / "lancaster_full.json") as f:
    lanc_full = json.load(f)
lf_map = {}
for k_key, entry in (lanc_full.get("entries") or {}).items():
    for t_raw in entry.get("taisho", []):
        tid = resolve_tid(t_raw)
        if not tid:
            continue
        tohs = set()
        for toh in entry.get("tohoku", []):
            # Lancaster full already has "Toh N" format strings
            if isinstance(toh, str) and toh.startswith("Toh"):
                tohs.add(toh)
            else:
                tohs.add(f"Toh {toh}")
        if tohs:
            lf_map.setdefault(tid, set()).update(tohs)
source_maps["lancaster_full"] = lf_map

# CBETA Tibetan
with open(BASE_DIR / "results" / "cbeta_jinglu_tibetan.json") as f:
    cbeta_tib = json.load(f)
ct_map = {}
for entry_id, entry in (cbeta_tib.get("entries") or {}).items():
    for t_raw in entry.get("taisho", []):
        tid = resolve_tid(t_raw)
        if not tid:
            continue
        if entry.get("entry_number"):
            ct_map.setdefault(tid, set()).add(f"Toh {entry['entry_number']}")
source_maps["cbeta_tibetan"] = ct_map

# CBETA Sanskrit
with open(BASE_DIR / "results" / "cbeta_jinglu_sanskrit.json") as f:
    cbeta_skt = json.load(f)
cs_map = {}
for entry_id, entry in (cbeta_skt.get("entries") or {}).items():
    for t_raw in entry.get("taisho", []):
        tid = resolve_tid(t_raw)
        if not tid:
            continue
        tohs = set()
        for toh in entry.get("tohoku", []):
            if isinstance(toh, str) and toh.startswith("Toh"):
                tohs.add(toh)
            else:
                tohs.add(f"Toh {toh}")
        if tohs:
            cs_map.setdefault(tid, set()).update(tohs)
source_maps["cbeta_sanskrit"] = cs_map

# acmuller Tohoku
with open(BASE_DIR / "results" / "tohoku_taisho_crossref.json") as f:
    acmuller = json.load(f)
am_map = {}
for toh_key, entry in (acmuller.get("entries") or {}).items():
    toh_num = entry.get("tohoku")
    for t_raw in entry.get("taisho", []):
        tid = resolve_tid(t_raw)
        if not tid:
            continue
        if toh_num:
            am_map.setdefault(tid, set()).add(f"Toh {toh_num}")
source_maps["acmuller"] = am_map

# rKTs
with open(BASE_DIR / "results" / "rkts_taisho.json") as f:
    rkts = json.load(f)
rk_map = {}
for rkts_id, entry in (rkts.get("entries") or {}).items():
    toh_num = entry.get("tohoku")
    for t_raw in entry.get("taisho", []):
        tid = resolve_tid(t_raw)
        if not tid:
            continue
        if toh_num:
            rk_map.setdefault(tid, set()).add(f"Toh {toh_num}")
source_maps["rkts"] = rk_map

# Analyze
print("=" * 70)
print("CONCORDANCE SOURCE AGREEMENT ANALYSIS")
print("=" * 70)

# For each tid, collect which sources have Toh data
all_covered_tids = set()
for m in source_maps.values():
    all_covered_tids.update(m.keys())

multi_source = {}  # tid -> {source: set(Toh)}
for tid in sorted(all_covered_tids):
    per_source = {}
    for src_name, src_map in source_maps.items():
        if tid in src_map:
            per_source[src_name] = src_map[tid]
    if len(per_source) >= 2:
        multi_source[tid] = per_source

print(f"\nTexts with Toh data from any source: {len(all_covered_tids)}")
print(f"Texts with Toh data from 2+ sources: {len(multi_source)}")

# Categorize
full_agree = []
partial_overlap = []
true_conflict = []

for tid, per_source in multi_source.items():
    all_tohs = list(per_source.values())
    union = set().union(*all_tohs)
    intersection = set.intersection(*all_tohs)

    if union == intersection:
        full_agree.append(tid)
    elif intersection:
        partial_overlap.append((tid, per_source, union, intersection))
    else:
        true_conflict.append((tid, per_source, union))

print(f"\nFull agreement (all sources same Toh set): {len(full_agree)}")
print(f"Partial overlap (some Tohs shared, some unique): {len(partial_overlap)}")
print(f"No overlap (sources give completely different Tohs): {len(true_conflict)}")

# TRUE CONFLICTS
print(f"\n{'=' * 70}")
print(f"TRUE CONFLICTS: Sources give completely different Tohoku numbers")
print(f"{'=' * 70}")
for tid, per_source, union in true_conflict:
    print(f"\n  {tid}:")
    for src, tohs in sorted(per_source.items()):
        print(f"    {src:20s}: {sorted(tohs)}")

# PARTIAL OVERLAPS - most interesting ones
print(f"\n{'=' * 70}")
print(f"PARTIAL OVERLAPS: Sources share some Tohs but not all (top 25)")
print(f"{'=' * 70}")
partial_sorted = sorted(
    partial_overlap,
    key=lambda x: len(x[2]) - len(x[3]),
    reverse=True,
)
for tid, per_source, union, intersection in partial_sorted[:25]:
    extras = sorted(union - intersection)
    print(f"\n  {tid}: shared={sorted(intersection)}, extras={extras}")
    for src, tohs in sorted(per_source.items()):
        print(f"    {src:20s}: {sorted(tohs)}")

# Summary stats
print(f"\n{'=' * 70}")
print(f"SUMMARY")
print(f"{'=' * 70}")
print(f"Total texts with Toh data from 2+ sources: {len(multi_source)}")
print(f"  Full agreement:    {len(full_agree):4d} ({100*len(full_agree)/len(multi_source):.1f}%)")
print(f"  Partial overlap:   {len(partial_overlap):4d} ({100*len(partial_overlap)/len(multi_source):.1f}%)")
print(f"  True conflict:     {len(true_conflict):4d} ({100*len(true_conflict)/len(multi_source):.1f}%)")
