"""Stage 2b: Candidate pair selection via containment scoring.

For each potential digest text (shorter texts), computes asymmetric
containment against all longer texts using the inverted index, and
also incorporates docNumber cross-references.
"""

import logging
import re
from collections import defaultdict

from . import config
from .models import ExtractedText, CandidatePair, TextMetadata

logger = logging.getLogger(__name__)


def _parse_docnumber_to_text_ids(
    metadata_map: dict[str, TextMetadata],
) -> dict[str, set[str]]:
    """Build a map from docnumber → set of text_ids that reference it.

    This lets us find cross-referenced texts. E.g., T08n0250's docNumber
    says "No. 250 [Nos. 251-255, 257]", so docnumber "251" maps to "T08n0250".
    """
    docnum_to_texts = defaultdict(set)

    for text_id, meta in metadata_map.items():
        # Extract volume prefix for matching (e.g., "T08" from "T08n0250")
        vol_match = re.match(r'(T\d+)n(\d+)', text_id)
        if not vol_match:
            continue
        vol_prefix = vol_match.group(1)
        main_num = vol_match.group(2)

        # The text references itself
        docnum_to_texts[f"{vol_prefix}:{main_num}"].add(text_id)

        # It also references these other docnumbers
        for ref in meta.docnumber_refs:
            docnum_to_texts[f"{vol_prefix}:{ref}"].add(text_id)

    return dict(docnum_to_texts)


def _find_docnumber_pairs(
    metadata_map: dict[str, TextMetadata],
) -> list[tuple[str, str]]:
    """Find all text pairs connected by docNumber cross-references.

    Returns (shorter_text_id, longer_text_id) pairs.
    """
    docnum_map = _parse_docnumber_to_text_ids(metadata_map)
    pairs = set()

    for docnum, text_ids in docnum_map.items():
        text_list = sorted(text_ids)
        for i in range(len(text_list)):
            for j in range(i + 1, len(text_list)):
                t1, t2 = text_list[i], text_list[j]
                # Ensure both texts exist in metadata
                if t1 in metadata_map and t2 in metadata_map:
                    # Order by size: shorter first (potential digest)
                    c1 = metadata_map[t1].char_count
                    c2 = metadata_map[t2].char_count
                    if c1 <= c2:
                        pairs.add((t1, t2))
                    else:
                        pairs.add((t2, t1))

    return list(pairs)


def generate_candidates(
    texts: list[ExtractedText],
    inverted_index: dict[int, list[tuple[str, int]]],
    stopgrams: set[int],
) -> list[CandidatePair]:
    """Generate candidate digest-source pairs using containment scoring.

    For each potential digest (shorter text), looks up its n-grams in the
    inverted index and counts matches against each candidate source (longer text).
    Also includes pairs from docNumber cross-references.
    """
    n = config.NGRAM_SIZE
    max_digest_len = config.MAX_DIGEST_LENGTH
    min_containment = config.MIN_CONTAINMENT
    min_size_ratio = config.MIN_SIZE_RATIO

    # Build lookup structures
    text_map = {t.text_id: t for t in texts}
    metadata_map = {t.text_id: t.metadata for t in texts}
    length_map = {t.text_id: t.metadata.char_count for t in texts}

    # Find docNumber-based pairs
    docnum_pairs = _find_docnumber_pairs(metadata_map)
    docnum_pair_set = set(docnum_pairs)
    logger.info("Found %d docNumber cross-reference pairs", len(docnum_pairs))

    # Identify potential digests (texts short enough to be digests)
    digest_candidates = [
        t for t in texts
        if t.metadata.char_count <= max_digest_len
    ]
    logger.info("Evaluating %d potential digest texts (char_count <= %d)",
                len(digest_candidates), max_digest_len)

    candidates = []
    seen_pairs = set()

    for digest in digest_candidates:
        d_id = digest.text_id
        d_len = digest.metadata.char_count
        # The inverted index is built from full_text (so texts can serve as
        # sources using all their content), but we query using jing_text on the
        # digest side to exclude preface material that would dilute containment
        # scores.  This works because jing n-grams are a subset of full-text
        # n-grams.
        content = digest.jing_text

        if len(content) < n:
            continue

        # Count matching n-grams per candidate source
        match_counts = defaultdict(int)
        total_ngrams = 0

        for i in range(len(content) - n + 1):
            h = hash(content[i:i + n])
            if h in stopgrams:
                continue
            total_ngrams += 1
            if h in inverted_index:
                # Count each source text only once per n-gram position
                seen_sources = set()
                for source_id, _ in inverted_index[h]:
                    if source_id != d_id and source_id not in seen_sources:
                        seen_sources.add(source_id)
                        match_counts[source_id] += 1

        if total_ngrams == 0:
            continue

        # Score candidates
        for source_id, matching in match_counts.items():
            s_len = length_map.get(source_id, 0)

            # Source must be sufficiently longer than digest.
            # Note: d_len uses full-text char_count while fingerprinting uses
            # jing_text.  This is intentional: the filter is a coarse pre-filter
            # (2x ratio) and using full-text length is conservative (never
            # accidentally excludes valid sources).
            if s_len < d_len * min_size_ratio:
                continue

            containment = matching / total_ngrams
            pair_key = (d_id, source_id)

            if containment >= min_containment:
                seen_pairs.add(pair_key)
                candidates.append(CandidatePair(
                    digest_id=d_id,
                    source_id=source_id,
                    containment_score=containment,
                    matching_ngrams=matching,
                    total_digest_ngrams=total_ngrams,
                    from_docnumber=pair_key in docnum_pair_set,
                ))

    # Add docNumber pairs not already found by fingerprinting
    for d_id, s_id in docnum_pairs:
        pair_key = (d_id, s_id)
        if pair_key not in seen_pairs:
            d_text = text_map.get(d_id)
            s_text = text_map.get(s_id)
            if d_text and s_text:
                candidates.append(CandidatePair(
                    digest_id=d_id,
                    source_id=s_id,
                    containment_score=0.0,  # Will be computed in alignment
                    matching_ngrams=0,
                    total_digest_ngrams=0,
                    from_docnumber=True,
                ))
                seen_pairs.add(pair_key)

    # Sort by containment score descending
    candidates.sort(key=lambda c: c.containment_score, reverse=True)

    logger.info("Generated %d candidate pairs (%d from fingerprinting, %d from docNumber)",
                len(candidates),
                sum(1 for c in candidates if not c.from_docnumber or c.containment_score > 0),
                sum(1 for c in candidates if c.from_docnumber))

    return candidates
