"""Export the cross-reference concordance as a flat CSV file.

Reads results/cross_reference_expanded.json and reconstructs per-mapping
provenance from the original source files. Outputs one row per
Taisho-Tohoku pair to results/cross_reference.csv.

Usage:
    python3 -m digest_detector.export_csv
"""

import csv

from ._export_common import (
    RESULTS_DIR,
    build_provenance,
    gather_metadata,
    load_json,
    load_known_error_pairs,
    EXPANDED_PATH,
)

# Output
OUTPUT_PATH = RESULTS_DIR / "cross_reference.csv"


def export_csv():
    """Export the concordance as a flat CSV with one row per Taisho-Tohoku pair."""
    expanded = load_json(EXPANDED_PATH)
    if not expanded:
        print(f"ERROR: {EXPANDED_PATH} not found.")
        return

    error_pairs = load_known_error_pairs()
    if error_pairs:
        print(f"Loaded {len(error_pairs)} known error pairs to exclude.")

    print("Reconstructing per-mapping provenance from source files...")
    provenance = build_provenance(expanded)

    print("Gathering titles and auxiliary data from source files...")
    titles, nanjio_map, otani_map = gather_metadata(expanded)

    # Build rows: one per (taisho_id, tohoku) pair
    rows = []
    taisho_ids_with_rows = set()
    tibetan = expanded.get("tibetan_parallels", {})

    for taisho_id in sorted(tibetan.keys()):
        parallels = tibetan[taisho_id]

        # Separate Toh and Otani entries, excluding known errors
        toh_entries = [
            p for p in parallels
            if p.startswith("Toh ") and (taisho_id, p) not in error_pairs
        ]
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
            # Collect Otani and Pali provenance for source tracking.
            all_sources = set()
            for ot in sorted(all_otani):
                all_sources.update(provenance.get((taisho_id, ot), set()))
            pali_refs = expanded.get("pali_parallels", {}).get(taisho_id, [])
            if isinstance(pali_refs, list):
                for p_ref in pali_refs:
                    all_sources.update(
                        provenance.get((taisho_id, p_ref), set()))
            sources_str = "; ".join(sorted(all_sources))
            rows.append({
                "taisho_id": taisho_id,
                "tohoku": "",
                "otani": otani_str,
                "nanjio": nanjio_str,
                "sanskrit_title": sanskrit_title,
                "chinese_title": chinese_title,
                "tibetan_title": tibetan_title,
                "pali_parallel": pali_str,
                "sources": sources_str,
                "source_count": len(all_sources),
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
        # Collect Pali provenance sources
        pali_sources = set()
        pali_list = pali if isinstance(pali, list) else [pali]
        for p_ref in pali_list:
            pali_sources.update(provenance.get((taisho_id, p_ref), set()))
        sources_str = "; ".join(sorted(pali_sources))
        rows.append({
            "taisho_id": taisho_id,
            "tohoku": "",
            "otani": "",
            "nanjio": "; ".join(sorted(nj)),
            "sanskrit_title": t.get("sanskrit_title", ""),
            "chinese_title": t.get("chinese_title", ""),
            "tibetan_title": t.get("tibetan_title", ""),
            "pali_parallel": pali_str,
            "sources": sources_str,
            "source_count": len(pali_sources),
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
