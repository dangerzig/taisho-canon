#!/usr/bin/env python3
"""Scrape ALL CBETA Jinglu Tibetan detail pages (4,569 entries).

URL: /cgi-bin/tibet_detail.pl?lang=&id=NNNN (NNNN=0001-4569)

Each page has structured fields:
  - 經碼 (No.): entry number / Tohoku-like number
  - 大正藏: Taisho numbers (linked)
  - 南條文雄: Nanjio number
  - 梵文經名: Sanskrit title
  - 中文經名: Chinese title
  - 藏文經名: Tibetan title (Unicode)
  - 藏語羅馬轉寫經名: Tibetan Wylie transliteration

Output: results/cbeta_jinglu_tibetan.json
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "results" / "cbeta_jinglu_tibetan.json"

BASE_URL = "http://jinglu.cbeta.org/cgi-bin/tibet_detail.pl?lang=&id="
MAX_ID = 4600
REQUEST_DELAY = 0.3
USER_AGENT = "TaishoCanonResearch/1.0 (academic research)"


def fetch_url(url, retries=3):
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


def extract_field(html, field_label):
    """Extract value from CBETA Jinglu HTML: <th>label</th><td>value</td>"""
    pattern = rf"<th[^>]*>{re.escape(field_label)}</th>\s*<td[^>]*>(.*?)</td>"
    match = re.search(pattern, html, re.DOTALL)
    if match:
        raw = match.group(1)
        # Strip HTML tags but keep text
        text = re.sub(r'<[^>]+>', '', raw)
        text = text.replace('&nbsp;', '').strip()
        return text if text else None
    return None


def extract_taisho_links(html):
    """Extract Taisho numbers from the 大正藏 field, which contains links.

    Format: <a href='...goto.pl?book=T&sutra=1444'>1444</a>,<a ...>1445</a>
    """
    pattern = r"<th[^>]*>大正藏</th>\s*<td[^>]*>(.*?)</td>"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return []
    field_html = match.group(1)
    # Extract all sutra numbers from links
    taisho_nums = re.findall(r"sutra=(\d+)", field_html)
    # Also try plain text numbers
    if not taisho_nums:
        taisho_nums = re.findall(r'>(\d+)<', field_html)
    return [f"T{int(n)}" for n in taisho_nums if n]


def parse_detail_page(html, entry_id):
    result = {
        "id": entry_id,
        "entry_number": None,
        "taisho": [],
        "nanjio": None,
        "sanskrit_title": None,
        "chinese_title": None,
        "tibetan_title": None,
        "tibetan_wylie": None,
        "section": None,
    }

    if not html or len(html) < 200:
        return None
    if "經碼" not in html:
        return None

    # Entry/Tohoku number
    entry_no = extract_field(html, "經碼")
    if entry_no:
        m = re.search(r'No\.?\s*(\d+)', entry_no)
        if m:
            result["entry_number"] = int(m.group(1))

    # Taisho numbers
    result["taisho"] = extract_taisho_links(html)

    # Section (部類)
    result["section"] = extract_field(html, "部類")

    # Nanjio
    nj = extract_field(html, "南條文雄")
    if nj:
        m = re.match(r'(\d+)', nj.strip())
        if m:
            result["nanjio"] = f"Nj {m.group(1)}"

    # Sanskrit title
    result["sanskrit_title"] = extract_field(html, "梵文經名")

    # Chinese title
    result["chinese_title"] = extract_field(html, "中文經名")

    # Tibetan title (Unicode)
    result["tibetan_title"] = extract_field(html, "藏文經名")

    # Tibetan Wylie
    result["tibetan_wylie"] = extract_field(html, "藏語羅馬轉寫經名")

    # Skip entries with no useful data
    if not result["taisho"] and not result["entry_number"]:
        return None

    return result


def main():
    print("Scraping CBETA Jinglu Tibetan detail pages...")
    print(f"URL: {BASE_URL}NNNN")
    print(f"Scanning IDs 0001-{MAX_ID}")

    entries = {}
    empty_count = 0
    consecutive_empty = 0

    for entry_id in range(1, MAX_ID + 1):
        if entry_id % 200 == 0 or entry_id == 1:
            print(f"  Progress: {entry_id}/{MAX_ID} ({len(entries)} entries, {empty_count} empty)")

        url = f"{BASE_URL}{entry_id:04d}"
        html = fetch_url(url)

        if html is None:
            consecutive_empty += 1
            empty_count += 1
            if consecutive_empty > 100:
                print(f"  100 consecutive failures at {entry_id}, stopping.")
                break
            time.sleep(REQUEST_DELAY)
            continue

        result = parse_detail_page(html, entry_id)
        if result:
            entries[str(entry_id)] = result
            consecutive_empty = 0
        else:
            empty_count += 1
            if "經碼" not in (html or ""):
                consecutive_empty += 1
            else:
                consecutive_empty = 0
            if consecutive_empty > 100:
                print(f"  100 consecutive empty at {entry_id}, stopping.")
                break

        time.sleep(REQUEST_DELAY)

    # Summary
    with_taisho = sum(1 for e in entries.values() if e["taisho"])
    with_nanjio = sum(1 for e in entries.values() if e["nanjio"])
    with_sanskrit = sum(1 for e in entries.values() if e["sanskrit_title"])

    all_taisho = set()
    for e in entries.values():
        all_taisho.update(e["taisho"])

    # Count unique Tohoku-like entry numbers
    entry_nums = set(e["entry_number"] for e in entries.values() if e["entry_number"])

    print(f"\n=== Results ===")
    print(f"Total entries: {len(entries)}")
    print(f"  With Taisho: {with_taisho}")
    print(f"  With Nanjio: {with_nanjio}")
    print(f"  With Sanskrit: {with_sanskrit}")
    print(f"  Unique Taisho IDs: {len(all_taisho)}")
    print(f"  Unique entry numbers: {len(entry_nums)}")

    output = {
        "summary": {
            "total_entries": len(entries),
            "with_taisho": with_taisho,
            "with_nanjio": with_nanjio,
            "with_sanskrit": with_sanskrit,
            "unique_taisho": len(all_taisho),
            "unique_entry_numbers": len(entry_nums),
            "max_id_scanned": MAX_ID,
        },
        "entries": entries,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
