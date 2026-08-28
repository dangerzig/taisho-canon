#!/usr/bin/env python3
"""Extract document-level Taishō-Tohoku pairs from MITRA-parallel filenames.

MITRA-parallel (Nehrdich & Keutzer 2025) contains sentence-level alignments
between Buddhist texts in Sanskrit, Chinese, and Tibetan. Each TSV file
represents alignments between a specific pair of texts.

This script:
1. Parses filenames for Taishō (T##n####) and Derge/Tohoku (D####) identifiers
2. Counts aligned sentence pairs per file
3. Aggregates across files for the same (Taishō, Tohoku) pair
4. Assigns confidence based on sentence count
5. Outputs JSON for the concordance builder

Usage:
    python3 scripts/parse_mitra.py
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MITRA_TSV_DIR = BASE_DIR / "data" / "mitra-parallel" / "mitra-parallel" / "tsv"
OUTPUT_PATH = BASE_DIR / "results" / "mitra_taisho_tohoku.json"

# Minimum sentences for a pair to be included.
# Threshold 20 chosen empirically: corroborated links (confirmed by catalog
# sources) have a median of 139 sentences, while uncorroborated links with
# <20 sentences are predominantly formulaic phrase coincidences (e.g. homage
# formulas, "Thus have I heard") rather than genuine document parallels.
MIN_SENTENCES = 20

# Confidence tiers
CONFIDENCE_STRONG = 0.9   # >=100 sentences
CONFIDENCE_MODERATE = 0.7  # 20-99 sentences
CONFIDENCE_WEAK = 0.4      # <20 sentences (filtered out before output)

# Patterns (matched against the segment-number columns, which are authoritative
# for the text identity, NOT against the filename).
TAISHO_PATTERN = re.compile(r'T(\d{2})n(\d{4}[A-Za-z]?)')
DERGE_PATTERN = re.compile(r'D(\d{4})')


def _script_fracs(s):
    """Return (cjk_fraction, tibetan_fraction) of a string."""
    if not s:
        return 0.0, 0.0
    cjk = sum(1 for c in s if '一' <= c <= '鿿')
    tib = sum(1 for c in s if 'ༀ' <= c <= '࿿')
    n = len(s)
    return cjk / n, tib / n


def count_chinese_tibetan_pairs(filepath):
    """Count only genuine Chinese<->Tibetan aligned rows in a TSV file, and
    return {(taisho_id, toh_int): n_rows} extracted from the aligned columns.

    Bug fixed here: the previous version keyed off the *filename* and counted
    every row, so Tibetan<->Sanskrit Tengyur alignments (whose filenames also
    carry a Taisho token) were miscounted as Chinese<->Tibetan. We now inspect
    the actual script of each aligned row: a row counts only if one side is
    CJK (Chinese) with a Taisho segment id and the other is Tibetan script with
    a Derge segment id.
    """
    from collections import defaultdict
    pairs = defaultdict(int)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.readline()  # header: src_segmentnr, src_original, tgt_segmentnr, tgt_original
            for line in f:
                p = line.rstrip('\n').split('\t')
                if len(p) < 4:
                    continue
                src_id, src_txt, tgt_id, tgt_txt = p[0], p[1], p[2], p[3]
                if not src_txt.strip() or not tgt_txt.strip():
                    continue
                src_cjk, src_tib = _script_fracs(src_txt)
                tgt_cjk, tgt_tib = _script_fracs(tgt_txt)
                # Identify which side is Chinese and which is Tibetan by script.
                if src_cjk > 0.3 and tgt_tib > 0.3:
                    chinese_id, tibetan_id = src_id, tgt_id
                elif tgt_cjk > 0.3 and src_tib > 0.3:
                    chinese_id, tibetan_id = tgt_id, src_id
                else:
                    continue  # not a Chinese<->Tibetan row (Skt/Ch, Skt/Tib, etc.)
                tm = TAISHO_PATTERN.search(chinese_id)
                dm = DERGE_PATTERN.search(tibetan_id)
                if not tm or not dm:
                    continue
                taisho_id = f"T{tm.group(1)}n{tm.group(2)}"
                toh = int(dm.group(1))
                pairs[(taisho_id, toh)] += 1
    except (OSError, UnicodeDecodeError):
        return {}
    return pairs


def assign_confidence(sentence_count):
    """Assign confidence tier based on sentence count."""
    if sentence_count >= 100:
        return CONFIDENCE_STRONG
    elif sentence_count >= 20:
        return CONFIDENCE_MODERATE
    else:
        return CONFIDENCE_WEAK


def parse_mitra():
    """Extract document-level pairs from MITRA filenames."""
    if not MITRA_TSV_DIR.exists():
        print(f"ERROR: MITRA directory not found: {MITRA_TSV_DIR}")
        return

    # Aggregate: (taisho_id, toh_num) -> total sentence count
    pair_sentences = defaultdict(int)
    file_count = 0
    skipped = 0

    tsv_files = sorted(MITRA_TSV_DIR.glob("*.tsv"))
    total = len(tsv_files)
    print(f"Scanning {total} MITRA TSV files...")

    for i, filepath in enumerate(tsv_files):
        if (i + 1) % 2000 == 0:
            print(f"  {i + 1}/{total}...")

        # Count only genuine Chinese<->Tibetan rows, keyed by the actual text
        # ids found in the aligned columns (script-verified).
        file_pairs = count_chinese_tibetan_pairs(filepath)
        if not file_pairs:
            skipped += 1
            continue

        file_count += 1
        for (taisho_id, toh), n_rows in file_pairs.items():
            pair_sentences[(taisho_id, toh)] += n_rows

    print(f"\nParsed {file_count} files with Taishō-Tohoku pairs "
          f"(skipped {skipped})")
    print(f"Raw unique pairs: {len(pair_sentences)}")

    # Filter and build output
    entries = {}
    filtered_out = 0
    for (taisho_id, toh), total_sentences in sorted(pair_sentences.items()):
        if total_sentences < MIN_SENTENCES:
            filtered_out += 1
            continue

        confidence = assign_confidence(total_sentences)
        toh_str = f"Toh {toh}"
        entry_key = f"{taisho_id}_{toh_str.replace(' ', '_')}"

        entries[entry_key] = {
            "taisho": taisho_id,
            "tohoku": toh_str,
            "sentence_count": total_sentences,
            "confidence": confidence,
            "note": f"{total_sentences} aligned sentence pairs (MITRA-parallel)"
        }

    print(f"After filtering (<{MIN_SENTENCES} sentences): "
          f"{len(entries)} pairs ({filtered_out} filtered out)")

    # Summary stats
    unique_taisho = set(e["taisho"] for e in entries.values())
    unique_toh = set(e["tohoku"] for e in entries.values())
    strong = sum(1 for e in entries.values()
                 if e["confidence"] == CONFIDENCE_STRONG)
    moderate = sum(1 for e in entries.values()
                   if e["confidence"] == CONFIDENCE_MODERATE)
    weak = sum(1 for e in entries.values()
               if e["confidence"] == CONFIDENCE_WEAK)

    print(f"\nUnique Taishō texts: {len(unique_taisho)}")
    print(f"Unique Tohoku numbers: {len(unique_toh)}")
    print(f"Confidence breakdown: "
          f"strong={strong}, moderate={moderate}, weak={weak}")

    output = {
        "source": "mitra",
        "citation": ("Nehrdich, Sebastian & Kurt Keutzer. 2025. "
                     "MITRA: A Large-Scale Parallel Corpus and Multilingual "
                     "Pretrained Language Model for Machine Translation and "
                     "Semantic Retrieval for Pali, Sanskrit, Buddhist Chinese, "
                     "and Tibetan. arXiv:2601.06400."),
        "min_sentences": MIN_SENTENCES,
        "total_pairs": len(entries),
        "unique_taisho": len(unique_taisho),
        "unique_tohoku": len(unique_toh),
        "entries": entries,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to {OUTPUT_PATH}")


if __name__ == "__main__":
    parse_mitra()
