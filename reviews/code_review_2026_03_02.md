# Code Review: `scripts/build_expanded_concordance.py`

**Date:** 2026-03-02
**Reviewer:** Claude Opus 4.6
**Script:** `/Users/danzigmond/taisho-canon/scripts/build_expanded_concordance.py` (1,540 lines)
**Scope:** Full script review, with special attention to the verified concordance export

---

## Overall Assessment

This is a well-structured, well-documented research pipeline script that merges 12+ data sources into a unified concordance with per-link provenance tracking. The code is generally clean, with good separation of concerns (merge, classify, output, verify). The ProvenanceTracker class is well-designed, and the classification logic is clear and well-tested.

However, the review identified **one critical bug** (flagged errors leaking into the verified output's classifications and provenance), **several important issues** (dead code, a misleading function name, `_toh_num` edge cases), and a handful of minor code quality items.

**Grade: A-** (would be A+ after addressing the critical and important findings below)

---

## Critical Findings

### C1. Flagged known errors leak into verified output classifications and provenance

**Location:** `classify_links()` (line 1116), `build_verified_output()` (lines 1252-1257, 1292-1304)

**Description:** `flag_known_errors()` correctly removes erroneous Toh IDs (e.g., "Toh 0", "Toh 237", "Toh 3908") from `concordance[text_id]["tibetan"]`, but it does NOT remove them from provenance. When `classify_links()` subsequently iterates over `provenance.all_links()`, it classifies these flagged errors as `"parallel"` / `"catalog-attested"` because the attestations are from catalog sources. Then `build_verified_output()` builds `verified_toh_links` from `link_classifications` where `info["type"] in VERIFIED_TYPES`. Since the flagged errors have type `"parallel"`, they pass through into:

1. `verified_provenance` (link_provenance in the JSON output)
2. `verified_classifications` (link_classifications in the JSON output)

They do NOT appear in `tibetan_parallels` (because the concordance tibetan set was cleaned), but the metadata sections are inconsistent.

**Verified empirically:** "Toh 0" appears in the verified output's `link_classifications` for T09n0278 and T13n0397 with `{"type": "parallel", "basis": "catalog-attested"}`, and in `link_provenance` with `flagged_error: true` attestations.

**Impact:** Downstream consumers of the verified concordance who use `link_classifications` to count parallels or analyze relationships will get inflated counts. The classification summary's `"parallel": 2700` likely includes ~8 erroneous links.

**Suggested fix:** After `flag_known_errors()` returns, either:
- (a) Have `classify_links()` skip links where ALL attestations have `flagged_error: True`, or
- (b) In `build_verified_output()`, exclude `(taisho_id, toh_id)` pairs that appear in `error_summary` from `verified_toh_links`, or
- (c) Add a new field to the classification: `"type": "error:flagged"` and exclude it from `VERIFIED_TYPES`.

Option (c) is the cleanest, as it preserves the classification while keeping it out of the verified output.

---

## Important Findings

### I1. `_toh_num()` returns -1 for unparseable Toh strings, causing wrong Kangyur classification

**Location:** `build_verified_output()`, line 1327-1342

**Description:** The nested function `_toh_num()` returns -1 for Toh strings it cannot parse. The Kangyur filter on line 1340 uses `_toh_num(t) <= 1108`, which means any Toh with an unparseable number (returning -1) would be counted as Kangyur.

Similarly, "Toh 0" (if it survives error flagging) returns 0, which is <= 1108, counting as Kangyur.

**Actual impact (current data):** The verified output contains no Toh entries with `_toh_num` returning -1 or 0, so this is latent rather than active. But it is a fragile design.

**Suggested fix:** Change the Kangyur filter to `1 <= _toh_num(t) <= 1108` and the Tengyur filter to `1109 <= _toh_num(t) <= 4569`. Log a warning for Toh numbers outside both ranges.

### I2. Toh numbers outside the Kangyur/Tengyur ranges (Toh 5639, Toh 5656) silently counted as Tengyur

**Location:** `build_verified_output()`, line 1341-1342

**Description:** The verified output contains two Toh numbers (5639 and 5656) that exceed the expected Tengyur maximum of 4569. These are counted in `tengyur_toh` with no warning. "Toh 5656" appears alongside "Otani 5656" for T04n0192, suggesting it may be a data entry error where an Otani number was recorded as a Tohoku number upstream.

**Impact:** The `pct_tengyur` statistic (currently 3.4%) is slightly inflated, and these out-of-range numbers may indicate data quality issues in upstream sources.

**Suggested fix:** Add a validation pass that warns about Toh numbers > 4569 and excludes them from the Tengyur count (or reports them separately as "unclassified" Toh numbers).

### I3. Dead code: `rkts_texts` set is built but never used

**Location:** `classify_links()`, lines 1094-1098

```python
rkts_texts = set()
for text_id, data in concordance.items():
    sources = data.get("sources", set())
    if "rkts" in sources:
        rkts_texts.add(text_id)
```

**Description:** The `rkts_texts` set is populated but never referenced anywhere after its construction. The actual Chinese-origin detection at lines 1134-1138 uses the per-link source set (`"rkts" in sources`), not this per-text set.

**Suggested fix:** Remove lines 1094-1098.

### I4. Misleading function name: `_is_scholarly_source` returns True for catalog databases

**Location:** `_is_scholarly_source()`, line 1051

**Description:** Despite its name and docstring ("Check if a source name is a scholarly citation"), this function returns True for ALL sources in `CATALOG_SOURCES`, including automated database sources like `"lancaster"`, `"cbeta_tibetan"`, `"existing"`, and `"84000_tei_refs"`. These are catalog databases, not scholarly citations. The function is really checking "is this a trusted/authoritative source (as opposed to a computational or infrastructure source)?"

The variable name at the call site (`has_catalog` on lines 1108 and 1122) is actually more accurate than the function name.

**Impact:** No functional bug, but confusing for anyone reading or maintaining the code.

**Suggested fix:** Rename to `_is_catalog_or_scholarly_source()` or `_is_authoritative_source()` and update the docstring to match.

### I5. `import re as _re` inside a nested loop

**Location:** `print_verified_genre_coverage()`, line 1432

```python
for label, v_start, v_end in genres:
    genre_ids = set()
    for text_id in corpus_ids:
        import re as _re  # <-- imported inside inner loop
        m = _re.match(r'^T(\d{2})n', text_id)
```

**Description:** `re` is already imported at the top of the file (line 57). The `import re as _re` statement inside the inner loop body is unnecessary. While Python caches imports after the first execution so there is no performance penalty, this is a code smell that suggests the function was written or copied without checking top-level imports.

**Suggested fix:** Remove `import re as _re` and use `re.match(...)` directly (as is done everywhere else in the file).

### I6. No test coverage for `build_verified_output()` or `build_output()`

**Location:** `tests/test_link_classification.py` (existing tests)

**Description:** The test file covers `_is_scholarly_source()` and `classify_links()` thoroughly, but there are no tests for `build_verified_output()`, `build_output()`, `flag_known_errors()`, `compare_with_existing()`, or `merge_sources()`. The verified output logic (the newest addition) has zero direct test coverage.

Given that C1 above is a bug in `build_verified_output()`, this gap is significant.

**Suggested fix:** Add unit tests for `build_verified_output()` covering:
- Filtering of computational-only links
- Correct exclusion of flagged errors from verified output
- Correct Kangyur/Tengyur Toh counting
- Schema consistency between expanded and verified outputs
- Edge case: text with only computational Tibetan links but catalog-backed Pali (should still appear in verified output via Pali)

---

## Minor Findings

### M1. `normalize_taisho_id` has mixed return type (str or int)

**Location:** line 133-149

**Description:** The function docstring says "Returns the canonical CBETA format like T08n0250" but for bare-number inputs like "T250", it returns `int(250)`. This mixed-type return is handled by `resolve_taisho_id` with an `isinstance(norm, int)` check, but the docstring is misleading and the design is fragile.

**Suggested fix:** Update the docstring to document the int return case, or refactor so the function always returns a string (returning `None` for bare numbers that need lookup).

### M2. `_make_attestation` always includes `"confidence": null` even for catalog sources

**Location:** line 205-220

**Description:** Every attestation dict includes a `"confidence"` key, even when the value is `None` (which serializes as `null` in JSON). For catalog assertions where confidence is semantically meaningless, this adds noise to the output. A missing key would be more idiomatic than an explicit null.

**Suggested fix:** Only include `"confidence"` when it is not None:
```python
att = {"source": source}
if confidence is not None:
    att["confidence"] = confidence
if note:
    att["note"] = note
return att
```

### M3. Schema inconsistency between expanded and verified outputs

**Location:** `build_output()` (line 821) vs `build_verified_output()` (line 1234)

**Description:** The two outputs have different top-level keys and summary fields:

| Field | Expanded | Verified |
|-------|----------|----------|
| `sources` (top-level) | Present | Missing |
| `verified_only` | Missing | Present |
| `known_errors` | Present | Present |
| `link_classifications` | Present | Present |
| summary: `unique_toh` | Missing | Present |
| summary: `kangyur_toh` | Missing | Present |
| summary: `tengyur_toh` | Missing | Present |
| summary: `pct_kangyur` | Missing | Present |
| summary: `pct_tengyur` | Missing | Present |

The Toh breakdown fields (`unique_toh`, `kangyur_toh`, `tengyur_toh`, `pct_kangyur`, `pct_tengyur`) are useful and arguably should also appear in the expanded output. The `sources` per-text count is missing from the verified output but would be useful there too.

**Suggested fix:** Consider adding the Toh breakdown to the expanded output summary as well, and/or documenting the schema differences explicitly.

### M4. `up*` references (e.g., "up3.050") pass through to expanded output without provenance

**Location:** Source 1 loading (line 315-332)

**Description:** The existing cross_reference.json contains tibetan_parallels entries like "up3.050" (Upadesha references from SuttaCentral). These are loaded into the concordance's "tibetan" set at line 317, but no provenance is recorded for them (line 318 only records provenance for entries starting with "Toh "). They appear in the expanded output's `tibetan_parallels` but are correctly filtered out of the verified output (since they don't start with "Toh " or "Otani ").

**Impact:** Minor; these are a small number of references. But they represent a category of Tibetan reference that is neither Toh nor Otani, and they have no provenance trail.

**Suggested fix:** Either (a) add provenance tracking for `up*` references, or (b) filter them out during loading, or (c) move them to a separate parallel category.

### M5. `ProvenanceTracker.add()` deduplication updates in-place

**Location:** `ProvenanceTracker.add()`, lines 241-251

**Description:** When a duplicate source is found, the existing attestation dict is mutated in place (updating `confidence` and `note`). This is correct but could be surprising if someone holds a reference to the attestation list and doesn't expect it to change. The current codebase doesn't do this, so it's not a bug, just a design note.

### M6. `compare_with_existing` computes `old_any` using `total_texts` from the NEW output

**Location:** line 919-921

```python
old_any = output["summary"]["total_texts"] - len(
    existing.get("no_parallel_found", [])
)
```

**Description:** This computes the old "any parallel" count by subtracting the old no_parallel count from the NEW total_texts. If the corpus size changed between the existing and expanded runs, this calculation would be wrong. Currently the corpus is stable at 2,455 texts, so this is not an active bug, but it's conceptually fragile.

**Suggested fix:** Use the existing output's total_texts if available:
```python
old_total = existing.get("summary", {}).get("total_texts", output["summary"]["total_texts"])
old_any = old_total - len(existing.get("no_parallel_found", []))
```

### M7. No type hints on any function

**Location:** Entire script

**Description:** No function in the script has type annotations. For a 1,540-line script with complex data structures (nested dicts, sets, defaultdicts, mixed-type returns), type hints would significantly improve readability and enable static analysis.

**Suggested fix:** Add type hints to at least the public functions and the ProvenanceTracker class. Example:
```python
def load_json(path: Path) -> dict | None:
def normalize_taisho_id(raw_id: str) -> str | int:
class ProvenanceTracker:
    def add(self, taisho_id: str, toh_id: str, source: str,
            confidence: float | None = None, note: str | None = None) -> None:
```

---

## Suggestions (Non-Issues, Style/Enhancement)

### S1. The docstring lists 12 sources but the script actually has 13+

**Location:** Module docstring, lines 1-54

**Description:** The docstring says "12 sources" and lists specific input files, but the script also loads:
- `results/84000_taisho_refs.json` (Source 8b)
- `data/known_errors.json` (post-processing)
- `results/peking_only_texts.json` (post-processing)
- `results/tohoku_otani_concordance.json` (post-processing)

These should be listed in the docstring for completeness.

### S2. The DILA catalog data (`results/dila_taisho_tibetan.json`) exists but is not integrated

**Location:** N/A (data file exists at `results/dila_taisho_tibetan.json`)

**Description:** The DILA Authority Database data (1,002 pairs, 600 unique Taisho) exists in the results directory but is not loaded by the concordance script. It appears to be derived from the same Lancaster/Goryeo data that other sources provide, so it may be intentionally excluded as redundant. Worth documenting the decision.

### S3. Consider extracting `_toh_num()` as a module-level function

**Location:** `build_verified_output()`, line 1327

**Description:** `_toh_num()` is defined as a nested function inside `build_verified_output()`, but it is a general utility that could be useful elsewhere (e.g., for validation in `flag_known_errors` or sorting). Extracting it to module level would improve reusability.

### S4. The `MITRA_STRONG_THRESHOLD` and `COMPUTATIONAL_CONFIDENCE_THRESHOLD` are both 0.9

**Location:** Lines 94 and 121

**Description:** These two thresholds happen to have the same value but serve different purposes: one gates whether MITRA links enter the active concordance, the other gates whether computational links get classified as `parallel:computational` vs `uncertain`. They should remain separate constants (as they are), but a comment noting they are intentionally the same value would prevent future confusion.

### S5. Peking-only provenance source attribution

**Location:** Lines 804-806 vs 811-812

**Description:** Peking-only Otani links from `from_lancaster` entries are attributed to source `"lancaster"`, while those from `from_concordance` entries are attributed to `"peking_only"`. This is reasonable (Lancaster originally reported them), but the mixed attribution could be confusing. Consider using `"peking_only"` consistently for all entries from this data file, with a note referencing the original Lancaster source.

---

## Summary of Findings by Severity

| Severity | Count | Items |
|----------|-------|-------|
| Critical | 1 | C1 (flagged errors in verified output) |
| Important | 6 | I1-I6 |
| Minor | 7 | M1-M7 |
| Suggestions | 5 | S1-S5 |

The script is well-engineered for a research pipeline. The critical finding (C1) should be fixed before using the verified concordance for any published statistics or downstream analysis. The important findings (especially I1/I2 on Toh range validation and I6 on test coverage) should be addressed to reach A+ quality.
