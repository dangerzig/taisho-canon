# Proofread Report (Second Pass): "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-03-03
**Reviewer:** Claude Opus 4.6

This is a second-pass proofread. All findings from the earlier report (`reviews/paper_proofread_2026_03_03.md`) were cross-checked against the current file to confirm which were applied. The current report covers only **new or remaining** issues.

---

## Verification of Previous Proofread Fixes

| Previous # | Issue | Status |
|---|---|---|
| C1 | Hardcoded `\S3.4` | **Fixed.** `\label{sec:agreement}` added; both refs now use `\S\ref{sec:agreement}`. |
| C2 | Percentages 64.3% + 36.5% = 100.8% | **Fixed.** Now 63.5% + 36.5% = 100.0%. |
| C3 | Duplicate T12n0452 / T14n0452 | **Fixed.** T12n0452 entry removed; table now has 40 entries. |
| I4 | "nine catalog sources" | **Fixed.** Now "nine data sources" (line 695). |
| M14 | Toh 897 vs Toh 691 for T20n1060 | **NOT FIXED.** See C1 below. |
| M15 | `\skt{}` used for Wylie text | **Fixed.** Now `\wy{chos kyi rgya mo}` (line 1871). |
| M18 | "at least one or more" redundancy | **Fixed.** Now "at least one catalog source" (line 1907). |
| M23 | "rgya mo" possibly truncated from "rgya mtsho" | **NOT FIXED.** See I1 below. |
| M29 | "sutra" without macron on line 1510 | **Fixed.** Now "s\=utra" (line 1511). |
| All others | No-change-needed items or optional suggestions | N/A |

---

## Critical (factual errors, numerical inconsistencies)

### C1. Toh 897 vs. Toh 691 for T20n1060 (STILL UNFIXED from previous proofread M14)

**Line 510:**
```
thousand-armed Avalokite\'{s}vara \skt{dh\=ara\d{n}\={\i}} (\Toh{897}, corresponding to T20n1060)
```

**Line 1886 (Table entry 27):**
```
27 & T20n1060 & \Toh{691} & Sahasrabhuja \skt{dh\=ara\d{n}\={\i}} & L, S & Lnc, CBT
```

**Issue:** Line 510 in the body text says T20n1060 corresponds to Toh 897. The scholarly table (entry 27) says T20n1060 corresponds to Toh 691. These are different Tohoku numbers. At least one must be wrong. If T20n1060 genuinely maps to both Toh numbers (a one-to-many mapping), the body text should say so and not present only one.

**Fix:** Verify the correct Tohoku number(s) for T20n1060 and reconcile the two references.

---

### C2. Table 2 arithmetic: 488 + 115 = 603, not 605

**Lines 831--832, 843--846:**
```
488 of 1,108 Kangyur texts (44.0%) and 115 of 3,461 Tengyur texts (3.3%),
for a total of 605 unique Tohoku numbers
```

Table 2 (tab:tibetan):
| Section | In Concordance | Total |
|---|---|---|
| Kangyur (Toh 1--1108) | 488 | 1,108 |
| Tengyur (Toh 1109--4569) | 115 | 3,461 |
| **Total unique Toh** | **605** | **4,569** |

**Issue:** 488 + 115 = 603, not 605. The total column for the canon (1,108 + 3,461 = 4,569) adds up correctly, confirming the Kangyur and Tengyur ranges are exhaustive and contiguous. So 605 unique Toh numbers should equal the Kangyur count plus the Tengyur count, but the current figures are off by 2. Either 605 should be 603, one of the row values (488 or 115) is wrong, or there are 2 Toh numbers being counted that don't fall into either row (which shouldn't happen given the defined ranges).

**Fix:** Verify the correct values from the data. If the total is truly 605, then one of the row counts is 2 too low (likely Kangyur 490 or Tengyur 117). If the rows are correct, change the total to 603 and update 13.2% accordingly (603/4569 = 13.2%, so the percentage may still round to 13.2%).

---

### C3. Explanation of uncorroborated entries is inaccurate (line 1918)

**Text (lines 1917--1921):**
```
Among the Chinese-to-Tibetan translations, 12 entries lack catalog confirmation
because they involve section-level mappings within larger Taish\=o texts
(particularly six chapters of the Ratnak\=u\d{t}a, T11n0310) that standard
catalogs do not index individually.
```

**Issue:** The "because" clause implies all 12 uncorroborated Chinese-to-Tibetan entries lack confirmation because they are section-level mappings. But only 6 of the 12 are Ratnakuta chapter mappings (entries 6--11). The other 6 uncorroborated entries are:
- Entry 12: T12n0354 (Toh 256), a standalone text
- Entry 15: T12n0397 (Toh 237), a standalone text
- Entry 17: T13n0410 (Toh 242), a standalone text
- Entry 20: T14n0559 (Toh 351), a standalone text
- Entry 23: T17n0653 (Toh 123), a standalone text
- Entry 24: T17n0784 (Toh 359), a standalone text

These are not section-level mappings. They lack catalog confirmation for other reasons (e.g., they are identifications by a single scholar without independent catalog attestation).

**Fix:** Revise the explanation to accurately describe both groups. For example: "Among the Chinese-to-Tibetan translations, 12 entries lack catalog confirmation. Six of these are chapter-level mappings within the \skt{Ratnak\=u\d{t}a} (T11n0310) that standard catalogs do not index individually; the remaining six are standalone texts identified by a single scholar without independent catalog attestation."

---

## Important (grammar, consistency, factual precision)

### I1. "chos kyi rgya mo" -- still possibly incorrect Wylie (unfixed M23)

**Line 1871:**
```
12 & T12n0354 & \Toh{256} & \wy{chos kyi rgya mo} & S & \dag
```

**Issue:** The M15 fix (changing `\skt{}` to `\wy{}`) was correctly applied, but the underlying Wylie form "chos kyi rgya mo" has not been verified. Toh 256 is the \skt{Dharmasagara} or \skt{Dharmasamudra} ("Ocean of Dharma"), which in Wylie would be "chos kyi rgya mtsho" (not "rgya mo"). "rgya mo" means "great/vast" while "rgya mtsho" means "ocean." This may be a transcription error.

**Fix:** Verify the correct Wylie title for Toh 256. If it is indeed "ocean of dharma," correct to `\wy{chos kyi rgya mtsho}`.

---

### I2. "sutra" without macron (line 433)

**Text:**
```
links were extracted by mapping individual \=Agama sutra references
```

**Issue:** "sutra" appears without diacritics. Everywhere else in the paper, the Sanskrit word uses the macron: "s\=utra." This was missed in the previous proofread (which only caught the instance at line 1510, now fixed).

**Fix:** Change `sutra` to `s\=utra` on line 433.

---

### I3. "sutta" formatting inconsistency (lines 662 vs. 970)

**Line 662:**
```
Sanskrit titles, Chinese titles, Tibetan titles, and P\=ali sutta IDs
```

**Line 970:**
```
Kangyur s\=utra, a Chinese \=Agama text, and a P\=ali \skt{sutta} all
```

**Issue:** Line 662 uses plain "sutta" (roman type), while line 970 uses `\skt{sutta}` (italic). For a Pali term used as a foreign word in English prose, italic is standard academic convention. The inconsistency should be resolved.

**Fix:** Change `sutta` on line 662 to `\skt{sutta}` for consistency with line 970.

---

### I4. Scholarly table entries out of Taisho order (entries 16--17)

**Lines 1875--1876:**
```
16 & T14n0452 & \Toh{199} & Maitreya Tu\d{s}ita ascension & L, S & ...
17 & T13n0410 & \Toh{242} & Sameness s\=utra & S & \dag
```

**Issue:** Entry 16 (T14n0452, volume 14) precedes entry 17 (T13n0410, volume 13). Within a scholarly table ordered by Taisho ID, T13 should come before T14. Similarly, entry 18 (T13n0411) also has volume 13. The sequence should be T13n0410, T13n0411, T14n0452, T14n0482, T14n0559, not the current ordering of T14n0452, T13n0410, T13n0411, T14n0482, T14n0559.

**Fix:** Reorder entries 16--20 into ascending Taisho order:
```
16 & T13n0410 & \Toh{242} & ...
17 & T13n0411 & \Toh{239} & ...
18 & T14n0452 & \Toh{199} & ...
19 & T14n0482 & \Toh{174} & ...
20 & T14n0559 & \Toh{351} & ...
```

---

### I5. Scholarly table: "Forty-Two Chapter S\=utra" mapped to Toh 359 (entry 24)

**Line 1883:**
```
24 & T17n0784 & \Toh{359} & Forty-Two Chapter S\=utra & L, S & \dag
```

**Issue:** In the body text (line 525--527), the same text T17n0784 is described but no Tohoku number is explicitly given there. The text calls it "the \zh{四十二章經}" and says it appears "in the rKTs list of Chinese-to-Tibetan translations." But the rKTs section (line 523) says "Two rKTs entries also lack Tohoku numbers." If T17n0784 is one of those entries that lacks a Tohoku number in rKTs, how is Toh 359 determined? This Toh number must come from Li or Silk (both listed as sources). Worth verifying that Toh 359 is correct.

**Fix:** Verify that Toh 359 is the correct Tohoku number for the Tibetan translation of T17n0784.

---

## Minor (style, suggestions, polish)

### M1. Semicolon before "and" in parenthetical list (lines 1502--1503)

**Text:**
```
(Otani~368, parallel to T20n1060, and Otani~398, parallel to T21n1253)
```

**Issue:** The previous proofread (M6) suggested changing "; and" to ", and." This was applied. However, the current phrasing is fine as is. No further action needed.

**Fix:** No change needed.

---

### M2. Line 1526 slightly redundant phrasing

**Text:**
```
\textbf{JSON} (JavaScript Object Notation, a standard structured data
format) provides a format suitable for automated querying by software:
```

**Issue:** "a standard structured data format) provides a format suitable for..." uses "format" twice in close proximity. Mildly awkward.

**Fix:** Consider: "...a standard structured data format) supports automated querying by software:" or "...a standard structured data format) is suitable for automated querying:"

---

### M3. Footnote on GitHub (line 429) is generic

**Text (lines 429--432):**
```
\footnote{Hosted on GitHub (\url{https://github.com}), a
platform for sharing code and data. SuttaCentral, 84000, rKTs, and
the MITRA project all maintain publicly accessible repositories
there.}
```

**Issue:** The footnote defines GitHub for a general audience. This is reasonable for a humanities journal, but the URL `https://github.com` is the homepage, not a specific repository. If the intent is to tell readers where to find the data, pointing to the specific repositories would be more useful. However, this is a design choice, not an error.

**Fix:** Optional. No change strictly necessary.

---

### M4. "T05--07n0220" formatting (line 927)

**Text:**
```
corresponding to T05--07n0220,
```

**Issue:** Flagged in the previous proofread (M12) as potentially confusing notation. Still present. The en-dash notation for a volume range within a single Taisho ID is unusual and may confuse readers.

**Fix:** Consider clarifying: "corresponding to T0220 (vols.~5--7)," or "corresponding to T05n0220--T07n0220,"

---

### M5. Verbatim source names don't match the nine named sources (lines 710--727)

**Text (from the JSON example):**
```
{"source": "84000_tei_refs"},
{"source": "acmuller_tohoku"},
{"source": "cbeta_sanskrit"},
{"source": "cbeta_tibetan"},
{"source": "existing"},
{"source": "lancaster"},
{"source": "lancaster_full"}
```

**Issue:** Line 732 says "Seven of the nine sources (all except rKTs and SuttaCentral) agree." But the JSON listing shows 7 source entries with internal code names, two of which ("existing" and "lancaster_full") don't clearly correspond to any of the nine named sources in Table 1. "existing" appears to be a prior concordance (not one of the nine), and "lancaster_full" appears to be a second Lancaster scrape (not a separate source). This could confuse careful readers who try to match the JSON source names to the nine sources listed in the paper.

**Fix:** Consider adding a brief parenthetical or footnote explaining that the JSON source identifiers are internal codes, e.g., "Seven sources attest this mapping (shown with their internal identifiers in the JSON)." Alternatively, map the internal names to the paper's source names in the example.

---

### M6. Long footnote on Prajnaparamita texts (lines 1239--1266)

**Issue:** Flagged in the previous proofread (M4). Still present as a 27-line footnote. This remains a stylistic concern; the content is valuable but extremely long for a footnote.

**Fix:** No change strictly needed, but consider moving to an appendix.

---

### M7. Footnote placement within comma-separated list (line 1442)

**Issue:** Flagged in the previous proofread (M7). The footnote for "Topic models" still interrupts a comma-separated list. This is a minor style issue.

**Fix:** No change strictly needed; optional repositioning.

---

### M8. Potential ambiguity in "Twelve centuries later" (line 1624)

**Text:**
```
The Denkarma's compilers organized translations by origin,
distinguishing Indian from Chinese sources. Twelve centuries later,
computational methods can identify those same cross-canon
relationships
```

**Issue:** The Denkarma is dated c. 812 CE (line 222). Twelve centuries later would be c. 2012, not 2026. More precisely, 1,214 years have elapsed. "Twelve centuries" is an approximation, but "more than twelve centuries later" would be slightly more accurate.

**Fix:** Optional. Change "Twelve centuries later" to "More than twelve centuries later" for precision.

---

## Summary of Findings Requiring Action

| # | Severity | Line(s) | Issue | Action |
|---|----------|---------|-------|--------|
| C1 | Critical | 510, 1886 | Toh 897 vs Toh 691 for T20n1060 (STILL UNFIXED) | Verify and reconcile |
| C2 | Critical | 831--832, 843--846 | 488 + 115 = 603, not 605 | Verify data and fix arithmetic |
| C3 | Critical | 1917--1921 | "12 entries... because section-level mappings" only covers 6 of 12 | Revise explanation |
| I1 | Important | 1871 | "rgya mo" possibly incorrect for "rgya mtsho" | Verify Wylie |
| I2 | Important | 433 | "sutra" without macron | Change to "s\=utra" |
| I3 | Important | 662 | "sutta" not italicized | Change to `\skt{sutta}` |
| I4 | Important | 1875--1876 | Entries 16--20 out of Taisho order | Reorder |
| I5 | Important | 1883 | Toh 359 for T17n0784 | Verify |
| M2 | Minor | 1525--1526 | "format...format" redundancy | Rephrase |
| M4 | Minor | 927 | "T05--07n0220" unusual notation | Consider clarifying |
| M5 | Minor | 710--727 | JSON source names differ from named sources | Consider note |
| M8 | Minor | 1624 | "Twelve centuries" approximation | Consider "More than twelve" |

---

## Overall Assessment

The paper is in excellent shape overall. The previous proofread's fixes were almost all correctly applied (8 of 10 actionable items resolved). The remaining issues fall into three categories:

1. **Two carry-over items from the first proofread** (C1: Toh 897/691 discrepancy, I1: "rgya mo" Wylie verification) that were flagged previously but not yet addressed.

2. **One new arithmetic issue** (C2: 488 + 115 = 603, not the stated 605) that was not caught in the first proofread. This affects Table 2 and the text on line 832.

3. **One new factual precision issue** (C3: the explanation of uncorroborated entries inaccurately implies all 12 lack confirmation because of section-level mappings, when only 6 do).

The remaining items are consistency/style issues (bare "sutra" on line 433, "sutta" formatting, table ordering, minor phrasing).

Transliteration rule compliance: Excellent. Every instance of CJK, Tibetan, and Devanagari script is accompanied by romanized transliteration.
American English: Fully consistent (no British spellings in author's text).
Em-dashes: None in running text.
Cross-references: All use `\ref{}` correctly.
