#!/usr/bin/env python3
"""Scrape ALL Lancaster K-number detail pages from acmuller.net.

The Lancaster Descriptive Catalogue has ~1,521 K-number entries at:
  http://www.acmuller.net/descriptive_catalogue/files/k####.html

Each page contains:
  - Header: K ### (T. ###) (H. ###)  — Taisho & Haeinsa numbers
  - (i) Sanskrit title
  - (ii) Tibetan title
  - (iii) Chinese title + romanization
  - (iv) Cross-references: Nj. ###; To. ###; O. ###; etc.
  - Author/translator info
  - Section/division info

This gives us the COMPLETE K-number catalogue, not just the subset
reachable from the Tohoku index (382) or already in our Lancaster JSON (790).

Output: results/lancaster_full.json
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "results" / "lancaster_full.json"

K_DETAIL_BASE = "http://www.acmuller.net/descriptive_catalogue/files/"
MAX_K = 1525  # Slightly above expected max
REQUEST_DELAY = 0.5  # seconds between requests — be polite to acmuller
USER_AGENT = "TaishoCanonResearch/1.0 (academic research)"


def fetch_url(url, retries=3):
    """Fetch a URL with retries."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(REQUEST_DELAY * 3)
            else:
                return None
    return None


def parse_k_page(html, k_num):
    """Parse a Lancaster K-number detail page.

    Extracts all cross-references and metadata from the structured HTML.
    """
    result = {
        "k_number": k_num,
        "taisho": [],
        "haeinsa": [],
        "tohoku": [],
        "otani": [],
        "nanjio": [],
        "sanskrit_title": None,
        "tibetan_title": None,
        "chinese_title": None,
        "chinese_romanization": None,
        "translator": None,
        "section": None,
    }

    if not html or len(html) < 100:
        return None

    # Check for 404 or empty pages
    if "404" in html[:200] or "Not Found" in html[:200]:
        return None
    # Must contain K-number reference
    if f"K {k_num}" not in html and f"K{k_num}" not in html:
        # Some pages use different formatting
        if "descriptive_catalogue" not in html:
            return None

    # --- Header: K ### (T. ###) (H. ###) ---
    # Taisho numbers from header
    t_matches = re.findall(r'\(T\.\s*([\d,\s]+[a-z]?)\)', html)
    for tm in t_matches:
        for num in re.findall(r'\d+', tm):
            t_id = f"T{int(num)}"
            if t_id not in result["taisho"]:
                result["taisho"].append(t_id)

    # Haeinsa numbers
    h_matches = re.findall(r'\(H\.\s*([\d,\s]+)\)', html)
    for hm in h_matches:
        for num in re.findall(r'\d+', hm):
            result["haeinsa"].append(f"H{int(num)}")

    # --- Strip HTML tags for text extraction ---
    text = re.sub(r'<[^>]+>', '\n', html)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')

    # --- Numbered sections ---
    # (i) Sanskrit/Pali title
    skt_match = re.search(r'\(i\)\s*([^\n]+)', text)
    if skt_match:
        title = skt_match.group(1).strip().rstrip('.')
        if title and len(title) > 2:
            result["sanskrit_title"] = title

    # (ii) Tibetan title
    tib_match = re.search(r'\(ii\)\s*([^\n]+)', text)
    if tib_match:
        title = tib_match.group(1).strip().rstrip('.')
        if title and len(title) > 2:
            result["tibetan_title"] = title

    # (iii) Chinese title + romanization
    zh_match = re.search(r'\(iii\)\s*([^\n]+)', text)
    if zh_match:
        raw = zh_match.group(1).strip().rstrip('.')
        if raw:
            # Chinese characters followed by romanization
            cjk_match = re.match(r'([\u4e00-\u9fff\u3400-\u4dbf]+)\s*(.*)', raw)
            if cjk_match:
                result["chinese_title"] = cjk_match.group(1)
                rom = cjk_match.group(2).strip().rstrip('.')
                if rom:
                    result["chinese_romanization"] = rom
            else:
                result["chinese_title"] = raw

    # (iv) or (4) Cross-references
    xref_match = re.search(r'\((?:iv|4)\)\s*([^\n]+(?:\n[^\n(]*)*)', text)
    if xref_match:
        xref_text = xref_match.group(1)

        # Nanjio
        for nj in re.findall(r'Nj\.\s*(\d+)', xref_text):
            nj_id = f"Nj {nj}"
            if nj_id not in result["nanjio"]:
                result["nanjio"].append(nj_id)

        # Tohoku
        for to in re.findall(r'To\.\s*([\d,\s]+)', xref_text):
            for num in re.findall(r'\d+', to):
                toh_id = f"Toh {num}"
                if toh_id not in result["tohoku"]:
                    result["tohoku"].append(toh_id)

        # Otani
        for o in re.findall(r'O\.\s*(\d+)', xref_text):
            ot_id = f"Otani {o}"
            if ot_id not in result["otani"]:
                result["otani"].append(ot_id)

    # Also check for Tohoku/Otani in broader text (some pages have different format)
    if not result["tohoku"]:
        for to in re.findall(r'To\.\s*([\d,\s]+)', text):
            for num in re.findall(r'\d+', to):
                toh_id = f"Toh {num}"
                if toh_id not in result["tohoku"]:
                    result["tohoku"].append(toh_id)

    if not result["otani"]:
        for o in re.findall(r'O\.\s*(\d+)', text):
            ot_id = f"Otani {o}"
            if ot_id not in result["otani"]:
                result["otani"].append(ot_id)

    # Translator info - look for "Translated by" or similar
    trans_match = re.search(r'(?:Translated|Trans\.?) by\s+([^\n.]+)', text, re.IGNORECASE)
    if trans_match:
        result["translator"] = trans_match.group(1).strip()

    # Skip pages with no useful data at all
    if not result["taisho"] and not result["tohoku"] and not result["chinese_title"]:
        return None

    return result


def main():
    print("Scraping ALL Lancaster K-number detail pages...")
    print(f"URL pattern: {K_DETAIL_BASE}k####.html")
    print(f"Scanning K1 to K{MAX_K}")

    entries = {}
    empty_count = 0
    consecutive_empty = 0

    for k_num in range(1, MAX_K + 1):
        if k_num % 100 == 0 or k_num == 1:
            print(f"  Progress: K{k_num}/{MAX_K} ({len(entries)} entries, {empty_count} empty)")

        url = f"{K_DETAIL_BASE}k{k_num:04d}.html"
        html = fetch_url(url)

        if html is None:
            consecutive_empty += 1
            empty_count += 1
            if consecutive_empty > 50:
                print(f"  50 consecutive failures at K{k_num}, stopping.")
                break
            time.sleep(REQUEST_DELAY)
            continue

        result = parse_k_page(html, k_num)
        if result:
            entries[f"K{k_num}"] = result
            consecutive_empty = 0
        else:
            empty_count += 1
            if "descriptive_catalogue" not in (html or ""):
                consecutive_empty += 1
            else:
                consecutive_empty = 0
            if consecutive_empty > 50:
                print(f"  50 consecutive empty at K{k_num}, stopping.")
                break

        time.sleep(REQUEST_DELAY)

    # Summary
    with_taisho = sum(1 for e in entries.values() if e["taisho"])
    with_tohoku = sum(1 for e in entries.values() if e["tohoku"])
    with_otani = sum(1 for e in entries.values() if e["otani"])
    with_nanjio = sum(1 for e in entries.values() if e["nanjio"])
    with_sanskrit = sum(1 for e in entries.values() if e["sanskrit_title"])

    all_taisho = set()
    all_tohoku = set()
    for e in entries.values():
        all_taisho.update(e["taisho"])
        all_tohoku.update(e["tohoku"])

    print(f"\n=== Results ===")
    print(f"Total K entries: {len(entries)}")
    print(f"  With Taisho:   {with_taisho}")
    print(f"  With Tohoku:   {with_tohoku}")
    print(f"  With Otani:    {with_otani}")
    print(f"  With Nanjio:   {with_nanjio}")
    print(f"  With Sanskrit: {with_sanskrit}")
    print(f"  Unique Taisho: {len(all_taisho)}")
    print(f"  Unique Tohoku: {len(all_tohoku)}")

    output = {
        "summary": {
            "total_entries": len(entries),
            "with_taisho": with_taisho,
            "with_tohoku": with_tohoku,
            "with_otani": with_otani,
            "with_nanjio": with_nanjio,
            "with_sanskrit": with_sanskrit,
            "unique_taisho": len(all_taisho),
            "unique_tohoku": len(all_tohoku),
            "max_k_scanned": MAX_K,
        },
        "entries": entries,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
