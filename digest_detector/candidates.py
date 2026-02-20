"""Stage 2b: Candidate pair selection via containment scoring.

For each potential digest text (shorter texts), computes asymmetric
containment against all longer texts using n-gram set intersection,
and also incorporates docNumber cross-references and phonetic candidates.
"""

import logging
import re
from bisect import bisect_left
from collections import defaultdict
from multiprocessing import Pool

from . import config
from .fast import fast_ngram_hashes
from .fingerprint import stable_hash
from .models import ExtractedText, CandidatePair, TextMetadata
from .phonetic import find_transliteration_regions, text_to_syllable_ngrams

logger = logging.getLogger(__name__)

# --- Pool worker state (set via initializer, avoids per-task pickling) ---
_worker_table: dict[str, set[str]] = {}
_worker_min_region_len: int = 10

# --- Pool worker state for candidate generation (Stage 2) ---
_cand_stopgrams: set[int] = set()
_cand_source_ids: list[str] = []
_cand_source_lens: list[int] = []
_cand_source_sets: list[frozenset[int]] = []
_cand_n: int = 5
_cand_min_containment: float = 0.10
_cand_docnum_pair_set: set[tuple[str, str]] = set()


def _candidate_init(
    stopgrams: set[int],
    source_ids: list[str],
    source_lens: list[int],
    source_sets: list[frozenset[int]],
    n: int,
    min_containment: float,
    docnum_pair_set: set[tuple[str, str]],
):
    """Pool initializer: set shared data for candidate workers."""
    global _cand_stopgrams, _cand_source_ids, _cand_source_lens
    global _cand_source_sets, _cand_n, _cand_min_containment, _cand_docnum_pair_set
    _cand_stopgrams = stopgrams
    _cand_source_ids = source_ids
    _cand_source_lens = source_lens
    _cand_source_sets = source_sets
    _cand_n = n
    _cand_min_containment = min_containment
    _cand_docnum_pair_set = docnum_pair_set


def _candidate_worker(args: tuple) -> list[CandidatePair]:
    """Worker: score one digest against all qualifying sources."""
    d_id, jing_text, d_len, min_size_ratio = args
    n = _cand_n
    stopgrams = _cand_stopgrams
    min_containment = _cand_min_containment
    source_ids_arr = _cand_source_ids
    source_lens_arr = _cand_source_lens
    source_sets_arr = _cand_source_sets
    docnum_pair_set = _cand_docnum_pair_set

    if len(jing_text) < n:
        return []

    # Build digest's n-gram set from jing_text (not full_text).
    # This is intentionally asymmetric: digest uses jing_text to exclude
    # preface material, while source n-gram sets (in source_sets_arr) use
    # full_text so they can match against any digest content.
    digest_set = fast_ngram_hashes(jing_text, n, stopgrams)

    if not digest_set:
        return []
    min_source_len = d_len * min_size_ratio

    # Binary search for the first source meeting the size threshold.
    # source_lens_arr is sorted ascending, so all entries from lo onward qualify.
    lo = bisect_left(source_lens_arr, min_source_len)

    results = []
    for idx in range(lo, len(source_ids_arr)):
        source_id = source_ids_arr[idx]
        if source_id == d_id:
            continue

        matching = len(digest_set & source_sets_arr[idx])
        containment = matching / len(digest_set)
        # Used only for from_docnumber check, not deduplication
        pair_key = (d_id, source_id)

        if containment >= min_containment:
            results.append(CandidatePair(
                digest_id=d_id,
                source_id=source_id,
                containment_score=containment,
                matching_ngrams=matching,
                total_digest_ngrams=len(digest_set),
                from_docnumber=pair_key in docnum_pair_set,
            ))

    return results


def _phonetic_init(table: dict[str, set[str]], min_region_len: int):
    """Pool initializer: set shared phonetic table for all workers."""
    global _worker_table, _worker_min_region_len
    _worker_table = table
    _worker_min_region_len = min_region_len


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
        # Strip leading zeros so "0250" and "250" map to the same key
        main_num = vol_match.group(2).lstrip('0') or '0'

        # The text references itself
        docnum_to_texts[f"{vol_prefix}:{main_num}"].add(text_id)

        # It also references these other docnumbers
        for ref in meta.docnumber_refs:
            normalized_ref = ref.lstrip('0') or '0'
            docnum_to_texts[f"{vol_prefix}:{normalized_ref}"].add(text_id)

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


def _cleanup_candidate_globals():
    """Release references to large shared arrays after candidate generation.

    The module-level _cand_* globals are set by _candidate_init (parallel path)
    or directly (serial path). Clearing them after use prevents large arrays
    from persisting in memory for the rest of the pipeline.
    """
    global _cand_stopgrams, _cand_source_ids, _cand_source_lens
    global _cand_source_sets, _cand_n, _cand_min_containment, _cand_docnum_pair_set
    _cand_stopgrams = set()
    _cand_source_ids = []
    _cand_source_lens = []
    _cand_source_sets = []
    _cand_n = 5
    _cand_min_containment = 0.10
    _cand_docnum_pair_set = set()


def generate_candidates(
    texts: list[ExtractedText],
    ngram_sets: dict[str, frozenset[int]],
    stopgrams: set[int],
    num_workers: int = None,
) -> list[CandidatePair]:
    """Generate candidate digest-source pairs using set containment.

    For each potential digest (shorter text), computes its n-gram set from
    jing_text and measures containment via set intersection against each
    source's pre-built n-gram set.
    Also includes pairs from docNumber cross-references.

    Note: Not thread-safe. Uses module-level globals for multiprocessing
    worker state. Do not call concurrently from multiple threads.
    """
    num_workers = config.resolve_worker_count(num_workers)
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

    # Precompute sources sorted by size for efficient filtering.
    # For each digest, we only need sources with char_count >= d_len * min_size_ratio.
    # Sort ascending so we can binary-search for the first qualifying source.
    source_entries = sorted(
        [(tid, length_map.get(tid, 0), ngram_sets[tid])
         for tid in ngram_sets if ngram_sets[tid]],  # skip empty sets
        key=lambda x: x[1],
    )
    source_ids_arr = [e[0] for e in source_entries]
    source_lens_arr = [e[1] for e in source_entries]
    source_sets_arr = [e[2] for e in source_entries]

    # Build worker args: (d_id, jing_text, d_len, min_size_ratio)
    worker_args = [
        (digest.text_id, digest.jing_text,
         digest.metadata.char_count, min_size_ratio)
        for digest in digest_candidates
    ]

    candidates = []
    seen_pairs = set()

    if num_workers > 1 and len(digest_candidates) >= 10:
        # Parallel path
        chunksize = max(1, len(worker_args) // (num_workers * 4))
        with Pool(
            num_workers,
            initializer=_candidate_init,
            initargs=(stopgrams, source_ids_arr, source_lens_arr,
                      source_sets_arr, n, min_containment, docnum_pair_set),
            maxtasksperchild=config.MAXTASKSPERCHILD,
        ) as pool:
            for result_batch in pool.imap_unordered(
                _candidate_worker, worker_args, chunksize=chunksize,
            ):
                for cand in result_batch:
                    pair_key = (cand.digest_id, cand.source_id)
                    seen_pairs.add(pair_key)
                    candidates.append(cand)
    else:
        # Serial path — set module globals directly for _candidate_worker
        global _cand_stopgrams, _cand_source_ids, _cand_source_lens
        global _cand_source_sets, _cand_n, _cand_min_containment, _cand_docnum_pair_set
        _cand_stopgrams = stopgrams
        _cand_source_ids = source_ids_arr
        _cand_source_lens = source_lens_arr
        _cand_source_sets = source_sets_arr
        _cand_n = n
        _cand_min_containment = min_containment
        _cand_docnum_pair_set = docnum_pair_set

        for args in worker_args:
            for cand in _candidate_worker(args):
                pair_key = (cand.digest_id, cand.source_id)
                seen_pairs.add(pair_key)
                candidates.append(cand)

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

    _cleanup_candidate_globals()

    logger.info("Generated %d candidate pairs (%d from fingerprinting, %d from docNumber)",
                len(candidates),
                sum(1 for c in candidates if c.containment_score > 0),
                sum(1 for c in candidates if c.from_docnumber))

    return candidates


def _phonetic_worker(
    args: tuple,
) -> tuple[str, list[tuple[str, int]]] | None:
    """Worker: find transliteration regions and syllable n-grams for one text.

    Uses module-level _worker_table and _worker_min_region_len set by
    _phonetic_init to avoid pickling the table per task.
    """
    text_id, full_text, dharani_ranges = args
    table = _worker_table
    min_region_len = _worker_min_region_len
    regions = find_transliteration_regions(
        full_text, table, dharani_ranges=dharani_ranges,
    )
    regions = [(s, e) for s, e in regions if e - s >= min_region_len]
    if not regions:
        return None
    ngrams = text_to_syllable_ngrams(full_text, regions, table)
    if not ngrams:
        return None
    return (text_id, ngrams)


def generate_phonetic_candidates(
    texts: list[ExtractedText],
    table: dict[str, set[str]],
    num_workers: int = None,
) -> list[CandidatePair]:
    """Generate candidate pairs from phonetic transliteration overlap.

    For texts with transliteration regions:
    1. Find transliteration regions (XML dharani markup + density-based)
    2. Convert to canonical syllable sequences
    3. Build per-text phonetic n-gram sets
    4. Compute phonetic containment via set intersection

    Args:
        texts: All extracted texts.
        table: Phonetic equivalence table (char → set of syllables).
        num_workers: Number of parallel workers (None = min(cpu_count, 4)).

    Returns:
        List of CandidatePair with from_phonetic=True.

    Note: Not thread-safe. Uses module-level globals for multiprocessing
    worker state. Do not call concurrently from multiple threads.
    """
    num_workers = config.resolve_worker_count(num_workers)
    min_region_len = config.MIN_TRANSLITERATION_LENGTH
    min_containment = config.MIN_PHONETIC_CONTAINMENT
    min_size_ratio = config.MIN_SIZE_RATIO

    # Step 1-2: Find transliteration regions and build syllable n-grams per text
    # (parallelized: each text is independent)
    text_ngrams: dict[str, list[tuple[str, int]]] = {}
    length_map = {t.text_id: t.metadata.char_count for t in texts}

    args_list = [
        (text.text_id, text.full_text, text.dharani_ranges)
        for text in texts
    ]

    if num_workers <= 1 or len(texts) < 10:
        # Serial path: set module globals directly for the worker
        global _worker_table, _worker_min_region_len
        _worker_table = table
        _worker_min_region_len = min_region_len
        for args in args_list:
            result = _phonetic_worker(args)
            if result is not None:
                text_ngrams[result[0]] = result[1]
    else:
        chunksize = max(1, len(args_list) // (num_workers * 4))
        with Pool(num_workers, initializer=_phonetic_init,
                  initargs=(table, min_region_len),
                  maxtasksperchild=config.MAXTASKSPERCHILD) as pool:
            for result in pool.imap_unordered(
                _phonetic_worker, args_list, chunksize=chunksize,
            ):
                if result is not None:
                    text_ngrams[result[0]] = result[1]

    if not text_ngrams:
        logger.info("No texts with transliteration regions found")
        return []

    logger.info("Found %d texts with indexable transliteration regions",
                len(text_ngrams))

    # Step 3: Build per-text phonetic n-gram sets and identify stopgrams.
    # First pass: collect all n-gram strings per text to compute doc frequencies.
    text_ngram_str_sets: dict[str, frozenset[str]] = {}
    for text_id, ngrams in text_ngrams.items():
        text_ngram_str_sets[text_id] = frozenset(ng for ng, _ in ngrams)

    # Compute document frequency for each phonetic n-gram
    phonetic_doc_freq: dict[str, int] = defaultdict(int)
    for ngram_set in text_ngram_str_sets.values():
        for ng in ngram_set:
            phonetic_doc_freq[ng] += 1

    # Identify phonetic stopgrams (syllable n-grams in too many texts).
    # min 2 so that with tiny corpora (e.g. 2 texts) nothing gets filtered.
    num_indexed = len(text_ngrams)
    max_freq = max(int(num_indexed * config.PHONETIC_STOPGRAM_DOC_FREQ), 2)
    phonetic_stopgrams = {
        ng for ng, freq in phonetic_doc_freq.items() if freq > max_freq
    }
    logger.info("Identified %d phonetic stopgrams (appearing in >%d texts)",
                len(phonetic_stopgrams), max_freq)

    # Build filtered per-text n-gram sets (excluding stopgrams)
    phonetic_sets: dict[str, frozenset[str]] = {}
    for text_id, ngram_set in text_ngram_str_sets.items():
        filtered = ngram_set - phonetic_stopgrams
        if filtered:
            phonetic_sets[text_id] = filtered

    # Step 4: Compute phonetic containment via set intersection
    candidates = []
    seen_pairs = set()

    for text in texts:
        d_id = text.text_id
        if d_id not in phonetic_sets:
            continue

        d_len = length_map[d_id]
        digest_set = phonetic_sets[d_id]

        # Score against all other texts with phonetic regions
        for source_id, source_set in phonetic_sets.items():
            if source_id == d_id:
                continue
            s_len = length_map.get(source_id, 0)

            # Source must be sufficiently longer than digest
            if s_len < d_len * min_size_ratio:
                continue

            matching = len(digest_set & source_set)
            containment = matching / len(digest_set)
            if containment < min_containment:
                continue

            # Ensure consistent pair ordering (shorter text = digest)
            if d_len <= s_len:
                pair_key = (d_id, source_id)
                final_containment = containment
                final_matching = matching
                final_digest_ngrams = len(digest_set)
            else:
                pair_key = (source_id, d_id)
                # Recompute containment from the actual digest's perspective
                final_matching = len(source_set & digest_set)
                final_digest_ngrams = len(source_set)
                final_containment = (final_matching / final_digest_ngrams
                                     if final_digest_ngrams > 0 else 0.0)

            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            candidates.append(CandidatePair(
                digest_id=pair_key[0],
                source_id=pair_key[1],
                containment_score=final_containment,
                matching_ngrams=final_matching,
                total_digest_ngrams=final_digest_ngrams,
                from_phonetic=True,
            ))

    candidates.sort(key=lambda c: c.containment_score, reverse=True)

    logger.info("Generated %d phonetic candidate pairs", len(candidates))
    return candidates
