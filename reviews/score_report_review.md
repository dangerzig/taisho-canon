# Code Review: score.py and report.py

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Files:** `digest_detector/score.py` (285 lines), `digest_detector/report.py` (399 lines)
**Test coverage:** `tests/test_score.py` (389 lines), `tests/test_known_pairs.py` (422 lines)

---

## Executive Summary

Both files are well-structured and the classification logic is sound for the domain. The test coverage for `score.py` is solid. However, there are several issues worth addressing, including a **classification gap** where certain coverage ranges silently fall through to "commentary" without meeting the documented precondition, a **redundant field** in DigestScore, and missing test coverage for `report.py`.

**Counts:** 2 P2, 5 P3, 4 P4

---

## P2: Important Issues

### P2-1: Classification gap -- commentary has no lower-bound coverage check (score.py:83-96)

The docstring at lines 47-53 states:
> commentary: coverage >= 0.20, avg segment < 10 chars

But the actual code at lines 83-96 has no explicit lower-bound check for commentary:

```python
if coverage < config.SHARED_TRADITION_THRESHOLD:      # < 0.10
    classification = "no_relationship"
elif coverage < config.DIGEST_THRESHOLD:               # 0.10 <= cov < 0.30
    classification = "shared_tradition"
elif size_ratio < config.RETRANSLATION_SIZE_RATIO:     # cov >= 0.30, small ratio
    classification = "retranslation"
elif coverage >= config.EXCERPT_THRESHOLD and avg_seg_len >= config.EXCERPT_AVG_SEG_LEN:
    classification = "excerpt"                         # cov >= 0.80, avg >= 15
elif avg_seg_len >= config.COMMENTARY_AVG_SEG_LEN:
    classification = "digest"                          # cov >= 0.30, avg >= 10
else:
    classification = "commentary"                      # cov >= 0.30, avg < 10
```

The actual reachable conditions for "commentary" are: **coverage >= 0.30 AND size_ratio >= 3.0 AND avg_seg_len < 10**. This is narrower than the documented `coverage >= 0.20`. Any pair with `0.20 <= coverage < 0.30` is classified as "shared_tradition", not "commentary". The docstring is misleading.

Additionally, the `COMMENTARY_AVG_SEG_LEN` constant name is confusing: it is used as the *floor* for "digest", not the *ceiling* for "commentary". A name like `DIGEST_MIN_AVG_SEG_LEN` would be clearer.

**Impact:** The docstring discrepancy could mislead anyone reasoning about classification boundaries. In the MEMORY.md, the distribution shows 621 commentaries, so this code path is actively used -- but only for coverage >= 0.30 cases, not the documented >= 0.20.

### P2-2: `containment` and `coverage` are always identical in DigestScore (score.py:114-115)

```python
return DigestScore(
    ...
    containment=coverage,
    coverage=coverage,
    ...
)
```

Both `containment` and `coverage` are set to the same phonetic-adjusted `coverage` value. The `DigestScore` dataclass has both fields (models.py:92-93), but they are never differentiated. This is confusing because:

1. Upstream, `AlignmentResult` has a single `coverage` field.
2. The original alignment coverage (before phonetic adjustment) is lost -- it is not stored anywhere in the DigestScore.
3. Tests never assert that `containment != coverage` for any case.
4. The `containment` field in the JSON output (report.py line 229, `'coverage': round(s.coverage, 4)`) does not even serialize `containment`.

**Impact:** The `containment` field is dead weight that suggests a distinction that does not exist. If the original pre-phonetic-adjustment coverage was intended to be stored as `containment`, that is a bug. If they are truly the same, the redundant field should be removed to avoid confusion.

---

## P3: Minor Issues

### P3-1: Multi-source digest uses metadata char_count, not jing_length (score.py:257-258)

```python
d_meta = metadata_map.get(digest_id)
d_len = d_meta.char_count if d_meta else 0
```

In `detect_multi_source_digests`, the combined coverage calculation uses `d_meta.char_count` (the full text length including prefaces). But `classify_relationship` and `score_all` carefully use `jing_length` when available (lines 79-81, 196-197). This inconsistency means that for texts like T251 (which has substantial xu prefaces), the combined coverage in multi-source detection would be computed against the full text length rather than the jing length, making it systematically lower.

**Impact:** Multi-source digest detection would undercount coverage for texts with significant preface material. In practice, this may not trigger often if most multi-source digests lack xu sections, but it is an inconsistency with the jing-aware design used elsewhere.

### P3-2: validate_ground_truth does not receive text_map (report.py:35-43)

```python
def validate_ground_truth(
    scores: list[DigestScore],
    alignments: list[AlignmentResult],
    metadata_map: dict[str, TextMetadata],
) -> dict:
```

The function validates against `score.coverage` which, after the phonetic adjustment in `classify_relationship`, may differ from `alignment.coverage`. However, the function also receives `alignments` (line 37) but never uses them. The `alignments` parameter is dead code in this function.

The `alignments` parameter may have been intended for future use (e.g., validating alignment structure), but currently it is unused and slightly misleading.

**Impact:** Minor. The unused parameter adds confusion but does not affect correctness since the scores already contain the coverage values needed for validation.

### P3-3: No test coverage for report.py functions

There is no `tests/test_report.py`. The functions `validate_ground_truth`, `generate_reports`, `_generate_summary`, `_generate_validation_report`, and `_format_alignment_visualization` are all untested in isolation. They are only exercised indirectly through the pipeline integration tests (which mock most stages).

Key untested scenarios:
- `validate_ground_truth` when a ground-truth pair is scored as `no_relationship` (filtered out by `score_all`)
- `generate_reports` with empty `scores` or `alignments` lists
- `_format_alignment_visualization` with phonetic segments
- `_generate_validation_report` with mixed pass/fail results
- File I/O error handling (none exists)

**Impact:** Report generation bugs would only surface during full pipeline runs, making them harder to diagnose.

### P3-4: _compute_confidence region normalization has a surprising mapping (score.py:143-144)

```python
c_regions = min((num_regions - 1) / 4.0, 1.0) if num_regions > 0 else 0.0
```

When `num_regions == 1`, `c_regions = 0.0`. This means a digest that draws from exactly 1 contiguous region of the source gets zero credit for the "regions" component. The comment says "1 region -> 0.2" but the code gives 0.0 for 1 region and 0.25 for 2 regions. This is arguably intentional (a single region is less interesting), but the comment is wrong.

**Impact:** The comment/code mismatch could confuse future maintainers. The actual behavior (1 region = 0.0) is arguably reasonable, but the comment at line 143 claims "1 region -> 0.2" which is incorrect.

### P3-5: Ground truth only covers 2+2=4 test cases (report.py:21-32, 107-124)

The `GROUND_TRUTH` dict contains only 2 positive pairs (T250->T223, T251->T223) and 2 negative pairs (T250<->T251). For a corpus of ~8,982 texts producing hundreds of classifications, this is a very thin validation layer.

**Impact:** Low confidence that pipeline-wide regressions would be caught. Consider adding more known relationships (e.g., from cross-reference concordance data) to improve validation breadth. This is more of a testing strategy concern than a code bug.

---

## P4: Style / Nits

### P4-1: Inconsistent use of `round()` for float formatting (report.py:229-234, 253-256)

In `generate_reports`, some fields are rounded (`coverage`, `novel_fraction`, `source_span`) while `confidence` is not. In `_generate_summary`, `coverage` uses `:.1%` formatting and `confidence` uses `:.3f`. The inconsistency is minor but could lead to precision differences between the JSON and Markdown outputs.

### P4-2: Magic number 1.1 in multi-source detection (score.py:276)

```python
if combined_coverage > best_single.coverage * 1.1:  # 10% improvement
```

The 10% improvement threshold is hardcoded rather than defined as a config constant. While the comment explains the intent, other thresholds in this codebase are defined in `config.py`.

### P4-3: `_format_alignment_visualization` column widths assume short text IDs (report.py:151, 158-161, 168-170)

The fixed-width formatting (`{d_range:<10}`, `{d_preview:<34}`) works for standard Taisho IDs like "T08n0250" but would break alignment if IDs or CJK previews are longer than expected. CJK characters are typically double-width in terminals, so the `{d_preview:<34}` alignment will be visually misaligned for CJK text.

### P4-4: Docstring for classify_relationship is missing the "retranslation" lower bound (score.py:47-53)

The docstring says "retranslation: coverage >= 0.30, size ratio < 3.0" but does not mention that retranslation is checked *before* excerpt/digest/commentary. The priority ordering is the key design decision and should be explicitly documented.

---

## Positive Observations

1. **Phonetic coverage discounting** (score.py:56-74) is well-designed. Phonetic matches are inherently lower confidence than exact/fuzzy matches, and the `PHONETIC_COVERAGE_WEIGHT` (0.8) provides a sensible discount.

2. **Jing-aware size ratio** (score.py:79-81) correctly strips preface material for classification. This was a learned fix for T251 and is well-tested in `test_known_pairs.py`.

3. **Multi-source digest detection** (score.py:217-284) uses proper interval merging to compute union coverage, avoiding double-counting overlapping segments. The 10% improvement threshold prevents flagging pairs where the second source adds negligible coverage.

4. **Confidence score decomposition** (score.py:126-166) is transparent and auditable. Each component is independently normalized to [0, 1] and the weights sum to 1.0 (verified by test).

5. **Ground truth negative checks** (report.py:107-124) correctly verify that T250 and T251 are not classified as digests of each other. This is a common pitfall for retranslation pairs and the test catches it.

6. **Score sorting** (score.py:211) ensures deterministic output ordering by confidence, which makes reports stable across runs.

7. **Clean separation of concerns**: `score.py` handles classification logic while `report.py` handles presentation. Neither module reaches into the other's domain.
