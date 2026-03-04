#!/usr/bin/env python3
"""Find Peking-only texts: Otani entries with no Derge/Tohoku counterpart.

Parses the rKTs collection XMLs to find kernel IDs that exist in the
Peking (Q) edition but not in the Derge (D) edition. These represent
texts present in the Peking canon but absent from the Derge, meaning
they have Otani numbers but no Tohoku numbers.

Then checks whether any of these Peking-only texts have known Taishō
parallels from any concordance source (Lancaster, CBETA, etc.).

Output:
  - results/peking_only_texts.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "rkts_collections"
RESULTS_DIR = BASE_DIR / "results"
CONCORDANCE_PATH = RESULTS_DIR / "cross_reference_expanded.json"
LANCASTER_PATH = BASE_DIR / "lancaster_taisho_crossref.json"
OUTPUT_PATH = RESULTS_DIR / "peking_only_texts.json"


def parse_collection_xml(xml_text, collection_type):
    """Parse an rKTs collection XML file to extract (kernel_id, ref, title) tuples.

    Returns dict mapping kernel_id -> list of dicts with ref and titles.
    """
    kernel_tag = "rkts" if collection_type == "kanjur" else "rktst"
    mapping = defaultdict(list)

    for item_match in re.finditer(r'<item>(.*?)</item>', xml_text, re.DOTALL):
        item_text = item_match.group(1)

        kernel_match = re.search(
            rf'<{kernel_tag}>(\d+)</{kernel_tag}>', item_text
        )
        if not kernel_match:
            continue
        kernel_id = kernel_match.group(1)

        ref_match = re.search(r'<ref>[DQ](\d+(?:[a-z]|,\d+)?)</ref>', item_text)
        if not ref_match:
            continue
        ref_str = ref_match.group(1)

        # Extract titles for identification
        tib_match = re.search(r'<tib>(.*?)</tib>', item_text, re.DOTALL)
        skt_match = (
            re.search(r'<skttrans>(.*?)</skttrans>', item_text, re.DOTALL)
            or re.search(r'<sanskrit>(.*?)</sanskrit>', item_text, re.DOTALL)
        )

        entry = {
            "ref": ref_str,
            "tibetan_title": tib_match.group(1).strip() if tib_match else "",
            "sanskrit_title": skt_match.group(1).strip() if skt_match else "",
        }

        if ref_str not in [e["ref"] for e in mapping[kernel_id]]:
            mapping[kernel_id].append(entry)

    return dict(mapping)


def find_peking_only(d_data, q_data, edition_label):
    """Find kernel IDs in Q but not in D."""
    q_only_kernels = set(q_data.keys()) - set(d_data.keys())
    results = []
    for kernel_id in sorted(q_only_kernels, key=int):
        for entry in q_data[kernel_id]:
            results.append({
                "kernel_id": kernel_id,
                "otani": f"Otani {entry['ref']}",
                "tibetan_title": entry["tibetan_title"],
                "sanskrit_title": entry["sanskrit_title"],
                "edition": edition_label,
            })
    return results


def check_lancaster_otani(lancaster_path):
    """Extract Otani entries from Lancaster with their Taishō links."""
    if not lancaster_path.exists():
        return {}

    with open(lancaster_path) as f:
        lancaster = json.load(f)

    otani_to_taisho = defaultdict(list)
    for k_num, data in lancaster.items():
        otani_nums = data.get("otani", [])
        toh_nums = data.get("tohoku", [])
        taisho_raw = data.get("taisho", None)

        # taisho field can be int or list
        if taisho_raw is None:
            continue
        if isinstance(taisho_raw, (int, str)):
            taisho_nums = [str(taisho_raw)]
        elif isinstance(taisho_raw, list):
            taisho_nums = [str(t) for t in taisho_raw]
        else:
            continue

        if otani_nums and taisho_nums:
            for ot in otani_nums:
                otani_key = f"Otani {ot}"
                for t in taisho_nums:
                    otani_to_taisho[otani_key].append({
                        "taisho": f"T{t}" if not t.startswith("T") else t,
                        "k_number": k_num,
                        "has_tohoku": bool(toh_nums),
                        "tohoku": toh_nums,
                    })

    return dict(otani_to_taisho)


def check_concordance_otani(concordance_path):
    """Build reverse Otani->Taishō index from the existing concordance."""
    if not concordance_path.exists():
        return {}

    with open(concordance_path) as f:
        concordance = json.load(f)

    # Schema v2: tibetan_parallels is a top-level dict of taisho_id -> list
    tibetan = concordance.get("tibetan_parallels", {})

    otani_to_taisho = defaultdict(list)
    for taisho_id, parallels in tibetan.items():
        if not isinstance(parallels, list):
            continue
        for p in parallels:
            if isinstance(p, str) and p.startswith("Otani "):
                otani_to_taisho[p].append(taisho_id)

    return dict(otani_to_taisho)


def main():
    print("Finding Peking-only texts (Q without D counterpart)")
    print("=" * 60)

    # Load and parse rKTs XMLs
    files = {
        "D_kanjur": DATA_DIR / "D_kanjur.xml",
        "Q_kanjur": DATA_DIR / "Q_kanjur.xml",
        "D_tanjur": DATA_DIR / "D_tanjur.xml",
        "Q_tanjur": DATA_DIR / "Q_tanjur.xml",
    }

    xml_texts = {}
    for name, path in files.items():
        if not path.exists():
            print(f"ERROR: {path} not found")
            return
        with open(path, encoding="utf-8") as f:
            xml_texts[name] = f.read()
        print(f"  Loaded {name}: {path.stat().st_size:,} bytes")

    print("\nParsing collection XMLs...")
    d_kanjur = parse_collection_xml(xml_texts["D_kanjur"], "kanjur")
    q_kanjur = parse_collection_xml(xml_texts["Q_kanjur"], "kanjur")
    d_tanjur = parse_collection_xml(xml_texts["D_tanjur"], "tanjur")
    q_tanjur = parse_collection_xml(xml_texts["Q_tanjur"], "tanjur")

    print(f"  D Kanjur: {len(d_kanjur)} kernel IDs")
    print(f"  Q Kanjur: {len(q_kanjur)} kernel IDs")
    print(f"  D Tanjur: {len(d_tanjur)} kernel IDs")
    print(f"  Q Tanjur: {len(q_tanjur)} kernel IDs")

    # Find Q-only entries
    print("\nFinding Peking-only texts...")
    kanjur_only = find_peking_only(d_kanjur, q_kanjur, "Kanjur")
    tanjur_only = find_peking_only(d_tanjur, q_tanjur, "Tanjur")
    all_peking_only = kanjur_only + tanjur_only

    print(f"\n  Peking-only Kanjur texts: {len(kanjur_only)}")
    print(f"  Peking-only Tanjur texts: {len(tanjur_only)}")
    print(f"  Total Peking-only:        {len(all_peking_only)}")

    if kanjur_only:
        print("\n  Peking-only Kanjur entries:")
        for entry in kanjur_only:
            print(f"    {entry['otani']} (kernel {entry['kernel_id']}): "
                  f"{entry['sanskrit_title'] or entry['tibetan_title'] or '(no title)'}")

    if tanjur_only:
        print(f"\n  Peking-only Tanjur entries (first 20 of {len(tanjur_only)}):")
        for entry in tanjur_only[:20]:
            print(f"    {entry['otani']} (kernel {entry['kernel_id']}): "
                  f"{entry['sanskrit_title'] or entry['tibetan_title'] or '(no title)'}")

    # Check for Taishō parallels
    print("\n" + "=" * 60)
    print("Checking for Taishō parallels...")

    # Build Otani->Taishō indices from existing data
    lancaster_otani = check_lancaster_otani(LANCASTER_PATH)
    concordance_otani = check_concordance_otani(CONCORDANCE_PATH)

    print(f"  Lancaster: {len(lancaster_otani)} Otani numbers with Taishō links")
    print(f"  Concordance: {len(concordance_otani)} Otani numbers with Taishō links")

    # Check each Peking-only text
    matches = []
    for entry in all_peking_only:
        otani_key = entry["otani"]
        taisho_from_lancaster = lancaster_otani.get(otani_key, [])
        taisho_from_concordance = concordance_otani.get(otani_key, [])

        if taisho_from_lancaster or taisho_from_concordance:
            entry["taisho_parallels"] = {
                "from_lancaster": taisho_from_lancaster,
                "from_concordance": taisho_from_concordance,
            }
            matches.append(entry)

    print(f"\n  Peking-only texts WITH Taishō parallels: {len(matches)}")
    if matches:
        for m in matches:
            taisho_ids = set()
            for item in m["taisho_parallels"].get("from_lancaster", []):
                taisho_ids.add(item["taisho"])
            for item in m["taisho_parallels"].get("from_concordance", []):
                taisho_ids.add(item)
            print(f"    {m['otani']} -> {', '.join(sorted(taisho_ids))}")
            print(f"      Title: {m['sanskrit_title'] or m['tibetan_title']}")

    print(f"\n  Peking-only texts WITHOUT Taishō parallels: "
          f"{len(all_peking_only) - len(matches)}")

    # Also check: are there Otani numbers in the concordance that are
    # NOT in the rKTs Toh->Otani concordance?
    print("\n" + "=" * 60)
    print("Checking for 'orphan' Otani numbers in concordance...")

    toh_otani_path = RESULTS_DIR / "tohoku_otani_concordance.json"
    if toh_otani_path.exists():
        with open(toh_otani_path) as f:
            toh_otani = json.load(f)
        rkts_otani = set()
        for otani_list in toh_otani.get("concordance", {}).values():
            rkts_otani.update(otani_list)

        concordance_all_otani = set(concordance_otani.keys())
        orphan_otani = concordance_all_otani - rkts_otani
        if orphan_otani:
            print(f"  Found {len(orphan_otani)} Otani numbers in concordance "
                  f"but NOT in rKTs Toh->Otani mapping:")
            for ot in sorted(orphan_otani,
                             key=lambda s: int(re.search(r'\d+', s).group())):
                taisho_texts = concordance_otani.get(ot, [])
                print(f"    {ot} -> {', '.join(taisho_texts)}")
        else:
            print("  All concordance Otani numbers are in rKTs mapping.")

    # Build and write Otani->Taishō reverse index
    print("\n" + "=" * 60)
    print("Building Otani → Taishō reverse index...")
    otani_reverse = {}
    for otani_key in sorted(concordance_otani.keys(),
                            key=lambda s: int(re.search(r'\d+', s).group())):
        otani_reverse[otani_key] = sorted(concordance_otani[otani_key])

    otani_index_path = RESULTS_DIR / "otani_taisho_crossref.json"
    otani_index_output = {
        "description": (
            "Reverse index: Otani number → Taishō texts. "
            "Built from cross_reference_expanded.json tibetan_parallels."
        ),
        "stats": {
            "total_otani_numbers": len(otani_reverse),
            "total_taisho_texts": len({t for ts in otani_reverse.values()
                                       for t in ts}),
        },
        "entries": otani_reverse,
    }
    with open(otani_index_path, "w") as f:
        json.dump(otani_index_output, f, indent=2, ensure_ascii=False)
    print(f"  {len(otani_reverse)} Otani numbers → "
          f"{otani_index_output['stats']['total_taisho_texts']} Taishō texts")
    print(f"  Written to {otani_index_path}")

    print("\n  Sample entries:")
    for key in list(otani_reverse.keys())[:5]:
        print(f"    {key} -> {otani_reverse[key]}")

    # Write output
    output = {
        "description": (
            "Peking-only texts: entries in the Peking (Q) edition with no "
            "Derge (D) counterpart, meaning they have Otani numbers but no "
            "Tohoku numbers."
        ),
        "stats": {
            "peking_only_kanjur": len(kanjur_only),
            "peking_only_tanjur": len(tanjur_only),
            "total_peking_only": len(all_peking_only),
            "with_taisho_parallels": len(matches),
            "without_taisho_parallels": len(all_peking_only) - len(matches),
        },
        "peking_only_texts": all_peking_only,
        "texts_with_taisho_parallels": matches,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
