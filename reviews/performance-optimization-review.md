# Code Review: Pipeline Performance Optimization

**Date**: 2026-02-19
**Files reviewed**: `config.py`, `fingerprint.py`, `candidates.py`, `cache.py`, `pipeline.py`, `test_fingerprint.py`, `test_candidates.py`, `test_cache.py`, `test_known_pairs.py`, `test_phonetic_candidates.py`
**Focus areas**: Efficiency, parallelism, readability, test coverage

---

## Summary

Three optimizations were applied: (1) replace the 48M-entry inverted index with per-text frozensets + C-level set intersection, (2) add phonetic stopgram filtering to prevent the 94K false-positive explosion, (3) add disk caching for Stages 1-2b. Additionally, multiprocessing was added to three functions and a binary-search size prefilter was added to candidate scoring.

**Final assessment: A-**. All review issues fixed, plus a critical cross-process hash bug was discovered and fixed via parallel equivalence tests. 185 tests pass, including parallel vs serial equivalence, cache invalidation, edge cases, and integration tests.

---

## Issues (all resolved)

### 1. ~~BUG: `compute_document_frequencies` now returns wrong values~~ RETRACTED

Verified correct: `Counter.update(set)` increments each key by 1 per text, correctly counting document frequency.

### 2. FIXED: `_ngram_set_worker` pickled stopgrams per task

**Fix**: Pool initializer pattern (`_ngram_set_init`) sends stopgrams once per worker.

### 3. FIXED: Same pickle-per-task issue for `_phonetic_region_worker`

**Fix**: Pool initializer pattern (`_phonetic_init`) sends phonetic table once per worker.

### 4. FIXED: `_phonetic_region_worker` missing return type annotation

**Fix**: Added `-> tuple[str, list[tuple[str, int]]] | None`.

### 5. FIXED: `generate_candidates` source prefiltering doesn't handle missing keys

**Fix**: Changed to `length_map.get(tid, 0)`.

### 6. FIXED: Phonetic stopgram threshold reuses `STOPGRAM_DOC_FREQ`

**Fix**: Added `PHONETIC_STOPGRAM_DOC_FREQ = 0.05` to config.py; candidates.py uses it.

### 7. FIXED: `cache.py` computes `corpus_hash` twice during save

**Fix**: `self._corpus_hash` field caches between `is_valid()` and `save()`.

### 8. FIXED: Cache doesn't invalidate when config parameters change

**Fix**: `_config_snapshot()` captures all Stage 1-2b config params; stored in manifest and checked by `is_valid()`.

### 9. FIXED: Cache has no version/schema marker

**Fix**: `CACHE_VERSION = 2` in cache.py; checked in `is_valid()`. (Bumped to 2 when hash function changed.)

### 10. FIXED: `data/cache/` not in `.gitignore`

**Fix**: Added `data/cache/` entry.

### 11. FIXED: `__init__.py` doesn't export `cache`

**Fix**: Added `"cache"` to `__all__`.

### 12. FIXED: No test for parallelism correctness

**Fix**: `tests/test_parallel.py` — 4 tests verifying `compute_document_frequencies`, `build_ngram_sets`, and `generate_phonetic_candidates` produce identical results with `num_workers=1` vs `num_workers=2`.

**CRITICAL BUG FOUND**: These tests exposed a fundamental bug — Python's `hash()` is randomized per-process (PEP 456), and macOS `multiprocessing` uses `spawn` which gives each worker a different hash seed. All cross-process hash comparisons were broken. Fixed by replacing `hash()` with `stable_hash()` (`zlib.crc32`).

### 13. Accepted: `chunksize=64` hardcoded

Acceptable for 2,455 texts with 8 workers (~38 chunks). Added as a minor comment consideration; not changed.

### 14. FIXED: Missing test — cache invalidation when file deleted

**Fix**: `test_invalid_when_file_deleted` in `tests/test_cache.py`.

### 15. FIXED: Missing test — binary search boundary condition

**Fix**: `TestBisectBoundary` class in `tests/test_edge_cases.py` — tests exactly-at, just-below, and multiple sources near boundary.

### 16. FIXED: `generate_phonetic_candidates` Step 4 used inverted index pattern

**Fix**: Rewrote to `frozenset[str]` intersection, consistent with Stage 2 approach.

---

## Additional Fix: `stable_hash()` replacing `hash()`

**File**: `fingerprint.py` (definition), `candidates.py` (import)
**Severity**: Critical (correctness)

Python's built-in `hash()` is randomized per-process via PEP 456. On macOS, `multiprocessing` defaults to `spawn`, creating fresh processes with independent hash seeds. This made n-gram hashes inconsistent across:
- Different worker processes within the same Pool
- Worker processes vs the parent process

**Impact**: All fingerprint-based operations (stopgram identification, n-gram set construction, containment scoring) produced garbage results when parallelized.

**Fix**: `stable_hash(s)` uses `zlib.crc32(s.encode('utf-8'))` — C-level fast, deterministic across processes. 32-bit output gives ~0.5% collision rate at 48M hashes, acceptable for approximate containment scoring.

---

## Test Coverage (final)

| Component | Tests | Verdict |
|-----------|-------|---------|
| `build_ngram_sets` | 3 unit + 2 integration + 1 parallel | Good |
| `compute_document_frequencies` (parallel) | 2 parallel equivalence | Good |
| `generate_candidates` (set-based) | 4 unit + 2 integration | Good |
| Size prefilter (bisect) | 3 boundary tests | Good |
| Phonetic stopgrams | 2 tests (stopgram filtering, min threshold) | Good |
| `generate_phonetic_candidates` (parallel) | 1 parallel equivalence | Good |
| `PipelineCache` | 11 tests (roundtrip, manifest, snapshot, valid, 5 invalid, hash x3) | Good |
| Cache config invalidation | 1 test | Good |
| Cache version invalidation | 1 test | Good |

**Total: 185 tests, all passing.**

---

## Remaining Items for A+ Quality

1. **Pipeline-level integration test**: No test runs `run_pipeline()` end-to-end with `--no-cache` to verify the full flow. This would require the XML corpus.
2. **Performance regression test**: No benchmark asserting that Stage 2 runs under a time budget (e.g., 15 min). Would need corpus access.
3. **32-bit hash collision monitoring**: `stable_hash` uses CRC32 (4.3B space). With 48M hashes, ~267K collisions expected. Could add a debug-mode check that logs actual collision rate.
4. **Parallel chunksize tuning**: The hardcoded `chunksize=64` works well for the current corpus but could be computed dynamically based on `len(texts) // (num_workers * 4)` for better load balancing with variable text lengths.
