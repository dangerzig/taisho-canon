# Final Code Review: Digest Detector Pipeline

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Scope:** All 11 production modules + 14 test files (245 tests)
**Method:** 9 parallel review agents, each with read access to source + tests + ability to run code

---

## Executive Summary

The codebase is well-engineered for a research pipeline. Code is clean, well-structured, and demonstrates good judgment about multiprocessing, caching, and domain-specific optimizations. The test suite is strong (245 tests), with particularly thorough phonetic detection and cache invalidation coverage.

**One P1 bug** was found in the alignment DP backtracking. **~19 P2 issues** span correctness, portability, and documentation concerns. The most significant test gap is `report.py` (zero coverage).

**Overall grade: A-** -- Production-quality code with one correctness bug and some rough edges to polish.

---

## P1 -- Critical (1 finding)

### 1. DP backtracking in `_chain_seeds` can miss the optimal solution
**File:** `align.py:168-189`

The backtracking assumes that if `dp[i] == remaining_coverage`, seed `i` is part of the optimal chain. This is incorrect when multiple seeds share the same DP value -- the greedy scan may select a seed that doesn't chain with the remaining seeds to form the global optimum.

**Impact:** Can silently undercount coverage. Rarely triggered in practice (seeds tend to have diverse weights, and the pre-filter removes contained seeds), but it is a correctness bug.

**Fix:** Store `prev[i]` during the forward DP pass (the predecessor index used to achieve `dp[i]`), then follow the `prev` chain backward from the global max. Standard weighted interval scheduling backtracking.

---

## P2 -- Important (19 findings)

### Extract Module (3)

**2. `build_char_map` silently ignores duplicate `char_id` definitions** (extract.py:92)
If two XML files define the same `char_id` with different resolved values, the first wins silently. Recommendation: log at WARNING when values differ.

**3. `<g>` handler appends both resolved text AND `elem.text`** (extract.py:187-197)
For `<g>` elements with fallback text like `[覆-西+非]`, normalization strips brackets but leaves spurious CJK chars `覆西非`. Fix: return early after resolving `<g>`, skipping `elem.text`.

**4. `<lem>` tail text from skipped elements still extracted** (extract.py:200-205)
Tail text after `<rdg>`, `<note>`, etc. is always appended to the parent, even when the element itself is skipped. In CBETA TEI, this is usually correct (tail text belongs to the parent), but for `<app>` children, tail text after `<rdg>` could be duplicative.

### Fingerprint Module (3)

**5. Inconsistent pool initializer pattern** (fingerprint.py:52-55 vs 110-117)
`_doc_freq_worker` passes `n` via args; `_ngram_set_worker` uses the initializer pattern. No functional bug, but inconsistent.

**6. CRC32 is 32-bit -- birthday-paradox collisions at corpus scale** (fingerprint.py:20-29)
With millions of unique 5-grams, collisions are virtually guaranteed. Impact is benign (slightly inflated containment scores, caught by Stage 3 alignment), but upgrading to 64-bit hash would eliminate the concern.

**7. `stopgrams` truthiness vs explicit check** (_fast_fallback.py:26)
Python fallback uses `if stopgrams:` (conflates None and empty set); Cython version uses `if stopgrams is not None and len(stopgrams) > 0`. Should be consistent.

### Candidates Module (2)

**8. Undocumented `jing_text` vs `full_text` asymmetry** (candidates.py:71-72)
Digest n-grams use `jing_text` (correct); source n-grams use `full_text` (also correct). But the asymmetry is intentional and undocumented -- a code comment would prevent future confusion.

**9. Phonetic containment direction may be wrong after pair normalization** (candidates.py:456-465)
After normalizing pairs to `(shorter, longer)`, the stored containment score still reflects the original iteration direction, which may measure the wrong text's coverage.

### Alignment Module (3)

**10. `_find_seeds` returns only best match per `d_pos`** (_fast_fallback.py:66-87)
Discards valid seeds at other source locations. The weighted interval scheduling DP is designed for multiple source regions but receives impoverished input. Mitigated by adjacent digest positions recovering nearby seeds.

**11. Seed deduplication uses wrong key** (align.py:411-417)
Dedup key `(d_start, s_start)` doesn't merge overlapping seeds on the same diagonal. Result: 5-10x more seeds than necessary enter `_extend_seeds`, causing redundant work.

**12. `_chain_seeds` containment pre-filter only checks adjacent pairs** (align.py:148-162)
After sorting by `d_start`, non-adjacent containments (A contains C but not B) are missed. The pre-filter is a performance optimization; missed containments just create slightly more work for the DP, not incorrect results.

### Score/Report Modules (2)

**13. Commentary classification has no documented lower-bound coverage** (score.py:83-96)
Docstring says `coverage >= 0.20` for commentary, but the code only reaches commentary for `coverage >= 0.30` (below 0.30 falls to `shared_tradition`). Also, `COMMENTARY_AVG_SEG_LEN` is used as the floor for digest, not the ceiling for commentary -- confusing name.

**14. `containment` and `coverage` are always identical in `DigestScore`** (score.py:114-115)
Both fields are set to the same phonetic-adjusted coverage value. The original pre-phonetic-adjustment coverage is lost. Either remove the redundant field or store the pre-adjustment value.

### Fast/Cython Module (2)

**15. CRC32 sign/width mismatch between Cython and Python** (_fast.pyx:75)
Cython casts to `<long>` (signed); Python's `zlib.crc32()` returns unsigned. On macOS (64-bit long), this works. On Windows (32-bit long), values >= 2^31 would diverge. Fix: use `uint32_t`.

**16. `fast_fuzzy_extend` gap-lookahead bounds check uses wrong variable** (_fast.pyx:214-223)
The `gap_d` check uses `s_idx` (intended next source position) but should verify bounds against the actual lookahead position. May cause out-of-bounds reads in edge cases.

### Phonetic Module (2)

**17. Common prose characters contaminate equivalence table** (phonetic.py:165-187)
18 common characters (天, 大, 佛, 法, 空, 色, etc.) enter the table via positional alignment of semantic+phonetic compounds. Creates 4 false equivalence pairs. Mitigated by downstream safeguards (seed length, diff count, density threshold).

**18. `_find_phonetic_seeds` worst-case complexity** (align.py:210-285)
O(D * S * max_positions_per_syllable) when source is dense with characters mapping to the same syllable. Synthetic worst-case: 0.9s for 100x1000 chars.

### Core Modules (2)

**19. `metadata` on `ExtractedText` can be `None` but `save_results()` doesn't guard** (models.py:35, extract.py:493)
Type annotation allows `None`, but `save_results()` accesses `text.metadata.text_id` without checking. Would crash on `None`. Low probability given extraction always sets metadata.

**20. `align_candidates` bypasses pipeline's resolved `num_workers`** (pipeline.py:205-206)
The pipeline resolves worker count for memory, but `align_candidates` uses `config.ALIGN_NUM_WORKERS` directly. Fix: pass the resolved count.

---

## Test Suite Assessment

### Strengths
- 245 tests across 14 files, covering all 5 stages + cross-cutting concerns
- Real CBETA XML files used for integration tests (T250, T251, T223)
- Parallel/serial equivalence verified for multiprocessing code
- Cache invalidation comprehensively tested (9 scenarios)
- Cython/fallback equivalence tests
- Phonetic detection has 3 dedicated test files with edge cases

### Critical Gap
- **`report.py` has zero test coverage.** This module handles JSON output, markdown report generation, alignment visualization, and ground truth validation. Bugs here could produce incorrect output without detection.

### Other Gaps
- `extract_all()` and `save_results()` not directly tested
- No end-to-end pipeline integration test (run on a small corpus, verify output files)
- Duplicated extraction helper between `conftest.py` and `test_phonetic_candidates.py`
- `_find_phonetic_seeds` not unit-tested in isolation (only via `align_pair` integration)

---

## Recommendations (Priority Order)

1. **Fix the DP backtracking bug** (P1, #1) -- Store `prev[i]` array for correct backtracking
2. **Add `report.py` tests** -- At minimum test JSON serialization and ground truth validation
3. **Fix `<g>` fallback text bug** (#3) -- Add early return after resolving `<g>` elements
4. **Add code comments for asymmetric design choices** (#8, #9) -- Prevent future confusion
5. **Fix `save_results()` None guard** (#19) -- Either guard or tighten the type annotation
6. **Pass resolved `num_workers` to alignment** (#20) -- Simple one-line fix

---

## Individual Review Files

Detailed findings for each module are in:
- `reviews/extract_code_review.md`
- `reviews/fingerprint_code_review.md`
- `reviews/candidates_review.md`
- `reviews/align_code_review.md`
- `reviews/score_report_review.md`
- `reviews/fast_module_review.md`
- `reviews/phonetic_code_review.md`
- `reviews/core_modules_review.md`
- `reviews/test_review.md`
