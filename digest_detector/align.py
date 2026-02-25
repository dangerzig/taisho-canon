"""Stage 3: Seed-and-extend alignment between digest and source texts.

Finds exact matching seeds, extends them with fuzzy matching, chains
non-overlapping seeds to maximize coverage, and classifies remaining
segments as novel material. Optionally rescans novel segments for
phonetically equivalent transliterations (dharani detection).
"""

import logging
from bisect import bisect_right
from collections import defaultdict
from multiprocessing import Pool

from tqdm import tqdm

from . import config
from .fast import fast_find_seeds, fast_fuzzy_extend
from .models import (
    ExtractedText, CandidatePair, AlignmentSegment, AlignmentResult,
)
from .phonetic import (
    build_equivalence_table,
    phonetic_mapping_for_pair,
)

logger = logging.getLogger(__name__)


def _build_kgram_table(text: str, k: int) -> dict[str, list[int]]:
    """Build a hash table of all k-grams in text with their positions."""
    table = defaultdict(list)
    for i in range(len(text) - k + 1):
        kgram = text[i:i + k]
        table[kgram].append(i)
    return table


def _find_seeds(
    digest: str, source: str, k: int = None,
    source_table: dict[str, list[int]] | None = None,
) -> list[tuple[int, int, int]]:
    """Find all maximal exact matching substrings of length >= k.

    Returns list of (d_start, s_start, length) triples.
    Uses a k-gram hash table on the source for efficient seed finding.
    Delegates to fast_find_seeds (Cython when available, else pure Python).
    """
    if k is None:
        k = config.MIN_SEED_LENGTH
    return fast_find_seeds(digest, source, k, source_table)


def _fuzzy_extend(
    digest: str, source: str,
    d_pos: int, s_pos: int,
    direction: int,  # +1 for forward, -1 for backward
) -> tuple[int, int]:
    """Extend a match boundary with fuzzy matching.

    Returns (d_extension, s_extension) — number of chars extended.
    Delegates to fast_fuzzy_extend (Cython when available, else pure Python).
    """
    return fast_fuzzy_extend(
        digest, source, d_pos, s_pos, direction,
        config.FUZZY_MATCH_SCORE,
        config.FUZZY_MISMATCH_SCORE,
        config.FUZZY_EXTEND_THRESHOLD,
    )


def _extend_seeds(
    digest: str, source: str,
    seeds: list[tuple[int, int, int]],
) -> list[tuple[int, int, int, int, str]]:
    """Extend exact seeds with fuzzy matching at boundaries.

    Returns list of (d_start, d_end, s_start, s_end, match_type) tuples.

    Note: fuzzy extensions may include gap characters (single-char insertions
    or deletions), so the digest and source spans of a fuzzy segment may differ
    in length and the segment text includes the gap characters.
    """
    extended = []
    for d_start, s_start, length in seeds:
        d_end = d_start + length
        s_end = s_start + length

        # Try extending forward
        fwd_d, fwd_s = _fuzzy_extend(digest, source, d_end, s_end, +1)
        # Try extending backward
        bwd_d, bwd_s = _fuzzy_extend(digest, source, d_start - 1, s_start - 1, -1)

        new_d_start = d_start - bwd_d
        new_d_end = d_end + fwd_d
        new_s_start = s_start - bwd_s
        new_s_end = s_end + fwd_s

        if fwd_d > 0 or bwd_d > 0:
            match_type = "fuzzy"
        else:
            match_type = "exact"

        extended.append((new_d_start, new_d_end, new_s_start, new_s_end, match_type))

    return extended


def _chain_seeds(
    seeds: list[tuple[int, int, int, int, str]],
    digest_len: int,
) -> list[tuple[int, int, int, int, str]]:
    """Select non-overlapping seeds (in digest coordinates) that maximize
    total coverage using weighted interval scheduling via DP.

    Seeds do NOT need to be monotonic in source coordinates (digests can
    rearrange material).
    """
    if not seeds:
        return []

    # Sort by digest end position
    sorted_seeds = sorted(seeds, key=lambda s: s[1])

    # Remove obviously duplicate/contained seeds by checking adjacent pairs.
    # This is a fast pre-filter only — the DP below handles any remaining
    # overlaps correctly via weighted interval scheduling.
    filtered = []
    for seed in sorted_seeds:
        d_start, d_end = seed[0], seed[1]
        if filtered:
            prev = filtered[-1]
            # If this seed is contained within the previous one, skip
            if d_start >= prev[0] and d_end <= prev[1]:
                continue
            # If previous is contained within this one, replace
            if prev[0] >= d_start and prev[1] <= d_end:
                filtered[-1] = seed
                continue
        filtered.append(seed)

    sorted_seeds = filtered
    n = len(sorted_seeds)

    # DP: dp[i] = max coverage using seeds[0..i] where seed i is included
    weights = [s[1] - s[0] for s in sorted_seeds]
    dp = weights[:]
    prev = [-1] * n  # predecessor index for backtracking

    # Precompute end positions for binary search (sorted ascending since
    # sorted_seeds is sorted by d_end)
    end_positions = [s[1] for s in sorted_seeds]

    for i in range(n):
        d_start_i = sorted_seeds[i][0]
        # Find the rightmost seed j < i where d_end <= d_start_i
        # bisect_right gives the insertion point for d_start_i in end_positions,
        # so index - 1 is the rightmost seed ending at or before d_start_i
        best_prev = bisect_right(end_positions, d_start_i, 0, i) - 1

        if best_prev >= 0:
            candidate = dp[best_prev] + weights[i]
            if candidate > dp[i]:
                dp[i] = candidate
                prev[i] = best_prev

    # Find the index with the global max dp value
    best_idx = 0
    for i in range(1, n):
        if dp[i] > dp[best_idx]:
            best_idx = i

    # Backtrack via prev chain to reconstruct the optimal solution
    selected = []
    i = best_idx
    while i >= 0:
        selected.append(sorted_seeds[i])
        i = prev[i]

    selected.reverse()
    return selected


# Module-level cache for phonetic equivalence table (loaded once)
_phonetic_table: dict[str, set[str]] | None = None


def _get_phonetic_table() -> dict[str, set[str]]:
    """Lazily load and cache the phonetic equivalence table."""
    global _phonetic_table
    if _phonetic_table is None:
        _phonetic_table = build_equivalence_table()
    return _phonetic_table


def _has_transliteration_chars(text: str, table: dict[str, set[str]]) -> bool:
    """Check if text contains any characters from the transliteration table."""
    return any(ch in table for ch in text)


def _find_phonetic_seeds(
    digest: str,
    source: str,
    table: dict[str, set[str]],
    k: int = None,
) -> list[tuple[int, int, int]]:
    """Find phonetically equivalent seed matches between digest and source.

    Like _find_seeds but uses phonetic equivalence instead of exact equality.
    Returns list of (d_start, s_start, length) triples.
    """
    if k is None:
        k = config.PHONETIC_SEED_LENGTH

    d_len = len(digest)
    s_len = len(source)
    if d_len < k or s_len < k:
        return []

    # Pre-compute which syllables appear in the digest so we only index
    # source positions for relevant syllables (reduces index size significantly)
    digest_syls: set[str] = set()
    for ch in digest:
        digest_syls.update(table.get(ch, ()))

    # Build index: for each source char, map its syllable values to positions
    # syllable → list of source positions where a char with that syllable appears
    syl_to_positions: dict[str, list[int]] = defaultdict(list)
    for i, ch in enumerate(source):
        for syl in table.get(ch, ()):
            if syl in digest_syls:
                syl_to_positions[syl].append(i)

    seeds = []
    d_pos = 0
    while d_pos <= d_len - k:
        d_ch = digest[d_pos]
        d_syls = table.get(d_ch, set())
        if not d_syls:
            d_pos += 1
            continue

        # Find source positions where the first digest char has a phonetic match.
        # Cap at 500 positions per digest char to prevent O(D*S) blowup when
        # a syllable like 'sa' maps to many source positions.
        candidate_positions: set[int] = set()
        for syl in d_syls:
            for s_pos in syl_to_positions.get(syl, ()):
                candidate_positions.add(s_pos)
                if len(candidate_positions) >= 500:
                    break
            if len(candidate_positions) >= 500:
                break

        best_match = None
        for s_pos in candidate_positions:
            if s_pos + k > s_len:
                continue

            # Inline phonetic equivalence check for speed: avoids
            # per-character function call overhead of are_phonetically_equivalent().
            # Uses isdisjoint() which short-circuits on first shared element.
            length = 0
            diff_count = 0
            while d_pos + length < d_len and s_pos + length < s_len:
                dc = digest[d_pos + length]
                s_ch = source[s_pos + length]
                if dc == s_ch:
                    length += 1
                else:
                    d_s = table.get(dc)
                    s_s = table.get(s_ch)
                    if d_s and s_s and not d_s.isdisjoint(s_s):
                        length += 1
                        diff_count += 1
                    else:
                        break

            if length >= k and diff_count >= 2:
                if best_match is None or length > best_match[2]:
                    best_match = (d_pos, s_pos, length)

        if best_match:
            seeds.append(best_match)

        d_pos += 1

    return seeds


def _phonetic_rescan(
    digest_text: str,
    source_text: str,
    segments: list[AlignmentSegment],
    table: dict[str, set[str]],
) -> list[AlignmentSegment]:
    """Rescan novel segments for phonetically equivalent transliterations.

    For each novel segment containing transliteration characters, searches
    the source for phonetically equivalent sequences using seed-and-extend
    with are_phonetically_equivalent() instead of ==.

    Returns a new list of segments with phonetic matches split out of
    novel segments.
    """
    k = config.PHONETIC_SEED_LENGTH
    new_segments = []

    for seg in segments:
        if seg.match_type != "novel":
            new_segments.append(seg)
            continue

        novel_text = seg.digest_text
        # Skip if too short or no transliteration chars
        if len(novel_text) < k or not _has_transliteration_chars(novel_text, table):
            new_segments.append(seg)
            continue

        # Find phonetic seeds within this novel segment against full source
        phonetic_seeds = _find_phonetic_seeds(novel_text, source_text, table, k)

        if not phonetic_seeds:
            new_segments.append(seg)
            continue

        # Chain non-overlapping phonetic seeds (reuse existing chainer)
        extended = [(d_s, d_s + length, s_s, s_s + length, "phonetic")
                    for d_s, s_s, length in phonetic_seeds]
        chained = _chain_seeds(extended, len(novel_text))

        if not chained:
            new_segments.append(seg)
            continue

        # Split the novel segment into phonetic + remaining novel parts
        prev_end = 0
        for d_start, d_end, s_start, s_end, _ in chained:
            # Novel portion before this phonetic match
            if d_start > prev_end:
                new_segments.append(AlignmentSegment(
                    digest_start=seg.digest_start + prev_end,
                    digest_end=seg.digest_start + d_start,
                    source_start=-1,
                    source_end=-1,
                    match_type="novel",
                    digest_text=novel_text[prev_end:d_start],
                    source_text="",
                ))

            # Phonetic match
            d_text = novel_text[d_start:d_end]
            s_text = source_text[s_start:s_end]
            mapping = phonetic_mapping_for_pair(d_text, s_text, table)

            new_segments.append(AlignmentSegment(
                digest_start=seg.digest_start + d_start,
                digest_end=seg.digest_start + d_end,
                source_start=s_start,
                source_end=s_end,
                match_type="phonetic",
                digest_text=d_text,
                source_text=s_text,
                phonetic_mapping=mapping,
            ))
            prev_end = d_end

        # Trailing novel portion
        if prev_end < len(novel_text):
            new_segments.append(AlignmentSegment(
                digest_start=seg.digest_start + prev_end,
                digest_end=seg.digest_end,
                source_start=-1,
                source_end=-1,
                match_type="novel",
                digest_text=novel_text[prev_end:],
                source_text="",
            ))

    return new_segments


def align_pair(
    digest_text: str,
    source_text: str,
    digest_id: str = "",
    source_id: str = "",
    skip_phonetic_rescan: bool = False,
    source_table: dict[str, list[int]] | None = None,
) -> AlignmentResult:
    """Perform full seed-and-extend alignment between digest and source.

    Args:
        skip_phonetic_rescan: If True, skip the expensive phonetic rescan
            of novel segments. Used for pairs already discovered via
            phonetic candidate generation (Stage 2b).
        source_table: Optional prebuilt k-gram table for the source text.
            If provided, _find_seeds reuses it instead of rebuilding.

    Returns an AlignmentResult with segment-by-segment mapping.
    """
    d_len = len(digest_text)
    s_len = len(source_text)

    if d_len == 0:
        return AlignmentResult(digest_id=digest_id, source_id=source_id)

    # Step 1: Find seeds and deduplicate
    raw_seeds = _find_seeds(digest_text, source_text, source_table=source_table)

    # Deduplicate by diagonal: seeds with the same (s_start - d_start) offset
    # describe the same aligned region. Merge overlapping seeds on each diagonal
    # into the maximal extent. This typically reduces seeds by 5-10x, cutting
    # redundant work in _extend_seeds and _chain_seeds.
    if raw_seeds:
        diagonals: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
        for d_start, s_start, length in raw_seeds:
            diagonals[s_start - d_start].append((d_start, s_start, length))

        deduped = []
        for seeds_on_diag in diagonals.values():
            seeds_on_diag.sort()  # sort by d_start
            cur_d, cur_s, cur_len = seeds_on_diag[0]
            cur_end = cur_d + cur_len
            for d_start, s_start, length in seeds_on_diag[1:]:
                d_end = d_start + length
                if d_start <= cur_end:  # overlapping on this diagonal
                    cur_end = max(cur_end, d_end)
                else:  # gap — emit current, start new
                    deduped.append((cur_d, cur_s, cur_end - cur_d))
                    cur_d, cur_s = d_start, s_start
                    cur_end = d_end
            deduped.append((cur_d, cur_s, cur_end - cur_d))
        raw_seeds = deduped

    # Early termination: if raw seed coverage is below SHARED_TRADITION_THRESHOLD
    # and phonetic rescan won't run, the pair cannot produce any useful
    # classification. Skip the expensive extend/chain steps.
    # Note: computed after dedup to avoid overcounting overlapping seeds.
    if raw_seeds:
        raw_coverage = sum(length for _, _, length in raw_seeds) / d_len
    else:
        raw_coverage = 0.0

    do_phonetic = config.ENABLE_PHONETIC_SCAN and not skip_phonetic_rescan
    if raw_coverage < config.SHARED_TRADITION_THRESHOLD and not do_phonetic:
        # Return a single novel segment covering the whole digest
        segments = [AlignmentSegment(
            digest_start=0,
            digest_end=d_len,
            source_start=-1,
            source_end=-1,
            match_type="novel",
            digest_text=digest_text,
            source_text="",
        )]
        return AlignmentResult(
            digest_id=digest_id,
            source_id=source_id,
            segments=segments,
            coverage=0.0,
            novel_fraction=1.0,
        )

    # Step 2: Extend seeds with fuzzy matching
    if raw_coverage >= config.SHARED_TRADITION_THRESHOLD:
        extended = _extend_seeds(digest_text, source_text, raw_seeds)
        chained = _chain_seeds(extended, d_len)
    else:
        # Seeds too sparse for useful extend/chain, but phonetic rescan
        # may still find matches — build a single novel segment.
        chained = []

    # Step 3-4: Build alignment segments from chained seeds
    segments = []
    covered = 0
    prev_end = 0

    for d_start, d_end, s_start, s_end, match_type in chained:
        # Add novel segment before this match
        if d_start > prev_end:
            segments.append(AlignmentSegment(
                digest_start=prev_end,
                digest_end=d_start,
                source_start=-1,
                source_end=-1,
                match_type="novel",
                digest_text=digest_text[prev_end:d_start],
                source_text="",
            ))

        # Add matched segment
        segments.append(AlignmentSegment(
            digest_start=d_start,
            digest_end=d_end,
            source_start=s_start,
            source_end=s_end,
            match_type=match_type,
            digest_text=digest_text[d_start:d_end],
            source_text=source_text[s_start:s_end],
        ))
        covered += d_end - d_start
        prev_end = d_end

    # Add trailing novel segment
    if prev_end < d_len:
        segments.append(AlignmentSegment(
            digest_start=prev_end,
            digest_end=d_len,
            source_start=-1,
            source_end=-1,
            match_type="novel",
            digest_text=digest_text[prev_end:d_len],
            source_text="",
        ))

    # Step 5: Phonetic rescan of novel segments (if enabled and not skipped)
    if do_phonetic:
        table = _get_phonetic_table()
        segments = _phonetic_rescan(digest_text, source_text, segments, table)
        # Recompute covered chars including phonetic matches
        covered = sum(
            s.digest_end - s.digest_start
            for s in segments if s.match_type != "novel"
        )

    # Compute stats
    coverage = covered / d_len if d_len > 0 else 0.0
    novel_fraction = 1.0 - coverage

    # Source span: fraction of source text that contributes
    # Uses interval merging rather than per-position sets for efficiency
    matched_segments = [s for s in segments
                        if s.match_type != "novel" and s.source_start >= 0]
    if matched_segments and s_len > 0:
        intervals = sorted((seg.source_start, seg.source_end) for seg in matched_segments)
        merged_len = 0
        cur_start, cur_end = intervals[0]
        for s, e in intervals[1:]:
            if s <= cur_end:
                cur_end = max(cur_end, e)
            else:
                merged_len += cur_end - cur_start
                cur_start, cur_end = s, e
        merged_len += cur_end - cur_start
        source_span = merged_len / s_len
    else:
        source_span = 0.0

    # Count disjoint source regions
    num_source_regions = _count_source_regions(matched_segments)

    return AlignmentResult(
        digest_id=digest_id,
        source_id=source_id,
        segments=segments,
        coverage=coverage,
        novel_fraction=novel_fraction,
        source_span=source_span,
        num_source_regions=num_source_regions,
    )


def _count_source_regions(
    matched_segments: list[AlignmentSegment],
    gap_threshold: int = 100,
) -> int:
    """Count disjoint regions in the source that contribute to the alignment.

    Two segments are in the same region if their source positions are within
    gap_threshold characters of each other.
    """
    if not matched_segments:
        return 0

    sorted_segs = sorted(matched_segments, key=lambda s: s.source_start)
    regions = 1
    prev_end = sorted_segs[0].source_end

    for seg in sorted_segs[1:]:
        if seg.source_start - prev_end > gap_threshold:
            regions += 1
        prev_end = max(prev_end, seg.source_end)

    return regions


# Process-local source table cache: (source_id, k) → kgram table.
# Caching just the last source avoids unbounded memory growth while
# exploiting consecutive same-source tasks (when sorted by source_id).
_cached_source_table: tuple[str, int, dict] | None = None


def _align_pair_wrapper(args):
    """Wrapper for multiprocessing with source table caching."""
    global _cached_source_table
    digest_id, source_id, digest_text, source_text, skip_phonetic = args

    k = config.MIN_SEED_LENGTH
    # Check if we can reuse the cached source table
    if (_cached_source_table is not None
            and _cached_source_table[0] == source_id
            and _cached_source_table[1] == k):
        source_table = _cached_source_table[2]
    else:
        source_table = _build_kgram_table(source_text, k)
        _cached_source_table = (source_id, k, source_table)

    return align_pair(digest_text, source_text, digest_id, source_id,
                      skip_phonetic_rescan=skip_phonetic,
                      source_table=source_table)


def align_candidates(
    candidates: list[CandidatePair],
    text_map: dict[str, ExtractedText],
    num_workers: int = None,
) -> list[AlignmentResult]:
    """Run alignment on all candidate pairs.

    Args:
        candidates: Candidate pairs from Stage 2.
        text_map: Mapping from text_id → ExtractedText.
        num_workers: Number of parallel workers.

    Returns list of AlignmentResult objects.
    """
    num_workers = config.resolve_worker_count(num_workers, memory_intensive=False)

    # Step 1: Build set of phonetic pair keys for cross-check
    phonetic_pairs = {(c.digest_id, c.source_id) for c in candidates
                      if c.from_phonetic}

    # Step 2: Build args list, pre-filtering and setting flags per pair
    args_list = []
    skipped = 0
    for cand in candidates:
        d_text = text_map.get(cand.digest_id)
        s_text = text_map.get(cand.source_id)
        if not d_text or not s_text:
            continue

        d_len = len(d_text.jing_text)
        s_len = len(s_text.full_text)

        # Pre-filter zero-containment docNumber pairs: if no fingerprint
        # overlap, not a phonetic discovery, only included because of
        # docNumber, and both texts are large → alignment is expensive
        # and fruitless.
        if (cand.containment_score == 0.0
                and cand.from_docnumber
                and not cand.from_phonetic
                and (cand.digest_id, cand.source_id) not in phonetic_pairs
                and d_len > config.DOCNUM_PREFILTER_MIN_LEN
                and s_len > config.DOCNUM_PREFILTER_MIN_LEN):
            skipped += 1
            continue

        # Skip phonetic rescan for phonetic-origin pairs (already
        # discovered via phonetic candidate generation in Stage 2b)
        skip_phonetic = cand.from_phonetic

        args_list.append((
            cand.digest_id,
            cand.source_id,
            d_text.jing_text,
            s_text.full_text,
            skip_phonetic,
        ))

    if skipped:
        logger.info("Skipped %d zero-containment docNumber pairs "
                    "(both texts >%d chars)",
                    skipped, config.DOCNUM_PREFILTER_MIN_LEN)

    # Step 3: Sort by (-source_len, source_id, -digest_len).
    # This clusters pairs by source for k-gram table cache reuse while
    # keeping LPT scheduling (largest sources first → expensive pairs start early).
    args_list.sort(key=lambda a: (-len(a[3]), a[1], -len(a[2])))

    logger.info("Aligning %d candidate pairs with %d workers...",
                len(args_list), num_workers)

    results = []
    if num_workers <= 1:
        for args in tqdm(args_list, desc="Aligning"):
            results.append(_align_pair_wrapper(args))
    else:
        with Pool(num_workers, maxtasksperchild=config.MAXTASKSPERCHILD) as pool:
            for result in tqdm(
                pool.imap_unordered(_align_pair_wrapper, args_list),
                total=len(args_list),
                desc="Aligning",
            ):
                results.append(result)

    # Canonicalize order so results are deterministic regardless of worker scheduling
    results.sort(key=lambda r: (r.digest_id, r.source_id))

    # Free the cached phonetic table — it's no longer needed after alignment
    global _phonetic_table
    _phonetic_table = None

    logger.info("Completed alignment for %d pairs", len(results))
    return results
