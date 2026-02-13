# Top-to-Bottom Code Review: digest_detector Pipeline

**Date:** 2026-02-13
**Scope:** Full review of all 10 source files and 4 test files
**Reviewer:** Claude Opus 4.6
**Test suite:** 59 tests, all passing
**Previous review:** jing-aware-pipeline-review.md (all identified issues resolved)

---

## Overall Grade: A-

The codebase is well-structured, correct for its purpose, and thoroughly tested on real data. The 5-stage pipeline (extract, fingerprint/candidates, align, score, report) is cleanly separated with clear data flow through well-defined dataclasses. The jing-aware changes from the previous review are properly integrated with explanatory comments. The main gaps are: a few pieces of dead code, one potentially incorrect calculation in multi-source digest detection, missing test files for two modules, and some minor performance patterns that will matter at full corpus scale.

---

## Previous Review Status

All issues from jing-aware-pipeline-review.md are resolved:

| ID | Status | Detail |
|----|--------|--------|
| D1 | Fixed | Unused `asdict` import removed from `report.py` |
| D2 | Fixed | Unused `defaultdict` import removed from `test_known_pairs.py` |
| T1 | Fixed | `test_score_all_with_text_map` added at line 362 |
| T2 | Fixed | `test_t250_not_digest_of_t251` now passes `jing_text` lengths (line 244-245) |
| C1 | Fixed | Comment at `candidates.py:114-118` explaining jing_text vs full_text asymmetry |
| C2 | Fixed | Comment at `candidates.py:149-152` documenting intentional mixed full/jing length |
| F1 | Fixed | Comments at `fingerprint.py:49-51` and `fingerprint.py:95-97` documenting full_text usage |
| S1 | Fixed | `score.py:88` now uses `digest_jing_length` for `_compute_confidence()` normalization |

---

## What Is Done Well

**Architecture.** The 5-stage pipeline with explicit dataclass boundaries (ExtractedText, CandidatePair, AlignmentResult, DigestScore) creates clear contracts between stages. Each stage can be tested and reasoned about independently.

**Domain modeling.** The `jing_text` property with fallback to `full_text` elegantly handles the asymmetry between texts with and without div annotations (~2400 texts have no jing/xu divisions). The `DivSegment` dataclass preserves enough structure for segment-level analysis without over-engineering.

**XML parsing.** The CBETA TEI P5b parser correctly handles the priority chain (normalized form > normal_unicode > unicode), the lem/rdg selection, tail text from skipped elements, and nested div tracking. The SKIP_TAGS/INCLUDE_TAGS separation makes the parsing rules explicit and maintainable.

**Test quality.** Tests operate on real XML data (T250, T251, T223) with `pytest.skip` guards when files are absent. The integration tests in `test_known_pairs.py` verify the full pipeline chain from extraction through classification, with both positive tests (T250 is a digest of T223) and negative tests (T250 is not a digest of T251). The jing-text unit tests cover the key edge cases (empty segments, no-jing segments, fallback behavior).

**Comments.** The recent additions explaining the jing_text/full_text asymmetry (candidates.py:114-118, fingerprint.py:49-51, fingerprint.py:95-97) are clear and address the exact points a future reader would question.

**Alignment algorithm.** The seed-and-extend approach with weighted interval scheduling DP is well-suited to the problem. The fuzzy extension with single-character gap handling and X-drop termination is a reasonable trade-off between sensitivity and performance.

---

## Issues by Severity

### Major

#### M1. `detect_multi_source_digests` uses approximate digest length instead of actual
**File:** `/Users/danzigmond/taisho-canon/digest_detector/score.py`, line 242
**Description:** The combined coverage calculation uses `max(covered_positions) + 1` as the denominator:
```python
d_len_approx = max(covered_positions) + 1
combined_coverage = len(covered_positions) / d_len_approx
```
If the digest has novel material at the end (after all matched positions), this denominator is smaller than the actual digest length, inflating combined_coverage. Since the function receives `scores` which contain the digest_id, and the actual digest length is available through the metadata or the alignment's segments, the correct denominator is the true digest length.

Additionally, `d_meta_len = max(s.coverage for s in digest_scores)` at line 238 is computed but never used -- it is dead code (a leftover from a previous approach).

**Suggested fix:** Pass `metadata_map` to this function and use `metadata_map[digest_id].char_count` as the denominator. Remove the unused `d_meta_len` variable.

#### M2. No dedicated test files for `candidates.py` and `score.py`
**File:** `/Users/danzigmond/taisho-canon/tests/`
**Description:** There are no `test_candidates.py` or `test_score.py` files. The candidate generation and scoring logic is only tested indirectly through `test_known_pairs.py` integration tests. This means:
- `_parse_docnumber_to_text_ids` has no unit test for edge cases (malformed text IDs, empty refs)
- `_find_docnumber_pairs` has no test for the size-ordering logic
- `classify_relationship` classification branches for "commentary" and "shared_tradition" have no direct tests
- `_compute_confidence` has no unit test verifying the weight calculation
- `detect_multi_source_digests` has no test at all (the integration tests only have 2-3 texts, never triggering multi-source)

**Suggested fix:** Add `test_candidates.py` with unit tests for docnumber parsing, pair ordering, and containment filtering. Add `test_score.py` with unit tests for each classification branch and for multi-source detection.

---

### Minor

#### m1. Dead variable `seen_files` in `build_char_map`
**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, line 89
**Description:** `seen_files = set()` is declared but never read or written to. The comment on line 92 says "avoid re-parsing" but the dedup is actually done via `char_id in char_map` (line 101), not via file tracking.
**Suggested fix:** Remove line 89 (`seen_files = set()`).

#### m2. Dead compiled regex `STRIP_PUNCT`
**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, lines 62-66
**Description:** `STRIP_PUNCT` is compiled but never referenced. The `normalize_text` function uses `CJK_RE.findall()` instead (a positive-match approach that implicitly strips everything non-CJK). The regex also has overlapping ranges: `\u3000` appears as a standalone character AND within `\u3000-\u303F`, and `\u3001-\u303F` partially overlaps with the earlier `\u3000-\u303F`.
**Suggested fix:** Remove the `STRIP_PUNCT` definition (lines 62-66).

#### m3. Redundant conditional in `_extract_text_recursive` tail handling
**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, lines 202-206
**Description:** The two branches of the if/elif both perform the same action:
```python
if child.tag not in SKIP_TAGS and child.tail:
    results.append((child.tail, current_div))
elif child.tag in SKIP_TAGS and child.tail:
    # Tail of skipped elements still belongs to parent
    results.append((child.tail, current_div))
```
This simplifies to `if child.tail: results.append((child.tail, current_div))`. The comment explaining the semantic reason is valuable and should be preserved, but the branching logic is unnecessarily complex.
**Suggested fix:** Collapse to:
```python
# Tail text always belongs to the parent, even for skipped elements
if child.tail:
    results.append((child.tail, current_div))
```

#### m4. Source span calculation uses per-position set for potentially large ranges
**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 339-343
**Description:** The source_span calculation builds a `set()` of every individual character position:
```python
source_positions = set()
for seg in matched_segments:
    for p in range(seg.source_start, seg.source_end):
        source_positions.add(p)
source_span = len(source_positions) / s_len
```
For T223 with ~286K characters, this creates a set with potentially tens of thousands of integers per alignment pair. While functional, this could be computed more efficiently using interval merging (sort intervals, merge overlapping, sum lengths).

The same pattern appears in `detect_multi_source_digests` (score.py, lines 227-235) for digest positions.

**Suggested fix:** Replace with interval-merging approach:
```python
intervals = sorted((seg.source_start, seg.source_end) for seg in matched_segments)
merged_len = 0
cur_start, cur_end = intervals[0]
for s, e in intervals[1:]:
    if s <= cur_end:
        cur_end = max(cur_end, e)
    else:
        merged_len += cur_end - cur_start
        cur_start, cur_end = s, e
merged_len += cur_end - cur_start
source_span = merged_len / s_len
```

#### m5. `_chain_seeds` dedup filter only checks adjacent elements
**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 200-212
**Description:** The containment filter for removing duplicate seeds only compares each seed against the immediately previous seed in the `filtered` list. Since seeds are sorted by end position (not start), a seed could be contained within a non-adjacent earlier seed. For example, seeds sorted by end: `(0, 20, ...), (5, 15, ...), (10, 25, ...)` -- the middle seed is contained in the first, but after the first seed is processed and the middle seed is compared only to the first, this works. However, if the sort order produces `(0, 20, ...), (10, 25, ...), (5, 15, ...)` -- the third seed would be compared only to the second, and the containment check `d_start >= prev[0] and d_end <= prev[1]` would evaluate `5 >= 10` which is False, so it would not be filtered. In practice this is unlikely because the DP handles overlaps correctly, but the dedup is not fully correct.
**Suggested fix:** Since the DP already handles overlapping intervals correctly, either remove the dedup filter (let the DP handle it) or implement a proper containment-removal pass.

#### m6. `_fuzzy_extend` can produce asymmetric extensions with gaps
**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 125-136
**Description:** When a gap is detected (mismatch with a look-ahead match), the function advances d_ext by 2 and s_ext by 1 (or vice versa). However, the next iteration re-computes `d_idx` and `s_idx` from the new positions, which means the gap character is silently skipped. The resulting `best_d_ext` and `best_s_ext` may not be symmetric: the extension counts the gap character as covered in one text but not the other. This means the extended segment boundaries include gap characters, which slightly inflates the matched-text length. The `match_type` is correctly set to "fuzzy" so downstream consumers can distinguish, but the segment text (`digest_text[d_start:d_end]`) will include the gap characters.

This is a design choice rather than a bug, and the impact is small (each gap contributes at most one character), but it is worth documenting.
**Suggested fix:** Add a comment in `_extend_seeds` noting that fuzzy segments may include gap characters and that their lengths are therefore approximate.

#### m7. `_find_seeds` picks only the longest match per digest position
**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 57-66
**Description:** For each digest position, the function iterates all source matches for the k-gram and keeps only the single longest extension (`best_match`). If there are two source positions with equally long matches at the same digest position, only the last one scanned is kept (due to `>` not `>=` on line 65). This means the algorithm is greedy: it may miss a shorter match at one digest position that would enable a better chain overall.

Since the chaining DP maximizes total coverage, missing one potential match is unlikely to affect the final result significantly. But it could cause slightly suboptimal chaining in rare cases.
**Suggested fix:** Consider keeping all matches (not just the longest) and letting the chaining DP select the optimal combination. This would increase the number of seeds passed to `_chain_seeds` but would guarantee optimality. Alternatively, document the greedy choice.

---

### Nit

#### N1. `config.py` weights lack a comment verifying they sum to 1.0
**File:** `/Users/danzigmond/taisho-canon/digest_detector/config.py`, lines 38-43
**Description:** The six confidence weights (0.35 + 0.20 + 0.10 + 0.10 + 0.15 + 0.10) sum to 1.0, which is correct. Adding a comment `# Must sum to 1.0` would prevent future edits from accidentally breaking this invariant.
**Suggested fix:** Add `# Must sum to 1.0` after line 43.

#### N2. `TextMetadata.metadata` defaults to `None` without type annotation
**File:** `/Users/danzigmond/taisho-canon/digest_detector/models.py`, line 35
**Description:** `metadata: TextMetadata = None` should be `metadata: TextMetadata | None = None` for type-correctness. The current annotation says the field is always `TextMetadata`, but the default is `None`.
**Suggested fix:** Change to `metadata: TextMetadata | None = None`.

#### N3. No `__all__` in `__init__.py`
**File:** `/Users/danzigmond/taisho-canon/digest_detector/__init__.py`
**Description:** The package `__init__.py` has a docstring but no `__all__` export list. This means `from digest_detector import *` would import nothing useful. While star imports are generally discouraged, defining `__all__` documents the public API.
**Suggested fix:** Optionally add an `__all__` list or leave as-is (this is genuinely a nit).

#### N4. `pipeline.py` `main()` imports `argparse` lazily but other imports are top-level
**File:** `/Users/danzigmond/taisho-canon/digest_detector/pipeline.py`, line 137
**Description:** `import argparse` is inside the `main()` function while all other imports are at the module level. This is a minor style inconsistency. The lazy import is defensible (avoids loading argparse unless running from CLI), but the style break is noticeable.
**Suggested fix:** Move `import argparse` to top-level, or add a comment explaining the lazy import.

#### N5. Ground truth in `report.py` is hardcoded
**File:** `/Users/danzigmond/taisho-canon/digest_detector/report.py`, lines 21-32
**Description:** The `GROUND_TRUTH` dict is hardcoded with T250/T251 pairs. As the project grows, ground truth data should move to a configuration file or test fixture. For now this is fine, but it creates a maintenance burden.
**Suggested fix:** Consider moving to a JSON/YAML config file in the future.

#### N6. `_generate_summary` creates a `TextMetadata` dummy object for missing metadata
**File:** `/Users/danzigmond/taisho-canon/digest_detector/report.py`, lines 284-286
**Description:**
```python
d_title = metadata_map.get(s.digest_id, TextMetadata(
    text_id='', title='', author='', extent_juan=0,
    char_count=0, file_count=0)).title
```
This creates a new `TextMetadata` instance on every iteration for the default case. While not a performance concern, it would be cleaner to use a sentinel or `metadata_map.get(s.digest_id)` with a conditional.
**Suggested fix:**
```python
d_meta = metadata_map.get(s.digest_id)
d_title = d_meta.title if d_meta else ''
```

#### N7. `_extract_text_recursive` mutates the `div_stack` list argument
**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py`, lines 159-210
**Description:** The function modifies the `div_stack` list in place (push at line 182, pop at line 210). Since the recursive calls pass the same list object, this correctly tracks nesting. However, mutation of arguments in recursive functions can be fragile -- if any code path returns early between push and pop, the stack will be corrupted. Currently all paths between push (line 182) and pop (line 209) are safe, but a future edit adding an early return would introduce a subtle bug.
**Suggested fix:** Consider using a try/finally around the pop, or passing `div_stack + [div_type]` (immutable copy) instead of mutating. The performance cost is negligible since div nesting depth is at most ~5 levels.

---

## Module-by-Module Summary

### `__init__.py`
Clean docstring, no issues. Could optionally export public API.

### `config.py`
Well-organized with clear section headers. All parameters have meaningful names and inline comments. The weights sum correctly. One nit (N1) about documenting the sum constraint.

### `models.py`
Clean dataclass definitions with appropriate defaults and field factories. The `jing_text` property is elegant. One nit about the `None` type annotation (N2).

### `extract.py`
The most complex module (481 lines). XML parsing is thorough with proper namespace handling. Two pieces of dead code (m1: `seen_files`, m2: `STRIP_PUNCT`). One redundant conditional (m3). One minor fragility concern about div_stack mutation (N7). Multiprocessing with tqdm progress is well-implemented.

### `fingerprint.py`
Concise and correct. Good use of hash-based n-grams for performance. Intentional-use comments for `full_text` are clear. No issues found.

### `candidates.py`
Well-commented with the jing_text/full_text asymmetry explained. The docNumber parsing handles ranges correctly. The candidate generation loop is straightforward. No issues found.

### `align.py`
The algorithmic core. The seed-and-extend approach is well-implemented. The DP chaining is correct but the dedup filter has a minor correctness gap (m5). The fuzzy extension has a minor documentation gap about gap characters (m6). The source_span set-based calculation works but is memory-heavy (m4).

### `score.py`
Classification logic is clear with well-chosen thresholds. The confidence weighting is well-designed. One major issue in `detect_multi_source_digests` with the approximate length calculation (M1). One dead variable in the same function.

### `report.py`
Clean output generation with JSON, Markdown, and validation reports. The alignment visualization is readable. Ground truth is hardcoded but appropriate for the current scope (N5).

### `pipeline.py`
Clean orchestrator that connects all stages. Good logging with timing information. The CLI interface via argparse is well-designed. No issues found.

### `test_extract.py`
33 lines of tests covering decode, normalize, charmap, file extraction, and file grouping. Good real-data tests with skip guards. No issues.

### `test_fingerprint.py`
8 tests covering ngram generation, document frequencies, stopgrams, inverted index, and fingerprinting. Uses a clean `_make_text` helper. No issues.

### `test_align.py`
15 tests covering seed finding, chaining, alignment, and source regions. Uses real CJK text examples. Good edge case coverage (empty, no match, perfect match). No issues.

### `test_known_pairs.py`
23 tests covering integration from extraction through classification. Excellent use of module-scoped fixtures for expensive text extraction. Tests both positive and negative cases. The `test_score_all_with_text_map` test closes the gap from the previous review.

---

## Summary Table

| ID | Severity | File | Line | Description |
|----|----------|------|------|-------------|
| M1 | Major | score.py | 238-243 | `detect_multi_source_digests` uses approx digest length + has dead variable |
| M2 | Major | tests/ | -- | No `test_candidates.py` or `test_score.py`; several code paths untested |
| m1 | Minor | extract.py | 89 | Dead variable `seen_files` |
| m2 | Minor | extract.py | 62-66 | Dead compiled regex `STRIP_PUNCT` (never referenced) |
| m3 | Minor | extract.py | 202-206 | Redundant conditional; both branches do the same thing |
| m4 | Minor | align.py | 339-343 | Source span uses per-position set (memory-heavy for large texts) |
| m5 | Minor | align.py | 200-212 | Seed dedup only checks adjacent elements; may miss non-adjacent containment |
| m6 | Minor | align.py | 125-136 | Fuzzy extension gap handling undocumented; segments include gap chars |
| m7 | Minor | align.py | 57-66 | Seed finding keeps only longest match per position; may miss optimal chains |
| N1 | Nit | config.py | 43 | Add comment that weights must sum to 1.0 |
| N2 | Nit | models.py | 35 | Type annotation should be `TextMetadata \| None = None` |
| N3 | Nit | __init__.py | -- | No `__all__` export list |
| N4 | Nit | pipeline.py | 137 | Lazy `import argparse` style inconsistency |
| N5 | Nit | report.py | 21-32 | Hardcoded ground truth dict |
| N6 | Nit | report.py | 284-286 | Dummy TextMetadata created on every iteration for default |
| N7 | Nit | extract.py | 159-210 | `div_stack` mutation in recursive function; fragile to early returns |

---

## Path to A+

1. Fix M1: use actual digest length in `detect_multi_source_digests` and remove dead `d_meta_len`.
2. Fix M2: add `test_candidates.py` and `test_score.py` with unit tests for classification branches, docnumber parsing, confidence calculation, and multi-source detection.
3. Clean up dead code: m1 (`seen_files`), m2 (`STRIP_PUNCT`).
4. Simplify m3 (redundant conditional).
5. Consider m4 (interval merging for source_span) if performance at full corpus scale matters.
