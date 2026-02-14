"""Stage 3: Seed-and-extend alignment between digest and source texts.

Finds exact matching seeds, extends them with fuzzy matching, chains
non-overlapping seeds to maximize coverage, and classifies remaining
segments as novel material.
"""

import logging
from collections import defaultdict
from multiprocessing import Pool, cpu_count

from tqdm import tqdm

from . import config
from .models import (
    ExtractedText, CandidatePair, AlignmentSegment, AlignmentResult,
)

logger = logging.getLogger(__name__)


def _build_kgram_table(text: str, k: int) -> dict[str, list[int]]:
    """Build a hash table of all k-grams in text with their positions."""
    table = defaultdict(list)
    for i in range(len(text) - k + 1):
        kgram = text[i:i + k]
        table[kgram].append(i)
    return table


def _find_seeds(digest: str, source: str, k: int = None) -> list[tuple[int, int, int]]:
    """Find all maximal exact matching substrings of length >= k.

    Returns list of (d_start, s_start, length) triples.
    Uses a k-gram hash table on the source for efficient seed finding.
    """
    if k is None:
        k = config.MIN_SEED_LENGTH

    if len(digest) < k or len(source) < k:
        return []

    source_table = _build_kgram_table(source, k)
    seeds = []
    d_len = len(digest)
    s_len = len(source)

    # Track which digest positions are already covered by extended seeds
    # to avoid redundant work
    d_pos = 0
    while d_pos <= d_len - k:
        kgram = digest[d_pos:d_pos + k]
        if kgram not in source_table:
            d_pos += 1
            continue

        # Keep only the longest match at this digest position. This greedy
        # choice trades a small risk of suboptimal chaining for much fewer
        # seeds passed to the DP, which matters for large texts.
        best_match = None
        for s_pos in source_table[kgram]:
            # Extend the match greedily
            length = k
            while (d_pos + length < d_len and
                   s_pos + length < s_len and
                   digest[d_pos + length] == source[s_pos + length]):
                length += 1
            if best_match is None or length > best_match[2]:
                best_match = (d_pos, s_pos, length)

        if best_match:
            seeds.append(best_match)
            # Skip past this match in the digest to find non-overlapping seeds
            # But we still need to find seeds at d_pos+1 for overlapping coverage
            d_pos += 1
        else:
            d_pos += 1

    return seeds


def _fuzzy_extend(
    digest: str, source: str,
    d_pos: int, s_pos: int,
    direction: int,  # +1 for forward, -1 for backward
) -> tuple[int, int]:
    """Extend a match boundary with fuzzy matching.

    Returns (d_extension, s_extension) — number of chars extended.
    Uses simple scoring: +1 match, -2 mismatch, stop when score < threshold.
    """
    match_score = config.FUZZY_MATCH_SCORE
    mismatch_score = config.FUZZY_MISMATCH_SCORE
    threshold = config.FUZZY_EXTEND_THRESHOLD

    d_len = len(digest)
    s_len = len(source)
    score = 0
    best_score = 0
    best_d_ext = 0
    best_s_ext = 0
    d_ext = 0
    s_ext = 0

    while True:
        d_idx = d_pos + d_ext * direction
        s_idx = s_pos + s_ext * direction

        if d_idx < 0 or d_idx >= d_len or s_idx < 0 or s_idx >= s_len:
            break

        if digest[d_idx] == source[s_idx]:
            score += match_score
            d_ext += 1
            s_ext += 1
        else:
            # Try skip in digest (gap in source)
            d_next = d_pos + (d_ext + 1) * direction
            # Try skip in source (gap in digest)
            s_next = s_pos + (s_ext + 1) * direction

            # Check single-char gap options
            gap_d = (0 <= d_next < d_len and 0 <= s_idx < s_len and
                     digest[d_next] == source[s_idx])
            gap_s = (0 <= d_idx < d_len and 0 <= s_next < s_len and
                     digest[d_idx] == source[s_next])

            if gap_d:
                score += mismatch_score
                d_ext += 2  # skip one char in digest
                s_ext += 1
            elif gap_s:
                score += mismatch_score
                d_ext += 1
                s_ext += 2  # skip one char in source
            else:
                score += mismatch_score
                d_ext += 1
                s_ext += 1

        if score > best_score:
            best_score = score
            best_d_ext = d_ext
            best_s_ext = s_ext

        if score < threshold:
            break

    return best_d_ext, best_s_ext


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

    for i in range(n):
        d_start_i = sorted_seeds[i][0]
        # Find the rightmost seed j < i that doesn't overlap with i
        best_prev = -1
        for j in range(i - 1, -1, -1):
            if sorted_seeds[j][1] <= d_start_i:
                best_prev = j
                break

        if best_prev >= 0:
            dp[i] = max(dp[i], dp[best_prev] + weights[i])

    # Also track the max dp up to each index (not necessarily including that seed)
    max_dp = dp[:]
    for i in range(1, n):
        max_dp[i] = max(max_dp[i], max_dp[i - 1])

    # Backtrack to find which seeds to include
    # Rebuild: select seeds greedily from right to left
    selected = []
    remaining_coverage = max(dp) if dp else 0
    i = n - 1

    # Find the index with the max dp value
    while i >= 0:
        # Find seeds that achieve the target coverage
        if dp[i] == remaining_coverage:
            selected.append(sorted_seeds[i])
            # Find the predecessor
            d_start_i = sorted_seeds[i][0]
            remaining_coverage -= weights[i]
            if remaining_coverage <= 0:
                break
            i -= 1
            while i >= 0 and sorted_seeds[i][1] > d_start_i:
                i -= 1
        else:
            i -= 1

    selected.reverse()
    return selected


def align_pair(
    digest_text: str,
    source_text: str,
    digest_id: str = "",
    source_id: str = "",
) -> AlignmentResult:
    """Perform full seed-and-extend alignment between digest and source.

    Returns an AlignmentResult with segment-by-segment mapping.
    """
    d_len = len(digest_text)
    s_len = len(source_text)

    if d_len == 0:
        return AlignmentResult(digest_id=digest_id, source_id=source_id)

    # Step 1: Find seeds
    raw_seeds = _find_seeds(digest_text, source_text)

    # Step 2: Extend seeds with fuzzy matching
    extended = _extend_seeds(digest_text, source_text, raw_seeds)

    # Step 3: Chain non-overlapping seeds
    chained = _chain_seeds(extended, d_len)

    # Step 4: Build alignment segments
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

    # Compute stats
    coverage = covered / d_len if d_len > 0 else 0.0
    novel_fraction = 1.0 - coverage

    # Source span: fraction of source text that contributes
    # Uses interval merging rather than per-position sets for efficiency
    matched_segments = [s for s in segments if s.match_type != "novel"]
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


def _align_pair_wrapper(args):
    """Wrapper for multiprocessing."""
    digest_id, source_id, digest_text, source_text = args
    return align_pair(digest_text, source_text, digest_id, source_id)


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
    if num_workers is None:
        num_workers = config.NUM_WORKERS or cpu_count()

    args_list = []
    for cand in candidates:
        d_text = text_map.get(cand.digest_id)
        s_text = text_map.get(cand.source_id)
        if d_text and s_text:
            args_list.append((
                cand.digest_id,
                cand.source_id,
                d_text.jing_text,
                s_text.full_text,
            ))

    logger.info("Aligning %d candidate pairs with %d workers...",
                len(args_list), num_workers)

    results = []
    if num_workers <= 1:
        for args in tqdm(args_list, desc="Aligning"):
            results.append(_align_pair_wrapper(args))
    else:
        with Pool(num_workers) as pool:
            for result in tqdm(
                pool.imap_unordered(_align_pair_wrapper, args_list),
                total=len(args_list),
                desc="Aligning",
            ):
                results.append(result)

    logger.info("Completed alignment for %d pairs", len(results))
    return results
