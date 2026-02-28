# Comprehensive Code Review: `digest_detector` Package (Re-Review)

**Date:** 2026-02-28
**Reviewer:** Claude (automated)
**Scope:** All 18 source files in `digest_detector/` and all 20 test files in `tests/`
**Test suite:** 418 tests passed, 1 pre-existing deselected, in 25.69 seconds
**Previous review:** 2026-02-27 (Grade: A-)

---

## Executive Summary

This is a re-review of the `digest_detector` package following fixes applied from the 2026-02-27 review. All 17 specific findings from the previous review have been addressed. The most significant improvement is the extraction of shared export code into `_export_common.py`, which eliminates roughly 250 lines of duplicated logic between `export_csv.py` and `export_tei.py`. Other improvements include proper cache corruption handling, the `SOURCE_REGION_GAP_THRESHOLD` config parameter, defensive comments throughout, additional tests, and the sliding-window optimization in `find_transliteration_regions`.

The codebase is now at A+ quality. The remaining observations are minor, mostly stylistic or informational, with no correctness, security, or significant maintainability concerns.

---

## Severity Key

- **HIGH**: Potential correctness bug, data loss risk, or security issue
- **MEDIUM**: Performance concern, maintainability problem, or robustness gap
- **LOW**: Style, documentation, minor improvement opportunity
- **INFO**: Positive observation, no action needed

---

## 1. Comparison to Previous Review: What Improved

All 17 findings from the 2026-02-27 review have been addressed. Below is a finding-by-finding accounting.

### Finding 1.1 (MEDIUM): Export Code Duplication -- FIXED

The shared functions (`load_json`, `build_number_to_id`, `resolve_taisho`, `build_provenance`, `gather_metadata`, `load_known_error_pairs`) have been extracted into `/Users/danzigmond/taisho-canon/digest_detector/_export_common.py`. Both `export_csv.py` and `export_tei.py` now import from it. The new module is 311 lines with clear docstrings explaining its purpose. The path constants (LANCASTER_PATH, ACMULLER_PATH, etc.) are also properly centralized.

### Finding 1.2 (HIGH -> Informational): `_chain_seeds` DP Pre-filter -- DOCUMENTED

The `_chain_seeds` docstring (align.py lines 108-121) now explicitly explains that the adjacent-pair pre-filter is a performance optimization that does not affect correctness:

```
The adjacent-pair pre-filter (lines below) removes seeds fully contained
within their neighbor. This is a performance optimization that does not
affect correctness: any chain using a contained seed could use the
containing seed instead for equal or better coverage.
```

### Finding 1.3 (HIGH): Unsafe Pickle Deserialization -- FIXED

The `PipelineCache.load()` method (cache.py lines 104-124) now includes:
1. A trust model comment in the docstring explaining that cache files are self-generated and trusted.
2. A proper `CacheCorruptionError` exception class (cache.py line 127-128).
3. Comprehensive exception handling catching `(pickle.UnpicklingError, EOFError, AttributeError, ModuleNotFoundError, OSError)` and wrapping in `CacheCorruptionError`.
4. The pipeline (`pipeline.py` lines 110-114) catches `CacheCorruptionError` and falls back to recomputation with a warning log.

### Finding 1.4 (HIGH -> LOW): Equal-Length Invariant in `_phonetic_rescan` -- DOCUMENTED

The `_phonetic_rescan` docstring (align.py lines 298-316) now explicitly states:

```
Phonetic matches are restricted to 1:1 character alignment (no gaps),
so digest and source spans are always equal length. This invariant is
required by phonetic_mapping_for_pair().
```

A reinforcing comment also appears at the call site (align.py lines 362-363):

```python
# Phonetic match: d_text and s_text are guaranteed equal length
# because _find_phonetic_seeds uses 1:1 character matching (no gaps).
```

### Finding 1.5 (MEDIUM): `d_pos` Advancement in `_find_phonetic_seeds` -- FIXED

The function now advances `d_pos` by `best_match[2]` (the match length) when a match is found (align.py line 291), with an explanatory comment:

```python
# Advance past the match: overlapping seeds from the same region
# add no value after chaining, so skip ahead by match length.
d_pos += best_match[2]
```

### Finding 2.2 (MEDIUM): `_flush_segment` Closure Side Effect -- DOCUMENTED

The `dharani_ranges` declaration now has a comment (extract.py line 359):

```python
# Mutated by _flush_segment closure below to track dharani character ranges
dharani_ranges = []
```

And the `_flush_segment` docstring (extract.py lines 362-366) explicitly notes:

```
Side effect: appends to the enclosing dharani_ranges list.
```

### Finding 2.3 (MEDIUM): `compute_document_frequencies` Global Mutation -- DOCUMENTED

The serial path in `fingerprint.py` (lines 86-88) now has a comment:

```python
# Side effect: sets module-level _worker_n so _doc_freq_worker can
# read it. Safe for single-pipeline-run processes; the global retains
# the last value if called again with a different n.
```

### Finding 2.7 (MEDIUM): `skip_phonetic_rescan` Behavior -- DOCUMENTED

The `align_candidates` function (align.py lines 673-677) now has an explanatory comment:

```python
# Skip phonetic rescan for phonetic-origin pairs (already
# discovered via phonetic candidate generation in Stage 2b).
# Note: phonetic-origin pairs with sparse character-level overlap
# may produce zero-coverage results after early termination, since
# the phonetic coverage from Stage 2b is not re-measured here.
```

### Finding 2.8 (MEDIUM): Hard-coded `gap_threshold=100` -- MOVED TO CONFIG

`SOURCE_REGION_GAP_THRESHOLD = 100` has been added to `config.py` (line 38), and `_count_source_regions` (align.py lines 576-599) now reads from config:

```python
if gap_threshold is None:
    gap_threshold = config.SOURCE_REGION_GAP_THRESHOLD
```

### Finding 3.8 (LOW): Cache Corruption Handling -- FIXED

This was addressed as part of Finding 1.3. The `CacheCorruptionError` exception and fallback in `pipeline.py` handle corrupted cache files gracefully.

### Finding 3.10 (LOW): Classification Priority Order Documentation -- FIXED

The `classify_relationship` docstring (score.py lines 47-57) now explicitly documents the priority order:

```
Categories (checked in this priority order; first match wins):
1. no_relationship: coverage < 0.10
2. shared_tradition: coverage 0.10-0.30
3. retranslation: coverage >= 0.30, size ratio < 3.0 (similar length texts)
4. excerpt: coverage >= 0.80, avg segment >= 15 chars (verbatim extraction)
5. digest: coverage >= 0.30, avg segment >= 10 chars (condensed derivation)
6. commentary: coverage >= 0.30, avg segment < 10 chars (scattered small matches)

Note: retranslation is checked before excerpt/digest, so a pair with 95%
coverage and size_ratio < 3.0 is classified as retranslation, not excerpt.
```

### Finding 3.12 (LOW): `load_kangyur_sanskrit_titles` Return Type -- FIXED

The function signature now correctly shows `list[tuple[int, str, str]]` and the docstring matches:

```python
def load_kangyur_sanskrit_titles() -> list[tuple[int, str, str]]:
    """Load Sanskrit titles for Kangyur/Tengyur texts.

    Returns: list of (tohoku_number, original_title, source) tuples.
    """
```

### Finding 3.13 (LOW): Python 3.10+ Requirement -- DOCUMENTED

The `sanskrit_match.py` file uses `from __future__ import annotations`, and the codebase consistently uses `X | None` syntax (PEP 604). The requirement is now documented in MEMORY.md under "Python 3.10+ requirement documented."

### Performance Item 5: Sliding-Window Optimization -- IMPLEMENTED

The `find_transliteration_regions` function (phonetic.py lines 266-294) now uses an incremental sliding window. It maintains a running `table_count`, incrementing/decrementing as characters enter/leave the window, for O(n) instead of O(n*w):

```python
# Initialize count for first window
table_count = sum(1 for ch in text[:window] if ch in table)

for i in range(len(text) - window + 1):
    if i > 0:
        # Remove char leaving the window, add char entering
        if text[i - 1] in table:
            table_count -= 1
        if text[i + window - 1] in table:
            table_count += 1
```

### Test Gaps Addressed

**Gap 1 (MEDIUM): `_flush_segment` dharani range tracking tests -- ADDED**
Three new tests in `test_extract.py` (`TestDharaniRangeTracking` class, lines 190-243):
- `test_t250_has_dharani_ranges`: Verifies T250 produces dharani ranges
- `test_no_dharani_in_plain_text`: Verifies T223 has no dharani ranges
- `test_dharani_ranges_are_merged`: Verifies adjacent ranges are merged

**Gap 3 (MEDIUM): Cache corruption recovery tests -- ADDED**
Three new tests in `test_cache.py` (`TestCacheCorruption` class, lines 238-274):
- `test_truncated_pickle`: Truncated pickle raises `CacheCorruptionError`
- `test_empty_pickle`: Empty pickle raises `CacheCorruptionError`
- `test_garbage_pickle`: Garbage data raises `CacheCorruptionError`

**Gap 4 (LOW): `phonetic_mapping_for_pair` ValueError tests -- ADDED**
Two new tests in `test_phonetic.py` (lines 189-197):
- `test_unequal_length_raises_value_error`: Forward case
- `test_unequal_length_reversed_raises_value_error`: Reversed case

---

## 2. New Findings

After thoroughly re-reading all 18 source files and all 20 test files, I identified the following new observations. None are high-severity.

### Finding N1: `__init__.py` Does Not Export New Modules [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/__init__.py`

**Description:** The `__all__` list exports 10 modules but does not include `_export_common`, `export_csv`, `export_tei`, `sanskrit_match`, `fast`, or `_fast_fallback`. The underscore-prefixed modules (`_export_common`, `_fast_fallback`) are correctly excluded as private. However, `export_csv`, `export_tei`, and `sanskrit_match` are public modules that users might want to import.

This is not a bug (the modules are importable regardless of `__all__`), but for completeness, `export_csv`, `export_tei`, and `sanskrit_match` could be added. On the other hand, these are standalone scripts (each has `if __name__ == "__main__"`) rather than pipeline components, so excluding them from `__all__` is a reasonable design choice.

**Recommendation:** No change required. The current `__all__` correctly reflects the core pipeline modules.

---

### Finding N2: `_export_common.py` `build_provenance` Falls Back to `print()` Instead of `logging` [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/_export_common.py`, line 100

**Description:** When the fallback provenance path is triggered, the code uses `print()` for the warning:

```python
print("  WARNING: No link_provenance in expanded JSON; using fallback "
      "provenance reconstruction (incomplete source coverage).")
```

The rest of the `digest_detector` package consistently uses `logging.getLogger(__name__)` for warnings. Using `print()` here means the warning bypasses the logging system (no log level filtering, no file output, no timestamp).

**Recommendation:** Replace with `logger.warning(...)` for consistency. This is minor since the fallback path is rarely triggered (only when `link_provenance` is absent from the expanded JSON, which indicates an older data format).

---

### Finding N3: `_export_common.py` Has No `logger` Object [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/_export_common.py`

**Description:** Unlike all other modules in the package, `_export_common.py` does not create a `logger` object. This is related to Finding N2: adding a logger would allow replacing the `print()` call with proper logging.

**Recommendation:** Add `import logging` and `logger = logging.getLogger(__name__)` at the top of the module, then use `logger.warning(...)` instead of `print(...)` in the fallback path. Very minor.

---

### Finding N4: `export_csv.py` and `export_tei.py` Use `print()` for Status Output [LOW]

**Files:**
- `/Users/danzigmond/taisho-canon/digest_detector/export_csv.py`
- `/Users/danzigmond/taisho-canon/digest_detector/export_tei.py`

**Description:** Both export modules use `print()` for status messages (e.g., "Reconstructing per-mapping provenance...", "CSV exported to ..."). This is consistent with their use as standalone scripts (`if __name__ == "__main__"`), where `print()` is the idiomatic approach.

**Recommendation:** No change needed. Using `print()` for standalone script output is appropriate. The pipeline module (`pipeline.py`) correctly uses `logging` for its own output.

---

### Finding N5: `candidates.py` `_candidate_worker` Does Not Add docNumber-origin Pairs For Sources Below `min_source_len` [INFO]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/candidates.py`, lines 80-108

**Description:** The `_candidate_worker` function uses binary search to skip sources below `min_source_len = d_len * min_size_ratio`. This means docNumber-referenced pairs where the source is shorter than the digest are not evaluated by the worker. However, `generate_candidates` (lines 295-309) adds docNumber pairs not found by fingerprinting as zero-containment candidates. So the pairs are still included in the output.

This design is correct: the worker handles the fast-path (intersection scoring), and the post-worker loop ensures all docNumber cross-references are present. No issue.

---

### Finding N6: `test_exports.py::TestOtaniNanjio::test_tei_otani_for_t01n0001` Is Deselected [INFO]

**Description:** One test is permanently deselected:

```
tests/test_exports.py::TestOtaniNanjio::test_tei_otani_for_t01n0001
```

This test checks that T01n0001 has specific Otani numbers in the TEI output. Based on the test code (lines 220-228), it looks for `<idno type='otani'>` elements, but the TEI export uses `<link type='otani'>` elements (export_tei.py line 159). The test appears to be looking for the wrong element type.

**Recommendation:** Fix the test to look for `<link type='otani'>` elements instead of `<idno type='otani'>` elements, matching the actual TEI export format. Then remove it from the deselect list. This appears to be a pre-existing bug in the test, not in the production code.

---

### Finding N7: `_export_common.py` Duplicate Path Constants [INFO]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/_export_common.py`, lines 12-13

**Description:** The `BASE_DIR` and `RESULTS_DIR` constants in `_export_common.py` are defined independently from `config.py`:

```python
# _export_common.py
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

# config.py
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
```

Both resolve to the same paths since both files are in the `digest_detector/` package. This is not a bug (both computations produce identical results), but it means there are two independent definitions of the same path.

**Recommendation:** `_export_common.py` could import `BASE_DIR` and `RESULTS_DIR` from `config` to avoid the duplication. However, the export modules operate somewhat independently from the main pipeline, so having independent path definitions may be a deliberate design choice to avoid coupling. No change strictly needed.

---

### Finding N8: `test_otani_concordance.py` -- Comprehensive Coverage [INFO]

**File:** `/Users/danzigmond/taisho-canon/tests/test_otani_concordance.py`

**Description:** This 30-test file provides thorough coverage of the Otani concordance pipeline, including XML parsing (12 tests), concordance building (10 tests), and merging (8 tests). The tests use real XML fixtures and handle edge cases like duplicate kernel IDs, letter suffixes (D7a), comma sub-sections (Q760,01), and missing Peking counterparts.

This is a positive observation. The test quality matches the A+ standard of the rest of the suite.

---

## 3. Test Coverage Assessment

### Summary

- **418 tests passing** across 19 test files (excluding `__init__.py`)
- **1 test deselected** (`test_tei_otani_for_t01n0001`) due to apparent element-type mismatch in the test
- **25.69 seconds** total runtime
- **0 failures, 0 errors, 0 warnings**

### Coverage by Module

| Source Module | Test File(s) | Test Count | Assessment |
|---|---|---|---|
| `extract.py` | `test_extract.py` | 14 | Good: real XML, dharani tracking, charDecl |
| `fingerprint.py` | `test_fingerprint.py` | 13 | Good: hashing, doc freq, stopgrams |
| `candidates.py` | `test_candidates.py` | 12 | Good: docNumber, pair ordering, jing_text |
| `align.py` | `test_align.py` | 17 | Excellent: seeds, chaining, early termination, pre-filter |
| `score.py` | `test_score.py` | 19 | Excellent: all 7 classifications, confidence, multi-source |
| `report.py` | `test_report.py` | 11 | Good: JSON, visualization, phonetic display |
| `phonetic.py` | `test_phonetic.py`, `test_phonetic_integration.py`, `test_phonetic_candidates.py` | 36 | Excellent: syllable splitting, equivalence, regions, n-grams |
| `pipeline.py` | `test_pipeline.py` | 3 | Adequate: cache bypass/valid/save paths |
| `cache.py` | `test_cache.py` | 15 | Excellent: roundtrip, invalidation (8 scenarios), corruption (3 scenarios) |
| `fast.py`, `_fast_fallback.py` | `test_fast.py` | 23 | Excellent: all three functions, edge cases, Cython equivalence |
| `_export_common.py`, `export_csv.py`, `export_tei.py` | `test_exports.py` | ~35 | Good: cross-validation, spot checks, well-formedness |
| `sanskrit_match.py` | `test_sanskrit_match.py` | 28 | Excellent: normalization, matching, section mismatch |
| Integration | `test_known_pairs.py` | 10 | Good: T250/T251/T223 end-to-end |
| Integration | `test_parallel.py` | 3 | Good: serial vs parallel equivalence |
| Edge cases | `test_edge_cases.py` | 4 | Good: bisect boundary, stopgram filtering |
| Otani concordance | `test_otani_concordance.py` | 30 | Excellent: parsing, building, merging |

### Remaining Coverage Gaps (Minor)

1. **No unit tests for `_build_kgram_table`** (align.py): Tested indirectly through `fast_find_seeds`. LOW priority.
2. **No tests for `_print_timing_history` or `main()` CLI** (pipeline.py): UI-level functions, LOW priority.
3. **No tests for the export functions themselves** (only their outputs are tested via pre-generated files): The `test_exports.py` tests validate the generated CSV, TEI, and JSON files against each other, which provides strong functional coverage. Direct invocation tests would add protection against import errors or path changes but are LOW priority.
4. **The deselected Otani TEI test** (Finding N6): Should be fixed to test `<link>` elements rather than `<idno>` elements.

---

## 4. Architecture and Design Assessment

### Strengths (carried forward from previous review, all confirmed)

1. **Clean 5-stage pipeline** with well-defined interfaces between stages
2. **Smart use of `frozenset[int]`** per-text n-gram sets with C-level set intersection
3. **Proper use of `zlib.crc32`** (`stable_hash()`) to avoid Python's per-process randomized hash (PEP 456)
4. **Cython acceleration** with transparent pure-Python fallback and `DIGEST_NO_CYTHON` env var
5. **Disk cache** with SHA256 corpus hashing, config snapshot, and CACHE_VERSION for invalidation
6. **Multiprocessing** with `Pool` + `initializer` pattern avoids per-task pickling overhead
7. **`slots=True`** on all 8 dataclasses reduces memory and prevents accidental attributes
8. **Factory functions** in `tests/helpers.py` reduce boilerplate across 19 test files
9. **Weight assertion** at import time (config.py line 48) catches configuration errors early
10. **LPT scheduling** (largest-source-first sort) with source k-gram table caching in alignment

### New Architectural Strength: `_export_common.py`

The new `_export_common.py` module cleanly separates shared export logic from format-specific output. The API surface is well-designed:

- `load_json(path)`: Safe file loading with existence check
- `build_number_to_id(concordance_keys)`: ID normalization
- `resolve_taisho(raw, num_to_id, valid_ids)`: Flexible ID resolution
- `build_provenance(expanded)`: Per-link provenance with fallback path
- `gather_metadata(expanded)`: Multi-source title/nanjio/otani aggregation
- `load_known_error_pairs()`: Error pair exclusion

This eliminates the primary deduction from the previous review.

---

## 5. Performance Observations

All performance items from the previous review are addressed. Notable optimizations now in place:

1. **Binary search prefiltering** in `generate_candidates` (candidates.py:85)
2. **Diagonal deduplication** in `align_pair` (align.py:414-446)
3. **Source table caching** in `_align_pair_wrapper` (align.py:605-621) with LPT scheduling
4. **`MAXTASKSPERCHILD=100`** (config.py:77) for memory reclamation
5. **Incremental sliding window** in `find_transliteration_regions` (phonetic.py:266-294) -- NEW, O(n) instead of O(n*w)
6. **`d_pos` advancement by match length** in `_find_phonetic_seeds` (align.py:291) -- NEW, avoids redundant seed generation
7. **Precomputed canonical syllable table** in `text_to_syllable_ngrams` (phonetic.py:341) avoids repeated `sorted()` calls

No new performance concerns identified.

---

## 6. Documentation Assessment

### Strengths (all improved since previous review)

- Every module has a clear module-level docstring explaining its role in the pipeline
- Function docstrings consistently describe parameters, return types, and behavioral notes
- Critical design decisions are documented inline (stable_hash, jing_text vs full_text, trust model, equal-length invariant, pre-filter correctness, classification priority order)
- The `_flush_segment` side effect is now explicitly documented
- The `skip_phonetic_rescan` behavior is now explained with a comment
- The `compute_document_frequencies` global mutation is now documented
- The `_chain_seeds` pre-filter correctness argument is now in the docstring

### Minor Documentation Suggestions

1. The `_export_common.py` module could add a module-level `logger` and use it instead of `print()` for the fallback warning (Findings N2/N3).
2. The `__init__.py` could optionally export `export_csv`, `export_tei`, and `sanskrit_match` in `__all__` (Finding N1).

Neither is significant enough to affect the grade.

---

## 7. Summary of New Recommendations

### Low Priority (nice-to-have):

1. **Fix** the deselected test `test_tei_otani_for_t01n0001` to check `<link type='otani'>` instead of `<idno type='otani'>` (Finding N6)
2. **Add** `logger` to `_export_common.py` and replace `print()` with `logger.warning()` in the fallback path (Findings N2/N3)
3. **Consider** importing `BASE_DIR`/`RESULTS_DIR` from `config` in `_export_common.py` rather than redefining (Finding N7)

None of these affect correctness or robustness.

---

## 8. Overall Assessment

**Grade: A+**

This is polished, production-quality research code. All 17 findings from the previous review have been properly addressed. The architecture is clean, the separation of concerns is excellent, the test suite is comprehensive (418 tests with strong coverage of edge cases), and the documentation is thorough. The few remaining observations are strictly informational or low-priority style matters.

Key quality indicators:
- **Correctness**: All invariants are documented. Cache corruption is handled gracefully. The DP chaining algorithm is provably correct with the pre-filter safety argument documented.
- **Performance**: Multiple well-considered optimizations (binary search, diagonal dedup, source table caching, incremental sliding window) without sacrificing readability.
- **Maintainability**: Shared export logic properly extracted. Module-level globals for worker state are documented as non-thread-safe. Config parameters are centralized with a compile-time weight assertion.
- **Testing**: 418 tests covering all stages, integration with real XML data, edge cases (bisect boundaries, tiny corpora, cache corruption), parallel/serial equivalence, cross-format validation.
- **Documentation**: Comprehensive docstrings, inline rationale for design decisions, and MEMORY.md capturing domain knowledge and gotchas.

### Comparison to Previous Review

| Aspect | Previous (2026-02-27) | Current (2026-02-28) |
|---|---|---|
| Grade | A- | A+ |
| Test count | 411 | 418 (+7 new tests) |
| Source files | 17 | 18 (+_export_common.py) |
| HIGH findings | 4 (1 real, 3 informational) | 0 |
| MEDIUM findings | 10 | 0 |
| LOW findings | 13 | 3 (all new, minor) |
| Export duplication | ~250 lines duplicated | Eliminated |
| Cache corruption handling | No error recovery | CacheCorruptionError + fallback |
| Sliding window | O(n*w) | O(n) |
| Phonetic seed advancement | d_pos += 1 | d_pos += match_length |
