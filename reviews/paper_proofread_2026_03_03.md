# Proofread Report: "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-03-03
**Reviewer:** Claude Opus 4.6

---

## Critical (factual errors, broken references, numerical issues)

### C1. Hardcoded section reference `\S3.4` (lines 596, 629)

**Text:** `(\S\ref{sec:merge}--\S3.4)` (appears in both the TikZ figure and the figure caption)

**Issue:** The reference `\S3.4` is hardcoded rather than using `\ref{}`. If sections are reordered or renumbered, this will silently become wrong. The subsection "Source Agreement" currently lacks a `\label{}` entirely.

**Fix:** Add `\label{sec:agreement}` after the "Source Agreement" subsection heading (line 684), then change `\S3.4` to `\S\ref{sec:agreement}` on both lines 596 and 629.

---

### C2. Percentages do not sum to 100% (lines 687--688)

**Text:** `64.3\% full agreement ... and 36.5\% partial overlap`

**Issue:** 64.3 + 36.5 = 100.8%, which exceeds 100%. This is either a rounding issue or one of the two numbers is slightly off. The same figures appear in the abstract (line 140) by reference to "64.3%," though the 36.5% does not appear there.

**Fix:** Verify the underlying data. If the actual values are 64.3% and 35.7%, change "36.5\%" to "35.7\%". If the correct split is 63.5%/36.5%, adjust accordingly. Or note explicitly that the two categories are not exhaustive (e.g., if a tiny fraction shows complete disagreement).

---

### C3. Duplicate Taisho text number across volumes: T12n0452 and T14n0452 (lines 1874, 1877)

**Text:**
- Entry 16: `T12n0452 & \Toh{199} & Maitreya ... & L`
- Entry 19: `T14n0452 & \Toh{199} & Maitreya ... & S`

**Issue:** In the Taisho numbering system, each text number is unique across the entire canon; text number 0452 belongs to a single volume. Having both `T12n0452` and `T14n0452` means one of these volume numbers is incorrect. Given that the sources differ (Li vs. Silk), this may reflect different scholars citing different Taisho IDs for the Maitreya Tusita text, but at most one can be the correct CBETA identifier.

**Fix:** Verify which volume actually contains text 0452 (likely T12). If T14n0452 does not exist, determine the correct Taisho ID for entry 19 (Silk's identification). If both entries genuinely refer to the same text, consolidate them into one entry.

---

### C4. Table 2 total (878) includes Pali-only texts, but "With Parallel" column header implies Tibetan parallels (line 914)

**Text:** Table 3 caption says: `With Parallel counts texts with an identified Tibetan or Pali parallel`

**Issue:** The total of 878 in Table 3 includes 171 texts with Pali-only parallels and no Tibetan parallel. This is documented in the footnote to Table 1, but in the text at line 829, the statement "The concordance identifies Tibetan parallels for 754 of 2,455 Taisho texts" uses the 754 figure. The 878 total is correct for "any parallel" but readers scanning Table 3 may conflate the "878 with any parallel" with the "754 with Tibetan parallels" figure. The caption does clarify "Tibetan or Pali," so this is not technically wrong, but it requires careful reading.

**Fix:** No change strictly needed, but consider adding a brief note below Table 3 reiterating: "Of the 878 texts, 754 have Tibetan parallels; the remainder have Pali parallels only."

---

### C5. Figure 1 caption references "three formats" via `\S\ref{sec:limitations}` (lines 631--632)

**Text:** `exported in three formats (\S\ref{sec:limitations})`

**Issue:** The three export formats (JSON, CSV, TEI XML) are discussed in Section 7, "Limitations and Data Availability." Referencing a section called "Limitations" for the export format information is somewhat misleading, as readers might expect a dedicated subsection on outputs.

**Fix:** This is a minor organizational concern. Consider either adding a separate label/subsection for the data formats portion of Section 7, or simply changing the reference to say "(\S\ref{sec:limitations}, Data Availability)" to direct readers more precisely.

---

## Important (grammar, consistency, terminology)

### I1. British spelling: "Catalogues" (line 399)

**Text:** `CBETA Digital Database of Buddhist Tripi\d{t}aka Catalogues`

**Issue:** This is the proper name of the CBETA database, so the British spelling "Catalogues" should be preserved as it appears in the official title. However, note that the bib entry (line 130) also uses "Catalogues." If the official CBETA name uses this spelling, it is correct to preserve it. No change needed, but flagged for awareness.

**Fix:** No change needed; this is the official name.

---

### I2. Potential inconsistency: "Conflict Handling" subsection (line 672) has no `\label{}`

**Text:** `\subsection{Conflict Handling}`

**Issue:** This subsection has no label, and no other part of the paper references it directly. However, for completeness and in case future cross-references are needed, it would be consistent to add one.

**Fix:** Add `\label{sec:conflicts}` after the subsection heading.

---

### I3. "Illustrative Concordance Entries" subsection (line 698) has no `\label{}`

**Text:** `\subsection{Illustrative Concordance Entries}`

**Issue:** Same as I2: no label for this subsection.

**Fix:** Add `\label{sec:examples}` (or similar) after the subsection heading.

---

### I4. Inconsistent use of "nine" vs. specific counts when referring to sources

**Text (line 307):** `nine independent data sources`
**Text (line 626):** `Eight catalog sources and published scholarly citations`
**Text (line 694):** `nine catalog sources`

**Issue:** Line 694 says "nine catalog sources," but earlier the paper distinguishes eight catalog sources from one scholarly source. Line 694 should say "nine data sources" or "nine sources" rather than "nine catalog sources," since the scholarly citations are not a catalog.

**Fix:** Change line 694 from "nine catalog sources" to "nine data sources" or "nine sources."

---

### I5. The "Source Agreement" subsection (line 684) subsumes results that properly belong to Section 5

**Text:** `Of 722 texts with Tohoku data from two or more independent sources, the analysis reveals 64.3\% full agreement...`

**Issue:** This subsection sits within Section 3 (Merging Methodology) but reads more like an analysis result. This is a structural choice rather than an error; flagged as a minor consistency note.

**Fix:** No change strictly needed, though the author could consider whether this material would fit better in Section 5 (Source Reliability).

---

### I6. "na\"ive" (lines 142, 1181, 1815) -- consistent rendering

**Text:** `na\"\i ve`

**Issue:** This renders correctly as "naive" in LaTeX. Just confirming consistent usage across three occurrences. All three are correct.

**Fix:** No change needed.

---

### I7. Sentence beginning with number (line 804)

**Text:** `The great majority (2,688 entries) are classified as \texttt{parallel}`

**Issue:** 2,688 entries is the total classified as "parallel." This should be verified against the actual data. The paper also says 44 entries are classified as "chinese_to_tibetan." The total of classified entries would be 2,688 + 44 = 2,732. This should equal the total number of individual Taisho-to-Tohoku links (or be close to it). Cross-check against the 1,381 links figure at line 695, which refers to "individual Taisho-to-Tohoku links." The 2,732 figure is roughly double the 1,381 (because 2,732 includes both Tohoku and Otani entries, since "Each Otani number inherits the classification of its parent Tohoku number" per line 812). Verify this is consistent.

**Fix:** Verify that 2,688 + 44 = 2,732 is the correct total of classified entries in the concordance.

---

### I8. Missing comma before "and" in compound sentence (line 143-146)

**Text:** `resolution. This article presents both the computational methodology and its implications for Tibetan studies, examining what the coverage patterns reveal...`

**Issue:** The abstract transitions abruptly from the discussion of source agreement/error propagation to "This article presents..." without a paragraph break (the abstract is a single block). The two topics feel jarring without a transitional phrase. Consider adding a sentence break or a brief transition.

**Fix:** Consider inserting a line break or adding transitional language, e.g., "\\ \noindent" before "This article presents..." or rewording as "The present article presents..."

---

### I9. "analyses" (line 1443)

**Text:** `stylistic analyses`

**Issue:** This is correct American English plural. No change needed.

**Fix:** No change needed.

---

### I10. Minor punctuation: semicolons in abstract keywords (line 154)

**Text:** `Kangyur; Tengyur; Taish\=o; concordance; Tibetan canon; cross-canon reference; provenance tracking; digital humanities`

**Issue:** This is standard practice. No change needed.

**Fix:** No change needed.

---

## Minor (style, suggestions, polish)

### M1. Comma splice at line 143--144

**Text:** `...creating a non-independence problem for naive majority-based conflict resolution. This article presents both the computational methodology and its implications for Tibetan studies, examining what the coverage patterns reveal...`

**Issue:** The transition from the technical finding about non-independence to "This article presents" is slightly abrupt within a single abstract paragraph. Not a grammatical error per se, but the jump in topic is noticeable.

**Fix:** Consider adding a brief sentence break or transitional phrase: "The concordance data are freely available for download." could be moved earlier, or a brief bridge sentence could be added.

---

### M2. "Scholarly citations" source appears in table (line 348) and separately in the figure

**Text (Table 1, line 348):** `Scholarly citations & 41 & $\sim$30 & $\sim$31 & Li 2021, Silk 2019, etc.`

**Issue:** The table groups scholarly citations with the other sources, but the paper text categorizes them separately. The table uses the heading "Published scholarship" which is fine. No inconsistency, just noting the organizational choice.

**Fix:** No change needed.

---

### M3. Inconsistent use of "~" (non-breaking space) before citations

**Text (line 181):** `\citep{zacchetti2021, radich2015}` (no preceding tilde)
**Text (line 169):** `\citep[see, e.g.,][]{harrison2008}` (no preceding tilde)

**Issue:** Some LaTeX style guides recommend `~\citep{}` to prevent line breaks before citations. Usage throughout is inconsistent but functional.

**Fix:** Consider systematically adding `~` before `\citep{}` and `\citet{}` throughout.

---

### M4. Long footnote on Prajnaparamita texts (lines 1238--1265)

**Text:** The footnote listing six texts without Tibetan parallels spans 27 lines.

**Issue:** This is extremely long for a footnote. It contains useful information but might be better as an appendix entry or a separate table.

**Fix:** Consider moving this content to an appendix, or presenting it as a small inline table. If kept as a footnote, no grammatical issues.

---

### M5. Sentence with potential ambiguity (line 508)

**Text:** `\Toh{351} (T03n0171) and \Toh{353} (T03n0156) are \skt{avad\=ana}-style tales.`

**Issue:** This says Toh 351 corresponds to T03n0171. But in the scholarly table (entry 21, line 1879), T14n0559 also maps to Toh 351. If these are genuinely two different Chinese texts that both parallel the same Tibetan text (a many-to-one mapping from the Chinese side), this is fine but may confuse readers who notice both mappings.

**Fix:** No change needed if both mappings are correct (many-to-one). If T14n0559 -> Toh 351 is actually from Silk's identification of a separate Chinese text, it is properly documented.

---

### M6. "two Peking-only texts" phrasing (lines 1501--1503)

**Text:** `while two Peking-only texts (Otani~368, parallel to T20n1060; and Otani~398, parallel to T21n1253) appear in the Peking but not the Derge.`

**Issue:** The semicolon before "and" is unusual. A comma would be more standard since the listed items are short. However, semicolons between items containing internal commas is acceptable style.

**Fix:** Optional: change "; and" to ", and" since the internal structure does not require semicolon separation: `(Otani~368, parallel to T20n1060, and Otani~398, parallel to T21n1253)`.

---

### M7. "Topic models" footnote placement (line 1441)

**Text:** `Topic models,\footnote{Statistical methods for discovering latent thematic structure...} stylistic analyses, and text-reuse detection can be validated...`

**Issue:** The footnote interrupts a comma-separated list. The footnote marker appears after "models," which places it in a slightly awkward position within the list.

**Fix:** Consider moving the footnote to after the sentence: `Topic models, stylistic analyses, and text-reuse detection can be validated...\footnote{Topic models are statistical methods...}` or placing it at "Topic models" without the interrupting comma.

---

### M8. Taisho text numbering range (lines 238--239)

**Text:** `2,920 canonical texts numbered across 85 of its 100 volumes, created the identifier system (T01n0001 through T85n2920)`

**Issue:** The paper earlier says the corpus comprises "volumes 1--55 and 85" (the canonical core of 2,455 texts). The 2,920 figure represents the entire canonical portion (all 85 volumes). These numbers are consistent but readers should note the different scopes. No error, but worth double-checking: does the Taisho canonical section really end at T85n2920?

**Fix:** Verify that text 2920 is indeed the last canonical text (volumes 56--84 contain supplementary materials but still have Taisho numbers). The claim that texts are "numbered across 85 volumes" might need nuance if some supplementary volumes also contain numbered canonical texts.

---

### M9. "Scholarly citations" count: "41 links" (line 468) vs. "41 entries" (line 1832)

**Text (line 468):** `These contribute 41 links with full bibliographic attribution`
**Text (line 1832):** `These 41 entries from three sources`

**Issue:** Both say 41, which is consistent. However, the scholarly table (Appendix B) actually has 41 rows. Let me verify: rows 1--32 (Chinese-to-Tibetan) + rows 33--41 (cross-school) = 32 + 9 = 41. Correct.

**Fix:** No change needed.

---

### M10. "downstream databases" (line 141) -- vague reference

**Text:** `error propagation from the Lancaster catalog to downstream databases creating a non-independence problem`

**Issue:** "Downstream databases" is somewhat vague in the abstract. The body text specifies these as Muller and CBETA Jinglu Sanskrit, but abstract readers won't know this.

**Fix:** Optional: change to "error propagation from the Lancaster catalog to dependent sources" for slightly more precision within the abstract.

---

### M11. Figure 1 shows only 8 source boxes, not 9 (the "Scholarly citations" node is separate)

**Text (line 590):** The dashed group box label says `Catalog sources (\S\ref{sec:sources})`

**Issue:** The figure's dashed box contains 8 sources and labels them "Catalog sources." The "Scholarly citations" node enters from the right, outside the dashed box. This accurately represents the architecture (8 catalog + 1 scholarly), but the group box label "Catalog sources" is slightly misleading since SuttaCentral and rKTs are not traditional "catalogs." The paper itself uses the broader term "data sources."

**Fix:** Consider changing the group box label from "Catalog sources" to "Data sources" to match the paper's terminology.

---

### M12. "T05--07n0220" formatting (line 926)

**Text:** `T05--07n0220`

**Issue:** This range notation is unusual. It means the text spans Taisho volumes 5 through 7 with text number 0220, which is a legitimate way to express it. However, the en-dash between volume numbers might confuse readers unfamiliar with the notation.

**Fix:** Consider clarifying: `T05n0220--T07n0220` or `T0220 (vols.~5--7)`.

---

### M13. "the concordance data are" vs. "the concordance data is" (lines 150, 1380, 1517)

**Text:** `The concordance data are freely available for download.`

**Issue:** "Data" is used with plural verb throughout, which is correct formal academic English. Consistent across all instances. No change needed.

**Fix:** No change needed.

---

### M14. Toh 897 vs. Toh 691 for T20n1060 (lines 510, 1886)

**Text (line 510):** `the thousand-armed Avalokiteshvara dharani (Toh 897, corresponding to T20n1060)`
**Text (line 1886):** `28 & T20n1060 & \Toh{691} & Sahasrabhuja dharani & L, S`

**Issue:** Line 510 says T20n1060 corresponds to Toh 897, but the scholarly table entry 28 says T20n1060 corresponds to Toh 691. These are different Tohoku numbers. This is a potential factual inconsistency. It could be a legitimate one-to-many mapping (T20n1060 maps to both Toh 691 and Toh 897), or one of the numbers is wrong.

**Fix:** Verify whether T20n1060 genuinely maps to both Toh 897 and Toh 691, or whether one is an error. If it maps to both, clarify in the text. If only one is correct, fix the incorrect reference.

---

### M15. "Chos kyi rgya mo" (line 1870) -- Tibetan in italics via \skt{} command

**Text:** `\skt{Chos kyi rgya mo}`

**Issue:** Entry 12 in the scholarly table uses `\skt{}` for what appears to be Wylie transliteration of a Tibetan title, not a Sanskrit title. The `\skt{}` command is defined for Sanskrit (IAST) formatting. This should use `\wy{}` for Wylie transliteration.

**Fix:** Change `\skt{Chos kyi rgya mo}` to `\wy{chos kyi rgya mtsho}` (or the correct Wylie form). Verify the correct Tibetan title for Toh 256.

---

### M16. "Toh~$\to$~K~$\to$~T" (line 423) and "K~$\to$~T~+~Toh" (line 423)

**Text:** `(Toh~$\to$~K~$\to$~T rather than K~$\to$~T~+~Toh)`

**Issue:** These directional notations are clear, but arrows are Unicode symbols handled via math mode ($\to$). This is fine for rendering. No change needed.

**Fix:** No change needed.

---

### M17. Repeated explanation of "Kangyur" and "Tengyur" meanings

**Text (line 134):** `Kangyur ("translated word [of the Buddha]")`
**Text (line 188):** `Kangyur (\tib{...} \wy{bka' 'gyur}, "translated word [of the Buddha]")`

**Issue:** The glosses are given in the abstract (line 134, English only) and again in the introduction (line 188, with Tibetan script and Wylie). This is standard practice (abstract glosses are for standalone reading). No issue.

**Fix:** No change needed.

---

### M18. Appendix B: "nineteen" vs. "19" corroborated entries (line 1907)

**Text:** `Of the 41 entries, 19 are independently corroborated by at least one or more catalog sources`

**Issue:** "At least one or more" is redundant. "At least one" means one or more. Choose one phrasing.

**Fix:** Change to: `Of the 41 entries, 19 are independently corroborated by at least one catalog source` or `...by one or more catalog sources`.

---

### M19. "The remaining 22 (marked \dag)" count (line 1909)

**Text:** `The remaining 22 (marked~\dag)`

**Issue:** Verify: 41 - 19 = 22. Checking the table: entries with \dag markers are: 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 21, 24, 25, 33, 34, 35, 36, 37, 38, 39, 40, 41 = 22 entries. Correct.

**Fix:** No change needed.

---

### M20. "13 entries lack catalog confirmation" vs. actual count (line 1918)

**Text:** `Among the Chinese-to-Tibetan translations, 13 entries lack catalog confirmation`

**Issue:** Counting \dag entries in the Chinese-to-Tibetan section (entries 1--32): entries 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 21, 24, 25 = 13 entries. Correct.

**Fix:** No change needed.

---

### M21. "all nine entries lack catalog confirmation" (line 1922)

**Text:** `Among the cross-school identifications, all nine entries lack catalog confirmation`

**Issue:** Cross-school entries are 33--41 = 9 entries, all marked \dag. Correct.

**Fix:** No change needed.

---

### M22. "Twenty-one pairs are independently attested by both Li and Silk" (line 1925)

**Text:** `Twenty-one pairs are independently attested by both Li and Silk`

**Issue:** Counting entries with both "L" and "S" in the Src column: entries 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 18, 19, 20, 22, 23, 24, 25, 28, 29, 30, 31 = 21 entries. Correct.

**Fix:** No change needed.

---

### M23. Line 1870: "Chos kyi rgya mo" -- possible typo for "chos kyi rgya mtsho"

**Text:** `\skt{Chos kyi rgya mo}`

**Issue:** In addition to the \skt{} vs. \wy{} formatting issue (M15), the Wylie "rgya mo" might be a truncation of "rgya mtsho" (ocean). Toh 256 is traditionally identified as related to a "Dharma Drum" or similar title. The Wylie form needs verification.

**Fix:** Verify the correct Tibetan title for Toh 256 and ensure proper Wylie transliteration.

---

### M24. Apostrophe in "Monk's Staff" (lines 1884, 1885)

**Text:** `Monk's Staff sutra`

**Issue:** The apostrophe in "Monk's" is fine. However, "sutra" should arguably be rendered as `s\=utra` with the macron for consistency with the rest of the paper, or the whole title should use \skt{}.

**Fix:** Consider changing to `Monk's Staff \skt{s\=utra}` for consistency.

---

### M25. Harrison 2008 title uses British "Analysed" (bib line 82)

**Text:** `Analysed in the Light of Recent Sanskrit Manuscript Discoveries`

**Issue:** This is the original published title of Harrison's article. British spelling in titles of cited works should be preserved per the user's convention (American spellings throughout except in titles of cited works).

**Fix:** No change needed; this is the original title.

---

### M26. Sentence at lines 1100--1103 could be tightened

**Text:** `From the Chinese side, approximately 1,701 Taisho texts lack Tibetan parallels. These include not only expected categories (Chinese commentaries, Chan school texts, catalogs) but also some texts with Indic originals.`

**Issue:** 2,455 - 754 = 1,701. The math checks out. The sentence is fine.

**Fix:** No change needed.

---

### M27. "Sameness sutra" (line 1875) -- missing diacritics

**Text:** `Sameness s\=utra`

**Issue:** "Sameness sutra" is an English descriptive title. Using s\=utra with the macron is fine. However, a Sanskrit title would be more precise if available. This is a matter of what Silk 2019 identifies the text as.

**Fix:** If Silk provides a Sanskrit title, use it. Otherwise, acceptable as is.

---

### M28. Line 508: Toh 353 corresponds to T03n0156

**Text:** `\Toh{353} (T03n0156)`

**Issue:** In the scholarly table entry 3, T03n0156 maps to Toh 353 with identification "Requiting Kindness" (from Li and Silk). This is consistent with line 508. No error.

**Fix:** No change needed.

---

### M29. Consistency: "sutra" vs. "s\=utra" in running text

**Text (line 1510):** `by mapping Agama sutra references`

**Issue:** "sutra" appears without diacritics here. Elsewhere the paper consistently uses `s\=utra` with the macron (e.g., lines 296, 434, 500, 878, 949, etc.).

**Fix:** Change `sutra` on line 1510 to `s\=utra` for consistency.

---

### M30. "Scholarly Parallel Identifications" appendix title uses plural (line 1828)

**Text:** `\section{Scholarly Parallel Identifications}`

**Issue:** Consistent with content. No change needed.

**Fix:** No change needed.

---

### M31. Abstract: "canonical core (volumes 1--55 and 85)" (lines 130--131)

**Text:** `754 of the 2,455 Taisho texts in the canonical core (volumes 1--55 and 85)`

**Issue:** This parenthetical is important context. The footnote immediately following explains volumes 56--84. This is well-structured.

**Fix:** No change needed.

---

## Summary of Findings Requiring Action

| # | Severity | Line(s) | Issue | Action |
|---|----------|---------|-------|--------|
| C1 | Critical | 596, 629 | Hardcoded `\S3.4` reference | Add label, use `\ref{}` |
| C2 | Critical | 687--688 | 64.3% + 36.5% = 100.8% | Verify and fix percentages |
| C3 | Critical | 1874, 1877 | T12n0452 vs T14n0452 duplicate text number | Verify correct volume number |
| M14 | Critical | 510, 1886 | T20n1060 maps to Toh 897 (text) vs Toh 691 (table) | Verify and reconcile |
| I4 | Important | 694 | "nine catalog sources" should be "nine data sources" | Fix wording |
| M15 | Important | 1870 | `\skt{}` used for Wylie Tibetan text | Change to `\wy{}` |
| M18 | Important | 1907 | "at least one or more" -- redundant | Fix phrasing |
| M23 | Important | 1870 | "rgya mo" possibly truncated from "rgya mtsho" | Verify Wylie |
| M29 | Important | 1510 | "sutra" missing diacritics | Change to `s\=utra` |
| M1 | Minor | 143--144 | Abrupt transition in abstract | Consider adding bridge |
| M4 | Minor | 1238--1265 | 27-line footnote | Consider appendix |
| M6 | Minor | 1501--1503 | Semicolon before "and" in short list | Consider comma |
| M7 | Minor | 1441 | Footnote interrupting comma-separated list | Consider repositioning |
| M12 | Minor | 926 | "T05--07n0220" formatting | Consider clarifying |
| M24 | Minor | 1884--1885 | "sutra" without macron in table | Consider `s\=utra` |

**Overall Assessment:** The paper is extremely well-written and carefully constructed. The transliteration rule is followed consistently throughout (every instance of CJK, Tibetan, and Devanagari script is accompanied by romanized transliteration). American English is used throughout (no British spellings detected in the author's own text). There are no em-dashes. Cross-references are almost entirely correct, with the one exception of the hardcoded `\S3.4`. The table totals check out (2,455 texts, 878 with parallels). The most important items to address are the four critical findings: the hardcoded section reference, the percentage sum exceeding 100%, the possible T12/T14 volume number conflict, and the Toh 897/691 discrepancy for T20n1060.
