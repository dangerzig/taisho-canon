# Proofread Report (Third Pass): "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-03-03
**Reviewer:** Claude Opus 4.6

This is a third-pass proofread. All findings from the two earlier reports (`reviews/paper_proofread_2026_03_03.md` and `reviews/paper_proofread_2026_03_03b.md`) were verified and excluded. This report covers only **new** issues not identified in prior passes.

---

## Verification of Previous Proofread Fixes

All actionable items from both previous proofreads have been verified:

| Previous # | Issue | Status |
|---|---|---|
| 1st C1 | Hardcoded `\S3.4` | Fixed |
| 1st C2 | 64.3% + 36.5% = 100.8% | Fixed (now 63.5% + 36.5%) |
| 1st C3 | Duplicate T12n0452 / T14n0452 | Fixed (removed, table now 40 entries) |
| 1st I4 | "nine catalog sources" | Fixed (now "nine data sources") |
| 1st M14 | Toh 897 vs Toh 691 for T20n1060 | **Fixed** (line 510 now says Toh 691) |
| 1st M15 | `\skt{}` used for Wylie text | Fixed (now `\wy{}`) |
| 1st M18 | "at least one or more" | Fixed |
| 1st M29 | "sutra" without macron | Fixed |
| 2nd C2 | 488 + 115 = 603, not 605 | See C1 below (partially addressed) |
| 2nd C3 | Explanation of uncorroborated entries | **Fixed** (text now correctly describes both groups) |
| 2nd I2 | "sutra" without macron on line 433 | Fixed |
| 2nd I3 | "sutta" not italicized on line 662 | Fixed |
| 2nd I4 | Entries 16-20 out of Taisho order | **Fixed** (table now correctly ordered) |
| 2nd M2 | "format...format" redundancy | Still present (optional, minor) |
| 2nd M8 | "Twelve centuries" approximation | Still present (optional, minor) |

Two carry-over items from the second proofread remain unverified:
- 2nd I1: "chos kyi rgya mo" Wylie form for Toh 256 (still unverified; see I1 below)
- 2nd I5: Toh 359 for T17n0784 (still unverified; noted below)

---

## Critical (factual errors, numerical inconsistencies)

### C1. "Four constituent sutras" should be "Six" (lines 751-752)

**Text:**
```
Four constituent s\=utras known to have been
translated from Chinese (\Toh{51}, \Toh{57}, \Toh{64}, \Toh{84}) are
classified as \texttt{chinese\_to\_tibetan}
```

**Issue:** The illustrative concordance entry for T11n0310 says "Four constituent sutras" are classified as `chinese_to_tibetan`, listing Toh 51, 57, 64, and 84. But the body text (line 501) identifies **six** chapters of the Maharatnakuta as Chinese-to-Tibetan translations: Toh 51, 57, 58, 61, 64, and 84. The scholarly table (Appendix B, entries 6-11) also lists all six in the "Chinese-to-Tibetan translations" section, all with both Li and Silk as sources. The omission of Toh 58 and Toh 61 from this list appears to be an error.

**Fix:** Change "Four" to "Six" and add the missing Tohoku numbers:
```
Six constituent s\=utras known to have been
translated from Chinese (\Toh{51}, \Toh{57}, \Toh{58}, \Toh{61}, \Toh{64}, \Toh{84}) are
classified as \texttt{chinese\_to\_tibetan}
```

---

### C2. "Muller and CBETA Jinglu Sanskrit sources" should be "CBETA Jinglu Sanskrit and rKTs sources" (line 1180)

**Text:**
```
Including three additional errors from the Muller and CBETA Jinglu Sanskrit sources,
Appendix~\ref{app:errors} catalogs all eight probable errors
```

**Issue:** The error table (Appendix A, Table 5) shows that the three additional errors beyond Lancaster's five are:
- Error 6: **CBETA Skt** (T31n1612, Toh 4066 -> 4059)
- Error 7: **CBETA Skt** (T31n1613, Toh 4059 -> 4066)
- Error 8: **rKTs** (T19n0945, Toh 237 -> 236)

The Muller index has no original errors in the table; its errors are all propagated from Lancaster. The text incorrectly says "Muller and CBETA Jinglu Sanskrit" when it should say "CBETA Jinglu Sanskrit and rKTs."

**Fix:** Change to:
```
Including three additional errors from the CBETA Jinglu Sanskrit and rKTs sources,
```

---

### C3. Prose implies 488 + 115 = 605, omitting the 2 out-of-range texts (lines 830-833)

**Text:**
```
The concordance identifies Tibetan parallels for 754 of 2,455
Taish\=o texts, comprising 488 of 1,108 Kangyur texts (44.0\%) and
115 of 3,461 Tengyur texts (3.3\%), for a total of 605 unique Tohoku
numbers
```

**Issue:** The word "comprising" directly links 488 and 115 to the total of 605, but 488 + 115 = 603, not 605. The difference is the 2 out-of-range Tohoku numbers (Toh 5639 and 5656), which are correctly shown in the table's "Out-of-range" row. The table arithmetic is correct (488 + 115 + 2 = 605), but the prose omits the 2 out-of-range texts, making the sentence arithmetically misleading. (This was flagged in the second proofread as C2 but the fix apparently only confirmed the table numbers were correct without adjusting the prose.)

**Fix:** Revise to acknowledge all three components:
```
The concordance identifies Tibetan parallels for 754 of 2,455
Taish\=o texts, comprising 488 of 1,108 Kangyur texts (44.0\%),
115 of 3,461 Tengyur texts (3.3\%), and 2 out-of-range entries,
for a total of 605 unique Tohoku numbers
```
Or simplify:
```
The concordance identifies Tibetan parallels for 754 of 2,455
Taish\=o texts, covering 488 of 1,108 Kangyur texts (44.0\%) and
115 of 3,461 Tengyur texts (3.3\%). In total, 605 unique Tohoku
numbers appear in the concordance
```

---

## Important (consistency, factual precision, clarity)

### I1. "chos kyi rgya mo" -- still unverified Wylie form (CARRY-OVER from second proofread)

**Line 1875:**
```
12 & T12n0354 & \Toh{256} & \wy{chos kyi rgya mo} & S & \dag
```

**Issue:** The second proofread's I1 flagged this: Toh 256 is traditionally identified as the *Dharmasamudra* ("Ocean of Dharma"), which in Wylie would be "chos kyi rgya mtsho" (not "rgya mo"). "rgya mo" means "great/vast" while "rgya mtsho" means "ocean." This remains unverified.

**Fix:** Verify the correct Wylie title for Toh 256 against rKTs or 84000 data. If it is indeed "Ocean of Dharma," correct to `\wy{chos kyi rgya mtsho}`.

---

### I2. Verbatim example shows "63 Toh entries" but text says "54 Tohoku numbers" (line 744)

**Text (verbatim block):**
```
"T11n0310": ["Otani 760,01", ..., "Toh 45", "Toh 46",
             "...(63 Toh entries)..."]
```

**Text (line 749):**
```
The 54 Tohoku numbers from catalog sources arise because...
```

**Issue:** The verbatim example says there are 63 Toh entries in the array for T11n0310, but the explanatory text says there are 54 Tohoku numbers from catalog sources. The discrepancy (63 vs. 54) is never explained. If the 63 includes Toh entries from the computational supplement (MITRA or Sanskrit title matching) in addition to the 54 from catalogs, this distinction should be noted. If the verbatim example is from the "expanded" concordance and the 54 is from the "verified" concordance, the example should clarify this.

**Fix:** Either update the verbatim comment to say "(54 Toh entries)" to match the catalog count, or add a brief note explaining the difference (e.g., "The full concordance entry includes 63 Tohoku numbers: 54 from catalog sources and 9 from computational methods").

---

### I3. Sanskrit title matching: "76.2% validation rate" arithmetic is opaque (lines 1677-1678)

**Text:**
```
A three-pass procedure ... identified 231 matches, of which 77
confirmed existing concordance entries (76.2\% validation rate) and
130 represented new proposals covering 107 unique Taish\=o texts
```

**Issue:** The sentence structure implies that 77 is 76.2% of 231, but 77/231 = 33.3%. The intended meaning appears to be: of 101 matches involving texts already in the concordance, 77 (76.2%) confirmed correctly, while the other 130 matches involved new texts. Indeed, 77/101 = 76.24% and 101 + 130 = 231. But the text's wording is ambiguous: "of which 77 confirmed" suggests 77 is the count, and the "(76.2% validation rate)" then confuses the reader because the denominator is not stated.

**Fix:** Clarify the denominator:
```
A three-pass procedure ... identified 231 matches: 101 involved texts
already in the concordance, of which 77 (76.2\%) confirmed the existing
mapping, while 130 represented new proposals covering 107 unique
Taish\=o texts not linked in any catalog source.
```

---

### I4. Entry 34 in scholarly table: T08n0228 mapped to Toh 21 (line 1900)

**Text:**
```
34 & T08n0228 & \Toh{21} & \skt{Pa\~{n}cavi\d{m}\'{s}atis\=ahasrik\=a} & N & \dag
```

**Issue:** Toh 21 in the Tohoku catalog is the *Prajnaparamitahrdaya* (Heart Sutra), not the *Pancavimsatisahasrika* (25,000-line Prajnaparamita). The Pancavimsatisahasrika is Toh 9. The identification name in the table says "Pancavimsatisahasrika" but maps to Toh 21 (Heart Sutra). This may be intentional if Nattier 1992 is being cited for the specific claim that the Heart Sutra (Toh 21) is textually related to the Pancavimsatisahasrika (T08n0228), but if so, the identification column should describe the relationship more precisely (e.g., "Heart Sutra / Pancavimsatisahasrika source") rather than implying that T08n0228 *is* the Pancavimsatisahasrika parallel of Toh 21.

**Fix:** Verify whether this entry is intended to represent Nattier's Heart Sutra derivation argument. If so, consider clarifying the identification (e.g., "Prajnaparamita source of Heart Sutra"). If the intent is to pair the Pancavimsatisahasrika with its direct Tibetan parallel, change to Toh 9.

---

## Minor (style, clarity, polish)

### M1. "Tripitaka" not italicized (lines 127, 234, 399)

**Text (line 127):**
```
Tripi\d{t}aka (``Three Baskets'')
```

**Issue:** "Tripitaka" appears three times in the paper, always rendered in roman type with diacritics. Other Sanskrit terms (Prajnaparamita, Vinaya, shastra, etc.) are consistently italicized via `\skt{}`. While "Tripitaka" is often treated as an English loanword in Buddhist studies, the paper's general practice is to italicize Sanskrit terms with IAST diacritics.

**Fix:** Optional. For consistency, consider using `\skt{Tripi\d{t}aka}` in all three instances. Alternatively, accept this as a conscious choice for a well-established English loanword.

---

### M2. "format...format" redundancy (CARRY-OVER from second proofread M2, lines 1529-1530)

**Text:**
```
\textbf{JSON} (JavaScript Object Notation, a standard structured data
format) provides a format suitable for automated querying by software:
```

**Issue:** "format" appears twice in close proximity. This was flagged in the second proofread and remains unchanged.

**Fix:** Consider: "...a standard structured data format) supports automated querying by software:" or "...a standard structured data format) is suitable for automated querying:"

---

### M3. "Twelve centuries later" approximation (CARRY-OVER from second proofread M8, line 1628)

**Text:**
```
The Denkarma's compilers organized translations by origin,
distinguishing Indian from Chinese sources. Twelve centuries later,
```

**Issue:** The Denkarma dates to c. 812 CE. 2026 - 812 = 1,214 years, which is over twelve centuries. "More than twelve centuries later" would be slightly more precise. This was flagged in the second proofread and remains unchanged.

**Fix:** Optional. Change to "More than twelve centuries later" or "Over twelve centuries later."

---

### M4. Missing paragraph break before final sentence of the LLM section (line 1729)

**Text:**
```
...not specifically trained on this material.
Quality control remains the principal bottleneck: the 244 filtered
generic matches illustrate how catalog entries with minimal
distinguishing information can inflate match counts without reflecting
genuine textual parallels.
```

**Issue:** "Quality control remains the principal bottleneck..." starts on the same line as the end of the preceding sentence, with no blank line to create a paragraph break. Given that this sentence shifts topic from the viability of LLM approaches back to quality control challenges, a paragraph break would improve readability.

**Fix:** Add a blank line before "Quality control remains..." to create a visual paragraph break.

---

### M5. Appendix B narrative says "21 (marked \dag)" but should verify against updated table (line 1913)

**Text:**
```
The remaining 21 (marked~\dag)
have no catalog corroboration.
```

**Issue:** With the table now at 40 entries and 19 corroborated, 40 - 19 = 21 uncorroborated. Counting \dag entries: Chinese-to-Tibetan (entries 6-12, 15-16, 20, 23-24 = 12) + cross-school (entries 32-40 = 9) = 21. Correct.

**Fix:** No change needed. Verified.

---

### M6. Conclusion says "nine independent catalog sources" but they are "data sources" (line 1588)

**Text:**
```
built by computationally merging nine
independent catalog sources with per-parallel provenance tracking
```

**Issue:** The first proofread (I4) flagged the distinction between "catalog sources" and "data sources," noting that the scholarly citations are not a catalog. The fix was applied at line 695 ("nine data sources"), but the conclusion at line 1588 still says "nine independent catalog sources." The scholarly citations, SuttaCentral, rKTs, and 84000 are not traditional "catalogs."

**Fix:** Change "catalog sources" to "data sources" at line 1588:
```
built by computationally merging nine
independent data sources with per-parallel provenance tracking
```

---

### M7. Abstract also says "nine independent catalog sources" (line 128-129)

**Text:**
```
compiled by computationally merging nine independent
catalog sources with per-parallel provenance tracking
```

**Issue:** Same as M6. The abstract uses "catalog sources" where "data sources" would be more accurate, since the nine include scholarly citations and digital databases that are not catalogs.

**Fix:** Change "catalog sources" to "data sources":
```
compiled by computationally merging nine independent
data sources with per-parallel provenance tracking
```

---

## Summary of Findings Requiring Action

| # | Severity | Line(s) | Issue | Action |
|---|----------|---------|-------|--------|
| C1 | Critical | 751-752 | "Four" constituent sutras should be "Six" (Toh 58, 61 missing) | Fix count and add missing Toh numbers |
| C2 | Critical | 1180 | "Muller" is wrong; should be "rKTs" | Fix source name |
| C3 | Critical | 830-833 | 488+115=603, not 605; 2 out-of-range texts omitted from prose | Revise sentence |
| I1 | Important | 1875 | "chos kyi rgya mo" still unverified (carry-over) | Verify Wylie |
| I2 | Important | 744 | "63 Toh entries" vs. "54 Tohoku numbers" unexplained | Reconcile or explain |
| I3 | Important | 1677-1678 | "76.2% validation rate" denominator unclear | Clarify |
| I4 | Important | 1900 | T08n0228 -> Toh 21 but identification says "Pancavimsatisahasrika" | Verify intent |
| M6 | Minor | 1588 | "catalog sources" should be "data sources" (conclusion) | Fix wording |
| M7 | Minor | 128-129 | "catalog sources" should be "data sources" (abstract) | Fix wording |
| M2 | Minor | 1529-1530 | "format...format" redundancy (carry-over) | Optional rephrase |
| M4 | Minor | 1729 | Missing paragraph break before quality control sentence | Add blank line |

---

## Arithmetic Verification Summary

All table arithmetic was verified and found correct:

| Check | Result |
|---|---|
| Genre table Texts sum: 45+155+597+190+72+610+87+96+68+192+159+184 | 2,455 (correct) |
| Genre table With Parallel sum: 39+131+322+82+28+229+26+9+4+5+3+0 | 878 (correct) |
| All 12 genre coverage percentages | All correct to stated precision |
| Table 2: 488+115+2 = 605 | Correct (table arithmetic ok; prose is misleading) |
| 488/1108 = 44.04% -> 44.0% | Correct |
| 115/3461 = 3.32% -> 3.3% | Correct |
| 605/4569 = 13.24% -> 13.2% | Correct |
| 878/2455 = 35.76% -> 35.8% | Correct |
| 171/2455 = 6.97% -> 7.0% | Correct |
| 63.5% + 36.5% = 100.0% | Correct |
| Scholarly table: 40 entries (1-31 Chinese-to-Tibetan, 32-40 cross-school) | Correct |
| 19 corroborated + 21 uncorroborated = 40 | Correct |
| 12 uncorroborated Chinese-to-Tibetan + 9 cross-school = 21 | Correct |
| 22 entries with both L and S | Correct |
| Lancaster errors: 5 | Correct per table |
| Total errors: 8 | Correct per table |
| 2455 - 754 = 1701 | Correct |
| 1108 - 488 = 620 | Correct |
| MITRA: 825 + 1401 = 2226 | Correct |
| LLM: 620 - 244 = 376; 376 - 208 = 168 | Correct |
| LLM: 208/376 = 55.3% | Correct |

---

## Cross-Reference Verification Summary

All `\ref{}` targets were checked against `\label{}` definitions:

| Reference | Target | Status |
|---|---|---|
| `\ref{sec:sources}` | Section 2 (Data Sources) | Correct |
| `\ref{sec:method}` | Section 3 (Merging Methodology) | Correct |
| `\ref{sec:normalization}` | Section 3.1 (ID Normalization) | Correct |
| `\ref{sec:merge}` | Section 3.2 (Source Merging) | Correct |
| `\ref{sec:agreement}` | Section 3.4 (Source Agreement) | Correct |
| `\ref{sec:classification}` | Section 3.6 (Parallel Classification) | Correct |
| `\ref{sec:coverage}` | (not used in text, only label) | N/A |
| `\ref{sec:reliability}` | Section 5 (Source Reliability) | Correct |
| `\ref{sec:cases}` | (not used in text, only label) | N/A |
| `\ref{sec:applications}` | (not used in text, only label) | N/A |
| `\ref{sec:limitations}` | Section 7 (Limitations) | Correct |
| `\ref{sec:conclusion}` | Section 8 (Conclusion) | Correct |
| `\ref{sec:chinese-tibetan}` | Section 2.1 (Chinese-to-Tibetan) | Correct |
| `\ref{tab:sources}` | Table 1 | Correct |
| `\ref{tab:tibetan}` | Table 2 | Correct |
| `\ref{tab:genre}` | Table 3 | Correct |
| `\ref{tab:allerrors}` | Table 4 (errors) | Correct |
| `\ref{tab:scholarly}` | Table 5 (scholarly) | Correct |
| `\ref{fig:pipeline}` | Figure 1 | Correct |
| `\ref{app:errors}` | Appendix A | Correct |
| `\ref{app:scholarly}` | (label exists but no \ref in text) | N/A (not an error) |

No orphaned references or missing labels detected.

---

## Overall Assessment

The paper is in very strong shape after two rounds of proofreading and fixes. The three critical findings in this third pass are:

1. **"Four constituent sutras" should be "Six"** (C1): The illustrative concordance example for T11n0310 omits Toh 58 and Toh 61 from the list of chapters classified as `chinese_to_tibetan`, contradicting both the body text (line 501, which lists six) and the scholarly table (entries 6-11, all six in the Chinese-to-Tibetan section).

2. **Wrong source name for additional errors** (C2): The text credits "Muller" for original errors when the table shows errors 6-7 are from CBETA Sanskrit and error 8 is from rKTs. Muller has no original errors; its errors are all propagated from Lancaster.

3. **Prose implies 488+115=605** (C3): The sentence structure with "comprising" suggests the total 605 is the sum of 488 and 115, but the actual sum is 603. The 2 out-of-range texts (correctly shown in the table) are omitted from the prose.

The remaining issues are either carry-over items requiring external verification (the Wylie title for Toh 256) or minor clarity and consistency improvements.

Transliteration rule compliance: Excellent throughout. Every CJK, Tibetan, and Devanagari script instance has accompanying transliteration.
American English: Fully consistent (no British spellings in author's text).
Em-dashes: None in running text.
Cross-references: All correct.
Table arithmetic: All verified correct.
