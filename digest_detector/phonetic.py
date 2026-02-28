"""Phonetic equivalence table for Sanskrit transliteration detection.

Parses the DDB dictionary to build a mapping from Chinese characters to
Sanskrit syllable values, enabling detection of phonetically equivalent
dharani passages that use different characters for the same Sanskrit sounds.
"""

import json
import logging
import re
import unicodedata
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

# Default path to DDB dictionary
DDB_PATH = config.BASE_DIR / "sc-data" / "dictionaries" / "simple" / "en" / "lzh2en_ddb.json"

# Common Buddhist prose characters that enter the phonetic table via
# positional alignment of mixed semantic+phonetic compounds (e.g. 梵天外道
# brahmadeva maps 天→ma, 道→va). These are too frequent in ordinary prose
# to be reliable phonetic indicators and would add noise to transliteration
# detection. Identified by reviewing the table for false equivalence pairs.
_COMMON_PROSE_EXCLUSIONS = frozenset(
    '無一大佛法人世天空色善道得行知說想相'
)


def _is_cjk(ch: str) -> bool:
    """Check if a character is a CJK ideograph."""
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or
            0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or
            0xF900 <= cp <= 0xFAFF)


def _cjk_chars(text: str) -> str:
    """Extract only CJK characters from a string."""
    return ''.join(ch for ch in text if _is_cjk(ch))


def _normalize_sanskrit(skt: str) -> str:
    """Normalize a Sanskrit term for syllable splitting.

    Strips diacritics for comparison, lowercases, removes hyphens.
    """
    # Decompose unicode to separate base chars from combining marks
    decomposed = unicodedata.normalize('NFD', skt.lower())
    # Remove combining marks (diacritics) but keep base letters
    stripped = ''.join(ch for ch in decomposed
                       if unicodedata.category(ch) != 'Mn')
    # Remove hyphens and spaces
    stripped = stripped.replace('-', '').replace(' ', '')
    return stripped


def _split_syllables(skt: str) -> list[str]:
    """Split a normalized Sanskrit term into syllables.

    Uses a simple heuristic: each consonant cluster followed by a vowel
    (and optional trailing consonants) forms one syllable. This gives a
    rough 1:1 alignment with Chinese transliteration characters.

    For example:
        "gandharva" → ["gan", "dhar", "va"]
        "gate" → ["ga", "te"]
        "paragate" → ["pa", "ra", "ga", "te"]
        "bodhi" → ["bo", "dhi"]
        "svaha" → ["sva", "ha"]
    """
    skt = _normalize_sanskrit(skt)
    if not skt:
        return []

    vowels = set('aeiou')
    syllables = []
    current = []

    i = 0
    while i < len(skt):
        ch = skt[i]
        current.append(ch)

        if ch in vowels:
            # Peek ahead: consume trailing consonants that are followed
            # by another consonant (i.e., they close this syllable)
            j = i + 1
            while j < len(skt) and skt[j] not in vowels:
                # If the next-next char is a vowel, this consonant starts
                # the next syllable
                if j + 1 < len(skt) and skt[j + 1] in vowels:
                    break
                # If this is the last char, it closes this syllable
                if j + 1 >= len(skt):
                    current.append(skt[j])
                    j += 1
                    break
                # Otherwise this consonant closes the current syllable
                current.append(skt[j])
                j += 1

            syllables.append(''.join(current))
            current = []
            i = j
        else:
            i += 1

    # Any remaining characters form a final syllable
    if current:
        syllables.append(''.join(current))

    return syllables


_INDIC_DIACRITICS = set('āīūṛṝḷḹṃṁḥśṣṇṭḍñṅ')
_INDIC_LETTER_PATTERN = re.compile(
    r'^[a-zāīūṛṝḷḹṃṁḥśṣṇṭḍñṅ\-]+$'
)


def _extract_sanskrit(definition: str) -> str | None:
    """Extract Sanskrit term from a DDB definition string.

    Extracts from:
    1. Explicit (Skt. ...) markers
    2. Bare lowercase terms containing Indic diacritics (clearly Sanskrit)

    Returns None if no Sanskrit term is found.
    """
    # Pattern 1: explicit (Skt. ...) marker
    m = re.search(r'\(Skt\.\s*\*?([^)]+)\)', definition)
    if m:
        skt = m.group(1).strip()
        # Take only the first word (drop English glosses like "heaven")
        parts = skt.split()
        if parts:
            return parts[0]

    # Pattern 2: bare lowercase term with Indic diacritics
    stripped = definition.strip().rstrip(';').strip()
    if _INDIC_LETTER_PATTERN.match(stripped):
        if any(ch in _INDIC_DIACRITICS for ch in stripped):
            return stripped

    return None


def build_equivalence_table(ddb_path: Path = None) -> dict[str, set[str]]:
    """Build a mapping from Chinese characters to Sanskrit syllable values.

    Parses 2-4 character DDB entries with Sanskrit references, positionally
    aligns characters to syllables, and builds a table where each Chinese
    character maps to the set of Sanskrit syllables it has been used to
    represent.

    Args:
        ddb_path: Path to the DDB dictionary JSON file.

    Returns:
        Dictionary mapping Chinese character → set of Sanskrit syllable strings.
        E.g. {'揭': {'ga'}, '帝': {'ti', 'te', 'di'}, ...}
    """
    if ddb_path is None:
        ddb_path = DDB_PATH

    with open(ddb_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    char_to_syllables: dict[str, set[str]] = {}

    for entry in entries:
        chinese = _cjk_chars(entry.get('entry', ''))
        definition = entry.get('definition', '')

        # Only process 2-4 character entries (best for positional alignment)
        if not (2 <= len(chinese) <= 4):
            continue

        skt = _extract_sanskrit(definition)
        if not skt:
            continue

        syllables = _split_syllables(skt)

        # Only align when character count matches syllable count
        if len(syllables) != len(chinese):
            continue

        for ch, syl in zip(chinese, syllables):
            if ch not in char_to_syllables:
                char_to_syllables[ch] = set()
            char_to_syllables[ch].add(syl)

    # Filter out common prose characters that contaminate the table
    prose_removed = [ch for ch in char_to_syllables if ch in _COMMON_PROSE_EXCLUSIONS]
    for ch in prose_removed:
        del char_to_syllables[ch]

    # Filter out overly ambiguous characters (too many syllable values)
    max_syls = config.PHONETIC_MAX_SYLLABLES
    ambiguous = [ch for ch, syls in char_to_syllables.items()
                 if len(syls) > max_syls]
    for ch in ambiguous:
        del char_to_syllables[ch]

    logger.info("Built phonetic equivalence table: %d chars, %d syllable groups "
                "(%d ambiguous, %d common prose chars removed)",
                len(char_to_syllables),
                len(get_equivalence_groups(char_to_syllables)),
                len(ambiguous), len(prose_removed))

    return char_to_syllables


def canonical_syllable(ch: str, table: dict[str, set[str]]) -> str | None:
    """Return the canonical (alphabetically first) syllable for a character.

    Args:
        ch: A single Chinese character.
        table: Equivalence table from build_equivalence_table().

    Returns:
        The alphabetically first syllable string, or None if the character
        is not in the table.
    """
    syls = table.get(ch)
    if not syls:
        return None
    return sorted(syls)[0]


def find_transliteration_regions(
    text: str,
    table: dict[str, set[str]],
    dharani_ranges: list[tuple[int, int]] | None = None,
    window: int | None = None,
    density_threshold: float | None = None,
) -> list[tuple[int, int]]:
    """Find transliteration-dense regions in text.

    Combines XML-annotated dharani ranges with density-based detection.
    Returns sorted, merged (start, end) ranges.

    Args:
        text: The full text to scan.
        table: Equivalence table from build_equivalence_table().
        dharani_ranges: Pre-annotated dharani ranges from XML extraction.
        window: Sliding window size for density detection (default from config).
        density_threshold: Min fraction of table chars in a window (default from config).
    """
    if window is None:
        window = config.TRANSLITERATION_WINDOW
    if density_threshold is None:
        density_threshold = config.TRANSLITERATION_DENSITY

    regions = []

    # Source 1: XML-annotated dharani ranges
    if dharani_ranges:
        regions.extend(dharani_ranges)

    # Source 2: Density-based detection using incremental sliding window.
    # Maintains a running count of table chars, incrementing/decrementing as
    # characters enter/leave the window, for O(n) instead of O(n*w).
    if len(text) >= window:
        in_region = False
        region_start = 0
        min_count = int(density_threshold * window)

        # Initialize count for first window
        table_count = sum(1 for ch in text[:window] if ch in table)

        for i in range(len(text) - window + 1):
            if i > 0:
                # Remove char leaving the window, add char entering
                if text[i - 1] in table:
                    table_count -= 1
                if text[i + window - 1] in table:
                    table_count += 1

            if table_count >= min_count:
                if not in_region:
                    region_start = i
                    in_region = True
            else:
                if in_region:
                    regions.append((region_start, i + window - 1))
                    in_region = False

        if in_region:
            regions.append((region_start, len(text)))

    # Sort and merge overlapping regions
    if not regions:
        return []

    regions.sort()
    merged = [regions[0]]
    for start, end in regions[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def text_to_syllable_ngrams(
    text: str,
    regions: list[tuple[int, int]],
    table: dict[str, set[str]],
    n: int | None = None,
) -> list[tuple[str, int]]:
    """Convert transliteration regions to syllable n-gram hashes.

    For each region, maps characters to their canonical syllable (or "_"
    for non-table characters), then generates sliding n-gram windows of
    syllable sequences.

    Args:
        text: The full text.
        regions: Transliteration regions as (start, end) offsets.
        table: Equivalence table from build_equivalence_table().
        n: Syllable n-gram size (default from config).

    Returns:
        List of (ngram_string, char_position) tuples, where ngram_string
        is a dash-joined canonical syllable sequence and char_position is
        the offset in text where the n-gram starts.
    """
    if n is None:
        n = config.PHONETIC_NGRAM_SIZE

    results = []

    # Precompute canonical syllable for each char in the table (avoids
    # repeated sorted() calls inside canonical_syllable per character)
    canonical = {ch: sorted(syls)[0] for ch, syls in table.items()}

    for reg_start, reg_end in regions:
        # Build syllable sequence for this region
        syllables = []  # (canonical_syllable, char_position)
        for i in range(reg_start, min(reg_end, len(text))):
            syl = canonical.get(text[i])
            if syl is not None:
                syllables.append((syl, i))

        # Generate n-grams from consecutive syllable positions
        for i in range(len(syllables) - n + 1):
            window = syllables[i:i + n]
            ngram = "-".join(s for s, _ in window)
            pos = window[0][1]
            results.append((ngram, pos))

    return results


def are_phonetically_equivalent(a: str, b: str,
                                 table: dict[str, set[str]]) -> bool:
    """Check if two Chinese characters are phonetically equivalent.

    Two characters are equivalent if they share at least one Sanskrit
    syllable value in the equivalence table.

    Args:
        a: First Chinese character.
        b: Second Chinese character.
        table: Equivalence table from build_equivalence_table().

    Returns:
        True if the characters share a Sanskrit syllable mapping.
    """
    if a == b:
        return True
    syls_a = table.get(a, set())
    syls_b = table.get(b, set())
    if not syls_a or not syls_b:
        return False
    return bool(syls_a & syls_b)


def get_equivalence_groups(table: dict[str, set[str]]) -> dict[str, set[str]]:
    """Invert the equivalence table: Sanskrit syllable → set of Chinese chars.

    Args:
        table: Equivalence table from build_equivalence_table().

    Returns:
        Dictionary mapping Sanskrit syllable → set of Chinese characters
        that represent it.
    """
    groups: dict[str, set[str]] = {}
    for ch, syllables in table.items():
        for syl in syllables:
            if syl not in groups:
                groups[syl] = set()
            groups[syl].add(ch)
    return groups


def phonetic_mapping_for_pair(
    digest_text: str,
    source_text: str,
    table: dict[str, set[str]],
) -> list[tuple[str, str, str]]:
    """Build char-by-char phonetic mapping for an aligned pair of strings.

    Both strings must be the same length. For each position, finds the
    shared Sanskrit syllable (if any).

    Args:
        digest_text: Characters from the digest.
        source_text: Characters from the source.
        table: Equivalence table.

    Returns:
        List of (digest_char, sanskrit_syllable, source_char) triples.
        If a position has no shared syllable, sanskrit_syllable is "?".
    """
    if len(digest_text) != len(source_text):
        raise ValueError(
            f"phonetic_mapping_for_pair requires equal-length strings, "
            f"got {len(digest_text)} and {len(source_text)}"
        )
    mapping = []
    for d_ch, s_ch in zip(digest_text, source_text):
        if d_ch == s_ch:
            # Exact match — find syllable if available
            syls = table.get(d_ch, set())
            syl = sorted(syls)[0] if syls else "="
            mapping.append((d_ch, syl, s_ch))
        else:
            syls_d = table.get(d_ch, set())
            syls_s = table.get(s_ch, set())
            shared = syls_d & syls_s
            syl = sorted(shared)[0] if shared else "?"
            mapping.append((d_ch, syl, s_ch))
    return mapping
