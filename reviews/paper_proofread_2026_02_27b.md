# Proofread Report: "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-02-27
**Reviewer:** Claude Opus 4.6

---

## Critical Issues

### C1. Genre Table (Table 3) Internal Inconsistency
**Lines 776--800**

The "With Parallel" column in Table 3 uses inconsistent definitions across rows. Some rows count texts with any parallel (Tibetan, Pali, or Sanskrit), while others count only a subset. The column sums to 1,031, but the actual "any parallel" total across all listed genres is 1,082. The table caption claims "the remaining 51 parallels falling in omitted volumes," but no volumes are omitted: the listed genres cover all 2,455 Taisho texts (the genre-range sums add up to exactly 2,455).

Specific discrepancies between the paper's table and actual data:

| Genre | Paper | Actual (any parallel) | Difference |
|-------|-------|----------------------|------------|
| Shastra (25--32) | 134 (70.5%) | 136 (71.6%) | +2 |
| Mahayana sutra (9--17) | 361 (60.5%) | 364 (61.0%) | +3 |
| Agama (1--2) | 86 (55.5%) | 131 (84.5%) | +45 |
| Jataka/Avadana (3--4) | 37 (51.4%) | 38 (52.8%) | +1 |

The Agama discrepancy is the largest. The actual data shows 41 texts with Tibetan parallels, 122 with Pali parallels, and 51 with Sanskrit parallels, for 131 with any parallel. The paper's value of 86 does not correspond to any obvious combination of parallel types (Tibetan-only = 41, Tibetan+Sanskrit = 57, any = 131). This appears to be a stale value from an earlier version of the concordance data.

**Recommendation:** Recompute the "With Parallel" column using a consistent definition (either "any parallel" or "Tibetan only"), update the caption accordingly, and remove the claim about "omitted volumes."

### C2. Table 2 Tengyur Count Inconsistency
**Lines 721--733**

Table 2 states Tengyur coverage as 156 of 3,461 (4.5%), but the actual data shows only 154 Tohoku numbers in the Tengyur range (1109--4569). The remaining 2 Tohoku numbers (Toh 5639 and 5656) are outside both the Kangyur and Tengyur ranges. The table's footnote acknowledges "two additional Tohoku numbers (outside the standard ranges)" but these are already included in the rows that sum to 652. The table simultaneously claims the rows sum to 652, that there are 2 additional numbers outside ranges, and that the Tengyur row header specifies "Toh 1109--Toh 4569." These three claims are mutually inconsistent.

**Recommendation:** Either (a) change the Tengyur row to 154 and add a third row for "Supplemental" with 2, or (b) revise the footnote to clarify that the 2 outside-range Toh numbers are included in the Tengyur row by convention.

---

## Moderate Issues

### M1. MITRA Numbers Discrepancy
**Lines 471--474, 625--631**

The paper states "After filtering, 2,226 unique Taisho-to-Tohoku pairs remain (825 strong, 1,401 moderate)." However, the actual MITRA data file (`results/mitra_taisho_tohoku.json`) contains 2,389 entries with 865 strong (confidence >= 0.9) and 1,524 moderate (confidence 0.7). The total 2,389 is stated correctly earlier in the same section (line 452), but 825 + 1,401 = 2,226, not 2,389. The "filtering" that reduces 2,389 to 2,226 is not explained, and the current data file does not reflect this reduction.

At line 627, the paper says "MITRA, is a computational source contributing 2,226 attestations," which should presumably be 2,389 if that is the actual total.

**Recommendation:** Reconcile the MITRA numbers with the current data file. If 2,389 is correct, update 825/1,401/2,226 throughout. If the filtering step is real, explain it and ensure the data file reflects it.

### M2. Catalog Agreement Statistics
**Lines 624--625**

The paper states "93.0% of 1,381 individual Taisho-to-Tohoku links are independently attested by two or more sources." The actual data shows 92.3% of 1,401 catalog-only links with multi-source attestation. Both the percentage and the total count are slightly off.

**Recommendation:** Update to match current data, or note what filtering produces 1,381/93.0%.

### M3. "both...and" with Three Items
**Lines 337--341**

> "The large gap ... reflects **both** substantial overlap between sources, the many catalog entries ... that lack Taisho cross-references, **and** the large number of SuttaCentral parallel entries ..."

The "both...and" construction should connect exactly two items, but three are listed.

**Recommendation:** Remove "both" to produce "reflects substantial overlap..., the many catalog entries..., and the large number..."

### M4. "Three Lancaster Errors" Undercount
**Line 1528**

> "The three Lancaster errors detected here were found because an independent source (CBETA Jinglu Tibetan) disagreed"

Lancaster actually had five confirmed errors (as correctly stated at line 1007). Only three of these (the two trailing-zero errors and the digit transposition) propagated and were detectable through disagreement with CBETA Jinglu Tibetan. The two spurious-zero entries (errors 4--5) were also Lancaster errors. Calling these "the three Lancaster errors" could confuse readers who remember the "five confirmed errors" from earlier.

**Recommendation:** Change to "The three propagating Lancaster errors" or "Three of the five Lancaster errors."

### M5. Council of Lhasa Date and Characterization
**Lines 864--868**

The footnote states: "Tibet's adoption of a single Vinaya lineage reflects a deliberate choice at the Council of Lhasa (c. 797 CE), which established the Mulasarvastivada ordination lineage as normative for Tibetan monasticism."

Two issues: (1) The event commonly called the "Council of Lhasa" or "Debate of Samye" (c. 792--794 CE, with some sources saying c. 797) was primarily about the dispute between Indian gradual and Chinese sudden approaches to enlightenment, not about Vinaya adoption. The adoption of the Mulasarvastivada Vinaya as normative was part of the broader monastic establishment in Tibet, not a specific outcome of the Samye debate. (2) The most commonly cited dates are 792--794 CE, though 797 CE appears in some sources.

**Recommendation:** Consider revising to separate the Vinaya adoption from the Samye debate, or at minimum qualify: "a deliberate choice during the imperial period (late eighth century)."

### M6. Overlapping Categories in Parallel Count
**Lines 341--343**

> "Of these 1,082 texts, 838 have identified Tibetan parallels, 171 have Pali parallels, and the remainder have Sanskrit parallels only."

This is technically correct but misleading because 59 texts appear in both the Tibetan and Pali categories. A casual reader summing 838 + 171 = 1,009 would compute a "remainder" of 73, but the actual Sanskrit-only count is 132 (because of the overlap). The sentence structure implies non-overlapping categories.

**Recommendation:** Add a clarifying phrase: "838 have identified Tibetan parallels (some of which also have Pali parallels), 171 have Pali parallels, and the remainder have Sanskrit parallels only" or restructure to show the overlaps explicitly.

---

## Minor Issues

### m1. Prajnaparamita Tibetan Count in Genre Table
**Lines 786--787**

The table shows Prajnaparamita with 41 "With Parallel." The actual Tibetan-only count is 40 (not 41). The 41 includes one text (T08n0234) with a Sanskrit parallel only. This is consistent with the "any parallel" definition but inconsistent with the Tibetan-focused framing of the row. (This is a symptom of the broader Table 3 inconsistency in C1.)

### m2. Footnote: "Sutra in Forty-Two Sections" Pinyin
**Line 530**

The pinyin for 四十二章經 is given as `S\`ish\'i'\`erzh\=angj\={\i}ng`. The apostrophe between `shi` and `er` (`\'i'\`e`) is unusual. Standard pinyin for 四十二 is `Sishier` (or `Si shi er` with spaces). The apostrophe is sometimes used in pinyin to disambiguate syllable boundaries, but `shi'er` (with apostrophe after `shi`) is not standard; the standard would be `shier` (no apostrophe needed since `shi` + `er` is unambiguous).

**Recommendation:** Remove the apostrophe: `S\`ish\'i\`erzh\=angj\={\i}ng` or `S\`i sh\'i\`er zh\=ang j\={\i}ng` (with spaces between syllables for readability).

### m3. Verbatim Block Chinese in TEI XML Example
**Line 1618**

The TEI XML example contains `<title type="chinese">長阿含經</title>` inside a verbatim block. While line 1624 provides the transliteration outside the block, the transliteration convention note in the project instructions says "no bare non-Latin script outside verbatim blocks." This particular case is handled correctly (inside verbatim, with transliteration provided afterward at line 1624). No action needed, but worth confirming this was intentional.

### m4. "minor compilations or texts" Phrasing
**Lines 1135--1136**

> "The remaining four are minor compilations or texts widely considered to be Chinese compositions rather than direct translations of Indic originals."

The phrase "minor compilations or texts widely considered to be Chinese compositions" is slightly ambiguous: does "widely considered to be Chinese compositions" modify only "texts" or also "minor compilations"? The former reading suggests some are minor compilations (which might still be translations) and others are Chinese compositions. The intended meaning appears to be that all four are either compilations or Chinese compositions (i.e., not translations).

**Recommendation:** Consider "The remaining four are minor compilations or texts widely considered to be Chinese compositions, rather than direct translations of Indic originals" (moving the comma for clarity), or "The remaining four are texts widely considered to be Chinese compilations or compositions rather than direct translations of Indic originals."

### m5. Footnote Length in Prajnaparamita Section
**Lines 1109--1132**

This footnote is extremely long (24 lines of source text). It provides detailed information about five texts including full Chinese titles, pinyin, translators, and dates. While informative, a footnote of this length may disrupt reading flow.

**Recommendation:** Consider moving this material to an appendix table, or shortening to just the Taisho numbers and brief descriptions.

### m6. "101 overlap" vs "77 confirmed + 24 contradicted"
**Lines 1347--1349**

The text says "101 overlap with texts that already have Taisho-to-Tohoku mappings" and then says "77 (76.2%) confirm the existing mapping." 77/101 = 76.2%. This is correct, but the validation rate in Table 4 shows "Validation rate: 76.2%" without specifying the denominator. It might be clearer to label this "Confirmation rate among overlapping matches."

### m7. Missing Citation for Buswell on Vajrasamadhisutra
**Lines 547--553**

The footnote cites `\citet{buswell2014}` (The Princeton Dictionary of Buddhism) for the scholarly consensus on the Vajrasamadhisutra's Korean/Chinese origin. While this work does discuss it, the primary scholarly reference is Buswell's earlier monograph *The Formation of Ch'an Ideology in China and Korea* (1989) or his study specifically on the Vajrasamadhisutra (*The Korean Origin of the Vajrasamadhi-Sutra*, 1989/2005). The Princeton Dictionary is a general reference work rather than the primary source for this argument.

**Recommendation:** Consider citing the more specific Buswell work on the Vajrasamadhisutra, or add it alongside the dictionary reference.

### m8. GitHub URL in Footnote
**Lines 1579--1583**

The repository URL is `https://github.com/dangerzig/taisho-canon` with the note "[to be released on acceptance]." The username is "dangerzig" which appears to be a placeholder or actual username. Verify this is the intended public URL.

### m9. "Claude Haiku 4.5" and "Claude Sonnet 4.5" Naming
**Lines 1716--1717**

The paper references "Claude Haiku 4.5" and "Claude Sonnet 4.5." As of the knowledge cutoff, these specific model names should be verified against Anthropic's official naming (the naming convention uses "Claude" followed by the model tier and version number). Verify these are the correct official names, as Anthropic has used various naming patterns.

### m10. Tense Consistency in MITRA Section
**Lines 441--474**

The MITRA section mixes passive and active voice, and present and past tense: "We extract document-level pairs" (present), "we require at least 20 aligned sentences" (present), "we adopt a conservative integration strategy" (present), but other sections use past tense ("was obtained," "were extracted"). The present tense is acceptable for describing the ongoing methodology, but the shift between sections is noticeable.

### m11. "Back-translated" Quotation Marks
**Line 1166**

> subsequently ``back-translated'' into Sanskrit

The scare quotes around "back-translated" are appropriate here since this is Nattier's specific terminology. The direction described (Chinese to Sanskrit) is correct per Nattier (1992). No change needed.

### m12. No Bare Non-Latin Script Found
All `\zh{}` instances are followed by `\py{}`, and all `\tib{}` instances are followed by `\wy{}`. No transliteration violations were found outside verbatim blocks.

### m13. No Em-Dashes in Running Prose
No em-dashes (`---`) appear in running prose. The only `---` is in a table cell (line 331) as a placeholder, which is standard.

### m14. American English Compliance
No British spellings found in the paper text. "Catalogues" appears once (line 370) but is part of the official name "CBETA Digital Database of Buddhist Tripitaka Catalogues," which should preserve the original spelling.

### m15. No Journal Name References
The paper does not reference any target journal by name.

### m16. Cross-Reference Consistency
All `\ref{}` targets have corresponding `\label{}` definitions. All 16 labels are referenced at least once.

---

## Summary of Verified Claims

The following key statistics were verified against the actual concordance data (`results/cross_reference_expanded.json`):

| Claim | Paper | Data | Status |
|-------|-------|------|--------|
| Taisho texts with Tibetan parallels | 838 | 838 | Matches |
| Total Taisho texts | 2,455 | 2,455 | Matches |
| Texts with any parallel | 1,082 | 1,082 | Matches |
| Pali parallels | 171 | 171 | Matches |
| Total unique Toh (strings) | 652 | 652 | Matches |
| Kangyur Toh (1--1108) | 496 | 496* | Matches (*includes Toh 359a) |
| Tengyur Toh (1109--4569) | 156 | 154 | **Mismatch** (see C2) |
| Sanskrit title total matches | 231 | 231 | Matches |
| Sanskrit exact matches | 192 | 192 | Matches |
| Sanskrit fuzzy matches | 39 | 39 | Matches |
| Sanskrit validated | 77 | 77 | Matches |
| Sanskrit contradicted | 24 | 24 | Matches |
| Sanskrit new proposals | 130 | 130 | Matches |
| New proposals unique Taisho | 107 | 107 | Matches |
| Validation rate | 76.2% | 76.2% | Matches |
| 12.8% expansion | 107/838 | 12.8% | Matches |
| T11n0310 Toh count | 63 | 63 | Matches |
| CBETA Tibetan unique Taisho | 613 | 613 | Matches |
| Genre table sum | 1,031 | 1,082 | **Mismatch** (see C1) |
| Catalog agreement % | 93.0% of 1,381 | 92.3% of 1,401 | **Mismatch** (see M2) |
| MITRA total pairs | 2,389 | 2,389 | Matches |
| MITRA strong pairs | 825 | 865 | **Mismatch** (see M1) |
| MITRA moderate pairs | 1,401 | 1,524 | **Mismatch** (see M1) |

---

## Bibliography Spot-Check

The following references were verified against available sources:

- **Nattier 1992**: JIABS vol. 15, no. 2, pp. 153--223. Confirmed correct.
- **Lancaster 1979**: UC Press, Berkeley. Confirmed correct.
- **Ui et al. 1934**: Tohoku Imperial University, Sendai. Confirmed correct.
- **Nanjio 1883**: Clarendon Press, Oxford. Confirmed correct.
- **Conze 1978**: Reiyukai, Tokyo, 2nd ed. Confirmed correct.
- **Kapstein 2000**: Oxford University Press. Confirmed correct.
- **Davidson 2002**: Columbia University Press. Confirmed correct.
- **Zurcher 2007**: Brill, 3rd ed. Confirmed correct.
- **Ishikawa 1990**: Studia Tibetica no. 18, Toyo Bunko. Confirmed correct.
- **Buswell & Lopez 2014**: Princeton University Press. Confirmed correct.

No ghost or fabricated references detected.
