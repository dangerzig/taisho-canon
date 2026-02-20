# Code Review: `digest_detector/fingerprint.py`

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Files reviewed:**
- `/Users/danzigmond/taisho-canon/digest_detector/fingerprint.py` (183 lines)
- `/Users/danzigmond/taisho-canon/digest_detector/_fast_fallback.py` (supporting implementation)
- `/Users/danzigmond/taisho-canon/digest_detector/_fast.pyx` (Cython implementation)
- `/Users/danzigmond/taisho-canon/digest_detector/config.py` (configuration)
- `/Users/danzigmond/taisho-canon/tests/test_fingerprint.py` (tests)

---

## Summary

This module is responsible for Stage 2a of the pipeline: computing character n-gram fingerprints for ~8,982 Chinese Buddhist texts, identifying stop-grams (n-grams appearing in too many documents), and building per-text n-gram hash sets for fast set-intersection containment scoring. The code is clean, well-structured, and demonstrates good multiprocessing practices. The findings below are mostly minor.

---

## Findings

### P2-1: `_doc_freq_worker` does not use pool initializer, inconsistent with `_ngram_set_worker`

**File:** `fingerprint.py`, lines 52-55 vs. lines 110-117
**Severity:** P2 (important)

`_ngram_set_worker` uses the pool initializer pattern (`_ngram_set_init`) to receive shared state (`stopgrams`, `n`), avoiding per-task pickling. However, `_doc_freq_worker` passes `n` via the args tuple instead. While this works (an int is cheap to pickle), the inconsistency is surprising and could become a problem if `_doc_freq_worker` ever needs to share more expensive state in the future.

More importantly, the `Pool` call at line 83 does not pass an `initializer` at all:

```python
with Pool(num_workers, maxtasksperchild=config.MAXTASKSPERCHILD) as pool:
```

This is functionally fine since `_doc_freq_worker` only needs `n` (an int) from args. But the asymmetry with `build_ngram_sets` (which does use an initializer at line 149) is worth noting for future maintainability.

**Impact:** Low risk now, but an inconsistency that could confuse future contributors.

---

### P2-2: CRC32 is 32-bit -- collision risk at scale

**File:** `fingerprint.py`, lines 20-29; `_fast_fallback.py`, line 28; `_fast.pyx`, lines 74-81
**Severity:** P2 (important)

`stable_hash()` uses `zlib.crc32()` which returns a 32-bit hash. With ~8,982 texts and NGRAM_SIZE=5, the corpus could easily produce millions of unique n-grams. By the birthday paradox, with 2^32 possible values:

- At ~77,000 unique n-grams: 50% chance of at least one collision
- At ~300,000 unique n-grams: near-certain collision(s)

For CJK text with ~286K chars in T223 alone, the total unique 5-gram count across the corpus could be in the low millions, making collisions virtually guaranteed.

The impact of collisions here is relatively benign: two different n-grams map to the same hash, causing slightly inflated containment scores (false positives, not false negatives). The downstream alignment stage (Stage 3) would catch these since it works on actual text, not hashes. The debug logging at lines 161-169 ("overlap from shared n-grams + collisions") already acknowledges this possibility.

Still, upgrading to a 64-bit hash (e.g., `xxhash.xxh64` or even `struct.unpack('<Q', hashlib.md5(...).digest()[:8])`) would eliminate this concern entirely with negligible performance cost. The `stable_hash()` function is only called from tests and `fingerprint_text()`; all hot-path hashing goes through `fast_ngram_hashes` which would also need updating.

**Impact:** Inflated containment scores for a small fraction of pairs; mitigated by Stage 3 alignment.

---

### P2-3: `stopgrams` parameter truthiness check in `_fast_fallback.py`

**File:** `_fast_fallback.py`, line 26
**Severity:** P2 (important)

```python
if stopgrams:
```

This uses truthiness, which means an **empty** `frozenset()` or `set()` is treated identically to `None`. While this is the desired behavior (skip filtering when there are no stopgrams), it conflates two semantically different cases: "no stopgram set provided" vs. "a stopgram set was provided but happens to be empty." This is actually correct in practice since both cases mean "don't filter," but it's worth noting as a defensive-coding concern.

The Cython version at `_fast.pyx` line 72 does:

```python
if stopgrams is not None and len(stopgrams) > 0:
```

This is more explicit and correct. The fallback should match the Cython behavior for consistency.

**Impact:** No functional bug today, but a potential source of confusion if semantics ever change.

---

### P3-1: `stable_hash()` in `fingerprint.py` is not used in the hot path

**File:** `fingerprint.py`, lines 20-29
**Severity:** P3 (minor)

The `stable_hash()` function exists in `fingerprint.py` but is only used:
1. In tests (`test_fingerprint.py`)
2. In `candidates.py` (via `from .fingerprint import stable_hash`)

All actual n-gram hashing in the pipeline goes through `fast_ngram_hashes()` (either Cython or fallback), which inlines its own `zlib.crc32()` calls. The `stable_hash()` function is effectively dead code for production, serving only as a convenience for tests and the candidates module.

This isn't a bug, but it means there are two places where the hashing algorithm is defined. If the hash function were ever changed, `stable_hash()` and `fast_ngram_hashes()` would need to be updated in lockstep, or hash values would silently diverge. The tests in `test_fingerprint.py` (e.g., `TestDocumentFrequencies.test_basic` at line 46) rely on `stable_hash()` producing the same values as `fast_ngram_hashes()`.

**Recommendation:** Add a comment or assertion somewhere (perhaps in tests) that explicitly verifies `stable_hash(s) == the hash produced by fast_ngram_hashes for the same string`.

**Impact:** Maintenance risk if hash function changes.

---

### P3-2: `generate_ngrams()` is unused in the pipeline

**File:** `fingerprint.py`, lines 43-49
**Severity:** P3 (minor)

`generate_ngrams()` returns actual n-gram strings (not hashes). It is not called anywhere in the production pipeline -- all n-gram work goes through `fast_ngram_hashes()`. It appears to be a utility function kept for debugging or testing, but no tests or pipeline code actually use it except `TestGenerateNgrams` in the test file.

This is fine as a utility, but it could be misleading since its name suggests it's part of the main pipeline.

**Impact:** Minor dead code.

---

### P3-3: Cython `byte_offsets` loop has a subtle edge case

**File:** `_fast.pyx`, lines 51-64
**Severity:** P3 (minor)

The byte-offset loop builds a mapping from character index to byte position:

```cython
while byte_idx <= byte_len and char_idx <= text_len:
    byte_offsets[char_idx] = byte_idx
    char_idx += 1
    if byte_idx < byte_len:
        byte_idx += 1
        while byte_idx < byte_len and (buf[byte_idx] & 0xC0) == 0x80:
            byte_idx += 1
```

This works correctly for well-formed UTF-8. However, if `byte_idx == byte_len` when `char_idx < text_len`, the inner `if` is skipped and `char_idx` increments without advancing `byte_idx`, which could populate later slots of `byte_offsets` with stale (duplicate) values. This should never happen for valid UTF-8 strings produced by Python's `.encode('utf-8')`, but there's no defensive check or assertion for it.

Additionally, the loop condition `byte_idx <= byte_len` allows `byte_offsets[text_len] = byte_len` to be set, which is needed for the `byte_offsets[i + n]` access pattern on line 74. This is correct but non-obvious; a comment would help.

**Impact:** No bug in practice (Python always produces valid UTF-8), but the sentinel value `byte_offsets[text_len]` is subtle.

---

### P3-4: Cython `fast_ngram_hashes` casts CRC32 to `long`, which is platform-dependent

**File:** `_fast.pyx`, line 75
**Severity:** P3 (minor)

```cython
h = <long>c_crc32(0, buf + byte_offsets[i], ngram_byte_len)
```

On most 64-bit platforms, C `long` is 64-bit (LP64), so this cast is fine. But on 64-bit Windows (LLP64), C `long` is 32-bit, and `c_crc32` returns `unsigned long`. The cast to `long` would still work but the sign behavior differs. The fallback uses Python's `zlib.crc32()` which always returns an unsigned 32-bit int (0 to 2^32-1) on Python 3.

Since this is a macOS project and the values are used only for set membership (not arithmetic), this is unlikely to cause issues, but it's worth noting for portability.

**Impact:** No bug on macOS/Linux; potential sign mismatch on Windows.

---

### P3-5: No validation that `num_texts > 0` in `identify_stopgrams`

**File:** `fingerprint.py`, lines 91-107
**Severity:** P3 (minor)

```python
max_docs = int(num_texts * threshold)
```

If `num_texts` is 0, `max_docs` would be 0, and then `freq > 0` would be true for any entry in `doc_freq`. This would mark everything as a stopgram, which is technically correct (if there are 0 texts, there are no n-grams), but only because `doc_freq` would also be empty. If somehow an empty `num_texts` were passed with a non-empty `doc_freq`, the behavior would be surprising.

The pipeline always calls this with `len(texts)`, which would be 0 only if the corpus is empty, making the `doc_freq` dict also empty. So this is not a real bug.

**Impact:** Theoretical only.

---

### P4-1: Type annotation for `_doc_freq_worker` return type is incorrect

**File:** `fingerprint.py`, line 52
**Severity:** P4 (style/nit)

```python
def _doc_freq_worker(args: tuple) -> frozenset[int]:
```

The return type annotation says `frozenset[int]`, which is correct since `fast_ngram_hashes` returns `frozenset[int]`. However, this annotation doesn't capture that `args` is specifically a `tuple[str, int]`. A more precise annotation would be:

```python
def _doc_freq_worker(args: tuple[str, int]) -> frozenset[int]:
```

Similarly, `_ngram_set_worker` at line 110:

```python
def _ngram_set_worker(args: tuple) -> tuple[str, frozenset[int]]:
```

Could be `args: tuple[str, str]`.

**Impact:** Pure style; no functional effect.

---

### P4-2: Module-level mutable globals for worker state

**File:** `fingerprint.py`, lines 32-33
**Severity:** P4 (style/nit)

```python
_worker_stopgrams: set[int] = set()
_worker_n: int = 5
```

These module-level mutable globals are set by `_ngram_set_init()` and also directly in `build_ngram_sets()` (line 141). This pattern is standard for `multiprocessing.Pool` initializers, but the direct mutation at line 141 (`global _worker_stopgrams, _worker_n`) means the serial path modifies module-level state as a side effect. If `build_ngram_sets()` were called twice with different stopgrams in the same process, the second call would correctly override the first, so there's no bug. But it's a somewhat fragile pattern.

**Impact:** Works correctly; standard multiprocessing pattern.

---

### P4-3: Debug logging builds a potentially large set

**File:** `fingerprint.py`, lines 161-169
**Severity:** P4 (style/nit)

```python
if logger.isEnabledFor(logging.DEBUG):
    all_hashes: set[int] = set()
    for s in result.values():
        all_hashes.update(s)
    unique = len(all_hashes)
```

This materializes the union of all n-gram sets, which with ~8,982 texts could be tens of millions of hashes. The `isEnabledFor` guard ensures this only runs when DEBUG is enabled, which is good. But if someone enables DEBUG logging on the full corpus, this could use significant memory. Consider logging a sample or skipping this entirely for large corpora.

**Impact:** Only matters with DEBUG logging on; properly guarded.

---

### P4-4: `fingerprint_text` returns `list[int]`, not `frozenset[int]`

**File:** `fingerprint.py`, lines 174-182
**Severity:** P4 (style/nit)

```python
def fingerprint_text(...) -> list[int]:
    ...
    return list(fast_ngram_hashes(text, n, stopgrams))
```

This converts the `frozenset` from `fast_ngram_hashes` into a `list`. Since the function is not used in the production pipeline (only exported), it's unclear why a list is preferred over a frozenset. If callers want set semantics (membership tests), the conversion is wasteful. If they want ordering, a list of hash values has no meaningful order anyway.

**Impact:** Minor API design question; no functional effect.

---

## Positive Observations

1. **Correct use of `stable_hash` over `hash()`** (line 20-29): The docstring clearly explains why Python's `hash()` is unsuitable for multiprocessing, referencing PEP 456. This is a critical correctness concern that's been handled well.

2. **Pool initializer pattern** (lines 36-40, 149-150): Using `initializer` + `initargs` to share `stopgrams` across workers avoids pickling the stopgram set (potentially millions of ints) for every task. This is the correct pattern.

3. **`maxtasksperchild`** (lines 83, 151): Periodic worker restart to reclaim leaked memory is good practice for long-running pools processing thousands of items.

4. **Memory management in pipeline**: The pipeline caller (`pipeline.py`, lines 148-152) explicitly `del`s `doc_freq`, `ngram_sets`, and `stopgrams` after they're no longer needed, which is good for a pipeline processing ~9K texts.

5. **Full_text vs. jing_text distinction**: The comment at lines 72-74 explains why `full_text` (not `jing_text`) is used for document frequency computation. This is an important domain decision that's well-documented.

6. **Dynamic chunksize** (lines 82, 148): `max(1, len(args_list) // (num_workers * 4))` provides reasonable granularity for load balancing across workers without excessive IPC overhead.

7. **Serial fallback** (lines 78, 139): Both parallelized functions gracefully fall back to serial execution when `num_workers <= 1` or when the corpus is small (`< 10` texts), avoiding pool overhead for trivial cases.

---

## Overall Assessment

**Grade: A-**

This is well-written, production-quality code. The multiprocessing patterns are correct and efficient. The use of `zlib.crc32` for cross-process hash stability is the right call. The module is focused, well-documented, and properly tested. The findings are mostly minor consistency issues and theoretical edge cases. The only item worth considering for action is P2-2 (32-bit hash collision risk), which is mitigated by the downstream alignment stage but could be cheaply eliminated with a 64-bit hash.
