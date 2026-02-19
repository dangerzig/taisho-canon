# Code Review: Memory Optimization Changes + Full Codebase Quality

**Date:** 2026-02-19
**Reviewer:** Claude
**Scope:** Memory optimization changes (config.py, pipeline.py, fingerprint.py, candidates.py, align.py, extract.py) plus full codebase quality assessment
**Tests:** 205/205 passing

---

## Part 1: Memory Optimization Changes

### 1.1 config.py — `resolve_worker_count()` and constants

**Grade: A**

```python
DEFAULT_MAX_WORKERS = 4
MAXTASKSPERCHILD = 100

def resolve_worker_count(num_workers: int | None = None) -> int:
```

- Clean, well-documented helper function
- Correct precedence: explicit arg > config override > sensible default
- `max(1, ...)` guard prevents 0-worker edge cases
- `MAXTASKSPERCHILD` as a named constant avoids magic numbers scattered across modules

**One nit:** `import cpu_count` at module level adds a dependency that only fires when no explicit worker count is given. This is fine for a config module but worth noting — `cpu_count()` is called at import time if used as a default value in any constant, but here it's deferred to function call time, which is correct.

### 1.2 pipeline.py — Eager memory freeing + RSS logging

**Grade: A-**

Good changes:
- `del doc_freq` after `identify_stopgrams` — correct, this dict can have millions of entries
- `del ngram_sets, stopgrams` after `generate_candidates` — correct, the ~8,982 frozensets are the second-largest data structure
- `gc.collect()` after the `del` — necessary because CPython's reference counting doesn't immediately free cycles, and `gc.collect()` forces a full collection that can return memory to the OS
- `_log_peak_rss()` after each stage — good diagnostic tool

Issues found:

**Issue 1 (Minor): `import sys` inside function body (line 37)**
```python
def _log_peak_rss(stage_name: str) -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    import sys  # <-- should be at module level
    if sys.platform == 'darwin':
```
The `import sys` should be at module level with the other imports. It's a stdlib module that's already loaded — the deferred import buys nothing and looks accidental.

**Issue 2 (Minor): Missing RSS logging after Stage 4 and Stage 5**
Stages 4 and 5 don't log RSS. For completeness and diagnosability, they should — especially Stage 4 which builds `scores` and `multi_source` data structures. (Not critical since Stages 4/5 are cheap, but inconsistent.)

**Issue 3 (Minor): Could free `phonetic_table` after Stage 2b**
In `pipeline.py` line 171, `phonetic_table = build_equivalence_table()` is used only for Stage 2b. After `generate_phonetic_candidates` returns, it could be `del`'d. The table in `align.py` is separately cached via `_get_phonetic_table()`.

**Issue 4 (Observation): `_save_timing` still logs `config.NUM_WORKERS` not resolved count**
Line 63: `"num_workers": config.NUM_WORKERS` will log `None` when using the default. Should log the resolved worker count that was actually used.

### 1.3 fingerprint.py — Pool changes

**Grade: A**

Both `compute_document_frequencies` and `build_ngram_sets` correctly:
- Replaced `config.NUM_WORKERS or cpu_count()` with `config.resolve_worker_count(num_workers)`
- Added `maxtasksperchild=config.MAXTASKSPERCHILD` to Pool
- Removed unused `cpu_count` import

No issues found.

### 1.4 candidates.py — Pool changes

**Grade: A**

Both `generate_candidates` and `generate_phonetic_candidates` correctly updated. The `maxtasksperchild` placement is clean.

**One minor stale docstring** at line 360: `num_workers: Number of parallel workers (None = cpu_count).` should say `(None = min(cpu_count, 4))` for accuracy, though not critical.

### 1.5 align.py — Pool + phonetic table cleanup

**Grade: A**

- Pool correctly updated with `maxtasksperchild`
- `_phonetic_table = None` after alignment is correct — the table was cached at module level and persisted indefinitely
- Properly uses `global _phonetic_table` declaration

### 1.6 extract.py — Pool changes

**Grade: A**

Clean update. No issues.

---

## Part 2: Full Codebase Quality Assessment

### 2.1 models.py

**Grade: A**

Clean dataclass definitions. The `jing_text` property is elegant. Good use of `field(default_factory=...)`.

Minor: `phonetic_mapping: list[tuple[str, str, str]]` — the triple semantics (digest_char, source_char, syllable) are only documented by convention. A NamedTuple or docstring annotation would improve readability, but this is a nit.

### 2.2 score.py

**Grade: A-**

Sophisticated classification logic. The phonetic coverage discount and multi-source detection are well-designed.

**Issue 1 (Edge case): `size_ratio` when both lengths are 0 (line 81)**
If both `d_len` and `s_len` are somehow 0, `size_ratio = max(d_len, s_len) / max(min(d_len, s_len), 1)` = `0 / 1 = 0.0`. This is correct behavior (ratio < RETRANSLATION_SIZE_RATIO), but worth a comment.

**Issue 2: Missing return type hints on some helper functions**
Several helpers like `_classify_relationship` lack explicit return type annotations, though the code is clear enough.

### 2.3 report.py

**Grade: A-**

Comprehensive reporting with ground truth validation.

**Issue 1: Alignment visualization built fully in memory (lines 353-364)**
For the full corpus this creates ~2,800 alignment files. Each file is small, so this isn't a memory concern — but the loop could potentially stream. Not urgent.

**Issue 2: Magic number 10% threshold (line 276)**
Hardcoded `0.10` for "low-coverage" warning should reference `config.SHARED_TRADITION_THRESHOLD` for consistency.

### 2.4 phonetic.py

**Grade: A**

The most complex module. The DDB dictionary parsing and syllable splitting are sophisticated and well-documented.

**Issue 1: Type hints for optional params**
`max_syls: int = None` (line 226) should be `int | None = None` for type checker compliance. Same at line 293.

### 2.5 cache.py

**Grade: A**

Clean caching with CACHE_VERSION, config snapshot, and corpus hash. SHA256 with nanosecond mtime is solid.

**Issue 1: No existence check on xml_dir (line 58)**
`xml_dir.rglob("*.xml")` would raise if directory doesn't exist. Low risk since pipeline validates this earlier, but defensive programming would be to return `None` early.

### 2.6 extract.py

**Grade: A**

Thorough XML parsing with correct namespace handling and charDecl priority.

No issues.

---

## Summary of Findings

### Memory optimization changes: **A**
All changes are correct, consistent, and well-applied. The pattern of `resolve_worker_count()` + `MAXTASKSPERCHILD` is clean and DRY. The `del` + `gc.collect()` placements are at the right points. RSS logging is a welcome diagnostic.

### Issues to fix (ordered by priority)

| # | File | Line | Severity | Issue |
|---|------|------|----------|-------|
| 1 | pipeline.py | 37 | Minor | `import sys` should be at module level |
| 2 | pipeline.py | 63 | Minor | `_save_timing` logs `config.NUM_WORKERS` (None) instead of resolved count |
| 3 | candidates.py | 360 | Trivial | Stale docstring `(None = cpu_count)` |
| 4 | pipeline.py | — | Minor | No RSS logging after Stages 4/5 (inconsistent) |
| 5 | pipeline.py | 171 | Minor | Could `del phonetic_table` after Stage 2b |
| 6 | phonetic.py | 226,293 | Trivial | `int = None` should be `int | None = None` |
| 7 | report.py | 276 | Trivial | Magic 0.10 threshold should reference config |

### Overall codebase grade: **A**

This is high-quality, well-structured research code with clean separation of concerns, comprehensive docstrings, good type hinting, and strong test coverage (205 tests). The memory optimization changes are well-executed and consistent. The issues identified are all minor/trivial — no correctness bugs found.
