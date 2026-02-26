#!/usr/bin/env python3
"""Build a Tohoku-to-Otani concordance using rKTs collection XML files.

The rKTs project (Resources for Kanjur and Tanjur Studies) maintains XML files
for each collection edition. The Derge (D) numbers correspond to Tohoku numbers,
and the Peking (Q) numbers correspond to Otani numbers. Both editions share
rKTs kernel IDs, enabling a join:

    D.xml:  rkts_id -> D_number (= Tohoku)
    Q.xml:  rkts_id -> Q_number (= Otani)

This script parses 4 XML files (Kanjur and Tanjur for both D and Q editions),
joins on kernel IDs, and produces a Tohoku-to-Otani concordance.

Input:
  - data/rkts_collections/D_kanjur.xml
  - data/rkts_collections/Q_kanjur.xml
  - data/rkts_collections/D_tanjur.xml
  - data/rkts_collections/Q_tanjur.xml

Output:
  - results/tohoku_otani_concordance.json
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "rkts_collections"
OUTPUT_PATH = BASE_DIR / "results" / "tohoku_otani_concordance.json"


def parse_collection_xml(xml_text, collection_type):
    """Parse an rKTs collection XML file to extract (kernel_id, ref) pairs.

    Args:
        xml_text: Raw XML text.
        collection_type: "kanjur" or "tanjur" -- determines the kernel ID tag
                         (<rkts> for Kanjur, <rktst> for Tanjur).

    Returns:
        Dict mapping kernel_id (str) -> list of ref_str (str).
        Ref strings are the bare number or number+letter, e.g. "1", "7a", "1109".
        Multiple refs per kernel ID occur when the same text appears at multiple
        locations in the canon (e.g., kernel 529 -> ["21", "531"]).
        Only top-level items are included (subitems like D1-1 are skipped).
    """
    kernel_tag = "rkts" if collection_type == "kanjur" else "rktst"
    mapping = defaultdict(list)

    # Match <item> blocks (not <subitem> blocks) that contain kernel IDs
    # and ref numbers. Use regex because the XML has irregular formatting.
    for item_match in re.finditer(r'<item>(.*?)</item>', xml_text, re.DOTALL):
        item_text = item_match.group(1)

        # Extract kernel ID -- must be a plain integer (skip sub-IDs like "1-1")
        kernel_match = re.search(
            rf'<{kernel_tag}>(\d+)</{kernel_tag}>', item_text
        )
        if not kernel_match:
            continue
        kernel_id = kernel_match.group(1)

        # Extract ref (D### or Q###), optionally with letter suffix (e.g. D7a)
        # or comma sub-section (e.g. Q760,01 — Ratnakūṭa sub-sections)
        ref_match = re.search(r'<ref>[DQ](\d+(?:[a-z]|,\d+)?)</ref>', item_text)
        if not ref_match:
            continue
        ref_str = ref_match.group(1)

        if ref_str not in mapping[kernel_id]:
            mapping[kernel_id].append(ref_str)

    return dict(mapping)


def _ref_sort_key(ref_str):
    """Sort key for ref strings: numeric part first, then suffix.

    Examples: "1" -> (1, "", 0), "7a" -> (7, "a", 0), "760,01" -> (760, "", 1)
    """
    # Handle comma sub-sections like "760,01"
    comma = re.match(r'(\d+),(\d+)', ref_str)
    if comma:
        return (int(comma.group(1)), "", int(comma.group(2)))
    m = re.match(r'(\d+)([a-z]*)', ref_str)
    return (int(m.group(1)), m.group(2), 0) if m else (0, ref_str, 0)


def build_concordance(d_kanjur, q_kanjur, d_tanjur, q_tanjur):
    """Build Tohoku-to-Otani concordance by joining D and Q on kernel IDs.

    Args:
        d_kanjur: Dict of kernel_id -> list of Derge/Tohoku ref strs (Kanjur).
        q_kanjur: Dict of kernel_id -> list of Peking/Otani ref strs (Kanjur).
        d_tanjur: Dict of kernel_id -> list of Derge/Tohoku ref strs (Tanjur).
        q_tanjur: Dict of kernel_id -> list of Peking/Otani ref strs (Tanjur).

    Returns:
        Tuple of (concordance_dict, stats_dict).
        concordance_dict maps "Toh N" -> sorted list of "Otani M" strings.
    """
    # Join on kernel IDs — each D ref maps to every Q ref for that kernel
    toh_to_otani = defaultdict(set)
    kanjur_count = 0
    tanjur_count = 0

    # Kanjur join
    shared_kanjur = set(d_kanjur.keys()) & set(q_kanjur.keys())
    for kernel_id in shared_kanjur:
        d_refs = d_kanjur[kernel_id]
        q_refs = q_kanjur[kernel_id]
        for toh_ref in d_refs:
            for otani_ref in q_refs:
                toh_to_otani[toh_ref].add(otani_ref)
        kanjur_count += 1

    # Tanjur join
    shared_tanjur = set(d_tanjur.keys()) & set(q_tanjur.keys())
    for kernel_id in shared_tanjur:
        d_refs = d_tanjur[kernel_id]
        q_refs = q_tanjur[kernel_id]
        for toh_ref in d_refs:
            for otani_ref in q_refs:
                toh_to_otani[toh_ref].add(otani_ref)
        tanjur_count += 1

    # Format output, sorted by Tohoku number
    concordance = {}
    for toh_ref in sorted(toh_to_otani.keys(), key=_ref_sort_key):
        toh_key = f"Toh {toh_ref}"
        otani_list = sorted(
            (f"Otani {n}" for n in toh_to_otani[toh_ref]),
            key=lambda s: _ref_sort_key(s.split(" ", 1)[1]),
        )
        concordance[toh_key] = otani_list

    stats = {
        "total_tohoku_numbers": len(concordance),
        "total_otani_numbers": len(
            {o for otanis in concordance.values() for o in otanis}
        ),
        "total_mappings": sum(len(v) for v in concordance.values()),
        "kanjur_mappings": kanjur_count,
        "tanjur_mappings": tanjur_count,
        "d_kanjur_items": len(d_kanjur),
        "q_kanjur_items": len(q_kanjur),
        "d_tanjur_items": len(d_tanjur),
        "q_tanjur_items": len(q_tanjur),
        "shared_kanjur_kernel_ids": len(shared_kanjur),
        "shared_tanjur_kernel_ids": len(shared_tanjur),
    }

    return concordance, stats


def main():
    print("Building Tohoku-to-Otani concordance from rKTs collection XMLs")
    print("=" * 60)

    # Load XML files
    files = {
        "D_kanjur": DATA_DIR / "D_kanjur.xml",
        "Q_kanjur": DATA_DIR / "Q_kanjur.xml",
        "D_tanjur": DATA_DIR / "D_tanjur.xml",
        "Q_tanjur": DATA_DIR / "Q_tanjur.xml",
    }

    xml_texts = {}
    for name, path in files.items():
        if not path.exists():
            print(f"ERROR: {path} not found. Please download rKTs XMLs first.")
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            xml_texts[name] = f.read()
        print(f"  Loaded {name}: {path.stat().st_size:,} bytes")

    # Parse each collection
    print("\nParsing collection XMLs...")
    d_kanjur = parse_collection_xml(xml_texts["D_kanjur"], "kanjur")
    q_kanjur = parse_collection_xml(xml_texts["Q_kanjur"], "kanjur")
    d_tanjur = parse_collection_xml(xml_texts["D_tanjur"], "tanjur")
    q_tanjur = parse_collection_xml(xml_texts["Q_tanjur"], "tanjur")

    print(f"  D Kanjur: {len(d_kanjur)} items")
    print(f"  Q Kanjur: {len(q_kanjur)} items")
    print(f"  D Tanjur: {len(d_tanjur)} items")
    print(f"  Q Tanjur: {len(q_tanjur)} items")

    # Build concordance
    print("\nJoining on kernel IDs...")
    concordance, stats = build_concordance(d_kanjur, q_kanjur, d_tanjur, q_tanjur)

    # Summary
    print(f"\n{'=' * 60}")
    print("CONCORDANCE SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Tohoku numbers with Otani mapping: {stats['total_tohoku_numbers']}")
    print(f"  Unique Otani numbers:              {stats['total_otani_numbers']}")
    print(f"  Total mappings (Toh->Otani pairs):  {stats['total_mappings']}")
    print(f"  Kanjur mappings:                   {stats['kanjur_mappings']}")
    print(f"  Tanjur mappings:                   {stats['tanjur_mappings']}")
    print(f"  Shared Kanjur kernel IDs:          {stats['shared_kanjur_kernel_ids']}")
    print(f"  Shared Tanjur kernel IDs:          {stats['shared_tanjur_kernel_ids']}")

    # Write output
    output = {
        "description": (
            "Tohoku-to-Otani concordance built from rKTs collection XMLs. "
            "Derge (D) numbers = Tohoku numbers; Peking (Q) numbers = Otani numbers. "
            "Joined via shared rKTs kernel IDs."
        ),
        "stats": stats,
        "concordance": concordance,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nConcordance written to {OUTPUT_PATH}")

    # Show a few examples
    print("\nSample entries:")
    for toh_key in list(concordance.keys())[:10]:
        print(f"  {toh_key} -> {concordance[toh_key]}")

    return concordance, stats


if __name__ == "__main__":
    main()
