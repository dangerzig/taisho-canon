#!/usr/bin/env python3
"""Extract Taisho-to-Tibetan cross-references from the Digital Dictionary
of Buddhism (DDB) public index pages.

Data sources (all at buddhism-dict.net, cached via Wayback Machine):

1. Taisho / SAT Availability Table
   URL: http://www.buddhism-dict.net/ddb/indexes/taisho-ddb.html
   Content: ~2,950 Taisho texts with Chinese titles, DDB entry IDs,
   and links to SAT. No Tohoku numbers on this page.

2. Tibetan Texts Index (214 entries)
   URL: http://www.buddhism-dict.net/ddb/indexes/text-bo.html
   Content: Tibetan text titles mapped to Chinese text titles (via DDB
   entry links). No explicit Taisho or Tohoku numbers.

3. Sanskrit Texts Index
   URL: http://www.buddhism-dict.net/ddb/indexes/text-sa.html
   Content: Sanskrit text titles mapped to Chinese text titles.

Strategy:
  - Parse the Taisho table to build a Chinese-title-to-T-number index.
  - Parse the Tibetan texts index for Tibetan-to-Chinese title mappings.
  - Cross-reference via shared Chinese titles (and DDB entry IDs) to get
    DDB-sourced Taisho-to-Tibetan-text correspondences.

Limitations:
  - Individual DDB entries contain Tohoku numbers (To.####) in their
    metadata, but accessing individual entries requires authentication
    (guest: 20 searches/day; unlimited requires contribution or paid
    subscription). This script does NOT attempt authenticated scraping.
  - The public index pages do not contain Tohoku numbers.
  - The Tibetan texts index has only 214 entries (vs. 2,950 in the
    Taisho table), so the cross-reference yield is modest.

Output: results/ddb_taisho_tibetan.json

References:
  - DDB intro: http://www.buddhism-dict.net/ddb/ddb-intro.html
  - DDB TEI paper: http://www.buddhism-dict.net/ddb/papers/201207-ddb_tei.html
  - Muller 2008: http://www.acmuller.net/articles/2008-03-nichibunken-ddb.html
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "results" / "ddb_taisho_tibetan.json"

# Wayback Machine URLs for the DDB index pages.
# The live site (buddhism-dict.net) frequently times out; Wayback caches
# are more reliable for bulk download.
# NOTE: Use the "id_/" URL format to get raw original content without
# the Wayback Machine JavaScript wrapper (which breaks urlopen).
TAISHO_TABLE_URL = (
    "https://web.archive.org/web/20250416011101id_/"
    "http://www.buddhism-dict.net/ddb/indexes/taisho-ddb.html"
)
TIBETAN_INDEX_URL = (
    "https://web.archive.org/web/20250507081805id_/"
    "http://www.buddhism-dict.net/ddb/indexes/text-bo.html"
)
SANSKRIT_INDEX_URL = (
    "https://web.archive.org/web/20250929031411id_/"
    "http://www.buddhism-dict.net/ddb/indexes/text-sa.html"
)

# Fallback: live DDB site (often slow/unreachable)
TAISHO_TABLE_LIVE = (
    "http://www.buddhism-dict.net/ddb/indexes/taisho-ddb.html"
)
TIBETAN_INDEX_LIVE = (
    "http://www.buddhism-dict.net/ddb/indexes/text-bo.html"
)

REQUEST_DELAY = 1.0
USER_AGENT = "TaishoCanonResearch/1.0 (academic research)"


def fetch_url(url, retries=3, timeout=60):
    """Fetch a URL with retries."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for {url[:80]}...: {e}")
            if attempt < retries - 1:
                time.sleep(REQUEST_DELAY * (attempt + 1))
            else:
                return None
    return None


def normalize_ddb_id(raw_id):
    """Extract a normalized DDB entry ID from an xpr-ddb.pl URL parameter.

    Example: "59.xml+id('b5927-822c-82e5-6ce2-7f85-871c-591a-7d93')"
    -> "59.xml+id(b5927-822c-82e5-6ce2-7f85-871c-591a-7d93)"
    """
    # Strip wayback machine prefix if present
    raw_id = re.sub(r".*/xpr-ddb\.pl\?", "", raw_id)
    # Remove quotes around id
    raw_id = raw_id.replace("'", "").replace('"', "")
    return raw_id


def parse_taisho_table(html):
    """Parse the DDB Taisho / SAT Availability Table.

    Returns two dicts:
      t_to_titles: {t_num: [chinese_titles]}
      title_to_t: {chinese_title: [t_nums]}
      ddb_id_to_t: {ddb_entry_id: t_num}
    """
    t_to_titles = {}
    title_to_t = {}
    ddb_id_to_t = {}

    # Split into table rows
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)

    for row in rows:
        # Extract T number from SAT link: >T NNN</a> or >T\nNNN</a>
        t_match = re.search(r">T\s*\n?\s*(\d+)\s*</a>", row)
        if not t_match:
            continue
        t_num = int(t_match.group(1))

        # Extract Chinese titles from all links in the first <td>
        # DDB links (blue): class="ddb"
        # K-canon links (green): class="kcanon"
        # Plain links (no DDB entry yet): search-ddb4.pl
        titles = set()

        # DDB entry links with IDs
        for m in re.finditer(
            r'href="[^"]*xpr-ddb\.pl\?([^"]+)"[^>]*>([^<]+)</a>', row
        ):
            ddb_id = normalize_ddb_id(m.group(1))
            title = m.group(2).strip()
            titles.add(title)
            ddb_id_to_t[ddb_id] = t_num

        # Non-DDB links (search links)
        for m in re.finditer(
            r'href="[^"]*search-ddb4\.pl\?[^"]*"[^>]*>([^<]+)</a>', row
        ):
            titles.add(m.group(1).strip())

        # Titles in plain spans (alternate names)
        for m in re.finditer(
            r'<span[^>]*>([^<]+)</span>', row
        ):
            text = m.group(1).strip()
            # Filter out style directives
            if text and not text.startswith("font") and len(text) > 1:
                # Only CJK titles
                if any("\u4e00" <= ch <= "\u9fff" for ch in text):
                    titles.add(text)

        title_list = sorted(titles)
        t_to_titles[t_num] = title_list

        for title in title_list:
            if title not in title_to_t:
                title_to_t[title] = []
            title_to_t[title].append(t_num)

    return t_to_titles, title_to_t, ddb_id_to_t


def parse_tibetan_index(html):
    """Parse the DDB Tibetan Texts Index.

    Returns a list of dicts:
      [{tibetan_title, chinese_titles, ddb_ids}]
    """
    entries = []

    # Strip the Wayback Machine toolbar (everything before <body>)
    body_start = html.find("<body")
    if body_start >= 0:
        html = html[body_start:]

    # Each entry is a <p> with Tibetan title text followed by <a> link(s)
    # to Chinese titles in the DDB.
    for m in re.finditer(
        r"<p>([^<]+?)\s*(<a\s[^>]*>.*?)</p>", html, re.DOTALL
    ):
        tibetan = m.group(1).strip()
        link_html = m.group(2)

        # Skip if this looks like navigation/metadata
        if not tibetan or tibetan.startswith("Digital Dictionary"):
            continue

        # Extract all Chinese titles and DDB IDs from links
        chinese_titles = []
        ddb_ids = []
        for link_m in re.finditer(
            r'<a\s+href="([^"]*)"[^>]*>([^<]+)</a>', link_html
        ):
            href = link_m.group(1)
            title = link_m.group(2).strip()
            chinese_titles.append(title)
            # Extract DDB entry ID if present
            id_m = re.search(r"xpr-ddb\.pl\?(.+)", href)
            if id_m:
                ddb_ids.append(normalize_ddb_id(id_m.group(1)))

        if chinese_titles:
            entries.append(
                {
                    "tibetan_title": tibetan,
                    "chinese_titles": chinese_titles,
                    "ddb_ids": ddb_ids,
                }
            )

    return entries


def parse_sanskrit_index(html):
    """Parse the DDB Sanskrit Texts Index.

    Returns a list of dicts:
      [{sanskrit_title, chinese_titles, ddb_ids}]
    """
    entries = []

    body_start = html.find("<body")
    if body_start >= 0:
        html = html[body_start:]

    for m in re.finditer(
        r"<p>([^<]+?)\s*(<a\s[^>]*>.*?)</p>", html, re.DOTALL
    ):
        sanskrit = m.group(1).strip()
        link_html = m.group(2)

        if not sanskrit or sanskrit.startswith("Digital Dictionary"):
            continue

        chinese_titles = []
        ddb_ids = []
        # Handle both single and double-quoted href attributes
        for link_m in re.finditer(
            r"<a\s+href=[\"']([^\"']*)[\"'][^>]*>([^<]+)</a>", link_html
        ):
            href = link_m.group(1)
            title = link_m.group(2).strip()
            chinese_titles.append(title)
            id_m = re.search(r"xpr-ddb\.pl\?(.+)", href)
            if id_m:
                ddb_ids.append(normalize_ddb_id(id_m.group(1)))

        if chinese_titles:
            entries.append(
                {
                    "sanskrit_title": sanskrit,
                    "chinese_titles": chinese_titles,
                    "ddb_ids": ddb_ids,
                }
            )

    return entries


def normalize_chinese(title):
    """Normalize a Chinese title for fuzzy matching.

    Handles common variant characters and honorific prefixes:
    - Strips 佛說 (spoken by Buddha) prefix
    - Normalizes traditional/simplified variants used inconsistently
    """
    # Common honorific prefixes to strip for matching
    for prefix in ["佛說", "佛爲", "佛爲首迦長者說"]:
        if title.startswith(prefix) and len(title) > len(prefix):
            title = title[len(prefix):]
    return title


def cross_reference(t_to_titles, title_to_t, ddb_id_to_t, tibetan_entries):
    """Cross-reference Tibetan titles to Taisho numbers via Chinese titles
    and DDB entry IDs.

    Returns a list of matched entries:
      [{taisho, chinese_title, tibetan_title, match_method}]
    """
    # Build normalized title index for fuzzy matching
    norm_title_to_t = {}
    for title, t_nums in title_to_t.items():
        norm = normalize_chinese(title)
        if norm not in norm_title_to_t:
            norm_title_to_t[norm] = []
        norm_title_to_t[norm].extend(t_nums)

    # Build reverse index: all Taisho titles by their normalized forms
    all_taisho_titles = {}
    for t_num, titles in t_to_titles.items():
        for t in titles:
            all_taisho_titles[t] = t_num

    matches = []
    unmatched = []

    for entry in tibetan_entries:
        found = False
        for i, cn_title in enumerate(entry["chinese_titles"]):
            # Method 1: direct title match
            if cn_title in title_to_t:
                for t_num in title_to_t[cn_title]:
                    matches.append(
                        {
                            "taisho": t_num,
                            "chinese_title": cn_title,
                            "tibetan_title": entry["tibetan_title"],
                            "match_method": "title",
                        }
                    )
                found = True
            # Method 2: DDB entry ID match
            elif i < len(entry["ddb_ids"]):
                ddb_id = entry["ddb_ids"][i]
                if ddb_id in ddb_id_to_t:
                    t_num = ddb_id_to_t[ddb_id]
                    matches.append(
                        {
                            "taisho": t_num,
                            "chinese_title": cn_title,
                            "tibetan_title": entry["tibetan_title"],
                            "match_method": "ddb_id",
                        }
                    )
                    found = True

        if not found:
            # Method 3: DDB ID matching for any remaining IDs
            for ddb_id in entry["ddb_ids"]:
                if ddb_id in ddb_id_to_t:
                    t_num = ddb_id_to_t[ddb_id]
                    cn = entry["chinese_titles"][0] if entry["chinese_titles"] else ""
                    matches.append(
                        {
                            "taisho": t_num,
                            "chinese_title": cn,
                            "tibetan_title": entry["tibetan_title"],
                            "match_method": "ddb_id_fallback",
                        }
                    )
                    found = True

        if not found:
            # Method 4: normalized title matching (strip 佛說 etc.)
            for cn_title in entry["chinese_titles"]:
                norm = normalize_chinese(cn_title)
                if norm in norm_title_to_t:
                    for t_num in norm_title_to_t[norm]:
                        matches.append(
                            {
                                "taisho": t_num,
                                "chinese_title": cn_title,
                                "tibetan_title": entry["tibetan_title"],
                                "match_method": "normalized_title",
                            }
                        )
                    found = True
                # Also check if the Tibetan entry's Chinese title is a
                # substring of a Taisho title or vice versa (for variant
                # title forms like 經 vs 經典)
                elif not found and len(cn_title) >= 3:
                    for taisho_title, t_num in all_taisho_titles.items():
                        if (
                            cn_title in taisho_title
                            or taisho_title in cn_title
                        ) and abs(len(cn_title) - len(taisho_title)) <= 2:
                            matches.append(
                                {
                                    "taisho": t_num,
                                    "chinese_title": cn_title,
                                    "tibetan_title": entry["tibetan_title"],
                                    "match_method": "substring",
                                }
                            )
                            found = True

        if not found:
            unmatched.append(entry)

    return matches, unmatched


def format_taisho_id(t_num):
    """Format a Taisho number as a standard CBETA-style ID.

    T1 -> T01n0001, T250 -> T08n0250, etc.

    We cannot determine the volume number from the T number alone, so
    we use a simplified format: T####.
    """
    return f"T{t_num}"


def main():
    print("=" * 60)
    print("DDB Cross-Reference Extraction")
    print("=" * 60)

    # Step 1: Fetch Taisho table
    print("\n[1/3] Fetching DDB Taisho / SAT Availability Table...")
    taisho_html = fetch_url(TAISHO_TABLE_URL, timeout=120)
    if not taisho_html:
        print("  Wayback failed, trying live site...")
        taisho_html = fetch_url(TAISHO_TABLE_LIVE, timeout=120)
    if not taisho_html:
        print("ERROR: Could not fetch Taisho table. Exiting.")
        sys.exit(1)

    t_to_titles, title_to_t, ddb_id_to_t = parse_taisho_table(taisho_html)
    print(f"  Parsed {len(t_to_titles)} Taisho entries")
    print(f"  {len(title_to_t)} unique Chinese titles")
    print(f"  {len(ddb_id_to_t)} DDB entry ID mappings")

    # Step 2: Fetch Tibetan texts index
    print("\n[2/3] Fetching DDB Tibetan Texts Index...")
    time.sleep(REQUEST_DELAY)
    tibetan_html = fetch_url(TIBETAN_INDEX_URL, timeout=60)
    if not tibetan_html:
        print("  Wayback failed, trying live site...")
        tibetan_html = fetch_url(TIBETAN_INDEX_LIVE, timeout=60)
    if not tibetan_html:
        print("WARNING: Could not fetch Tibetan index. Proceeding without.")
        tibetan_entries = []
    else:
        tibetan_entries = parse_tibetan_index(tibetan_html)
        print(f"  Parsed {len(tibetan_entries)} Tibetan text entries")

    # Step 3: Fetch Sanskrit texts index (optional, for enrichment)
    print("\n[3/3] Fetching DDB Sanskrit Texts Index...")
    time.sleep(REQUEST_DELAY)
    sanskrit_html = fetch_url(SANSKRIT_INDEX_URL, timeout=60)
    if sanskrit_html:
        sanskrit_entries = parse_sanskrit_index(sanskrit_html)
        print(f"  Parsed {len(sanskrit_entries)} Sanskrit text entries")
    else:
        print("  Could not fetch Sanskrit index. Continuing without.")
        sanskrit_entries = []

    # Step 4: Cross-reference
    print("\n--- Cross-referencing ---")
    matches, unmatched = cross_reference(
        t_to_titles, title_to_t, ddb_id_to_t, tibetan_entries
    )

    # Deduplicate matches by (taisho, tibetan_title)
    seen = set()
    unique_matches = []
    for m in matches:
        key = (m["taisho"], m["tibetan_title"])
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)

    # Build output entries
    output_entries = {}
    for m in unique_matches:
        t_num = m["taisho"]
        key = f"T{t_num}"
        if key not in output_entries:
            output_entries[key] = {
                "taisho": format_taisho_id(t_num),
                "taisho_num": t_num,
                "chinese_titles": sorted(t_to_titles.get(t_num, [])),
                "tibetan_titles": [],
                "match_methods": [],
            }
        output_entries[key]["tibetan_titles"].append(m["tibetan_title"])
        if m["match_method"] not in output_entries[key]["match_methods"]:
            output_entries[key]["match_methods"].append(m["match_method"])

    # Summary statistics
    unique_taisho = set(m["taisho"] for m in unique_matches)

    print(f"\n=== Results ===")
    print(f"Total Taisho texts in DDB table: {len(t_to_titles)}")
    print(f"  With DDB entries (blue links): "
          f"{sum(1 for ts in t_to_titles if any(d for d, t in ddb_id_to_t.items() if t == ts))}")
    print(f"Tibetan texts in DDB index: {len(tibetan_entries)}")
    print(f"Sanskrit texts in DDB index: {len(sanskrit_entries)}")
    print(f"Cross-referenced pairs (Taisho with Tibetan): {len(unique_matches)}")
    print(f"Unique Taisho texts matched: {len(unique_taisho)}")
    print(f"Unmatched Tibetan entries: {len(unmatched)}")

    # Show match method breakdown
    method_counts = {}
    for m in unique_matches:
        method_counts[m["match_method"]] = (
            method_counts.get(m["match_method"], 0) + 1
        )
    for method, count in sorted(method_counts.items()):
        print(f"  Match method '{method}': {count}")

    # Build final output
    output = {
        "source": "ddb",
        "source_name": "Digital Dictionary of Buddhism",
        "source_url": "http://www.buddhism-dict.net/ddb/",
        "description": (
            "Cross-references extracted from DDB public index pages: "
            "the Taisho/SAT Availability Table (mapping Chinese titles "
            "to T numbers) and the Tibetan Texts Index (mapping Tibetan "
            "titles to Chinese titles). Cross-referenced via shared "
            "Chinese titles and DDB entry IDs."
        ),
        "limitations": (
            "Individual DDB entries contain Tohoku numbers (To.####) "
            "in their metadata, but accessing entries requires "
            "authentication (guest: 20 lookups/day; unlimited requires "
            "contribution or paid subscription). This extraction uses "
            "only publicly available index pages, which do not contain "
            "Tohoku numbers. To get Tohoku cross-references, one would "
            "need to scrape individual DDB entries with credentials."
        ),
        "data_dates": {
            "taisho_table": "2018-10-11 (per page header)",
            "tibetan_index": "2019-01-03 (per page header)",
        },
        "summary": {
            "taisho_texts_in_ddb": len(t_to_titles),
            "tibetan_texts_in_ddb": len(tibetan_entries),
            "sanskrit_texts_in_ddb": len(sanskrit_entries),
            "cross_referenced_pairs": len(unique_matches),
            "unique_taisho_matched": len(unique_taisho),
            "unmatched_tibetan": len(unmatched),
        },
        "total_pairs": len(unique_matches),
        "entries": output_entries,
        "unmatched_tibetan": [
            {
                "tibetan_title": e["tibetan_title"],
                "chinese_titles": e["chinese_titles"],
            }
            for e in unmatched
        ],
    }

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {OUTPUT_PATH}")

    # Show sample entries
    print("\n--- Sample entries ---")
    for key in sorted(output_entries.keys(), key=lambda k: output_entries[k]["taisho_num"])[:10]:
        e = output_entries[key]
        cn = e["chinese_titles"][0] if e["chinese_titles"] else "?"
        tib = e["tibetan_titles"][0][:50] if e["tibetan_titles"] else "?"
        print(f"  {e['taisho']:>6}  {cn}  ->  {tib}")


if __name__ == "__main__":
    main()
