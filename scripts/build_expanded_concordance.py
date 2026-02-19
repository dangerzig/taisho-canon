#!/usr/bin/env python3
"""Build an expanded cross-canon concordance by merging ALL data sources.

Inputs:
  - lancaster_taisho_crossref.json (existing Lancaster data, 790 entries)
  - results/lancaster_full.json (full Lancaster K-number scrape, ~1521 entries)
  - results/84000_tohoku_extract.json (84000 TEI Tohoku extraction)
  - results/tohoku_taisho_crossref.json (acmuller Tohoku→K→Taisho scrape)
  - results/cbeta_jinglu_sanskrit.json (CBETA Jinglu Sanskrit/Pali scrape)
  - results/cbeta_jinglu_tibetan.json (CBETA Jinglu Tibetan catalogue, ~4569 entries)
  - results/rkts_taisho.json (rKTs kernel Taisho cross-refs)
  - results/cross_reference.json (existing concordance, for comparison)

Output:
  - results/cross_reference_expanded.json (new expanded concordance)
  - Prints delta statistics vs. existing concordance
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

# Input files
LANCASTER_PATH = BASE_DIR / "lancaster_taisho_crossref.json"
LANCASTER_FULL_PATH = RESULTS_DIR / "lancaster_full.json"
TOHOKU_84000_PATH = RESULTS_DIR / "84000_tohoku_extract.json"
TOHOKU_ACMULLER_PATH = RESULTS_DIR / "tohoku_taisho_crossref.json"
CBETA_SANSKRIT_PATH = RESULTS_DIR / "cbeta_jinglu_sanskrit.json"
CBETA_TIBETAN_PATH = RESULTS_DIR / "cbeta_jinglu_tibetan.json"
RKTS_PATH = RESULTS_DIR / "rkts_taisho.json"
EXISTING_XREF_PATH = RESULTS_DIR / "cross_reference.json"

# Output
OUTPUT_PATH = RESULTS_DIR / "cross_reference_expanded.json"

# All valid Taisho text IDs from our corpus
CORPUS_IDS_PATH = RESULTS_DIR / "digest_relationships.json"


def load_json(path):
    """Load a JSON file if it exists, else return None."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    print(f"  WARNING: {path} not found, skipping.")
    return None


def normalize_taisho_id(raw_id):
    """Normalize various Taisho ID formats to T##n#### format.

    Handles: T250, T0250, T1, T08n0250, etc.
    Returns the canonical CBETA format like T08n0250.
    """
    # Already in T##n#### format
    m = re.match(r'^T(\d{2})n(\d{4}[A-Za-z]?)$', raw_id)
    if m:
        return raw_id

    # Bare number: T250, T0250, T1
    m = re.match(r'^T(\d+)$', raw_id)
    if m:
        return int(m.group(1))  # Return as int for lookup

    return raw_id


def build_taisho_number_to_id_map(corpus_ids):
    """Build a map from bare Taisho number (e.g. 250) to full ID (e.g. T08n0250).

    This handles the mismatch between Lancaster (bare T250) and CBETA (T08n0250).
    """
    num_to_id = {}
    for text_id in corpus_ids:
        m = re.match(r'^T(\d{2})n(\d{4})', text_id)
        if m:
            num = int(m.group(2))
            # Store first occurrence (some numbers may have vol variants)
            if num not in num_to_id:
                num_to_id[num] = text_id
            # Also store with suffix variants
            num_to_id[text_id] = text_id
    return num_to_id


def get_corpus_ids():
    """Get the set of all text IDs in our corpus from digest results."""
    ids = set()
    data = load_json(CORPUS_IDS_PATH)
    if data:
        for rel in data:
            ids.add(rel["digest_id"])
            ids.add(rel["source_id"])
    # Also add IDs from existing cross-reference
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for section in ["tibetan_parallels", "pali_parallels", "sanskrit_parallels"]:
            if section in xref:
                ids.update(xref[section].keys())
        if "no_parallel_found" in xref:
            ids.update(xref["no_parallel_found"])
    return ids


def merge_sources():
    """Merge all data sources into a unified concordance."""
    # Master lookup: taisho_id -> {tibetan: set(), pali: set(), sanskrit: set(), sources: set()}
    concordance = defaultdict(lambda: {
        "tibetan": set(),
        "pali": set(),
        "sanskrit": set(),
        "nanjio": set(),
        "sources": set(),
    })

    corpus_ids = get_corpus_ids()
    num_to_id = build_taisho_number_to_id_map(corpus_ids)
    print(f"Corpus has {len(corpus_ids)} text IDs, {len(num_to_id)} number→ID mappings")

    def resolve_taisho_id(raw):
        """Resolve a raw Taisho reference to a canonical corpus ID."""
        norm = normalize_taisho_id(raw)
        if isinstance(norm, int):
            return num_to_id.get(norm)
        if norm in corpus_ids:
            return norm
        # Try stripping suffix
        base = re.sub(r'[A-Za-z]+$', '', norm)
        if base in corpus_ids:
            return base
        return norm if re.match(r'^T\d{2}n\d{4}', norm) else None

    # --- Source 1: Existing cross_reference.json ---
    print("\n1. Loading existing cross_reference.json...")
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for text_id, parallels in xref.get("tibetan_parallels", {}).items():
            concordance[text_id]["tibetan"].update(parallels)
            concordance[text_id]["sources"].add("existing")
        for text_id, parallels in xref.get("pali_parallels", {}).items():
            if isinstance(parallels, list):
                concordance[text_id]["pali"].update(parallels)
            concordance[text_id]["sources"].add("existing")
        for text_id, parallels in xref.get("sanskrit_parallels", {}).items():
            if isinstance(parallels, str):
                concordance[text_id]["sanskrit"].add(parallels)
            elif isinstance(parallels, list):
                concordance[text_id]["sanskrit"].update(parallels)
            concordance[text_id]["sources"].add("existing")
        existing_tib = sum(1 for v in concordance.values() if v["tibetan"])
        print(f"  Loaded: {existing_tib} texts with Tibetan parallels")

    # --- Source 2: Lancaster data ---
    print("\n2. Loading Lancaster crossref...")
    lancaster = load_json(LANCASTER_PATH)
    if lancaster:
        added = 0
        for raw_id, data in lancaster.items():
            raw_t = data["taisho"]
            # Handle entries like '974a' - strip letter suffix
            t_num_str = re.sub(r'[a-zA-Z]+$', '', str(raw_t))
            try:
                t_num = int(t_num_str)
            except ValueError:
                continue
            text_id = num_to_id.get(t_num)
            if not text_id:
                continue

            # Tohoku
            for toh in (data.get("tohoku") or []):
                concordance[text_id]["tibetan"].add(f"Toh {toh}")
                added += 1
            # Otani
            for ot in (data.get("otani") or []):
                concordance[text_id]["tibetan"].add(f"Otani {ot}")
            # Sanskrit
            if data.get("sanskrit_title"):
                concordance[text_id]["sanskrit"].add(data["sanskrit_title"])
            # Nanjio
            if data.get("nanjio"):
                concordance[text_id]["nanjio"].add(f"Nj {data['nanjio']}")

            concordance[text_id]["sources"].add("lancaster")
        print(f"  Added {added} Tohoku mappings from Lancaster")

    # --- Source 3: acmuller Tohoku→Taisho scrape ---
    print("\n3. Loading acmuller Tohoku→Taisho scrape...")
    tohoku_data = load_json(TOHOKU_ACMULLER_PATH)
    if tohoku_data:
        new_toh_mappings = 0
        for toh_key, entry in tohoku_data.get("entries", {}).items():
            toh_num = entry["tohoku"]
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                toh_id = f"Toh {toh_num}"
                if toh_id not in concordance[text_id]["tibetan"]:
                    new_toh_mappings += 1
                concordance[text_id]["tibetan"].add(toh_id)
                # Otani
                for ot in entry.get("otani", []):
                    concordance[text_id]["tibetan"].add(ot)
                # Nanjio
                for nj in entry.get("nanjio", []):
                    concordance[text_id]["nanjio"].add(nj)
                # Sanskrit
                if entry.get("sanskrit_title"):
                    concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                concordance[text_id]["sources"].add("acmuller_tohoku")
        print(f"  Added {new_toh_mappings} new Toh mappings from acmuller")

    # --- Source 4: CBETA Jinglu Sanskrit scrape ---
    print("\n4. Loading CBETA Jinglu Sanskrit scrape...")
    cbeta_data = load_json(CBETA_SANSKRIT_PATH)
    if cbeta_data:
        new_from_cbeta = 0
        for entry_id, entry in cbeta_data.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                # Tohoku
                for toh in entry.get("tohoku", []):
                    if toh not in concordance[text_id]["tibetan"]:
                        new_from_cbeta += 1
                    concordance[text_id]["tibetan"].add(toh)
                # Otani
                for ot in entry.get("otani", []):
                    concordance[text_id]["tibetan"].add(ot)
                concordance[text_id]["sources"].add("cbeta_sanskrit")
        print(f"  Added {new_from_cbeta} new Toh mappings from CBETA Sanskrit")

    # --- Source 5: Lancaster FULL K-number scrape ---
    print("\n5. Loading Lancaster full K-number scrape...")
    lancaster_full = load_json(LANCASTER_FULL_PATH)
    if lancaster_full:
        new_from_lanc_full = 0
        for k_key, entry in lancaster_full.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                # Tohoku
                for toh in entry.get("tohoku", []):
                    if toh not in concordance[text_id]["tibetan"]:
                        new_from_lanc_full += 1
                    concordance[text_id]["tibetan"].add(toh)
                # Otani
                for ot in entry.get("otani", []):
                    concordance[text_id]["tibetan"].add(ot)
                # Nanjio
                for nj in entry.get("nanjio", []):
                    concordance[text_id]["nanjio"].add(nj)
                # Sanskrit
                if entry.get("sanskrit_title"):
                    concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                concordance[text_id]["sources"].add("lancaster_full")
        print(f"  Added {new_from_lanc_full} new Toh mappings from Lancaster full")

    # --- Source 6: CBETA Jinglu Tibetan catalogue ---
    print("\n6. Loading CBETA Jinglu Tibetan catalogue...")
    cbeta_tib = load_json(CBETA_TIBETAN_PATH)
    if cbeta_tib:
        new_from_cbeta_tib = 0
        for entry_id, entry in cbeta_tib.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                # Entry number as Tohoku-like reference
                if entry.get("entry_number"):
                    toh_id = f"Toh {entry['entry_number']}"
                    if toh_id not in concordance[text_id]["tibetan"]:
                        new_from_cbeta_tib += 1
                    concordance[text_id]["tibetan"].add(toh_id)
                # Nanjio
                if entry.get("nanjio"):
                    concordance[text_id]["nanjio"].add(entry["nanjio"])
                # Sanskrit
                if entry.get("sanskrit_title"):
                    concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                concordance[text_id]["sources"].add("cbeta_tibetan")
        print(f"  Added {new_from_cbeta_tib} new Toh mappings from CBETA Tibetan")

    # --- Source 7: rKTs kernel Taisho cross-refs ---
    print("\n7. Loading rKTs kernel Taisho cross-refs...")
    rkts_data = load_json(RKTS_PATH)
    if rkts_data:
        new_from_rkts = 0
        for rkts_id, entry in rkts_data.get("entries", {}).items():
            toh_num = entry.get("tohoku")
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                if toh_num:
                    toh_id = f"Toh {toh_num}"
                    if toh_id not in concordance[text_id]["tibetan"]:
                        new_from_rkts += 1
                    concordance[text_id]["tibetan"].add(toh_id)
                # Sanskrit
                if entry.get("sanskrit_title"):
                    concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                concordance[text_id]["sources"].add("rkts")
        print(f"  Added {new_from_rkts} new Toh mappings from rKTs")

    # --- Source 8: 84000 TEI data (Toh titles for enrichment) ---
    print("\n8. Loading 84000 TEI Tohoku extraction...")
    toh_84000 = load_json(TOHOKU_84000_PATH)
    if toh_84000:
        titles_added = 0
        for toh_key, entry in toh_84000.get("entries", {}).items():
            titles = entry.get("titles", {})
            if titles.get("english") or titles.get("sanskrit"):
                # Enrich existing entries that already have this Toh number
                for text_id, data in concordance.items():
                    if toh_key in data["tibetan"]:
                        if titles.get("sanskrit"):
                            data["sanskrit"].add(titles["sanskrit"])
                            titles_added += 1
        print(f"  Enriched {titles_added} entries with 84000 titles")

    return concordance, corpus_ids


def build_output(concordance, corpus_ids):
    """Build the output JSON in the same format as the existing cross_reference.json."""
    tibetan_parallels = {}
    pali_parallels = {}
    sanskrit_parallels = {}
    no_parallel = []

    for text_id in sorted(corpus_ids):
        data = concordance.get(text_id)
        has_any = False

        if data and data["tibetan"]:
            tibetan_parallels[text_id] = sorted(data["tibetan"])
            has_any = True
        if data and data["pali"]:
            pali_parallels[text_id] = sorted(data["pali"])
            has_any = True
        if data and data["sanskrit"]:
            # Keep as string if single, list if multiple
            skt = sorted(data["sanskrit"])
            sanskrit_parallels[text_id] = skt[0] if len(skt) == 1 else skt
            has_any = True

        if not has_any:
            no_parallel.append(text_id)

    # Summary
    total = len(corpus_ids)
    with_tib = len(tibetan_parallels)
    with_pali = len(pali_parallels)
    with_skt = len(sanskrit_parallels)
    with_any = len(corpus_ids) - len(no_parallel)

    summary = {
        "total_texts": total,
        "with_tibetan": with_tib,
        "with_pali": with_pali,
        "with_sanskrit": with_skt,
        "with_any_parallel": with_any,
        "no_parallel": len(no_parallel),
        "pct_tibetan": round(100 * with_tib / total, 1) if total else 0,
        "pct_any": round(100 * with_any / total, 1) if total else 0,
    }

    # Also build provenance tracking
    sources_used = defaultdict(int)
    for data in concordance.values():
        for s in data.get("sources", set()):
            sources_used[s] += 1

    return {
        "summary": summary,
        "sources": dict(sources_used),
        "tibetan_parallels": tibetan_parallels,
        "pali_parallels": pali_parallels,
        "sanskrit_parallels": sanskrit_parallels,
        "no_parallel_found": no_parallel,
    }


def compare_with_existing(output, existing_path):
    """Compare expanded concordance with existing one."""
    existing = load_json(existing_path)
    if not existing:
        return

    old_tib = len(existing.get("tibetan_parallels", {}))
    new_tib = len(output["tibetan_parallels"])
    old_pali = len(existing.get("pali_parallels", {}))
    new_pali = len(output["pali_parallels"])
    old_skt = len(existing.get("sanskrit_parallels", {}))
    new_skt = len(output["sanskrit_parallels"])

    old_any = output["summary"]["total_texts"] - len(existing.get("no_parallel_found", []))
    new_any = output["summary"]["with_any_parallel"]

    print(f"\n{'='*50}")
    print(f"COMPARISON: Existing vs. Expanded Concordance")
    print(f"{'='*50}")
    print(f"{'Category':<25} {'Old':>8} {'New':>8} {'Delta':>8}")
    print(f"{'-'*50}")
    print(f"{'Tibetan parallels':<25} {old_tib:>8} {new_tib:>8} {'+' + str(new_tib - old_tib):>8}")
    print(f"{'Pali parallels':<25} {old_pali:>8} {new_pali:>8} {'+' + str(new_pali - old_pali):>8}")
    print(f"{'Sanskrit parallels':<25} {old_skt:>8} {new_skt:>8} {'+' + str(new_skt - old_skt):>8}")
    print(f"{'Any parallel':<25} {old_any:>8} {new_any:>8} {'+' + str(new_any - old_any):>8}")
    print(f"{'No parallel':<25} {len(existing.get('no_parallel_found', [])):>8} {len(output['no_parallel_found']):>8}")

    # Show new Tibetan entries
    old_tib_set = set(existing.get("tibetan_parallels", {}).keys())
    new_tib_set = set(output["tibetan_parallels"].keys())
    newly_found = new_tib_set - old_tib_set
    if newly_found:
        print(f"\nNewly found Tibetan parallels ({len(newly_found)} texts):")
        for t_id in sorted(newly_found)[:30]:
            print(f"  {t_id}: {output['tibetan_parallels'][t_id]}")
        if len(newly_found) > 30:
            print(f"  ... and {len(newly_found) - 30} more")


def main():
    print("Building expanded cross-canon concordance")
    print("=" * 50)

    concordance, corpus_ids = merge_sources()
    output = build_output(concordance, corpus_ids)

    print(f"\n{'='*50}")
    print(f"EXPANDED CONCORDANCE SUMMARY")
    print(f"{'='*50}")
    for k, v in output["summary"].items():
        print(f"  {k}: {v}")
    print(f"\nSources contributing:")
    for source, count in sorted(output["sources"].items()):
        print(f"  {source}: {count} texts")

    compare_with_existing(output, EXISTING_XREF_PATH)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nExpanded concordance written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
