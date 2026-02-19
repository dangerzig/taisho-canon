#!/usr/bin/env python3
"""Parse rKTs (Resources for Kanjur and Tanjur Studies) XML data.

Downloads and parses:
  - Kernel/rkts.xml (Kanjur kernel with Taisho cross-refs)
  - Collections/D Derge Kanjur/D.xml (rkts→Dergé/Tohoku mapping)

The rKTs kernel has `<cmp>` comparison tags, some of type "translation-taisho"
that map Tibetan texts to their Chinese translations in the Taisho.

Note: Only ~26 Taisho cross-refs exist in the Kanjur kernel (this is a
Tibetan-centric resource), but every mapping is valuable.

Output: results/rkts_taisho.json
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from io import StringIO
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "results" / "rkts_taisho.json"

RKTS_KERNEL_URL = "https://raw.githubusercontent.com/brunogml/rKTs/master/Kernel/rkts.xml"
DERGE_KANJUR_URL = "https://raw.githubusercontent.com/brunogml/rKTs/master/Collections/D%20Derge%20Kanjur/D.xml"

USER_AGENT = "TaishoCanonResearch/1.0 (academic research)"


def fetch_url(url):
    """Fetch a URL."""
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=60) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def parse_derge_mapping(xml_text):
    """Parse D.xml to build rkts→Tohoku mapping.

    Format: <item><rkts>1</rkts><ref>D1</ref>...</item>
    D numbers ARE Tohoku numbers (Dergé Kanjur).
    """
    rkts_to_toh = {}
    # Use regex since the XML may have irregular formatting
    for match in re.finditer(r'<rkts>([^<]+)</rkts>\s*<ref>D(\d+)</ref>', xml_text):
        rkts_id = match.group(1).strip()
        d_num = int(match.group(2))
        rkts_to_toh[rkts_id] = d_num
    return rkts_to_toh


def parse_kernel(xml_text, rkts_to_toh):
    """Parse rkts.xml kernel to extract Taisho cross-references.

    Each <item> may have:
      <rkts>###</rkts> — rKTs ID
      <section>...</section> — section name
      <StandardTibetan>...</StandardTibetan> — standard Tibetan title
      <StandardSanskrit>...</StandardSanskrit> — standard Sanskrit title
      <English84000>...</English84000> — English title from 84000
      <cmp><ref>T####</ref><type>translation-taisho</type></cmp> — Taisho link
    """
    entries = {}

    # Parse item by item using regex (XML may have issues)
    for item_match in re.finditer(r'<item>(.*?)</item>', xml_text, re.DOTALL):
        item_text = item_match.group(1)

        # rKTs ID
        rkts_match = re.search(r'<rkts>([^<]+)</rkts>', item_text)
        if not rkts_match:
            continue
        rkts_id = rkts_match.group(1).strip()

        # Extract Taisho cross-refs
        taisho_refs = []
        for cmp_match in re.finditer(
            r'<cmp><ref>(T\d+(?:-\d+)?)</ref><type>translation-taisho</type></cmp>',
            item_text
        ):
            t_raw = cmp_match.group(1)
            # Normalize: T0310-7 → T310, T0670 → T670
            t_base = re.match(r'T(\d+)', t_raw)
            if t_base:
                t_id = f"T{int(t_base.group(1))}"
                if t_id not in taisho_refs:
                    taisho_refs.append(t_id)

        if not taisho_refs:
            continue

        # Tohoku number
        toh_num = rkts_to_toh.get(rkts_id)

        # Section
        section_match = re.search(r'<section>([^<]+)</section>', item_text)
        section = section_match.group(1).strip() if section_match else None

        # Titles
        std_tib = re.search(r'<StandardTibetan>([^<]+)', item_text)
        std_skt = re.search(r'<StandardSanskrit>([^<]+)', item_text)
        eng_84000 = re.search(r'<English84000>([^<]+)', item_text)

        entry = {
            "rkts_id": rkts_id,
            "tohoku": toh_num,
            "taisho": taisho_refs,
            "section": section,
            "tibetan_title": std_tib.group(1).strip() if std_tib else None,
            "sanskrit_title": std_skt.group(1).strip() if std_skt else None,
            "english_title": eng_84000.group(1).strip() if eng_84000 else None,
        }
        entries[rkts_id] = entry

    return entries


def main():
    print("Parsing rKTs (Resources for Kanjur and Tanjur Studies)...")

    # Step 1: Download Dergé mapping
    print(f"\n1. Fetching Dergé Kanjur mapping...")
    derge_xml = fetch_url(DERGE_KANJUR_URL)
    if not derge_xml:
        print("ERROR: Could not fetch Dergé mapping")
        sys.exit(1)
    rkts_to_toh = parse_derge_mapping(derge_xml)
    print(f"  Found {len(rkts_to_toh)} rkts→Tohoku mappings")

    # Step 2: Download and parse kernel
    print(f"\n2. Fetching Kanjur kernel...")
    kernel_xml = fetch_url(RKTS_KERNEL_URL)
    if not kernel_xml:
        print("ERROR: Could not fetch kernel")
        sys.exit(1)
    entries = parse_kernel(kernel_xml, rkts_to_toh)
    print(f"  Found {len(entries)} entries with Taisho cross-refs")

    # Summary
    all_taisho = set()
    all_toh = set()
    for e in entries.values():
        all_taisho.update(e["taisho"])
        if e["tohoku"]:
            all_toh.add(e["tohoku"])

    print(f"\n=== Results ===")
    print(f"Entries with Taisho mapping: {len(entries)}")
    print(f"  Unique Taisho IDs: {len(all_taisho)}")
    print(f"  With Tohoku number: {len(all_toh)}")
    print(f"  Taisho IDs: {sorted(all_taisho)}")

    output = {
        "summary": {
            "total_entries": len(entries),
            "unique_taisho": len(all_taisho),
            "with_tohoku": len(all_toh),
        },
        "entries": entries,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
