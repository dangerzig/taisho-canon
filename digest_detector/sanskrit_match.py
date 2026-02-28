"""Sanskrit title matching pipeline for Chinese-Tibetan parallel identification.

Matches Sanskrit titles across the Taishō and Kangyur/Tengyur canons to discover
new parallel identifications beyond the 733 already catalogued in the concordance.

Sources:
  Taishō side:
    - Lancaster catalogue (lancaster_taisho_crossref.json): ~770 texts with Sanskrit titles
    - CBETA Jinglu Sanskrit (results/cbeta_jinglu_sanskrit.json): 704 entries
  Kangyur/Tengyur side:
    - 84000 TEI XML files (kangyur placeholders + translations, tengyur placeholders)
    - CBETA Jinglu Tibetan (results/cbeta_jinglu_tibetan.json): 3,727 with Sanskrit titles

Run: python3 -m digest_detector.sanskrit_match
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 1. Title normalisation
# ---------------------------------------------------------------------------

# IAST diacritics → plain ASCII mapping
_IAST_MAP: dict[str, str] = {
    "ā": "a", "ī": "i", "ū": "u",
    "ṃ": "m", "ṁ": "m",
    "ṇ": "n", "ñ": "n", "ṅ": "n",
    "ś": "s", "ṣ": "s",
    "ṭ": "t",
    "ḍ": "d",
    "ḥ": "h",
    "ṛ": "r", "ṝ": "r",
    "ḷ": "l", "ḹ": "l",
    # uppercase
    "Ā": "a", "Ī": "i", "Ū": "u",
    "Ṃ": "m", "Ṁ": "m",
    "Ṇ": "n", "Ñ": "n", "Ṅ": "n",
    "Ś": "s", "Ṣ": "s",
    "Ṭ": "t",
    "Ḍ": "d",
    "Ḥ": "h",
    "Ṛ": "r", "Ṝ": "r",
    "Ḷ": "l", "Ḹ": "l",
}

# Build a single-pass translation table
_IAST_TRANS = str.maketrans(_IAST_MAP)

# Minimum Levenshtein ratio for fuzzy matches (pass 3)
FUZZY_THRESHOLD = 0.90

# Soft hyphen / zero-width characters used by 84000 TEI
_INVISIBLE_RE = re.compile(r"[\u00ad\u200b\u200c\u200d\ufeff]")


def normalize_title(raw: str) -> str:
    """Normalise a Sanskrit title for comparison.

    Steps:
      1. Decode HTML entities (Lancaster data may have &ntilde; etc.)
      2. Strip IAST diacritics
      3. Lowercase
      4. Remove hyphens, soft hyphens, punctuation, spaces
      5. Collapse to a single ASCII string
    """
    if not raw:
        return ""
    # Decode HTML entities
    text = html.unescape(raw)
    # Remove invisible Unicode chars (soft hyphen, zero-width, etc.)
    text = _INVISIBLE_RE.sub("", text)
    # Apply IAST → ASCII
    text = text.translate(_IAST_TRANS)
    # Lowercase
    text = text.lower()
    # Remove hyphens, periods, parentheses, spaces, punctuation
    text = re.sub(r"[-–—.\s()\[\]{},;:/'\"*?!]+", "", text)
    return text


def tokenize_title(raw: str) -> set[str]:
    """Split a Sanskrit title into normalised word tokens for Jaccard matching."""
    if not raw:
        return set()
    text = html.unescape(raw)
    text = _INVISIBLE_RE.sub("", text)
    text = text.translate(_IAST_TRANS)
    text = text.lower()
    # Split on hyphens, spaces, punctuation (keeping words)
    tokens = re.split(r"[-–—.\s()\[\]{},;:/'\"*?!]+", text)
    return {t for t in tokens if len(t) >= 2}


# ---------------------------------------------------------------------------
# 2. Levenshtein ratio (pure Python, no external deps)
# ---------------------------------------------------------------------------

def _levenshtein_distance_bounded(s1: str, s2: str, max_dist: int) -> int:
    """Compute Levenshtein distance with early termination.

    Returns the edit distance, or max_dist + 1 if it exceeds max_dist.
    This is much faster than full Levenshtein when we only care about
    distances below a threshold.
    """
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > max_dist:
        return max_dist + 1
    if len1 < len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1
    if not len2:
        return len1

    prev = list(range(len2 + 1))
    for i in range(len1):
        curr = [i + 1]
        row_min = i + 1
        c1 = s1[i]
        for j in range(len2):
            cost = 0 if c1 == s2[j] else 1
            val = min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost)
            curr.append(val)
            if val < row_min:
                row_min = val
        if row_min > max_dist:
            return max_dist + 1
        prev = curr
    return prev[len2]


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Return similarity ratio in [0, 1] based on Levenshtein distance."""
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = _levenshtein_distance_bounded(s1, s2, max_len)
    return 1.0 - dist / max_len


def levenshtein_ratio_threshold(s1: str, s2: str, threshold: float) -> float:
    """Compute Levenshtein ratio, returning 0.0 early if below threshold.

    Uses bounded distance computation for speed.
    """
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    max_dist = int(max_len * (1.0 - threshold))
    dist = _levenshtein_distance_bounded(s1, s2, max_dist)
    if dist > max_dist:
        return 0.0
    return 1.0 - dist / max_len


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard index of two token sets."""
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


# ---------------------------------------------------------------------------
# 3. Data loading
# ---------------------------------------------------------------------------

def _project_root() -> Path:
    """Return the project root (parent of digest_detector/)."""
    return Path(__file__).resolve().parent.parent


def _normalize_taisho_id(raw: str) -> str:
    """Convert various Taishō ID formats to canonical TXXnNNNN.

    Lancaster uses 'T250', CBETA uses 'T220', we need 'T08n0250'.
    """
    raw = raw.strip()
    # Already in TXXnNNNN format?
    if re.match(r"T\d{2}n\d{4}", raw):
        return raw
    # Bare T-number: T250 → need to determine volume
    m = re.match(r"T(\d+)", raw)
    if not m:
        return raw
    num = int(m.group(1))
    vol = _taisho_number_to_volume(num)
    return f"T{vol:02d}n{num:04d}"


# Rough Taishō number → volume mapping based on the catalogue structure.
# This covers the main ranges; edge cases may exist.
_TAISHO_VOL_RANGES: list[tuple[int, int, int]] = [
    (1, 25, 1),      # T01: 1-25
    (26, 99, 1),     # T01: 26-99
    (100, 124, 2),   # T02
    (125, 150, 2),
    (151, 219, 4),
    (220, 220, 5),   # T220 spans vols 5-7
    (221, 223, 8),
    (224, 228, 8),
    (229, 261, 8),
    (262, 277, 9),
    (278, 309, 10),
    (310, 310, 11),
    (311, 373, 12),
    (374, 396, 12),
    (397, 424, 13),
    (425, 460, 14),
    (461, 639, 15),
    (640, 644, 15),
    (645, 741, 16),
    (742, 802, 17),
    (803, 864, 18),
    (865, 1019, 19),
    (1020, 1108, 20),
    (1109, 1197, 21),
    (1198, 1420, 22),
    (1421, 1504, 24),
    (1505, 1535, 25),
]


def _taisho_number_to_volume(num: int) -> int:
    """Best-effort mapping from Taishō text number to volume number."""
    for lo, hi, vol in _TAISHO_VOL_RANGES:
        if lo <= num <= hi:
            return vol
    # Fallback: try to infer from the XML corpus
    return _lookup_volume_from_xml(num)


def _lookup_volume_from_xml(num: int) -> int:
    """Try to find the volume by checking which XML file exists."""
    xml_dir = _project_root() / "xml" / "T"
    if not xml_dir.exists():
        return 0
    # Look for T??n{num:04d}.xml pattern
    pattern = f"n{num:04d}"
    for vol_dir in sorted(xml_dir.iterdir()):
        if vol_dir.is_dir():
            for f in vol_dir.iterdir():
                if pattern in f.name:
                    # Extract volume from directory name
                    try:
                        return int(vol_dir.name)
                    except ValueError:
                        pass
    return 0


def load_taisho_sanskrit_titles() -> dict[str, list[str]]:
    """Load Sanskrit titles for Taishō texts from Lancaster and CBETA Sanskrit.

    Returns: {taisho_id: [sanskrit_title_1, ...]}  (canonical TXXnNNNN IDs)
    """
    root = _project_root()
    titles: dict[str, list[str]] = defaultdict(list)

    # --- Lancaster ---
    lancaster_path = root / "lancaster_taisho_crossref.json"
    if lancaster_path.exists():
        with open(lancaster_path) as f:
            data = json.load(f)
        for key, entry in data.items():
            skt = entry.get("sanskrit_title", "")
            if skt:
                tnum = entry.get("taisho", "")
                tid = _normalize_taisho_id(key)
                if tid:
                    titles[tid].append(skt)

    # --- CBETA Jinglu Sanskrit ---
    cbeta_skt_path = root / "results" / "cbeta_jinglu_sanskrit.json"
    if cbeta_skt_path.exists():
        with open(cbeta_skt_path) as f:
            data = json.load(f)
        for eid, entry in data.get("entries", {}).items():
            skt = entry.get("sanskrit_title", "")
            if skt:
                for t_raw in entry.get("taisho", []):
                    tid = _normalize_taisho_id(t_raw)
                    if tid:
                        titles[tid].append(skt)

    # Deduplicate per Taishō ID
    for tid in titles:
        titles[tid] = list(dict.fromkeys(titles[tid]))

    return dict(titles)


def _parse_toh_numbers(bibl_keys: list[str]) -> list[int]:
    """Extract Tohoku numbers from bibl key attributes like 'toh17', 'toh489'."""
    nums = []
    for key in bibl_keys:
        m = re.match(r"toh(\d+)", key)
        if m:
            nums.append(int(m.group(1)))
    return nums


def _parse_toh_from_filename(fname: str) -> list[int]:
    """Extract Tohoku numbers from 84000 filename.

    Examples:
      034-009_toh21,531-the_heart_... → [21, 531]
      034-005_toh17,489-the_principles... → [17, 489]
      001-001_toh1109-visesastava.xml → [1109]
    """
    m = re.search(r"toh([\d,]+)", fname)
    if not m:
        return []
    return [int(n) for n in m.group(1).split(",") if n.isdigit()]


def _parse_84000_tei(filepath: Path) -> list[tuple[int, str, str]]:
    """Parse an 84000 TEI XML file for Sanskrit titles and Tohoku numbers.

    Returns list of (tohoku_number, sanskrit_main_title, source_path).
    """
    results = []
    try:
        tree = ET.parse(filepath)
    except ET.ParseError:
        return []
    root = tree.getroot()

    # Collect Sanskrit titles
    sanskrit_titles: list[str] = []
    for title_el in root.iter("{http://www.tei-c.org/ns/1.0}title"):
        lang = title_el.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        if lang == "Sa-Ltn":
            text = "".join(title_el.itertext()).strip()
            if text:
                sanskrit_titles.append(text)

    if not sanskrit_titles:
        return []

    # Main Sanskrit title is the first mainTitle with Sa-Ltn,
    # but we collect all as variants
    main_skt = sanskrit_titles[0]

    # Get Tohoku numbers from bibl elements
    toh_nums: list[int] = []
    for bibl in root.iter("{http://www.tei-c.org/ns/1.0}bibl"):
        key = bibl.get("key", "")
        if key.startswith("toh"):
            m = re.match(r"toh(\d+)", key)
            if m:
                toh_nums.append(int(m.group(1)))

    # Fallback: parse from filename
    if not toh_nums:
        toh_nums = _parse_toh_from_filename(filepath.name)

    for toh in toh_nums:
        results.append((toh, main_skt, str(filepath)))

    # Also record alternate Sanskrit titles for the same Toh numbers
    return results


def load_kangyur_sanskrit_titles() -> list[tuple[int, str, str]]:
    """Load Sanskrit titles for Kangyur/Tengyur texts.

    Returns: list of (tohoku_number, original_title, source) tuples.
    """
    root = _project_root()
    # Collect (tohoku_number, original_title, source)
    all_entries: list[tuple[int, str, str]] = []

    # --- 84000 TEI: Kangyur ---
    kangyur_dir = root / "84000-data-tei" / "translations" / "kangyur"
    if kangyur_dir.exists():
        for subdir in ("placeholders", "translations"):
            d = kangyur_dir / subdir
            if d.exists():
                for fpath in sorted(d.glob("*.xml")):
                    entries = _parse_84000_tei(fpath)
                    for toh, skt, src in entries:
                        all_entries.append((toh, skt, f"84000-kangyur/{subdir}"))

    # --- 84000 TEI: Tengyur ---
    tengyur_dir = root / "84000-data-tei" / "translations" / "tengyur"
    if tengyur_dir.exists():
        for subdir in ("placeholders", "translations"):
            d = tengyur_dir / subdir
            if d.exists():
                for fpath in sorted(d.glob("*.xml")):
                    entries = _parse_84000_tei(fpath)
                    for toh, skt, src in entries:
                        all_entries.append((toh, skt, f"84000-tengyur/{subdir}"))

    # --- CBETA Jinglu Tibetan ---
    # These are Tibetan catalogue entries with Sanskrit titles.
    # They don't always have Tohoku numbers, but the entry_number serves
    # as a CBETA Tibetan catalogue ID. We use them as a Kangyur/Tengyur-side
    # source since they represent the Tibetan canon's view.
    cbeta_tib_path = root / "results" / "cbeta_jinglu_tibetan.json"
    if cbeta_tib_path.exists():
        with open(cbeta_tib_path) as f:
            data = json.load(f)
        for eid, entry in data.get("entries", {}).items():
            skt = entry.get("sanskrit_title", "")
            if not skt:
                continue
            entry_num = entry.get("entry_number", 0)
            # Use negative numbers for CBETA Tibetan entries (no real Toh number)
            # to distinguish them from real Tohoku numbers
            toh_id = -entry_num  # placeholder
            all_entries.append((toh_id, skt, f"cbeta-tibetan/{eid}"))

    return all_entries


def _build_norm_index(
    entries: list[tuple[int, str, str]],
) -> dict[str, list[tuple[int, str, str]]]:
    """Build {normalized_title: [(toh, original_title, source), ...]} index."""
    idx: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for toh, skt, src in entries:
        norm = normalize_title(skt)
        if norm:
            idx[norm].append((toh, skt, src))
    return dict(idx)


# ---------------------------------------------------------------------------
# 4. Matching
# ---------------------------------------------------------------------------

def find_matches(
    taisho_titles: dict[str, list[str]],
    kangyur_entries: list[tuple[int, str, str]],
) -> list[dict[str, Any]]:
    """Find Sanskrit title matches between Taishō and Kangyur/Tengyur.

    Three-pass approach for efficiency:
      1. Exact match on normalised titles (O(n) hash lookups)
      2. Token match via inverted token index (avoids full pairwise)
      3. Fuzzy match: pre-compute norm→norm matches, then expand to entries

    Returns a list of match dicts.
    """
    # Build normalised indexes
    kangyur_idx = _build_norm_index(kangyur_entries)

    # --- Build Taishō normalised index: norm → [(tid, original_skt)] ---
    taisho_norm_idx: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for tid, skt_list in taisho_titles.items():
        for skt in skt_list:
            norm = normalize_title(skt)
            if norm:
                taisho_norm_idx[norm].append((tid, skt))

    # Pre-compute kangyur token sets keyed by normalised title
    kangyur_tokens: dict[str, set[str]] = {}
    for norm, entries in kangyur_idx.items():
        toks = tokenize_title(entries[0][1])
        if toks:
            kangyur_tokens[norm] = toks

    # Pre-compute taisho token sets
    taisho_tokens: dict[str, set[str]] = {}
    for t_norm, entries in taisho_norm_idx.items():
        toks = tokenize_title(entries[0][1])
        if toks:
            taisho_tokens[t_norm] = toks

    # Build inverted token index: token → set of kangyur normalised titles
    token_to_knorms: dict[str, set[str]] = defaultdict(set)
    for k_norm, toks in kangyur_tokens.items():
        for tok in toks:
            token_to_knorms[tok].add(k_norm)

    # Pre-compute kangyur norm lengths for fuzzy filtering
    kangyur_norms_by_len: dict[int, list[str]] = defaultdict(list)
    for k_norm in kangyur_idx:
        kangyur_norms_by_len[len(k_norm)].append(k_norm)
    sorted_lengths = sorted(kangyur_norms_by_len.keys())

    # ---------------------------------------------------------------
    # Pass 1: Exact matches (norm-level)
    # ---------------------------------------------------------------
    # norm_matches: {(t_norm, k_norm): (match_type, score)}
    norm_matches: dict[tuple[str, str], tuple[str, float]] = {}
    for t_norm in taisho_norm_idx:
        if t_norm in kangyur_idx:
            norm_matches[(t_norm, t_norm)] = ("exact", 1.0)

    # ---------------------------------------------------------------
    # Pass 2: Token matches via inverted index (norm-level)
    # ---------------------------------------------------------------
    for t_norm, t_toks in taisho_tokens.items():
        if not t_toks:
            continue
        candidate_knorms: set[str] = set()
        for tok in t_toks:
            candidate_knorms.update(token_to_knorms.get(tok, set()))
        candidate_knorms.discard(t_norm)  # skip exact

        for k_norm in candidate_knorms:
            if (t_norm, k_norm) in norm_matches:
                continue
            k_toks = kangyur_tokens.get(k_norm)
            if not k_toks:
                continue
            jacc = jaccard_similarity(t_toks, k_toks)
            if jacc >= 0.7:
                norm_matches[(t_norm, k_norm)] = ("token", round(jacc, 4))

    # ---------------------------------------------------------------
    # Pass 3: Fuzzy matches (norm-level, length-filtered)
    # ---------------------------------------------------------------
    for t_norm in taisho_norm_idx:
        norm_len = len(t_norm)
        if norm_len < 5:
            continue
        # For ratio >= FUZZY_THRESHOLD, length difference bounded
        min_len = int(norm_len * FUZZY_THRESHOLD)
        max_len = int(norm_len / FUZZY_THRESHOLD) + 1

        for klen in sorted_lengths:
            if klen < min_len:
                continue
            if klen > max_len:
                break
            for k_norm in kangyur_norms_by_len[klen]:
                if k_norm == t_norm:
                    continue
                if (t_norm, k_norm) in norm_matches:
                    continue
                ratio = levenshtein_ratio_threshold(t_norm, k_norm, FUZZY_THRESHOLD)
                if ratio >= FUZZY_THRESHOLD:
                    norm_matches[(t_norm, k_norm)] = ("fuzzy", round(ratio, 4))

    # ---------------------------------------------------------------
    # Expand norm-level matches to entry-level matches
    # ---------------------------------------------------------------
    matches: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    exact_pairs: set[tuple[str, int]] = set()

    # Process exact matches first so we can skip them later
    for (t_norm, k_norm), (mtype, score) in sorted(
        norm_matches.items(), key=lambda x: (x[1][0] != "exact", -x[1][1])
    ):
        for tid, t_skt in taisho_norm_idx[t_norm]:
            for toh, k_skt, src in kangyur_idx[k_norm]:
                if mtype == "exact":
                    key = (tid, toh, "exact")
                    if key not in seen:
                        seen.add(key)
                        exact_pairs.add((tid, toh))
                        matches.append({
                            "taisho_id": tid,
                            "tohoku": toh,
                            "taisho_sanskrit": t_skt,
                            "kangyur_sanskrit": k_skt,
                            "match_type": "exact",
                            "match_score": 1.0,
                            "sources": [src],
                        })
                else:
                    if (tid, toh) in exact_pairs:
                        continue
                    key = (tid, toh, mtype)
                    if key not in seen:
                        seen.add(key)
                        matches.append({
                            "taisho_id": tid,
                            "tohoku": toh,
                            "taisho_sanskrit": t_skt,
                            "kangyur_sanskrit": k_skt,
                            "match_type": mtype,
                            "match_score": score,
                            "sources": [src],
                        })

    return matches


# ---------------------------------------------------------------------------
# 4b. Section mismatch detection
# ---------------------------------------------------------------------------

# Tohoku number boundaries
_KANGYUR_MAX_TOH = 1108
_TENGYUR_MIN_TOH = 1109

# Taishō volume boundaries for sūtra vs. śāstra sections
_TAISHO_SUTRA_MAX_VOL = 21
_TAISHO_SASTRA_MIN_VOL = 25
_TAISHO_SASTRA_MAX_VOL = 32


def _taisho_vol_from_id(taisho_id: str) -> int:
    """Extract volume number from canonical TXXnNNNN ID."""
    m = re.match(r"T(\d{2})n\d{4}", taisho_id)
    return int(m.group(1)) if m else 0


def _is_section_mismatch(taisho_id: str, tohoku: int, match_type: str) -> str | None:
    """Check whether a match crosses sūtra/commentary section boundaries.

    Only applies to fuzzy and token matches — exact cross-section matches
    are preserved (they likely reflect genuine parallels with variant titles).

    Returns a reason string if mismatched, or None if OK.
    """
    if match_type == "exact":
        return None
    if tohoku <= 0:
        return None

    vol = _taisho_vol_from_id(taisho_id)
    if vol == 0:
        return None

    is_taisho_sutra = vol <= _TAISHO_SUTRA_MAX_VOL
    is_taisho_sastra = _TAISHO_SASTRA_MIN_VOL <= vol <= _TAISHO_SASTRA_MAX_VOL
    is_kangyur = tohoku <= _KANGYUR_MAX_TOH
    is_tengyur = tohoku >= _TENGYUR_MIN_TOH

    if is_taisho_sutra and is_tengyur:
        return f"sūtra text (vol {vol}) matched Tengyur commentary (Toh {tohoku})"
    if is_taisho_sastra and is_kangyur:
        return f"śāstra text (vol {vol}) matched Kangyur sūtra (Toh {tohoku})"

    return None


def annotate_section_preference(matches: list[dict[str, Any]]) -> None:
    """Annotate matches with section preference metadata.

    When a Taishō sūtra text (vol 1-21) has both Kangyur and Tengyur matches,
    the Tengyur matches get ``section_demoted=True``.  This is purely
    informational — no matches are removed.
    """
    # Group matches by taisho_id
    by_tid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in matches:
        by_tid[m["taisho_id"]].append(m)

    for tid, group in by_tid.items():
        vol = _taisho_vol_from_id(tid)
        if vol == 0 or vol > _TAISHO_SUTRA_MAX_VOL:
            continue
        has_kangyur = any(
            0 < m["tohoku"] <= _KANGYUR_MAX_TOH for m in group
        )
        if not has_kangyur:
            continue
        for m in group:
            if m["tohoku"] >= _TENGYUR_MIN_TOH:
                m["section_demoted"] = True


# ---------------------------------------------------------------------------
# 5. Validation against existing concordance
# ---------------------------------------------------------------------------

def load_concordance() -> dict[str, set[int]]:
    """Load existing concordance: {taisho_id: set of Tohoku numbers}."""
    root = _project_root()
    conc_path = root / "results" / "cross_reference_expanded.json"
    if not conc_path.exists():
        return {}
    with open(conc_path) as f:
        data = json.load(f)
    result: dict[str, set[int]] = {}
    for tid, parallels in data.get("tibetan_parallels", {}).items():
        tohs: set[int] = set()
        for p in parallels:
            m = re.match(r"Toh (\d+)", str(p))
            if m:
                tohs.add(int(m.group(1)))
        if tohs:
            result[tid] = tohs
    return result


def validate_matches(
    matches: list[dict[str, Any]],
    concordance: dict[str, set[int]],
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Validate matches against existing concordance.

    Returns (validated, contradicted, new_proposals, filtered).
    - validated: match confirms a known Taisho→Tohoku mapping
    - contradicted: match proposes a Toh for a text that has a DIFFERENT Toh in concordance
    - new_proposals: text has no Toh mapping in concordance, or this is a new Toh
    - filtered: matches removed due to section mismatch (sūtra↔commentary)
    """
    validated = []
    contradicted = []
    new_proposals = []
    filtered = []

    for m in matches:
        tid = m["taisho_id"]
        toh = m["tohoku"]
        if toh < 0:
            # CBETA Tibetan catalogue entry, not a real Toh number
            # Skip for validation purposes
            continue

        # Check for section mismatch before concordance lookup
        reason = _is_section_mismatch(tid, toh, m["match_type"])
        if reason:
            m_copy = dict(m)
            m_copy["filter_reason"] = reason
            filtered.append(m_copy)
            continue

        known_tohs = concordance.get(tid, set())
        if not known_tohs:
            new_proposals.append(m)
        elif toh in known_tohs:
            validated.append(m)
        else:
            # This Taishō text has known Toh mappings, but NOT this one
            m_copy = dict(m)
            m_copy["known_tohoku"] = sorted(known_tohs)
            contradicted.append(m_copy)

    return validated, contradicted, new_proposals, filtered


# ---------------------------------------------------------------------------
# 6. Reporting
# ---------------------------------------------------------------------------

_PRAJNA_TEXTS = [
    "T08n0234", "T08n0245", "T08n0246", "T08n0247", "T08n0259", "T08n0261",
]


def _format_toh(toh: int) -> str:
    """Format Tohoku number, handling CBETA placeholders."""
    if toh < 0:
        return f"CBETA-Tib-{-toh}"
    return f"Toh {toh}"


def print_report(
    validated: list[dict],
    contradicted: list[dict],
    new_proposals: list[dict],
    total_matches: int,
    taisho_count: int,
    kangyur_count: int,
    filtered: list[dict] | None = None,
) -> None:
    """Print a human-readable summary report."""
    if filtered is None:
        filtered = []
    all_active = validated + contradicted + new_proposals
    exact = sum(1 for m in all_active if m["match_type"] == "exact")
    token = sum(1 for m in all_active if m["match_type"] == "token")
    fuzzy = sum(1 for m in all_active if m["match_type"] == "fuzzy")

    print("=" * 72)
    print("SANSKRIT TITLE MATCHING PIPELINE — RESULTS")
    print("=" * 72)
    print()
    print(f"  Taishō texts with Sanskrit titles:      {taisho_count:>6}")
    print(f"  Kangyur/Tengyur entries with Sanskrit:   {kangyur_count:>6}")
    print()
    print(f"  Total matches (real Toh only):           {total_matches:>6}")
    print(f"    Exact matches:                         {exact:>6}")
    print(f"    Token matches (Jaccard >= 0.7):        {token:>6}")
    print(f"    Fuzzy matches (Levenshtein >= {FUZZY_THRESHOLD}):"
          f"   {fuzzy:>6}")
    print()
    print("-" * 72)
    print("VALIDATION AGAINST EXISTING CONCORDANCE")
    print("-" * 72)
    print()
    val_rate = (
        len(validated) / (len(validated) + len(contradicted))
        if (len(validated) + len(contradicted)) > 0
        else 0.0
    )
    print(f"  Confirmed (match agrees with concordance):   {len(validated):>5}")
    print(f"  Contradicted (match disagrees):              {len(contradicted):>5}")
    print(f"  Filtered (section mismatch):                 {len(filtered):>5}")
    print(f"  Validation rate:                             {val_rate:>5.1%}")
    print()

    if filtered:
        print("  Section-filtered matches:")
        for m in filtered[:10]:
            print(
                f"    {m['taisho_id']} → {_format_toh(m['tohoku'])} "
                f"({m['match_type']}): {m.get('filter_reason', '')}"
            )
        print()

    if contradicted:
        print("  Top contradictions:")
        for m in contradicted[:10]:
            known = ", ".join(f"Toh {t}" for t in m.get("known_tohoku", []))
            print(
                f"    {m['taisho_id']}: title match → {_format_toh(m['tohoku'])}, "
                f"concordance has {known}"
            )
            print(
                f"      T: {m['taisho_sanskrit'][:60]}"
            )
            print(
                f"      K: {m['kangyur_sanskrit'][:60]}"
            )
        print()

    print("-" * 72)
    print("NEW PROPOSALS")
    print("-" * 72)
    print()
    # Deduplicate by (taisho_id, toh) for reporting
    seen_proposals: set[tuple[str, int]] = set()
    unique_proposals: list[dict] = []
    for p in new_proposals:
        key = (p["taisho_id"], p["tohoku"])
        if key not in seen_proposals:
            seen_proposals.add(key)
            unique_proposals.append(p)
    unique_taisho = len({p["taisho_id"] for p in unique_proposals})
    print(f"  Unique new Taisho→Toh proposals:   {len(unique_proposals):>5}")
    print(f"  Covering unique Taishō texts:      {unique_taisho:>5}")
    print()

    if unique_proposals:
        print("  Sample proposals (first 20):")
        for m in unique_proposals[:20]:
            print(
                f"    {m['taisho_id']} → {_format_toh(m['tohoku'])} "
                f"({m['match_type']}, score={m['match_score']:.2f})"
            )
            print(f"      T: {m['taisho_sanskrit'][:70]}")
            print(f"      K: {m['kangyur_sanskrit'][:70]}")
        print()

    # Special report for Prajñāpāramitā texts
    print("-" * 72)
    print("PRAJNAPARAMITA FOCUS TEXTS")
    print("-" * 72)
    print()
    for tid in _PRAJNA_TEXTS:
        prajna_matches = [
            m for m in validated + contradicted + new_proposals
            if m["taisho_id"] == tid
        ]
        if prajna_matches:
            print(f"  {tid}:")
            for m in prajna_matches:
                cat = "CONFIRMED" if m in validated else (
                    "CONTRADICTED" if m in contradicted else "NEW"
                )
                print(
                    f"    [{cat}] → {_format_toh(m['tohoku'])} "
                    f"({m['match_type']}, {m['match_score']:.2f})"
                )
                print(f"      T: {m['taisho_sanskrit'][:70]}")
                print(f"      K: {m['kangyur_sanskrit'][:70]}")
        else:
            print(f"  {tid}: no Sanskrit title matches found")
    print()
    print("=" * 72)


def save_results(
    validated: list[dict],
    contradicted: list[dict],
    new_proposals: list[dict],
    output_path: Path,
    filtered: list[dict] | None = None,
) -> None:
    """Save detailed results to JSON."""
    if filtered is None:
        filtered = []
    all_active = validated + contradicted + new_proposals
    exact_count = sum(1 for m in all_active if m["match_type"] == "exact")
    token_count = sum(1 for m in all_active if m["match_type"] == "token")
    fuzzy_count = sum(1 for m in all_active if m["match_type"] == "fuzzy")

    val_rate = (
        len(validated) / (len(validated) + len(contradicted))
        if (len(validated) + len(contradicted)) > 0
        else 0.0
    )

    # Convert sets to lists for JSON serialisation
    def _serialise(m: dict) -> dict:
        out = dict(m)
        if "known_tohoku" in out:
            out["known_tohoku"] = sorted(out["known_tohoku"])
        return out

    result = {
        "validated": [_serialise(m) for m in validated],
        "contradicted": [_serialise(m) for m in contradicted],
        "new_proposals": [_serialise(m) for m in new_proposals],
        "filtered": [_serialise(m) for m in filtered],
        "validation_rate": round(val_rate, 4),
        "total_exact_matches": exact_count,
        "total_token_matches": token_count,
        "total_fuzzy_matches": fuzzy_count,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results written to: {output_path}")


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Sanskrit title matching pipeline."""
    root = _project_root()
    output_path = root / "results" / "sanskrit_title_matches.json"

    print("Loading Taishō Sanskrit titles...")
    taisho_titles = load_taisho_sanskrit_titles()
    print(f"  {len(taisho_titles)} Taishō texts with Sanskrit titles")

    print("Loading Kangyur/Tengyur Sanskrit titles...")
    kangyur_entries = load_kangyur_sanskrit_titles()
    # Count unique real Toh numbers
    real_toh = {e[0] for e in kangyur_entries if e[0] > 0}
    cbeta_tib = {e[0] for e in kangyur_entries if e[0] < 0}
    print(
        f"  {len(real_toh)} unique Tohoku texts + "
        f"{len(cbeta_tib)} CBETA Tibetan entries"
    )

    print("\nMatching titles...")
    all_matches = find_matches(taisho_titles, kangyur_entries)
    # Filter to real Toh numbers for main reporting
    real_matches = [m for m in all_matches if m["tohoku"] > 0]
    print(f"  {len(real_matches)} matches with real Tohoku numbers")

    print("Annotating section preferences...")
    annotate_section_preference(real_matches)

    print("\nValidating against concordance...")
    concordance = load_concordance()
    validated, contradicted, new_proposals, filtered = validate_matches(
        real_matches, concordance
    )

    print()
    print_report(
        validated,
        contradicted,
        new_proposals,
        total_matches=len(real_matches),
        taisho_count=len(taisho_titles),
        kangyur_count=len(real_toh) + len(cbeta_tib),
        filtered=filtered,
    )

    save_results(validated, contradicted, new_proposals, output_path,
                 filtered=filtered)


if __name__ == "__main__":
    main()
