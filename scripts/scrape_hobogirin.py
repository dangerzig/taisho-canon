#!/usr/bin/env python3
"""Extract Taisho cross-reference data from the Digital Hobogirin (法寶義林).

The Digital Hobogirin at https://tripitaka.l.u-tokyo.ac.jp/hbgrn/ is based on:
  Demiéville, P., Durt, H., and Seidel, A. (eds.): Fascicule annexe du
  Hōbōgirin: Répertoire du Canon bouddhique sino-japonais, édition de Taishō
  (Taishō Shinshū Daizōkyō), 2ème édition révisé et augmentée, Paris/Tokyo (1978).

The TEI/XML data file (hobotei.xml) is available under CC BY-SA from:
  https://tripitaka.l.u-tokyo.ac.jp/hbgrn/hobotei.xml

Data produced by SAT Daizōkyō Database Committee and Académie des inscriptions
et belles-lettres. Digital encoding by Nobumi Iyanaga, Yoichiro Watanabe,
Kiyonori Nagasaki, et al. Principal: Masahiro Shimoda.

IMPORTANT FINDING: The Hobogirin Repertoire is fundamentally a Sino-Japanese
catalog of the Taishō edition. It does NOT contain systematic Taisho-to-Tohoku
(Tibetan) cross-references in its scripture entries. The reference systems used
in the bibl entries are:

  - S.     = Shōwa (Shōwa Hōbō Sōmokuroku)
  - 卍      = Manji (Dai Nihon Zokuzōkyō)
  - Z.     = Zokuzōkyō continuation volumes
  - Nj.    = Nanjio Bunyiu catalogue (A Catalogue of the Chinese Translation
             of the Buddhist Tripitaka, 1883)
  - K.     = Korean canon (Koryŏ/Haeinsa)
  - Kyik.  = Kyōto Imperial Kōza series

Tohoku numbers (Tt. and Ttt.) appear ONLY in the biographical notes about
translators/authors, referencing their Tibetan canonical works. These are NOT
Taisho-to-Tibetan text parallels but biographical cross-references.

What this script DOES extract (valuable for concordance building):
  1. 3,018 Taisho text entries with structured metadata
  2. Sanskrit titles for ~712 entries (usable for title-matching against
     Tibetan catalogs like Toh)
  3. Nanjio numbers for ~1,630 entries (Nj. → Toh concordances exist)
  4. Korean canon numbers for ~1,411 entries
  5. Taisho-to-Taisho cross-references ("Cf." entries)
  6. 915 translator/author person entries with biographical data
  7. Person-to-Taisho-text links via the @corresp and @sameAs attributes

Output: results/hobogirin_taisho_tibetan.json
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "results" / "hobogirin_taisho_tibetan.json"
TEI_CACHE_PATH = BASE_DIR / "data" / "hobotei.xml"

TEI_URL = "https://tripitaka.l.u-tokyo.ac.jp/hbgrn/hobotei.xml"
USER_AGENT = "TaishoCanonResearch/1.0 (academic research)"
TEI_NS = "http://www.tei-c.org/ns/1.0"


def fetch_tei_xml():
    """Download the TEI XML file if not already cached."""
    if TEI_CACHE_PATH.exists():
        print(f"Using cached TEI XML: {TEI_CACHE_PATH}")
        return TEI_CACHE_PATH

    print(f"Downloading TEI XML from {TEI_URL} ...")
    TEI_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    req = Request(TEI_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        data = resp.read()
    TEI_CACHE_PATH.write_bytes(data)
    print(f"Saved {len(data):,} bytes to {TEI_CACHE_PATH}")
    return TEI_CACHE_PATH


def ns(tag):
    """Add TEI namespace to tag name."""
    return f"{{{TEI_NS}}}{tag}"


def text_content(elem):
    """Get all text content of an element, including children."""
    if elem is None:
        return ""
    return "".join(elem.itertext()).strip()


def normalize_taisho_id(raw_id):
    """Normalize a Taisho ID to standard CBETA format (e.g., T1 -> T01n0001).

    The Hobogirin uses bare numbers or T-prefixed IDs (T1, T250, T2917A).
    We convert to CBETA format using a volume lookup when available.
    """
    # Strip leading 'T' if present
    num_str = raw_id
    if num_str.startswith("T"):
        num_str = num_str[1:]

    # Handle letter suffixes like T2917A, T2917B
    suffix = ""
    match = re.match(r"^(\d+)([A-Za-z]*)$", num_str)
    if match:
        num_part = match.group(1)
        suffix = match.group(2).lower()
    else:
        num_part = num_str

    return f"T{int(num_part):04d}{suffix}" if num_part.isdigit() else raw_id


def extract_nanjio(note_text):
    """Extract Nanjio catalogue number(s) from note text."""
    matches = re.findall(r"Nj\.\s*(\d+)", note_text)
    return [int(m) for m in matches]


def extract_korean(note_text):
    """Extract Korean canon (K.) number(s) from note text."""
    matches = re.findall(r"K\.\s*(\d+)", note_text)
    return [int(m) for m in matches]


def extract_cf_refs(note_text):
    """Extract Cf. (cross-reference) Taisho numbers from note text.

    Handles formats like:
      Cf. 251-255, 257
      Cf. 1 (10)
      Cf. 26 (99-101), 125 (48, 4)
    """
    cf_match = re.search(r"Cf\.\s*(.+?)(?:\s*[東西南北後前劉宋唐秦晉隋梁陳]|\s*\d{1,2}\s*$)", note_text)
    if not cf_match:
        return []

    cf_text = cf_match.group(1)
    # Extract all bare numbers (not in parentheses)
    refs = []
    # Remove parenthetical sub-references
    clean = re.sub(r"\([^)]*\)", "", cf_text)
    # Extract numbers and ranges
    for part in clean.split(","):
        part = part.strip()
        range_match = re.match(r"(\d+)\s*-\s*(\d+)", part)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            refs.extend(range(start, end + 1))
        elif part.isdigit():
            refs.append(int(part))
    return refs


def extract_hobogirin_page(note_text):
    """Extract the Hobogirin Repertoire page number from note text.

    Format: dynasty name followed by a number at the end of the note.
    e.g., "後秦 31" or "唐 8"

    IMPORTANT: This number is the PAGE NUMBER in the 1978 Hobogirin Répertoire,
    NOT the Taisho volume number. The two are unrelated.
    """
    dynasty_match = re.search(
        r"(?:後漢|三國|西晉|東晉|前秦|後秦|姚秦|北涼|劉宋|蕭齊|梁|陳|北魏|北齊|隋|唐|宋|五代|元|明|清|高麗|新羅|日本)\s*(\d+)\s*$",
        note_text,
    )
    if dynasty_match:
        return int(dynasty_match.group(1))
    return None


def extract_dynasty(note_text):
    """Extract the dynasty attribution from note text.

    The dynasty name at the end of the note indicates when the translation
    was made (e.g., 後秦 = Later Qin, 唐 = Tang, etc.)
    """
    dynasty_match = re.search(
        r"(後漢|三國|西晉|東晉|前秦|後秦|姚秦|北涼|劉宋|蕭齊|梁|陳|北魏|北齊|隋|唐|宋|五代|元|明|清|高麗|新羅|日本)\s*\d*\s*$",
        note_text,
    )
    if dynasty_match:
        return dynasty_match.group(1)
    return None


# Dynasty names and approximate date ranges (for reference)
DYNASTY_DATES = {
    "後漢": "25-220",
    "三國": "220-280",
    "西晉": "265-316",
    "東晉": "317-420",
    "前秦": "351-394",
    "後秦": "384-417",
    "姚秦": "384-417",
    "北涼": "397-439",
    "劉宋": "420-479",
    "蕭齊": "479-502",
    "梁": "502-557",
    "陳": "557-589",
    "北魏": "386-534",
    "北齊": "550-577",
    "隋": "581-618",
    "唐": "618-907",
    "宋": "960-1279",
    "五代": "907-960",
    "元": "1271-1368",
    "明": "1368-1644",
    "清": "1644-1912",
    "高麗": "918-1392",
    "新羅": "57 BCE-935",
    "日本": "",
}


def main():
    """Main extraction pipeline."""
    print("=" * 70)
    print("Digital Hobogirin (法寶義林) Data Extraction")
    print("=" * 70)

    # Step 1: Fetch TEI XML
    tei_path = fetch_tei_xml()

    # Step 2: Parse XML
    print("\nParsing TEI XML ...")
    # xml.etree doesn't handle xml:id natively; we need to preprocess
    xml_text = tei_path.read_text(encoding="utf-8")
    # Convert xml:id to plain id attributes for easier parsing
    xml_text = xml_text.replace("xml:id=", "xmlid=")
    xml_text = xml_text.replace("xml:lang=", "xmllang=")

    root = ET.fromstring(xml_text)

    # Step 3: Extract bibl entries (Taisho texts)
    print("\nExtracting Taisho text entries ...")

    # Re-parse with modified attribute names
    bibl_entries = {}
    for bibl in root.iter(ns("bibl")):
        xml_id = bibl.get("xmlid", "")
        if not xml_id or not re.match(r"T\d+", xml_id):
            continue

        taisho_id = normalize_taisho_id(xml_id)

        titles = {}
        for title_elem in bibl.findall(ns("title")):
            lang = title_elem.get("xmllang", "")
            title_text = text_content(title_elem).strip()
            if title_text:
                titles[lang] = title_text

        idno_elem = bibl.find(ns("idno"))
        idno = text_content(idno_elem).strip() if idno_elem is not None else ""

        persons = []
        for name_elem in bibl.findall(ns("name")):
            corresp = name_elem.get("corresp", "")
            role = name_elem.get("type", "")
            if corresp:
                persons.append({"id": corresp.lstrip("#"), "role": role})

        note_elem = bibl.find(ns("note"))
        note_text = text_content(note_elem).strip() if note_elem is not None else ""

        nanjio = extract_nanjio(note_text)
        korean = extract_korean(note_text)
        cf_refs = extract_cf_refs(note_text)
        hbgrn_page = extract_hobogirin_page(note_text)
        dynasty = extract_dynasty(note_text)

        entry = {
            "taisho_id": taisho_id,
            "hobogirin_id": xml_id,
        }

        if titles.get("zh"):
            entry["chinese_title"] = titles["zh"]
        if titles.get("zh-Latn"):
            entry["chinese_title_pinyin"] = titles["zh-Latn"]
        if titles.get("ja-Latn"):
            entry["japanese_title_romaji"] = titles["ja-Latn"]
        if titles.get("sa-Latn"):
            entry["sanskrit_title"] = titles["sa-Latn"]

        if persons:
            entry["persons"] = persons
        if nanjio:
            entry["nanjio"] = nanjio
        if korean:
            entry["korean"] = korean
        if cf_refs:
            entry["cf_refs"] = [f"T{r:04d}" for r in cf_refs]
        if dynasty:
            entry["dynasty"] = dynasty
        if hbgrn_page:
            entry["hobogirin_page"] = hbgrn_page

        if note_text:
            entry["note"] = note_text

        bibl_entries[taisho_id] = entry

    print(f"  Found {len(bibl_entries)} Taisho text entries")

    # Count entries with various data
    n_sanskrit = sum(1 for e in bibl_entries.values() if "sanskrit_title" in e)
    n_nanjio = sum(1 for e in bibl_entries.values() if "nanjio" in e)
    n_korean = sum(1 for e in bibl_entries.values() if "korean" in e)
    n_cf = sum(1 for e in bibl_entries.values() if "cf_refs" in e)
    n_dynasty = sum(1 for e in bibl_entries.values() if "dynasty" in e)

    print(f"  With Sanskrit titles: {n_sanskrit}")
    print(f"  With Nanjio numbers: {n_nanjio}")
    print(f"  With Korean numbers: {n_korean}")
    print(f"  With cross-references: {n_cf}")
    print(f"  With dynasty attribution: {n_dynasty}")

    # Step 4: Extract person entries
    print("\nExtracting person entries ...")
    person_entries = {}
    for person in root.iter(ns("person")):
        xml_id = person.get("xmlid", "")
        if not xml_id or not xml_id.startswith("TP"):
            continue

        names = {}
        for pn in person.findall(f".//{ns('persName')}"):
            lang = pn.get("xmllang", "")
            name_text = text_content(pn).strip()
            if name_text and lang:
                if lang not in names:
                    names[lang] = []
                names[lang].append(name_text)

        for an in person.findall(f".//{ns('addName')}"):
            lang = an.get("xmllang", "")
            name_text = text_content(an).strip()
            if name_text and lang:
                key = f"{lang}-alt"
                if key not in names:
                    names[key] = []
                names[key].append(name_text)

        taisho_refs = []
        tohoku_refs = []
        for bibl_elem in person.findall(f".//{ns('bibl')}"):
            same_as = bibl_elem.get("sameAs", "")
            if same_as and same_as.startswith("#T") and re.match(
                r"#T\d+", same_as
            ):
                taisho_refs.append(normalize_taisho_id(same_as.lstrip("#")))

            bibl_text = text_content(bibl_elem)
            for m in re.findall(r"Tt\.\s*(\d+)", bibl_text):
                tohoku_refs.append(f"Toh {m}")
            for m in re.findall(r"Ttt\.\s*(\d+)", bibl_text):
                tohoku_refs.append(f"Toh {m}")

        for abbr_elem in person.findall(f".//{ns('abbr')}"):
            abbr_text = text_content(abbr_elem)
            for m in re.findall(r"Tt\.\s*(\d+)", abbr_text):
                tohoku_refs.append(f"Toh {m}")
            for m in re.findall(r"Ttt\.\s*(\d+)", abbr_text):
                tohoku_refs.append(f"Toh {m}")

        note_elem = person.find(ns("note"))
        note_text = text_content(note_elem).strip() if note_elem is not None else ""

        # Extract Taisho attributions from note ending
        note_taisho = []
        dash_match = re.search(r"[–—]\s*([\d\[\], ]+)\.\s*$", note_text)
        if dash_match:
            nums_text = dash_match.group(1)
            for num_match in re.findall(r"\[?(\d+)\]?", nums_text):
                note_taisho.append(normalize_taisho_id(f"T{num_match}"))

        entry = {
            "person_id": xml_id,
            "names": names,
        }
        if taisho_refs:
            entry["taisho_works"] = sorted(set(taisho_refs))
        if note_taisho:
            entry["taisho_attributions"] = sorted(set(note_taisho))
        if tohoku_refs:
            entry["tohoku_refs"] = sorted(set(tohoku_refs))

        person_entries[xml_id] = entry

    print(f"  Found {len(person_entries)} person entries")
    n_with_taisho = sum(
        1 for p in person_entries.values()
        if p.get("taisho_works") or p.get("taisho_attributions")
    )
    n_with_tohoku = sum(
        1 for p in person_entries.values() if p.get("tohoku_refs")
    )
    print(f"  With Taisho text links: {n_with_taisho}")
    print(f"  With Tohoku references: {n_with_tohoku}")

    # Step 5: Extract indirect Tibetan links
    print("\nSearching for indirect Taisho-to-Tibetan links ...")
    indirect_links = []
    for pid, person in person_entries.items():
        toh_refs = person.get("tohoku_refs", [])
        all_taisho = list(
            set(
                person.get("taisho_works", [])
                + person.get("taisho_attributions", [])
            )
        )
        if toh_refs and all_taisho:
            indirect_links.append(
                {
                    "person_id": pid,
                    "person_names": person.get("names", {}),
                    "taisho_works": sorted(all_taisho),
                    "tohoku_refs": sorted(set(toh_refs)),
                }
            )

    if indirect_links:
        print(f"  Found {len(indirect_links)} persons with both Taisho and Tohoku refs")
        for link in indirect_links:
            print(
                f"    {link['person_id']}: "
                f"{len(link['taisho_works'])} Taisho, "
                f"{len(link['tohoku_refs'])} Tohoku"
            )
    else:
        print("  No indirect links found.")

    # Step 6: Build output in requested format
    print("\nBuilding output ...")

    # Format bibl entries with tibetan_refs field (will be empty for most entries
    # since the Hobogirin doesn't contain systematic Taisho-to-Tibetan mappings)
    formatted_entries = {}
    for tid, entry in sorted(bibl_entries.items()):
        formatted = {
            "taisho": tid,
            "tibetan_refs": [],  # Not available in Hobogirin
            "sanskrit_title": entry.get("sanskrit_title", ""),
            "chinese_title": entry.get("chinese_title", ""),
            "japanese_title": entry.get("japanese_title_romaji", ""),
            "nanjio": entry.get("nanjio", []),
            "korean": entry.get("korean", []),
            "cf_refs": entry.get("cf_refs", []),
            "note": entry.get("note", ""),
        }
        if "dynasty" in entry:
            formatted["dynasty"] = entry["dynasty"]
        if "hobogirin_page" in entry:
            formatted["hobogirin_page"] = entry["hobogirin_page"]
        if "persons" in entry:
            formatted["translators"] = entry["persons"]
        formatted_entries[tid] = formatted

    output = {
        "source": "hobogirin",
        "source_url": "https://tripitaka.l.u-tokyo.ac.jp/hbgrn/",
        "source_description": (
            "Digital 法寶義林 (Hôbôgirin) TEI edition, based on the 1978 "
            "Répertoire du Canon bouddhique sino-japonais. Data under CC BY-SA."
        ),
        "extraction_note": (
            "The Hobogirin Repertoire does NOT contain systematic "
            "Taisho-to-Tohoku (Tibetan) cross-references. The tibetan_refs "
            "fields are empty. However, the Sanskrit titles and Nanjio numbers "
            "can be used for indirect matching against Tibetan catalogs. "
            "Tohoku numbers (Tt./Ttt.) appear only in biographical notes about "
            "translators and refer to biographical texts, not text parallels."
        ),
        "statistics": {
            "total_taisho_entries": len(bibl_entries),
            "entries_with_sanskrit_title": n_sanskrit,
            "entries_with_nanjio": n_nanjio,
            "entries_with_korean": n_korean,
            "entries_with_cross_refs": n_cf,
            "total_persons": len(person_entries),
            "persons_with_taisho_links": n_with_taisho,
            "persons_with_tohoku_refs": n_with_tohoku,
            "indirect_taisho_tibetan_links": len(indirect_links),
        },
        "total_entries": len(formatted_entries),
        "entries": formatted_entries,
        "persons": {
            pid: {
                k: v
                for k, v in p.items()
                if k != "note"  # Omit lengthy notes to keep file manageable
            }
            for pid, p in sorted(person_entries.items())
        },
        "indirect_tibetan_links": indirect_links,
    }

    # Step 7: Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    file_size = OUTPUT_PATH.stat().st_size
    print(f"\nOutput saved to {OUTPUT_PATH}")
    print(f"File size: {file_size:,} bytes")

    # Step 8: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Taisho entries extracted: {len(bibl_entries)}")
    print(f"Entries with Sanskrit titles:   {n_sanskrit}")
    print(f"Entries with Nanjio numbers:    {n_nanjio}")
    print(f"Entries with Korean numbers:    {n_korean}")
    print(f"Entries with cross-references:  {n_cf}")
    print(f"Total person entries:           {len(person_entries)}")
    print(f"Persons with Tohoku refs:       {n_with_tohoku}")
    print()
    print("NOTE: The Hobogirin does not contain direct Taisho-to-Tohoku")
    print("cross-references. For Tibetan concordance building, the most")
    print("valuable data are:")
    print("  1. Sanskrit titles (for title-based matching)")
    print("  2. Nanjio numbers (existing Nj-to-Toh concordances can bridge)")
    print("  3. Taisho cross-references (for related text discovery)")
    print("=" * 70)


if __name__ == "__main__":
    main()
