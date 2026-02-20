# Final Re-Review: Digest Detector Pipeline

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Scope:** All 11 modules + 15 test files (260 tests, all passing)
**Focus:** Verify P1/P2 bug fixes, identify remaining issues

---

## 1. DP Backtracking Fix in `align.py::_chain_seeds` (Lines 108-180)

**Verdict: CORRECT**

The weighted interval scheduling DP is now properly implemented:

1. Seeds are sorted by `d_end` (line 122).
2. A `prev[i]` array tracks the predecessor index for each seed (line 147).
3. Binary search via `bisect_right(end_positions, d_start_i, 0, i) - 1` correctly finds the rightmost non-overlapping predecessor (line 158). The `hi=i` bound is correct because `end_positions[0..i-1]` are the only valid predecessors.
4. The DP recurrence updates `dp[i]` and `prev[i]` only when including the predecessor chain improves coverage (lines 161-163).
5. Backtracking walks `prev[]` from the global best index to `-1` (lines 173-177), then reverses.

One subtle point: the DP finds the best chain **ending at** each seed `i`, but the global optimum is found by scanning all `dp[i]` values (lines 167-169). This is correct because the optimal solution must end at *some* seed.

The pre-filter (lines 127-141) handles obvious containment cases (identical or subset seeds) as a fast-path optimization. The DP handles any remaining overlaps correctly via weighted interval scheduling, so correctness does not depend on the pre-filter being exhaustive.

**No issues found.**

---

## 2. Diagonal-Based Seed Dedup in `align.py::align_pair` (Lines 407-426)

**Verdict: CORRECT**

Seeds on the same diagonal (`s_start - d_start` = constant) describe the same aligned region shifted by overlapping k-gram windows. Merging them into maximal extents is correct:

1. Seeds are grouped by diagonal key `s_start - d_start` (line 410).
2. Within each diagonal, seeds are sorted by `d_start` and merged with standard interval-merge logic (lines 414-425).
3. `cur_s` is set from `seeds_on_diag[0]` and updated to `s_start` on gap (line 423). Since `s_start = d_start + diagonal_offset`, and within one diagonal the offset is constant, `cur_s` is always consistent with `cur_d`.

**No issues found.**

---

## 3. Inlined Phonetic Equivalence in `_find_phonetic_seeds` (Lines 200-280)

**Verdict: CORRECT, with one minor observation**

The inlined check (lines 256-269) correctly:
- Checks exact equality first (`d_ch == s_ch`, line 260).
- Falls back to phonetic equivalence via `table.get()` + `isdisjoint()` (lines 263-265).
- Tracks `diff_count` only for phonetic (non-exact) matches (line 267).
- Requires `length >= k and diff_count >= 2` (line 271) to prevent false positives from single-substitution coincidences on regular prose.

The `d_ch` variable is shadowed inside the inner loop (line 258 overwrites the outer `d_ch` from line 229). This is benign because the outer `d_ch` is only used before the inner loop, but it could confuse future readers.

The 500-position cap per digest character (lines 242-245) is a practical safeguard against O(D*S) blowup. The `break` on `len(candidate_positions) >= 500` exits the inner loop early, which could miss some positions on the current syllable -- but since this is just a cap on candidate_positions (a set), positions from other syllables for the same `d_ch` are still added up to the cap. This is an acceptable approximation for performance.

**No issues found.**

---

## 4. Phonetic Containment Direction Fix in `candidates.py` (Lines 441-489)

**Verdict: CORRECT**

The `generate_phonetic_candidates` function iterates all text pairs and ensures consistent ordering:

1. When `d_len <= s_len`, the current text is the digest and `containment` is already from the correct perspective (line 466-469).
2. When `d_len > s_len`, the roles are swapped: `pair_key = (source_id, d_id)` and containment is recomputed from the actual (shorter) digest's perspective (lines 471-476).
3. The `seen_pairs` set prevents duplicate pairs from both directions being emitted (lines 478-480).

The recomputation `len(source_set & digest_set)` on line 473 is identical to `len(digest_set & source_set)` (set intersection is commutative), so `final_matching` equals `matching`. The denominator changes to `len(source_set)` because the shorter text's n-gram set is now the baseline. This is correct.

**No issues found.**

---

## 5. Containment vs. Coverage in `score.py` (Lines 37-123)

**Verdict: CORRECT**

The `DigestScore` model distinguishes:
- `containment`: raw alignment coverage from `AlignmentResult.coverage` (line 114) -- fraction of digest chars matched.
- `coverage`: effective coverage after phonetic discount (line 73-74).

The phonetic discount formula:
```python
coverage = alignment.coverage * (1 - phonetic_fraction) + phonetic_cov * PHONETIC_COVERAGE_WEIGHT
```
This correctly discounts phonetic matches by `PHONETIC_COVERAGE_WEIGHT` (0.8) while keeping exact/fuzzy matches at full weight. When `phonetic_fraction = 0`, `coverage = alignment.coverage`.

Classification thresholds (lines 84-96) use the discounted `coverage`, which is correct: phonetic matches are less reliable than exact matches and should be penalized.

**No issues found.**

---

## 6. Module-by-Module Review

### 6.1 `extract.py` -- Stage 1

**CORRECT.** Clean XML parsing with proper namespace handling, charDecl resolution priority, SKIP/INCLUDE tag sets, dharani range tracking, and CJK normalization.

One observation: `_extract_text_recursive` uses a `div_stack` list as a mutable argument passed through recursion. The `try/finally` block on lines 224-226 ensures the stack is always popped even if an exception occurs. This is correct and defensive.

### 6.2 `fingerprint.py` -- Stage 2a

**CORRECT.** Uses `zlib.crc32` for deterministic cross-process hashing (`stable_hash`). Document frequency computation, stopgram identification, and n-gram set construction all use proper multiprocessing patterns (Pool with initializer, `maxtasksperchild`).

### 6.3 `candidates.py` -- Stage 2b

**CORRECT.** Binary search prefiltering via `bisect_left` (line 83) correctly finds the first source meeting `min_source_len`. The serial path sets module globals directly (lines 272-281) and cleans them up afterward (line 309).

### 6.4 `phonetic.py` -- Phonetic Equivalence

**CORRECT.** The DDB dictionary parsing, syllable splitting heuristic, and transliteration region detection are well-implemented. The `_COMMON_PROSE_EXCLUSIONS` filter and `PHONETIC_MAX_SYLLABLES` cap are important for precision.

One minor note: `_split_syllables` uses a simple consonant/vowel heuristic that won't handle all Sanskrit edge cases (e.g., syllabic consonants, aspiration clusters). This is documented as an approximation and is adequate for the phonetic equivalence use case.

### 6.5 `_fast_fallback.py` -- Pure Python Hot Path

**CORRECT.** Signatures match the Cython `.pyx` file exactly. The `fast_find_seeds` function takes the best match per `d_pos` (not all matches), which is consistent with the Cython version.

### 6.6 `_fast.pyx` -- Cython Hot Path

**CORRECT.** Uses `PyUnicode_READ` for C-level character comparison with proper bounds checks before every access. The UTF-8 byte offset construction for `fast_ngram_hashes` correctly walks continuation bytes. The `malloc/free` is guarded by `try/finally`. The CRC32 is computed via C-level `zlib.h` function, avoiding Python object allocation in the inner loop.

### 6.7 `pipeline.py` -- Orchestrator

**CORRECT.** Proper stage sequencing with timing, memory tracking (`_log_peak_rss`), cache integration, and cleanup of intermediate data (`del doc_freq`, `del ngram_sets`, `gc.collect()`). The `phonetic_table` is deleted after Stage 2b. The `_phonetic_table` global in `align.py` is cleared after Stage 3.

### 6.8 `models.py` -- Dataclasses

**CORRECT.** Clean dataclass definitions with appropriate defaults. The `jing_text` property on `ExtractedText` falls back to `full_text` when no jing segments exist, which is the correct behavior for texts without div-type annotations.

### 6.9 `cache.py` -- Disk Cache

**CORRECT.** Cache invalidation checks three conditions: `CACHE_VERSION`, config snapshot, and corpus hash (SHA256 of all XML file paths/mtimes/sizes). The `_corpus_hash` is memoized between `is_valid` and `save` calls to avoid recomputation.

### 6.10 `report.py` -- Stage 5

**CORRECT.** Validation against ground truth, JSON and Markdown report generation, alignment visualization with phonetic mapping display. The `_segment_to_dict` function only includes `phonetic_mapping` when non-empty, keeping JSON output clean.

### 6.11 `fast.py` -- Import Dispatcher

**CORRECT.** Tries Cython first, falls back to pure Python, respects `DIGEST_NO_CYTHON` env var for forced fallback.

### 6.12 `config.py` -- Configuration

**CORRECT.** `resolve_worker_count` provides sensible defaults: `min(cpu_count(), 4)` for memory-intensive stages, `min(cpu_count(), 16)` for memory-light stages. Confidence weights sum to 1.0.

---

## 7. Test Coverage Assessment

**260 tests across 15 files -- all passing.**

| Test File | Tests | Coverage Area |
|---|---|---|
| `test_align.py` | 20 | Seeds, chaining, align_pair, early termination, prefilter, workers |
| `test_candidates.py` | 12 | DocNumber parsing, pair generation, size ratio, parallel equivalence |
| `test_cache.py` | ~8 | Cache validity, invalidation, round-trip |
| `test_edge_cases.py` | 5 | Bisect boundary, phonetic stopgram min threshold |
| `test_extract.py` | ~20 | XML parsing, charDecl, normalization, dharani ranges |
| `test_fast.py` | 30 | Cython/fallback equivalence, edge cases, source table compat |
| `test_fingerprint.py` | ~15 | N-gram hashing, stopgrams, stable_hash determinism |
| `test_known_pairs.py` | ~10 | T250/T251/T223 integration tests |
| `test_parallel.py` | ~10 | Serial/parallel equivalence across stages |
| `test_phonetic.py` | ~20 | Equivalence table, syllable splitting, mapping |
| `test_phonetic_candidates.py` | ~20 | Transliteration regions, syllable n-grams, phonetic pairs |
| `test_phonetic_integration.py` | ~15 | End-to-end dharani matching, false positive rejection |
| `test_pipeline.py` | 3 | Cache bypass, cache usage, cache save |
| `test_report.py` | 14 | Segment dict, validation, visualization, report output |
| `test_score.py` | 17 | Classification, confidence, multi-source, filtering |

**Coverage is thorough.** Key areas well-tested include:
- DP backtracking correctness (via chain_seeds containment tests in `test_fast.py`)
- Serial/parallel equivalence for candidates, fingerprinting, and phonetic detection
- Edge cases: bisect boundary, tiny corpus stopgram threshold, zero workers, empty inputs
- Integration: real T250/T251/T223 alignment with coverage assertions
- Phonetic: false positive rejection on prose, dharani pair matching across translators

**Missing test coverage (minor gaps):**
1. No direct test of the diagonal dedup in `align_pair` -- tested indirectly through `align_pair` integration tests, but no unit test explicitly verifying dedup reduces seed count.
2. No test for `_phonetic_rescan` splitting a novel segment into multiple phonetic + novel sub-segments.
3. No test for `detect_multi_source_digests` when sources overlap significantly (the "overlapping_sources_not_flagged" test exists but only checks the 10% improvement threshold).
4. No test for the `_fuzzy_extend` backward direction starting from a non-boundary position (e.g., middle of text).

These are all P3 (nice-to-have) rather than P2 (should fix).

---

## 8. Remaining Issues

### P3 Issues (Minor / Cosmetic)

**P3-1: Variable shadowing in `_find_phonetic_seeds`**
File: `/Users/danzigmond/taisho-canon/digest_detector/align.py`, line 258
`d_ch` is rebound inside the inner `while` loop, shadowing the `d_ch` from line 229. Benign but could confuse future readers. Consider renaming the inner variable to `dc` or `d_char`.

**P3-2: `_find_phonetic_seeds` only keeps best match per `d_pos`**
File: `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 272-278
When multiple source positions match at the same `d_pos`, only the longest is kept. This means if there are two valid phonetic seeds starting at the same digest position but in different source regions, only the longest is retained. This is the correct greedy behavior (same as `fast_find_seeds`), but the docstring says "Find phonetically equivalent seed matches" (plural) which could be misleading. Very minor docstring nit.

**P3-3: `_flush_segment` closure captures `dharani_ranges` by reference**
File: `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, line 361
The nested function `_flush_segment` modifies the outer `dharani_ranges` list. This works correctly but is a side-effect pattern that could surprise readers. A return-value pattern would be cleaner.

**P3-4: `fast.py` import structure**
File: `/Users/danzigmond/taisho-canon/digest_detector/fast.py`
The `# noqa: F401` comments suppress "imported but unused" warnings. This is necessary since the imports are re-exported, but adding `__all__` to `fast.py` would be more explicit.

**P3-5: `config.py` confidence weights documentation**
File: `/Users/danzigmond/taisho-canon/digest_detector/config.py`, lines 39-45
Comment says "must sum to 1.0" but there is no runtime assertion. The weights do sum to 1.0 (0.35 + 0.20 + 0.10 + 0.10 + 0.15 + 0.10 = 1.00), but a future edit could break this invariant silently. An `assert` in `_compute_confidence` or config validation would be a small safety net.

**P3-6: `_count_source_regions` gap_threshold is hardcoded**
File: `/Users/danzigmond/taisho-canon/digest_detector/align.py`, line 558
The `gap_threshold=100` parameter is hardcoded as a default and not exposed in `config.py`. This is a minor consistency issue since most other thresholds live in config.

**P3-7: No `__all__` in several modules**
Modules like `align.py`, `candidates.py`, `score.py` do not define `__all__`, so `from module import *` would export private functions like `_chain_seeds`. Not a bug since wildcard imports are not used in the codebase.

---

## 9. Things Done Well

1. **Stable hashing**: The `stable_hash` / CRC32 approach correctly avoids PEP 456 randomized hash across spawned processes on macOS.

2. **Memory management**: Aggressive `del` of intermediate data structures (doc_freq, ngram_sets, stopgrams, phonetic_table), `gc.collect()`, and `maxtasksperchild=100` for worker recycling.

3. **Cython/fallback pattern**: Clean import dispatcher with env-var override, equivalent signatures, and a dedicated equivalence test class.

4. **Early termination**: The raw-coverage check in `align_pair` (lines 432-455) skips expensive extend/chain for hopeless pairs, with a proper gate for phonetic rescan.

5. **Cache design**: Three-way invalidation (version, config snapshot, corpus hash) prevents stale results from silently persisting.

6. **Defensive coding**: `try/finally` in extract.py for div_stack cleanup, `try/finally` in Cython for `free(byte_offsets)`, bounds checks before every `PyUnicode_READ`.

7. **Test quality**: Serial/parallel equivalence tests, boundary condition tests, integration tests on real data (T250/T251/T223), false positive rejection tests.

8. **Classification cascade**: The priority order (no_relationship < shared_tradition < retranslation < excerpt/digest/commentary) with separate thresholds for coverage, segment length, and size ratio is well-designed for the Buddhist text domain.

---

## 10. Grade

**Grade: A**

The codebase is production-quality with no P1 or P2 bugs remaining. All five requested fixes have been correctly implemented and are covered by tests. The 260-test suite provides strong coverage of the critical paths.

The gap to A+ is the collection of P3 items above -- none are bugs, but they represent minor polish opportunities (variable shadowing, missing `__all__`, hardcoded threshold, config weight assertion). In a research pipeline of this complexity, these are entirely acceptable.

This is clean, well-structured, well-documented code with thoughtful performance optimization. The multiprocessing patterns are correct, the Cython code is safe, and the algorithmic choices (weighted interval scheduling, diagonal dedup, phonetic equivalence) are sound.
