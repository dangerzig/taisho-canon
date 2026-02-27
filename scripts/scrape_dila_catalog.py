#!/usr/bin/env python3
"""Scrape DILA Authority Database of Buddhist Tripitaka Catalogues for
Taisho-to-Tohoku cross-references.

DILA (Dharma Drum Institute of Liberal Arts) maintains a catalog database at:
  https://authority.dila.edu.tw/catalog/

The database covers 22 Buddhist canon editions with 33,700+ Chinese and 4,569
Tibetan catalog entries. The Taisho catalog entries contain cross-references
to the Tohoku (Derge) catalog from the Lancaster/Goryeo catalog data embedded
in each entry's detail view.

Data architecture:
  - Static JSON at GitHub (DILA-edu/Authority-Databases/authority_catalog/json/)
    provides basic metadata (title, author, date, etc.) but NO cross-references.
  - The web interface at search.php renders additional data from the relational
    database, including Goryeo (Lancaster) catalog cross-references that contain
    Tohoku and Otani numbers.
  - Cross-references appear in two labeled fields:
    * 東北大學藏經目錄 (Tohoku University Catalog): "To. 34, 352"
    * 西藏大藏經甘殊爾勘同目錄 (Otani Catalog): "O. 750, 1021"
  - These fields exist only for entries that have Lancaster/Goryeo catalog data,
    typically the main Taisho canon (T0001-T2184).

This script:
  1. Downloads the static T.json from GitHub for the full ID list
  2. Scrapes each entry's detail page from search.php
  3. Extracts Tohoku and Otani numbers
  4. Saves results with progress tracking and resume capability

Output: results/dila_taisho_tibetan.json

Rate limiting: 0.5s delay between requests to be respectful.
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_PATH = RESULTS_DIR / "dila_taisho_tibetan.json"
PROGRESS_PATH = RESULTS_DIR / ".dila_scrape_progress.json"

# DILA endpoints
SEARCH_URL = "https://authority.dila.edu.tw/catalog/search.php"
GITHUB_JSON_URL = (
    "https://raw.githubusercontent.com/DILA-edu/Authority-Databases/"
    "master/authority_catalog/json/T.json"
)

REQUEST_DELAY = 0.5  # seconds between requests
USER_AGENT = "TaishoCanonResearch/1.0 (academic research; djz@shmonk.com)"


def fetch_url(url, retries=3):
    """Fetch a URL with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                wait = REQUEST_DELAY * (2 ** attempt)
                print(f"    Retry {attempt + 1} after {wait:.1f}s: {e}")
                time.sleep(wait)
            else:
                print(f"    Failed after {retries} attempts: {e}")
                return None
    return None


def get_taisho_ids():
    """Get all Taisho text IDs from the DILA GitHub data.

    Downloads T.json from the Authority-Databases repository.
    Falls back to a locally cached copy if available.
    """
    cache_path = BASE_DIR / "data" / "cache" / "dila_T.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Try cached copy first
    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        print(f"  Loaded {len(data)} Taisho IDs from cache")
        return data

    # Download from GitHub
    print(f"  Downloading T.json from GitHub...")
    html = fetch_url(GITHUB_JSON_URL)
    if html is None:
        print("  ERROR: Could not download T.json from GitHub")
        sys.exit(1)

    data = json.loads(html)
    # Cache for future runs
    with open(cache_path, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"  Downloaded and cached {len(data)} Taisho IDs")
    return data


def parse_tohoku_field(text):
    """Parse Tohoku numbers from a field value like 'To. 34, 352'.

    Handles various formats:
      - "To. 34"
      - "To. 34, 352"
      - "To. 45-93" (ranges)
      - "To. 21, 531"
      - "To. 289, 290, 291, 297, 339. (313, 338, 617, 974)"
        (parenthesized numbers are tentative/secondary refs)
    """
    if not text:
        return [], []

    text = text.strip()

    # Split into primary (before parens) and secondary (in parens)
    primary_refs = []
    secondary_refs = []

    # Extract parenthesized secondary refs first
    paren_match = re.findall(r'\(([^)]+)\)', text)
    for pm in paren_match:
        for num in re.findall(r'\d+', pm):
            secondary_refs.append(f"Toh {num}")

    # Remove parenthesized parts for primary parsing
    primary_text = re.sub(r'\([^)]*\)', '', text)

    # Remove Lancaster footnote markers like "n3", "n1" before numbers
    # These appear as "To. 555, n3 556" meaning footnote 3 applies to 556
    primary_text = re.sub(r'\bn\d+\b', '', primary_text)

    # Handle ranges like "To. 45-93"
    range_matches = re.findall(r'(\d+)\s*-\s*(\d+)', primary_text)
    range_nums = set()
    for start, end in range_matches:
        s, e = int(start), int(end)
        if e - s < 200:  # sanity check
            for n in range(s, e + 1):
                primary_refs.append(f"Toh {n}")
                range_nums.add(start)
                range_nums.add(end)

    # Extract individual numbers (skip those already in ranges)
    for num in re.findall(r'\d+', primary_text):
        if num not in range_nums:
            toh = f"Toh {num}"
            if toh not in primary_refs:
                primary_refs.append(toh)

    return primary_refs, secondary_refs


def parse_otani_field(text):
    """Parse Otani numbers from a field value like 'O. 750, 1021'.

    Handles various formats:
      - "O. 750"
      - "O. 750, 1021."
      - "O. 760(5)." (subsection refs)
      - "O. 955, 956, 957, 963, 1006, (599, 979, 1005)."
    """
    if not text:
        return []

    text = text.strip()

    # Skip "see below" type references
    if "see below" in text.lower():
        return []

    refs = []
    # Match O. followed by number, with optional parenthesized subsection
    for m in re.finditer(r'(\d+)(?:\(([^)]+)\))?', text):
        num = m.group(1)
        sub = m.group(2)
        if sub:
            refs.append(f"Otani {num}({sub})")
        else:
            refs.append(f"Otani {num}")

    return refs


def parse_entry_html(html, taisho_id):
    """Parse a DILA catalog search result page for cross-references.

    Extracts:
      - Tohoku numbers from 東北大學藏經目錄
      - Otani numbers from 西藏大藏經甘殊爾勘同目錄
      - Authority ID (CA number)
      - Whether Lancaster/Goryeo data is present
      - Title (for verification)
    """
    if not html:
        return None

    result = {
        "taisho": taisho_id,
        "authority_id": None,
        "title": None,
        "has_goryeo": False,
        "tohoku_raw": None,
        "otani_raw": None,
        "tohoku": [],
        "tohoku_secondary": [],
        "otani": [],
    }

    # Authority ID
    aid_match = re.search(r'規範碼：</span>(CA\d+)', html)
    if aid_match:
        result["authority_id"] = aid_match.group(1)

    # Title
    title_match = re.search(r'經名：</span>(.+?)</div>', html)
    if title_match:
        result["title"] = title_match.group(1).strip()

    # Check for Goryeo/Lancaster data
    result["has_goryeo"] = "高麗藏經目錄" in html

    # Extract Tohoku field: 東北大學藏經目錄
    tohoku_match = re.search(
        r'東北大學藏經目錄</div><div>(.*?)</div>', html
    )
    if tohoku_match:
        raw = tohoku_match.group(1).strip()
        result["tohoku_raw"] = raw
        primary, secondary = parse_tohoku_field(raw)
        result["tohoku"] = primary
        result["tohoku_secondary"] = secondary

    # Extract Otani field: 西藏大藏經甘殊爾勘同目錄
    otani_match = re.search(
        r'西藏大藏經甘殊爾勘同目錄</div><div>(.*?)</div>', html
    )
    if otani_match:
        raw = otani_match.group(1).strip()
        result["otani_raw"] = raw
        result["otani"] = parse_otani_field(raw)

    # Also check the "其他目錄" (Other catalogs) field as fallback
    # This contains all cross-refs in one line: "Nj. ###; To. ###; O. ###"
    if not result["tohoku"] and not result["otani"]:
        other_match = re.search(
            r'其他目錄</div><div>(.*?)</div>', html
        )
        if other_match:
            raw = other_match.group(1)
            # Try to extract To. and O. from the combined field
            to_match = re.search(r'To\.\s*([\d,\s.\-()]+?)(?:;|$)', raw)
            if to_match:
                result["tohoku_raw"] = f"To. {to_match.group(1).strip()}"
                primary, secondary = parse_tohoku_field(to_match.group(1))
                result["tohoku"] = primary
                result["tohoku_secondary"] = secondary

            o_match = re.search(r'O\.\s*([\d,\s.()]+?)(?:;|$)', raw)
            if o_match:
                result["otani_raw"] = f"O. {o_match.group(1).strip()}"
                result["otani"] = parse_otani_field(o_match.group(1))

    # Skip entries with no Tibetan data at all
    if not result["tohoku"] and not result["tohoku_secondary"]:
        return None

    return result


def taisho_to_cbeta(taisho_id, vol=None):
    """Convert a bare Taisho ID (T0001) to CBETA format (T01n0001).

    Uses volume info from the DILA JSON data if available.
    """
    m = re.match(r'T(\d+)([a-zA-Z]*)', taisho_id)
    if not m:
        return taisho_id
    num = m.group(1)
    suffix = m.group(2)

    if vol and vol.startswith("T"):
        vol_num = vol[1:]  # "T01" -> "01"
        return f"T{vol_num}n{num.zfill(4)}{suffix}"

    # Fallback: cannot determine volume
    return taisho_id


def load_progress():
    """Load scraping progress for resume capability."""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH) as f:
            return json.load(f)
    return {"completed": [], "results": {}}


def save_progress(progress):
    """Save scraping progress."""
    with open(PROGRESS_PATH, "w") as f:
        json.dump(progress, f, ensure_ascii=False)


def main():
    print("=" * 60)
    print("DILA Authority Database Catalog Scraper")
    print("Extracting Taisho-to-Tohoku cross-references")
    print("=" * 60)

    # Step 1: Get all Taisho IDs from GitHub JSON
    print("\n[1] Loading Taisho catalog IDs from DILA GitHub...")
    taisho_data = get_taisho_ids()
    all_ids = sorted(taisho_data.keys())
    print(f"  Total Taisho entries: {len(all_ids)}")

    # Step 2: Load progress for resume
    progress = load_progress()
    completed = set(progress["completed"])
    results = progress["results"]
    remaining = [tid for tid in all_ids if tid not in completed]

    if completed:
        print(f"\n[2] Resuming from previous run:")
        print(f"  Already completed: {len(completed)}")
        print(f"  Remaining: {len(remaining)}")
    else:
        print(f"\n[2] Starting fresh scrape of {len(all_ids)} entries")

    # Step 3: Scrape each entry
    print(f"\n[3] Scraping DILA catalog search pages...")
    print(f"  URL: {SEARCH_URL}?code=XXXX")
    print(f"  Delay: {REQUEST_DELAY}s between requests")
    print()

    entries_with_tohoku = len([r for r in results.values() if r.get("tohoku")])
    consecutive_errors = 0
    start_time = time.time()

    for i, taisho_id in enumerate(remaining):
        # Progress report every 50 entries
        if i % 50 == 0 and i > 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(remaining) - i) / rate if rate > 0 else 0
            print(
                f"  Progress: {len(completed) + i}/{len(all_ids)} "
                f"({entries_with_tohoku} with Tohoku) "
                f"[{rate:.1f}/s, ETA {eta/60:.0f}m]"
            )

        url = f"{SEARCH_URL}?code={taisho_id}"
        html = fetch_url(url)

        if html is None:
            consecutive_errors += 1
            if consecutive_errors > 10:
                print(f"\n  WARNING: 10 consecutive errors, pausing 30s...")
                time.sleep(30)
                consecutive_errors = 0
            completed.add(taisho_id)
            continue

        consecutive_errors = 0
        entry = parse_entry_html(html, taisho_id)

        if entry:
            # Add volume and CBETA ID info from the static JSON
            vol = taisho_data.get(taisho_id, {}).get("vol")
            entry["cbeta_id"] = taisho_to_cbeta(taisho_id, vol)
            entry["vol"] = vol
            results[taisho_id] = entry
            entries_with_tohoku += 1

        completed.add(taisho_id)

        # Save progress every 100 entries
        if (len(completed) + i) % 100 == 0:
            progress["completed"] = list(completed)
            progress["results"] = results
            save_progress(progress)

        time.sleep(REQUEST_DELAY)

    # Final save
    progress["completed"] = list(completed)
    progress["results"] = results
    save_progress(progress)

    # Step 4: Build output
    print(f"\n[4] Building output...")

    # Convert results to the requested output format
    entries_output = {}
    all_tohoku = set()
    all_taisho = set()

    for taisho_id, entry in sorted(results.items()):
        cbeta_id = entry.get("cbeta_id", taisho_id)
        all_taisho.add(cbeta_id)

        for toh in entry.get("tohoku", []):
            all_tohoku.add(toh)
            toh_num = re.search(r'\d+', toh).group()
            key = f"{cbeta_id}_Toh_{toh_num}"
            entries_output[key] = {
                "taisho": cbeta_id,
                "tohoku": toh,
                "authority_id": entry.get("authority_id"),
                "title": entry.get("title"),
                "tohoku_raw": entry.get("tohoku_raw"),
                "otani": entry.get("otani", []),
                "status": "primary",
            }

        # Also include secondary (parenthesized) Tohoku refs
        for toh in entry.get("tohoku_secondary", []):
            all_tohoku.add(toh)
            toh_num = re.search(r'\d+', toh).group()
            key = f"{cbeta_id}_Toh_{toh_num}"
            if key not in entries_output:
                entries_output[key] = {
                    "taisho": cbeta_id,
                    "tohoku": toh,
                    "authority_id": entry.get("authority_id"),
                    "title": entry.get("title"),
                    "tohoku_raw": entry.get("tohoku_raw"),
                    "otani": entry.get("otani", []),
                    "status": "secondary",
                }

    output = {
        "source": "dila_catalog",
        "description": (
            "Taisho-to-Tohoku cross-references extracted from the DILA "
            "Authority Database of Buddhist Tripitaka Catalogues "
            "(authority.dila.edu.tw/catalog/). Cross-references originate "
            "from the Lancaster/Goryeo catalog data embedded in each entry."
        ),
        "url": "https://authority.dila.edu.tw/catalog/",
        "github": "https://github.com/DILA-edu/Authority-Databases",
        "date_scraped": time.strftime("%Y-%m-%d"),
        "total_pairs": len(entries_output),
        "unique_taisho": len(all_taisho),
        "unique_tohoku": len(all_tohoku),
        "total_taisho_queried": len(all_ids),
        "taisho_with_tibetan": len(results),
        "entries": entries_output,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Step 5: Print summary
    print(f"\n{'=' * 60}")
    print(f"RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total Taisho entries queried: {len(all_ids)}")
    print(f"  Entries with Tohoku data:     {len(results)}")
    print(f"  Total Taisho-Tohoku pairs:    {len(entries_output)}")
    print(f"  Unique Taisho texts:          {len(all_taisho)}")
    print(f"  Unique Tohoku numbers:        {len(all_tohoku)}")
    primary = sum(1 for e in entries_output.values() if e["status"] == "primary")
    secondary = sum(1 for e in entries_output.values() if e["status"] == "secondary")
    print(f"  Primary refs:                 {primary}")
    print(f"  Secondary (tentative) refs:   {secondary}")
    print(f"\n  Output: {OUTPUT_PATH}")

    # Clean up progress file
    if PROGRESS_PATH.exists():
        PROGRESS_PATH.unlink()
        print(f"  Cleaned up progress file")

    print()


if __name__ == "__main__":
    main()
