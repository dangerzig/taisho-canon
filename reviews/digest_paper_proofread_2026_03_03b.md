# Proofread: Computational Detection of Text Reuse in the Chinese Buddhist Canon

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-digest-detection/zigmond-digest-detection.tex`
**Date:** 2026-03-03
**Reviewer:** Claude (Opus 4.6)

---

## Summary

The paper is in strong shape overall. The writing is clear, the structure is logical, the citations are properly formed, and the vast majority of numbers are accurately reported. I found no instances of "we/our," no em-dashes in running text, and no British spellings. All cross-references resolve to valid \label targets. All citation keys match entries in `references.bib`.

Below I list every issue found, organized by severity.

---

## Critical Issues (Factual Errors)

### 1. T85n2783 title has wrong Chinese characters (line 949)

**Paper says:** `\zh{大乘道嵱經隨聽疏決}`
**Should be:** `\zh{大乘稻芉經隨聽疏決}`

The CBETA XML file (`xml/T/T85/T85n2783_001.xml`) and `results/summary.md` both confirm the title is 大乘稻芉經隨聽疏決 (with 稻芉, not 道嵱). The characters are visually similar but distinct.

### 2. Phonetic match numbers are stale (line 1067)

**Paper says:** "268 text pairs containing 1,021 individual phonetic match segments"
**Source data says:** 270 pairs with phonetic matches, 990 total phonetic match segments

Both numbers are off. `results/summary.md` (dated Feb 27, the most recent pipeline run) clearly reports 270 and 990.

### 3. T21n1336 derivative count is wrong (line 908)

**Paper says:** "17 shorter texts were found to be excerpts, digests, or retranslations"
**Source data says:** 16 derivatives listed under T21n1336 in `results/summary.md`

Table 4 (line 812) correctly says 16. The running text at line 908 says 17. These are inconsistent, and 16 is the correct number.

### 4. T18n0901 derivative count is wrong (line 911-912)

**Paper says:** "serves as a source for 16 shorter ritual and dharani texts"
**Source data says:** 13 derivatives listed under T18n0901 in `results/summary.md`

Table 4 (line 813) correctly says 13. The running text at line 911 says 16. These are inconsistent, and 13 is the correct number.

### 5. T17n0724 coverage is slightly wrong (line 856)

**Paper says:** 84.4%
**Source data says:** 84.3%

In `results/summary.md`: "T17n0724 (佛說罪業應報教化地獄經): excerpt, coverage=84.3%"

### 6. T48n2014 (永嘉證道歌) coverage is slightly wrong (line 1002)

**Paper says:** "matches at 99.2%"
**Source data says:** 99.1%

In `results/summary.md`: "T48n2014 (永嘉證道歌): excerpt, coverage=99.1%"

---

## Moderate Issues (Ordering, Consistency, Convention)

### 7. Absorption table (Table 5) has two entries out of order (lines 867-868)

T51n2082 (65.3%) is listed before T14n0506 (65.5%). Since the table caption says "by coverage," the 65.5% entry should come first. The current ordering has a descending-order violation.

### 8. "CJK" appears in running text (lines 362, 372)

Line 362: "extracting CJK text content"
Line 372: "texts shorter than 20 CJK characters"

Per the user's convention, running prose should say "Chinese" rather than "CJK." The term "CJK" is a technical computing abbreviation appropriate in code or parameter descriptions but not in humanistic prose. (The occurrences in lines 26-28 are in LaTeX preamble comments, which are fine.)

### 9. Retranslation validation statistics may need re-verification (lines 1114-1118)

The paper claims: 88 confirmed out of 94 pairs where both texts have Tibetan data (93.6%). The `cross_reference_analysis.json` (dated Feb 17) shows different numbers: 87 validated, 7 unconfirmed (94 total, 92.6% rate). However, this file predates the more recent pipeline run (Feb 27), so the paper's numbers may be from a more current analysis not captured in that JSON file. Recommend re-running or re-verifying the retranslation validation calculation to confirm 88/94 = 93.6%.

### 10. Concordance coverage claim may need verification (line 1110)

The paper says the concordance covers "878 Taisho texts with Tibetan and/or Pali parallels." The MEMORY.md records show: 838 Tibetan, 171 Pali, 1,082 any parallel (expanded). The number 878 does not appear in any recorded statistic. It could be 838 Tibetan + some Pali-only texts, but this number should be verified against the current concordance data.

### 11. Unused bibliography entries

The following 12 entries in `references.bib` are never cited in the paper and will not appear in the compiled bibliography (which is correct behavior for biblatex without \nocite):

- lancaster1979
- nanjio1883
- ui1934
- akanuma1929
- hackett2013
- herrmannpfandt2008
- rkts
- 84000
- copp2014
- silk2019
- buswell2014
- tokuno1990

This is not an error, but cleaning the .bib file of unused entries is good practice.

---

## Minor Issues (Style, Grammar, Formatting)

### 12. Unicode "Sūtras" instead of LaTeX-encoded macron (lines 828, 831)

Lines 828 and 831 use the Unicode character "ū" directly in "Sūtras" and "Sūtras" inside English translation quotes, rather than the LaTeX-encoded `s\=utra` used everywhere else. While this may compile correctly under XeLaTeX, it is inconsistent with the rest of the paper, which uses `\=u` throughout.

Affected lines:
- Line 828: `(``Illustrations of the Sūtras and Vinaya,'' T53n2121)`
- Line 831: `(``Essential Collection from the Sūtras,'' T54n2123)`

Suggest changing to: `S\=utras`

### 13. Comma splice / weak punctuation (line 112)

"the detection of a 28.6-percentage-point gap between same-translator and cross-translator matching, a computational signature of translator individuality previously described only qualitatively."

The comma before "a computational signature" creates a potentially ambiguous reading. A colon would be clearer: "...cross-translator matching: a computational signature of..."

### 14. Vinaya section lacks Chinese characters for T22n1428 (line 921)

"The Four-Part Vinaya (T22n1428, \skt{Dharmaguptaka})" does not include the Chinese title 四分律 with pinyin, which was introduced in Table 4. Per the transliteration convention, every reference to a text should include the Chinese with romanization. The same issue applies to T22n1431, T22n1434, T22n1429 on lines 922-924, and T23n1442-1443 on line 925.

### 15. First use of 法苑珠林 in the abstract (line 107-108) provides English translation, but some later first uses of other texts do not

Most texts get their English translation at first use (e.g., 經律異相 at line 828, 諸經要集 at line 831). However, a few texts introduced later in the paper lack English translations at first use:
- T48n2012A (黃檗山斷際禪師傳心法要, line 1003): English translation IS provided. OK.
- T47n1991, T47n1989, T47n1990, T47n1986B, T47n1986A (lines 1006): No English titles or translations provided, just Taisho numbers. These are minor, as the texts are only listed in passing.

### 16. Bamman 2008 publisher may be incorrect

The bib entry says `publisher = {Association for Computational Linguistics}`, but the LaTeCH 2008 workshop was held at LREC (European Language Resources Association), not ACL. Later LaTeCH workshops were ACL-affiliated, but the 2008 edition was at LREC in Marrakech. Consider changing to `publisher = {European Language Resources Association}` or removing the publisher field and using `organization`.

### 17. Silk 1994 entry type

The bib entry uses `@incollection` with pages 1-144, but the work is a standalone monograph (xi + 204 pages) in the Wiener Studien series, not a chapter in an edited volume. The type should arguably be `@book` or `@monograph`.

### 18. GitHub URL username (line 1394)

The URL is `https://github.com/dangerzig/taisho-canon`. Please verify that "dangerzig" is the intended GitHub username. (The placeholder note "[to be released on acceptance]" is fine.)

### 19. Line 290: bioinformatics citation

"a seed-and-extend alignment strategy borrowed from bioinformatics \parencite[cf.][]{smith2015}" cites Smith, Cordell, and Mullen (2015), who worked on newspaper reprinting, not bioinformatics. The seed-and-extend strategy originates from BLAST (Altschul et al., 1990) in bioinformatics. Either cite the bioinformatics origin directly or rephrase to avoid attributing it to Smith et al.

---

## Arithmetic Verification

All of the following were verified and found correct:

| Claim | Verification |
|-------|-------------|
| 3,610 total relationships | 136+538+538+224+2174 = 3,610 |
| 60.2% shared tradition | 2174/3610 = 60.22% |
| 14.9% digest | 538/3610 = 14.90% |
| 14.9% commentary | 538/3610 = 14.90% |
| 6.2% retranslation | 224/3610 = 6.20% |
| 3.8% excerpt | 136/3610 = 3.77% |
| Percentages sum to 100% | 60.2+14.9+14.9+6.2+3.8 = 100.0% |
| 1,436 higher-confidence | 3610-2174 = 1,436 |
| 63% of corpus | 1558/2455 = 63.5% |
| 28.6 pp gap | 73.2-44.6 = 28.6 |
| 26.9% novel fraction | 1-0.7315 = 0.2685 = 26.85% |
| T250 coverage 73.2% | 0.7315 rounds to 73.2% (or 73.1%) |
| T251 coverage 44.6% | 0.4462 rounds to 44.6% |
| T250: 8 source regions | Confirmed from validation.md |
| T250: 156 char longest segment | Confirmed from validation.md |
| 11/102 = 10.8% excerpts | Correct |
| 91/102 = 89.2% digests | Correct (89.2%) |
| 88/94 = 93.6% validation | Correct arithmetic (but see issue #9) |
| 6/94 = 6.4% unconfirmed | Correct |
| 94/224 = 42% | Correct (41.96%) |
| 130/224 = 58% | Correct (58.04%) |
| Total runtime ~54 min | 19s+23min+36s+30min+<1s+8s = ~54 min |
| Stages 2+3 >99% of runtime | (23*60+36+30*60)/3244 = 99.1% |
| Stages 1+4+5 <1% | (19+1+8)/3244 = 0.86% |
| ~5,900 lines Python | Actual: 5,861 (rounds to ~5,900) |
| ~250 lines Cython | Actual: 247 (rounds to ~250) |

---

## Cross-Reference Verification

All \ref{} targets have matching \label{} definitions:

| Reference | Label | Status |
|-----------|-------|--------|
| sec:background | Defined line 191 | OK |
| sec:method | Defined line 298 | OK |
| sec:validation | Defined line 713 | OK |
| sec:results | Defined line 762 | OK |
| sec:discussion | Defined line 1036 | OK |
| sec:limitations | Defined line 1162 | OK |
| sec:future | Defined line 1308 | OK |
| sec:conclusion | Defined line 1372 | OK |
| sec:absorption | Defined line 793 | OK |
| sec:translator | Defined line 1039 | OK |
| sec:phonetic | Defined line 1065 | OK |
| sec:tibetan | Defined line 1106 | OK |
| fig:pipeline | Defined line 357 | OK |
| fig:alignment | Defined line 623 | OK |
| fig:classification | Defined line 708 | OK |
| fig:validation | Defined line 1149 | OK |
| fig:falsepositives | Defined line 1230 | OK |
| tab:runtimes | Defined line 441 | OK |
| tab:classification | Defined line 636 | OK |
| tab:validation | Defined line 723 | OK |
| tab:dist | Defined line 771 | OK |
| tab:topsources | Defined line 803 | OK |
| tab:absorption | Defined line 845 | OK |
| tab:threshold | Defined line 1263 | OK |
| app:params | Defined line 1401 | OK |

---

## Citation Verification

All 22 citation keys used in the paper have matching entries in `references.bib`:

| Key | Used | Status |
|-----|------|--------|
| nattier1992 | 3x | OK |
| cbeta | 2x | OK |
| attwood2021a | 1x | OK (verified: JIABS vol 44, pp 13-52, 2021) |
| silk1994 | 1x | OK (entry type should arguably be @book, see issue #17) |
| huifeng2014 | 1x | OK (verified: JOCBS vol 6, pp 72-105, 2014) |
| bingenheimer2006 | 1x | OK |
| suttacentral | 1x | OK |
| sat | 1x | OK |
| zigmond2023 | 1x | OK |
| zigmond2021 | 1x | OK |
| bingenheimer2011 | 1x | OK (verified: LLC vol 26 no 3, pp 271-278, 2011) |
| buechler2014 | 1x | OK (verified: Springer, pp 221-238, 2014) |
| smith2015 | 2x | OK (verified: ALH vol 27 no 3, pp E1-E15, 2015) |
| forstall2015 | 2x | OK (verified: DSH vol 30 no 4, pp 503-515, 2015) |
| bamman2008 | 1x | OK (verified, but see issue #16 re publisher) |
| ganascia2014 | 1x | OK (verified: LLC vol 29 no 3, pp 412-421, 2014) |
| lee2007 | 1x | OK (verified: ACL 2007, pp 472-479) |
| ddb | 1x | OK |
| mcrae2003 | 1x | OK (verified: UC Press, 2003) |
| zigmond2026b | 1x | OK (unpublished, in preparation) |
| jockers2013 | 2x | OK (verified: U Illinois Press, 2013) |
| moretti2013 | 1x | OK |

---

## Checklist Summary

| Check | Result |
|-------|--------|
| No "we/our" | PASS (none found) |
| No em-dashes in text | PASS (only in LaTeX comments) |
| American spellings | PASS (no British spellings found) |
| Transliteration convention | PASS with exceptions (see issues #14, #15) |
| First-person singular | PASS |
| No venue references | PASS |
| All cross-refs valid | PASS |
| All citations valid | PASS |
| Arithmetic correct | PASS (all verified) |
| Numbers match source data | FAIL (6 discrepancies noted) |

---

## Priority Fix List

1. **Fix T85n2783 title** (道嵱 -> 稻芉): Factual error, easy fix.
2. **Fix phonetic numbers** (268->270, 1,021->990): Stale numbers from older pipeline run.
3. **Fix T21n1336 count** (17->16 in running text, line 908): Inconsistent with Table 4.
4. **Fix T18n0901 count** (16->13 in running text, line 911): Inconsistent with Table 4.
5. **Fix T17n0724 coverage** (84.4%->84.3%): Minor but factual.
6. **Fix T48n2014 coverage** (99.2%->99.1%): Minor but factual.
7. **Fix Table 5 ordering** (swap T51n2082 and T14n0506 rows).
8. **Replace "CJK" with "Chinese"** in lines 362 and 372.
9. **Verify retranslation validation stats** (88/94 = 93.6% vs 87/94 = 92.6%).
10. **Verify concordance coverage number** (878 Taisho texts).
11. **Fix bioinformatics citation** (line 290: smith2015 is not bioinformatics).
