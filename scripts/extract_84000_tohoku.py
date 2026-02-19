#!/usr/bin/env python3
"""Extract Tohoku numbers from all 84000 TEI XML files.

Parses both translation files (Kangyur + Tengyur) and section files
to build a complete Toh→file mapping, then cross-references against
the existing concordance to identify gaps.

Output: results/84000_tohoku_extract.json
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "84000-data-tei"
XREF_PATH = BASE_DIR / "results" / "cross_reference.json"
OUTPUT_PATH = BASE_DIR / "results" / "84000_tohoku_extract.json"

TEI_NS = "http://www.tei-c.org/ns/1.0"


def extract_tohoku_from_filename(filename):
    """Extract Tohoku number(s) from 84000 filename pattern like '035-018_toh44-18-...'."""
    # Match patterns like toh44, toh44-18, toh710,930
    match = re.search(r'toh([\d,]+(?:-\d+)?)', filename)
    if match:
        raw = match.group(1)
        # Handle comma-separated (toh710,930 = two separate Toh numbers)
        if ',' in raw:
            return [f"Toh {n.strip()}" for n in raw.split(',')]
        # Handle chapter references (toh44-18 = Toh 44, chapter 18)
        if '-' in raw:
            base = raw.split('-')[0]
            return [f"Toh {base}"]
        return [f"Toh {raw}"]
    return []


def extract_tohoku_from_xml(filepath):
    """Extract Tohoku numbers from <bibl key="toh###"> tags in TEI XML."""
    toh_nums = []
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        # Search for bibl elements with key starting with "toh"
        for bibl in root.iter(f"{{{TEI_NS}}}bibl"):
            key = bibl.get("key", "")
            if key.startswith("toh"):
                # Extract number: toh44, toh44-18, toh4568-5
                match = re.match(r'toh(\d+)', key)
                if match:
                    toh_nums.append(f"Toh {match.group(1)}")
    except ET.ParseError:
        pass
    return list(set(toh_nums))


def extract_titles_from_xml(filepath):
    """Extract English, Sanskrit, Tibetan titles from TEI XML."""
    titles = {}
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        for title in root.iter(f"{{{TEI_NS}}}title"):
            lang = title.get(f"{{{TEI_NS}}}lang", title.get("xml:lang", ""))
            ttype = title.get("type", "")
            text = (title.text or "").strip()
            if text and ttype == "mainTitle":
                if lang == "en":
                    titles["english"] = text
                elif lang in ("Sa-Ltn", "sa-Ltn"):
                    titles["sanskrit"] = text
                elif lang in ("Bo-Ltn", "bo-Ltn"):
                    titles["tibetan_wylie"] = text
                elif lang == "bo":
                    titles["tibetan"] = text
    except ET.ParseError:
        pass
    return titles


def scan_translations(data_dir):
    """Scan all translation XML files and extract Tohoku data."""
    entries = {}
    translations_dir = data_dir / "translations"

    for collection in ["kangyur", "tengyur"]:
        coll_dir = translations_dir / collection
        if not coll_dir.exists():
            continue
        for root_dir, dirs, files in os.walk(coll_dir):
            for filename in files:
                if not filename.endswith(".xml"):
                    continue
                filepath = Path(root_dir) / filename

                # Get Toh from filename
                toh_from_name = extract_tohoku_from_filename(filename)
                # Get Toh from XML
                toh_from_xml = extract_tohoku_from_xml(filepath)
                # Get titles
                titles = extract_titles_from_xml(filepath)

                # Merge Toh numbers
                all_toh = list(set(toh_from_name + toh_from_xml))

                for toh in all_toh:
                    if toh not in entries:
                        entries[toh] = {
                            "collection": collection,
                            "files": [],
                            "titles": {},
                        }
                    entries[toh]["files"].append(str(filepath.relative_to(data_dir)))
                    if titles:
                        entries[toh]["titles"].update(titles)

    return entries


def cross_reference_with_existing(entries, xref_path):
    """Compare extracted Toh numbers against existing concordance."""
    if not xref_path.exists():
        return {"matched": [], "unmatched": [], "new_toh": []}

    with open(xref_path) as f:
        xref = json.load(f)

    # Build set of all Toh numbers in existing concordance
    existing_toh = set()
    for text_id, parallels in xref.get("tibetan_parallels", {}).items():
        for p in parallels:
            if p.startswith("Toh "):
                existing_toh.add(p)

    # Compare
    extracted_toh = set(entries.keys())
    matched = sorted(extracted_toh & existing_toh)
    new_toh = sorted(extracted_toh - existing_toh)

    return {
        "existing_toh_count": len(existing_toh),
        "extracted_toh_count": len(extracted_toh),
        "matched": matched,
        "matched_count": len(matched),
        "new_toh": new_toh,
        "new_toh_count": len(new_toh),
    }


def main():
    print("Scanning 84000 TEI files...")
    entries = scan_translations(DATA_DIR)
    print(f"  Found {len(entries)} unique Tohoku numbers")

    kangyur = {k: v for k, v in entries.items() if v["collection"] == "kangyur"}
    tengyur = {k: v for k, v in entries.items() if v["collection"] == "tengyur"}
    print(f"  Kangyur: {len(kangyur)}")
    print(f"  Tengyur: {len(tengyur)}")

    print("\nCross-referencing with existing concordance...")
    comparison = cross_reference_with_existing(entries, XREF_PATH)
    print(f"  Existing Toh numbers in concordance: {comparison['existing_toh_count']}")
    print(f"  Extracted from 84000: {comparison['extracted_toh_count']}")
    print(f"  Already matched: {comparison['matched_count']}")
    print(f"  New (not in existing concordance): {comparison['new_toh_count']}")

    if comparison["new_toh"]:
        print(f"\n  Sample new Toh numbers: {comparison['new_toh'][:20]}")

    # Save results
    output = {
        "summary": {
            "total_toh": len(entries),
            "kangyur_toh": len(kangyur),
            "tengyur_toh": len(tengyur),
        },
        "comparison": comparison,
        "entries": {k: v for k, v in sorted(entries.items(),
                    key=lambda x: int(re.search(r'\d+', x[0]).group()))},
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
