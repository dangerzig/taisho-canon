#!/usr/bin/env python3
"""Extract Taisho cross-references from 84000 TEI translation files.

The 84000 TEI files contain bibliographic references to Chinese translations
in the Taisho canon, embedded in notes, bibliography sections, and inline
references. This script extracts all such Taisho number references and maps
them to their corresponding Tohoku numbers.

Output: results/84000_taisho_refs.json
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEI_DIR = BASE_DIR / "84000-data-tei" / "translations" / "kangyur"
OUTPUT_PATH = BASE_DIR / "results" / "84000_taisho_refs.json"


def extract_taisho_refs():
    """Extract all Taisho references from 84000 TEI files."""
    entries = {}

    for xml_path in sorted(TEI_DIR.rglob("*.xml")):
        fname = xml_path.name

        # Extract Toh number(s) from filename
        # Filenames like: 040-005_toh54-the_exposition...xml
        # or: 088-001_toh507,883-the_dharani...xml
        toh_matches = re.findall(r'toh(\d+[a-z]?)', fname)
        if not toh_matches:
            continue

        content = xml_path.read_text(errors="replace")

        # Find Taisho references in two formats:
        # 1. "Taishō 645" (in prose text)
        # 2. "taisho/t0645" (in URLs)
        taisho_nums = set()
        for m in re.finditer(r'Taishō\s+(\d+)', content):
            taisho_nums.add(int(m.group(1)))
        for m in re.finditer(r'taisho/t0*(\d+)', content):
            taisho_nums.add(int(m.group(1)))

        if not taisho_nums:
            continue

        # Record for each Toh number in this file
        for toh_str in toh_matches:
            toh_key = f"Toh {toh_str}"
            if toh_key not in entries:
                entries[toh_key] = {
                    "toh": toh_str,
                    "taisho_nums": set(),
                    "source_files": [],
                }
            entries[toh_key]["taisho_nums"].update(taisho_nums)
            entries[toh_key]["source_files"].append(fname)

    # Convert sets to sorted lists for JSON
    output_entries = {}
    for toh_key in sorted(entries, key=lambda x: int(re.search(r'\d+', x).group())):
        entry = entries[toh_key]
        output_entries[toh_key] = {
            "toh": entry["toh"],
            "taisho_nums": sorted(entry["taisho_nums"]),
            "source_files": sorted(set(entry["source_files"])),
        }

    total_links = sum(len(e["taisho_nums"]) for e in output_entries.values())

    output = {
        "source": "84000 Reading Room TEI translations",
        "description": (
            "Taisho cross-references extracted from bibliographic notes "
            "and inline references in 84000 Kangyur translation TEI files."
        ),
        "url": "https://84000.co/",
        "extraction_note": (
            "References found as 'Taishō NNN' in text or "
            "'taisho/tNNN' in URLs within TEI XML files."
        ),
        "stats": {
            "toh_entries_with_taisho_refs": len(output_entries),
            "total_taisho_refs": total_links,
        },
        "entries": output_entries,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(output_entries)} Toh entries "
          f"with {total_links} Taisho cross-references")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    extract_taisho_refs()
