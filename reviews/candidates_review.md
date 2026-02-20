# Code Review: `digest_detector/candidates.py`

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**File:** `/Users/danzigmond/taisho-canon/digest_detector/candidates.py` (484 lines)
**Scope:** Bugs, logic errors, edge cases, performance, multiprocessing safety, code quality

---

## Summary

The module is well-structured and shows evidence of careful iteration. The multiprocessing architecture is sound (initializer pattern, `stable_hash` via `fast_ngram_hashes`), the docNumber parsing handles edge cases (leading zeros, malformed IDs), and the candidate generation uses an efficient binary-search prefilter. Test coverage for the core paths is good.

That said, I found **2 P2 issues** (logic correctness), **3 P3 issues** (robustness/edge cases), and **4 P4 nits** (style/readability).

---

## P2 -- Important

### P2-1: `generate_candidates` uses `jing_text` for digest n-grams but `full_text` for source n-gram sets -- asymmetric comparison may inflate/deflate scores

**Lines 71-72 (worker) vs. fingerprint.py line 136**

In `_candidate_worker` (line 72), the digest's n-gram set is built from `jing_text`:
```python
digest_set = fast_ngram_hashes(jing_text, n, stopgrams)
```

But the source n-gram sets in `ngram_sets` (passed from `fingerprint.build_ngram_sets`, line 136) are built from `full_text`:
```python
args_list = [(text.text_id, text.full_text) for text in texts]
```

This asymmetry is *intentional* and documented (digest uses jing to exclude preface material; source uses full_text so it can match against any digest content). However, the digest's `full_text` n-gram set from `ngram_sets` is **also passed into the Pool via `source_sets_arr`** (line 239), meaning when Text A is being evaluated as a *source* for Text B's digest comparison, it uses the `full_text` fingerprint. But when Text A is being evaluated as a *digest*, it recomputes n-grams from `jing_text` on the fly.

The issue: the pre-built `ngram_sets[d_id]` (full_text) is never used for the digest side, and the freshly-computed `digest_set` (jing_text) is never stored. This is all consistent but there is a subtle correctness concern:

**The `source_sets_arr` includes digest-sized texts.** Line 232-236 builds `source_entries` from *all* entries in `ngram_sets`, including short texts. A short text T1 (300 chars) will appear in `source_sets_arr` and could be scored as a "source" for another short text T2 (200 chars) -- if T2's `char_count * MIN_SIZE_RATIO <= 300`. The `MIN_SIZE_RATIO = 2.0` default means T2 must be <= 150 chars for T1 to qualify as a source, which is small but possible. This isn't a bug per se, but including every text in `source_entries` wastes memory for texts that are too small to ever be a meaningful source. Consider filtering `source_entries` to exclude texts below some absolute minimum source size.

**Severity:** P2 -- Not a bug in current behavior, but the asymmetry deserves a brief code comment clarifying that `digest_set` is intentionally recomputed from `jing_text` per-worker while `source_sets_arr` uses the pre-built `full_text` sets.

---

### P2-2: Phonetic containment score stored in `CandidatePair` may not represent the correct direction

**Lines 456-458**

```python
matching = len(digest_set & source_set)
containment = matching / len(digest_set)
```

The containment is computed as `|D intersect S| / |D|` -- the fraction of the *digest's* phonetic n-grams found in the source. This is the correct asymmetric containment direction for digest detection.

However, the deduplication logic (lines 461-465) normalizes the pair key to `(shorter, longer)`:
```python
if d_len <= s_len:
    pair_key = (d_id, source_id)
else:
    pair_key = (source_id, d_id)
```

This means when Text A (400 chars) iterates as `d_id` and Text B (300 chars) iterates as `source_id`, the pair key becomes `(B, A)` (shorter first). The `containment_score` stored is `|A_ngrams & B_ngrams| / |A_ngrams|` -- the fraction of A's phonetic n-grams in B. But the `CandidatePair.digest_id` is set to B (the shorter text) and `source_id` to A.

So the `containment_score` represents A's coverage by B, but the pair claims B is the digest and A is the source. If these two texts have very different phonetic n-gram set sizes, the containment score is misleading -- it measures the wrong direction.

**Impact:** This only matters for phonetic candidate pairs where the shorter text (by char_count) has a *larger* phonetic n-gram set than the longer text. In practice, longer texts tend to have more phonetic n-grams, so this is an edge case. But it is logically incorrect.

**Fix:** After normalizing `pair_key`, recompute containment from the perspective of the actual digest (shorter text). Or better: only iterate over texts as digests when they are shorter than the source, like `generate_candidates` does with `digest_candidates` and the size ratio filter.

---

## P3 -- Minor

### P3-1: `_find_docnumber_pairs` cross-volume matching is too broad

**Lines 131-138**

The docnumber key includes the volume prefix: `f"{vol_prefix}:{main_num}"`. This means T08n0250's reference to "251" creates key `T08:251`, and T08n0251 creates the same key via self-reference. Good.

But consider: if T08n0250 references "251" and T**14**n0251 also exists, they would NOT be paired because the volume prefixes differ (T08 vs T14). This is actually correct behavior for CBETA's Taisho numbering where docNumber references are volume-scoped. However, there is also no validation that the referenced number actually corresponds to a text in the same volume. If T08n0250 references "999" and there is no T08n0999, the key `T08:999` is created with only one text_id, so no pair is generated -- which is the correct graceful handling.

**The concern:** CBETA docNumber references are *not* always volume-scoped. A docNumber like "No. 250 [Nos. 251-255, 257]" references other texts in the same volume, but cross-volume references do exist in the Taisho (e.g., an Agama text referencing a Vinaya text in a different volume). These cross-volume pairs would be silently missed.

**Severity:** P3 -- The current volume-scoping is a reasonable heuristic and avoids false positives across unrelated texts that happen to share a number. But it should be documented as a known limitation.

---

### P3-2: `_candidate_worker` does not account for CRC32 hash collisions

**Line 88-89**

```python
matching = len(digest_set & source_sets_arr[idx])
containment = matching / len(digest_set)
```

CRC32 produces 32-bit hashes. With ~286K chars in T223 and n=5, that text has ~286K n-grams. The birthday paradox gives a non-trivial collision probability: for k n-grams, the expected number of collisions is approximately k^2 / (2 * 2^32). For 286K n-grams, that is ~286000^2 / 2^33 = ~9.5 collisions.

For the purpose of *candidate generation* (a coarse filter), this is fine -- a handful of false-positive matching n-grams won't meaningfully inflate containment above the 10% threshold. The detailed alignment (Stage 3) operates on actual character sequences and is collision-proof.

The debug logging in `fingerprint.py` (lines 161-169) already reports hash space overlap, which is good. But the code has no runtime monitoring of collision rates in the candidate scoring itself.

**Severity:** P3 -- Acceptable for the coarse candidate filter. The ~9.5 expected collisions out of 286K n-grams is negligible (~0.003%).

---

### P3-3: `generate_phonetic_candidates` iterates all texts, not just digest-sized ones

**Lines 438-448**

```python
for text in texts:
    d_id = text.text_id
    if d_id not in phonetic_sets:
        continue
    ...
    for source_id, source_set in phonetic_sets.items():
```

Unlike `generate_candidates` which pre-filters to `digest_candidates` (texts <= `MAX_DIGEST_LENGTH`), the phonetic candidate generator iterates over *all* texts as potential digests. If a 200K-char text has a small dharani section, it will be scored as a potential digest against all other texts with dharani sections. This is likely intentional (dharani matching can exist in long texts too), but it means the function is O(P^2) where P is the number of texts with phonetic regions.

The `min_size_ratio` check (line 453) prevents scoring when the "source" is not sufficiently longer than the "digest," and the deduplication (lines 461-469) prevents double-counting, so there is no correctness issue. But if many long texts have dharani sections, the quadratic scan could be slow.

**Severity:** P3 -- Unlikely to be a bottleneck in practice since only texts with indexed transliteration regions participate, and the inner loop is just set intersection.

---

## P4 -- Style/Nit

### P4-1: Type annotation `num_workers: int = None` should be `int | None = None`

**Lines 193, 342**

```python
def generate_candidates(
    texts: list[ExtractedText],
    ngram_sets: dict[str, frozenset[int]],
    stopgrams: set[int],
    num_workers: int = None,         # <-- should be int | None = None
) -> list[CandidatePair]:
```

Same at line 342:
```python
def generate_phonetic_candidates(
    texts: list[ExtractedText],
    table: dict[str, set[str]],
    num_workers: int = None,         # <-- should be int | None = None
) -> list[CandidatePair]:
```

The default is `None` but the type hint says `int`. Modern Python (3.10+) should use `int | None`. This is consistent with how `config.py` line 75 declares it: `num_workers: int | None = None`.

---

### P4-2: Unused `seen_pairs` tracking in the parallel path

**Lines 249, 264-267**

```python
seen_pairs = set()

if num_workers > 1 and len(digest_candidates) >= 10:
    ...
    for result_batch in pool.imap_unordered(...):
        for cand in result_batch:
            pair_key = (cand.digest_id, cand.source_id)
            seen_pairs.add(pair_key)
            candidates.append(cand)
```

In both serial and parallel paths, `seen_pairs` is populated but never *checked* during the main loop. It is only used afterward (line 289) to deduplicate docNumber pairs. But within the main loop itself, there is no `if pair_key in seen_pairs: continue` check.

This is actually correct behavior: each digest is processed independently, and a digest never compares against itself (`source_id == d_id` check on line 85). So duplicate pairs cannot arise from the main loop -- a pair (A, B) is only generated when A is the digest, and it will not be generated again when B is the digest (because the pair key would be (B, A), not (A, B)).

However, the `seen_pairs` set is misleadingly named and populated during the main loop when its only real purpose is post-loop deduplication of docNumber pairs. Consider renaming it to `fingerprint_pairs` or `ngram_pairs` to clarify its role.

---

### P4-3: `_cleanup_candidate_globals` resets `_cand_n` to hardcoded 5 instead of config default

**Line 184**

```python
_cand_n = 5
_cand_min_containment = 0.10
```

These hardcoded defaults should reference `config.NGRAM_SIZE` and `config.MIN_CONTAINMENT` to stay consistent if the config defaults change. Or, since this is a cleanup function that simply releases references, the exact values don't matter (they'll be overwritten by the next call to `_candidate_init`). But hardcoding values that happen to match current config defaults creates a maintenance trap.

---

### P4-4: Log message double-counts `from_docnumber` candidates

**Lines 308-311**

```python
logger.info("Generated %d candidate pairs (%d from fingerprinting, %d from docNumber)",
            len(candidates),
            sum(1 for c in candidates if c.containment_score > 0),
            sum(1 for c in candidates if c.from_docnumber))
```

A candidate found by both fingerprinting (containment_score > 0) and docNumber cross-reference (`from_docnumber=True`) will be counted in *both* categories. The log message implies these are disjoint ("from fingerprinting" vs "from docNumber") but they overlap. This is because `_candidate_worker` sets `from_docnumber=True` on any pair that exists in `docnum_pair_set` (line 100), even if it was found via n-gram containment.

The counts thus don't add up to `len(candidates)`:
- "from fingerprinting" = pairs with containment_score > 0 (includes those that also have from_docnumber=True)
- "from docNumber" = pairs with from_docnumber=True (includes those that also have containment_score > 0)
- docNumber-only pairs (containment_score == 0) = `sum(1 for c in candidates if c.from_docnumber and c.containment_score == 0)`

Consider: `%d from fingerprinting only, %d from docNumber only, %d from both`.

---

## Not Issues (Confirmed Correct)

1. **`stable_hash` usage:** The code correctly uses `fast_ngram_hashes` (which internally uses `zlib.crc32`) rather than Python's `hash()`. All n-gram hashing is deterministic across processes. Good.

2. **Pool initializer pattern:** Both `_candidate_init` and `_phonetic_init` set module-level globals in the child process, avoiding per-task pickling of large data structures. The `maxtasksperchild=100` prevents memory leaks. Good.

3. **Binary search prefilter:** `bisect_left` on sorted `source_lens_arr` correctly finds the first source meeting the size threshold. Since the array is sorted ascending, all entries from `lo` onward are >= `min_source_len`. Good.

4. **`_parse_docnumber_to_text_ids` leading-zero handling:** `vol_match.group(2).lstrip('0') or '0'` correctly handles "0000" -> "0". Good.

5. **Serial/parallel equivalence:** The serial path (lines 269-284) sets the same globals that `_candidate_init` sets for workers, ensuring `_candidate_worker` behaves identically. Test `test_parallel_equivalence` verifies this. Good.

6. **Thread-safety disclaimer:** Both `generate_candidates` and `generate_phonetic_candidates` document that they are not thread-safe due to module-level globals. Good.

---

## Overall Assessment

**Grade: A-**

The code is well-engineered for its purpose. The multiprocessing architecture is correct, the fingerprinting logic is efficient, and edge cases are handled thoughtfully. The P2-2 issue (phonetic containment direction) is the most significant finding -- it produces logically incorrect scores when the shorter text has a larger phonetic n-gram set. Everything else is minor or cosmetic.
