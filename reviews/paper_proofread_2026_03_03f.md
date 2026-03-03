# Proofread Report (Sixth Pass): "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-03-03
**Reviewer:** Claude Opus 4.6

This is a sixth-pass proofread. All findings from the five earlier reports were verified and excluded. This report covers only **new** issues not identified in prior passes.

---

## Verification of Previous Proofread Fixes

All actionable items from the five previous proofreads were checked against the current file:

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
| 2nd M2 | "format...format" redundancy | Fixed |
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
| 4th I4 | Figure 1 label says "Catalog sources" | Fixed |
| 4th M1 | Caption says "Eight catalog sources" | Fixed |
| 5th C1 | 754 + 171 = 925 arithmetic error in footnote | Fixed (now 754 + 124 = 878) |
| 5th I1 | `\citealt` vs `\citet` inconsistency | Fixed (all now `\citet`) |

Two carry-over items from previous proofreads remain:
- "chos kyi rgya mo" Wylie form for Toh 256 (carry-over from 2nd, 3rd, 4th, and 5th proofreads; requires external verification)
- "Twelve centuries later" approximation (carry-over from 2nd, 3rd, 4th, and 5th proofreads; optional)

---

## Critical

No new critical issues found. All previous critical findings have been addressed.

---

## Important

No new important issues found.

---

## Minor

### M1. Singular "volume" should be plural "volumes" (line 1341)

**Text:**
```
texts corresponding to Taish\=o volume~30 and~32. Vasubandhu
```

**Issue:** "volume~30 and~32" refers to two volumes (30 and 32), so the noun should be plural: "volumes~30 and~32." Compare with correct plural usage elsewhere in the paper, e.g., "vols.~30--32" (line 1603), "vols.~33--44" (line 876), and "volumes~29--31" at line 1343 (just two lines later).

**Fix:** Change to:
```
texts corresponding to Taish\=o volumes~30 and~32. Vasubandhu
```

---

### M2. "chos kyi rgya mo" still unverified (CARRY-OVER from 2nd, 3rd, 4th, and 5th proofreads)

**Line 1877:**
```
12 & T12n0354 & \Toh{256} & \wy{chos kyi rgya mo} & S & \dag
```

**Issue:** Flagged in four previous proofreads. Toh 256 is traditionally identified as the *Dharmasamudra* ("Ocean of Dharma"), which in Wylie would be "chos kyi rgya mtsho" (not "rgya mo"). "rgya mo" means "great/vast" while "rgya mtsho" means "ocean." This requires external verification against rKTs or the 84000 database.

**Fix:** Verify the correct Wylie title for Toh 256. If the title is "Ocean of Dharma," correct to `\wy{chos kyi rgya mtsho}`.

---

### M3. "Twelve centuries later" approximation (CARRY-OVER from 2nd, 3rd, 4th, and 5th proofreads)

**Line 1629:**
```
distinguishing Indian from Chinese sources. Twelve centuries later,
```

**Issue:** The Denkarma dates to c. 812 CE. 2026 - 812 = 1,214 years, which is over twelve centuries. "More than twelve centuries later" would be slightly more precise.

**Fix:** Optional. Change to "More than twelve centuries later" for precision.

---

## Summary of Findings Requiring Action

| # | Severity | Line(s) | Issue | Action |
|---|----------|---------|-------|--------|
| M1 | Minor | 1341 | "volume" should be "volumes" (plural) | Fix |
| M2 | Minor | 1877 | "chos kyi rgya mo" unverified Wylie (carry-over) | Verify externally |
| M3 | Minor | 1629 | "Twelve centuries" approximation (carry-over) | Optional fix |

---

## Comprehensive Verification Summary

### Arithmetic Verification

All numbers were independently verified and found correct:

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
| 171/2455 = 6.97% -> 7.0% | Correct |
| 63.5% + 36.5% = 100.0% | Correct |
| Table 1 footnote: 754 + 124 = 878 | Correct |
| 47 Pali-also-Tibetan + 124 Pali-only = 171 | Correct |
| Scholarly table: 40 entries (1-31 Chinese-to-Tibetan, 32-40 cross-school) | Correct |
| 19 corroborated + 21 uncorroborated = 40 | Correct |
| 12 uncorroborated Chinese-to-Tibetan + 9 cross-school = 21 | Correct |
| 22 entries with both L and S | Correct |
| Lancaster errors: 5, total errors: 8 | Correct |
| 2455 - 754 = 1701 (Taisho texts without Tibetan parallels) | Correct |
| 1108 - 488 = 620 (Kangyur texts without Chinese parallels) | Correct |
| MITRA: 825 + 1401 = 2226 | Correct |
| LLM: 620 - 244 = 376; 208/376 = 55.3% | Correct |
| LLM: 376 - 208 = 168 | Correct |
| Sanskrit title matching: 101 + 130 = 231; 77/101 = 76.24% -> 76.2% | Correct |

### Cross-Reference Verification

All `\ref{}` targets verified against `\label{}` definitions:

| Reference | Target | Status |
|---|---|---|
| `\ref{sec:intro}` | Section 1 (Introduction) | Correct |
| `\ref{sec:sources}` | Section 2 (Data Sources) | Correct |
| `\ref{sec:normalization}` | Section 3.1 (ID Normalization) | Correct |
| `\ref{sec:merge}` | Section 3.2 (Source Merging) | Correct |
| `\ref{sec:agreement}` | Section 3.4 (Source Agreement) | Correct |
| `\ref{sec:classification}` | Section 3.6 (Parallel Classification) | Correct |
| `\ref{sec:chinese-tibetan}` | Section 2.1 (Chinese-to-Tibetan) | Correct |
| `\ref{sec:coverage}` | Section 4 (Coverage) | Correct |
| `\ref{sec:reliability}` | Section 5 (Source Reliability) | Correct |
| `\ref{sec:cases}` | Section 6 (Case Studies) | Correct |
| `\ref{sec:applications}` | Section 7 (Applications) | Correct |
| `\ref{sec:limitations}` | Section 8 (Limitations) | Correct |
| `\ref{sec:conclusion}` | Section 9 (Conclusion) | Correct |
| `\ref{tab:sources}` | Table 1 | Correct |
| `\ref{tab:tibetan}` | Table 2 | Correct |
| `\ref{tab:genre}` | Table 3 | Correct |
| `\ref{tab:allerrors}` | Table 4 | Correct |
| `\ref{tab:scholarly}` | Table 5 | Correct |
| `\ref{fig:pipeline}` | Figure 1 | Correct |
| `\ref{app:errors}` | Appendix A | Correct |
| `\ref{app:scholarly}` | Appendix B | Correct |

No orphaned references or missing labels.

### Citation Verification

All `\citep{}`, `\citet{}`, and `\citealp{}` calls verified against `references.bib`:

All 27 bibliography keys used in the paper are present in the bib file: `takakusu1924`, `nanjio1883`, `ui1934`, `lancaster1979`, `herrmannpfandt2008`, `akanuma1929`, `nattier1992`, `buswell1989`, `harrison2008`, `silk2019`, `li2021`, `zigmond2026a`, `zigmond2026b`, `zigmond2026c`, `suttacentral`, `cbeta_jinglu`, `rkts`, `84000`, `bdrc`, `conze1978`, `frauwallner1956`, `shimoda1997`, `lalou1953`, `kapstein2000`, `vanschaik2015`, `davidson2002`, `snellgrove1987`, `cabezon1996`, `openpecha_kangyur`, `schoch2013`, `sahle2016`, `binding2016`, `barnett2025`, `kyogoku2025`, `schwartz2025`, `engels2025`, `zurcher2007`, `braarvig1993`, `nattier2003`, `zacchetti2021`, `radich2015`, `anthropic2025`, `ishikawa1990`, `nehrdich2026`.

### Consistency Checks

| Check | Result |
|---|---|
| "Taisho" always rendered as `Taish\=o` (with macron) | Correct (no bare "Taisho") |
| "sutra" always rendered as `s\=utra` (with macron) | Correct (no bare "sutra") |
| "sutta" always in `\skt{}` (italic) | Correct |
| Em-dashes in running text | None found |
| American English | Consistent throughout (no British spellings in author's text) |
| Transliteration rule: all `\zh{}` followed by `\py{}` | Correct |
| Transliteration rule: all `\tib{}` followed by `\wy{}` | Correct |
| Table numbering | Tables 1-5, sequential, all referenced |
| Figure numbering | Figure 1, referenced |
| Section numbering | Sections 1-9 plus appendices A-B, all correctly labeled |
| "Data sources" terminology | Consistent across abstract, figure, caption, body, and conclusion |
| Scholarly source count ("six sources") | Consistent between text, pre-table description, and caption |
| Scholarly source abbreviation ordering | Consistent between pre-table text and caption |
| Scholarly table: Taisho ordering | Correct in both sections (Chinese-to-Tibetan and cross-school) |
| "721 multi-source texts" | Consistent between abstract (line 140) and body (line 688) |
| "data are" (plural verb) | Consistent across all three occurrences |

### Table Verification

**Table 1 (Sources):** 40 scholarly entries, 878 total Taisho texts, 605 Tohoku numbers. Footnote arithmetic correct (754 + 124 = 878).

**Table 2 (Tibetan Coverage):** 488 + 115 + 2 = 605. Percentages correct. Total 4,569.

**Table 3 (Genre Coverage):** All 12 rows sum correctly. All 12 percentages verified. Total 2,455 texts, 878 with parallel, 35.8%.

**Table 4 (Errors):** 8 entries. Sources (Lancaster 5, CBETA Skt 2, rKTs 1) correct.

**Table 5 (Scholarly):** 40 entries. Correctly numbered 1-40. Ordered by Taisho ID within each section. 19 corroborated, 21 uncorroborated. 22 with both L and S. Counts all verified.

---

## Overall Assessment

The paper is in excellent shape after five rounds of proofreading and extensive fixes. This sixth pass found only one new issue: a singular/plural mismatch ("volume" should be "volumes" at line 1341) when referring to two Taisho volumes. This is a minor grammatical error.

Two carry-over items from previous proofreads remain: the unverified Wylie transliteration "chos kyi rgya mo" for Toh 256 (which requires checking against rKTs or 84000), and the optional "Twelve centuries later" approximation.

All other aspects of the paper are verified clean:
- **Transliteration rule compliance:** Excellent. Every instance of CJK, Tibetan, and Devanagari script is accompanied by romanized transliteration in italics.
- **American English:** Fully consistent (no British spellings in author's text; British spellings in cited titles correctly preserved).
- **Em-dashes:** None in running text.
- **Cross-references:** All correct and using `\ref{}`.
- **Table arithmetic:** All verified correct.
- **Numbers and percentages:** All consistent between text and tables.
- **Bibliography:** All citation keys resolve to bib entries.
- **Scholarly table:** All 40 entries verified for count, ordering, source attributions, and corroboration tallies.
