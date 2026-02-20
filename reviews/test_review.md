# Test Suite Review

**Reviewed:** 14 test files, 245 tests
**Source modules:** 11 production files

---

## Summary Verdict

The test suite is **strong overall**, with 245 tests across 14 files, covering each of the 5 pipeline stages plus cross-cutting concerns (parallelism, caching, edge cases, Cython/fallback equivalence). The tests are well-organized by stage, use good helper abstractions, and exercise real-world data through integration tests. There are, however, several notable coverage gaps and a few structural concerns.

---

## What Is Well-Tested

### Stage 1: Extraction (`test_extract.py`)
- Good coverage of `_decode_unicode_hex`, `normalize_text`, `build_char_map`, `extract_file`, `_group_files_by_text`.
- Tests use **real XML files** (T250, T251, T08), providing genuine integration-level validation.
- Tests verify both structure (metadata, div types, dharani detection) and content (key phrases, character counts).
- Proper `pytest.skip()` for missing files.

### Stage 2: Fingerprinting (`test_fingerprint.py`)
- Solid unit tests for `generate_ngrams`, `compute_document_frequencies`, `identify_stopgrams`, `build_ngram_sets`, `stable_hash`, `fingerprint_text`.
- Tests both behavior (shared n-grams appear in both sets) and invariants (stopgrams are excluded).
- `num_workers=0` edge case is covered.

### Stage 2b: Candidates (`test_candidates.py`)
- Good coverage of `_parse_docnumber_to_text_ids`, `_find_docnumber_pairs`, and `generate_candidates`.
- Tests verify: size ratio filtering, pair ordering (shorter first), self-pair exclusion, docNumber pair inclusion, jing_text usage for containment, and degenerate inputs (empty sets).
- Parallel equivalence test is thorough.

### Stage 3: Alignment (`test_align.py`)
- Tests cover `_find_seeds`, `_chain_seeds`, `align_pair`, `_count_source_regions`.
- Early termination logic tested both with and without phonetic rescan enabled.
- Pre-filter tests for `align_candidates` (zero-containment docNumber pairs).
- Good segment coverage assertion (segments cover entire digest, no gaps).

### Stage 4: Scoring (`test_score.py`)
- Thorough classification tests: excerpt, digest, commentary, shared_tradition, no_relationship, retranslation.
- Confidence weight sum invariant tested (`abs(total - 1.0) < 1e-10`).
- `score_all` tested for filtering, sorting, missing metadata.
- `detect_multi_source_digests` tested for single source, multi-source, overlapping, and non-digest classifications.

### Phonetic detection (`test_phonetic.py`, `test_phonetic_integration.py`, `test_phonetic_candidates.py`)
- Very thorough: syllable splitting, Sanskrit extraction, equivalence table building, char-by-char equivalence, equivalence groups, phonetic mapping.
- Integration tests on real dharani text (T250/T251/T901).
- False positive prevention tested: prose should not trigger phonetic matches; exact matches preferred over phonetic.
- Phonetic candidate generation tested with synthetic and real (T250/T901) data.

### Caching (`test_cache.py`)
- Comprehensive: roundtrip save/load, manifest contents, validation under corpus change, config change, version change, file added/deleted, pickle deleted, JSON corruption, hash determinism.

### Fast path (`test_fast.py`)
- Unit tests for `fast_ngram_hashes`, `fast_find_seeds`, `fast_fuzzy_extend`.
- CJK multi-byte handling tested.
- Cython/fallback equivalence tests (conditional on Cython availability).
- Chain seeds containment edge case tested.

### Cross-cutting
- Parallel equivalence in `test_parallel.py`, `test_candidates.py`, `test_phonetic_candidates.py`.
- Bisect boundary conditions in `test_edge_cases.py`.
- Known pair integration in `test_known_pairs.py`.

---

## Coverage Gaps

### 1. Stage 5: Report generation and validation (`report.py`) -- NO TESTS

This is the most significant gap. `report.py` contains:
- `validate_ground_truth()` -- validates against known pairs. This is mocked away in `test_pipeline.py` and never tested directly.
- `generate_reports()` -- generates JSON and Markdown output. Not tested.
- `_format_alignment_visualization()` -- visualization formatting. Not tested.
- `_segment_to_dict()` -- JSON serialization of segments (including phonetic mapping). Not tested.
- `_generate_summary()` -- summary report. Not tested.
- `_generate_validation_report()` -- validation report. Not tested.

**Risk:** Report formatting bugs, incorrect JSON output, or validation logic errors would not be caught. These functions also handle some non-trivial logic (interval merging for visualization, conditional phonetic mapping in JSON).

### 2. `extract_all()` and `save_results()` -- not directly tested

`extract_all()` is the top-level extraction function that:
- Scans all XML directories
- Builds the global char map
- Parallelizes `_process_text_group` calls
- Filters by `MIN_TEXT_LENGTH`

`save_results()` serializes texts to disk as `.txt` + `metadata.json`. Neither is directly unit tested. They are only exercised through mocks in `test_pipeline.py` (where they are patched out entirely) and indirectly through the `_extract_full_text` helper in `test_known_pairs.py` (which reimplements the logic).

### 3. `_process_text_group()` -- not directly tested

This is the main worker function for Stage 1 parallel extraction. It handles segment building, dharani range merging, and the `MIN_TEXT_LENGTH` filter. The `_extract_full_text` helper in `test_known_pairs.py` duplicates most of its logic but is not the production function. If `_process_text_group` diverges from the helper, tests would pass while production breaks.

### 4. `_extend_seeds()` -- only tested indirectly

`_extend_seeds()` in `align.py` is the fuzzy extension wrapper. While `fast_fuzzy_extend` is tested directly in `test_fast.py`, the orchestration logic in `_extend_seeds` (calling forward/backward fuzzy extension, determining match_type) is only exercised through `align_pair` integration tests. A dedicated unit test for the orchestration logic would be valuable.

### 5. `_phonetic_rescan()` -- only tested indirectly

This complex function (rescanning novel segments for phonetic matches, splitting segments, building phonetic mappings) is tested only through `align_pair` integration tests and `test_phonetic_integration.py`. A unit test with controlled novel segments would increase confidence.

### 6. `_find_phonetic_seeds()` -- only tested indirectly

Similar to `_find_seeds` (which has direct tests), `_find_phonetic_seeds` is only exercised through higher-level integration tests. It contains non-trivial logic: syllable-based source indexing, the "at least 2 differing chars" requirement, and best-match selection.

### 7. `resolve_worker_count()` in `config.py` -- not tested

This function has three code paths (explicit, config override, default) and a `memory_intensive` parameter that changes the cap. No tests verify these paths.

### 8. `_align_pair_wrapper()` -- source table caching not tested

This function caches k-gram tables across consecutive calls with the same source_id. While `test_fast.py::TestSourceTableCompatibility` tests table equivalence, the caching logic itself (global `_cached_source_table`) is not tested.

### 9. Pipeline orchestration (`test_pipeline.py`) -- shallow

The pipeline test file tests only cache bypass behavior. It mocks **all** stage functions, meaning it does not test:
- Correct wiring between stages (does Stage 2 output feed into Stage 3 correctly?)
- The `ENABLE_PHONETIC_SCAN` conditional path
- Memory cleanup (`del doc_freq`, `gc.collect()`)
- The `docnum_pair_set` construction from candidates
- Timing/logging logic

---

## Potential Flakiness / Brittleness

### 1. Dependency on local XML corpus

Many tests (`test_extract.py`, `test_known_pairs.py`, `test_phonetic_integration.py`, `test_phonetic_candidates.py` integration class) require the XML corpus at `xml/T/`. These tests use `pytest.skip()` when files are missing, which is correct, but:
- In CI without the corpus, a large portion of the test suite silently skips.
- There is no marker (like `@pytest.mark.integration`) to separate these from unit tests. A CI run might report "245 tests passed" when in reality only ~150 ran.

**Recommendation:** Add a `@pytest.mark.corpus` or `@pytest.mark.integration` marker and configure pytest to make skipped-due-to-missing-corpus visible.

### 2. Hardcoded coverage thresholds in integration tests

Tests like `test_t250_aligns_to_t223` assert `result.coverage >= 0.50`. These thresholds are derived from current behavior and could drift if the alignment algorithm changes. This is not inherently bad (they serve as regression guards), but several tests assert on **both** a minimum threshold AND a specific classification string (e.g., `assert score.classification == "digest"`), which doubles the brittleness.

### 3. Test data duplication

The `_extract_full_text()` helper in `test_known_pairs.py` (107 lines) **reimplements** `_process_text_group()` from `extract.py`. This means:
- Changes to production extraction logic might not be reflected in tests.
- The integration tests might pass even if the production code is broken.

**Recommendation:** Refactor to use the production `_process_text_group()` in tests, or at minimum add a cross-check test.

### 4. Phonetic table fixture scoping

`build_equivalence_table()` is called in at least 5 different test files. Some use `scope="class"`, others `scope="module"`. The table build is moderately expensive (parses DDB dictionary). The inconsistent scoping is not a correctness issue but adds unnecessary overhead.

### 5. CJK-heavy test data

Many tests embed CJK strings as test data. While this is domain-appropriate, subtle encoding issues (e.g., visually identical but codepoint-different characters) could cause hard-to-diagnose failures if the test file encoding is ever corrupted. The tests do not explicitly validate encoding.

---

## Tests That Test Implementation Details

### 1. `test_fingerprint.py::TestNgramSets::test_basic_structure`

```python
# Each entry should be a frozenset of ints
for text_id, hashes in ngram_sets.items():
    assert isinstance(hashes, frozenset)
    for h in hashes:
        assert isinstance(h, int)
```

This tests the **type** of the return value rather than its **behavior**. If the implementation switched to a regular `set` or used string hashes, these tests would fail even if the behavior was correct.

### 2. `test_fast.py::TestFastNgramHashes::test_single_char_ngrams`

```python
result = fast_ngram_hashes("AABA", 1)
# Unique: A, B -> 2 hashes
assert len(result) == 2
```

This implicitly tests that the hashing function produces no collisions for "A" vs "B", which is a property of CRC32, not the function's contract. With different hash functions, this could fail spuriously.

---

## Missing Edge Case Tests

1. **Empty source text in `align_pair`**: `test_align.py` tests empty digest but not empty source.

2. **Unicode supplementary plane characters** in extraction: The `CJK_RE` regex covers Extension B-D but there are no tests with actual supplementary plane characters in `normalize_text`.

3. **Extremely long texts**: No test verifies behavior with texts approaching or exceeding `MAX_DIGEST_LENGTH` (50,000 chars).

4. **Concurrent access to module-level globals**: `candidates.py` has a `_cleanup_candidate_globals()` function and a note "Not thread-safe", but there's no test verifying that cleanup actually occurs after `generate_candidates()`.

5. **Pickle version compatibility**: `test_cache.py` tests roundtrip but doesn't test loading a cache written by a different Python version or with a different pickle protocol.

6. **`_group_files_by_text` with letter suffixes**: The regex `r'(T\d+n\d+[A-Za-z]?)_(\d+)\.xml$'` supports optional letter suffixes (e.g., `T01n0001a`), but no test exercises this path.

7. **docNumber parsing edge cases**: The regex parsing in `extract_file` handles "No. 250 [Nos. 251-255, 257]" but there are no tests for malformed docNumber strings (e.g., empty brackets, missing numbers, non-numeric content).

8. **`score_all` with `docnumber_pairs` parameter**: The production pipeline passes `docnum_pair_set` to `score_all`, but `test_score.py::TestScoreAll` never tests with a non-empty `docnumber_pairs` set.

---

## Test Organization Notes

- **helpers.py**: Good -- shared `make_text()` factory prevents boilerplate duplication.
- **No conftest.py**: No shared fixtures or configuration at the test package level. The `phonetic_table` fixture is duplicated across 4+ files.
- **File count**: 14 test files is appropriate for the codebase size. Each maps clearly to a pipeline stage or concern.
- **Naming**: Test class and method names are descriptive and follow a consistent pattern.
- **No test for `__init__.py`**: The `digest_detector/__init__.py` module exists but appears to be empty or minimal -- not a concern.

---

## Priority Recommendations

1. **HIGH: Add tests for `report.py`** -- `validate_ground_truth()` and `generate_reports()` have zero test coverage. These are relatively simple to test with synthetic inputs.

2. **HIGH: Add integration marker** -- Tag corpus-dependent tests with `@pytest.mark.integration` so CI can distinguish unit test failures from missing-corpus skips.

3. **MEDIUM: Test `_process_text_group` directly** -- or refactor `test_known_pairs._extract_full_text()` to call the production function.

4. **MEDIUM: Test `resolve_worker_count()`** -- simple function with multiple branches, easy to test.

5. **MEDIUM: Add unit tests for `_phonetic_rescan` and `_find_phonetic_seeds`** -- complex logic that is currently only integration-tested.

6. **LOW: Consolidate `phonetic_table` fixtures** into a `conftest.py` with `scope="session"`.

7. **LOW: Add docNumber parsing edge case tests**.

8. **LOW: Test `_extend_seeds` directly** to verify match_type assignment logic.
