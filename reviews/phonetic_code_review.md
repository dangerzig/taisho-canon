# Code Review: `digest_detector/phonetic.py`

**Reviewer:** Claude Opus 4.6
**Date:** 2026-02-19
**File:** `/Users/danzigmond/taisho-canon/digest_detector/phonetic.py` (417 lines)
**Related files examined:** `config.py`, `align.py` (phonetic rescan), `candidates.py` (Stage 2b), `tests/test_phonetic.py`, `tests/test_phonetic_integration.py`, `tests/test_phonetic_candidates.py`, DDB dictionary

---

## Summary

The phonetic module is well-structured and demonstrates careful domain-specific engineering. The DDB dictionary parsing, syllable splitting heuristic, and multi-source transliteration region detection are thoughtfully designed. However, there are several issues worth addressing, ranging from a semantic correctness concern in how common Chinese characters contaminate the equivalence table, to minor performance and robustness issues.

**Overall grade: B+** -- Solid domain logic with a few issues that are partly mitigated by downstream safeguards but could cause subtle problems at scale.

---

## Findings

### P2-01: Common prose characters contaminate the equivalence table (Line 165-187)

**Severity: P2 (Important)**

The positional alignment heuristic (aligning CJK characters 1:1 with Sanskrit syllables) produces incorrect mappings for compound words where semantic characters are positionally aligned to phonetic syllables. For example:

- `梵天外道` (Skt. `brahmadeva`) maps `天` to `ma` and `道` to `va`
- `都史天` (Skt. `Tuṣita`) maps `天` to `ta`
- `肉色花` (Skt. `kiṁśuka`) maps `色` to `su`

As a result, 18 common Buddhist prose characters end up in the table: `無`, `一`, `大`, `佛`, `法`, `人`, `世`, `天`, `空`, `色`, `善`, `道`, `得`, `行`, `知`, `說`, `想`, `相`. This creates 4 false equivalence pairs among common characters (`大`=`天` via `ma`, `天`=`得` via `ta`, `空`=`說` via `da`, `道`=`知` via `va`).

**Downstream impact:** Partially mitigated by three safeguards: (1) `PHONETIC_SEED_LENGTH=5` requires 5 consecutive phonetic equivalences, (2) `diff_count >= 2` in `_find_phonetic_seeds` rejects near-exact matches, (3) `TRANSLITERATION_DENSITY` threshold filters in region detection. In practice, I was unable to construct a realistic prose example that triggers false positives. However, the contamination increases the table from ~540 "true" transliteration characters to 559, and the false syllable mappings could cause subtle issues with corpus-scale phonetic containment scoring in Stage 2b.

**Possible fix:** Filter entries where the Chinese compound is predominantly semantic rather than phonetic. One heuristic: require that at least half of the characters in the entry also appear in other transliteration entries (i.e., entries where the entire Chinese string is phonetic).

---

### P2-02: `_find_phonetic_seeds` has O(D * S * max_positions_per_syllable) worst-case complexity (align.py Lines 210-285, called from phonetic rescan)

**Severity: P2 (Important)**

While this function lives in `align.py`, it is the core consumer of the phonetic equivalence table. For each position in the digest, it iterates over all source positions sharing a syllable. The syllable `sa` has 38 characters mapping to it; if the source text is dense with `sa`-mapped characters, a single digest position generates hundreds or thousands of candidate positions, each requiring a character-by-character extension loop.

Benchmarking: a synthetic worst-case (100-char digest vs 1000-char source, all mapping to `sa`) took **0.9 seconds**. With real texts this is rarely triggered, but long dharani-heavy texts (T901 is ~176K chars) could hit this pathology.

**Possible fix:** Pre-filter source positions using positional bucketing or limit the number of candidate positions per digest position. Alternatively, only run `_find_phonetic_seeds` on identified transliteration regions rather than the full source text.

---

### P3-01: `_split_syllables` assigns trailing consonants ambiguously (Lines 79-95)

**Severity: P3 (Minor)**

The syllable splitting heuristic assigns coda consonants to the current syllable when the next character is also a consonant. This is a reasonable first approximation for Sanskrit phonotactics, but it can produce unexpected results:

- `gandharva` -> `["gand", "har", "va"]` (expected: `["gan", "dhar", "va"]`)
- `mantra` -> `["mant", "ra"]` (expected: `["man", "tra"]`)
- `bodhi` -> `["bod", "hi"]` (expected: `["bo", "dhi"]`)

The issue is that consonant clusters in Sanskrit often belong to the onset of the following syllable (e.g., `dh`, `tr` are onset clusters), but the heuristic greedily assigns consonants to the coda of the current syllable.

**Impact:** Low. Since both the dictionary extraction and the runtime lookup use the same splitting logic, the syllable labels are internally consistent. A character mapped to `"gand"` via one entry will still match another character mapped to `"gand"` via a different entry. The syllable strings are arbitrary labels as long as they are consistent.

**Note:** The tests in `test_phonetic.py` (lines 25-38) have the expected values matching this behavior, so the code is correct relative to its own spec.

---

### P3-02: `canonical_syllable` sorts on every call (Lines 204-218)

**Severity: P3 (Minor)**

`canonical_syllable` calls `sorted(syls)[0]` each time it is invoked. In `text_to_syllable_ngrams`, this is called once per character per region. With 559 characters in the table and regions potentially spanning thousands of characters, this is called frequently.

The syllable sets are small (max 5 elements due to `PHONETIC_MAX_SYLLABLES`), so each `sorted()` call is cheap. But a simple optimization would be to precompute `min(syls)` (or cache canonical values) during table construction.

**Impact:** Negligible in practice. The `sorted()` call on a <=5-element set is O(1) amortized. This is a style/optimization nit.

---

### P3-03: `phonetic_mapping_for_pair` requires equal-length strings (Lines 397-416)

**Severity: P3 (Minor)**

The function raises `ValueError` if the two strings have different lengths. Since phonetic seeds are found by character-by-character extension (no gaps allowed), digest and source spans always have equal length when this function is called from `_phonetic_rescan`.

However, if the function is ever called from other contexts (e.g., interactive analysis, future fuzzy phonetic extension), this constraint would be surprising. The function should at minimum document WHY equal-length is required (no gap alignment in phonetic matching), or handle the unequal case gracefully.

**Impact:** No current bug, but a documentation/API robustness concern.

---

### P3-04: `find_transliteration_regions` density detection is fragile with common chars in table (Lines 252-272)

**Severity: P3 (Minor)**

Because common prose characters like `天`, `世`, `色`, `大`, `行` are in the table (see P2-01), density-based transliteration detection can produce false regions in regular Buddhist prose. The default `TRANSLITERATION_DENSITY=0.6` and `TRANSLITERATION_WINDOW=20` thresholds help, but dense prose passages could occasionally trigger.

Tested with the Heart Sutra opening: density detection was not triggered for normal prose. But this depends on the specific distribution of common-char contamination in the table.

**Impact:** Low in practice. False regions are filtered by `MIN_TRANSLITERATION_LENGTH=10` and phonetic stopgram filtering in Stage 2b. The downstream `_find_phonetic_seeds` with `diff_count >= 2` provides additional protection.

---

### P4-01: `_normalize_sanskrit` strips ALL combining marks, not just diacritics (Lines 36-48)

**Severity: P4 (Style/nit)**

The function removes all Unicode category `Mn` (nonspacing combining marks). This is correct for IAST diacritics (macrons, dots, tildes) but could theoretically strip other combining marks if unusual Unicode sequences appear in the DDB dictionary. In practice, the DDB entries use standard IAST encoding, so this is not a real issue.

---

### P4-02: `_INDIC_DIACRITICS` set is defined at module level (Line 109)

**Severity: P4 (Style/nit)**

The set is correct and complete for IAST romanization. One observation: `ṁ` (dot above) and `ṃ` (dot below) are both included, which is correct since both conventions appear in different IAST traditions. However, `ḹ` (long syllabic l) is extremely rare in Buddhist Sanskrit -- its inclusion is harmless but slightly over-inclusive.

---

### P4-03: `build_equivalence_table` uses `get_equivalence_groups` for logging before returning (Lines 195-199)

**Severity: P4 (Style/nit)**

The logging call at line 198 invokes `get_equivalence_groups(char_to_syllables)` purely to count syllable groups for the log message. This builds the full inverse mapping just for a count. A simpler approach would be to count unique syllables directly:

```python
all_syls = set()
for syls in char_to_syllables.values():
    all_syls.update(syls)
num_groups = len(all_syls)
```

**Impact:** Negligible -- `build_equivalence_table` is called once per pipeline run.

---

### P4-04: Dictionary comprehension style in `build_equivalence_table` (Lines 183-186)

**Severity: P4 (Style/nit)**

```python
if ch not in char_to_syllables:
    char_to_syllables[ch] = set()
char_to_syllables[ch].add(syl)
```

Could be simplified to:

```python
char_to_syllables.setdefault(ch, set()).add(syl)
```

Or use `defaultdict(set)`.

---

### P4-05: `get_equivalence_groups` uses manual dict building (Lines 370-376)

**Severity: P4 (Style/nit)**

Same pattern as P4-04. Could use `defaultdict(set)` for cleaner code.

---

## Items NOT flagged (positive observations)

1. **Star (`*`) handling in `_extract_sanskrit`:** The regex `\*?` correctly strips the reconstructed-form asterisk before capturing the Sanskrit term. Verified that entries like `(Skt. *buddha)` correctly extract `buddha`.

2. **CJK range coverage in `_is_cjk`:** Covers the main CJK block (U+4E00-9FFF), Extension A (U+3400-4DBF), Extension B (U+20000-2A6DF), and CJK Compatibility Ideographs (U+F900-FAFF). This is sufficient for the CBETA corpus.

3. **`are_phonetically_equivalent` short-circuit:** The `a == b` check at line 351 correctly handles identical characters (including those filtered from the table by `PHONETIC_MAX_SYLLABLES`), which is essential for the phonetic rescan where many characters match exactly.

4. **Region merging logic:** The sort-and-merge algorithm at lines 274-284 is correct, handles adjacent regions (via `start <= merged[-1][1]`), and is efficient.

5. **Test coverage:** The three test files provide good coverage of the core functions, including edge cases (empty strings, non-table chars), integration tests with real Taisho texts, and parallel/serial equivalence verification.

6. **`PHONETIC_MAX_SYLLABLES=5` filtering:** This is a well-calibrated threshold that removes the most ambiguous characters (波=13, 羅=12, 婆=21) while retaining useful transliteration characters. The filtered characters are documented in test comments.

---

## Recommendation

The most impactful improvement would be addressing **P2-01** (common character contamination). While the downstream safeguards prevent outright false positives in the current pipeline, the contamination adds noise to phonetic containment scores and could cause issues as the pipeline is applied to larger text collections or different sub-corpora. A targeted fix -- such as filtering entries where the Chinese term is a compound of semantic + phonetic characters rather than purely phonetic -- would improve the table quality without requiring architectural changes.

**P2-02** (phonetic seed performance) is worth monitoring as the corpus grows but is not urgent for the current ~9K text corpus.

The remaining P3/P4 items are minor and can be addressed at convenience.
