# Performance Optimizations Code Review (v3)

**Previous reviews:** `reviews/performance_optimizations_review.md` (v1), `reviews/performance_optimizations_review_v2.md` (v2)
**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Scope:** Cython infrastructure, modified pipeline files, test coverage, .gitignore

---

## Files Reviewed

| File | Role |
|------|------|
| `digest_detector/_fast.pyx` | Cython-accelerated hot loops |
| `digest_detector/_fast_fallback.py` | Pure-Python fallback (identical semantics) |
| `digest_detector/fast.py` | Import router (Cython vs. fallback) |
| `setup.py` | Cython build script |
| `digest_detector/align.py` | Stage 3: alignment, source table caching, seed dedup, binary search chaining |
| `digest_detector/fingerprint.py` | Stage 2a: n-gram hashing via `fast_ngram_hashes` |
| `digest_detector/candidates.py` | Stage 2b: binary search prefiltering, parallel candidate generation |
| `digest_detector/config.py` | Configuration constants |
| `digest_detector/pipeline.py` | Pipeline orchestrator |
| `digest_detector/cache.py` | Disk cache (PipelineCache) |
| `.gitignore` | Cython build artifact exclusions |
| `tests/test_align.py` | Alignment tests |
| `tests/test_fingerprint.py` | Fingerprint tests |
| `tests/test_candidates.py` | Candidate generation tests |
| `tests/test_phonetic_candidates.py` | Phonetic candidate tests |
| `tests/test_pipeline.py` | Pipeline cache/bypass tests |

---

## 1. Correctness

### Grade: A-

The code is functionally correct for the cases tested. There are a few subtle issues worth flagging.

#### 1.1 Cython vs. Fallback Behavioral Equivalence

**fast_ngram_hashes:** The Cython version checks `stopgrams is not None and len(stopgrams) > 0` (line 52 of `_fast.pyx`) while the fallback checks `if stopgrams:` (line 27 of `_fast_fallback.py`). These are semantically equivalent for `None` and for non-empty sets, but they diverge on an edge case: **an empty `frozenset()`**. In the Cython version, `stopgrams is not None and len(stopgrams) > 0` evaluates to `False` for an empty frozenset, so it takes the no-filter branch. In the fallback, `if stopgrams:` also evaluates to `False` for an empty frozenset. So these actually agree. Good.

However, there is a real divergence risk: if `stopgrams` is passed as a non-set truthy value (e.g., a dict), the Cython version would call `len()` while the fallback would just check truthiness. This is a minor type-safety concern -- callers currently always pass `set[int] | None`, so it is not a practical bug.

**fast_find_seeds:** The Cython version builds a `dict` (line 85-91) when `source_table is None`, while the fallback builds a `defaultdict(list)` (line 61-63). The Cython version manually checks `if kgram in source_table` and either appends or creates a new list. This produces identical results but uses a different dict type. When an external `source_table` is passed in (from `_build_kgram_table` in `align.py`, which returns a `defaultdict`), both implementations call `.get(kgram)` which works identically for both `dict` and `defaultdict`. No bug here, but the inconsistency in internal table construction is worth noting for maintainability.

**fast_fuzzy_extend:** The Cython and fallback implementations are structurally identical. The Cython version uses `PyUnicode_READ` for character comparison while the fallback uses Python's `[]` indexing. These produce identical results for all valid Unicode strings.

**Verdict:** No functional divergence between Cython and fallback for current call patterns. The implementations are well-mirrored.

#### 1.2 Seed Deduplication in `align_pair` (align.py lines 411-417)

```python
best_seeds: dict[tuple[int, int], int] = {}
for d_start, s_start, length in raw_seeds:
    key = (d_start, s_start)
    if key not in best_seeds or length > best_seeds[key]:
        best_seeds[key] = length
raw_seeds = [(d, s, l) for (d, s), l in best_seeds.items()]
```

This deduplicates by `(d_start, s_start)`, keeping only the longest. This is correct for seeds sharing the same starting positions. However, `fast_find_seeds` produces one seed per `d_pos` (the best across all source positions for that `d_pos`). So two seeds can only share the same `(d_start, s_start)` if `fast_find_seeds` emitted them -- but since it advances `d_pos` by 1 each iteration and picks the best `s_pos` per `d_pos`, duplicates on `(d_start, s_start)` should be rare. The dedup is cheap and harmless, but it is worth understanding that the main redundancy it catches is overlapping seeds from *adjacent* `d_pos` values that happen to pick the same `s_pos`.

**Potential issue:** The dedup key `(d_start, s_start)` does not deduplicate seeds that overlap in digest space but start at different source positions. For example, seeds `(10, 500, 20)` and `(12, 502, 18)` cover nearly the same digest region but have different keys. These are left to `_chain_seeds` to resolve. This is fine, but the code comment "Deduplicate: keep only the longest seed for each (d_start, s_start)" could be clearer that this is a *partial* dedup, not comprehensive overlap removal.

#### 1.3 `_chain_seeds` Pre-filter (align.py lines 128-142)

The pre-filter removes "obviously duplicate/contained seeds" by checking adjacent pairs after sorting by `d_end`. This is a performance optimization, not a correctness requirement -- the DP handles all overlaps. However, there is a subtle issue: the loop only compares each seed against the *most recent* entry in `filtered`. Consider three seeds A, B, C where A contains C but B (between them) is not contained in A. After processing A and B, `filtered[-1]` is B, so when C arrives it is compared only against B, not A. If C is not contained in B, it passes through. This is fine -- the comment correctly states "This is a fast pre-filter only."

**Verdict:** No correctness bugs. The pre-filter is conservative (never removes seeds incorrectly) and the DP handles the rest.

#### 1.4 Binary Search in `_chain_seeds` (align.py lines 149-158)

```python
end_positions = [s[1] for s in sorted_seeds]
...
best_prev = bisect_right(end_positions, d_start_i, 0, i) - 1
```

This finds the rightmost seed `j < i` whose `d_end <= d_start_i`. Using `bisect_right` is correct: if `d_start_i = 10` and there are seeds ending at 8, 10, 12, `bisect_right` returns the index after 10, so `index - 1` gives the seed ending at 10 (non-overlapping, since the seed at position 10 ends at 10 and the next starts at 10). This is correct because `d_end` is exclusive (half-open intervals).

**Backtracking (lines 174-187):** The backtracking finds the seed `i` with `dp[i] == remaining_coverage`, subtracts its weight, and jumps to the predecessor via binary search. This assumes the DP solution is unique, which is not guaranteed when multiple seeds have the same weight/coverage. In theory, this could miss the optimal selection if two seeds have equal `dp` values. However, since we are looking for *any* set achieving max coverage (not necessarily unique), this greedy backtrack is correct: it finds *a* valid chain.

#### 1.5 Source Table Caching (align.py lines 569-592)

```python
_cached_source_table: tuple[str, int, dict] | None = None
```

The cache stores exactly one entry: `(source_id, k, table)`. This is safe:
- **Multiprocessing:** Each worker process gets its own copy of `_cached_source_table` (macOS spawn creates fresh processes). No cross-process sharing.
- **Memory:** Only one table is cached at a time; the old one is replaced when a new source is encountered.
- **Thread safety:** Not relevant here (no threads; only processes).

**Potential concern:** The cache key is `source_id`, not `source_text`. If a `source_id` maps to different text across calls (which would be a bug elsewhere), the cache would return stale data. This is fine given the pipeline's data model.

The sorting of `args_list` by `(-source_len, source_id, -digest_len)` in `align_candidates` (line 660) is cleverly designed: clustering by `source_id` maximizes cache hits, while sorting by `-source_len` first gives LPT scheduling. This is a solid optimization.

#### 1.6 `stopgrams` Truthiness (Cython)

In `_fast.pyx` line 52: `if stopgrams is not None and len(stopgrams) > 0:`. This correctly handles `None` (no stopgrams) and empty sets. The `len(stopgrams) > 0` call is O(1) for Python sets. No issue here.

---

## 2. Test Coverage

### Grade: C+

This is the weakest area. The new performance-critical functions lack dedicated unit tests.

#### 2.1 No Direct Tests for `fast_ngram_hashes`, `fast_find_seeds`, `fast_fuzzy_extend`

There are **zero test files** that import from `digest_detector.fast`, `digest_detector._fast`, or `digest_detector._fast_fallback`. A `grep` for these symbols across the `tests/` directory returns nothing.

These functions are tested *indirectly* through `test_fingerprint.py` (which calls `fingerprint_text` and `build_ngram_sets`, which call `fast_ngram_hashes`) and `test_align.py` (which calls `align_pair` and `_find_seeds`, which delegate to `fast_find_seeds` and `fast_fuzzy_extend`). However, indirect testing is insufficient for several reasons:

1. **Cython/fallback equivalence is untested.** There is no test that forces both code paths and compares outputs. Setting `DIGEST_NO_CYTHON=1` in the environment could test the fallback, but there is no test that does both and asserts equality.

2. **Edge cases for the fast functions are untested.** Examples:
   - `fast_ngram_hashes` with `n=1` (single-character n-grams)
   - `fast_ngram_hashes` with text containing surrogate pairs or multi-byte UTF-8 (e.g., emoji, rare CJK)
   - `fast_ngram_hashes` with `n > len(text)`
   - `fast_find_seeds` with a pre-built `source_table` (the caching path)
   - `fast_find_seeds` where multiple source positions match and the best is not the first
   - `fast_fuzzy_extend` with `direction=-1` (backward extension)
   - `fast_fuzzy_extend` when a gap-d and gap-s both match (gap-d is preferred; is this tested?)
   - `fast_fuzzy_extend` at text boundaries (d_pos=0 backward, d_pos=len-1 forward)

3. **The `source_table` parameter is untested directly.** `_build_kgram_table` is called in `_align_pair_wrapper` and the table is passed to `fast_find_seeds`, but no test verifies that a pre-built table produces identical results to letting `fast_find_seeds` build its own.

#### 2.2 No Direct Tests for Source Table Caching

`_cached_source_table` and `_align_pair_wrapper` have no unit tests. The caching logic is exercised indirectly when `test_align.py::TestAlignCandidatesPrefilter` calls `align_candidates`, but:

- No test verifies cache hits (same source, consecutive calls)
- No test verifies cache misses (different source)
- No test verifies that `_build_kgram_table` and the internally-built table in `fast_find_seeds` produce compatible structures

#### 2.3 No Direct Tests for Seed Deduplication

The seed dedup block in `align_pair` (lines 411-417) has no targeted test. It could be tested by crafting a digest/source pair where `_find_seeds` produces multiple seeds with the same `(d_start, s_start)` but different lengths, and verifying only the longest survives.

#### 2.4 No Direct Tests for `_chain_seeds` Pre-filter

The contained-seed removal (lines 128-142) has no targeted test. `TestChainSeeds` tests basic non-overlapping and overlapping cases but does not specifically test:
- A seed fully contained within another (same `d_start` or `d_end`)
- Three seeds where A contains C but B (in between) does not

#### 2.5 No Tests for Binary Search in `generate_candidates`

The `bisect_left` pre-filtering in `_candidate_worker` (line 80) is tested implicitly by `TestGenerateCandidates.test_size_ratio_filter`, but there is no targeted test verifying the binary search boundary condition (e.g., source length exactly equal to `d_len * min_size_ratio`).

#### 2.6 Existing Tests Are Good

The *existing* test suite is well-structured:
- `TestEarlyTermination` (3 tests) covers the early-return logic paths
- `TestAlignCandidatesPrefilter` (3 tests) covers the zero-containment docNumber skip
- `TestNumWorkersEdgeCases` covers `num_workers=0`
- `TestGenerateCandidatesParallel` and `TestPhoneticCandidatesParallel` verify serial/parallel equivalence
- `TestPipelineCacheBypass` (3 tests) covers cache save/load/bypass

#### 2.7 Recommended New Tests

| Priority | Test | Why |
|----------|------|-----|
| **P0** | Direct unit tests for `fast_ngram_hashes`, `fast_find_seeds`, `fast_fuzzy_extend` in a new `tests/test_fast.py` | Core optimization functions have zero direct coverage |
| **P0** | Cython/fallback equivalence test (import both, compare outputs on identical inputs) | Ensures the two implementations agree |
| **P1** | Source table caching: call `_align_pair_wrapper` twice with same source_id, verify identical results and that the second call is faster | Validates the caching optimization |
| **P1** | `_chain_seeds` with fully-contained seeds | Validates the pre-filter |
| **P1** | `fast_find_seeds` with external `source_table` vs. internal build | Validates the table reuse path |
| **P2** | `fast_ngram_hashes` with multi-byte UTF-8 chars (e.g., CJK Extension B) | Edge case for byte-offset logic |
| **P2** | `fast_fuzzy_extend` backward from position 0 | Boundary condition |
| **P2** | `bisect_left` boundary in `_candidate_worker` with exact threshold match | Validates inclusive/exclusive boundary |

---

## 3. Efficiency

### Grade: B+

The Cython code provides real speedups, but several opportunities are missed.

#### 3.1 `fast_ngram_hashes`: Excessive Python Object Allocation in Hot Loop

```python
# _fast.pyx lines 42-46
for i in range(text_len):
    byte_offsets.append(offset)
    ch_bytes = text[i].encode('utf-8')  # Python object allocation per char
    encoded.extend(ch_bytes)
    offset += len(ch_bytes)
```

This loop creates a Python `bytes` object (`ch_bytes`) for every character in the text. For a 286K-character text like T223, that is 286K temporary `bytes` objects. The `bytearray.extend()` call then copies the bytes.

**Better approach:** Encode the entire string to UTF-8 once (`text.encode('utf-8')`) and build byte offsets by walking the UTF-8 byte sequence. UTF-8 encoding is a single C-level operation; the per-character approach forces CPython's memory allocator into a tight loop.

Even better: since CRC32 operates on bytes, the entire encoding + slicing + hashing could be done in a typed memoryview without Python object allocation. This would be the "true Cython" approach.

**Current approach works correctly** but leaves a significant performance opportunity on the table, especially for large texts.

#### 3.2 `fast_ngram_hashes`: Byte Slice Allocation in Hashing Loop

```python
# _fast.pyx lines 53-56
for i in range(text_len - n + 1):
    h = zlib.crc32(encoded_bytes[byte_offsets[i]:byte_offsets[i + n]])
```

Each iteration creates a new `bytes` slice object via `encoded_bytes[start:end]`. For T223, this is ~286K temporary `bytes` objects. Since `zlib.crc32` accepts a buffer protocol object, a `memoryview` slice would avoid the copy:

```python
mv = memoryview(encoded_bytes)
# ...
h = zlib.crc32(mv[byte_offsets[i]:byte_offsets[i + n]])
```

`memoryview` slicing creates a view (no copy), which `zlib.crc32` accepts. This would eliminate 286K allocations per call.

#### 3.3 `fast_ngram_hashes`: `byte_offsets` is a Python `list`

```python
cdef list byte_offsets = []
```

This is a Python list of Python ints. Accessing `byte_offsets[i]` involves Python object overhead. A C array (`Py_ssize_t *`) allocated via `malloc` would be faster for random access. However, since `byte_offsets` is only accessed twice per iteration (and the bottleneck is likely the CRC32 + slice allocation), this is a secondary concern.

#### 3.4 `fast_find_seeds`: k-gram Table Build Uses Python Dict

When `source_table is None`, the Cython code builds a plain `dict` with Python string keys (lines 85-91). This is fine -- the table build is O(n) and the dict lookups during seed finding are O(1) amortized. The real speedup comes from the `PyUnicode_READ` extension loop (lines 121-125), which avoids Python string indexing overhead.

#### 3.5 `fast_fuzzy_extend`: Efficient Character Comparison

The `PyUnicode_READ` calls in `fast_fuzzy_extend` are the correct approach for Cython character-level comparison. This avoids creating temporary Python string objects for each character comparison. This is where Cython provides the most value.

However, the gap detection (lines 190-199) calls `PyUnicode_READ` up to 4 times per mismatch iteration, with bounds checks that are Python-level boolean expressions. The `boundscheck=False` directive does not affect these manual bounds checks -- those are Python `if` statements, not Cython array accesses. This is fine for correctness but the bounds checks add overhead.

#### 3.6 `_chain_seeds` Binary Search: Good Optimization

The switch from linear search to `bisect_right` for finding the best predecessor in the DP (line 158) reduces `_chain_seeds` from O(n^2) to O(n log n). This is a significant improvement for texts with many seeds.

#### 3.7 Binary Search in `_candidate_worker`: Good Optimization

Using `bisect_left` (line 80) to skip sources below the size threshold avoids iterating over small sources. With sources sorted by length, this is optimal.

#### 3.8 Dynamic Chunksize

```python
chunksize = max(1, len(args_list) // (num_workers * 4))
```

This formula (used in `fingerprint.py` line 82, `candidates.py` lines 253, 388) provides reasonable load balancing. The factor of 4 means each worker gets ~4 chunks, allowing some dynamic scheduling. For very small workloads, `max(1, ...)` prevents zero-sized chunks. This is standard practice.

#### 3.9 Source Table Caching: Good for Sequential Access

The single-entry cache in `_align_pair_wrapper` is well-designed for the sorted access pattern. Since `args_list` is sorted by `(-source_len, source_id)`, consecutive pairs often share the same source. Building the k-gram table once per source instead of once per pair is a meaningful savings for large sources.

**Memory concern:** For a 286K-character source like T223, the k-gram table has ~286K entries (each a string key + list of ints). This is perhaps 30-50 MB. Since only one table is cached at a time, and it is replaced when the source changes, memory is bounded. No leak risk.

---

## 4. Legibility

### Grade: A-

The code is generally clean, well-documented, and easy to follow.

#### 4.1 `_fast.pyx` Documentation

The module docstring (lines 2-5) clearly states the purpose. Each function has a complete docstring with Args and Returns. The Cython-specific constructs (`cdef`, `PyUnicode_READ`, etc.) are well-commented. The code is readable despite the C-level operations.

#### 4.2 `_fast_fallback.py` Documentation

Clean type annotations, identical docstrings to the Cython version. The use of `collections.defaultdict` in the fallback (vs. manual dict in Cython) is a minor inconsistency but does not affect readability.

#### 4.3 `fast.py` Import Router

The three-way import logic (env var override, Cython try/except, fallback) is clear and concise. The `# noqa` and `# type: ignore` comments are appropriate.

#### 4.4 `align.py` Source Table Caching

The comments on `_cached_source_table` (line 570-571) explain the single-entry caching strategy and its rationale. The comment on `args_list.sort()` (lines 657-659) explains both the cache-clustering and LPT scheduling motivations. This is good documentation.

#### 4.5 `_chain_seeds` Pre-filter Comments

The comment on lines 126-127 ("This is a fast pre-filter only -- the DP below handles any remaining overlaps correctly via weighted interval scheduling") is important and well-placed. Without it, a reader might worry about correctness.

#### 4.6 Minor Documentation Issues

1. **`fast_find_seeds` return description:** The docstring says "List of (d_start, s_start, length) triples" but does not mention that it returns *one seed per d_pos* (the best across all source positions). This is important for understanding the dedup logic in `align_pair`.

2. **`_build_kgram_table` vs. internal table in `fast_find_seeds`:** It is not immediately obvious that `_build_kgram_table` (using `defaultdict`) and the internal table in `_fast.pyx` (using `dict`) produce compatible structures. A brief comment noting this would help.

3. **`align_pair` parameter `source_table`:** The docstring says "Optional prebuilt k-gram table for the source text" but does not specify the expected type (`dict[str, list[int]]`). The type annotation on `_find_seeds` has it, but `align_pair`'s annotation is also `dict[str, list[int]] | None` -- so this is fine, just slightly hidden.

---

## 5. Architecture

### Grade: A

The overall architecture is clean and well-layered.

#### 5.1 Fallback Pattern

The three-tier import strategy (env var > Cython > fallback) is robust:

```python
if os.environ.get("DIGEST_NO_CYTHON"):
    from ._fast_fallback import ...
else:
    try:
        from ._fast import ...
    except ImportError:
        from ._fast_fallback import ...
```

- **Env var override:** Useful for debugging and testing.
- **ImportError fallback:** Graceful degradation when Cython is not compiled.
- **Single import point:** All other modules import from `digest_detector.fast`, not directly from `_fast` or `_fast_fallback`.

**Minor concern:** The `DIGEST_NO_CYTHON` env var is not documented anywhere (no README, no `--help` output, no config.py comment). It should be mentioned in a developer guide or at minimum in the `fast.py` module docstring.

#### 5.2 `setup.py` Cython Build

```python
try:
    from Cython.Build import cythonize
    extensions = cythonize(...)
except ImportError:
    extensions = []
```

This gracefully handles the case where Cython is not installed. The `compiler_directives` match the `# cython:` pragma at the top of `_fast.pyx` (redundant but harmless -- the pragma is the authoritative source, and `setup.py` directives are applied as defaults).

The `boundscheck=False` and `wraparound=False` directives are set in both places. These disable safety checks on Cython `cdef` typed array accesses. Since the Cython code does not use typed arrays (it uses Python lists and dicts with manual bounds checking), these directives have *no effect* on the current code. They would matter if the code used, e.g., `cdef int[:] arr` memoryview syntax. Keeping them is harmless (forward-looking), but they create a false impression of optimization. Worth a comment.

#### 5.3 `.gitignore` Entries

```
# Cython build artifacts
*.so
*.c
!digest_detector/_fast.pyx
```

The `*.so` and `*.c` patterns correctly exclude compiled extension modules and Cython-generated C files. The `!digest_detector/_fast.pyx` exception is well-intentioned but technically unnecessary: `.pyx` files are not matched by `*.c` or `*.so`. It acts as documentation that the `.pyx` file is *not* a build artifact. No issue here.

**Missing pattern:** The `.gitignore` does not exclude `*.html` files, which `cython -a _fast.pyx` generates (annotated HTML for profiling). This is a minor omission.

#### 5.4 Disk Cache Architecture

`PipelineCache` is well-designed:
- **Invalidation:** Version number + config snapshot + corpus hash. This is comprehensive.
- **Atomicity concern:** The `save()` method writes `texts.pkl`, then `candidates.pkl`, then `manifest.json`. If the process crashes between writes, the cache is left in an inconsistent state. However, `is_valid()` checks all three files exist *and* the manifest matches, so a partial write will fail validation and trigger a fresh run. This is acceptable for a development tool.
- **Pickle security:** The cache uses `pickle.load()` without restrictions. Since this is a local development tool (not a web service), pickle deserialization attacks are not a concern. Fine.

#### 5.5 `_cleanup_candidate_globals()` Pattern

```python
def _cleanup_candidate_globals():
    global _cand_stopgrams, _cand_source_ids, ...
    _cand_stopgrams = set()
    _cand_source_ids = []
    ...
```

This explicit cleanup (called at the end of `generate_candidates`) prevents large shared arrays from persisting in memory. Good practice. The corresponding cleanup for the phonetic table in `align.py` (line 679: `_phonetic_table = None`) follows the same pattern.

#### 5.6 Memory Leak Risk Assessment

| Global | Cleaned up? | Leak risk |
|--------|-------------|-----------|
| `_cand_*` (candidates.py) | Yes, via `_cleanup_candidate_globals()` | None |
| `_worker_table`, `_worker_min_region_len` (candidates.py) | No explicit cleanup | Low (small data, reset on next call) |
| `_worker_stopgrams`, `_worker_n` (fingerprint.py) | No explicit cleanup | Low (stopgrams set is small) |
| `_phonetic_table` (align.py) | Yes, set to `None` after alignment | None |
| `_cached_source_table` (align.py) | No explicit cleanup | Low (single entry, replaced on miss) |

No memory leak risks in practice. The `_worker_*` globals in `fingerprint.py` and `candidates.py` are small and overwritten on each pipeline run. The `_cached_source_table` holds one k-gram table (bounded by a single source text's size).

---

## 6. Specific Findings

### 6.1 [BUG, Low] `_fast.pyx` `boundscheck=False` with `PyUnicode_READ`

`PyUnicode_READ` is a CPython C-API macro that does *not* perform bounds checking. With `boundscheck=False` in the Cython directives and manual bounds checks via Python `if` statements (lines 121-124, 183-186, 194-198), correctness depends entirely on the manual checks. If a bounds check is ever accidentally removed or written incorrectly, the result would be a buffer overread/segfault rather than a Python IndexError.

The current bounds checks are correct. But this is a fragile setup. A future maintainer adding a new `PyUnicode_READ` call might forget bounds checking.

**Recommendation:** Add a comment at the top of `_fast.pyx` noting that `PyUnicode_READ` does not bounds-check and all callers must validate indices manually.

### 6.2 [BUG, Low] `fast_fuzzy_extend` Gap Detection Priority

In `fast_fuzzy_extend`, when both `gap_d` and `gap_s` are true (i.e., skipping one character in either the digest or the source would produce a match), the code always prefers `gap_d` (digest gap). This is an arbitrary tie-breaking rule that produces a valid but potentially suboptimal alignment. The fallback has the same behavior, so Cython/fallback agree.

However, neither the docstring nor inline comments explain this priority. If someone later changes the order, they might not realize it affects alignment quality.

**Recommendation:** Add a comment: "When both gap_d and gap_s match, prefer digest gap (arbitrary tie-break)."

### 6.3 [STYLE] Inconsistent Table Build Between Cython and Fallback

In `fast_find_seeds`:
- **Cython** (lines 85-91): Manual `if kgram in source_table` / `.append()` / `else: [i]`
- **Fallback** (lines 59-63): `defaultdict(list)` + `.append()`

Both produce identical results, but the Cython version avoids the `defaultdict` overhead (no need for the default factory). This is a reasonable micro-optimization. However, the inconsistency makes diff-based code review harder. Consider adding a comment explaining the choice.

### 6.4 [PERF] `_chain_seeds` Backtrack Could Be Simplified

The backtracking in `_chain_seeds` (lines 174-187) has two paths: one where `dp[i] == remaining_coverage` (select this seed) and one where it decrements `i`. The binary search jump (line 185) is efficient, but the outer `while` loop with the `dp[i] == remaining_coverage` check can visit many seeds whose `dp` values do not match. An alternative is to precompute a "next selected" array during the forward pass, which would make backtracking O(selected_seeds) instead of O(all_seeds). For typical alignment chains (tens to hundreds of seeds), this is not a bottleneck, but it is worth noting.

### 6.5 [PERF] `align_pair` Early Termination Uses Raw Seed Coverage

```python
raw_coverage = sum(length for _, _, length in raw_seeds) / d_len
```

This sums all seed lengths, including overlapping seeds. The actual coverage after `_chain_seeds` could be much lower (since overlapping seeds are resolved). This means early termination might *not* fire when it should (raw coverage inflated by overlaps). The effect is extra computation, not incorrect results -- `_chain_seeds` will resolve the overlaps and the final coverage will be correct.

This is a deliberate trade-off (checking raw coverage is O(n) while running the full chain is more expensive). The current threshold (`SHARED_TRADITION_THRESHOLD = 0.10`) is low enough that this is unlikely to cause problems in practice.

### 6.6 [DOC] `DIGEST_NO_CYTHON` Env Var Undocumented

The `DIGEST_NO_CYTHON` environment variable (checked in `fast.py` line 8) is not documented in any README, docstring, or CLI help text. Developers who want to profile the fallback path have to read the source to discover it.

**Recommendation:** Add a comment in `fast.py` and mention it in any developer documentation.

### 6.7 [DOC] `setup.py` Missing `pyproject.toml`

Modern Python packaging recommends `pyproject.toml` over bare `setup.py`. The current `setup.py` works fine for `python3 setup.py build_ext --inplace`, but if the project ever needs to be installed as a package, a `pyproject.toml` with `[build-system]` configuration would be needed. This is a low-priority modernization.

### 6.8 [STYLE] `.gitignore` Exception for `.pyx`

```
!digest_detector/_fast.pyx
```

This negation pattern excludes `_fast.pyx` from `*.c`. But `.pyx` files are not matched by `*.c`. The line serves as documentation ("this .pyx file is intentionally tracked") rather than functional gitignore logic. It is harmless but mildly confusing. A comment above it would help:

```
# Note: _fast.pyx is source code (tracked); .c files are Cython-generated (ignored)
!digest_detector/_fast.pyx
```

---

## 7. Summary of Recommendations

### P0 (Should fix)

| # | Recommendation | Files |
|---|---------------|-------|
| 1 | **Add `tests/test_fast.py`** with direct unit tests for `fast_ngram_hashes`, `fast_find_seeds`, `fast_fuzzy_extend`. Include edge cases: empty text, n > len(text), multi-byte chars, pre-built source_table, backward fuzzy extend, gap-d/gap-s both matching. | `tests/test_fast.py` (new) |
| 2 | **Add Cython/fallback equivalence test**: import both `_fast_fallback` and (if available) `_fast`, run identical inputs through both, assert identical outputs. Skip if Cython not compiled. | `tests/test_fast.py` (new) |

### P1 (Should fix soon)

| # | Recommendation | Files |
|---|---------------|-------|
| 3 | **Add source table caching test**: call `_align_pair_wrapper` with same source_id twice, verify second call reuses cached table (mock `_build_kgram_table` and assert it is called once). | `tests/test_align.py` |
| 4 | **Add `_chain_seeds` contained-seed test**: test with seeds where one is fully contained within another. | `tests/test_align.py` |
| 5 | **Add `boundscheck` warning comment** in `_fast.pyx`: "PyUnicode_READ does not bounds-check; all callers must validate indices." | `_fast.pyx` |
| 6 | **Document `DIGEST_NO_CYTHON`** env var in `fast.py` module docstring. | `fast.py` |

### P2 (Nice to have)

| # | Recommendation | Files |
|---|---------------|-------|
| 7 | **Use `memoryview` for CRC32 slicing** in `fast_ngram_hashes` to avoid per-n-gram `bytes` object allocation. | `_fast.pyx` |
| 8 | **Encode text as single operation** in `fast_ngram_hashes` instead of per-character encoding. | `_fast.pyx` |
| 9 | **Add `.html` to `.gitignore`** Cython section (cython -a generates annotated HTML). | `.gitignore` |
| 10 | **Comment gap-d priority** in `fast_fuzzy_extend`: "When both gaps match, prefer digest gap." | `_fast.pyx`, `_fast_fallback.py` |
| 11 | **Add `pyproject.toml`** build configuration for modern packaging. | `pyproject.toml` (new) |
| 12 | **Clarify `.pyx` gitignore exception** with a comment. | `.gitignore` |

---

## 8. Overall Assessment

### Grade: A-

The performance optimizations are well-implemented and architecturally sound. The Cython/fallback pattern is robust, the import router is clean, and the optimizations (binary search, source table caching, seed dedup, early termination) are all correct. The disk cache is well-designed with proper invalidation.

The main gap is **test coverage for the new fast functions**. These are the most performance-critical and most error-prone parts of the codebase (Cython with `boundscheck=False`, manual Unicode buffer access), yet they have zero direct unit tests. Indirect coverage through higher-level tests provides some confidence, but targeted tests are essential for long-term maintainability and for validating Cython/fallback equivalence.

The Cython code itself, while correct, leaves performance on the table. The per-character encoding and per-n-gram byte slice allocation in `fast_ngram_hashes` could be eliminated with a one-line change to `memoryview`. The `PyUnicode_READ`-based comparison in `fast_find_seeds` and `fast_fuzzy_extend` is where the real Cython value lies, and that code is well-written.

Overall, this is solid B+ to A- work. Filling the test coverage gap would bring it to A+.
