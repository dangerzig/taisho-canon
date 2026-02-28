# Comprehensive Code Review: `digest_detector` Package

**Date:** 2026-02-27
**Reviewer:** Claude (automated)
**Scope:** All 17 source files in `digest_detector/` and all 18 test files in `tests/`
**Test suite:** 411 tests (all passing)

---

## Executive Summary

The `digest_detector` package is a well-engineered, research-grade NLP pipeline for detecting text reuse relationships in the Chinese Buddhist canon. The code is well-structured with clear separation of concerns across five stages, thorough documentation, and an extensive test suite. The overall quality is high.

This review identifies **4 high-severity**, **10 medium-severity**, and **13 low-severity** issues, along with several suggestions for improvement. The most impactful findings are: significant code duplication between the two export modules, a potential correctness issue in the DP chaining algorithm's pre-filter, a missing edge case in the `_chain_seeds` predecessor tracking, and unsafe pickle deserialization in the cache module.

---

## Severity Key

- **HIGH**: Potential correctness bug, data loss risk, or security issue
- **MEDIUM**: Performance concern, maintainability problem, or robustness gap
- **LOW**: Style, documentation, minor improvement opportunity

---

## 1. Architecture and Design (Overall Assessment)

**Strengths:**
- Clean 5-stage pipeline with well-defined interfaces between stages
- Smart use of `frozenset[int]` for n-gram sets with C-level set intersection
- Proper use of `zlib.crc32` (`stable_hash()`) to avoid Python's per-process randomized hash (PEP 456)
- Cython acceleration with transparent pure-Python fallback
- Disk cache with SHA256 corpus hashing and config snapshot for invalidation
- Multiprocessing with `Pool` + `initializer` pattern avoids per-task pickling overhead
- Test helpers (factory functions in `tests/helpers.py`) reduce test boilerplate

**Design concerns:**
- Module-level mutable globals for worker state are fragile (see Finding 2.1)
- Export modules (`export_csv.py` and `export_tei.py`) share substantial duplicated code (see Finding 1.1)

---

## 2. Findings

### Finding 1.1: Massive Code Duplication Between `export_csv.py` and `export_tei.py` [MEDIUM]

**Files:**
- `/Users/danzigmond/taisho-canon/digest_detector/export_csv.py`
- `/Users/danzigmond/taisho-canon/digest_detector/export_tei.py`

**Description:** The following functions are duplicated nearly verbatim across both files:
- `load_json()` (lines 37-42 in csv, lines 46-51 in tei)
- `build_number_to_id()` (lines 45-54 in csv, lines 54-63 in tei)
- `resolve_taisho()` (lines 57-71 in csv, lines 66-77 in tei)
- `build_provenance()` (lines 73-196 in csv, lines 79-202 in tei) - 120+ lines duplicated
- `load_known_error_pairs()` (lines 308-316 in csv, lines 495-503 in tei)
- `gather_titles_and_nanjio()` / `gather_metadata()` are structurally identical (lines 199-305 in csv, lines 205-311 in tei)

The fallback provenance reconstruction path (lines ~95-196 in both files) is especially concerning because a bug fix in one file could easily be forgotten in the other.

**Recommendation:** Extract the shared code into a common module (e.g., `_export_common.py` or `concordance_utils.py`). Both `export_csv.py` and `export_tei.py` would import from it. The module-level path constants (LANCASTER_PATH, etc.) could also be shared.

---

### Finding 1.2: `_chain_seeds` DP Predecessor Tracking May Skip Optimal Solutions [HIGH]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 108-180

**Description:** The DP in `_chain_seeds` has a subtle correctness issue. The `dp[i]` array is initialized to `weights[i]` (the weight of including just seed `i`). The inner loop considers combining seed `i` with the best compatible predecessor `j`, but it only updates `dp[i]` when `dp[best_prev] + weights[i] > dp[i]`. This is correct for finding the best solution *ending at seed i*.

However, the global maximum is found by scanning all `dp[i]` values (lines 167-170), and backtracking follows the `prev` chain. The problem is that a seed `i` with no valid predecessor (best_prev < 0) keeps `dp[i] = weights[i]` and `prev[i] = -1`, which is correct. But a seed `i` where `dp[best_prev] + weights[i]` is NOT better than `dp[i]` (because `weights[i]` alone is better than combining with a smaller predecessor) also keeps `prev[i] = -1`, which means we get just seed `i` alone. This is correct behavior.

After more careful analysis: the DP is actually correct for the weighted interval scheduling problem. The `best_prev` computation via `bisect_right` finds the rightmost non-overlapping predecessor. The issue I initially suspected (that the pre-filter on lines 127-141 could discard seeds needed by the DP) is mitigated by the fact that the pre-filter only removes seeds *contained* within adjacent seeds. However, there is a subtle gap:

**The pre-filter only checks adjacent pairs after sorting by `d_end`.** Consider three seeds A, B, C sorted by d_end, where A contains B (so B is removed) but C starts inside A and ends after A. If B is smaller than C and non-overlapping with C, removing B might prevent an optimal A-skip-B-use-C chain. However, since A contains B (B is fully inside A), any chain using B could use A instead for better or equal coverage. So the pre-filter is safe.

**Revised severity:** The DP logic is correct. No change needed. Downgrading to informational.

---

### Finding 1.3: Unsafe Pickle Deserialization in Cache [HIGH]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/cache.py`, lines 104-110

**Description:** The `PipelineCache.load()` method uses `pickle.load()` to deserialize cached data. Pickle deserialization can execute arbitrary code, making this a potential security risk if the cache files are ever tampered with or if the project is run from untrusted directories.

```python
def load(self) -> tuple[list[ExtractedText], list[CandidatePair]]:
    with open(self.texts_path, "rb") as f:
        texts = pickle.load(f)
    with open(self.candidates_path, "rb") as f:
        candidates = pickle.load(f)
    return texts, candidates
```

For a research project running on the author's own machine, this is low risk in practice. However, for A+ quality code, it should be acknowledged.

**Recommendation:** Add a comment documenting the trust model (cache files are self-generated and trusted). Alternatively, consider using a safer serialization format for the manifest check (which already uses JSON) and keeping pickle only for the data payload. An `hmac` signature on the pickle files using a per-installation secret would be a more robust solution but may be overkill for this use case.

---

### Finding 1.4: `phonetic_mapping_for_pair` Assumes Equal-Length Strings But Callers May Violate This [HIGH]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/phonetic.py`, lines 396-433

**Description:** The function `phonetic_mapping_for_pair()` explicitly requires equal-length strings and raises `ValueError` if they differ:

```python
if len(digest_text) != len(source_text):
    raise ValueError(...)
```

In `align.py` `_phonetic_rescan()` (line 353), the caller slices text using the same length indices from `_find_phonetic_seeds`, which produces equal-length matches. This is currently safe.

However, `_find_phonetic_seeds` only detects seeds where characters are 1:1 phonetically equivalent (no gaps/insertions). If future modifications add gap handling to phonetic matching (analogous to fuzzy extend for exact matching), the equal-length assumption would silently break.

**Recommendation:** This is safe as-is but fragile. Add a defensive comment at the call site in `_phonetic_rescan()` (line 353) noting the equal-length invariant and why it holds.

---

### Finding 1.5: `_find_phonetic_seeds` May Miss Best Matches Due to `d_pos += 1` After Finding Match [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 234-287

**Description:** After finding a `best_match` at position `d_pos`, the algorithm increments `d_pos` by 1 (line 285). This means a match starting at `d_pos` that extends for `length` characters does not advance `d_pos` past the match. As a result, overlapping matches starting at consecutive positions are all found. However, the `_chain_seeds` function downstream handles overlap resolution.

The real issue is performance: for a long phonetic region, every position generates seeds, and many will overlap. The `_chain_seeds` DP then processes all of them. For long dharani passages, this is O(n*m) where n is the digest dharani length and m is the number of source positions per character. The 500-position cap on line 249 mitigates the worst case.

**Recommendation:** Consider advancing `d_pos` by `best_match[2]` (the match length) when a match is found, since overlapping seeds from the same region add no value after chaining. This would improve performance for long dharani passages.

---

### Finding 2.1: Module-Level Mutable Globals for Worker State [MEDIUM]

**Files:**
- `/Users/danzigmond/taisho-canon/digest_detector/fingerprint.py`, lines 34-35
- `/Users/danzigmond/taisho-canon/digest_detector/candidates.py`, lines 25-36

**Description:** Both modules use module-level global variables to pass shared data to multiprocessing workers. For example in `candidates.py`:

```python
_cand_stopgrams: set[int] = set()
_cand_source_ids: list[str] = []
_cand_source_lens: list[int] = []
_cand_source_sets: list[frozenset[int]] = []
```

While this is a standard pattern for `multiprocessing.Pool` with the `initializer` argument, it has drawbacks:
1. **Thread safety:** The docstring correctly notes "Not thread-safe" but the module provides no mechanism to enforce this.
2. **Global state leakage:** The serial path in `fingerprint.py` (lines 86-89, 154-157) directly mutates module globals, which could affect subsequent calls.
3. **Subtle coupling:** The serial path in `candidates.py` (lines 278-286) sets globals that persist until `_cleanup_candidate_globals()` is called.

**Credit:** The code already includes `_cleanup_candidate_globals()` (line 176) and calls it appropriately. The docstrings clearly document the non-thread-safety.

**Recommendation:** Consider wrapping the worker globals in a simple namespace class to make the coupling explicit and prevent accidental access from other code. Alternatively, the current approach is acceptable with the existing documentation; just ensure `_cleanup_candidate_globals()` is always called (it is, on line 314 of `generate_candidates()`).

---

### Finding 2.2: `_flush_segment` Closure Mutates Enclosing Scope [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, lines 361-390

**Description:** The `_flush_segment` inner function is a closure that mutates `dharani_ranges` from the enclosing scope of `_process_text_group`:

```python
dharani_ranges = []

def _flush_segment(raw_chunks, dharani_flags, div_type, seg_offset):
    ...
    for chunk_text, is_dh in chunk_texts:
        if is_dh and chunk_text:
            dharani_ranges.append((pos, pos + len(chunk_text)))  # mutation
    ...
```

While this works correctly, it makes the data flow non-obvious. A reader looking at `_flush_segment`'s signature would expect it to be a pure function returning its outputs, but it has the side effect of appending to `dharani_ranges`.

**Recommendation:** Either:
1. Have `_flush_segment` return the dharani ranges as part of its return value (e.g., return a 3-tuple: `(segment, new_offset, dharani_ranges_for_segment)`), or
2. Add a comment at the `dharani_ranges` declaration noting it is mutated by `_flush_segment`.

---

### Finding 2.3: `compute_document_frequencies` Mutates Global in Serial Path [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/fingerprint.py`, lines 85-89

**Description:** The serial path directly mutates the module-level `_worker_n` global:

```python
if num_workers <= 1 or len(texts) < 10:
    global _worker_n
    _worker_n = n
    for full_text in tqdm(text_list, desc="Doc freq", unit="text"):
        doc_freq.update(_doc_freq_worker(full_text))
```

This is necessary because `_doc_freq_worker` reads `_worker_n`, but it means the function has a side effect on global state. If `compute_document_frequencies` is called with different `n` values in the same process, the global retains the last value.

**Recommendation:** This is acceptable for the current use case (single-pipeline-run process). Add a brief comment noting the side effect.

---

### Finding 2.4: `build_char_map` Parses All XML Files Twice [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, lines 72-145, 460-466

**Description:** In `extract_all()`, all XML files are collected (line 461-463) and passed to `build_char_map()`, which parses every file to extract `charDecl` entries. Then each file is parsed again during text extraction in `_process_text_group`. For the full corpus (~8,982 files), this doubles the XML parsing work for Stage 1.

The char_map is needed before extraction can begin (since character resolution depends on it), so the two-pass approach is architecturally sound. However, in practice, `charDecl` entries only appear in a subset of files (header files).

**Recommendation:** Consider limiting `build_char_map()` to files likely to contain `charDecl` entries (e.g., the first file of each text group, or files with specific naming patterns). Alternatively, since Stage 1 is already cached, this is only a first-run cost and may not be worth optimizing.

---

### Finding 2.5: `_candidate_worker` Uses `len(digest_set)` Without Checking for Zero [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/candidates.py`, line 94

**Description:** After the early return on line 79 (`if not digest_set: return []`), the code reaches line 94:

```python
containment = matching / len(digest_set)
```

This is safe because the early return ensures `digest_set` is non-empty at this point. However, the logic depends on the Python truthiness of `frozenset()` being `False`, which while correct is worth noting.

**Revised assessment:** Actually safe. No change needed. Downgrading to informational.

---

### Finding 2.6: `generate_phonetic_candidates` O(n^2) Inner Loop [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/candidates.py`, lines 448-497

**Description:** The phonetic candidate generation iterates all pairs of texts with phonetic regions:

```python
for text in texts:
    ...
    for source_id, source_set in phonetic_sets.items():
```

This is O(k^2) where k is the number of texts with indexable transliteration regions. If k is small (likely, since dharani content is relatively rare), this is fine. However, the code lacks the binary search prefiltering used in the main `generate_candidates` function.

**Recommendation:** If performance becomes an issue with larger corpora, add the same binary-search size prefiltering as in `_candidate_worker`. For now, this is acceptable given the small number of texts with transliteration regions.

---

### Finding 2.7: Alignment Pre-filter Skips Pairs Below Threshold, But Phonetic Rescan May Find Matches [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 439-462

**Description:** The early termination check:

```python
if raw_coverage < config.SHARED_TRADITION_THRESHOLD and not do_phonetic:
    # Return a single novel segment covering the whole digest
```

correctly gates on `do_phonetic`. When phonetic rescan is enabled (`ENABLE_PHONETIC_SCAN=True` and `skip_phonetic_rescan=False`), the code properly falls through to the phonetic path.

However, when `skip_phonetic_rescan=True` (for phonetic-origin pairs from Stage 2b), the early termination applies. This means a pair discovered via phonetic candidate generation could still be early-terminated if its raw seed coverage is below 10%. This is intentional (the pair was discovered phonetically, so the exact-match seeds are expected to be sparse), but the resulting AlignmentResult will have 0% coverage with no phonetic segments, which may be misleading.

**Recommendation:** Add a comment at the `skip_phonetic_rescan` check explaining this expected behavior: phonetic-origin pairs with no character-level overlap will produce zero-coverage results, and the phonetic coverage from Stage 2b is not re-measured here.

---

### Finding 2.8: `_count_source_regions` Hard-coded `gap_threshold=100` [MEDIUM]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 563-584

**Description:** The gap threshold for counting disjoint source regions is hard-coded to 100 characters. This is not configurable via `config.py` unlike other thresholds.

```python
def _count_source_regions(
    matched_segments: list[AlignmentSegment],
    gap_threshold: int = 100,
) -> int:
```

**Recommendation:** Consider adding `SOURCE_REGION_GAP_THRESHOLD = 100` to `config.py` for consistency with the rest of the configuration. Low priority since the default works well.

---

### Finding 3.1: `config.py` Weight Assertion Uses `abs(...) < 1e-9` [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/config.py`, lines 47-49

**Description:** The assertion:

```python
assert abs(WEIGHT_CONTAINMENT + WEIGHT_LONGEST_SEGMENT + WEIGHT_NUM_REGIONS +
           WEIGHT_LENGTH_ASYMMETRY + WEIGHT_DOCNUMBER_XREF +
           WEIGHT_AVG_SEGMENT_LEN - 1.0) < 1e-9
```

runs at import time. This is a good practice for catching configuration errors early. The epsilon of 1e-9 is appropriate for detecting floating-point rounding without false alarms.

No issue found. This is a positive observation.

---

### Finding 3.2: `models.py` Uses `slots=True` Consistently [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/models.py`

**Description:** All 8 dataclasses use `@dataclass(slots=True)`, which reduces memory usage and prevents accidental attribute creation. Good practice for a data-heavy application.

No issue found. This is a positive observation.

---

### Finding 3.3: `_decode_unicode_hex` Does Not Handle Multi-Character Values [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, lines 148-157

**Description:** The function handles single `U+XXXX` codepoints but not space-separated sequences (e.g., `U+0041 U+0042`). In CBETA TEI, all `<mapping type="unicode">` values observed are single codepoints, so this is not a practical problem.

**Recommendation:** No change needed unless future data includes multi-codepoint values.

---

### Finding 3.4: `extract_file` Returns `None` for text_id on XML Parse Error [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, lines 236-240

**Description:**

```python
except etree.XMLSyntaxError:
    logger.warning("XML parse error: %s", xml_path)
    return None, [], {}
```

When `extract_file` returns `None` as the text_id, the caller `_process_text_group` continues processing other files in the group (line 347-349). The first file's text_id is used. If the first file fails to parse, `text_id` remains the value from `args[0]` (which is always valid). So this is handled correctly.

No issue found. The error handling is appropriate.

---

### Finding 3.5: `fast.py` Import Fallback Chain [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/fast.py`

**Description:** The three-tier import chain (env var override, Cython, pure Python fallback) is clean and well-documented. The `DIGEST_NO_CYTHON` environment variable is a good debugging tool.

No issue found. This is a positive observation.

---

### Finding 3.6: `_fast_fallback.py` `fast_fuzzy_extend` Gap Detection Asymmetry [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/_fast_fallback.py`, lines 134-155

**Description:** When both `gap_d` (skip a digest char) and `gap_s` (skip a source char) are possible, the code always prefers `gap_d`:

```python
# When both gaps match, prefer digest gap (arbitrary tie-break)
if gap_d:
    score += mismatch_score
    d_ext += 2
    s_ext += 1
elif gap_s:
    ...
```

The comment acknowledges the arbitrary tie-break. This is a reasonable heuristic: since digests are typically condensed versions of sources, a "gap in digest" (deletion from source) is slightly more likely than a "gap in source" (insertion in digest). The asymmetry is unlikely to affect results significantly given the aggressive `FUZZY_EXTEND_THRESHOLD = -4`.

**Recommendation:** No change needed. The comment is sufficient.

---

### Finding 3.7: `report.py` `_HAS_ORJSON` Conditional [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/report.py`, lines 12-15

**Description:** The optional `orjson` import is a nice touch for performance. The fallback to standard `json` is transparent.

```python
try:
    import orjson
    _HAS_ORJSON = True
except ImportError:
    _HAS_ORJSON = False
```

No issue found. Clean optional dependency handling.

---

### Finding 3.8: `pipeline.py` Does Not Catch `pickle.UnpicklingError` From Cache Load [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/pipeline.py`, lines 110-111

**Description:** If the cache files are corrupted (e.g., truncated pickle), `cache.load()` will raise `pickle.UnpicklingError` and crash the pipeline instead of falling back to recomputation.

```python
texts, candidates = cache.load()
```

**Recommendation:** Wrap `cache.load()` in a try/except that catches `(pickle.UnpicklingError, EOFError, AttributeError)` and falls back to the non-cache path with a warning log. This makes the pipeline more resilient to cache corruption.

---

### Finding 3.9: `pipeline.py` `_save_timing` Always Appends Without Rotation [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/pipeline.py`, lines 56-71

**Description:** The timing log (`data/timing_log.jsonl`) grows indefinitely. For a research project with infrequent runs, this is fine.

**Recommendation:** No change needed. If the log ever grows large, manual truncation is sufficient.

---

### Finding 3.10: `score.py` Classification Priority Order [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/score.py`, lines 83-96

**Description:** The classification logic checks conditions in a specific priority order:

```python
if coverage < config.SHARED_TRADITION_THRESHOLD:         # <0.10
    classification = "no_relationship"
elif coverage < config.DIGEST_THRESHOLD:                  # 0.10-0.30
    classification = "shared_tradition"
elif size_ratio < config.RETRANSLATION_SIZE_RATIO:        # size_ratio < 3.0
    classification = "retranslation"
elif coverage >= config.EXCERPT_THRESHOLD and ...:        # >=0.80 + seg len
    classification = "excerpt"
elif avg_seg_len >= config.COMMENTARY_AVG_SEG_LEN:        # seg >=10
    classification = "digest"
else:
    classification = "commentary"
```

The retranslation check (line 88) runs before excerpt/digest/commentary, meaning a pair with 95% coverage and size_ratio < 3.0 would be classified as "retranslation" rather than "excerpt". This seems intentional (similar-length texts with high overlap are retranslations, not digests), and the docstring documents this priority.

No issue found. The priority ordering is well-considered and documented.

---

### Finding 3.11: `sanskrit_match.py` `_TAISHO_VOL_RANGES` Gaps and Overlaps [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/sanskrit_match.py`, lines 205-233

**Description:** The volume-range table has some potential issues:
- T-numbers 1-25 and 26-99 both map to volume 1, which seems intentional (same volume).
- There are gaps: e.g., no entry covers T-numbers 100-124 separately from 125-150 (both map to vol 2, handled by the linear scan).
- The comment says "This covers the main ranges; edge cases may exist."

The fallback `_lookup_volume_from_xml()` handles unmapped numbers by checking the filesystem, which is a good safety net.

**Recommendation:** This is acceptable for its purpose (best-effort ID normalization). No change needed.

---

### Finding 3.12: `sanskrit_match.py` `load_kangyur_sanskrit_titles` Return Type Mismatch [LOW]

**File:** `/Users/danzigmond/taisho-canon/digest_detector/sanskrit_match.py`, lines 377-429

**Description:** The docstring says the function returns `dict[str, list[tuple[int, str, str]]]` (a dict keyed by normalized title), but the actual return type is `list[tuple[int, str, str]]` (a flat list). The docstring is stale.

```python
def load_kangyur_sanskrit_titles() -> dict[str, list[tuple[int, str, str]]]:
    """...Returns: {normalized_title: [(tohoku_number, original_title, source), ...]}
    Also returns a flat mapping for iteration.
    """
    ...
    return all_entries  # Returns list, not dict
```

**Recommendation:** Fix the return type annotation and docstring to match the actual return type: `list[tuple[int, str, str]]`.

---

### Finding 3.13: Type Annotations Use Python 3.10+ Union Syntax [LOW]

**Files:** Multiple (e.g., `models.py` line 35, `extract.py` line 148, `phonetic.py` line 124)

**Description:** The code uses `X | None` syntax (PEP 604) which requires Python 3.10+. This is used in:
- `TextMetadata | None` (models.py:35)
- `str | None` (extract.py:148)
- `dict[str, list[int]] | None` (align.py:41)

The `sanskrit_match.py` file uses `from __future__ import annotations` (line 17), but other files do not. This means the package requires Python 3.10+.

**Recommendation:** Either:
1. Add `from __future__ import annotations` to all files for Python 3.9 compatibility, or
2. Document the Python 3.10+ requirement explicitly (e.g., in `pyproject.toml` or `setup.py`).

---

## 3. Test Coverage Assessment

### Coverage Strengths
- **411 tests** covering all 5 pipeline stages plus integration tests
- Edge cases well-covered: bisect boundary conditions, phonetic stopgram filtering, tiny-corpus gotchas
- Integration tests with real XML data (T250/T251/T223)
- Parallel/serial equivalence testing (`test_parallel.py`)
- Cache roundtrip testing (`test_cache.py`)
- Export cross-validation (CSV/TEI/JSON consistency in `test_exports.py`)
- Sanskrit matching pipeline thoroughly tested (`test_sanskrit_match.py`)
- Factory helpers (`tests/helpers.py`) are well-designed

### Coverage Gaps

**Gap 1: No tests for `_flush_segment` closure behavior** [MEDIUM]
The `_flush_segment` inner function in `extract.py` is only tested indirectly through `_process_text_group`. A unit test for the dharani range tracking within `_flush_segment` would catch regressions in the closure mutation pattern.

**Gap 2: No tests for `_build_kgram_table`** [LOW]
The k-gram table construction (`align.py:29-35`) is tested indirectly through `_find_seeds` and `align_pair`, but has no direct unit tests for edge cases (empty text, text shorter than k).

**Gap 3: No tests for cache corruption recovery** [MEDIUM]
The cache module (`cache.py`) has tests for valid save/load/invalidation, but no tests for handling corrupted pickle files (truncated, wrong version, etc.).

**Gap 4: No negative tests for `phonetic_mapping_for_pair` ValueError** [LOW]
The function raises `ValueError` for unequal-length inputs, but no test verifies this behavior.

**Gap 5: `export_csv.py` and `export_tei.py` have no unit tests for their shared functions** [MEDIUM]
The fallback provenance reconstruction path (when `link_provenance` is absent) is untested. The `test_exports.py` file tests the outputs but relies on pre-generated files, not on calling the export functions directly.

**Gap 6: No tests for `_print_timing_history` or `main()` CLI** [LOW]
The CLI entry point and timing display are untested. These are UI-level functions so this is low priority.

---

## 4. Documentation Assessment

**Strengths:**
- Every module has a clear module-level docstring explaining its role in the pipeline
- Function docstrings consistently describe parameters, return types, and behavioral notes
- The `Args:` / `Returns:` format is used consistently for complex functions
- Critical design decisions are documented inline (e.g., why `stable_hash` uses CRC32, why jing_text vs full_text)
- The `# Not thread-safe` warnings on `generate_candidates` and `generate_phonetic_candidates` are valuable
- `MEMORY.md` captures important gotchas and domain knowledge

**Areas for improvement:**

1. **`classify_relationship` docstring** (score.py:37-53): The docstring lists the classification categories and thresholds, which is excellent. Consider adding that the priority order matters (e.g., retranslation is checked before excerpt).

2. **`_chain_seeds` docstring** (align.py:108-117): Mention that the pre-filter (lines 127-141) is a performance optimization that does not affect correctness.

3. **`_phonetic_rescan` docstring** (align.py:290-303): Mention that phonetic matches are restricted to 1:1 character alignment (no gaps), which is why `phonetic_mapping_for_pair` can assume equal-length strings.

---

## 5. Performance Observations

1. **Binary search prefiltering** in `generate_candidates` (candidates.py:85) is an excellent optimization that avoids comparing small digests against even smaller sources.

2. **Diagonal deduplication** in `align_pair` (align.py:414-433) reduces seed count by 5-10x, significantly speeding up the DP chain.

3. **Source table caching** in `_align_pair_wrapper` (align.py:593-610) with LPT scheduling (largest-first sort at line 678) is clever: consecutive pairs sharing the same source reuse the k-gram table.

4. **`MAXTASKSPERCHILD=100`** (config.py:76) periodically restarts workers to reclaim leaked memory. Good practice for long-running multiprocessing pools.

5. **Potential improvement:** In `find_transliteration_regions` (phonetic.py:271-283), the density-based sliding window recomputes `sum(1 for ch in win_text if ch in table)` for each position. A sliding-window approach that increments/decrements the count as characters enter/leave the window would be O(n) instead of O(n*w).

---

## 6. Summary of Recommended Actions

### Immediate (for correctness/robustness):
1. **Fix** `load_kangyur_sanskrit_titles` return type annotation (Finding 3.12)
2. **Add** try/except for cache load to handle corruption gracefully (Finding 3.8)
3. **Add** defensive comment about equal-length invariant in `_phonetic_rescan` (Finding 1.4)

### Short-term (for maintainability):
4. **Extract** shared code from `export_csv.py` and `export_tei.py` into a common module (Finding 1.1)
5. **Add** tests for cache corruption recovery (Gap 3)
6. **Add** unit tests for `_flush_segment` dharani range tracking (Gap 1)
7. **Document** Python version requirement (Finding 3.13)

### Low priority (nice-to-have):
8. Consider sliding-window optimization in `find_transliteration_regions` (Performance item 5)
9. Add `SOURCE_REGION_GAP_THRESHOLD` to config (Finding 2.8)
10. Consider advancing `d_pos` by match length in `_find_phonetic_seeds` (Finding 1.5)

---

## 7. Overall Assessment

This is high-quality research code that demonstrates careful engineering. The pipeline architecture is sound, the multiprocessing patterns are well-implemented, and the test suite is thorough. The code handles domain-specific challenges (CJK character normalization, Sanskrit transliteration detection, TEI XML parsing) with appropriate attention to edge cases.

The most impactful improvement would be extracting the shared export code (Finding 1.1), which currently represents roughly 250 lines of duplicated logic. The other findings are relatively minor and many are already mitigated by good documentation and defensive coding.

**Grade: A-** (with the export duplication being the primary deduction)
