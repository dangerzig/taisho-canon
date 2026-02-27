#!/usr/bin/env python3
"""Extract Pali-to-Taisho parallel links from SuttaCentral parallels.json.

SuttaCentral's parallels.json contains 8,124 entries linking texts across
Pali, Chinese, Sanskrit, Tibetan, and other Buddhist canons. Each entry
is a group of mutually parallel texts.

This script:
1. Classifies each reference as Pali, Chinese/Taisho, or other
2. Pairs each Pali reference with each Chinese/Taisho reference in the
   same entry
3. Tracks full vs. partial parallel status (~ prefix in SC data)
4. Maps Agama collection references (da, ma, sa, ea) to parent Taisho texts
5. Resolves standalone Taisho references (t15, t210) to T##n#### format
6. Outputs structured JSON for the concordance builder

Usage:
    python3 scripts/parse_sc_parallels.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SC_PARALLELS = BASE_DIR / "sc-data" / "relationship" / "parallels.json"
CORPUS_IDS_PATH = BASE_DIR / "results" / "digest_relationships.json"
EXISTING_XREF_PATH = BASE_DIR / "results" / "cross_reference.json"
OUTPUT_PATH = BASE_DIR / "results" / "sc_pali_parallels.json"

# Agama collection prefixes -> parent Taisho text
AGAMA_TO_TAISHO = {
    "da": "T01n0001",      # Dirghagama
    "ma": "T01n0026",      # Madhyamagama
    "sa": "T02n0099",      # Samyuktagama (main)
    "sa-2": "T02n0100",    # Bieyi za ahan jing (shorter SA)
    "sa-3": "T02n0101",    # Partial SA translation
    "ea": "T02n0125",      # Ekottaragama
    "ea-2": "T02n0150A",   # Qi Chu San Guan Jing
}

# Pali collection prefixes (Sutta Pitaka, Vinaya, Abhidhamma, Khuddaka)
PALI_PREFIXES = {
    "dn", "mn", "sn", "an",              # Four Nikayas
    "dhp", "snp", "ud", "iti",           # Khuddaka Nikaya (verse)
    "thag", "thig",                       # Theragatha, Therigatha
    "ja",                                  # Jataka
    "kp",                                  # Khuddakapatha
    "pv", "vv",                           # Petavatthu, Vimanavatthu
    "cp",                                  # Cariyapitaka
    "cnd", "mnd",                         # Niddesa
    "tha-ap", "thi-ap",                   # Apadana
    "mil",                                 # Milindapanha
    "ne", "pe",                           # Netti, Petakopadesa
    "ds", "vb", "dt", "pp", "kv", "ya", "patthana",  # Abhidhamma
    "pli-tv",                             # Vinaya (prefix for all Vinaya refs)
}

# Standalone Taisho pattern: t followed by digits, optionally with .chapter
TAISHO_STANDALONE = re.compile(r'^~?t(\d+)')

# Agama pattern: collection prefix + optional dot + digits
# sa-2, sa-3, ea-2 use dot separator (sa-2.180), others don't (da21, ma98)
AGAMA_PATTERN = re.compile(r'^~?(da|ma|sa-3|sa-2|sa|ea-2|ea)\.?(\d+)')


def get_corpus_ids():
    """Get the set of all text IDs in our corpus."""
    ids = set()
    data = load_json(CORPUS_IDS_PATH)
    if data:
        for rel in data:
            ids.add(rel["digest_id"])
            ids.add(rel["source_id"])
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for section in ["tibetan_parallels", "pali_parallels",
                        "sanskrit_parallels"]:
            if section in xref:
                ids.update(xref[section].keys())
        if "no_parallel_found" in xref:
            ids.update(xref["no_parallel_found"])
    return ids


def build_num_to_id(corpus_ids):
    """Build bare Taisho number -> corpus ID mapping."""
    num_to_id = {}
    for text_id in sorted(corpus_ids):
        m = re.match(r'^T(\d{2})n(\d{4})', text_id)
        if m:
            num = int(m.group(2))
            if num not in num_to_id:
                num_to_id[num] = text_id
    return num_to_id


def load_json(path):
    """Load a JSON file, returning None on error."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  Warning: Could not load {path}: {e}")
        return None


def classify_ref(raw_ref):
    """Classify a single reference from parallels.json.

    Returns (category, normalized_ref, is_partial) where category is one of:
    'pali', 'taisho_standalone', 'agama', 'other'
    """
    is_partial = raw_ref.startswith("~")
    ref = raw_ref.lstrip("~")

    # Strip section reference (#...) for classification
    base_ref = ref.split("#")[0]

    # Check Agama collections (order matters: sa-2/sa-3 before sa, ea-2 before ea)
    agama_m = AGAMA_PATTERN.match(raw_ref)
    if agama_m:
        collection = agama_m.group(1)
        return "agama", collection, base_ref, is_partial

    # Check standalone Taisho (t followed by digits)
    taisho_m = TAISHO_STANDALONE.match(raw_ref)
    if taisho_m:
        num = int(taisho_m.group(1))
        return "taisho_standalone", num, base_ref, is_partial

    # Check Pali
    for prefix in sorted(PALI_PREFIXES, key=len, reverse=True):
        if prefix == "pli-tv":
            if base_ref.startswith("pli-tv"):
                return "pali", base_ref, base_ref, is_partial
        elif base_ref == prefix or base_ref.startswith(prefix) and (
            len(base_ref) == len(prefix) or
            base_ref[len(prefix)] in "0123456789.-"
        ):
            return "pali", base_ref, base_ref, is_partial

    return "other", base_ref, base_ref, is_partial


def parse_sc_parallels():
    """Parse SuttaCentral parallels.json and extract Pali-Taisho links."""
    data = load_json(SC_PARALLELS)
    if not data:
        print("ERROR: Could not load parallels.json")
        return

    print(f"Loaded {len(data)} parallel entries from SuttaCentral")

    corpus_ids = get_corpus_ids()
    num_to_id = build_num_to_id(corpus_ids)
    print(f"Corpus has {len(corpus_ids)} known Taisho text IDs")

    # Collect all (taisho_id, pali_ref) pairs with metadata
    # Key: (taisho_id, pali_ref) -> {types, agama_refs, entry_count}
    pair_data = defaultdict(lambda: {
        "types": set(),       # "full" or "partial"
        "agama_refs": set(),  # e.g. {"da1", "ma98"}
        "entry_count": 0,
    })

    stats = {
        "entries_with_pali": 0,
        "entries_with_chinese": 0,
        "entries_with_both": 0,
        "taisho_unresolved": set(),
    }

    for entry in data:
        refs = entry.get("parallels", [])

        pali_refs = []    # (normalized_ref, is_partial)
        chinese_refs = []  # (taisho_id, agama_ref_or_None, is_partial)

        for raw_ref in refs:
            result = classify_ref(raw_ref)

            if result[0] == "pali":
                _, norm, _, is_partial = result
                pali_refs.append((norm, is_partial))

            elif result[0] == "agama":
                _, collection, base_ref, is_partial = result
                taisho_id = AGAMA_TO_TAISHO.get(collection)
                if taisho_id and taisho_id in corpus_ids:
                    chinese_refs.append((taisho_id, base_ref, is_partial))

            elif result[0] == "taisho_standalone":
                _, num, base_ref, is_partial = result
                taisho_id = num_to_id.get(num)
                if taisho_id:
                    chinese_refs.append((taisho_id, None, is_partial))
                else:
                    stats["taisho_unresolved"].add(num)

        if pali_refs:
            stats["entries_with_pali"] += 1
        if chinese_refs:
            stats["entries_with_chinese"] += 1

        if pali_refs and chinese_refs:
            stats["entries_with_both"] += 1

            for pali_ref, pali_partial in pali_refs:
                for taisho_id, agama_ref, chinese_partial in chinese_refs:
                    is_partial = pali_partial or chinese_partial
                    link_type = "partial" if is_partial else "full"

                    key = (taisho_id, pali_ref)
                    pair_data[key]["types"].add(link_type)
                    pair_data[key]["entry_count"] += 1
                    if agama_ref:
                        pair_data[key]["agama_refs"].add(agama_ref)

    print(f"\nEntries with Pali refs: {stats['entries_with_pali']}")
    print(f"Entries with Chinese/Taisho refs: {stats['entries_with_chinese']}")
    print(f"Entries with both: {stats['entries_with_both']}")
    if stats["taisho_unresolved"]:
        print(f"Unresolved Taisho numbers: "
              f"{sorted(stats['taisho_unresolved'])[:20]}...")

    # Build output grouped by Taisho text
    pali_parallels = defaultdict(list)
    link_details = {}

    for (taisho_id, pali_ref), meta in sorted(pair_data.items()):
        # Best type: if any entry says "full", use "full"
        best_type = "full" if "full" in meta["types"] else "partial"

        pali_parallels[taisho_id].append(pali_ref)

        if taisho_id not in link_details:
            link_details[taisho_id] = {}
        link_details[taisho_id][pali_ref] = {
            "type": best_type,
            "entry_count": meta["entry_count"],
        }
        if meta["agama_refs"]:
            link_details[taisho_id][pali_ref]["agama_refs"] = sorted(
                meta["agama_refs"])

    # Sort Pali refs within each Taisho text
    for taisho_id in pali_parallels:
        pali_parallels[taisho_id] = sorted(set(pali_parallels[taisho_id]))

    # Summary
    unique_taisho = len(pali_parallels)
    unique_pali = set()
    for refs in pali_parallels.values():
        unique_pali.update(refs)
    total_links = sum(len(refs) for refs in pali_parallels.values())
    full_links = sum(
        1 for details in link_details.values()
        for d in details.values() if d["type"] == "full"
    )
    partial_links = total_links - full_links

    print(f"\nResults:")
    print(f"  Unique Taisho texts with Pali parallels: {unique_taisho}")
    print(f"  Unique Pali references: {len(unique_pali)}")
    print(f"  Total links: {total_links} "
          f"(full: {full_links}, partial: {partial_links})")

    # Compare with existing
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        old_pali = xref.get("pali_parallels", {})
        old_texts = set(old_pali.keys())
        new_texts = set(pali_parallels.keys())
        added = new_texts - old_texts
        print(f"\n  Previously: {len(old_texts)} texts with Pali parallels")
        print(f"  Now: {len(new_texts)} texts with Pali parallels")
        print(f"  New texts: {len(added)}")

    output = {
        "source": "suttacentral_parallels",
        "description": (
            "Pali-to-Taisho parallel links extracted from SuttaCentral "
            "parallels.json. Includes Agama collection mappings (DA/MA/SA/EA "
            "to parent Taisho texts) and standalone Taisho text references."
        ),
        "total_links": total_links,
        "full_links": full_links,
        "partial_links": partial_links,
        "unique_taisho": unique_taisho,
        "unique_pali": len(unique_pali),
        "pali_parallels": dict(sorted(pali_parallels.items())),
        "link_details": dict(sorted(link_details.items())),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to {OUTPUT_PATH}")


if __name__ == "__main__":
    parse_sc_parallels()
