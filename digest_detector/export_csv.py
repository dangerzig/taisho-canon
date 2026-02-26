"""Export the cross-reference concordance as a flat CSV file.

Reads results/cross_reference_expanded.json and reconstructs per-mapping
provenance from the original source files. Outputs one row per
Taisho-Tohoku pair to results/cross_reference.csv.

Usage:
    python3 -m digest_detector.export_csv
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

# Input: expanded concordance
EXPANDED_PATH = RESULTS_DIR / "cross_reference_expanded.json"

# Source files for provenance reconstruction
LANCASTER_PATH = BASE_DIR / "lancaster_taisho_crossref.json"
LANCASTER_FULL_PATH = RESULTS_DIR / "lancaster_full.json"
ACMULLER_PATH = RESULTS_DIR / "tohoku_taisho_crossref.json"
CBETA_SANSKRIT_PATH = RESULTS_DIR / "cbeta_jinglu_sanskrit.json"
CBETA_TIBETAN_PATH = RESULTS_DIR / "cbeta_jinglu_tibetan.json"
RKTS_PATH = RESULTS_DIR / "rkts_taisho.json"
EXISTING_XREF_PATH = RESULTS_DIR / "cross_reference.json"

# Output
OUTPUT_PATH = RESULTS_DIR / "cross_reference.csv"


def load_json(path):
    """Load a JSON file if it exists."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def build_number_to_id(concordance_keys):
    """Build a map from bare Taisho number to canonical ID (e.g., 251 -> T08n0251)."""
    num_to_id = {}
    for text_id in concordance_keys:
        m = re.match(r'^T(\d{2})n(\d{4})', text_id)
        if m:
            num = int(m.group(2))
            if num not in num_to_id:
                num_to_id[num] = text_id
    return num_to_id


def resolve_taisho(raw, num_to_id, valid_ids):
    """Resolve a raw Taisho reference (e.g. 'T251', 'T08n0251') to a canonical ID."""
    # Already canonical
    if raw in valid_ids:
        return raw
    # Bare number format: T250, T0250
    m = re.match(r'^T(\d+)$', raw)
    if m:
        return num_to_id.get(int(m.group(1)))
    # Try as-is with suffix stripping
    base = re.sub(r'[A-Za-z]+$', '', raw)
    if base in valid_ids:
        return base
    return None


def build_provenance(expanded):
    """Reconstruct per-mapping provenance: (taisho_id, toh_number) -> set of sources.

    Scans all original source files to determine which sources assert each
    specific Taisho-to-Tohoku mapping.
    """
    # Collect all taisho IDs that have tibetan parallels
    all_ids = set()
    for section in ("tibetan_parallels", "pali_parallels", "sanskrit_parallels"):
        all_ids.update(expanded.get(section, {}).keys())
    all_ids.update(expanded.get("no_parallel_found", []))

    num_to_id = build_number_to_id(all_ids)

    # provenance[(taisho_id, "Toh NNN")] = set of source names
    provenance = defaultdict(set)

    # --- Source: existing cross_reference.json ---
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for text_id, parallels in xref.get("tibetan_parallels", {}).items():
            for p in parallels:
                if p.startswith("Toh "):
                    provenance[(text_id, p)].add("existing")

    # --- Source: Lancaster (original) ---
    lancaster = load_json(LANCASTER_PATH)
    if lancaster:
        for _k, entry in lancaster.items():
            t_num_str = re.sub(r'[a-zA-Z]+$', '', str(entry.get("taisho", "")))
            try:
                t_num = int(t_num_str)
            except ValueError:
                continue
            text_id = num_to_id.get(t_num)
            if not text_id:
                continue
            for toh in entry.get("tohoku") or []:
                provenance[(text_id, f"Toh {toh}")].add("lancaster")

    # --- Source: Lancaster full ---
    lancaster_full = load_json(LANCASTER_FULL_PATH)
    if lancaster_full:
        for _k, entry in lancaster_full.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                for toh in entry.get("tohoku", []):
                    # Lancaster full tohoku may be "Toh NNN" or bare number
                    toh_str = toh if toh.startswith("Toh ") else f"Toh {toh}"
                    provenance[(text_id, toh_str)].add("lancaster_full")

    # --- Source: acmuller Tohoku ---
    acmuller = load_json(ACMULLER_PATH)
    if acmuller:
        for _k, entry in acmuller.get("entries", {}).items():
            toh_num = entry.get("tohoku")
            if toh_num is None:
                continue
            toh_str = f"Toh {toh_num}"
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                provenance[(text_id, toh_str)].add("acmuller")

    # --- Source: CBETA Sanskrit ---
    cbeta_skt = load_json(CBETA_SANSKRIT_PATH)
    if cbeta_skt:
        for _k, entry in cbeta_skt.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                for toh in entry.get("tohoku", []):
                    toh_str = toh if toh.startswith("Toh ") else f"Toh {toh}"
                    provenance[(text_id, toh_str)].add("cbeta_sanskrit")

    # --- Source: CBETA Tibetan ---
    cbeta_tib = load_json(CBETA_TIBETAN_PATH)
    if cbeta_tib:
        for _k, entry in cbeta_tib.get("entries", {}).items():
            entry_num = entry.get("entry_number")
            if entry_num is None:
                continue
            toh_str = f"Toh {entry_num}"
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                provenance[(text_id, toh_str)].add("cbeta_tibetan")

    # --- Source: rKTs ---
    rkts = load_json(RKTS_PATH)
    if rkts:
        for _k, entry in rkts.get("entries", {}).items():
            toh_num = entry.get("tohoku")
            if toh_num is None:
                continue
            toh_str = f"Toh {toh_num}"
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                provenance[(text_id, toh_str)].add("rkts")

    return provenance


def gather_titles_and_nanjio(expanded):
    """Gather Chinese, Sanskrit, Tibetan titles and Nanjio numbers from source files.

    Returns:
        titles: dict[taisho_id] -> {chinese_title, sanskrit_title, tibetan_title}
        nanjio: dict[taisho_id] -> set of Nanjio numbers
        otani_map: dict[taisho_id] -> set of Otani numbers
    """
    all_ids = set()
    for section in ("tibetan_parallels", "pali_parallels", "sanskrit_parallels"):
        all_ids.update(expanded.get(section, {}).keys())
    all_ids.update(expanded.get("no_parallel_found", []))

    num_to_id = build_number_to_id(all_ids)

    titles = defaultdict(lambda: {
        "chinese_title": "",
        "sanskrit_title": "",
        "tibetan_title": "",
    })
    nanjio = defaultdict(set)
    otani_map = defaultdict(set)

    # Lancaster (original) - has Chinese, Sanskrit, Tibetan titles and Nanjio
    lancaster = load_json(LANCASTER_PATH)
    if lancaster:
        for _k, entry in lancaster.items():
            t_num_str = re.sub(r'[a-zA-Z]+$', '', str(entry.get("taisho", "")))
            try:
                t_num = int(t_num_str)
            except ValueError:
                continue
            text_id = num_to_id.get(t_num)
            if not text_id:
                continue
            if entry.get("chinese_title"):
                titles[text_id]["chinese_title"] = entry["chinese_title"]
            if entry.get("sanskrit_title"):
                titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]
            if entry.get("tibetan_title"):
                titles[text_id]["tibetan_title"] = entry["tibetan_title"]
            if entry.get("nanjio"):
                nanjio[text_id].add(f"Nj {entry['nanjio']}")
            for ot in entry.get("otani") or []:
                otani_map[text_id].add(f"Otani {ot}")

    # Lancaster full - additional titles and Nanjio
    lancaster_full = load_json(LANCASTER_FULL_PATH)
    if lancaster_full:
        for _k, entry in lancaster_full.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                if entry.get("chinese_title") and not titles[text_id]["chinese_title"]:
                    titles[text_id]["chinese_title"] = entry["chinese_title"]
                if entry.get("sanskrit_title") and not titles[text_id]["sanskrit_title"]:
                    titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]
                if entry.get("tibetan_title") and not titles[text_id]["tibetan_title"]:
                    titles[text_id]["tibetan_title"] = entry["tibetan_title"]
                for nj in entry.get("nanjio", []):
                    nanjio[text_id].add(nj)
                for ot in entry.get("otani", []):
                    otani_map[text_id].add(ot)

    # acmuller - Nanjio, Otani
    acmuller = load_json(ACMULLER_PATH)
    if acmuller:
        for _k, entry in acmuller.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                for nj in entry.get("nanjio", []):
                    nanjio[text_id].add(nj)
                for ot in entry.get("otani", []):
                    otani_map[text_id].add(ot)

    # CBETA Tibetan - has Chinese, Tibetan, Sanskrit titles and Nanjio
    cbeta_tib = load_json(CBETA_TIBETAN_PATH)
    if cbeta_tib:
        for _k, entry in cbeta_tib.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                if entry.get("chinese_title") and not titles[text_id]["chinese_title"]:
                    titles[text_id]["chinese_title"] = entry["chinese_title"]
                if entry.get("sanskrit_title") and not titles[text_id]["sanskrit_title"]:
                    titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]
                if entry.get("tibetan_title") and not titles[text_id]["tibetan_title"]:
                    titles[text_id]["tibetan_title"] = entry["tibetan_title"]
                if entry.get("nanjio"):
                    nanjio[text_id].add(entry["nanjio"])

    # rKTs - Sanskrit titles
    rkts = load_json(RKTS_PATH)
    if rkts:
        for _k, entry in rkts.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                if entry.get("sanskrit_title") and not titles[text_id]["sanskrit_title"]:
                    titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]

    return titles, nanjio, otani_map


def export_csv():
    """Export the concordance as a flat CSV with one row per Taisho-Tohoku pair."""
    expanded = load_json(EXPANDED_PATH)
    if not expanded:
        print(f"ERROR: {EXPANDED_PATH} not found.")
        return

    print("Reconstructing per-mapping provenance from source files...")
    provenance = build_provenance(expanded)

    print("Gathering titles and auxiliary data from source files...")
    titles, nanjio_map, otani_map = gather_titles_and_nanjio(expanded)

    # Build rows: one per (taisho_id, tohoku) pair
    rows = []
    taisho_ids_with_rows = set()
    tibetan = expanded.get("tibetan_parallels", {})

    for taisho_id in sorted(tibetan.keys()):
        parallels = tibetan[taisho_id]

        # Separate Toh and Otani entries
        toh_entries = [p for p in parallels if p.startswith("Toh ")]
        otani_entries = [p for p in parallels if p.startswith("Otani ")]
        other_entries = [
            p for p in parallels
            if not p.startswith("Toh ") and not p.startswith("Otani ")
        ]

        # Merge Otani from source files with those in the expanded JSON
        all_otani = set(otani_entries)
        if taisho_id in otani_map:
            all_otani.update(otani_map[taisho_id])
        otani_str = "; ".join(sorted(all_otani))

        # Nanjio
        nj = nanjio_map.get(taisho_id, set())
        nanjio_str = "; ".join(sorted(nj))

        # Titles
        t = titles.get(taisho_id, {})
        sanskrit_title = t.get("sanskrit_title", "")
        chinese_title = t.get("chinese_title", "")
        tibetan_title = t.get("tibetan_title", "")

        # Pali parallels for this text
        pali = expanded.get("pali_parallels", {}).get(taisho_id, [])
        pali_str = "; ".join(sorted(pali)) if isinstance(pali, list) else str(pali)

        if not toh_entries:
            # Text has Otani or other Tibetan refs but no Tohoku numbers.
            # Include one row with empty tohoku.
            sources = provenance.get((taisho_id, ""), set())
            rows.append({
                "taisho_id": taisho_id,
                "tohoku": "",
                "otani": otani_str,
                "nanjio": nanjio_str,
                "sanskrit_title": sanskrit_title,
                "chinese_title": chinese_title,
                "tibetan_title": tibetan_title,
                "pali_parallel": pali_str,
                "sources": "",
                "source_count": 0,
            })
            taisho_ids_with_rows.add(taisho_id)
        else:
            for toh in sorted(toh_entries):
                sources = provenance.get((taisho_id, toh), set())
                sources_str = "; ".join(sorted(sources))
                rows.append({
                    "taisho_id": taisho_id,
                    "tohoku": toh,
                    "otani": otani_str,
                    "nanjio": nanjio_str,
                    "sanskrit_title": sanskrit_title,
                    "chinese_title": chinese_title,
                    "tibetan_title": tibetan_title,
                    "pali_parallel": pali_str,
                    "sources": sources_str,
                    "source_count": len(sources),
                })
                taisho_ids_with_rows.add(taisho_id)

    # Also include texts that have only Pali/Sanskrit parallels (no Tibetan)
    for taisho_id in sorted(expanded.get("pali_parallels", {}).keys()):
        if taisho_id in taisho_ids_with_rows:
            continue
        t = titles.get(taisho_id, {})
        pali = expanded["pali_parallels"][taisho_id]
        pali_str = "; ".join(sorted(pali)) if isinstance(pali, list) else str(pali)
        nj = nanjio_map.get(taisho_id, set())
        rows.append({
            "taisho_id": taisho_id,
            "tohoku": "",
            "otani": "",
            "nanjio": "; ".join(sorted(nj)),
            "sanskrit_title": t.get("sanskrit_title", ""),
            "chinese_title": t.get("chinese_title", ""),
            "tibetan_title": t.get("tibetan_title", ""),
            "pali_parallel": pali_str,
            "sources": "",
            "source_count": 0,
        })
        taisho_ids_with_rows.add(taisho_id)

    # Write CSV
    fieldnames = [
        "taisho_id", "tohoku", "otani", "nanjio",
        "sanskrit_title", "chinese_title", "tibetan_title",
        "pali_parallel", "sources", "source_count",
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    unique_taisho = len(set(r["taisho_id"] for r in rows))
    toh_rows = sum(1 for r in rows if r["tohoku"])
    with_sources = sum(1 for r in rows if r["source_count"] > 0)
    multi_source = sum(1 for r in rows if r["source_count"] >= 2)

    print(f"\nCSV exported to {OUTPUT_PATH}")
    print(f"  Total rows: {len(rows)}")
    print(f"  Unique Taisho texts: {unique_taisho}")
    print(f"  Rows with Tohoku number: {toh_rows}")
    print(f"  Rows with provenance data: {with_sources}")
    print(f"  Rows with 2+ sources: {multi_source}")


if __name__ == "__main__":
    export_csv()
