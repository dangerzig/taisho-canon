# Code Review: `digest_detector/align.py`

**Reviewer:** Claude
**Date:** 2026-02-19
**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py` (686 lines)
**Also reviewed:** `_fast_fallback.py`, `_fast.pyx`, `config.py`, `models.py`, `phonetic.py`, `tests/test_align.py`

---

## Executive Summary

The alignment module is well-structured and demonstrates strong engineering judgment. The seed-and-extend algorithm is sound, the weighted interval scheduling DP is correctly implemented, and the multiprocessing strategy is sensible. I found one correctness bug in the DP backtracking (P1), one algorithmic concern in seed deduplication (P2), and several performance and robustness issues. Overall quality is high -- most findings are P3/P4.

---

## Findings

### 1. [P1 - Critical] DP backtracking can miss the optimal solution

**Lines 168-189** (`_chain_seeds`)

The backtracking logic assumes that if `dp[i] == remaining_coverage`, then seed `i` is part of the optimal solution. This is not correct in general. Multiple seeds can have the same `dp[i]` value, and the one encountered during the rightward-to-leftward scan may not be the one that actually chains with the remaining seeds to form the optimal set.

```python
while i >= 0:
    if dp[i] == remaining_coverage:
        selected.append(sorted_seeds[i])
        d_start_i = sorted_seeds[i][0]
        remaining_coverage -= weights[i]
        if remaining_coverage <= 0:
            break
        i = bisect_right(end_positions, d_start_i, 0, i) - 1
    else:
        i -= 1
```

**The specific problem:** After selecting seed `i`, the code jumps to `bisect_right(end_positions, d_start_i, 0, i) - 1`, which finds the rightmost non-overlapping predecessor. But `dp[best_prev]` was the max dp value among *all* seeds `0..best_prev`, not specifically the value at that index. The code then searches leftward from that index for a seed where `dp[j] == remaining_coverage`, but the actual predecessor of seed `i` in the optimal chain might be at a *different* index than the one matching `remaining_coverage` at that position.

**Concrete failure scenario:** Consider seeds sorted by d_end:
- Seed 0: weight=5, dp[0]=5
- Seed 1: weight=8, dp[1]=8 (overlaps seed 0)
- Seed 2: weight=5, dp[2]=10 (compatible with seed 0: dp[0]+5=10)
- Seed 3: weight=6, dp[3]=14 (compatible with seed 1: dp[1]+6=14)

Optimal is {1, 3} with coverage=14. The backtrack starts at i=3, selects it, sets remaining=8. Jumps to bisect position. Now it seeks dp[j]==8. If seed 1 is compatible and dp[1]=8, it works. But if the bisect jump lands at index 0 (because seed 3's d_start is before seed 1's d_end), the code scans left from 0 looking for dp[j]==8, finds nothing, and the backtrack terminates with remaining_coverage > 0, producing a suboptimal chain.

**In practice:** This may rarely trigger because:
(a) Seeds in CJK text alignment tend to have diverse weights (few ties).
(b) The pre-filter removes contained seeds, reducing the density of overlaps.
(c) Even if it produces a suboptimal chain, the difference is likely small (a few characters).

But it *is* a correctness bug that can silently undercount coverage.

**Recommended fix:** Use a standard DP backtracking approach: store `prev[i]` during the forward pass (the index of the predecessor seed used to achieve `dp[i]`), then follow the `prev` chain backward from the global max.


### 2. [P2 - Important] `_find_seeds` returns only best match per `d_pos`, losing valid multi-site seeds

**Lines 66-87** (`fast_find_seeds` in `_fast_fallback.py`, mirrored in `_fast.pyx` lines 131-159)

For each digest position `d_pos`, the code finds all source positions where the k-gram matches, extends each one, then keeps *only the longest* match:

```python
if best_match is None or length > best_match[2]:
    best_match = (d_pos, s_pos, length)
```

This means if a digest k-gram appears at two locations in the source (e.g., source positions 100 and 50000), only the one that happens to extend longest is returned. The other valid seed is discarded.

This matters for digests that draw material from multiple locations in the source. Consider: digest position 5 matches source position 100 for length 20, and source position 50000 for length 18. The code keeps only (5, 100, 20). But both are valid seeds -- the length-18 match at position 50000 might chain with *other* seeds to produce better total coverage.

**Impact:** The weighted interval scheduling DP (which is designed precisely to handle multiple source regions) receives an impoverished input set. Coverage estimates could be slightly low for texts that reuse phrases from different parts of the source.

**Mitigation already in place:** Since the code advances `d_pos` by 1 each step, nearby digest positions will produce seeds pointing to the other source location, so the loss is typically bounded by the k-gram size (5 chars). Still, for completeness, returning all maximal seeds (not just the best per d_pos) would be more correct.


### 3. [P2 - Important] Deduplication in `align_pair` uses wrong key -- can discard distinct seeds

**Lines 411-417** (`align_pair`)

```python
best_seeds: dict[tuple[int, int], int] = {}
for d_start, s_start, length in raw_seeds:
    key = (d_start, s_start)
    if key not in best_seeds or length > best_seeds[key]:
        best_seeds[key] = length
raw_seeds = [(d, s, l) for (d, s), l in best_seeds.items()]
```

The dedup key is `(d_start, s_start)`. But `_find_seeds` already produces at most one seed per `d_pos` (finding #2 above). So seeds with the same `d_start` will almost always have the same `s_start` too -- this dedup is largely a no-op.

More importantly, this dedup is *insufficient* for overlapping seed removal. Consider two seeds: `(d_start=0, s_start=100, len=20)` and `(d_start=3, s_start=103, len=17)`. These describe the *exact same* source region (they share the substring at digest[3:20] = source[103:120]), but have different `(d_start, s_start)` keys, so dedup does not merge them. They become separate inputs to `_extend_seeds`, which may produce near-identical extended segments that the chainer must handle.

**Impact:** The seed list fed to `_extend_seeds` can be 5-10x larger than necessary (one seed per digest position for each matching region). For a 28K-pair workload with some large texts, this matters for performance. The chainer handles it correctly (it's designed for overlaps), but extend-then-chain does redundant work.

**Suggestion:** Dedup by merging overlapping seeds that point to the same source region. A simple approach: sort by (s_start - d_start, d_start), then merge seeds with the same diagonal offset.


### 4. [P2 - Important] `_chain_seeds` containment pre-filter only checks adjacent pairs

**Lines 128-142** (`_chain_seeds`)

```python
for seed in sorted_seeds:
    d_start, d_end = seed[0], seed[1]
    if filtered:
        prev = filtered[-1]
        if d_start >= prev[0] and d_end <= prev[1]:
            continue
        if prev[0] >= d_start and prev[1] <= d_end:
            filtered[-1] = seed
            continue
    filtered.append(seed)
```

This only checks containment against the *immediately previous* filtered seed. A seed can be contained in one that is two or more positions earlier in `filtered`. Example (sorted by d_end):
- Seed A: [0, 50]
- Seed B: [10, 30]   -- contained in A, correctly skipped
- Seed C: [5, 45]    -- contained in A, but only compared against the *last* filtered entry

Wait -- actually, since B is skipped, the last filtered entry is still A, so C *is* compared against A. The logic works correctly as long as the "replace" case (line 137-139) doesn't introduce a narrower seed that then fails to catch a later containment.

On closer inspection: The replace case fires when `prev[0] >= d_start and prev[1] <= d_end`, replacing the narrow `prev` with the wider current seed. This could cause a seed added *before* prev to now contain `prev`'s replacement... but since the replacement is *wider*, not narrower, previous non-contained seeds remain non-contained. So containment is monotonically preserved.

**Revised assessment:** After careful analysis, this pre-filter is actually correct for its purpose (removing obviously contained seeds). The DP handles any remaining overlaps. Downgrading to **P3** -- the comment "fast pre-filter only" is accurate, but could be more explicit about why adjacent-only checking suffices.


### 5. [P3 - Minor] Early termination uses raw seed coverage (overcounts due to overlaps)

**Lines 423-424** (`align_pair`)

```python
raw_coverage = sum(length for _, _, length in raw_seeds) / d_len
```

After the `(d_start, s_start)` dedup, seeds can still overlap heavily in digest coordinates. Summing their lengths gives an *overestimate* of actual coverage. This means the early termination check (`raw_coverage < SHARED_TRADITION_THRESHOLD`) fires less often than it should, allowing more pairs through to the expensive extend/chain steps.

**Impact:** False negatives for early termination are safe (just slower, not incorrect). But for 28K pairs, some of which have sparse seeds on large texts, tightening this could save meaningful wall-clock time. Computing the actual non-overlapping coverage here (e.g., via a sorted merge) would be O(n log n) -- cheap compared to the extend/chain that follows.


### 6. [P3 - Minor] `_phonetic_table` global is not process-safe with multiprocessing

**Lines 194-202**

```python
_phonetic_table: dict[str, set[str]] | None = None

def _get_phonetic_table() -> dict[str, set[str]]:
    global _phonetic_table
    if _phonetic_table is None:
        _phonetic_table = build_equivalence_table()
    return _phonetic_table
```

In the multiprocessing path (`Pool`), each worker is a separate process (macOS `spawn`). The module-level `_phonetic_table` starts as `None` in each worker. If `align_pair` calls `_get_phonetic_table()` inside a worker, each worker independently builds the table by parsing the DDB JSON file.

**Impact:** Building the table is I/O-bound (reading a ~5MB JSON file) and takes ~0.2s. With 16 workers, that's 16 parallel file reads at startup. Not catastrophic, but wasteful. More importantly, `build_equivalence_table()` logs a message each time, so the log output is noisy.

**In practice:** The phonetic table is only accessed when `do_phonetic` is True, which is gated by `ENABLE_PHONETIC_SCAN` and `skip_phonetic_rescan`. For phonetic-origin pairs, `skip_phonetic_rescan=True`, so it's only triggered for non-phonetic pairs. If most pairs go through the early termination path (line 429), few workers actually build it.

**Suggestion:** Consider initializing the phonetic table in a Pool initializer (like `_ngram_set_init` in `fingerprint.py`) to load it once per worker at startup rather than lazily. Or pass it as part of the args for the pairs that need it.


### 7. [P3 - Minor] `_cached_source_table` global may cause stale cache across test runs

**Lines 571-574**

```python
_cached_source_table: tuple[str, int, dict] | None = None
```

This module-level cache persists across test functions in the same process. If test A aligns source "X" and test B aligns a *different* source also named "X" (same `source_id`), test B will get test A's k-gram table, which is built from a different text.

**Impact:** Only affects tests, not production (where source_id is a unique CBETA ID like "T08n0223"). But it's a latent footgun for future test authors who might reuse generic IDs like "s".

**Note:** The existing tests use `align_pair` directly (which doesn't go through `_align_pair_wrapper`), so this cache is not exercised. But `test_align_candidates_zero_workers` does use `align_candidates` -> `_align_pair_wrapper`, which hits this cache. The test texts are sufficiently distinct that it works by coincidence.


### 8. [P3 - Minor] `_find_phonetic_seeds` has O(d_len * s_len) worst case

**Lines 210-285**

The function iterates over each digest position (O(d_len)) and for each, checks candidate source positions by syllable. In the worst case (every character maps to the same syllable), every digest position checks every source position, giving O(d_len * s_len * k) time.

**Impact:** This is mitigated by:
(a) Only running on "novel" segments (typically short -- a few hundred chars max).
(b) The phonetic table has ~559 chars with ~200 syllable groups, so collisions are limited.
(c) `PHONETIC_MAX_SYLLABLES=5` caps per-char fan-out.

In practice this is fine for the dharani detection use case. But if novel segments ever become large (e.g., a 10K-char novel segment against a 286K-char source), this could become expensive. The source text passed in is the *full* source (`source_text`), not just a local region.


### 9. [P3 - Minor] `_extend_seeds` does not merge overlapping extended seeds before chaining

**Lines 72-106**

After fuzzy extension, two seeds that were originally distinct may now overlap in digest coordinates. The list is passed directly to `_chain_seeds`, which handles overlaps via DP. But the DP's time is O(n^2) in the number of seeds if many overlap (binary search reduces it to O(n log n) for well-separated seeds, but the containment pre-filter in `_chain_seeds` only catches adjacent containments).

**Impact:** For texts with dense seed regions (common in CJK text alignment where many 5-grams match), the extended seed list can be large. The containment pre-filter helps, but a merge pass (combining extended seeds on the same diagonal that now overlap) would reduce the input to `_chain_seeds` substantially.


### 10. [P3 - Minor] `imap_unordered` loses deterministic ordering

**Lines 672-678**

```python
for result in tqdm(
    pool.imap_unordered(_align_pair_wrapper, args_list),
    ...
):
    results.append(result)
```

`imap_unordered` returns results in completion order, not submission order. The output `results` list has nondeterministic ordering. This is fine if downstream code doesn't depend on order (the scoring stage processes each result independently). But it makes debugging harder -- re-running the same input can produce different result orderings.

**Impact:** Low. The scoring stage indexes by `(digest_id, source_id)` pairs. But for reproducible debugging, `imap` (ordered) would be better, at the cost of slightly worse throughput if tasks have high variance in runtime.


### 11. [P4 - Style] Early termination comment says "below SHARED_TRADITION_THRESHOLD" but the gate is `raw_coverage < config.SHARED_TRADITION_THRESHOLD and not do_phonetic`

**Lines 419-429**

The comment on line 419 says:
> "if raw seed coverage is below SHARED_TRADITION_THRESHOLD and phonetic rescan won't run"

This is accurate but could be clearer. The actual condition is a conjunction: low coverage AND no phonetic rescan. A reader might wonder why we don't also early-terminate when phonetic rescan is enabled but coverage is zero -- the answer is that phonetic rescan might find matches where exact seeds didn't.

**Suggestion:** Add a one-line comment: `# Phonetic rescan can find matches missed by exact seeds, so don't skip.`


### 12. [P4 - Style] `_build_kgram_table` duplicates logic in `fast_find_seeds`

**Lines 30-36** (`_build_kgram_table`) vs. **`_fast_fallback.py` lines 59-63**

Both build the same `defaultdict(list)` k-gram table. `_build_kgram_table` exists only to be called from `_align_pair_wrapper` for caching. The duplication is minor but could lead to divergence if the table format changes.

**Suggestion:** Have `_build_kgram_table` be the single source of truth, and have `fast_find_seeds` accept an optional pre-built table (which it already does).


### 13. [P4 - Style] Type annotations could be tightened

**Line 574:**
```python
_cached_source_table: tuple[str, int, dict] | None = None
```

The `dict` here is `dict[str, list[int]]` (a k-gram table). Using the precise type would aid readability and catch misuse.


### 14. [P4 - Style] `_phonetic_rescan` does not validate that chained seeds are within novel segment bounds

**Lines 335-375**

The chained seeds come from `_find_phonetic_seeds(novel_text, source_text, ...)` where `novel_text` is a substring. The `d_start`/`d_end` in the chained results are offsets within `novel_text`, and `s_start`/`s_end` are offsets within `source_text`. The code correctly adjusts digest coordinates via `seg.digest_start + d_start`. But there's no assertion that `d_end <= len(novel_text)` or `s_end <= len(source_text)`. An off-by-one error in `_find_phonetic_seeds` or `_chain_seeds` could silently produce out-of-bounds slicing (Python silently truncates string slices, masking the bug).

**Suggestion:** Add debug assertions:
```python
assert d_end <= len(novel_text), f"phonetic seed d_end {d_end} > {len(novel_text)}"
assert s_end <= len(source_text), f"phonetic seed s_end {s_end} > {len(source_text)}"
```


### 15. [P4 - Style] `align_candidates` clears `_phonetic_table` but not `_cached_source_table`

**Lines 680-682**

```python
global _phonetic_table
_phonetic_table = None
```

The phonetic table is cleared after alignment (good -- frees memory). But `_cached_source_table` is *not* cleared. In the main process (serial path), it holds a reference to the last source's k-gram table. For a large source (~286K chars, k=5), this table can be 50-100 MB.

**Impact:** The main process cache is only used in the serial path. In the multiprocessing path, each worker has its own cache which is freed when the Pool terminates. In the serial path, the single cache entry is bounded (only one source table at a time). Still, explicitly clearing it at the end of `align_candidates` would be good hygiene, matching the phonetic table cleanup.

---

## Summary Table

| # | Severity | Category | Summary |
|---|----------|----------|---------|
| 1 | **P1** | Correctness | DP backtracking can miss optimal chain; needs `prev[]` array |
| 2 | **P2** | Correctness | `_find_seeds` keeps only best match per d_pos, losing multi-site seeds |
| 3 | **P2** | Performance | Seed dedup key `(d_start, s_start)` is ineffective; overlapping seeds inflate extend/chain work |
| 4 | **P3** | Correctness | `_chain_seeds` containment pre-filter is adjacent-only (actually OK -- revised from P2) |
| 5 | **P3** | Performance | Raw coverage overcounts overlaps, weakening early termination |
| 6 | **P3** | Multiprocessing | Phonetic table rebuilt independently in each worker process |
| 7 | **P3** | Testing | `_cached_source_table` persists across tests; latent footgun |
| 8 | **P3** | Performance | `_find_phonetic_seeds` is O(d*s*k) worst case on full source text |
| 9 | **P3** | Performance | Extended seeds not merged before chaining; inflates DP input |
| 10 | **P3** | Reproducibility | `imap_unordered` gives nondeterministic result ordering |
| 11 | **P4** | Documentation | Early termination comment could be clearer about phonetic gate |
| 12 | **P4** | Duplication | `_build_kgram_table` duplicates logic in `fast_find_seeds` |
| 13 | **P4** | Type safety | `_cached_source_table` type annotation is imprecise |
| 14 | **P4** | Robustness | No bounds assertions on phonetic rescan output |
| 15 | **P4** | Memory | `_cached_source_table` not cleared at end of `align_candidates` |

---

## Things Done Well

- **Weighted interval scheduling via DP** is the right algorithm for non-overlapping seed selection. The use of `bisect_right` for predecessor lookup is clean and efficient.
- **Source table caching** in `_align_pair_wrapper` with LPT scheduling (largest sources first, sorted by source_id) is a clever optimization that avoids rebuilding the k-gram table for consecutive same-source pairs.
- **Early termination** for low-overlap pairs is a smart performance heuristic that avoids expensive extend/chain/phonetic work.
- **Fuzzy extension with gap handling** (single-char insertions/deletions via the gap_d/gap_s lookahead) is well-designed for Chinese text where translators may insert/omit individual characters.
- **Phonetic rescan architecture** -- running only on novel segments, gating on `ENABLE_PHONETIC_SCAN`, skipping for phonetic-origin pairs -- shows careful thought about when the expensive phonetic pass is worthwhile.
- **`maxtasksperchild=100`** prevents memory leaks from accumulating across long-lived workers.
- **Test coverage** is solid: edge cases (empty digest, zero workers, short texts), early termination, pre-filtering, and source region counting are all tested.
