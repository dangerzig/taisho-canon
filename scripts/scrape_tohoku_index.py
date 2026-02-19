#!/usr/bin/env python3
"""Scrape the acmuller.net Tohoku index to build Toh→K→Taisho mappings.

Works from the Tibetan side: starts with each Tohoku number, follows to
its K-number detail page(s), and extracts Taisho cross-references.

This catches Taisho↔Tibetan mappings that our Chinese-side scraping missed.

Output: results/tohoku_taisho_crossref.json
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from html.parser import HTMLParser

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "results" / "tohoku_taisho_crossref.json"
EXISTING_LANCASTER = BASE_DIR / "lancaster_taisho_crossref.json"

TOHOKU_INDEX_URL = "http://www.acmuller.net/descriptive_catalogue/indexes/index-tohoku.html"
K_DETAIL_BASE = "http://www.acmuller.net/descriptive_catalogue/files/"

# Be polite
REQUEST_DELAY = 1.0  # seconds between requests
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
                print(f"  Retry {attempt + 1} for {url}: {e}")
                time.sleep(REQUEST_DELAY * 2)
            else:
                print(f"  FAILED {url}: {e}")
                return None
    return None


def parse_tohoku_index(html):
    """Parse the Tohoku index page to extract Toh→[K numbers] mapping.

    Format: <p>To. 21     <a href="../files/k0020.html">K 20</a>, ...</p>
    """
    toh_to_k = {}
    # Match lines like: To. 21 ... K 20, K 21, ...
    for line in html.split("\n"):
        toh_match = re.search(r'To\.\s+(\d+)', line)
        if not toh_match:
            continue
        toh_num = int(toh_match.group(1))
        # Extract all K references
        k_refs = re.findall(r'href="[^"]*/(k[\d-]+\.html)"[^>]*>([^<]+)</a>', line)
        k_numbers = []
        k_files = []
        for k_file, k_label in k_refs:
            k_numbers.append(k_label.strip())
            k_files.append(k_file)
        if k_numbers:
            toh_to_k[toh_num] = {
                "k_numbers": k_numbers,
                "k_files": list(set(k_files)),
            }
    return toh_to_k


def parse_k_detail_page(html, k_file):
    """Parse a K-number detail page to extract Taisho and other cross-references.

    The detail pages contain lines like:
    (4) Nj. 19; Ono. 10:274a; To. 21, 531; O. 16.
    And a line with T. number like:
    K 21  (T. 250)  (H. 247)
    """
    result = {
        "taisho": [],
        "nanjio": [],
        "otani": [],
        "tohoku": [],
        "sanskrit_title": None,
        "chinese_title": None,
        "tibetan_title": None,
    }

    # Extract Taisho number from header: K ### (T. ###)
    t_matches = re.findall(r'\(T\.\s*([\d,\s]+)\)', html)
    for tm in t_matches:
        for num in re.findall(r'\d+', tm):
            t_id = f"T{int(num)}"
            if t_id not in result["taisho"]:
                result["taisho"].append(t_id)

    # Extract from cross-reference line (usually line 4)
    # Nanjio
    nj_matches = re.findall(r'Nj\.\s*(\d+)', html)
    for nj in nj_matches:
        result["nanjio"].append(f"Nj {nj}")

    # Otani
    o_matches = re.findall(r'O\.\s*(\d+)', html)
    for o in o_matches:
        result["otani"].append(f"Otani {o}")

    # Tohoku (from the detail page itself)
    to_matches = re.findall(r'To\.\s*([\d,\s]+)', html)
    for to in to_matches:
        for num in re.findall(r'\d+', to):
            toh_id = f"Toh {num}"
            if toh_id not in result["tohoku"]:
                result["tohoku"].append(toh_id)

    # Try to extract Sanskrit title (usually line (i))
    skt_match = re.search(r'\(i\)\s*([^\n<]+)', html)
    if skt_match:
        title = skt_match.group(1).strip().rstrip('.')
        if title and len(title) > 2:
            result["sanskrit_title"] = title

    # Chinese title
    zh_match = re.search(r'\(iii\)\s*([^\n<]+)', html)
    if zh_match:
        title = zh_match.group(1).strip().rstrip('.')
        if title and len(title) > 2:
            result["chinese_title"] = title

    # Tibetan title
    tib_match = re.search(r'\(ii\)\s*([^\n<]+)', html)
    if tib_match:
        title = tib_match.group(1).strip().rstrip('.')
        if title and len(title) > 2:
            result["tibetan_title"] = title

    return result


def load_existing_lancaster():
    """Load existing Lancaster data to check what we already have."""
    if not EXISTING_LANCASTER.exists():
        return {}
    with open(EXISTING_LANCASTER) as f:
        return json.load(f)


def main():
    # Load existing data for comparison
    existing = load_existing_lancaster()
    existing_taisho_with_toh = set()
    for t_id, data in existing.items():
        if data.get("tohoku") and len(data["tohoku"]) > 0:
            existing_taisho_with_toh.add(t_id)
    print(f"Existing Lancaster entries with Tohoku: {len(existing_taisho_with_toh)}")

    # Step 1: Fetch and parse the Tohoku index
    print(f"\nFetching Tohoku index from {TOHOKU_INDEX_URL}...")
    html = fetch_url(TOHOKU_INDEX_URL)
    if not html:
        print("ERROR: Could not fetch Tohoku index")
        sys.exit(1)

    toh_to_k = parse_tohoku_index(html)
    print(f"  Found {len(toh_to_k)} Tohoku entries with K-number links")

    # Collect unique K files to fetch
    all_k_files = set()
    for data in toh_to_k.values():
        all_k_files.update(data["k_files"])
    print(f"  Total unique K-number pages to fetch: {len(all_k_files)}")

    # Step 2: Fetch each K-number detail page
    k_details = {}
    total = len(all_k_files)
    for i, k_file in enumerate(sorted(all_k_files)):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  Fetching K pages: {i + 1}/{total}...")
        url = K_DETAIL_BASE + k_file
        html = fetch_url(url)
        if html:
            k_details[k_file] = parse_k_detail_page(html, k_file)
        time.sleep(REQUEST_DELAY)

    print(f"  Successfully fetched {len(k_details)}/{total} K pages")

    # Step 3: Build Toh→Taisho mapping
    toh_taisho = {}
    new_mappings = 0

    for toh_num, k_data in sorted(toh_to_k.items()):
        entry = {
            "tohoku": toh_num,
            "k_numbers": k_data["k_numbers"],
            "taisho": [],
            "nanjio": [],
            "otani": [],
            "sanskrit_title": None,
            "tibetan_title": None,
            "chinese_title": None,
        }

        for k_file in k_data["k_files"]:
            if k_file in k_details:
                kd = k_details[k_file]
                for t in kd["taisho"]:
                    if t not in entry["taisho"]:
                        entry["taisho"].append(t)
                for nj in kd["nanjio"]:
                    if nj not in entry["nanjio"]:
                        entry["nanjio"].append(nj)
                for o in kd["otani"]:
                    if o not in entry["otani"]:
                        entry["otani"].append(o)
                if kd["sanskrit_title"] and not entry["sanskrit_title"]:
                    entry["sanskrit_title"] = kd["sanskrit_title"]
                if kd["tibetan_title"] and not entry["tibetan_title"]:
                    entry["tibetan_title"] = kd["tibetan_title"]
                if kd["chinese_title"] and not entry["chinese_title"]:
                    entry["chinese_title"] = kd["chinese_title"]

        toh_key = f"Toh {toh_num}"
        toh_taisho[toh_key] = entry

        # Check if this is a new mapping
        for t_id in entry["taisho"]:
            if t_id not in existing_taisho_with_toh:
                new_mappings += 1

    # Summary stats
    with_taisho = sum(1 for e in toh_taisho.values() if e["taisho"])
    without_taisho = sum(1 for e in toh_taisho.values() if not e["taisho"])

    print(f"\n=== Results ===")
    print(f"Total Tohoku entries: {len(toh_taisho)}")
    print(f"  With Taisho mapping: {with_taisho}")
    print(f"  Without Taisho mapping: {without_taisho}")
    print(f"  New Taisho↔Toh mappings (not in existing Lancaster): {new_mappings}")

    output = {
        "summary": {
            "total_tohoku_entries": len(toh_taisho),
            "with_taisho": with_taisho,
            "without_taisho": without_taisho,
            "new_mappings": new_mappings,
            "k_pages_fetched": len(k_details),
        },
        "entries": toh_taisho,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
