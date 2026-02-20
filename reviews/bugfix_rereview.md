# Bugfix Re-Review

Review of 15 fixes applied to the digest_detector codebase. For each fix: OK if correct, or a description of the issue found.

---

**1. align.py `_chain_seeds` -- DP with prev[] backtracking**

OK. The DP correctly implements weighted interval scheduling: `dp[i]` stores the max coverage of any chain ending with seed `i`; `prev[i]` stores the predecessor index (-1 if none). The binary search via `bisect_right(end_positions, d_start_i, 0, i) - 1` correctly finds the rightmost non-overlapping predecessor. The backtracking loop `while i >= 0: selected.append(...); i = prev[i]` correctly follows the predecessor chain. The pre-filter for contained seeds is a safe optimization (the DP handles remaining overlaps). All correct.

**2. extract.py `build_char_map` -- WARNING for duplicate char_id**

OK. When `char_id` is already in `char_map`, the code resolves the new value and compares it to the existing value. If different, it logs a warning and keeps the existing value. The `continue` on line 108 correctly skips re-adding the duplicate. The only minor note: if the new entry has a different resolution path (e.g. `normal_unicode` instead of `normalized form`), the comparison only checks `normalized form`, but this is consistent with the resolution priority elsewhere and is fine for a warning.

**3. extract.py `<g>` handler -- early return**

OK. The `<g>` tag is correctly handled as a leaf element: it resolves the character reference, appends the result, and returns immediately. This prevents falling through to `elem.text` processing, which would append the fallback rendering (e.g. `[覆-西+非]`) alongside the resolved character. The early `return results` is correct.

**4. extract.py `save_results` -- None guard for metadata**

OK. Defensive check: if `text.metadata is None`, logs a warning and `continue`s to skip that text's metadata entry. The `full_text` is still saved (line 508 runs before the guard), so no text data is lost. Clean.

**5. fingerprint.py -- `_doc_freq_worker` initializer pattern**

OK. Uses the standard `Pool(initializer=_doc_freq_init, initargs=(n,))` pattern to set `_worker_n` in each worker process. The single-process fallback path also sets `_worker_n` directly. This correctly avoids pickling issues and ensures the value is available in all workers. Clean.

**6. `_fast_fallback.py` -- stopgrams check `is not None and len() > 0`**

OK. The check `if stopgrams is not None and len(stopgrams) > 0` correctly distinguishes three cases: (a) no stopgrams provided (`None`), (b) empty frozenset, (c) non-empty frozenset. Cases (a) and (b) skip the filtering branch, which is correct since an empty set would never match anything. Consistent with the Cython version on line 72 of `_fast.pyx`.

**7. candidates.py -- jing_text/full_text asymmetry comment**

OK. The comment on lines 71-74 correctly documents the intentional asymmetry: the digest's n-grams come from `jing_text` (excluding preface material), while source n-gram sets use `full_text`. This is a documentation-only change. Clean.

**8. candidates.py -- phonetic containment recomputation after pair normalization**

OK. When the pair is normalized (shorter text becomes digest), the code correctly recomputes `final_matching`, `final_digest_ngrams`, and `final_containment` from the new digest's perspective (`source_set` becomes the digest set). The intersection `source_set & digest_set` is symmetric so matching count is the same either way, but `final_digest_ngrams` correctly uses `len(source_set)` (the new digest). The division-by-zero guard is present. Clean.

**9. score.py -- commentary docstring threshold fix (0.20 to 0.30)**

OK. The docstring now correctly states `coverage >= 0.30` for digest/commentary, matching the actual config value `DIGEST_THRESHOLD` (which defaults to 0.30 based on the classification logic at line 86: `elif coverage < config.DIGEST_THRESHOLD`). Clean.

**10. score.py -- containment uses raw `alignment.coverage`**

OK. Line 114: `containment=alignment.coverage` correctly stores the raw alignment coverage before phonetic discounting. The `coverage` field (line 115) stores the phonetic-adjusted value. This properly separates the two metrics, matching the field documentation in models.py. Clean.

**11. models.py -- field documentation for containment vs coverage**

OK. Line 92: `containment: float  # raw alignment coverage (before phonetic adjustment)` and line 93: `coverage: float  # effective coverage (phonetic matches discounted)` clearly document the distinction. Consistent with the score.py usage. Clean.

**12. `_fast.pyx` -- hash type `uint32_t`**

OK. CRC32 returns a 32-bit unsigned integer. Using `uint32_t` (line 40) instead of `long` is correct and matches the Python `zlib.crc32()` return range (0 to 2^32-1). The cast on line 75 `<uint32_t>c_crc32(...)` is also correct. This ensures consistency between the Cython fast path and the Python fallback (which also uses `zlib.crc32`). Clean.

**13. phonetic.py -- `_COMMON_PROSE_EXCLUSIONS` and filtering**

OK. The frozenset on lines 26-28 contains 17 high-frequency Buddhist prose characters that would create false phonetic equivalences. The filtering at lines 198-200 removes these characters from `char_to_syllables` before the ambiguity filter runs. This is applied in the right order (prose exclusions first, then ambiguity cap). The log message on line 210 reports the count of removed prose chars. Clean.

**14. align.py `_find_phonetic_seeds` -- 500-position cap**

OK. Lines 239-246 cap `candidate_positions` at 500 per digest character, breaking out of both the inner `syl_to_positions` loop and the outer `d_syls` loop. This prevents O(D*S) blowup when a common syllable maps to thousands of source positions. The cap of 500 is generous enough to find real matches while bounding worst-case complexity. Clean.

**15. pipeline.py -- `align_candidates` uses resolved `num_workers`**

ISSUE (minor). At line 96, the pipeline resolves `num_workers` with the default `memory_intensive=True`, which caps workers at `DEFAULT_MAX_WORKERS` (4). This resolved value is then passed to `align_candidates` at line 205-206. Inside `align_candidates` (align.py line 608), `resolve_worker_count(num_workers, memory_intensive=False)` is called, but since `num_workers` is now a concrete integer (not `None`), `resolve_worker_count` returns it immediately (line 86-87 of config.py), ignoring the `memory_intensive=False` flag. The intent of `memory_intensive=False` is to allow alignment to use up to `min(cpu_count(), 16)` workers (since alignment is memory-light), but this is defeated by the pre-resolution in the pipeline.

**Net effect**: alignment runs with at most 4 workers instead of potentially up to 16. This is a performance regression (alignment could use more parallelism) but not a correctness bug. If the user explicitly passes `--workers N`, both old and new behavior respect that value, so the impact is limited to the default case.

**Fix**: The pipeline should either (a) pass `None` to `align_candidates` when no explicit `--workers` was provided, or (b) resolve separately for alignment using `resolve_worker_count(num_workers, memory_intensive=False)` where `num_workers` is the original user-provided value (before pipeline resolution).

---

## Summary

| # | Fix | Verdict |
|---|-----|---------|
| 1 | DP backtracking in `_chain_seeds` | OK |
| 2 | Duplicate char_id warning | OK |
| 3 | `<g>` early return | OK |
| 4 | None guard for metadata | OK |
| 5 | `_doc_freq_worker` initializer pattern | OK |
| 6 | Stopgrams `is not None and len() > 0` | OK |
| 7 | jing_text/full_text asymmetry comment | OK |
| 8 | Phonetic containment recomputation | OK |
| 9 | Commentary docstring threshold | OK |
| 10 | Containment uses raw coverage | OK |
| 11 | containment vs coverage field docs | OK |
| 12 | CRC32 `uint32_t` type | OK |
| 13 | Common prose exclusions | OK |
| 14 | 500-position cap in phonetic seeds | OK |
| 15 | Pipeline `num_workers` for alignment | Minor issue -- alignment loses `memory_intensive=False` benefit |

**14 of 15 fixes are clean. Fix #15 has a minor performance issue (not a correctness bug) where alignment's intended higher parallelism is capped by the pipeline's early worker resolution.**
