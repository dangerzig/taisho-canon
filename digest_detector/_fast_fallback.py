"""Pure-Python fallback implementations of performance-critical functions.

These are used when the Cython extension (_fast) is not compiled.
Signatures and behavior are identical to the Cython versions.
"""

import zlib


def fast_ngram_hashes(text: str, n: int, stopgrams: set[int] | None = None) -> frozenset[int]:
    """Compute CRC32 hashes for all n-grams in text, optionally filtering stopgrams.

    Args:
        text: Input text string.
        n: N-gram size.
        stopgrams: Optional set of hash values to exclude.

    Returns:
        Frozenset of CRC32 hash values for non-stop n-grams.
    """
    text_len = len(text)
    if text_len < n:
        return frozenset()

    hashes = set()
    if stopgrams is not None and len(stopgrams) > 0:
        for i in range(text_len - n + 1):
            h = zlib.crc32(text[i:i + n].encode('utf-8'))
            if h not in stopgrams:
                hashes.add(h)
    else:
        for i in range(text_len - n + 1):
            hashes.add(zlib.crc32(text[i:i + n].encode('utf-8')))
    return frozenset(hashes)


def fast_find_seeds(
    digest: str, source: str, k: int,
    source_table: dict[str, list[int]] | None = None,
) -> list[tuple[int, int, int]]:
    """Find all maximal exact matching substrings of length >= k.

    Args:
        digest: The shorter (digest) text.
        source: The longer (source) text.
        k: Minimum seed length.
        source_table: Optional prebuilt k-gram table for the source text.
            If None, one is built internally.

    Returns:
        List of (d_start, s_start, length) triples.
    """
    d_len = len(digest)
    s_len = len(source)
    if d_len < k or s_len < k:
        return []

    # Build or reuse source k-gram table
    if source_table is None:
        from collections import defaultdict
        source_table = defaultdict(list)
        for i in range(s_len - k + 1):
            source_table[source[i:i + k]].append(i)

    seeds = []
    d_pos = 0
    while d_pos <= d_len - k:
        kgram = digest[d_pos:d_pos + k]
        positions = source_table.get(kgram)
        if positions is None:
            d_pos += 1
            continue

        best_match = None
        for s_pos in positions:
            length = k
            while (d_pos + length < d_len and
                   s_pos + length < s_len and
                   digest[d_pos + length] == source[s_pos + length]):
                length += 1
            if best_match is None or length > best_match[2]:
                best_match = (d_pos, s_pos, length)

        if best_match:
            seeds.append(best_match)

        d_pos += 1

    return seeds


def fast_fuzzy_extend(
    digest: str, source: str,
    d_pos: int, s_pos: int,
    direction: int,
    match_score: int, mismatch_score: int,
    threshold: int,
) -> tuple[int, int]:
    """Extend a match boundary with fuzzy matching.

    Args:
        digest: Digest text.
        source: Source text.
        d_pos: Starting position in digest.
        s_pos: Starting position in source.
        direction: +1 for forward, -1 for backward.
        match_score: Score for matching characters.
        mismatch_score: Score for mismatching characters.
        threshold: Stop when score drops below this.

    Returns:
        (d_extension, s_extension) — number of chars extended.
    """
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
            d_next = d_pos + (d_ext + 1) * direction
            s_next = s_pos + (s_ext + 1) * direction

            gap_d = (0 <= d_next < d_len and 0 <= s_idx < s_len and
                     digest[d_next] == source[s_idx])
            gap_s = (0 <= d_idx < d_len and 0 <= s_next < s_len and
                     digest[d_idx] == source[s_next])

            # When both gaps match, prefer digest gap (arbitrary tie-break)
            if gap_d:
                score += mismatch_score
                d_ext += 2
                s_ext += 1
            elif gap_s:
                score += mismatch_score
                d_ext += 1
                s_ext += 2
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
