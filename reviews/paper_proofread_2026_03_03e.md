# Proofread Report (Fifth Pass): "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-03-03
**Reviewer:** Claude Opus 4.6

This is a fifth-pass proofread. All findings from the four earlier reports were verified and excluded. This report covers only **new** issues not identified in prior passes.

---

## Verification of Previous Proofread Fixes

All actionable items from the four previous proofreads were checked against the current file:

| Previous # | Issue | Status |
|---|---|---|
| 1st C1 | Hardcoded `\S3.4` | Fixed |
| 1st C2 | 64.3% + 36.5% = 100.8% | Fixed |
| 1st C3 | Duplicate T12n0452 / T14n0452 | Fixed |
| 1st I4 | "nine catalog sources" | Fixed |
| 1st M14 | Toh 897 vs Toh 691 for T20n1060 | Fixed |
| 1st M15 | `\skt{}` used for Wylie text | Fixed |
| 1st M18 | "at least one or more" | Fixed |
| 1st M29 | "sutra" without macron | Fixed |
| 2nd C2 | 488 + 115 = 603, not 605 | Fixed (prose restructured) |
| 2nd C3 | Explanation of uncorroborated entries | Fixed |
| 2nd I2 | "sutra" without macron on line 433 | Fixed |
| 2nd I3 | "sutta" not italicized on line 662 | Fixed |
| 2nd I4 | Entries 16-20 out of Taisho order | Fixed |
| 2nd M2 | "format...format" redundancy | Fixed (now "is suitable for") |
| 3rd C1 | "Four constituent sutras" should be "Six" | Fixed |
| 3rd C2 | "Muller" wrong source name for errors | Fixed |
| 3rd C3 | Prose implies 488+115=605 | Fixed |
| 3rd I2 | "63 Toh entries" vs "54 Tohoku numbers" | Fixed |
| 3rd I3 | "76.2% validation rate" denominator unclear | Fixed |
| 3rd I4 | T08n0228/Toh 21 identification | Fixed |
| 3rd M6 | "catalog sources" in conclusion | Fixed |
| 3rd M7 | "catalog sources" in abstract | Fixed |
| 4th I1 | "three sources" should be "six sources" | Fixed |
| 4th I2 | Inconsistent ordering of source abbreviations | Fixed |
| 4th I3 | Shimoda 1997 omitted from scholarly sources paragraph | Fixed |
| 4th I4 | Figure 1 label says "Catalog sources" | Fixed (now "Data sources") |
| 4th M1 | Caption says "Eight catalog sources" | Fixed (now "data sources") |

Two carry-over items from previous proofreads remain:
- "chos kyi rgya mo" Wylie form for Toh 256 (carry-over from 2nd, 3rd, and 4th proofreads; requires external verification)
- "Twelve centuries later" approximation (carry-over from 2nd, 3rd, and 4th proofreads; optional)

---

## Critical (factual errors, numerical inconsistencies)

### C1. Table 1 footnote: 754 + 171 = 925, not 878 (lines 354-362)

**Text:**
```
The 878 Taisho total comprises 754 texts with Tibetan
parallels (some also with Pali connections) and 171 with Pali
parallels only.
```

**Issue:** The footnote states that 878 = 754 + 171, but 754 + 171 = 925, not 878. The actual arithmetic is: 878 total texts with any parallel minus 754 texts with Tibetan parallels = 124 texts with Pali parallels only. The "171" figure is the total number of Taisho texts with Pali parallels from SuttaCentral (as shown in Table 1, line 342), but 47 of those 171 also have Tibetan parallels from other sources and are already counted among the 754. The footnote incorrectly uses 171 as the "Pali parallels only" count when it should be 124 (= 878 - 754).

**Fix:** Change "171 with Pali parallels only" to "124 with Pali parallels only":
```
The 878 Taisho total comprises 754 texts with Tibetan
parallels (some also with Pali connections) and 124 with Pali
parallels only.
```

Or, if keeping the 171 figure is preferred for transparency, rephrase to avoid the arithmetic error:
```
The 878 Taisho total includes 754 texts with Tibetan
parallels (some also with Pali connections); separately,
171 texts have Pali parallels, of which 47 also have
Tibetan parallels.
```

This also affects the later sentence in the same footnote (lines 360-362):
```
because 171 of the 878 texts have only Pali (not Tibetan) parallels
and therefore contribute no Tohoku numbers.
```
This should likewise read "124 of the 878 texts" if the correction above is adopted.

---

## Important (consistency, clarity)

### I1. `\citealt` vs `\citet` inconsistency in scholarly abbreviation definitions (lines 1842-1844 vs 1852-1853)

**Pre-table text (lines 1842-1844):**
```
L~=~\citealt{li2021}, S~=~\citealt{silk2019},
C~=~\citealt{conze1978}, F~=~\citealt{frauwallner1956},
N~=~\citealt{nattier1992}, Sh~=~\citealt{shimoda1997}.
```

**Table caption (lines 1852-1853):**
```
L~=~\citet{li2021}, S~=~\citet{silk2019}, C~=~\citet{conze1978},
F~=~\citet{frauwallner1956}, N~=~\citet{nattier1992}, Sh~=~\citet{shimoda1997}.
```

**Issue:** The pre-table text uses `\citealt` (producing "Li 2021" without parentheses) while the table caption uses `\citet` (producing "Li (2021)" with parenthetical year). Both define the same abbreviations within a few lines of each other, and the inconsistent formatting is visible to the reader.

**Fix:** Standardize both to the same citation command. `\citealt` is more natural for abbreviation definitions (L = Li 2021), since the parenthetical year in `\citet` output is somewhat redundant when the year is the main identifying information. Change lines 1852-1853 to use `\citealt`:
```
L~=~\citealt{li2021}, S~=~\citealt{silk2019}, C~=~\citealt{conze1978},
F~=~\citealt{frauwallner1956}, N~=~\citealt{nattier1992}, Sh~=~\citealt{shimoda1997}.
```

---

### I2. "chos kyi rgya mo" still unverified (CARRY-OVER from 2nd, 3rd, and 4th proofreads)

**Line 1876:**
```
12 & T12n0354 & \Toh{256} & \wy{chos kyi rgya mo} & S & \dag
```

**Issue:** Flagged in three previous proofreads. Toh 256 is traditionally identified as the *Dharmasamudra* ("Ocean of Dharma"), which in Wylie would be "chos kyi rgya mtsho" (not "rgya mo"). "rgya mo" means "great/vast" while "rgya mtsho" means "ocean." This requires external verification against rKTs or the 84000 database.

**Fix:** Verify the correct Wylie title for Toh 256 against rKTs or 84000. If the title is "Ocean of Dharma," correct to `\wy{chos kyi rgya mtsho}`.

---

## Minor (style, polish)

### M1. "Twelve centuries later" approximation (CARRY-OVER from 2nd, 3rd, and 4th proofreads)

**Line 1628:**
```
Twelve centuries later,
```

**Issue:** The Denkarma dates to c. 812 CE. 2026 - 812 = 1,214 years, which is over twelve centuries. "More than twelve centuries later" would be slightly more precise. This has been flagged as optional in three previous proofreads.

**Fix:** Optional. Change to "More than twelve centuries later" for precision.

---

### M2. Redundant definition of JSON (lines 309 and 1529)

**Line 309 (footnote):**
```
JavaScript Object Notation, a lightweight data format
readable by both humans and software, widely used in web applications
and digital humanities.
```

**Line 1529:**
```
\textbf{JSON} (JavaScript Object Notation, a standard structured data
format) is suitable for automated querying by software:
```

**Issue:** JSON is defined in a footnote at its first mention (line 309) and then again parenthetically at line 1529 in Section 7. While the two descriptions are slightly different ("lightweight data format readable by both humans and software" vs. "standard structured data format"), defining the same acronym twice in the same paper is mildly redundant. A humanities reader reaching Section 7 will have already encountered the definition.

**Fix:** Optional. Consider shortening the second definition: `\textbf{JSON} is suitable for automated querying by software:` (dropping the parenthetical redefinition, since it was already explained). Alternatively, accept the redundancy as helpful for readers who skip to Section 7.

---

## Arithmetic Verification Summary

All numbers were independently verified:

| Check | Result |
|---|---|
| Genre table Texts sum: 45+155+597+190+72+610+87+96+68+192+159+184 | 2,455 (correct) |
| Genre table With Parallel sum: 39+131+322+82+28+229+26+9+4+5+3+0 | 878 (correct) |
| All 12 genre coverage percentages | All correct to stated precision |
| Table 2: 488+115+2 = 605 | Correct |
| 488/1108 = 44.04% -> 44.0% | Correct |
| 115/3461 = 3.32% -> 3.3% | Correct |
| 605/4569 = 13.24% -> 13.2% | Correct |
| 878/2455 = 35.76% -> 35.8% | Correct |
| 63.5% + 36.5% = 100.0% | Correct |
| Table 1 footnote: 754 + 171 = 925, not 878 | **ERROR** (see C1) |
| 878 - 754 = 124 (Pali-only texts) | Should replace "171" in footnote |
| Scholarly table: 40 entries (1-31 Chinese-to-Tibetan, 32-40 cross-school) | Correct |
| 19 corroborated + 21 uncorroborated = 40 | Correct |
| 12 uncorroborated Chinese-to-Tibetan + 9 cross-school = 21 | Correct |
| 22 entries with both L and S | Correct |
| Lancaster errors: 5, total errors: 8 | Correct |
| 2455 - 754 = 1701 | Correct |
| 1108 - 488 = 620 | Correct |
| MITRA: 825 + 1401 = 2226 | Correct |
| LLM: 620 - 244 = 376; 208/376 = 55.3% | Correct |
| LLM: 376 - 208 = 168 | Correct |
| Sanskrit title matching: 101 + 130 = 231; 77/101 = 76.24% -> 76.2% | Correct |
| 171/2455 = 6.97% -> 7.0% | Correct |

---

## Cross-Reference Verification

All `\ref{}` targets verified against `\label{}` definitions. No orphaned references or missing labels.

---

## Consistency Checks

| Check | Result |
|---|---|
| "Taisho" always rendered as `Taish\=o` (with macron) | Correct |
| "sutra" always rendered as `s\=utra` (with macron) | Correct |
| Em-dashes in running text | None found |
| American English | Consistent throughout |
| Transliteration rule | All CJK, Tibetan, and Devanagari script accompanied by romanization |
| Table numbering | Tables 1-5, sequential, all referenced |
| Figure numbering | Figure 1, referenced |
| Section numbering | Sections 1-8 plus appendices A-B, all correctly labeled |
| "Data sources" vs "catalog sources" | Consistent: abstract, figure, caption, body, and conclusion all say "data sources" |
| Scholarly table ordering (by Taisho ID) | Correct in both sections |
| Scholarly source abbreviation ordering | Consistent between pre-table text and caption (L, S, C, F, N, Sh) |

---

## Summary of Findings Requiring Action

| # | Severity | Line(s) | Issue | Action |
|---|----------|---------|-------|--------|
| C1 | Critical | 354-362 | 754 + 171 = 925, not 878; "171 with Pali parallels only" should be 124 | Fix arithmetic in footnote |
| I1 | Important | 1842-1853 | `\citealt` vs `\citet` inconsistency in abbreviation definitions | Standardize |
| I2 | Important | 1876 | "chos kyi rgya mo" unverified Wylie (carry-over) | Verify externally |
| M1 | Minor | 1628 | "Twelve centuries" approximation (carry-over) | Optional fix |
| M2 | Minor | 309, 1529 | JSON defined twice | Optional simplification |

---

## Overall Assessment

The paper is in excellent shape after four rounds of proofreading. All previous critical and important findings have been addressed. This fifth pass found one new critical issue: the Table 1 footnote contains an arithmetic error where it states that 878 = 754 + 171, but 754 + 171 = 925 (the correct Pali-only count is 124, not 171; the 171 figure is the total SuttaCentral contribution, not the Pali-only subset). This error is in a footnote explaining the table totals and could confuse careful readers who check the arithmetic.

The remaining findings are a citation command inconsistency (`\citealt` vs `\citet` in the scholarly appendix abbreviation definitions), a JSON redefinition, and two carry-over items from previous proofreads.

Transliteration rule compliance: Excellent throughout. Every CJK, Tibetan, and Devanagari script instance has accompanying romanized transliteration.
American English: Fully consistent (no British spellings in author's text).
Em-dashes: None in running text.
Cross-references: All correct and using `\ref{}`.
Table arithmetic: All verified correct except the footnote issue (C1).
Numbers and percentages: All consistent between text and tables.
Scholarly table: All 40 entries verified for count, ordering, source attributions, and corroboration tallies.
