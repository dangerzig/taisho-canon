# cython: language_level=3, boundscheck=False, wraparound=False
"""Cython-accelerated implementations of performance-critical functions.

These functions replace pure-Python inner loops with C-level operations
for 10-50x speedups on character comparison and hashing.

IMPORTANT: PyUnicode_READ is a CPython C-API macro that performs NO bounds
checking. All callers of PyUnicode_READ must validate indices manually before
the call. Failing to do so will cause buffer overreads / segfaults.
"""

from cpython.unicode cimport PyUnicode_READ, PyUnicode_KIND, PyUnicode_DATA
from libc.stdint cimport uint32_t
from libc.stdlib cimport malloc, free

# C-level CRC32 from zlib — avoids Python zlib.crc32() overhead and
# eliminates per-n-gram bytes object allocation in the hashing loop.
cdef extern from "zlib.h":
    unsigned long c_crc32 "crc32"(unsigned long crc,
                                   const unsigned char *buf,
                                   unsigned int length) nogil


def fast_ngram_hashes(str text, int n, stopgrams=None):
    """Compute CRC32 hashes for all n-grams in text, optionally filtering stopgrams.

    Args:
        text: Input text string.
        n: N-gram size.
        stopgrams: Optional set of hash values to exclude.

    Returns:
        Frozenset of CRC32 hash values for non-stop n-grams.
    """
    cdef Py_ssize_t text_len = len(text)
    if text_len < n:
        return frozenset()

    cdef Py_ssize_t i
    cdef uint32_t h

    # Encode entire string to UTF-8 once (single C-level operation),
    # then build byte offsets by walking the UTF-8 byte sequence.
    cdef bytes encoded_bytes = text.encode('utf-8')
    cdef Py_ssize_t byte_len = len(encoded_bytes)
    cdef const unsigned char *buf = <const unsigned char *>encoded_bytes

    # Build byte offsets: character i starts at byte_offsets[i].
    # UTF-8 continuation bytes have bit pattern 10xxxxxx (0x80-0xBF),
    # so we skip them to find character boundaries.
    cdef Py_ssize_t *byte_offsets = <Py_ssize_t *>malloc((text_len + 1) * sizeof(Py_ssize_t))
    if byte_offsets == NULL:
        raise MemoryError("Failed to allocate byte_offsets")

    cdef Py_ssize_t char_idx = 0
    cdef Py_ssize_t byte_idx = 0
    while byte_idx <= byte_len and char_idx <= text_len:
        byte_offsets[char_idx] = byte_idx
        char_idx += 1
        if byte_idx < byte_len:
            # Skip to next character start (past continuation bytes)
            byte_idx += 1
            while byte_idx < byte_len and (buf[byte_idx] & 0xC0) == 0x80:
                byte_idx += 1

    # Hash n-grams using C-level crc32() directly on the UTF-8 buffer.
    # No Python object allocation in the inner loop — just pointer arithmetic.
    cdef set hashes = set()
    cdef unsigned int ngram_byte_len

    try:
        if stopgrams is not None and len(stopgrams) > 0:
            for i in range(text_len - n + 1):
                ngram_byte_len = <unsigned int>(byte_offsets[i + n] - byte_offsets[i])
                h = <uint32_t>c_crc32(0, buf + byte_offsets[i], ngram_byte_len)
                if h not in stopgrams:
                    hashes.add(h)
        else:
            for i in range(text_len - n + 1):
                ngram_byte_len = <unsigned int>(byte_offsets[i + n] - byte_offsets[i])
                h = <uint32_t>c_crc32(0, buf + byte_offsets[i], ngram_byte_len)
                hashes.add(h)
    finally:
        free(byte_offsets)

    return frozenset(hashes)


def fast_find_seeds(str digest, str source, int k, source_table=None):
    """Find all maximal exact matching substrings of length >= k.

    Args:
        digest: The shorter (digest) text.
        source: The longer (source) text.
        k: Minimum seed length.
        source_table: Optional prebuilt k-gram table for the source text.

    Returns:
        List of (d_start, s_start, length) triples.
    """
    cdef Py_ssize_t d_len = len(digest)
    cdef Py_ssize_t s_len = len(source)

    if d_len < k or s_len < k:
        return []

    # Build or reuse source k-gram table
    if source_table is None:
        source_table = {}
        for i in range(s_len - k + 1):
            kgram = source[i:i + k]
            if kgram in source_table:
                source_table[kgram].append(i)
            else:
                source_table[kgram] = [i]

    cdef Py_ssize_t d_pos = 0
    cdef Py_ssize_t s_pos
    cdef Py_ssize_t length
    cdef Py_ssize_t best_len
    cdef Py_ssize_t best_s_pos
    cdef int have_best
    cdef list seeds = []

    # Access the underlying unicode data for fast character comparison
    cdef int d_kind = PyUnicode_KIND(digest)
    cdef void* d_data = PyUnicode_DATA(digest)
    cdef int s_kind = PyUnicode_KIND(source)
    cdef void* s_data = PyUnicode_DATA(source)

    while d_pos <= d_len - k:
        kgram = digest[d_pos:d_pos + k]
        positions = source_table.get(kgram)
        if positions is None:
            d_pos += 1
            continue

        have_best = 0
        best_len = 0
        best_s_pos = 0

        for s_pos in positions:
            length = k
            # Extend using direct Unicode buffer access
            while (d_pos + length < d_len and
                   s_pos + length < s_len and
                   PyUnicode_READ(d_kind, d_data, d_pos + length) ==
                   PyUnicode_READ(s_kind, s_data, s_pos + length)):
                length += 1

            if not have_best or length > best_len:
                have_best = 1
                best_len = length
                best_s_pos = s_pos

        if have_best:
            seeds.append((d_pos, best_s_pos, best_len))

        d_pos += 1

    return seeds


def fast_fuzzy_extend(
    str digest, str source,
    Py_ssize_t d_pos, Py_ssize_t s_pos,
    int direction,
    int match_score, int mismatch_score,
    int threshold,
):
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
    cdef Py_ssize_t d_len = len(digest)
    cdef Py_ssize_t s_len = len(source)
    cdef int score = 0
    cdef int best_score = 0
    cdef Py_ssize_t best_d_ext = 0
    cdef Py_ssize_t best_s_ext = 0
    cdef Py_ssize_t d_ext = 0
    cdef Py_ssize_t s_ext = 0
    cdef Py_ssize_t d_idx, s_idx, d_next, s_next
    cdef int gap_d, gap_s

    # Access the underlying unicode data for fast character comparison
    cdef int d_kind = PyUnicode_KIND(digest)
    cdef void* d_data = PyUnicode_DATA(digest)
    cdef int s_kind = PyUnicode_KIND(source)
    cdef void* s_data = PyUnicode_DATA(source)

    while True:
        d_idx = d_pos + d_ext * direction
        s_idx = s_pos + s_ext * direction

        if d_idx < 0 or d_idx >= d_len or s_idx < 0 or s_idx >= s_len:
            break

        if PyUnicode_READ(d_kind, d_data, d_idx) == PyUnicode_READ(s_kind, s_data, s_idx):
            score += match_score
            d_ext += 1
            s_ext += 1
        else:
            d_next = d_pos + (d_ext + 1) * direction
            s_next = s_pos + (s_ext + 1) * direction

            gap_d = (0 <= d_next < d_len and 0 <= s_idx < s_len and
                     PyUnicode_READ(d_kind, d_data, d_next) ==
                     PyUnicode_READ(s_kind, s_data, s_idx))
            gap_s = (0 <= d_idx < d_len and 0 <= s_next < s_len and
                     PyUnicode_READ(d_kind, d_data, d_idx) ==
                     PyUnicode_READ(s_kind, s_data, s_next))

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

    return (best_d_ext, best_s_ext)
