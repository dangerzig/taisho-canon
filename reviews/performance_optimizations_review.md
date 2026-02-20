# Performance Optimizations Code Review

**Commit:** `2ad9ce4` - Add performance optimization: disk cache, dynamic chunksize, collision monitoring
**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19

## Scope of Changes

| File | Summary |
|------|---------|
| `digest_detector/candidates.py` | Replaced inverted index with set-intersection containment; parallelized `generate_candidates()` and `generate_phonetic_candidates()` with Pool+initializer; replaced `hash()` with `stable_hash()` |
| `digest_detector/align.py` | Added early termination in `align_pair()`; added `skip_phonetic_rescan` flag; LPT scheduling in `align_candidates()`; pre-filter zero-containment docNumber pairs |
| `digest_detector/pipeline.py` | Wired `num_workers` through to `generate_candidates()`; added disk cache (`PipelineCache`); added `--no-cache` CLI flag |
| `digest_detector/cache.py` | New file: disk cache with version, config snapshot, corpus hash |
| `tests/test_candidates.py` | Added `TestGenerateCandidatesDegenerate`, `TestGenerateCandidatesParallel`; updated all existing tests from `build_inverted_index` to `build_ngram_sets` |
| `tests/test_align.py` | Added `TestEarlyTermination` (2 tests) |
| `tests/test_phonetic_candidates.py` | Added `test_t250_t901_containment_score` |

---

## 1. Correctness

### Grade: A-

#### 1.1 `stable_hash()` usage -- CRITICAL BUG FIX (A+)

The old `candidates.py` used Python's built-in `hash()` at line 132 of the prior version:

```python
# OLD (HEAD~1) - candidates.py line 132
h = hash(content[i:i + n])
```

The new code correctly uses `stable_hash()`:

```python
# NEW - candidates.py line 72
h = stable_hash(jing_text[i:i + n])
```

This is the single most important fix in this commit. Python's `hash()` is randomized per-process (PEP 456), and macOS uses `spawn` for multiprocessing, so cross-process hash values would be inconsistent. The old code was serial so this didn't bite, but the new parallel path would have been silently broken without this fix. `stable_hash()` uses `zlib.crc32()` which is deterministic. Correctly done.

Additionally, the worker builds digest n-gram hashes from `jing_text` (not `full_text`), which is consistent with the old inverted-index approach and the design intent of excluding preface material.

#### 1.2 Parallel data sharing in `_candidate_worker` (A)

The Pool+initializer pattern is correctly implemented:

```python
# candidates.py lines 34-52
def _candidate_init(stopgrams, source_ids, source_lens, source_sets, ...):
    global _cand_stopgrams, _cand_source_ids, ...
    _cand_stopgrams = stopgrams
    ...
```

On macOS `spawn`, the initializer runs once per worker process, setting module-level globals. The worker function reads these globals as local aliases (lines 58-64), which is idiomatic and efficient. The data passed via `initargs` is pickled once to each worker at pool creation, not per-task. This avoids the O(tasks * data_size) pickling cost.

One subtlety: the `source_sets_arr` contains `frozenset[int]` objects. These are large but immutable, and pickle handles them correctly. On `fork` (Linux), they'd be copy-on-write shared; on `spawn` (macOS), each worker gets a full copy. This is the expected tradeoff -- there's no way around it with `spawn` without shared memory, and the frozensets are read-only.

**No race conditions**: each worker processes a different digest and reads (never writes) the shared source arrays. The results are collected via `imap_unordered` in the main process, which is thread-safe.

#### 1.3 Early termination logic (A-)

```python
# align.py lines 493-516
if raw_seeds:
    raw_coverage = sum(length for _, _, length in raw_seeds) / d_len
else:
    raw_coverage = 0.0

do_phonetic = config.ENABLE_PHONETIC_SCAN and not skip_phonetic_rescan
if raw_coverage < config.SHARED_TRADITION_THRESHOLD and not do_phonetic:
    # Return a single novel segment covering the whole digest
    ...
```

**The overcounting concern**: `raw_coverage` sums the `length` field of all raw seeds, which can include overlapping seeds. For example, if digest positions 0-9 are covered by two overlapping seeds (0,5,10) and (3,8,10), raw_coverage would count 20 chars covered instead of 10. This means `raw_coverage` is an *upper bound* on true coverage.

**Is this safe?** Yes, conservatively so. The early termination fires when `raw_coverage < 0.10`. Since raw_coverage overcounts, the true coverage is even lower than the computed value. So if the overcounted estimate is below 0.10, the true non-overlapping coverage is definitely below 0.10. The early termination will never fire on a pair that would have achieved >= 0.10 coverage after proper chaining. **No false positives**.

However, there's a subtle interaction: the second condition gate (lines 519-525):

```python
if raw_coverage >= config.SHARED_TRADITION_THRESHOLD:
    extended = _extend_seeds(digest_text, source_text, raw_seeds)
    chained = _chain_seeds(extended, d_len)
else:
    chained = []
```

This means when `do_phonetic` is True and `raw_coverage < 0.10`, we skip extend/chain but still run phonetic rescan. Due to overcounting, it's possible that raw_coverage slightly overcounts past 0.10 while true coverage is below 0.10 -- in that case we'd do extend/chain unnecessarily but harmlessly. The only risk would be if overcounting caused us to *skip* phonetic rescan, but that path is gated by `do_phonetic`, not by raw_coverage. So this is safe.

**One edge case**: if `SHARED_TRADITION_THRESHOLD` were ever raised significantly (say to 0.30), the overcounting could start to matter -- pairs with true coverage around 0.15-0.29 might be overcounted past 0.30, causing them to go through extend/chain when they'd produce only `shared_tradition` classifications. This is wasteful but not incorrect. At the current 0.10 threshold, this is a non-issue.

#### 1.4 `skip_phonetic_rescan` interaction with `ENABLE_PHONETIC_SCAN` (A)

```python
do_phonetic = config.ENABLE_PHONETIC_SCAN and not skip_phonetic_rescan
```

This is correct:
- If `ENABLE_PHONETIC_SCAN = False`: `do_phonetic = False` regardless of `skip_phonetic_rescan`
- If `ENABLE_PHONETIC_SCAN = True` and `skip_phonetic_rescan = True`: `do_phonetic = False` (skip for phonetic-origin pairs)
- If `ENABLE_PHONETIC_SCAN = True` and `skip_phonetic_rescan = False`: `do_phonetic = True` (normal rescan)

The `skip_phonetic` flag is set in `align_candidates()` at line 691:

```python
skip_phonetic = cand.from_phonetic
```

This correctly avoids redundant phonetic rescanning for pairs that were already discovered through phonetic candidate generation. Such pairs already have phonetic overlap established -- running the expensive `_find_phonetic_seeds()` again on their novel segments would be duplicative work.

#### 1.5 LPT scheduling sort (A)

```python
# align.py line 707
args_list.sort(key=lambda a: len(a[2]) * len(a[3]), reverse=True)
```

This sorts by estimated alignment cost (digest_len * source_len) descending, implementing Longest Processing Time (LPT) scheduling. This is a well-known heuristic for load balancing in multiprocessing.

**Does this change alignment results?** No. Each pair is aligned independently, and `align_candidates` returns results collected via `imap_unordered` (which already doesn't preserve order). The results list is unordered regardless. Downstream scoring in `score_all()` sorts by confidence, so the LPT reordering is invisible to the final output.

#### 1.6 Pre-filter zero-containment docNumber pairs (B+)

```python
# align.py lines 682-688
if (cand.containment_score == 0.0
        and cand.from_docnumber
        and not cand.from_phonetic
        and (cand.digest_id, cand.source_id) not in phonetic_pairs
        and d_len > 5000 and s_len > 5000):
    skipped += 1
    continue
```

**Concern: potential false negatives.** This skips docNumber pairs with zero n-gram containment where both texts are > 5000 chars. The rationale is: if two large texts share zero n-gram fingerprint overlap, alignment will almost certainly find nothing meaningful.

However, there are edge cases to consider:
- **Retranslations with completely different Chinese phrasing**: Two translations of the same Sanskrit source with zero 5-gram overlap. These are possible for highly divergent translators (e.g., early vs. late Chinese Buddhist translation conventions). For texts > 5000 chars, it's unlikely they share *zero* 5-grams if related, so this is probably safe in practice.
- **The 5000-char threshold is arbitrary**: Why 5000? For smaller texts, zero-containment docNumber pairs are still checked (good), but the threshold isn't documented or configurable. A brief comment explaining the rationale would help.

The filter is conservative -- it only fires when *all five conditions* are true. The `not cand.from_phonetic` and `not in phonetic_pairs` guards ensure phonetic discoveries are never filtered. This is well-designed.

**One minor issue**: the `d_len` and `s_len` used in the filter come from `len(d_text.jing_text)` and `len(s_text.full_text)` respectively (lines 677-678). This is an asymmetric comparison -- digest uses jing length, source uses full text length. This is probably intentional (consistent with how alignment uses these), but it means a source with a 6000-char preface and 3000-char jing body would not be filtered (s_len = 9000 > 5000), even though the meaningful alignment target is only 3000 chars. This is fine since it errs on the side of *not* filtering.

#### 1.7 Subtle behavioral change: `ngram_sets` vs inverted index

The old code used an inverted index: `hash -> [(text_id, position)]`. The new code uses per-text frozensets: `text_id -> frozenset[int]`. This changes how containment is counted:

- **Old**: For each digest n-gram, look up matching texts in the inverted index, count each source once per n-gram position.
- **New**: For each digest, compute the n-gram set (deduplicating positions), then intersect with each source's set.

The key difference: if a digest n-gram appears at positions 5 and 15 in the digest, the old code counted it twice in `total_ngrams` but the set-based approach counts it once. This means containment scores could differ slightly for digests with repeated n-grams.

In practice, this is a very minor difference and arguably the set-based approach is more correct (it measures "what fraction of *distinct* n-grams are shared" rather than "what fraction of n-gram *positions* are shared"). The parallel equivalence test confirms serial and parallel paths agree.

---

## 2. Robustness

### Grade: B+

#### 2.1 `num_workers=0` or negative values (B-)

None of the functions validate `num_workers` against invalid values:

```python
# candidates.py line 192-193
if num_workers is None:
    num_workers = config.NUM_WORKERS or cpu_count()
```

If `num_workers=0`, the code hits `num_workers > 1` checks and falls through to the serial path -- which works, but only by accident. If `num_workers=-1`, same behavior (serial path), again by accident.

However, if someone passes `num_workers=0` to `Pool(0)` (in align.py line 717 where the check is `num_workers <= 1`), it would actually create a pool with 0 workers, which would hang or error. Wait -- looking more carefully, align.py line 713 checks `if num_workers <= 1:` and takes the serial path, so 0 and negative values are safe there.

In `candidates.py`, line 239 checks `num_workers > 1 and len(digest_candidates) >= 10`, so 0 and negative values take the serial path.

**Verdict**: Works by accident but should defensively clamp. Not a real-world problem since the pipeline defaults to `cpu_count()` and the CLI takes `int` arguments, but a `max(1, num_workers)` guard would be cleaner.

#### 2.2 Empty inputs (A)

The code handles degenerate cases well:
- `candidates.py:66-67`: Short `jing_text` (< n chars) returns empty list
- `candidates.py:76-77`: Empty `digest_hashes` after stopgram filtering returns empty
- `align.py:484-485`: Empty digest text returns empty `AlignmentResult`
- `candidates.py:380-382`: No texts with transliteration regions returns early
- The `TestGenerateCandidatesDegenerate` class explicitly tests empty ngram_sets and empty frozensets

#### 2.3 Module-level global mutation (B)

The serial path in `generate_candidates()` mutates module-level globals:

```python
# candidates.py lines 257-265
global _cand_stopgrams, _cand_source_ids, ...
_cand_stopgrams = stopgrams
_cand_source_ids = source_ids_arr
...
```

This is fine for single-threaded use but means:
1. The module retains references to potentially large data structures after the function returns
2. Concurrent calls to `generate_candidates()` from different threads would clobber each other's globals

Issue (1) is a minor memory concern -- the globals persist for the lifetime of the module. Issue (2) is theoretical since the pipeline is single-threaded, but it's worth noting as technical debt. The existing codebase (`fingerprint.py` lines 151-154) already follows this pattern, so this is consistent.

#### 2.4 Pickle safety with disk cache (B+)

The `PipelineCache` uses `pickle` for serialization. This is fine for a local disk cache but has known concerns:
- `pickle.HIGHEST_PROTOCOL` may change across Python versions
- The `CACHE_VERSION = 2` mechanism handles field changes but not Python version changes

The `_config_snapshot()` correctly captures all Stage 1-2b parameters that affect output. The corpus hash uses `mtime_ns` and `st_size` rather than content hashing, which is much faster but could miss content changes that preserve timestamps (extremely unlikely in practice).

---

## 3. Efficiency

### Grade: A

#### 3.1 Set intersection vs inverted index (A+)

The core algorithmic change -- replacing the inverted index with per-text frozenset intersection -- is excellent. The old approach:
1. Built a massive inverted index: O(total_ngrams) space, O(total_ngrams) time
2. For each digest n-gram, scanned all matching (source_id, position) pairs
3. Required per-n-gram source deduplication via temporary sets

The new approach:
1. Builds per-text frozensets: O(distinct_ngrams_per_text * num_texts) space
2. Uses `frozenset.__and__()` for intersection: C-level set operation
3. One set intersection per (digest, source) pair

The memory reduction is dramatic: the old inverted index stored `(source_id, position)` tuples for every n-gram occurrence, potentially 48M+ entries for the full corpus. The new frozensets store only distinct hashes, drastically reducing memory.

#### 3.2 Binary search pre-filter (A)

```python
# candidates.py lines 82-89
lo, hi = 0, len(source_lens_arr)
while lo < hi:
    mid = (lo + hi) // 2
    if source_lens_arr[mid] < min_source_len:
        lo = mid + 1
    else:
        hi = mid
```

This correctly implements `bisect_left` to find the first source meeting the minimum size ratio. Combined with the ascending-sorted source arrays, this skips all sources too short to qualify. For a corpus with many small texts, this can skip a large fraction of comparisons.

Minor style note: this could use `bisect.bisect_left(source_lens_arr, min_source_len)` from the stdlib, which is the same algorithm but more readable and possibly slightly faster (C implementation). Not a bug, just a missed opportunity.

#### 3.3 Dynamic chunksize (A-)

```python
chunksize = max(1, len(worker_args) // (num_workers * 4))
```

This formula aims to create ~4x as many chunks as workers, balancing task granularity against IPC overhead. For 100 digests and 4 workers, this gives chunksize=6, meaning ~17 tasks of 6 items each. This is reasonable.

However, the formula is applied identically in all three parallel paths (candidates, phonetic regions, and doc frequencies). The optimal chunksize can vary significantly: candidate scoring is CPU-heavy per digest (set intersection against all sources), while phonetic region detection is lighter per text. A single formula is a reasonable default, but the comment could note this is a heuristic.

#### 3.4 LPT scheduling (A)

Sorting by `len(a[2]) * len(a[3])` descending before `imap_unordered` is textbook LPT scheduling. The alignment cost is dominated by `_find_seeds`, which is O(d_len * s_len / k) in the worst case, so the product is a good cost proxy. Starting expensive pairs first minimizes tail latency.

#### 3.5 Missed optimization: parallel phonetic containment scoring (B+)

The phonetic containment scoring in `generate_phonetic_candidates()` (lines 420-461) remains serial -- it iterates all pairs of texts with phonetic regions sequentially. For a large corpus with many texts containing transliteration regions, this could become a bottleneck. The per-text region detection is parallelized (good), but the O(n^2) pairwise scoring is not.

In practice, the number of texts with indexable transliteration regions is typically small (the project notes ~559 chars across the corpus), so this is unlikely to matter. But it's worth noting as a future optimization point if the corpus grows.

---

## 4. Legibility

### Grade: A-

#### 4.1 Code clarity and comments (A)

The code is well-commented throughout. Key design decisions are documented inline:

```python
# Skip the expensive extend/chain steps.    (align.py:490)
# Seeds too sparse for useful extend/chain  (align.py:524)
# LPT scheduling -- sort by estimated cost  (align.py:705)
# min 2 so that with tiny corpora...        (candidates.py:402)
```

The module docstrings are updated to reflect the new approach ("n-gram set intersection" vs "inverted index"). Function signatures are well-typed with type hints.

#### 4.2 Naming (A-)

Variable names are descriptive and consistent:
- `source_ids_arr`, `source_lens_arr`, `source_sets_arr` -- the `_arr` suffix signals these are parallel arrays
- `_cand_*` prefix for candidate worker globals vs `_worker_*` for phonetic worker globals -- clear namespace separation
- `do_phonetic` is concise and readable

One naming concern: the `_candidate_init` / `_candidate_worker` naming parallels `_phonetic_init` / `_phonetic_region_worker`, but the latter has `_region_` in the name while the former doesn't. Minor inconsistency.

#### 4.3 Step numbering in `align_candidates` (B+)

The inline comments reference "Step 3", "Step 4", "Step 6" but the numbering is non-sequential:

```python
# Step 6: Pre-filter zero-containment docNumber pairs  (line 679)
# Step 4: skip phonetic rescan for phonetic-origin pairs (line 691)
# Step 3: LPT scheduling  (line 705)
```

Steps are numbered 6, then 4, then 3 -- reverse order. This suggests the step numbers refer to some external document or the order of *importance*, not execution order. Either renumber them sequentially or add a comment explaining the numbering scheme.

#### 4.4 Consistency with existing patterns (A)

The Pool+initializer pattern in `candidates.py` exactly mirrors the pattern already established in `fingerprint.py` (lines 30-40, 113-127). The serial-path global-setting pattern is also consistent. This makes the codebase feel cohesive.

---

## 5. Test Coverage

### Grade: B+

#### 5.1 What's covered (A)

| Test | Coverage |
|------|----------|
| `TestGenerateCandidatesParallel::test_parallel_equivalence` | Serial vs parallel candidate results match (pairs + scores) |
| `TestGenerateCandidatesDegenerate::test_empty_ngram_sets` | Empty input edge case |
| `TestGenerateCandidatesDegenerate::test_text_with_empty_frozenset` | Empty frozenset edge case |
| `TestEarlyTermination::test_low_overlap_returns_early` | Zero-overlap early termination with `skip_phonetic_rescan=True` |
| `TestEarlyTermination::test_does_not_skip_real_matches` | Shared content NOT early-terminated |
| `test_t250_t901_containment_score` | Real-data phonetic containment above threshold |

The parallel equivalence test is particularly well-designed: it creates 16 texts (15 base + 1 source), exceeding the `>= 10` threshold for parallel execution, and verifies both pair sets and containment scores match between `num_workers=1` and `num_workers=2`.

#### 5.2 What's missing (B-)

1. **No test for `skip_phonetic_rescan=False` with `ENABLE_PHONETIC_SCAN=True`**: The early termination test only checks the `skip_phonetic_rescan=True` path. There should be a test verifying that when `skip_phonetic_rescan=False` and `ENABLE_PHONETIC_SCAN=True`, the phonetic rescan *does* run on low-overlap pairs (i.e., early termination does NOT fire).

2. **No test for the pre-filter in `align_candidates`**: The zero-containment docNumber pair filter (Step 6) with the 5000-char threshold has no direct test. Adding a test that creates a zero-containment docNumber pair with both texts > 5000 chars and verifying it's skipped would be valuable.

3. **No test for `num_workers=0`**: As noted in Robustness, invalid worker counts are untested. A test asserting that `num_workers=0` or `num_workers=-1` doesn't crash (falls through to serial) would document the intended behavior.

4. **No test for LPT sort stability**: While LPT shouldn't change results, a test verifying that the sort order doesn't affect the final set of `AlignmentResult` objects would provide regression safety.

5. **No test for the `raw_coverage` overcounting edge case**: A test with deliberately overlapping seeds (e.g., a digest where the same 5-gram appears at multiple positions) to verify the early termination still behaves correctly would strengthen confidence.

6. **No test for disk cache**: The `PipelineCache` class has no unit tests. While it's somewhat integration-level, testing `is_valid()` with stale config, wrong version, and missing files would prevent cache-related regressions.

7. **Phonetic candidate parallelism**: `generate_phonetic_candidates` with `num_workers > 1` is not tested for parallel equivalence (only the Stage 2 candidates have this test).

---

## Specific Issues Found

### Issue 1: `pair_key` computed but unused in `_candidate_worker` (Minor)

```python
# candidates.py line 99
pair_key = (d_id, source_id)
```

This `pair_key` is computed on line 99 but only used on line 108 for `from_docnumber=pair_key in docnum_pair_set`. The variable is fine functionally, but the name `pair_key` suggests it might be used for deduplication (as it is in the caller), which could confuse a reader. The worker doesn't deduplicate -- deduplication happens in the main process via `seen_pairs`. This is correct (each worker processes a different digest, so no duplicates within a worker), but the dead-looking `pair_key` variable could benefit from a brief comment.

### Issue 2: Source arrays include digest texts (Cosmetic)

```python
# candidates.py lines 220-224
source_entries = sorted(
    [(tid, length_map.get(tid, 0), ngram_sets[tid])
     for tid in ngram_sets if ngram_sets[tid]],
    key=lambda x: x[1],
)
```

The "source" arrays include *all* texts (including digests). The worker then skips self-comparison at line 94 (`if source_id == d_id: continue`). This works but means every digest compares against itself in the source list and wastes one iteration. For ~8,900 texts this is negligible, but a comment noting "source arrays include all texts; self-pairs are skipped in the worker" would clarify.

### Issue 3: `length_map.get(tid, 0)` could produce 0-length source entries (Minor)

```python
# candidates.py line 221
length_map.get(tid, 0)
```

If a text_id exists in `ngram_sets` but not in `length_map`, its length defaults to 0. Such an entry would never pass the binary search filter (since `0 < min_source_len` for any digest), so it's harmless. But it shouldn't happen in practice since both maps are built from the same `texts` list. Defensive but correct.

### Issue 4: The `from_docnumber` flag is set in the worker but checked in the caller (Cosmetic)

In `_candidate_worker` (line 108):
```python
from_docnumber=pair_key in docnum_pair_set,
```

And in `generate_candidates` (line 276):
```python
for d_id, s_id in docnum_pairs:
    pair_key = (d_id, s_id)
    if pair_key not in seen_pairs:
        ...
```

The docNumber flag is set correctly in the worker, and docNumber-only pairs (zero containment) are added separately in the main function. This dual-path approach is correct -- fingerprinting may find a pair that also has a docNumber cross-reference, and those pairs get `from_docnumber=True` from the worker. Pairs found *only* via docNumber (zero fingerprint overlap) are added in the second pass.

### Issue 5: `_align_pair_wrapper` unpacks 5-tuple now (Correct)

```python
# align.py lines 640-644
def _align_pair_wrapper(args):
    digest_id, source_id, digest_text, source_text, skip_phonetic = args
    return align_pair(digest_text, source_text, digest_id, source_id,
                      skip_phonetic_rescan=skip_phonetic)
```

The old code unpacked 4-tuple, new code unpacks 5-tuple. The `args_list.append()` at line 693-699 correctly builds the 5-tuple. Consistent and correct.

---

## Summary of Grades

| Category | Grade | Notes |
|----------|-------|-------|
| **Correctness** | **A-** | Critical `hash()` -> `stable_hash()` fix; early termination overcounting is safe; all parallel patterns correct |
| **Robustness** | **B+** | Good empty-input handling; no `num_workers` validation; module globals persist |
| **Efficiency** | **A** | Set intersection is dramatically better; binary search pre-filter; LPT scheduling; dynamic chunksize |
| **Legibility** | **A-** | Well-commented; consistent patterns; minor step-numbering confusion |
| **Test Coverage** | **B+** | Strong parallel equivalence test; gaps in pre-filter testing, cache testing, and edge cases |

---

## Recommendations (Priority Order)

1. **Add `max(1, num_workers)` guard** in each function's `num_workers` handling to prevent accidental Pool(0) or Pool(-1) creation. Low effort, high defensive value.

2. **Add a test for the align_candidates pre-filter**: Create a zero-containment docNumber pair with both texts > 5000 chars and verify it's excluded from the alignment args_list.

3. **Add a test for early termination with `do_phonetic=True`**: Verify that when `skip_phonetic_rescan=False` and `ENABLE_PHONETIC_SCAN=True`, low-overlap pairs still proceed to phonetic rescan rather than early-terminating.

4. **Replace manual binary search with `bisect.bisect_left`**: One-line change, more readable, uses C implementation.

5. **Add `PipelineCache` unit tests**: Test `is_valid()` with various invalid states (wrong version, changed config, missing files).

6. **Renumber steps in `align_candidates`**: Change the Step 6/4/3 comments to sequential numbering (Step 1/2/3) or remove step numbers entirely.

7. **Consider `bisect_left` for the source length binary search**: `from bisect import bisect_left; lo = bisect_left(source_lens_arr, min_source_len)` is equivalent to the current 8-line binary search and is more idiomatic Python.

8. **Document the 5000-char threshold**: Add a config constant (e.g., `DOCNUM_PREFILTER_MIN_LEN = 5000`) with a comment explaining why this threshold exists.

---

## Overall Assessment

This is a well-executed performance optimization that addresses a real bottleneck (the O(total_ngrams) inverted index) with a cleaner algorithmic approach (per-text frozenset intersection). The parallelization is correctly implemented using the established Pool+initializer pattern, and the critical `hash()` -> `stable_hash()` fix prevents a subtle but devastating multiprocessing bug.

The early termination and pre-filtering optimizations are conservatively designed -- they can only produce false negatives (skipping work that would be useless), never false positives (incorrectly classifying real relationships). The LPT scheduling is a nice touch for load balancing.

The main areas for improvement are defensive validation of `num_workers`, additional test coverage for the new filtering/pre-filtering paths, and minor readability improvements (step numbering, stdlib bisect). None of these are blocking issues.
