# Code Review: Core Modules (models, config, cache, pipeline, __init__)

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Files reviewed:**
- `digest_detector/models.py`
- `digest_detector/config.py`
- `digest_detector/cache.py`
- `digest_detector/pipeline.py`
- `digest_detector/__init__.py`

**Overall assessment:** Solid, well-structured code with clear separation of concerns. The pipeline orchestration is thoughtful about memory management and the cache design is sound. A handful of correctness issues worth addressing, mostly around cache invalidation completeness and an edge case in the scoring model.

---

## P1 — Critical

### 1. Confidence weights do not sum to 1.0 (config.py:39-45)

```python
WEIGHT_CONTAINMENT = 0.35
WEIGHT_LONGEST_SEGMENT = 0.20
WEIGHT_NUM_REGIONS = 0.10
WEIGHT_LENGTH_ASYMMETRY = 0.10
WEIGHT_DOCNUMBER_XREF = 0.15
WEIGHT_AVG_SEGMENT_LEN = 0.10
```

Sum = 0.35 + 0.20 + 0.10 + 0.10 + 0.15 + 0.10 = **1.00**. Actually, this is correct. *(Self-correction: verified with calculator, no issue here.)*

### 1. (Revised) Cache config snapshot misses parameters that affect Stage 3+ behavior but are cached indirectly through candidates (cache.py:23-42)

The `_config_snapshot()` correctly captures all Stage 1-2b parameters. However, it does **not** capture `PHONETIC_SEED_LENGTH` or `PHONETIC_MAX_SYLLABLES`, which are used when building the phonetic equivalence table (`phonetic.py:189`). The table itself is rebuilt from scratch (not cached), so this is actually fine for cache correctness — the cache only stores texts and candidates, not the table.

**Downgrade: No P1 issues found.** The code is clean at the critical level.

---

## P2 — Important

### 2. `metadata` on `ExtractedText` can be `None`, but pipeline builds `metadata_map` without guarding (pipeline.py:112, 128; models.py:35)

```python
# models.py:35
metadata: TextMetadata | None = None

# pipeline.py:112 (cache path) and :128 (fresh path)
metadata_map = {t.text_id: t.metadata for t in texts}
```

If any `ExtractedText` has `metadata=None`, `metadata_map` will contain `None` values. Downstream in `score_all()` (score.py:186-189), there is a guard:

```python
d_meta = metadata_map.get(alignment.digest_id)
if not d_meta or not s_meta:
    continue
```

So this is **safe** at runtime — the `None` values are filtered. But the `save_results()` function in `extract.py:493` does `m = text.metadata` and then accesses `m.text_id`, which **will** crash with `AttributeError` if metadata is `None`.

**Impact:** If a text somehow has `None` metadata, `save_results()` crashes. Low probability given the extraction code always sets it, but the type annotation says `None` is valid.

**Recommendation:** Either remove `| None` from the type annotation (if metadata is always set) or add a guard in `save_results()`.

### 3. Cache invalidation misses scoring/classification config params (cache.py:23-42)

The cache stores only Stage 1-2b outputs (texts + candidates), so the snapshot correctly focuses on those parameters. However, consider this scenario:

- Run pipeline with `EXCERPT_THRESHOLD = 0.80` → results cached.
- Change `EXCERPT_THRESHOLD` to `0.70`.
- Re-run: cache is still valid (snapshot doesn't include scoring params), so Stages 1-2 are skipped. Stages 3-5 run fresh with the new threshold. **This is correct behavior** — scoring params don't affect cached data.

**Verdict: This is actually fine.** The cache boundary is well-designed. *(Self-correction.)*

### 4. `align_candidates` receives raw `config.ALIGN_NUM_WORKERS` which bypasses the pipeline's resolved `num_workers` (pipeline.py:205-206)

```python
# pipeline.py:96 — resolves for memory-intensive stages
num_workers = config.resolve_worker_count(num_workers)

# pipeline.py:205-206 — passes ALIGN_NUM_WORKERS directly
alignments = align_candidates(candidates, text_map,
                               num_workers=config.ALIGN_NUM_WORKERS)
```

When `ALIGN_NUM_WORKERS = None` (the default), `align_candidates` calls `resolve_worker_count(None, memory_intensive=False)`, which returns `min(cpu_count(), 16)`. This is intentional per the comment on config.py:70.

However, the CLI `--workers` flag is **ignored for alignment**. A user who passes `--workers 2` expecting to limit all parallelism will find alignment still uses `cpu_count()` workers.

**Impact:** Unexpected behavior for CLI users trying to limit resource usage.

**Recommendation:** Pass `num_workers` from the CLI through to alignment as well, or add a separate `--align-workers` flag, or at minimum document that `--workers` only affects Stages 1-2.

### 5. Pickle deserialization without integrity check (cache.py:109-112)

```python
with open(self.texts_path, "rb") as f:
    texts = pickle.load(f)
```

The manifest validates corpus hash and config snapshot, but the pickle files themselves have no checksum. If `texts.pkl` or `candidates.pkl` are corrupted (partial write, disk error), `pickle.load` could silently return bad data or raise an opaque `UnpicklingError`.

**Impact:** Corrupted cache could cause silent data issues or confusing crashes.

**Recommendation:** Store SHA256 of the pickle files in the manifest and verify before loading. Alternatively, wrap `pickle.load` in try/except and invalidate cache on failure.

### 6. Non-atomic cache save can leave inconsistent state (cache.py:82-101)

```python
def save(self, texts, candidates, xml_dir: Path):
    self.cache_dir.mkdir(parents=True, exist_ok=True)
    with open(self.texts_path, "wb") as f:
        pickle.dump(texts, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(self.candidates_path, "wb") as f:
        pickle.dump(candidates, f, protocol=pickle.HIGHEST_PROTOCOL)
    # ... then writes manifest
```

If the process is killed after writing `texts.pkl` but before writing the manifest, the next run will find no valid manifest and recompute. That's safe. But if the process is killed after writing `texts.pkl` and the manifest but before writing `candidates.pkl`, we have an inconsistent cache with a valid-looking manifest.

Wait — the manifest is written **last** (line 98), after both pickles. So interruption between the two pickles leaves no manifest, which is safe. The only dangerous case is if `candidates.pkl` is partially written, then the manifest is written (impossible since manifest comes after). **Actually this ordering is correct — manifest is written last.**

The remaining risk: the manifest from a *previous* valid run could match if nothing changed. In that case the old manifest matches, and the new `texts.pkl` is complete but `candidates.pkl` is only half-written. On next load, `pickle.load(candidates.pkl)` would fail.

**Impact:** Low — requires process kill at exactly the wrong moment during a re-run where config/corpus hasn't changed. But worth noting.

**Recommendation:** Write manifest last (already done) and consider writing to temp files + atomic rename.

---

## P3 — Minor

### 7. `_log_peak_rss` returns `int(rss_mb)` but return value is never used (pipeline.py:31-42)

```python
def _log_peak_rss(stage_name: str) -> int:
    ...
    return int(rss_mb)
```

Called as `_log_peak_rss("Stage 1")` (line 138) — return value discarded every time.

**Recommendation:** Either use the return value (e.g., include in timing records) or change return type to `None`. Including peak RSS in the timing log would actually be a useful addition.

### 8. `_git_short_hash()` swallows all exceptions (pipeline.py:46-53)

```python
try:
    return subprocess.check_output(...)
except Exception:
    return ""
```

Catching bare `Exception` is overly broad. This could mask unexpected issues like `PermissionError` or `MemoryError`.

**Recommendation:** Catch `(subprocess.CalledProcessError, FileNotFoundError, OSError)` specifically.

### 9. `resource` module is Linux/macOS only (pipeline.py:7)

```python
import resource
```

This import will fail on Windows. While the project likely only runs on macOS/Linux, the import is unconditional at module level.

**Impact:** Pipeline cannot even be imported on Windows.

**Recommendation:** If Windows support is not a goal, add a comment. Otherwise, guard the import and `_log_peak_rss` with a platform check.

### 10. `DivSegment.start`/`end` offsets not validated against `full_text` (models.py:21-26)

The `DivSegment` stores `start` and `end` char offsets, but there is no validation that these are consistent with the parent `ExtractedText.full_text`. A `__post_init__` check like `assert end >= start >= 0` would catch construction bugs early.

**Impact:** Low — extraction code is presumably correct, but defensive validation prevents silent corruption.

### 11. `MultiSourceDigest.combined_coverage` uses `char_count` instead of `jing_text` length (score.py:256-258, 272)

```python
# score.py:257-258
d_meta = metadata_map.get(digest_id)
d_len = d_meta.char_count if d_meta else 0
...
combined_coverage = merged_len / d_len
```

Elsewhere, the code carefully distinguishes between `char_count` (full text including prefaces) and `jing_text` length. Here, `detect_multi_source_digests` uses `char_count` for the denominator, which could undercount combined coverage for texts with large prefaces.

**Impact:** Multi-source digest detection could miss cases where combined coverage is actually higher when measured against jing-only text.

**Recommendation:** Use `jing_text` length when available, consistent with `classify_relationship`.

### 12. `_print_timing_history` has hardcoded column width (pipeline.py:308)

```python
print("-" * 110)
```

This doesn't adjust if column headers change. Minor cosmetic issue.

---

## P4 — Style/Nit

### 13. Inconsistent `Path` default parameter style (pipeline.py:74-76)

```python
def run_pipeline(
    xml_dir: Path = None,  # should be Path | None = None
    results_dir: Path = None,
```

The type annotation `Path = None` is technically incorrect — the parameter accepts `None` as a value, so the annotation should be `Path | None = None`.

### 14. `__all__` in `__init__.py` lists module names as strings but doesn't import them (\_\_init\_\_.py:8-20)

```python
__all__ = [
    "config",
    "extract",
    ...
]
```

This `__all__` is conventional for packages (controls `from digest_detector import *`), but since none of these modules are actually imported at the package level, `from digest_detector import config` works via Python's implicit submodule import, not because of `__all__`. The `__all__` only affects star imports. This is fine but could confuse someone expecting `__all__` to mean "these are imported."

### 15. Missing `__repr__`/`__str__` on dataclasses (models.py)

The dataclasses use `@dataclass` which auto-generates `__repr__`, but for large text fields (e.g., `ExtractedText.full_text` with 285K chars), the default `repr` would be enormous. Consider adding `repr=False` to `full_text` or implementing a custom `__repr__`.

### 16. Comment says "~8,982 frozensets" (pipeline.py:152)

```python
del ngram_sets, stopgrams  # ~8,982 frozensets, only needed for candidates
```

This hardcoded count in a comment will become stale if the corpus changes. Consider removing the specific number.

### 17. `CACHE_VERSION` lacks documentation about what changed (cache.py:20)

```python
CACHE_VERSION = 2
```

No changelog for what changed from version 1 to 2. A brief comment would help future maintainers know when to bump.

---

## Summary

| Severity | Count | Key Issues |
|----------|-------|-----------|
| P1       | 0     | None found |
| P2       | 3     | CLI `--workers` ignored for alignment; pickle integrity; `metadata` None edge case |
| P3       | 6     | Multi-source uses char_count vs jing_text; unused return value; broad exception catch; Windows compat; no offset validation; hardcoded width |
| P4       | 5     | Type annotations; `__all__` semantics; repr for large fields; stale comment; cache version docs |

The architecture is clean and well-thought-out. The cache boundary (Stage 1-2b outputs) is the right abstraction, the memory management with explicit `del` + `gc.collect()` is appropriate, and the pipeline stage ordering is correct. The most actionable items are #4 (alignment workers ignoring --workers), #5 (pickle integrity), and #11 (jing_text consistency in multi-source detection).
