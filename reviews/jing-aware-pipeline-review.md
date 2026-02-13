# Code Review: Jing-Aware Alignment and Classification

**Date:** 2026-02-13
**Scope:** Changes to make the pipeline jing-aware (models, candidates, align, score, pipeline, report, tests)
**Goal:** Fix two validation failures: T251→T223 not found; T250→T251 wrongly classified as partial_digest.

---

## Summary

The changes correctly thread `jing_text` through the pipeline so that xu (preface) material does not dilute alignment, candidate generation, or size-ratio classification. The fix required touching 7 files (6 source + 1 test). All 58 tests pass. The approach is sound and the implementation is clean.

**Overall grade: B+** — Correct and well-structured, but has a consistency gap in the fingerprinting layer and a few minor issues that should be addressed to reach A+.

---

## File-by-File Review

### `models.py` — `jing_text` property

```python
@property
def jing_text(self) -> str:
    jing_segs = [seg.text for seg in self.segments if seg.div_type == 'jing']
    if jing_segs:
        return ''.join(jing_segs)
    return self.full_text
```

**Verdict: Good.** Clean, correct, appropriate fallback. Now has 4 unit tests covering the key cases (jing present, no jing, empty segments, non-jing segments).

**No issues.**

---

### `candidates.py:114` — Jing-aware candidate fingerprinting

Changed `digest.full_text` to `digest.jing_text` for the fingerprint content.

**Verdict: Correct, but reveals an asymmetry.**

The inverted index (`fingerprint.py:92`) is built from `text.full_text` for ALL texts. When candidate generation fingerprints a digest using `jing_text`, the n-grams being looked up are a subset of the digest's full-text n-grams, so they will still be found in the index entries of other texts. This works correctly.

However, the **asymmetry is confusing**: the inverted index includes n-grams from xu sections of ALL texts (since it uses `full_text`), but the candidate generation query only uses jing n-grams from the digest side. This means:

- A source text's xu n-grams are indexed but will never cause false matches (the digest query simply won't generate them).
- A digest text's xu n-grams are indexed (for when that text acts as a source for other digests) but skipped when that text is queried as a digest.

This is **semantically correct** but **not immediately obvious**. A comment explaining this asymmetry would help future readers.

**Issue C1 (minor):** Add a comment at `candidates.py:114` explaining why `jing_text` is used for the digest query while the inverted index uses `full_text`, and why this is correct.

**Issue C2 (minor):** There is also a subtle inconsistency at `candidates.py:144`:

```python
if s_len < d_len * min_size_ratio:
    continue
```

Here `d_len = digest.metadata.char_count` (full text length), while the fingerprint uses jing text. For T251, this means the size-ratio filter uses 1090 (full) while containment is computed over ~260 chars (jing). This doesn't cause a bug (the filter is permissive at 2.0x), but conceptually the comparison mixes full and jing measurements. Consider whether `d_len` should also use jing length here, or document why the mismatch is intentional.

---

### `align.py:416` — Use `jing_text` for digest alignment

Changed `d_text.full_text` to `d_text.jing_text`.

**Verdict: Good.** Source side correctly stays as `full_text` (digests can draw from any part of the source). The change is minimal and clear.

**No issues.**

---

### `score.py` — Jing-aware size ratio

Added `digest_jing_length` and `source_jing_length` optional params to `classify_relationship()`, and `text_map` param to `score_all()`.

**Verdict: Correct, with one subtlety to document.**

The jing lengths are used for:
1. The `size_ratio` in the classification logic (retranslation check) — correct.
2. The `size_ratio` passed to `_compute_confidence()` for the `c_asymmetry` component — this is a side effect worth noting.

For T250 vs T251 with jing lengths: `size_ratio = 260/331 = 0.79`, so `c_asymmetry = log2(max(0.79, 1.0))/10 = 0`. The asymmetry signal disappears entirely for this pair, which is correct (they ARE similar-sized texts).

For the general case: using jing lengths for the confidence asymmetry component means the confidence score now reflects the "real" content ratio rather than the metadata ratio. This is the right behavior.

**Issue S1 (minor):** The `digest_length` param passed to `_compute_confidence()` (line 88) still uses the full-text `digest_length`, not the jing length. This is used for normalizing `c_longest` (longest segment / digest length). Since alignment now runs on jing text, the longest segment is relative to jing length, but it's normalized against full-text length. For T251 this makes the longest segment look smaller than it is. Consider using the jing length for this normalization too, or document why full-text length is preferred.

**Issue S2 (nit):** `score_all()` computes `len(d_extracted.jing_text)` on every alignment iteration. For texts without jing segments, `jing_text` returns `full_text`, which is fine, but it does a list comprehension + join on every call. Consider caching the result if performance matters at scale (currently ~6810 iterations, so negligible).

---

### `pipeline.py:95` — Pass `text_map` to `score_all`

One-line change: `score_all(alignments, metadata_map, docnum_pair_set, text_map=text_map)`.

**Verdict: Good.** Clean, minimal.

**No issues.**

---

### `report.py:28-32` — Updated ground truth

Changed T251→T223 from `full_digest`/0.70 to `partial_digest`/0.30.

**Verdict: Correct.** Cross-translator alignment (Xuanzang vs Kumarajiva) gives ~44% coverage, which is squarely in the partial_digest range (0.30-0.70).

**No issues.**

---

### `fingerprint.py` — Unchanged, but worth noting

Both `compute_document_frequencies()` (line 49) and `build_inverted_index()` (line 92) use `text.full_text`. This means:

- Document frequencies count all n-grams including xu sections.
- The inverted index includes xu n-gram positions.

This is fine because:
- Stop-gram identification should be based on the full corpus content.
- The index needs full-text positions so texts can serve as sources (sources should use full text).

**Issue F1 (design question):** Should document frequencies use `jing_text`? An xu-heavy corpus could inflate document frequencies for n-grams that only appear in prefaces. In practice, xu sections are a tiny fraction of the corpus, so this is unlikely to matter. But it's worth a comment noting the design choice.

---

## Test Suite Review

### New tests (7 added, 58 total)

| Test | Coverage |
|------|----------|
| `test_jing_text_returns_jing_only` | Property returns correct jing-only text |
| `test_jing_text_fallback` | Property falls back for text without jing segments |
| `test_jing_text_empty_segments` | Edge case: empty segments list |
| `test_jing_text_no_jing_segments` | Edge case: segments present but none are jing |
| `test_t250_t251_retranslation_with_jing_lengths` | Jing lengths produce correct retranslation classification |
| `test_t251_jing_classified_as_partial_digest` | T251 jing→T223 classifies correctly |
| `test_t251_appears_as_candidate` | T251→T223 appears in candidate generation |

**Verdict: Good coverage of the new code paths.** Each change point has at least one test that would fail if reverted.

### Remaining test gaps

**Issue T1 (medium):** No test for `score_all()` with `text_map` in an end-to-end context. The new tests exercise `classify_relationship()` directly with jing length params, but nothing tests that `score_all()` correctly looks up jing lengths from `text_map` and passes them through. A unit test with a small `text_map` and mock alignments would close this gap.

**Issue T2 (minor):** `test_t250_not_digest_of_t251` (line 233) still calls `classify_relationship()` WITHOUT jing lengths. This test passes because the full-text size ratio (3.3) is just above the threshold (3.0), making it `partial_digest` which != `full_digest`. But if `RETRANSLATION_SIZE_RATIO` were raised to 3.5, this test would still pass while the pipeline (which uses jing lengths) would behave differently. The test should arguably use jing lengths to match the pipeline's behavior, or at minimum there should be a comment noting that the test intentionally uses the old code path.

---

## Dead Code / Cleanup

**Issue D1:** `report.py:10` imports `asdict` from `dataclasses` but never uses it.

**Issue D2:** `tests/test_known_pairs.py:28` imports `defaultdict` inside `_extract_full_text()` but never uses it.

---

## Summary of Issues

### Must fix (for A+ quality)

| ID | File | Issue |
|----|------|-------|
| T1 | tests | Add unit test for `score_all()` with `text_map` param |
| D1 | report.py:10 | Remove unused `asdict` import |
| D2 | tests/test_known_pairs.py:28 | Remove unused `defaultdict` import |

### Should fix (clarity / correctness)

| ID | File | Issue |
|----|------|-------|
| C1 | candidates.py:114 | Add comment explaining jing_text vs full_text index asymmetry |
| S1 | score.py:88 | `_compute_confidence()` normalizes longest segment by full-text length, but alignment runs on jing text; consider using jing length |
| T2 | test_known_pairs.py:233 | `test_t250_not_digest_of_t251` doesn't use jing lengths (matches old behavior, not pipeline) |

### Nice to have (documentation)

| ID | File | Issue |
|----|------|-------|
| C2 | candidates.py:144 | Document mixed full/jing length in size-ratio filter |
| S2 | score.py | `jing_text` property called repeatedly; fine for now, note if perf matters |
| F1 | fingerprint.py | Document that doc frequencies use full_text intentionally |

---

## Verdict

The implementation is correct and the changes are well-scoped. The core insight — that xu (preface) material should be excluded from digest-side operations — is applied consistently across candidate generation, alignment, and scoring. The fallback behavior (returning `full_text` when no jing segments exist) ensures backward compatibility for the ~2400 texts without jing/xu divisions.

To reach A+: fix the three must-fix items (dead imports + one test gap), add the clarifying comments, and consider the `_compute_confidence()` normalization question.
