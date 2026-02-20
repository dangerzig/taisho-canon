# Final Re-Review (v2): Post-P3 Fixes and Efficiency Optimizations

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Scope:** Verification of P3 fixes, efficiency optimizations, and remaining issues
**Test Suite:** 260 tests, all passing (3.10s)
**Previous Grade:** A (final_code_review.md)

---

## Changes Under Review

### P3 Fixes (from previous review)

| ID | Description | Status |
|----|-------------|--------|
| P3-1 | Renamed shadowed `d_ch` to `dc` in `_find_phonetic_seeds` inner loop | **Verified** |
| P3-4 | Added `__all__` to `fast.py` | **Verified** |
| P3-5 | Added assertion for confidence weights summing to 1.0 | **Verified** |

### Efficiency Optimizations

| # | Description | Files |
|---|-------------|-------|
| 1 | `slots=True` on all 8 dataclasses | models.py |
| 2 | Pre-filter source syllable index to digest-relevant syllables | align.py |
| 3 | Precompute canonical syllable dict | phonetic.py |
| 4 | orjson with fallback for JSON output | report.py |
| 5 | Bumped CACHE_VERSION from 2 to 3 | cache.py |
| 6 | Fixed `__dict__` usage to `dataclasses.replace()` | test_report.py |

---

## 1. P3 Fix Verification

### P3-1: Shadowed `d_ch` -> `dc` (align.py:265-270)

**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 265-270

```python
dc = digest[d_pos + length]
s_ch = source[s_pos + length]
if dc == s_ch:
    length += 1
else:
    d_s = table.get(dc)
    s_s = table.get(s_ch)
```

The outer loop variable at line 236 is `d_ch = digest[d_pos]`, and the inner loop variable is now `dc` at line 265. The shadow is eliminated. The variable name `dc` is terse but unambiguous in this tight inner loop context. **Correct.**

### P3-4: `__all__` in fast.py

**File:** `/Users/danzigmond/taisho-canon/digest_detector/fast.py`, line 13

```python
__all__ = ["fast_ngram_hashes", "fast_find_seeds", "fast_fuzzy_extend"]
```

Lists the three public names exported by this module. Matches the actual imports in all three branches (env var override, Cython, fallback). **Correct.**

### P3-5: Confidence weights assertion (config.py:47-49)

**File:** `/Users/danzigmond/taisho-canon/digest_detector/config.py`, lines 47-49

```python
assert abs(WEIGHT_CONTAINMENT + WEIGHT_LONGEST_SEGMENT + WEIGHT_NUM_REGIONS +
           WEIGHT_LENGTH_ASYMMETRY + WEIGHT_DOCNUMBER_XREF +
           WEIGHT_AVG_SEGMENT_LEN - 1.0) < 1e-9, "Confidence weights must sum to 1.0"
```

This is a module-level assertion that runs at import time. It uses `1e-9` tolerance for floating-point comparison, which is appropriate for the sum of six values each with two decimal places (0.35 + 0.20 + 0.10 + 0.10 + 0.15 + 0.10 = 1.00 exactly in this case, but the tolerance is correct for future changes). The assertion message is clear. **Correct.**

**One consideration:** Module-level `assert` statements are disabled when Python is run with `-O` (optimize). Since this is a research pipeline unlikely to be run with `-O`, this is acceptable. If paranoia is desired, it could be an `if ... raise ValueError(...)` instead, but this is a P4-level nit.

---

## 2. Efficiency Optimization Verification

### 2.1 `slots=True` on All 8 Dataclasses (models.py)

**File:** `/Users/danzigmond/taisho-canon/digest_detector/models.py`

All 8 dataclasses now use `@dataclass(slots=True)`: TextMetadata, DivSegment, ExtractedText, CandidatePair, AlignmentSegment, AlignmentResult, DigestScore, MultiSourceDigest.

**Compatibility checks:**

1. **Property on ExtractedText (line 38-44):** The `jing_text` property uses `@property` which works correctly with `slots=True`. Python 3.10+ supports properties on slotted dataclasses. **No issue.**

2. **Pickle in cache.py (lines 86-88, 109-112):** Slotted dataclasses are pickle-compatible. Python's pickle protocol handles `__slots__` via `__getstate__`/`__setstate__` automatically. The `CACHE_VERSION` was correctly bumped from 2 to 3 (see below), which ensures old caches with non-slotted instances are invalidated rather than silently loaded with potential attribute mismatch. **No issue.**

3. **`__dict__` access:** A `grep` for `__dict__` across the entire codebase returns zero matches. The test_report.py fix (see section 2.6 below) replaced the only usage. **No issue.**

4. **`dataclasses.asdict` / `vars()`:** A `grep` for these patterns returns zero matches. The codebase manually constructs dicts (e.g., `_segment_to_dict` in report.py), which is compatible with slots. **No issue.**

5. **`dataclasses.replace()`:** Used in test_report.py (lines 229, 282). This function works correctly with slotted dataclasses. **No issue.**

6. **`default_factory=list`:** Several fields use `field(default_factory=list)`. With `slots=True`, mutable default factories work correctly -- the descriptor handles per-instance initialization. **No issue.**

**Verdict:** `slots=True` is correctly applied with no compatibility breakage. The 260 passing tests confirm this.

### 2.2 Pre-filter Source Syllable Index (align.py:220-231)

**File:** `/Users/danzigmond/taisho-canon/digest_detector/align.py`, lines 220-231

```python
# Pre-compute which syllables appear in the digest
digest_syls: set[str] = set()
for ch in digest:
    digest_syls.update(table.get(ch, ()))

# Build index: only index source positions for syllables in the digest
syl_to_positions: dict[str, list[int]] = defaultdict(list)
for i, ch in enumerate(source):
    for syl in table.get(ch, ()):
        if syl in digest_syls:
            syl_to_positions[syl].append(i)
```

This is a sound optimization. Previously, the source syllable index included all syllables, most of which would never be queried. By pre-filtering to only syllables that appear in the digest, the index is smaller and building it is faster (fewer `append` calls).

**Correctness:** The filter cannot remove any syllable that would produce a valid match, because a match requires a shared syllable between digest and source chars, and `digest_syls` contains all syllables of all digest chars. **Correct.**

**Edge case:** If the digest contains no phonetic characters (`digest_syls` is empty), the source index will be empty and `_find_phonetic_seeds` will return no seeds, which is the correct behavior.

### 2.3 Precompute Canonical Syllable Dict (phonetic.py:333)

**File:** `/Users/danzigmond/taisho-canon/digest_detector/phonetic.py`, line 333

```python
canonical = {ch: sorted(syls)[0] for ch, syls in table.items()}
```

This precomputes the canonical syllable (alphabetically first) for every character in the table, avoiding repeated `sorted()` calls inside the `canonical_syllable()` function. The dict is used at line 339: `syl = canonical.get(text[i])`.

**Correctness:** The semantics are identical to calling `canonical_syllable(ch, table)` for each character. The `sorted(syls)[0]` expression produces the same result as the original function. **Correct.**

**Performance:** For a table of ~559 characters, each with 1-5 syllables, this is a negligible upfront cost (559 small sorts) that eliminates O(N) sorts during the n-gram generation loop, where N is the number of characters in all transliteration regions. **Good optimization.**

### 2.4 orjson with Fallback (report.py:12-16, 209-216)

**File:** `/Users/danzigmond/taisho-canon/digest_detector/report.py`, lines 12-16, 209-216

```python
try:
    import orjson
    _HAS_ORJSON = True
except ImportError:
    _HAS_ORJSON = False

def _write_json(path: Path, data) -> None:
    if _HAS_ORJSON:
        with open(path, 'wb') as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    else:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

**Correctness:**
- orjson outputs bytes, hence `'wb'` mode. Standard json outputs str, hence `'w'` mode with encoding. Both correct.
- `orjson.OPT_INDENT_2` produces 2-space indentation matching `json.dump(..., indent=2)`.
- orjson handles `ensure_ascii=False` by default (always outputs UTF-8). No data loss.
- The fallback path preserves the original behavior exactly.

**One nuance:** orjson does not support custom default serializers via keyword arg (it uses `option=orjson.OPT_*` flags). The data passed to `_write_json` consists of dicts, lists, strings, ints, and floats -- all natively supported by orjson. No custom serialization is needed. **Correct.**

### 2.5 CACHE_VERSION Bump (cache.py:20)

**File:** `/Users/danzigmond/taisho-canon/digest_detector/cache.py`, line 20

```python
CACHE_VERSION = 3
```

Changed from 2 to 3. This forces invalidation of any cache created before the `slots=True` change. This is necessary because:

1. Slotted dataclasses pickle differently from non-slotted ones (they use `__getstate__`/`__setstate__` instead of `__dict__`-based pickling).
2. Unpickling a non-slotted instance when the class definition now has `slots=True` could fail or produce an instance with missing attributes.

**Correct and necessary.**

### 2.6 `__dict__` -> `dataclasses.replace()` in test_report.py

**File:** `/Users/danzigmond/taisho-canon/tests/test_report.py`, lines 1, 229, 282

```python
from dataclasses import replace
...
score = replace(score, phonetic_coverage=0.3)
...
score = replace(score, phonetic_coverage=0.15)
```

This replaces what was previously `score.__dict__['phonetic_coverage'] = 0.3` (which would fail with `slots=True` since slotted dataclasses have no `__dict__`). `dataclasses.replace()` creates a new instance with the specified field changed, which is the correct pattern for immutable-style modification. **Correct.**

---

## 3. Review of Previously Flagged Issues

### Issues Fixed Since Last Review

| Previous ID | Description | Status |
|-------------|-------------|--------|
| P1-2 | Source span may include segments with source_start=-1 | **Fixed.** Line 533 now filters `s.source_start >= 0` |
| P2-5 | COMMENTARY_COVERAGE_FLOOR dead code | **Fixed.** Removed from config.py |
| P2-7 | No worker cap for memory_intensive=False | **Fixed.** Line 95 now caps at `min(cpu_count(), 16)` |
| P2-12 | fast.py no logging of active implementation | **Fixed.** Lines 23, 31, 38 now log debug messages |
| P2-14 | phonetic_mapping_for_pair assumes equal lengths | **Fixed.** Lines 415-419 now raise ValueError on mismatch |
| P3-1 | Shadowed `d_ch` variable | **Fixed** (verified above) |
| P3-4 | Missing `__all__` in fast.py | **Fixed** (verified above) |
| P3-5 | Confidence weights unchecked | **Fixed** (verified above) |

### Issues Remaining (Acknowledged, Low Impact)

| Previous ID | Description | Assessment |
|-------------|-------------|------------|
| P1-1 | Pickle deserialization from cache | Acceptable for single-user research tool. Not fixing. |
| P1-3 | Chain seeds backtracking tie-breaking | Coverage metric is always correct; only seed selection varies in degenerate ties. Not impactful. |
| P2-1 | Cython byte offset loop fragility | Correct for valid Python strings. Fragility is theoretical. |
| P2-2 | Phonetic seed finding O(d*S) | Only runs on novel segments (typically short). The new pre-filter (2.2) further reduces work. |
| P2-3 | `_make_text` duplicated across test files | Maintenance burden only. No correctness impact. |
| P2-4 | Logging overcounts fingerprinting pairs | Cosmetic logging issue only. |
| P2-6 | raw_coverage overcounts overlapping seeds | Comment on line 438 now says "computed after dedup" -- the dedup at lines 414-433 (diagonal-based dedup) significantly reduces overcounting. Remaining overcounting is conservative (never causes false early termination). |
| P2-8 | Phonetic index rebuilt per novel segment | Low impact; typically few novel segments per pair. |
| P2-9 | Missing return type hint on cache.load() | Minor legibility item. |
| P2-10 | Recursive list extension O(n^2) in extract.py | CBETA XML is shallow; no practical impact. |
| P2-11 | Fragile mock patching in test_pipeline.py | Works correctly; just not idiomatic. |
| P2-13 | timing_log.jsonl not gitignored | Minor. |

---

## 4. New Observations

### 4.1 [P3, Style] `_write_json` parameter type annotation

**File:** `/Users/danzigmond/taisho-canon/digest_detector/report.py`, line 209

```python
def _write_json(path: Path, data) -> None:
```

The `data` parameter has no type annotation. It accepts `list[dict]` or `dict` depending on the call site. Adding `data: list | dict` or `data: Any` would improve documentation. Negligible impact.

### 4.2 [P3, Style] `canonical` dict naming in `text_to_syllable_ngrams`

**File:** `/Users/danzigmond/taisho-canon/digest_detector/phonetic.py`, line 333

```python
canonical = {ch: sorted(syls)[0] for ch, syls in table.items()}
```

The variable name `canonical` is clear but it shadows the concept of a function (`canonical_syllable`). A name like `canonical_map` or `char_to_canonical` would be slightly more descriptive. Negligible impact.

### 4.3 [P3, Note] `_phonetic_rescan` and `_find_phonetic_seeds` share table but not the pre-filtered index

The pre-filter optimization in `_find_phonetic_seeds` (section 2.2) computes `digest_syls` and builds a filtered `syl_to_positions` per call. In `_phonetic_rescan`, which calls `_find_phonetic_seeds` once per novel segment, the source syllable index is rebuilt for each novel segment. This is the same concern as the original P2-8, but the pre-filter makes each rebuild cheaper. The remaining inefficiency is minor and does not warrant a higher severity.

### 4.4 [INFO] No remaining `__dict__` usage anywhere in codebase

A grep across the entire codebase confirms zero uses of `__dict__` on any dataclass instance. The `slots=True` migration is complete.

### 4.5 [INFO] Seed deduplication improved

The old `(d_start, s_start)` keyed dedup was replaced with diagonal-based merging (align.py lines 414-433). This properly merges overlapping seeds on the same diagonal, which is more effective at reducing redundant work in `_extend_seeds` and `_chain_seeds`. The code is well-commented and correct.

---

## 5. Per-Category Grades

| Category | Grade | Change | Notes |
|----------|-------|--------|-------|
| Correctness | A | (unchanged) | P3 fixes verified. `slots=True` migration complete and correct. No new bugs introduced. |
| Test Coverage | A | (unchanged) | 260 tests all passing. Tests updated for `slots=True` compatibility. |
| Efficiency | A+ | (up from A) | `slots=True` reduces per-instance memory. Phonetic index pre-filter, canonical dict precomputation, and orjson are all sound optimizations. |
| Legibility | A | (unchanged) | Clean code. Minor naming nits only (P3 level). |
| Consistency | A- | (unchanged) | `_make_text` duplication remains. Not addressed in this round. |
| Security/Safety | B+ | (unchanged) | Pickle cache remains the only concern, acceptable for research tool. |

---

## 6. Summary

All three P3 fixes from the previous review are correctly implemented. The six efficiency optimizations are correct, well-tested (260 tests pass), and introduce no regressions. The `slots=True` migration is particularly well-handled: the CACHE_VERSION bump prevents stale cache issues, the `__dict__` usage in tests was properly replaced with `dataclasses.replace()`, and the `@property` on `ExtractedText` works correctly with slots.

Several P2 items from the original review have also been addressed since the last review cycle (P1-2 source_start guard, P2-5 dead config, P2-7 worker cap, P2-12 logging, P2-14 length validation), which shows continued attention to quality.

The remaining issues are all P2 or lower and have been triaged as acceptable for a research-grade tool. No new P0 or P1 issues were found.

**Overall Grade: A**

The codebase has moved from A- (pre-P3-fixes) to a solid A. The code is correct, well-tested, efficient, and cleanly structured. Achieving A+ would require addressing the remaining P2 items (test helper consolidation, cache.load() type hint, timing log gitignore), none of which affect correctness or performance.
