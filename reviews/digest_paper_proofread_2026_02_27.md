# Proofread Report: "Computational Detection of Text Reuse in the Chinese Buddhist Canon"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-digest-detection/zigmond-digest-detection.tex`
**Date:** 2026-02-27
**Reviewer:** Claude Opus 4.6

---

## Critical Issues

### C1. Excerpt/Digest Counts Mismatch (Abstract, Table, Running Text)
**Lines 95--97, 505--524**

The paper states "135 excerpts" and "539 digests" (abstract line 95, distribution table lines 515--519), but the actual pipeline output (`results/summary.md` and `results/digest_relationships.json`) shows **136 excerpts** and **538 digests**. The total 3,610, the 224 retranslations, 538 commentaries, and 2,174 shared tradition all match the data. Only the excerpt and digest counts are swapped by one unit (it appears one excerpt was miscounted as a digest).

**Data:**
- `summary.md`: excerpt: 136, digest: 538
- `digest_relationships.json`: excerpt: 136, digest: 538, commentary: 538, retranslation: 224, shared_tradition: 2174 (total: 3610)

**Recommendation:** Change "135 excerpts" to "136 excerpts" and "539 digests" to "538 digests" in the abstract (line 95), the distribution table (lines 515--519), and verify any other occurrences.

### C2. Top 10 Sources Table Contains Incorrect Counts and a Wrong Entry
**Lines 538--559 (Table 3)**

Several entries in the "Top 10 source texts by number of derivative relationships" table are inconsistent with the data:

| Source | Paper Claims | Actual (excerpt+digest) | Actual (non-shared) |
|--------|-------------|------------------------|---------------------|
| T53n2122 | 102 | 102 | 113 |
| T53n2121 | 49 | **48** | 50 |
| T54n2123 | 27 | **28** | 29 |
| T48n2016 | 24 | 24 | 38 |
| T21n1336 | 16 | 16 | 17 |
| T18n0901 | 13 | 13 | 16 |
| T22n1428 | 11 | 11 | 21 |
| **T02n0099** | **8** | **4** | **4** |
| T51n2076 | 8 | 8 | 8 |
| T02n0125 | 7 | **8** | 16 |

Three problems:
1. **T02n0099 should not be in the top 10.** It has only 4 excerpt+digest relationships (3 excerpts, 1 digest), not 8. It does have 29 shared-tradition relationships, but these are excluded from this table's scope.
2. **T53n2121** has 48 excerpt+digest relationships, not 49.
3. **T54n2123** has 28, not 27.
4. **T02n0125** has 8, not 7.

The actual top 10 by excerpt+digest count should replace T02n0099 with T30n1579 (7 derivatives, tied with T36n1736 and T18n0848).

**Recommendation:** Recompute the table from current data. The table's "Derivatives" column should be defined explicitly (excerpt+digest, or all non-shared-tradition?). The running text mixes conventions (e.g., the Dharani section says T21n1336 has "17" at line 647, counting all non-shared types, while the table says 16, counting excerpt+digest only).

### C3. T53n2121 Breakdown Incorrect
**Line 617**

The paper states "4 excerpts, 45 digests" for T53n2121 (total 49), but the actual data shows **2 excerpts** (T03n0182a at 86.8%, T03n0177 at 80.7%) and **46 digests** (total 48).

**Recommendation:** Change to "2 excerpts, 46 digests."

### C4. Bibliography Reference: Ganascia et al. Wrong Authors
**references.bib lines 222--230**

The entry `ganascia2014` lists authors as "Ganascia, Jean-Gabriel and Leblanc, Pierre and Molin, Martin." The actual authors are **Ganascia, Jean-Gabriel and Glaudes, Pierre and Del Lungo, Andrea** (verified via HAL archive hal-00977310 and the publisher Literary and Linguistic Computing vol. 29, no. 3). Additionally, the entry uses `@inproceedings` with a `booktitle` field, but this is a journal article in Literary and Linguistic Computing; it should use `@article` with a `journal` field.

**Recommendation:** Correct the authors to "Ganascia, Jean-Gabriel and Glaudes, Pierre and {Del Lungo}, Andrea" and change to `@article` with `journal = {Literary and Linguistic Computing}`.

### C5. Bibliography Reference: Buechler et al. Wrong Author Names
**references.bib lines 201--208**

The entry `buechler2014` lists "Burns, Patrick R." and "Geser, Emily." The actual authors are **Burns, Philip R.** (not Patrick) and **Franzini, Emily** (not Geser, Emily). The correct full author list is: Büchler, Marco; Burns, Philip R.; Müller, Martin; Franzini, Emily; Franzini, Greta (verified via Springer, Semantic Scholar, and DBLP).

**Recommendation:** Correct "Patrick R." to "Philip R." and "Geser, Emily" to "Franzini, Emily."

### C6. Bibliography Reference: Hung & Bingenheimer Appears Fabricated
**references.bib lines 83--91**

The entry `hung2015` cites "Social Network Analysis of Buddhist Biographical Collections" in the Journal of the Japanese Association for Digital Humanities, vol. 1, no. 1, pp. 27--43, 2015. This reference cannot be verified. The actual collaborative work by Bingenheimer and Hung on social networks is "Social Network Visualization from TEI Data" published in **Literary and Linguistic Computing, vol. 26, no. 3, pp. 271--278, 2011** (authors: Bingenheimer, Hung, and Wiles). A later collaboration appeared in JJADH vol. 2 (2017), not vol. 1 (2015). No paper matching the cited title, journal, volume, or year could be found.

**Recommendation:** Replace with the correct reference (Bingenheimer, Hung, and Wiles 2011 in LLC) or verify whether a genuine 2015 JJADH publication exists.

### C7. Bibliography Reference: zigmond2021 Wrong Title
**references.bib lines 51--58**

The entry `zigmond2021` cites the title as "Frequency-Based Text Mining in the P\=ali Canon." The actual title (verified via JOCBS website) is **"Toward a Computational Analysis of the Pali Canon."**

**Recommendation:** Correct the title.

---

## Moderate Issues

### M1. "954 Taisho Texts" vs. Companion Paper's 838
**Line 838**

The paper states the concordance covers "954 Taish\=o texts with Tibetan, Sanskrit, and/or P\=ali parallels." The companion paper (`zigmond-tibetan-concordance.tex`) reports 838 Taisho texts with Tibetan parallels and 1,082 with any parallel (Tibetan, Pali, or Sanskrit). The number 954 does not match either figure. From the project memory: "838 Taisho texts with Tibetan parallels" and "1,031 texts with any parallel."

**Recommendation:** Replace 954 with the correct number. If the intended meaning is "texts with any parallel," use 1,082 (or 1,031 if only counting texts in the extractable corpus). If "Tibetan parallels only," use 838. Clarify the scope.

### M2. Companion Paper Title Mismatch in Bibliography
**references.bib lines 69--74**

The `zigmond2026b` entry gives the title as "A Unified Concordance of the Chinese and Tibetan Buddhist Canons: Merging Eight Data Sources with Provenance Tracking." The actual companion paper title is **"Mapping the Chinese and Tibetan Canons: A Computational Concordance and Its Implications for Tibetan Buddhist Studies."** Also, the companion paper uses **ten** data sources (as stated at its line 284), not eight.

**Recommendation:** Update the title to match the actual companion paper, and change "Eight" to "Ten" if the bib title is retained in any form.

### M3. "Eight Independent Data Sources" Should Be Ten
**Line 835**

The paper states "we compiled a unified cross-canon concordance from eight independent data sources." The companion paper explicitly states "ten independent data sources" (line 284 of zigmond-tibetan-concordance.tex). The list at lines 835--837 names only seven sources explicitly (SuttaCentral, Lancaster catalogue, CBETA Jinglu Tibetan, CBETA Jinglu Sanskrit, acmuller Tohoku index, rKTs, 84000 TEI) plus "manual scholarship" (eight). The companion paper also includes MITRA and the Otani concordance.

**Recommendation:** Change "eight" to match the companion paper's count, or explain which sources are included and which are excluded.

### M4. Coverage Rounding Inconsistencies
**Lines 595 and 741**

Two coverage values in the paper do not match the data when rounded to one decimal place:

| Text Pair | Paper | Raw Data | Correctly Rounded |
|-----------|-------|----------|-------------------|
| T17n0724 from T53n2122 | 84.3% | 0.8435 | **84.4%** |
| T48n2014 from T51n2076 | 99.1% | 0.9915 | **99.2%** (or 99.1% if truncated) |

The summary.md shows 84.3% and 99.1%, suggesting these may have been taken from summary.md which uses a different rounding/truncation convention than standard mathematical rounding.

**Recommendation:** Use consistently rounded values. Standard mathematical rounding gives 84.4% and 99.2%.

### M5. Shared Absorbed Texts Count Off by One
**Line 617**

The paper states "The two encyclopedias also share 23 absorbed texts in common." The actual intersection of texts absorbed by both T53n2122 and T53n2121 (as excerpt or digest) is **22** texts.

**Recommendation:** Change "23" to "22."

### M6. Inconsistent Definition of "Derivatives" Between Table and Text
**Lines 538--559, 645--651**

The Top 10 Sources table counts excerpt+digest relationships only (e.g., T21n1336 = 16, T18n0901 = 13). But the running text at line 647 says T21n1336 has "17 shorter texts" (counting all non-shared types including retranslation), and line 650 says T18n0901 serves as "source for 16 shorter ritual and dharani texts" (counting non-shared including commentary). The table and text use different counting conventions without noting the difference.

**Recommendation:** Either use a consistent counting convention throughout, or add a note explaining that the table counts excerpt+digest relationships while the text may include other categories (retranslation, commentary).

### M7. Pervasive Em-Dashes in Running Prose
**Throughout the paper (39+ instances)**

The paper contains approximately 39 em-dashes (`---` in LaTeX) in running prose. Per the author's strong preference, em-dashes should be avoided in favor of commas, parentheses, colons, semicolons, or separate sentences. Examples:

- Line 93: "Using a five-stage pipeline---text extraction..." (use a colon)
- Line 142: "specific cases---most notably Jan Nattier's..." (use a comma or parentheses)
- Line 202: "original narrative apparatus---an opening scene" (use a colon)
- Line 270: "a common methodological core---fingerprinting..." (use a colon)
- Line 346: "inherently asymmetric---a 300-character text" (use a colon)
- Line 528: "digests were identified---texts drawing content" (use parentheses or a comma)
- Line 690: "at 97.3% coverage---essentially a verbatim excerpt" (use a comma)
- Lines 762--763: "earlier textual material---poems, sayings, doctrinal treatises---into" (use parentheses)

**Recommendation:** Systematically replace em-dashes with appropriate alternative punctuation. A few may be acceptable where no other punctuation works, but the current density (roughly one every 25 lines) is far higher than the author's stated preference.

### M8. "Catalogue" Spelling (British) Instead of "Catalog" (American)
**Lines 219, 836, 842, 950, 962**

The paper uses "catalogues" and "catalogue" in five places in the running text. American English uses "catalog(s)."

- Line 219: "digital comparative catalogues" (in running text, not a title)
- Line 836: "Lancaster catalogue"
- Line 842: "catalogue number"
- Line 950: "catalogue dates"
- Line 962: "catalogue matching"

**Recommendation:** Change all instances in running text to "catalog(s)." Preserve "Catalogue" in cited work titles (e.g., Lancaster's book title).

---

## Minor Issues

### m1. Missing English Translations at First Use of Key Terms
**Lines 101, 547--557**

Several Chinese text titles appear without English translations at their first use:

- \zh{法苑珠林} (line 101, abstract): No English translation anywhere in the paper. Should include "Forest of Gems in the Garden of the Dharma" or similar at first use.
- \zh{經律異相} (line 548, Table 3): First use in the table without English translation. The English name ("Illustrations of Different [Accounts in] Sutras and Vinaya") should appear at first textual use.
- \zh{諸經要集} (line 549, Table 3): No English translation. Consider "Collection of Essentials from Various Sutras."
- \zh{宗鏡錄} (line 550, Table 3): English appears later at line 748 ("Records of the Mirror of the Source") but not at first use.
- \zh{陀羅尼雜集} (line 551, Table 3): English appears later at line 645 but not at first use in the table.
- \zh{四分律} (line 553, Table 3): Not translated. "Four-Part Vinaya" appears at line 660 but as a standalone reference.

**Recommendation:** Add English translations in parentheses at first use, or add a "Title" column to Table 3 with English names.

### m2. "Roughly 63%" Is Slightly Imprecise
**Line 151**

The paper says "roughly 63% of the extractable corpus." The actual figure is 1,558/2,455 = 63.5%. "Roughly 63%" is acceptable but "roughly 64%" or "approximately 63.5%" would be more accurate.

**Recommendation:** Consider updating to "roughly 64%" or "approximately 63.5%."

### m3. Table 3 Header Ambiguity
**Line 545**

The column header "Derivatives" is ambiguous. It could mean excerpt+digest only, or all non-shared-tradition relationships. As noted in M6, the paper uses different conventions in different places. The reader cannot tell what is counted.

**Recommendation:** Change to "Excerpt/Digest Derivatives" or add a table note defining the scope.

### m4. T250 Novel Fraction Stated as 26.9%, Data Shows 26.85%
**Line 480**

The paper states "the 26.9% novel fraction." The actual novel_fraction from validation.md is 0.2685 = 26.85%, which rounds to 26.9% but could also be reported as 26.8%. This is acceptable rounding but slightly imprecise.

### m5. Abstract Says "135 Excerpts" but Also "102 Shorter Texts"
**Lines 95, 101--102**

The abstract mentions both "135 excerpts" (actually 136, see C1) and separately that the Fayuan Zhulin "incorporates 102 shorter texts." A reader might wonder about the relationship between these numbers. The 102 refers to excerpt+digest relationships for one specific source, while 135/136 is the total excerpt count. The two are not in conflict, but the juxtaposition could confuse a casual reader.

### m6. Phonetic Pair Count Cannot Be Verified from JSON
**Line 806**

The paper states "268 text pairs containing 1,021 individual phonetic match segments." The `digest_relationships.json` output does not include a `phonetic_coverage` or `phonetic_segments` field (the only fields are: avg_segment_length, classification, confidence, coverage, digest_id, has_docnumber_xref, longest_segment, novel_fraction, num_source_regions, source_id, source_span). These phonetic statistics cannot be independently verified from the shipped JSON output.

**Recommendation:** Either add phonetic fields to the JSON output for reproducibility, or document where these figures can be verified.

### m7. Stop-Gram Count and Candidate Count Not in Output Files
**Lines 336, 391**

The paper claims "381 stop-grams" were removed and "6,850 candidate pairs (51% of all candidates)" were generated by phonetic matching. Neither figure appears in `summary.md` or any output file in `results/`. These are pipeline runtime statistics that are only logged during execution.

**Recommendation:** Consider adding these statistics to the summary output for reproducibility.

### m8. "122 of 2,455 Texts" for Stop-Gram Threshold
**Line 336**

The paper says "more than 5% of all documents (i.e., in more than 122 of the 2,455 texts)." 5% of 2,455 = 122.75, so the threshold is >122.75, meaning a gram must appear in 123+ texts to be filtered. The paper says "more than 122," which is technically correct (>122.75 means >122 in integer terms, i.e., 123+), but could be clearer as "in 123 or more of the 2,455 texts."

### m9. GitHub URL Uses "dangerzig"
**Line 1015**

The repository URL is `https://github.com/dangerzig/taisho-canon`. Verify this is the intended public username. (Same issue noted in the companion paper review.)

### m10. LaTeX Comment References JIABS
**Line 4**

The comment `% Targeting: Journal of the International Association of Buddhist Studies` should be removed before submission. While comments are not rendered, they may be visible to reviewers or editors who inspect the LaTeX source.

### m11. Tense Consistency
**Throughout**

The paper mostly uses past tense for methodology ("was performed," "was built," "were excluded") and present tense for results ("shows," "reveals," "confirms"), which is an acceptable convention. However, a few switches are jarring: line 505 uses "detected" (past) for results, while nearby text uses present tense.

### m12. "Both...And" Check
No instances of "both...and" with more than two items were found.

### m13. Cross-Reference Labels Verified
All `\ref{}` targets have matching `\label{}` definitions. All labels are referenced. No dangling references found.

### m14. No Bare Non-Latin Script
All `\zh{}` instances are followed by `\py{}`. All `\tib{}` instances are followed by `\wy{}`. No transliteration violations were found.

### m15. No Journal Name in Paper Text
The paper does not reference any target journal by name in the body text. The JIABS reference appears only in a LaTeX comment (line 4).

### m16. Retranslation Size Ratio in Classification Table
**Line 438**

The classification table states "size ratio < 3.0" for retranslation. The config.py parameter `RETRANSLATION_SIZE_RATIO = 3.0` and the scoring logic presumably means the source must be *less than* 3x the digest length. The table says "size ratio < 3.0" which matches the config. Verified correct.

### m17. Appendix Parameter Table Verification
**Lines 1024--1053**

All parameter values in the appendix table match `config.py`:

| Parameter | Paper | config.py | Status |
|-----------|-------|-----------|--------|
| N-gram size | 5 | NGRAM_SIZE = 5 | Match |
| Stop-gram doc freq | 0.05 | STOPGRAM_DOC_FREQ = 0.05 | Match |
| Min containment | 0.10 | MIN_CONTAINMENT = 0.10 | Match |
| Min size ratio | 2.0 | MIN_SIZE_RATIO = 2.0 | Match |
| Max digest length | 50,000 | MAX_DIGEST_LENGTH = 50000 | Match |
| Min seed length | 5 | MIN_SEED_LENGTH = 5 | Match |
| Fuzzy match score | +1 | FUZZY_MATCH_SCORE = 1 | Match |
| Fuzzy mismatch | -2 | FUZZY_MISMATCH_SCORE = -2 | Match |
| Fuzzy threshold | -4 | FUZZY_EXTEND_THRESHOLD = -4 | Match |
| Excerpt threshold | 0.80 | EXCERPT_THRESHOLD = 0.80 | Match |
| Digest threshold | 0.30 | DIGEST_THRESHOLD = 0.30 | Match |
| Shared tradition threshold | 0.10 | SHARED_TRADITION_THRESHOLD = 0.10 | Match |
| Retranslation ratio | 3.0 | RETRANSLATION_SIZE_RATIO = 3.0 | Match |
| Commentary avg seg | 10 | COMMENTARY_AVG_SEG_LEN = 10 | Match |
| Phonetic seed length | 5 | PHONETIC_SEED_LENGTH = 5 | Match |
| Phonetic n-gram size | 3 | PHONETIC_NGRAM_SIZE = 3 | Match |
| Min phonetic containment | 0.25 | MIN_PHONETIC_CONTAINMENT = 0.25 | Match |
| Phonetic stopgram freq | 0.05 | PHONETIC_STOPGRAM_DOC_FREQ = 0.05 | Match |
| Phonetic max syllables | 5 | PHONETIC_MAX_SYLLABLES = 5 | Match |

---

## Summary of Verified Claims

| Claim | Paper | Data | Status |
|-------|-------|------|--------|
| Total relationships | 3,610 | 3,610 | **Match** |
| Unique texts | 1,558 | 1,558 | **Match** |
| Excerpts | 135 | 136 | **Mismatch** (C1) |
| Digests | 539 | 538 | **Mismatch** (C1) |
| Commentaries | 538 | 538 | **Match** |
| Retranslations | 224 | 224 | **Match** |
| Shared tradition | 2,174 | 2,174 | **Match** |
| T250 to T223 coverage | 0.732 (73.2%) | 0.7315 | **Match** |
| T251 to T223 coverage | 0.446 (44.6%) | 0.4462 | **Match** |
| 28.6-point gap | 28.6 | 73.15 - 44.62 = 28.53 | **Close** (rounds to 28.5 from exact, 28.6 from displayed) |
| T250 source regions | 8 | 8 | **Match** |
| T250 longest segment | 156 | 156 | **Match** |
| T250 novel fraction | 26.9% | 26.85% | **Match** (rounds correctly) |
| T53n2122 derivatives | 102 | 102 (exc+dig) | **Match** |
| T53n2122 excerpts | 11 | 11 | **Match** |
| T53n2122 digests | 91 | 91 | **Match** |
| T53n2121 total | 49 | 48 | **Mismatch** (C2) |
| T53n2121 "4 exc, 45 dig" | 4+45 | 2+46 | **Mismatch** (C3) |
| T54n2123 derivatives | 27 | 28 | **Mismatch** (C2) |
| T02n0099 derivatives | 8 | 4 | **Mismatch** (C2) |
| T02n0125 derivatives | 7 | 8 | **Mismatch** (C2) |
| Multi-source digests | 55 | 55 | **Match** |
| Higher-confidence relationships | 1,436 | 1,436 | **Match** |
| Shared absorbed texts | 23 | 22 | **Mismatch** (M5) |
| T21n1336 "17 texts" | 17 | 17 (non-shared) | **Match** |
| T15n0615 coverage | 100.0% | 100.0% | **Match** |
| T12n0332 coverage | 99.4% | 99.4% | **Match** |
| T32n1689 coverage | 99.4% | 99.4% | **Match** |
| T02n0115 coverage | 98.3% | 98.3% | **Match** |
| T14n0494 coverage | 88.6% | 88.6% | **Match** |
| T12n0369 coverage | 87.4% | 87.4% | **Match** |
| T17n0724 coverage | 84.3% | 84.4% | **Mismatch** (M4) |
| T54n2123 coverage | 84.0% | 84.0% | **Match** |
| T19n1028A coverage | 82.2% | 82.2% | **Match** |
| T02n0132a coverage | 82.0% | 82.0% | **Match** |
| T14n0581 coverage | 81.2% | 81.2% | **Match** |
| T85n2783 (Yogacara) | 97.3% | 97.3% | **Match** |
| T24n1501 (Yogacara) | 97.0% | 97.0% | **Match** |
| T16n0676 (Yogacara) | 86.5% | 86.5% | **Match** |
| T24n1499 (Yogacara) | 72.3% | 72.3% | **Match** |
| T14n0524 (Yogacara) | 65.7% | 65.7% | **Match** |
| T31n1615 (Yogacara) | 62.9% | 62.9% | **Match** |
| T31n1602 (Yogacara) | 40.8% | 40.8% | **Match** |
| T31n1603 from T31n1602 | 99.0% | 99.0% | **Match** |
| T29n1560 from T29n1558 | 99.5% | 99.5% | **Match** |
| T31n1601 from T31n1600 | 99.7% | 99.7% | **Match** |
| T48n2010 from T51n2076 | 100% | 100.0% | **Match** |
| T48n2014 from T51n2076 | 99.1% | 99.2% | **Mismatch** (M4) |
| T48n2012A from T51n2076 | 54.4% | 54.4% | **Match** |
| T22n1431 from T22n1428 | 81.0% | 81.0% | **Match** |
| T22n1434 from T22n1428 | 65.6% | 65.6% | **Match** |
| T22n1429 from T22n1428 | 65.6% | 65.6% | **Match** |
| T14n0502 from T02n0099 | 100% | 100.0% | **Match** |
| T14n0503 from T02n0099 | 100% | 100.0% | **Match** |
| T14n0499 from T02n0099 | 100% | 100.0% | **Match** |
| Chan sayings 32%--52% | 32%--52% | 32.8%--52.0% | **Match** |
| T46n1927 from T48n2016 | 80.4% | 80.4% | **Match** |
| T19n1020 from T48n2016 | 65.9% | 65.9% | **Match** |
| T46n1920 from T48n2016 | 62.2% | 62.2% | **Match** |
| T31n1586 from T48n2016 | 55.2% | 55.2% | **Match** |
| T32n1667 from T48n2016 | 46.2% | 46.2% | **Match** |
| T45n1858 from T48n2016 | 40.9% | 40.9% | **Match** |
| T48n2014 from T48n2016 | 31.8% | 31.8% | **Match** |
| Retranslation pairs confirmed | 88/224 (39.3%) | 88/224 = 39.3% | **Match** |
| Validation rate | 93.6% | 88/94 = 93.6% | **Match** |
| 2,455 texts after filtering | 2,455 | 2,455 | **Match** |
| 8,982 XML files | 8,982 | 8,982 | **Match** |
| All appendix parameters | (see m17) | (see m17) | **All match** |

---

## Bibliography Spot-Check

| Reference | Status | Notes |
|-----------|--------|-------|
| Nattier 1992 | **Correct** | JIABS 15(2):153--223 |
| Attwood 2021 | **Correct** | JIABS 44:13--52 |
| Huifeng 2014 | **Correct** | Numen 61(5--6):659--692 |
| Silk 1994 | **Correct** | WSTB 34:1--144, Vienna |
| Smith et al. 2015 | **Correct** | ALH 27(3):E1--E15 |
| Lee 2007 | **Correct** | ACL 2007:472--479 |
| Forstall et al. 2015 | **Partially correct** | DSH 30(4):503--515; but missing co-authors Buck, Roache, Jacobson |
| Bamman & Crane 2008 | **Partially correct** | Full proceedings name is "LaTeCH 2008 Workshop" |
| **Ganascia et al. 2014** | **Wrong authors** | Should be Ganascia, Glaudes, Del Lungo (not Leblanc, Molin); entry type should be @article not @inproceedings |
| **Büchler et al. 2014** | **Wrong author names** | Burns is Philip (not Patrick); Geser should be Franzini, Emily |
| **Hung & Bingenheimer 2015** | **Cannot be verified** | May be fabricated; actual collaboration is LLC 2011 with different title |
| **Zigmond 2021** | **Wrong title** | Actual title is "Toward a Computational Analysis of the Pali Canon" |
| Zigmond 2023 | **Cannot be verified** | No web evidence found; may exist but unindexed |
| Zigmond 2026b | **Wrong title** | Should match companion paper: "Mapping the Chinese and Tibetan Canons: A Computational Concordance..." |
| Jockers 2013 | **Correct** | U of Illinois Press |
| Moretti 2013 | **Correct** | Verso, London |
| McRae 2003 | **Correct** | UC Press, Berkeley |
| Buswell & Lopez 2014 | **Correct** | Princeton UP |

---

## Content and Logic Check

### Abstract Accuracy
The abstract is mostly accurate but contains the C1 excerpt/digest count error (135/539 should be 136/538). All other claims in the abstract are verified.

### Unsupported Claims
No claims were found that are unsupported by the data, apart from the numerical errors documented above.

### Logical Gaps
The paper's argument is logically coherent. The progression from validation through results to discussion follows naturally.

### Companion Paper Cross-References
Two inconsistencies found:
1. **954 vs 838/1,082** (M1): The number of Taisho texts with parallels does not match the companion paper.
2. **"Eight data sources" vs. ten** (M3): The companion paper says ten.
3. **Companion paper title** (M2): The bib entry does not match the actual paper title.

---

## Summary

**Critical issues:** 7 (3 statistical mismatches, 4 bibliography errors including one likely fabrication)
**Moderate issues:** 8 (cross-reference inconsistencies, em-dashes, British spelling, rounding)
**Minor issues:** 17 (missing translations, ambiguous headers, unverifiable statistics, tense)

The most urgent fixes are C1--C3 (incorrect statistics that will be immediately noticed by any reviewer checking the math), C4--C7 (bibliography errors, especially C6 which may be a fabricated reference), and M1--M3 (inconsistencies with the companion paper).
