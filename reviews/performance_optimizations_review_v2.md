# Performance Optimizations Code Review (v2)

**Previous review:** `reviews/performance_optimizations_review.md` (v1)
**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Test suite:** 202 tests, all passing

---

## Context

The v1 review identified eight recommendations. Six have been implemented:

| # | Recommendation | Status |
|---|---------------|--------|
| 1 | `max(1, num_workers)` guards | Fixed in `candidates.py` (lines 190, 344), `align.py` (line 663), `fingerprint.py` (lines 74, 147) |
| 2 | Test for `align_candidates` pre-filter | Fixed: 3 tests in `TestAlignCandidatesPrefilter` |
| 3 | Test for early termination with `do_phonetic=True` | Fixed: `test_low_overlap_with_phonetic_enabled` |
| 4 | Replace manual binary search with `bisect.bisect_left` | Fixed: `candidates.py` line 10, 85 |
| 5 | `PipelineCache` unit tests | **Not addressed** (not in scope of this review) |
| 6 | Renumber steps in `align_candidates` | Fixed: now sequential 1/2/3 |
| 7 | (Duplicate of #4 -- `bisect_left`) | Fixed |
| 8 | Document 5000-char threshold as config constant | Fixed: `DOCNUM_PREFILTER_MIN_LEN` in `config.py` (line 65), used in `align.py` (lines 689-690) |

Additionally, 2 new `num_workers=0` edge-case tests were added (`TestNumWorkersEdgeCases` in `test_align.py`).

This review re-examines all eight files with fresh eyes.

---

## 1. Correctness

### Grade: A

Every correctness concern from v1 has been addressed, and no new correctness issues were introduced.

#### 1.1 `stable_hash()` usage (unchanged, A+)

`candidates.py` line 73 and `fingerprint.py` lines 19-28 continue to use `zlib.crc32` via `stable_hash()`. The critical PEP 456 / macOS-spawn issue remains solved.

#### 1.2 Parallel data sharing (unchanged, A)

Pool+initializer pattern in `candidates.py` (lines 35-53) and `fingerprint.py` (lines 35-39) remains correct. Workers read module-level globals set by the initializer; no cross-worker mutation.

#### 1.3 Early termination logic (A)

```python
# align.py lines 493-516
do_phonetic = config.ENABLE_PHONETIC_SCAN and not skip_phonetic_rescan
if raw_coverage < config.SHARED_TRADITION_THRESHOLD and not do_phonetic:
    ...
```

The overcounting concern from v1 remains technically present (raw_coverage sums overlapping seeds) but remains safe for the same reason: overcounting produces an upper bound, so if the upper bound is below 0.10, true coverage is definitely below 0.10. No false positives from early termination.

The new test `test_low_overlap_with_phonetic_enabled` (line 164) directly verifies the `do_phonetic` gate: with `skip_phonetic_rescan=False` and `ENABLE_PHONETIC_SCAN=True`, low-overlap pairs proceed to phonetic rescan instead of early-terminating. This closes the coverage gap flagged in v1.

#### 1.4 `bisect_left` replacement (A+)

```python
# candidates.py lines 10, 83-85
from bisect import bisect_left
...
lo = bisect_left(source_lens_arr, min_source_len)
```

The hand-rolled 8-line binary search is replaced with the stdlib C implementation. Functionally identical (both find the leftmost insertion point), but more readable and slightly faster.

One subtlety: `bisect_left` finds the position where `min_source_len` would be inserted to keep the list sorted. Since `source_lens_arr` is sorted ascending and we want all sources with `source_lens_arr[idx] >= min_source_len`, starting iteration at `lo` is correct. (If `min_source_len` is, say, 600.0 and source_lens_arr contains `[100, 300, 600, 1000]`, `bisect_left` returns 2, and iterating from index 2 gives `[600, 1000]`.) Verified correct.

#### 1.5 Pre-filter now uses config constant (A)

```python
# align.py lines 689-690
and d_len > config.DOCNUM_PREFILTER_MIN_LEN
and s_len > config.DOCNUM_PREFILTER_MIN_LEN):
```

The hardcoded `5000` is replaced with `config.DOCNUM_PREFILTER_MIN_LEN`. The config constant includes a clear docstring (config.py lines 62-65). The filter logic is unchanged and remains conservative.

#### 1.6 Step renumbering (A)

```python
# align.py
# Step 1: Build set of phonetic pair keys (line 665)
# Step 2: Build args list, pre-filtering (line 669)
# Step 3: LPT scheduling (line 711)
```

Steps are now sequential 1/2/3 in execution order. Clear and unconfusing.

#### 1.7 `num_workers` clamping (A)

All five locations now have `max(1, num_workers)` after the `None` default:

```python
# candidates.py line 190
num_workers = max(1, num_workers)

# candidates.py line 344
num_workers = max(1, num_workers)

# align.py line 663
num_workers = max(1, num_workers)

# fingerprint.py line 74
num_workers = max(1, num_workers)

# fingerprint.py line 147
num_workers = max(1, num_workers)
```

This means `num_workers=0` or negative values are safely clamped to 1, taking the serial path. No more "works by accident" behavior.

#### 1.8 Remaining minor concern: `pair_key` variable in `_candidate_worker`

The `pair_key` variable at `candidates.py` line 95 is still computed for every (digest, source) pair but only used on line 104 for the `from_docnumber` check. This is correct but slightly misleading in name -- a reader might expect it to be used for deduplication. This is cosmetic, not a correctness issue.

---

## 2. Robustness

### Grade: A-

#### 2.1 `num_workers` validation (A, up from B-)

The `max(1, num_workers)` guards close the primary robustness gap from v1. Two new tests (`test_align_candidates_zero_workers` and `test_generate_candidates_zero_workers`) explicitly verify `num_workers=0` does not crash. These tests exercise the actual production code paths, not just boundary checks.

#### 2.2 Empty inputs (A, unchanged)

All empty-input paths remain correctly handled:
- `_candidate_worker`: `len(jing_text) < n` returns `[]` (line 67)
- `_candidate_worker`: empty `digest_hashes` returns `[]` (line 77)
- `align_pair`: empty digest returns empty `AlignmentResult` (line 484)
- `generate_phonetic_candidates`: no transliteration regions returns `[]` (line 378)

#### 2.3 Module-level global mutation (B+, unchanged)

The serial paths still mutate module-level globals:

```python
# candidates.py lines 254-262
global _cand_stopgrams, _cand_source_ids, ...
_cand_stopgrams = stopgrams
```

This means:
1. Globals retain references to large data after function returns
2. Thread-unsafe if `generate_candidates` were called concurrently from multiple threads

Both issues are theoretical -- the pipeline is single-threaded, and the data is needed for the lifetime of the pipeline run anyway. This is consistent with the pattern in `fingerprint.py` (lines 153-155). Still worth noting as technical debt, but not a practical concern.

#### 2.4 Pre-filter guard completeness (A)

The pre-filter in `align_candidates` (lines 685-691) has five guards, all correctly chained:

```python
if (cand.containment_score == 0.0
        and cand.from_docnumber
        and not cand.from_phonetic
        and (cand.digest_id, cand.source_id) not in phonetic_pairs
        and d_len > config.DOCNUM_PREFILTER_MIN_LEN
        and s_len > config.DOCNUM_PREFILTER_MIN_LEN):
```

The `not cand.from_phonetic` and `not in phonetic_pairs` guards protect phonetic pairs from being filtered. Three new tests cover the happy path (large pair skipped), the boundary case (small pair not skipped), and the phonetic override (phonetic pair not skipped even if large).

#### 2.5 What would bring this to A+

- **Module globals cleanup**: Adding a `_cleanup_globals()` function called at the end of `generate_candidates()` to `None` out the large arrays would prevent them from persisting after the function returns. This is a minor memory hygiene issue, not a functional problem.
- **Thread safety**: If the pipeline ever becomes multi-threaded (unlikely), the global-mutation pattern would need to be replaced with a thread-local or closure-based approach. A brief comment noting "not thread-safe" would suffice.

---

## 3. Efficiency

### Grade: A

#### 3.1 Set intersection (A+, unchanged)

The frozenset-based containment scoring remains the correct algorithmic choice. C-level `frozenset.__and__()` is dramatically faster than the old inverted-index approach.

#### 3.2 `bisect_left` pre-filter (A+, up from A)

```python
lo = bisect_left(source_lens_arr, min_source_len)
```

Now uses the stdlib C implementation instead of a hand-rolled binary search. Functionally identical, but cleaner and avoids any chance of off-by-one errors in a custom implementation. The performance difference is negligible for this use case, but the readability gain is meaningful.

#### 3.3 Dynamic chunksize (A-, unchanged)

```python
chunksize = max(1, len(worker_args) // (num_workers * 4))
```

The formula is applied identically across all parallel paths. This is a reasonable default heuristic. The `max(1, ...)` ensures chunksize is never 0 (which would hang `imap_unordered`).

#### 3.4 LPT scheduling (A, unchanged)

```python
args_list.sort(key=lambda a: len(a[2]) * len(a[3]), reverse=True)
```

Correct LPT implementation. `len(a[2]) * len(a[3])` is a good proxy for alignment cost.

#### 3.5 `DOCNUM_PREFILTER_MIN_LEN` as configurable constant (A)

Moving the threshold to `config.py` means it can be tuned without modifying `align.py`. The docstring explains the rationale clearly:

```python
# Skip zero-containment docNumber pairs where both texts exceed this length.
# Such pairs have no n-gram overlap and are expensive to align for no benefit.
# Small texts (<5000 chars) are cheap to align so we keep them just in case.
DOCNUM_PREFILTER_MIN_LEN = 5000
```

#### 3.6 Serial phonetic containment scoring (B+, unchanged from v1)

The O(n^2) pairwise phonetic containment scoring in `generate_phonetic_candidates()` (lines 418-458) remains serial. As noted in v1, the number of texts with indexable transliteration regions is typically small, so this is unlikely to be a practical bottleneck. No change needed unless the corpus grows significantly.

#### 3.7 What would bring this to A+

- **Parallel phonetic containment**: If the number of texts with transliteration regions ever grows large, parallelizing the pairwise scoring loop would help. Currently unnecessary.
- **Per-path chunksize tuning**: Different parallel paths have different cost profiles. Custom chunksize formulas (or measurement-based auto-tuning) would improve load balancing. Currently the uniform formula is adequate.

---

## 4. Legibility

### Grade: A

#### 4.1 Step numbering (A, up from B+)

The `align_candidates` steps are now sequentially numbered 1/2/3 in execution order. No more confusing 6/4/3 ordering.

#### 4.2 Config constant documentation (A)

`DOCNUM_PREFILTER_MIN_LEN` has a clear 3-line comment in `config.py` explaining what it does, why it exists, and why the default is 5000. It sits in a dedicated "Stage 3: Alignment Pre-filtering" section header (line 61). Well-organized.

#### 4.3 `bisect_left` readability (A+)

One line replaces eight. The import at the top of the file (line 10) is clear:

```python
from bisect import bisect_left
```

And the usage at line 85 is self-documenting:

```python
lo = bisect_left(source_lens_arr, min_source_len)
```

A reader familiar with Python's stdlib immediately understands this.

#### 4.4 Code comments and docstrings (A)

All functions have clear docstrings. Key design decisions are documented inline:
- Early termination rationale (align.py lines 490-492)
- Skip-phonetic-rescan rationale (align.py lines 694-695)
- LPT scheduling rationale (align.py line 711)
- Phonetic stopgram min-2 threshold (candidates.py line 400)
- Binary search comment (candidates.py lines 83-84)

#### 4.5 Naming (A-)

Same minor inconsistency from v1: `_candidate_init` / `_candidate_worker` vs `_phonetic_init` / `_phonetic_region_worker` (the `_region_` in the name is asymmetric). This is cosmetic and not confusing enough to deduct a full grade point.

#### 4.6 What would bring this to A+

- Consistent naming between `_candidate_worker` and `_phonetic_region_worker` (e.g., rename to `_candidate_score_worker` or `_phonetic_worker`).
- A brief comment on `pair_key` in `_candidate_worker` (line 95) explaining it is used solely for the `from_docnumber` flag, not for deduplication.

---

## 5. Test Coverage

### Grade: A-

#### 5.1 New tests added (6 new, 202 total)

| Test | File | What it covers |
|------|------|---------------|
| `test_low_overlap_with_phonetic_enabled` | `test_align.py:164` | Phonetic rescan gate not blocked by early termination |
| `test_large_zero_containment_docnum_pair_skipped` | `test_align.py:201` | Pre-filter happy path: large zero-containment pair skipped |
| `test_small_zero_containment_docnum_pair_not_skipped` | `test_align.py:223` | Pre-filter boundary: small pair NOT skipped |
| `test_phonetic_pair_not_skipped_even_if_large` | `test_align.py:244` | Pre-filter override: phonetic pairs never filtered |
| `test_align_candidates_zero_workers` | `test_align.py:269` | `num_workers=0` safe in `align_candidates` |
| `test_generate_candidates_zero_workers` | `test_align.py:289` | `num_workers=0` safe in `generate_candidates` |

These directly address the top three test gaps identified in v1 (pre-filter testing, phonetic gate, num_workers edge cases).

#### 5.2 Pre-existing coverage (strong)

The existing tests continue to provide solid coverage:

- **Parallel equivalence** (`test_candidates.py:247`): 16 texts, serial vs 2-worker results match (pairs + scores). Excellent regression test.
- **Degenerate inputs** (`test_candidates.py:129`): Empty ngram_sets and empty frozensets.
- **Early termination** (`test_align.py:135`): Both the "fires correctly" and "doesn't fire on real matches" paths.
- **Real-data integration** (`test_phonetic_candidates.py:231`): T250/T901 phonetic discovery with actual XML corpus data.

#### 5.3 Remaining gaps

1. **`PipelineCache` unit tests**: Still not tested. `cache.py` has no tests for `is_valid()` with stale config, wrong version, missing files, or corrupt manifest. This was noted in v1 and acknowledged as out-of-scope for this round.

2. **`num_workers=0` for `fingerprint.py` functions**: The `max(1, num_workers)` guard was added to `compute_document_frequencies` and `build_ngram_sets`, but neither has a dedicated test for `num_workers=0`. The guards are simple and clearly correct, but for parity with the candidate/align tests, explicit tests would be completeness-improving.

3. **`num_workers=-1` (negative values)**: The `max(1, num_workers)` guard handles negatives correctly (clamps to 1), but no test exercises this explicitly. `num_workers=0` is tested, and since `max(1, -1) == 1` follows the same code path, this is very low risk.

4. **Phonetic candidate parallel equivalence**: `generate_phonetic_candidates` with `num_workers=1` vs `num_workers=2` is not tested for result equivalence. The Stage 2 `generate_candidates` has this test (`test_parallel_equivalence`), but the Stage 2b phonetic path does not. The phonetic path's parallel region is the per-text region detection (each text is independent), so correctness is almost assured, but the test would add confidence.

5. **LPT sort stability**: No test verifies that reordering by estimated cost does not change the set of alignment results. This is inherently safe (each pair is aligned independently), so the risk is negligible.

6. **`raw_coverage` overcounting edge case**: No test creates deliberately overlapping seeds to exercise the early termination with overcounted raw_coverage. As analyzed in v1, this can only make early termination more conservative (not less), so it is safe but untested.

#### 5.4 What would bring this to A+

- Add `PipelineCache` unit tests (acknowledged as out-of-scope here)
- Add `num_workers=0` tests for `compute_document_frequencies` and `build_ngram_sets` (trivial to add, completes the pattern)
- Add phonetic candidate parallel equivalence test (mirrors the existing `test_parallel_equivalence`)

---

## Summary of Grades

| Category | v1 Grade | v2 Grade | Change |
|----------|----------|----------|--------|
| **Correctness** | A- | **A** | `bisect_left`, config constant, step numbering all clean |
| **Robustness** | B+ | **A-** | `max(1, num_workers)` closes main gap; globals persist |
| **Efficiency** | A | **A** | `bisect_left` improves readability; no perf change |
| **Legibility** | A- | **A** | Sequential steps, documented config constant, stdlib bisect |
| **Test Coverage** | B+ | **A-** | 6 new tests close top gaps; cache tests remain absent |

---

## Remaining Issues by Priority

### Would bring Correctness to A+ (none -- already addressed)

No remaining correctness issues. The grade stays at A rather than A+ only because the `pair_key` naming in `_candidate_worker` is slightly misleading (cosmetic, not a real bug).

### Would bring Robustness to A+

1. **Module globals cleanup**: Clear the `_cand_*` globals at the end of `generate_candidates()` to release references to potentially large arrays. Estimated effort: 5 lines.
2. **Thread-safety comment**: Add a brief note to the docstrings of `generate_candidates()` and `generate_phonetic_candidates()` stating they are not thread-safe due to module-global mutation.

### Would bring Efficiency to A+

No actionable changes needed. The serial phonetic pairwise scoring and uniform chunksize formula are theoretical concerns that would only matter with a much larger corpus or transliteration-heavy corpus.

### Would bring Legibility to A+

1. **Consistent worker naming**: Rename `_phonetic_region_worker` to `_phonetic_worker` (or `_candidate_worker` to `_candidate_score_worker`) for naming symmetry. Estimated effort: 2-line rename + test updates.
2. **Comment on `pair_key`**: Add `# Used only for from_docnumber check, not deduplication` at `candidates.py` line 95.

### Would bring Test Coverage to A+

1. **`PipelineCache` unit tests**: Test `is_valid()` with wrong version, changed config, missing files, corrupt JSON. Estimated effort: ~30 lines.
2. **`num_workers=0` for fingerprint functions**: Two small tests exercising `compute_document_frequencies(num_workers=0)` and `build_ngram_sets(num_workers=0)`. Estimated effort: ~15 lines.
3. **Phonetic candidate parallel equivalence**: Mirror `test_parallel_equivalence` but for `generate_phonetic_candidates`. Estimated effort: ~20 lines.

---

## Overall Assessment

The code has meaningfully improved since v1. All six addressed recommendations were implemented cleanly and correctly. The `max(1, num_workers)` guards convert accidental-serial-path behavior into documented, tested, intentional behavior. The `bisect_left` replacement is a textbook readability improvement. The `DOCNUM_PREFILTER_MIN_LEN` config constant with documentation makes the 5000-char threshold discoverable and tunable. The sequential step numbering eliminates a source of reader confusion.

The six new tests directly close the three most important coverage gaps from v1 (pre-filter, phonetic gate, worker count edge cases), plus add boundary and override cases for the pre-filter. The test suite has grown from 196 to 202 tests, all passing.

The remaining gaps are minor: module-global memory hygiene, cache unit tests (out of scope), and a few cosmetic naming/comment improvements. None affect correctness or practical robustness. This codebase is in strong shape for production use.
