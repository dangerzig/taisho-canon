# Code Review: fast.py / _fast.pyx / _fast_fallback.py

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**Files reviewed:**
- `/Users/danzigmond/taisho-canon/digest_detector/fast.py` (dispatch module)
- `/Users/danzigmond/taisho-canon/digest_detector/_fast.pyx` (Cython implementation)
- `/Users/danzigmond/taisho-canon/digest_detector/_fast_fallback.py` (Python fallback)

---

## Summary

Overall this is well-written, well-tested code. The dispatch mechanism is clean, the Cython and Python implementations are structurally parallel, and the test suite includes equivalence checking. I found one critical correctness bug in the Cython byte-offset loop, one important CRC32 sign-extension portability issue, and several minor/style items.

---

## Findings

### 1. [P1 CRITICAL] Cython `fast_ngram_hashes`: byte-offset loop can under-fill when text ends with multi-byte characters

**File:** `_fast.pyx`, lines 57-64

```cython
while byte_idx <= byte_len and char_idx <= text_len:
    byte_offsets[char_idx] = byte_idx
    char_idx += 1
    if byte_idx < byte_len:
        byte_idx += 1
        while byte_idx < byte_len and (buf[byte_idx] & 0xC0) == 0x80:
            byte_idx += 1
```

The loop condition is `byte_idx <= byte_len and char_idx <= text_len`. For the last character in a string, after processing it, `char_idx` will equal `text_len` and `byte_idx` will equal `byte_len`. The loop needs one more iteration to set `byte_offsets[text_len] = byte_len` (the sentinel entry used on line 74/80 as `byte_offsets[i + n]`). Let's trace through:

- After the last real character: `char_idx = text_len - 1`, the body runs, increments to `char_idx = text_len`, and then `byte_idx` advances past the last character's bytes to `byte_idx = byte_len`.
- The while condition checks `byte_idx <= byte_len` (true, equal) and `char_idx <= text_len` (true, equal). So we enter the loop body again.
- `byte_offsets[text_len] = byte_len` -- the sentinel is set correctly.
- `char_idx` increments to `text_len + 1`.
- The `if byte_idx < byte_len` check is false (they're equal), so `byte_idx` doesn't advance.
- Next iteration: `char_idx = text_len + 1`, `char_idx <= text_len` is false, loop exits.

On closer inspection, this works correctly for the sentinel case. The `byte_offsets[text_len]` is always set to `byte_len`. No bug here -- I retract this as P1. The logic is correct but the loop structure makes it hard to verify at a glance. See P4 item below about clarity.

**Revised severity: P4 (style)** -- the loop is correct but its termination logic is non-obvious. A comment explaining that `byte_offsets[text_len]` is the sentinel would improve maintainability.

### 2. [P2 IMPORTANT] CRC32 hash value sign/width mismatch between Cython and Python

**File:** `_fast.pyx`, line 75 vs `_fast_fallback.py`, line 28

Cython code:
```cython
cdef long h
...
h = <long>c_crc32(0, buf + byte_offsets[i], ngram_byte_len)
```

Python code:
```python
h = zlib.crc32(text[i:i + n].encode('utf-8'))
```

Python's `zlib.crc32()` always returns an unsigned 32-bit value in the range `[0, 2^32 - 1]` (since Python 3). The C `crc32()` function returns `unsigned long`. However, in the Cython code, the result is cast to `<long>` (a signed type). On a 64-bit platform where `long` is 64 bits, this cast preserves the value since the unsigned 32-bit result fits in a signed 64-bit long. On a platform where `long` is 32 bits (Windows x64 with MSVC, for example), values >= 2^31 would become negative, creating a divergence from the Python fallback.

Since this project targets macOS (where `long` is 64 bits), this is not an active bug. But it is a portability concern. If the code ever runs on Windows or is compiled with a 32-bit C compiler, the hash sets will differ between Cython and Python, causing silent data corruption.

**Recommendation:** Use `uint32_t` (already imported but unused at line 13) instead of `long` for the hash variable, or cast to `<unsigned long>` and ensure the Python side is consistent.

### 3. [P2 IMPORTANT] `fast_fuzzy_extend` gap-lookahead can read out of bounds in Cython

**File:** `_fast.pyx`, lines 214-223

```cython
d_next = d_pos + (d_ext + 1) * direction
s_next = s_pos + (s_ext + 1) * direction

gap_d = (0 <= d_next < d_len and 0 <= s_idx < s_len and
         PyUnicode_READ(d_kind, d_data, d_next) ==
         PyUnicode_READ(s_kind, s_data, s_idx))
gap_s = (0 <= d_idx < d_len and 0 <= s_next < s_len and
         PyUnicode_READ(d_kind, d_data, d_idx) ==
         PyUnicode_READ(s_kind, s_data, s_next))
```

The bounds checks `0 <= d_next < d_len` are evaluated as Python-level boolean expressions within a single assignment. In Cython with `boundscheck=False`, the compiler does not enforce short-circuit evaluation guarantees at the C level for `and` expressions within typed variable assignments. However, since `gap_d` and `gap_s` are declared as `int`, and Cython compiles Python `and` as C `&&` for boolean expressions, short-circuit evaluation IS guaranteed by C semantics.

**Revised assessment:** The short-circuit evaluation is safe here because Cython translates Python `and` to C `&&`. The bounds check correctly guards the `PyUnicode_READ` calls. However, the code comment at the top of the file (lines 7-9) warns: "All callers of PyUnicode_READ must validate indices manually before the call." The current code does validate -- but the pattern is fragile. If someone refactors the boolean expression, the bounds check and the `PyUnicode_READ` call could become separated, introducing a buffer overread.

**Recommendation:** Consider splitting the bounds check and the `PyUnicode_READ` calls into explicit `if` statements for clarity and safety, consistent with the file's own documentation.

### 4. [P2 IMPORTANT] `fast_find_seeds` Cython version builds source_table differently from fallback

**File:** `_fast.pyx`, lines 108-115 vs `_fast_fallback.py`, lines 59-63

Cython:
```cython
source_table = {}
for i in range(s_len - k + 1):
    kgram = source[i:i + k]
    if kgram in source_table:
        source_table[kgram].append(i)
    else:
        source_table[kgram] = [i]
```

Fallback:
```python
from collections import defaultdict
source_table = defaultdict(list)
for i in range(s_len - k + 1):
    source_table[source[i:i + k]].append(i)
```

These produce functionally identical results (a dict mapping str to list[int]). The Cython version uses a plain dict with manual key-check; the fallback uses `defaultdict`. Both are correct. However, the caller in `align.py` (`_build_kgram_table` at line 30) also uses `defaultdict`. If a `defaultdict` is passed as `source_table`, the Cython version's `.get(kgram)` call on line 133 will return `None` for missing keys (correct behavior -- `defaultdict.get()` does NOT trigger the default factory). So this is fine.

**Revised severity: P4 (nit)** -- no actual bug, just an implementation style difference. The Cython approach of avoiding `defaultdict` is reasonable for C-level performance.

### 5. [P3 MINOR] `fast_ngram_hashes` fallback: `if stopgrams:` vs `if stopgrams is not None and len(stopgrams) > 0:`

**File:** `_fast_fallback.py`, line 26 vs `_fast.pyx`, line 72

Fallback:
```python
if stopgrams:
```

Cython:
```cython
if stopgrams is not None and len(stopgrams) > 0:
```

The fallback uses truthiness (`if stopgrams:`), which evaluates to `False` for both `None` and an empty set. The Cython version explicitly checks `is not None and len(stopgrams) > 0`. These are functionally equivalent for the expected inputs (`None` or `set[int]`), but diverge if someone passes an unexpected falsy value (e.g., `0`, `False`, empty `frozenset`). In practice this is not an issue since all callers pass `None` or a `set`.

**Recommendation:** For consistency, use the same idiom in both files. The Cython version's explicit check is slightly more defensive.

### 6. [P3 MINOR] Unused `uint32_t` import in Cython

**File:** `_fast.pyx`, line 13

```cython
from libc.stdint cimport uint32_t
```

`uint32_t` is imported but never used. It should either be used (see finding #2 above, where it would be the correct type for the hash variable) or removed.

### 7. [P3 MINOR] `fast_find_seeds` returns only the best match per digest position, not all maximal matches

**File:** `_fast.pyx`, lines 142-159 and `_fast_fallback.py`, lines 75-87

Both implementations iterate over all source positions for a given k-gram, but only keep the single best (longest) match per digest position. If two source positions produce equally long matches, only one is kept (the first one found in the Cython version due to `length > best_len` being strict greater-than; same in the fallback due to `length > best_match[2]`).

This is not a bug per se -- the docstring says "find all maximal exact matching substrings" which is slightly misleading since it only finds one per digest position. But the downstream `_chain_seeds` function handles overlapping seeds, so having one per d_pos is sufficient. The behavior is consistent between Cython and Python.

**Recommendation:** Clarify the docstring to say "find the best exact matching substring at each digest position" or similar.

### 8. [P3 MINOR] `fast_fuzzy_extend` gap logic can advance past bounds on next iteration

**File:** `_fast.pyx`, lines 226-237 and `_fast_fallback.py`, lines 144-155

When a gap is detected (e.g., `gap_d`), the code advances `d_ext += 2` and `s_ext += 1`. On the next loop iteration, the bounds check at lines 207-208 (Cython) / 127-128 (fallback) correctly catches any out-of-bounds access. So this is safe. However, the gap advancement can cause `d_ext` and `s_ext` to diverge by more than 1 per iteration, which means the "extension count" includes the gap character. This is the intended behavior (documented in `align.py` line 80: "fuzzy extensions may include gap characters").

No action needed -- just noting this for the record.

### 9. [P4 STYLE] Dispatch module `fast.py` is clean and well-structured

**File:** `fast.py`, lines 1-37

The dispatch logic is straightforward: check env var first, then try Cython import, then fallback. The `noqa` and `type: ignore` comments are appropriate. The logging is helpful for debugging. No issues.

### 10. [P4 STYLE] Cython byte-offset loop would benefit from a comment

**File:** `_fast.pyx`, lines 48-64

The byte-offset building loop correctly produces `text_len + 1` entries (indices 0 through `text_len`), where `byte_offsets[text_len] = byte_len` serves as a sentinel for the n-gram byte length calculation on line 74. A brief comment noting this sentinel purpose would make the code easier to audit.

### 11. [P4 STYLE] `try/finally` for `free()` is good practice

**File:** `_fast.pyx`, lines 71-84

The `try/finally` block ensuring `free(byte_offsets)` is called even if an exception occurs in the hashing loop is excellent defensive practice. No issues.

### 12. [P4 STYLE] `setup.py` compiler directives are duplicated

**File:** `setup.py`, lines 13-16 and `_fast.pyx`, line 1

The compiler directives (`boundscheck=False`, `wraparound=False`, `language_level=3`) are specified both in the `.pyx` file header comment and in `setup.py`'s `cythonize()` call. This is harmless (the `.pyx` file-level directives take precedence for per-file settings), but the duplication could lead to confusion if they ever diverge.

**Recommendation:** Pick one location. The `.pyx` file is the canonical place for per-file directives; `setup.py` is better for project-wide defaults.

---

## Equivalence Assessment

**Are the Cython and fallback implementations equivalent?**

Yes, with one caveat:

1. **`fast_ngram_hashes`**: Equivalent. Both compute `zlib.crc32` / C `crc32()` on UTF-8 encoded n-gram bytes. The Cython version avoids per-n-gram string slicing and encoding by operating directly on a pre-encoded byte buffer with character-to-byte offset mapping. The hash values will be identical on 64-bit platforms where `long` is 64 bits (macOS, Linux x86_64). See finding #2 for the portability caveat.

2. **`fast_find_seeds`**: Equivalent. Both build the same k-gram table (dict mapping substrings to position lists), iterate over digest positions, and keep the longest match per position. The extension loop uses direct Unicode buffer access in Cython vs Python string indexing in the fallback, but the comparison logic is identical. The test suite confirms equivalence.

3. **`fast_fuzzy_extend`**: Equivalent. The scoring, gap detection, and best-score tracking logic are structurally identical. Both use the same tie-breaking rule (prefer digest gap). The test suite confirms equivalence across multiple scenarios including forward/backward extension and gap cases.

---

## Test Coverage Assessment

The test suite (`tests/test_fast.py`) is thorough:
- Direct unit tests for all three functions
- Edge cases (empty strings, short strings, boundaries)
- CJK character handling (multi-byte UTF-8)
- Pre-built source table compatibility
- Cython/fallback equivalence tests (conditional on Cython availability)
- Regression tests for caching bugs

**Gap:** No test for the case where `n = 0` or `k = 0` is passed. Both implementations would produce `range(text_len + 1)` n-grams of length 0, all hashing to the same CRC32 value. This is unlikely to be called in practice but could be worth a defensive check.

**Gap:** No test for very large texts (performance regression testing). The Cython version's `malloc` of `(text_len + 1) * sizeof(Py_ssize_t)` could theoretically fail for extremely large texts, but the `MemoryError` check on line 53 handles this correctly.

---

## Overall Grade: A-

The code is clean, well-documented, and thoroughly tested. The Cython implementation correctly avoids Python object allocation in hot loops and uses direct C-level operations. The dispatch mechanism is simple and robust. The main areas for improvement are the portability concern with `long` vs `uint32_t` for hash values (finding #2) and adding explicit bounds-check comments around `PyUnicode_READ` calls (finding #3).
