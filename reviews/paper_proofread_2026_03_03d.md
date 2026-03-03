# Proofread Report (Fourth Pass): "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-03-03
**Reviewer:** Claude Opus 4.6

This is a fourth-pass proofread. All findings from the three earlier reports were verified and excluded. This report covers only **new** issues not identified in prior passes.

---

## Verification of Previous Proofread Fixes

All actionable items from the three previous proofreads were checked against the current file:

| Previous # | Issue | Status |
|---|---|---|
| 1st C1 | Hardcoded `\S3.4` | Fixed |
| 1st C2 | 64.3% + 36.5% = 100.8% | Fixed (now 63.5% + 36.5%) |
| 1st C3 | Duplicate T12n0452 / T14n0452 | Fixed (removed, table now 40 entries) |
| 1st I4 | "nine catalog sources" | Fixed (now "nine data sources") |
| 1st M14 | Toh 897 vs Toh 691 for T20n1060 | Fixed (line 510 now says Toh 691) |
| 1st M15 | `\skt{}` used for Wylie text | Fixed (now `\wy{}`) |
| 1st M18 | "at least one or more" | Fixed |
| 1st M29 | "sutra" without macron | Fixed |
| 2nd C2 | 488 + 115 = 603, not 605 | Fixed (prose restructured, no longer implies sum) |
| 2nd C3 | Explanation of uncorroborated entries | Fixed |
| 2nd I2 | "sutra" without macron on line 433 | Fixed |
| 2nd I3 | "sutta" not italicized on line 662 | Fixed |
| 2nd I4 | Entries 16-20 out of Taisho order | Fixed |
| 3rd C1 | "Four constituent sutras" should be "Six" | Fixed (now "Six" with all six Toh numbers) |
| 3rd C2 | "Muller" wrong source name for errors | Fixed (now "CBETA Jinglu Sanskrit and rKTs") |
| 3rd C3 | Prose implies 488+115=605 | Fixed (now uses "covering...In total" structure) |
| 3rd I2 | "63 Toh entries" vs "54 Tohoku numbers" | Fixed (verbatim now says "54") |
| 3rd I3 | "76.2% validation rate" denominator unclear | Fixed (sentence restructured to show 101 as base) |
| 3rd I4 | T08n0228/Toh 21 identification | Fixed (now "Hrdaya source text") |
| 3rd M6 | "catalog sources" in conclusion | Fixed (now "data sources") |
| 3rd M7 | "catalog sources" in abstract | Fixed (now "data sources") |

Two carry-over items from previous proofreads remain:
- "chos kyi rgya mo" Wylie form for Toh 256 (carry-over from 2nd and 3rd proofreads; requires external verification)
- "Twelve centuries later" approximation (carry-over from 2nd and 3rd proofreads; optional)

---

## Critical

No critical issues found. All previous critical findings have been addressed.

---

## Important

### I1. "Three sources" should be "six sources" (line 1839)

**Text:**
```
These 40 entries from three sources provide independent scholarly attestation for
parallels.
```

**Issue:** The text says "three sources," but the table and its legend list six distinct scholarly sources: L (Li 2021), S (Silk 2019), C (Conze 1978), F (Frauwallner 1956), N (Nattier 1992), and Sh (Shimoda 1997). The six abbreviations are defined three lines later (lines 1842-1844), directly contradicting the "three sources" claim. This likely reflects an earlier version of the table that used only three scholars, and the count was never updated when Frauwallner, Nattier, and Shimoda were added.

**Fix:** Change "three sources" to "six sources":
```
These 40 entries from six sources provide independent scholarly attestation for
parallels.
```

---

### I2. Inconsistent ordering of scholarly source abbreviations between pre-table text and table caption

**Lines 1842-1843 (pre-table text):**
```
L~=~Li 2021, S~=~Silk 2019, C~=~Conze 1978, F~=~Frauwallner 1956,
N~=~Nattier 1992, Sh~=~Shimoda 1997.
```

**Lines 1852-1853 (table caption):**
```
L~=~Li 2021, S~=~Silk 2019, C~=~Conze 1978,
N~=~Nattier 1992, Sh~=~Shimoda 1997, F~=~Frauwallner 1956.
```

**Issue:** The pre-table text lists the abbreviations in the order L, S, C, F, N, Sh, while the table caption lists them as L, S, C, N, Sh, F. The two orderings disagree on the placement of F (Frauwallner).

**Fix:** Standardize to one order. Alphabetical by abbreviation (C, F, L, N, S, Sh) or chronological by publication year (F 1956, C 1978, N 1992, Sh 1997, S 2019, L 2021) would both be natural. Or simply list the two primary sources first (L, S) then the remainder in alphabetical order in both locations.

---

### I3. Body text at line 463-468 omits Shimoda as a scholarly source

**Text (lines 463-468):**
```
Published identifications from specialist
scholarship, drawn from \citet{li2021}'s survey of Chinese s\=utras in
Tibetan translation, \citet{silk2019}'s study of Chinese-to-Tibetan
transmission, and standard parallel identifications from comparative
Buddhist textual scholarship citing \citet{conze1978},
\citet{frauwallner1956}, and \citet{nattier1992}.
```

**Issue:** This paragraph lists five scholars (Li, Silk, Conze, Frauwallner, Nattier) but omits Shimoda 1997, who appears as source "Sh" in the scholarly table (entry 35: T12n0375 -> Toh 119). A reader relying on this paragraph would not expect a sixth source in the table.

**Fix:** Add Shimoda to the list:
```
...and standard parallel identifications from comparative
Buddhist textual scholarship citing \citet{conze1978},
\citet{frauwallner1956}, \citet{nattier1992}, and \citet{shimoda1997}.
```

---

### I4. Figure 1 group box label says "Catalog sources" while paper text says "data sources" (line 590)

**Text:**
```
{Catalog sources (\S\ref{sec:sources})};
```

**Issue:** The body text consistently uses "data sources" (lines 129, 307, 695, 1589), but the Figure 1 group box label still says "Catalog sources." This was flagged in the first proofread (M11) as a suggestion, and the abstract/conclusion were subsequently fixed to "data sources" (third proofread M6, M7), but the figure was not updated to match. Since the dashed box contains SuttaCentral and rKTs (which are not traditional catalogs), "Data sources" would be more accurate and consistent with the rest of the paper.

**Fix:** Change line 590 from "Catalog sources" to "Data sources":
```
{Data sources (\S\ref{sec:sources})};
```

---

## Minor

### M1. Figure 1 caption says "Eight catalog sources" (line 626)

**Text:**
```
\caption{Concordance construction pipeline. Eight catalog sources and
  published scholarly citations (\S\ref{sec:sources})...}
```

**Issue:** Same terminology issue as I4. The caption says "Eight catalog sources" while the paper's preferred term is now "data sources." SuttaCentral, rKTs, and 84000 are expert-curated digital databases, not traditional catalogs.

**Fix:** Change "Eight catalog sources" to "Eight data sources":
```
\caption{Concordance construction pipeline. Eight data sources and
  published scholarly citations (\S\ref{sec:sources})...}
```

---

### M2. "chos kyi rgya mo" still unverified (CARRY-OVER from 2nd and 3rd proofreads)

**Line 1876:**
```
12 & T12n0354 & \Toh{256} & \wy{chos kyi rgya mo} & S & \dag
```

**Issue:** This has been flagged in two previous proofreads. Toh 256 is traditionally identified as the *Dharmasamudra* ("Ocean of Dharma"), which in Wylie would be "chos kyi rgya mtsho" (not "rgya mo"). "rgya mo" means "great/vast" while "rgya mtsho" means "ocean." This requires external verification against rKTs or the 84000 database.

**Fix:** Verify the correct Wylie title for Toh 256. If the title is "Ocean of Dharma," correct to `\wy{chos kyi rgya mtsho}`.

---

### M3. "Twelve centuries later" approximation (CARRY-OVER from 2nd and 3rd proofreads)

**Line 1628:**
```
Twelve centuries later,
```

**Issue:** The Denkarma dates to c. 812 CE. 2026 - 812 = 1,214 years, which is over twelve centuries. "More than twelve centuries later" would be slightly more precise. This has been flagged as optional in two previous proofreads.

**Fix:** Optional. Change to "More than twelve centuries later" for precision.

---

## Arithmetic Verification

All numbers were independently verified:

| Check | Result |
|---|---|
| Genre table Texts sum: 45+155+597+190+72+610+87+96+68+192+159+184 | 2,455 (correct) |
| Genre table With Parallel sum: 39+131+322+82+28+229+26+9+4+5+3+0 | 878 (correct) |
| All 12 genre coverage percentages | All correct to stated precision |
| Table 2: 488+115+2 = 605 | Correct (prose no longer implies 488+115=605) |
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
| Lancaster errors: 5, total errors: 8 | Correct per table |
| 2455 - 754 = 1701 | Correct |
| 1108 - 488 = 620 | Correct |
| MITRA: 825 + 1401 = 2226 | Correct |
| LLM: 620 - 244 = 376; 208/376 = 55.3% | Correct |
| LLM: 376 - 208 = 168 | Correct |
| Sanskrit title matching: 101 + 130 = 231; 77/101 = 76.24% -> 76.2% | Correct |

---

## Cross-Reference Verification

All `\ref{}` targets verified against `\label{}` definitions. No orphaned references or missing labels.

---

## Consistency Checks

| Check | Result |
|---|---|
| "Taisho" always rendered as `Taish\=o` (with macron) | Correct (no bare "Taisho") |
| "sutra" always rendered as `s\=utra` (with macron) | Correct (no bare "sutra") |
| Em-dashes | None found |
| American English | Consistent throughout (no British spellings in author's text) |
| Transliteration rule | All CJK, Tibetan, and Devanagari script accompanied by romanization |
| Table numbering | Tables 1-5, sequential, all referenced |
| Figure numbering | Figure 1, referenced |
| Section numbering | Sections 1-8 plus appendices A-B, all correctly labeled |
| "Catalog sources" vs "data sources" | Fixed in abstract, body, and conclusion; still says "Catalog" in Figure 1 (see I4, M1) |

---

## Summary of Findings Requiring Action

| # | Severity | Line(s) | Issue | Action |
|---|----------|---------|-------|--------|
| I1 | Important | 1839 | "three sources" should be "six sources" | Fix count |
| I2 | Important | 1842-1843, 1852-1853 | Inconsistent ordering of source abbreviations | Standardize order |
| I3 | Important | 463-468 | Shimoda 1997 omitted from scholarly sources paragraph | Add citation |
| I4 | Important | 590 | Figure 1 label says "Catalog sources" instead of "Data sources" | Fix wording |
| M1 | Minor | 626 | Caption says "Eight catalog sources" | Change to "data sources" |
| M2 | Minor | 1876 | "chos kyi rgya mo" unverified Wylie (carry-over) | Verify externally |
| M3 | Minor | 1628 | "Twelve centuries" approximation (carry-over) | Optional fix |

---

## Overall Assessment

The paper is in excellent shape after three rounds of proofreading. All previous critical findings have been addressed. The most significant new finding is that the scholarly appendix says "three sources" (line 1839) when there are actually six distinct scholarly sources listed immediately below. This appears to be a vestige from an earlier version of the table. The related issue of Shimoda 1997 being absent from the body text's enumeration of scholarly sources (line 463-468) should also be addressed for consistency.

The remaining findings are the "Catalog sources" vs "Data sources" inconsistency in Figure 1 (which was noted as optional in the first proofread but has become more pressing now that the abstract, body, and conclusion all say "data sources"), the source abbreviation ordering inconsistency in the scholarly appendix, and two carry-over items requiring external verification.

Transliteration rule compliance: Excellent throughout.
American English: Fully consistent.
Em-dashes: None.
Cross-references: All correct.
Table arithmetic: All verified correct.
Numbers and percentages: All consistent between text and tables.
