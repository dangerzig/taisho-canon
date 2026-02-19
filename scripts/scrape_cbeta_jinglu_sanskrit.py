#!/usr/bin/env python3
"""Scrape CBETA Jinglu Sanskrit/Pali detail pages for additional cross-references.

The CBETA Jinglu has ~1,395 Sanskrit/Pali entries with Taisho cross-references
accessible via /cgi-bin/jl_san_detail.pl?lang=&id=NNNN (NNNN=0001-1395).

This complements the Tibetan pages we already scraped by providing Taisho
mappings from the Sanskrit/Pali angle.

Output: results/cbeta_jinglu_sanskrit.json
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "results" / "cbeta_jinglu_sanskrit.json"

BASE_URL = "http://jinglu.cbeta.org/cgi-bin/jl_san_detail.pl?lang=&id="
MAX_ID = 1400  # Slightly above expected max
REQUEST_DELAY = 0.5  # seconds between requests
USER_AGENT = "TaishoCanonResearch/1.0 (academic research)"


def fetch_url(url, retries=3):
    """Fetch a URL with retries and polite delay."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(REQUEST_DELAY * 2)
            else:
                return None
    return None


def extract_table_field(html, field_name):
    """Extract value from a CBETA Jinglu HTML table row.

    Format: <td>field_name</td><td>value&nbsp;</td>
    """
    pattern = rf'<td>{re.escape(field_name)}</td>\s*<td>(.*?)(?:&nbsp;)*</td>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        # Strip HTML tags and normalize whitespace
        val = re.sub(r'<[^>]+>', '', match.group(1))
        val = val.replace('&nbsp;', '').strip()
        return val if val else None
    return None


def parse_detail_page(html, entry_id):
    """Parse a Sanskrit/Pali detail page for cross-references.

    The pages use structured HTML tables with labeled fields:
    T_No., K_No., title_sa, cat_to, cat_o, cat_nj, etc.
    """
    result = {
        "id": entry_id,
        "sanskrit_title": None,
        "k_number": None,
        "taisho": [],
        "tohoku": [],
        "otani": [],
        "nanjio": None,
    }

    if not html or len(html) < 100:
        return None

    # Check for empty/error pages
    if "No data" in html or "找不到" in html:
        return None

    # Check this is actually a detail page with data
    if "T_No." not in html and "K_No." not in html:
        return None

    # Extract Taisho number from structured field
    t_no = extract_table_field(html, "T_No.")
    if t_no:
        # Format: T0220 or T0220(1-200), etc.
        for m in re.findall(r'T(\d{4})', t_no):
            t_id = f"T{int(m)}"
            if t_id not in result["taisho"]:
                result["taisho"].append(t_id)

    # K number
    k_no = extract_table_field(html, "K_No.")
    if k_no:
        result["k_number"] = k_no.strip()

    # Sanskrit title
    title_sa = extract_table_field(html, "title_sa")
    if title_sa:
        result["sanskrit_title"] = title_sa

    # Tohoku from cat_to field
    cat_to = extract_table_field(html, "cat_to")
    if cat_to:
        for m in re.findall(r'(\d+)', cat_to):
            num = int(m)
            if num > 0:  # Skip zeros
                toh_id = f"Toh {num}"
                if toh_id not in result["tohoku"]:
                    result["tohoku"].append(toh_id)

    # Otani from cat_o field
    cat_o = extract_table_field(html, "cat_o")
    if cat_o and cat_o != "O. (see below).":
        for m in re.findall(r'(\d+)', cat_o):
            num = int(m)
            if num > 10:  # Otani numbers are typically > 10
                ot_id = f"Otani {num}"
                if ot_id not in result["otani"]:
                    result["otani"].append(ot_id)

    # Also extract Otani from other_catalogues if present
    other_cat = extract_table_field(html, "other_catalogues")
    if other_cat:
        # Pattern: O. 731, O. 16
        for m in re.findall(r'O\.\s*(\d+)', other_cat):
            num = int(m)
            if num > 10:
                ot_id = f"Otani {num}"
                if ot_id not in result["otani"]:
                    result["otani"].append(ot_id)

    # Nanjio from cat_nj field
    cat_nj = extract_table_field(html, "cat_nj")
    if cat_nj:
        m = re.match(r'(\d+)', cat_nj.strip())
        if m:
            result["nanjio"] = f"Nj {m.group(1)}"

    # Also check trans_desc for additional Taisho refs (T. 2154-555b:28 format)
    trans_desc = extract_table_field(html, "trans_desc")
    if trans_desc:
        for m in re.findall(r'T\.\s*(\d{4})', trans_desc):
            t_id = f"T{int(m)}"
            # These are typically bibliography refs (T2154 = Kaiyuan lu), not text IDs
            # Only include if they look like actual text numbers (< 2100)
            if int(m) < 2100 and t_id not in result["taisho"]:
                result["taisho"].append(t_id)

    # If we found no Taisho number, skip
    if not result["taisho"]:
        return None

    return result


def main():
    print(f"Scraping CBETA Jinglu Sanskrit/Pali detail pages...")
    print(f"URL pattern: {BASE_URL}NNNN")
    print(f"Scanning IDs 0001-{MAX_ID:04d}")

    entries = {}
    empty_count = 0
    consecutive_empty = 0

    for entry_id in range(1, MAX_ID + 1):
        if entry_id % 100 == 0:
            print(f"  Progress: {entry_id}/{MAX_ID} ({len(entries)} entries found, {empty_count} empty)")

        url = f"{BASE_URL}{entry_id:04d}"
        html = fetch_url(url)

        if html is None:
            consecutive_empty += 1
            empty_count += 1
            if consecutive_empty > 50:
                print(f"  50 consecutive failures at ID {entry_id}, stopping.")
                break
            time.sleep(REQUEST_DELAY)
            continue

        result = parse_detail_page(html, entry_id)
        if result:
            entries[str(entry_id)] = result
            consecutive_empty = 0
        else:
            empty_count += 1
            consecutive_empty += 1
            if consecutive_empty > 50:
                print(f"  50 consecutive empty pages at ID {entry_id}, stopping.")
                break

        time.sleep(REQUEST_DELAY)

    # Summary
    with_taisho = sum(1 for e in entries.values() if e["taisho"])
    with_tohoku = sum(1 for e in entries.values() if e["tohoku"])
    with_otani = sum(1 for e in entries.values() if e["otani"])

    # Collect all unique Taisho IDs found
    all_taisho = set()
    for e in entries.values():
        all_taisho.update(e["taisho"])

    print(f"\n=== Results ===")
    print(f"Total entries with data: {len(entries)}")
    print(f"  With Taisho refs: {with_taisho}")
    print(f"  With Tohoku refs: {with_tohoku}")
    print(f"  With Otani refs: {with_otani}")
    print(f"  Unique Taisho IDs: {len(all_taisho)}")

    # Remove raw_text from output to keep file size reasonable
    for e in entries.values():
        if "raw_text" in e:
            del e["raw_text"]

    output = {
        "summary": {
            "total_entries": len(entries),
            "with_taisho": with_taisho,
            "with_tohoku": with_tohoku,
            "with_otani": with_otani,
            "unique_taisho": len(all_taisho),
            "max_id_scanned": MAX_ID,
        },
        "entries": entries,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
