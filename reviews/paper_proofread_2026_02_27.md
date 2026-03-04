# Proofread: zigmond-tibetan-concordance.tex

**Date:** 2026-02-27
**Reviewer:** Claude (automated proofread)
**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Bib file:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/references.bib`

---

## Summary

The paper is well-written and carefully structured. I found issues in the following categories: one grammar error, one probable factual error (Sanskrit title), one internal date inconsistency, one numerical inconsistency, a bib entry mismatch with text, two bib entries naming target journals, a few areas where numbers could confuse readers, and minor style/consistency items. No broken cross-references, no `??` citations, no bare non-Latin script (outside verbatim blocks), and no British spellings were found.

---

## Critical Issues

### 1. Grammar Error: Subject-Verb Disagreement (Line 847)

**Line 847:**
> this material was composed in Chinese, never had an Indic original, and were never translated into Tibetan.

The subject is "this material" (singular), so "were never" should be "was never."

**Fix:** Change "and were never translated" to "and was never translated."

---

### 2. Probable Factual Error: Sanskrit Title "Damamukonidhi" (Line 486)

**Line 486:**
> the \skt{Damamukonidhi} ("Wise and Foolish"), is a popular \skt{avadana} collection

The standard Sanskrit title for Toh 341 is *Damamukanidanasutra* (Skt. *Damamuka-nidana-sutra*). The form "Damamukonidhi" does not appear in any standard reference. 84000 gives the Sanskrit reconstruction as "(damamuka)"; Rigpa Wiki and other encyclopedias give "Damamuka-nidana-sutra." The form in the paper appears to be garbled.

**Fix:** Replace `\skt{Damamukonidhi}` with `\skt{Damamukanidanasutra}` or `\skt{Damamukanidana}`.

---

### 3. Internal Date Inconsistency: sgra sbyor bam po gnyis pa (Lines 255 vs. 1235)

**Line 254-255:**
> \wy{sgra sbyor bam po gnyis pa} ("Two-Volume Lexicon," early 9th cent.)

**Line 1235:**
> (c.~783 CE; see \citealp{ishikawa1990})

783 CE is late 8th century, not early 9th century. Scholarly sources confirm that a decree in the Tabo manuscript version is dated to 783 CE, while a later version in the Tibet Museum carries an 814 CE decree. The two occurrences in the paper give conflicting dates.

**Fix:** Either change "early 9th cent." at line 255 to "late 8th cent." or "c. 783 CE" to be consistent with line 1235, or use a formulation like "late 8th/early 9th cent." if the intent is to cover the range of the standardization period.

---

### 4. Numerical Inconsistency: 613 vs. 612 Kangyur Texts Without Parallels (Lines 923, 1420)

**Lines 923 and 1420:** "613 Kangyur texts without identified Chinese parallels"

But the paper states 496 of 1,108 Kangyur texts have parallels (lines 103, 679-680, 692). By arithmetic: 1,108 - 496 = **612**, not 613.

This off-by-one error appears in two places:
- Line 923: "Among the 613 Kangyur texts..."
- Line 1420: "The 613 Kangyur texts without Chinese parallels..."

Note: Line 956 also uses "613" but in a completely different context (CBETA Jinglu Tibetan entries with Taisho cross-references), so that usage is not affected.

**Fix:** Either correct 613 to 612 in both places, or adjust the 496/1,108 figures to be consistent.

---

### 5. Bib Entry Mismatch: Anthropic Model Names (Line 1659-1660 vs. references.bib line 343)

**Paper text (lines 1659-1660):**
> using Claude Haiku~4.5 for initial scoring, with escalation to Claude Sonnet~4.5 for ambiguous cases

**Bib entry `anthropic2025` (references.bib line 343):**
> title = {The {Claude} Model Family: {Claude} 3.5 {Haiku}, {Claude} 3.5 {Sonnet}, and {Claude} 3.5 {Opus}}

The paper uses models from the Claude 4.5 family (Haiku 4.5, released October 2025; Sonnet 4.5, released September 2025) but the bib entry describes the older Claude 3.5 model family. The bib title needs to be updated to match the models actually used.

**Fix:** Update the `anthropic2025` bib entry title to reference the Claude 4.5 model family, or create a new entry for the 4.5 models.

---

### 6. Presumptuous Journal Names in Bib Entries (references.bib lines 351, 358)

Per Dan's preference: never name the target journal in the paper text or filename.

**Bib entry `zigmond2026b` (line 351):**
> note = {Submitted to the \emph{Journal of the International Association of Buddhist Studies}}

**Bib entry `zigmond2026c` (line 358):**
> note = {Submitted to \emph{Digital Scholarship in the Humanities}}

**Fix:** Change both `note` fields to something like "Submitted for publication" or "In preparation."

---

## Moderate Issues

### 7. Potential Reader Confusion: "~12,346" Raw Entries (Line 322)

**Line 322:**
> The large gap between total raw entries (~12,346) and final unique Taisho texts (1,082)

But summing the "Raw Entries" column from Table 1 gives approximately 20,201 (1,478 + 4,569 + 1,395 + 382 + 8,124 + 23 + 1,108 + 457 + 45 + 2,389 + 231). The stated ~12,346 does not match. The figure may represent a different calculation (perhaps only counting entries that have Taisho cross-references, or excluding SuttaCentral's 8,124 entries many of which are Pali-only), but the mismatch is never explained in the text. A reader adding up the table will get a different number.

**Fix:** Either explain how ~12,346 was derived, or update the number to match the table. If SuttaCentral and 84000 titles are excluded from the count, state this explicitly.

---

### 8. Genre Table Does Not Sum to 2,455 "With Parallel" vs. 1,082 (Table 3 vs. Line 317)

The "With Parallel" column in Table 3 sums to 1,031, while the "After removing duplicates" row in Table 1 says 1,082. The difference (51 texts) is presumably because Table 3 does not cover all Taisho volumes (volumes 56-84 are omitted). This is not stated anywhere, and a careful reader might wonder about the discrepancy.

Note: The "Texts" column correctly sums to 2,455, consistent with the stated total.

**Suggestion:** Add a footnote to Table 3 noting that the volume ranges shown do not cover all Taisho volumes, and that the "With Parallel" total (1,031) is less than the full concordance total (1,082) because some texts in omitted volume ranges also have parallels.

---

### 9. Table 1 Includes Sanskrit Title Matching But Text Says "Ten Sources" (Lines 101, 272, 315)

The paper consistently says "ten independent data sources" (lines 101, 272, 1573, 1620), and the source reliability section distinguishes "nine catalog sources" (line 590) plus MITRA. But Table 1 (line 315) includes Sanskrit title matching as a row, making 11 rows total. The text at line 551 clarifies that "computational discovery methods (like Sanskrit title matching) are applied last," but a reader scanning the table might count 11 sources.

**Suggestion:** Consider adding a visual divider or footnote in the table clarifying that Sanskrit title matching is a derived computational method, not one of the "ten sources."

---

## Minor Issues

### 10. Inconsistent Use of "analyses" (Line 1440)

**Line 1440:**
> stylistic analyses, and text-reuse detection

"Analyses" is the standard American English plural of "analysis." This is correct and not an error. However, note that the instructions specify checking for British spellings. "Analyses" is the same in both American and British English. No change needed.

---

### 11. Chinese Characters in Verbatim Block (Line 1566)

**Line 1566 (inside `\begin{verbatim}`):**
> `<title type="chinese">長阿含經</title>`

This is bare Chinese script inside a code/verbatim block, without `\zh{}` or `\py{}`. Since it is inside a verbatim block showing XML output, `\zh{}` and `\py{}` LaTeX commands cannot be used. This is acceptable as a code example. However, if the transliteration rule is applied absolutely, the reader gets no pinyin for these characters.

**Suggestion:** Consider adding a parenthetical note before or after the verbatim block: "(*Chang Ahanjing*, 'Long Agama Sutra')" or similar, to provide transliteration for readers.

---

### 12. Possible Ambiguity: "three systematic errors" (Line 968)

**Line 968:**
> The three systematic errors matter particularly because they have propagated to dependent sources.

This follows the sentence describing five Lancaster errors (two trailing zeros, one transposition, two spurious zeros). The "three systematic errors" refers to errors 1-3 (the non-spurious-zero ones), which propagated. But a reader might wonder: why "three" when five errors were just listed? The distinction (trailing-zero and transposition errors propagated; spurious-zero errors did not) is not made explicit.

**Suggestion:** Add a brief clarification, e.g., "The three non-zero systematic errors (errors 1-3) matter particularly because they have propagated to dependent sources, while the two spurious-zero entries (errors 4-5) are confined to Lancaster."

---

### 13. First Use of "Jinglu" Without Full Translation (Line 163 vs. 349)

**Line 163:**
> CBETA Jinglu (\zh{經錄} \py{jingliu}, "catalog of scriptures")

This is the first use and correctly includes Chinese + pinyin + English. Good.

**Line 349:**
> (\zh{經錄} \py{jingliu})

Correctly repeats the Chinese + pinyin without the English translation (which was given at first use). Good.

No issue here; just noting this was checked.

---

### 14. "Four independent sources" for Heart Sutra (Line 1109-1110 vs. 1120)

**Line 1109-1110:**
> Four independent sources confirm this mapping with no disagreement.

**Line 1120:**
> The concordance's four-source agreement that both Chinese versions map to the same Tibetan text...

But the illustrative entry for T08n0251 earlier (lines 613-625) shows **nine** sources attesting Toh 21. The "four" may refer to a different count (perhaps only the sources that attest both T250 and T251 mapping to Toh 21 independently), but the discrepancy with the nine-source example is never explained.

**Suggestion:** Clarify what "four independent sources" means in context, or reconcile with the nine-source example shown earlier.

---

### 15. "Nine of the ten sources" (Line 630)

**Line 630:**
> Nine of the ten sources agree on a single Tohoku number with no conflict.

But the verbatim example (lines 614-624) shows nine entries in the provenance list, and the paper says there are ten sources. The text implies one source (presumably rKTs, which only covers Chinese-to-Tibetan translations) did not attest this mapping. This is correctly stated but might benefit from a brief parenthetical: "(all except rKTs, which covers only Chinese-to-Tibetan translations)" for clarity.

---

### 16. Redundant "see" in \citep Usage (Line 139)

**Line 139:**
> \citep[see, e.g.,][]{harrison2008}

This is correct biblatex usage. The "see, e.g.," appears before the citation. No issue.

---

### 17. Possible Infelicity: "back-translation" (Line 1119)

**Line 1118-1119:**
> \citet{nattier1992} famously argued that the Chinese short text may be a "back-translation" from Sanskrit rather than a direct translation from an Indic original.

Nattier's argument is more nuanced: she argued the Chinese short text was composed in Chinese by extracting passages from Kumarajiva's Large Perfection of Wisdom translation, then "back-translated" into Sanskrit. The phrase "back-translation from Sanskrit" is slightly ambiguous here; it could be read as translating *from* Sanskrit *back* to Chinese, which reverses Nattier's point. Nattier argues the *Sanskrit* text was a back-translation *from* the Chinese.

**Suggestion:** Reword to: "the Chinese short text may have been composed in Chinese and subsequently 'back-translated' into Sanskrit" or similar, to avoid ambiguity about the direction of the back-translation.

---

### 18. No Explicit Link Between 2,920 and 2,455 (Lines 210-211 vs. 103)

The paper says the Taisho has "2,920 canonical texts" (line 210) but the concordance covers "2,455 Taisho texts" (line 103). The difference (465 texts) is never explained. A reader might wonder why only 2,455 texts are in scope. This may be because the concordance covers only vols. 1-55 and 85 (the canonical core), excluding supplementary volumes. If so, this should be stated explicitly somewhere.

**Suggestion:** Add a brief note explaining the scope of "2,455 Taisho texts" when first introduced.

---

### 19. Possible Typo: "翔公" (Line 1068)

**Line 1068:**
> \zh{翔公} \py{Xianggong} (Liu Song, 420-479 CE)

The translator name "翔公" (*Xianggong*) appears in connection with T08n0234. The standard attribution for this text in CBETA is to 翔公 (Xianggong), which is a monastic name, but some sources give the translator as 竺法護 (Zhu Fahu / Dharmaraksa) for related texts. The attribution should be verified, though this may be correct for this specific text.

**Note:** This is flagged for verification rather than as a confirmed error.

---

## Bibliography Verification

All 28 bibliography entries were checked against web sources. Results:

| Entry | Status | Notes |
|-------|--------|-------|
| takakusu1924 | OK | Taisho Shinshu Daizokyo, 1924-1934 |
| nanjio1883 | OK | Clarendon Press, Oxford |
| ui1934 | OK | Tohoku Imperial University, 1934 |
| lancaster1979 | OK | UC Press, Berkeley |
| herrmannpfandt2008 | OK | Vienna, VOAW |
| akanuma1929 | OK | Hajinkaku Shobo, Nagoya |
| nattier1992 | OK | JIABS 15(2): 153-223 |
| buswell2014 | OK | Princeton UP, 2014 |
| harrison2008 | OK | JIABS 31(1-2): 205-249 |
| silk2019 | OK | ARIRIAB 22: 227-246 |
| li2021 | OK | RET no. 60: 174-219 |
| zigmond2026a | OK | Unpublished/in preparation |
| suttacentral | OK | URL correct |
| cbeta_jinglu | OK | URL correct |
| rkts | OK | URL correct |
| 84000 | OK | URL correct |
| bdrc | OK | URL correct |
| conze1978 | OK | Reiyukai, Tokyo, 2nd ed |
| frauwallner1956 | OK | Rome, IsMEO |
| lalou1953 | OK | J. asiatique 241: 313-353 |
| kapstein2000 | OK | Oxford UP |
| davidson2002 | OK | Columbia UP |
| snellgrove1987 | OK | Shambhala, 2 vols |
| cabezon1996 | OK | Snow Lion, Ithaca |
| openpecha_kangyur | OK | GitHub URL correct |
| schoch2013 | OK | J. Digital Humanities 2(3): 2-13 |
| sahle2016 | OK | Open Book Publishers |
| binding2016 | OK | Int J Digital Libraries 17(1): 5-21 |
| barnett2025 | OK | RET no. 74: 5-43 |
| kyogoku2025 | OK | RET no. 74: 187-220 |
| schwartz2025 | OK | RET no. 74: 221-260 |
| engels2025 | OK | RET no. 74: 261-283 |
| zurcher2007 | OK | Brill, Leiden, 3rd ed |
| braarvig1993 | OK | Solum Forlag, Oslo |
| nattier2003 | OK | U of Hawai'i Press |
| zacchetti2021 | OK | projektverlag, HBS 14 |
| radich2015 | OK | BSR 32(2): 245-270 |
| **anthropic2025** | **MISMATCH** | Title says "3.5" models but paper uses 4.5 models |
| **zigmond2026b** | **STYLE** | Names target journal (JIABS) |
| **zigmond2026c** | **STYLE** | Names target journal (DSH) |
| ishikawa1990 | OK | Toyo Bunko, Studia Tibetica 18 |
| nehrdich2026 | OK | arXiv 2601.06400 |

---

## Cross-Reference Verification

All `\ref{}` targets resolve to defined `\label{}` targets:

| Reference | Target | Status |
|-----------|--------|--------|
| sec:sources | Line 270 | OK |
| sec:method | Line 528 | OK |
| sec:coverage | Line 675 | OK |
| sec:reliability | Line 950 | OK |
| sec:cases | Line 1050 | OK |
| sec:sanskrit | Line 1218 | OK |
| sec:applications | Line 1392 | OK |
| sec:limitations | Line 1461 | OK |
| sec:conclusion | Line 1585 | OK |
| sec:intro | Line 130 | OK |
| app:errors | Line 1745 | OK |
| tab:sources | Line 293 | OK |
| tab:tibetan | Line 687 | OK |
| tab:genre | Line 747 | OK |
| tab:sanskrit | Line 1276 | OK |
| tab:allerrors | Line 1755 | OK |

---

## Transliteration Compliance

Every `\zh{}` is followed by `\py{}`. Every `\tib{}` is followed by `\wy{}`. Sanskrit uses `\skt{}` for IAST throughout. No bare non-Latin script was found outside of verbatim blocks.

One note: Line 1566 has bare Chinese (長阿含經) inside a `\begin{verbatim}` block (XML example). This is technically unavoidable in a verbatim context but see item #11 above.

---

## American English

No British spellings found. The paper consistently uses "catalog" (not "catalogue"), "analyze" (not "analyse"), etc. The one instance of "analyses" (line 1440) is the standard plural, identical in both American and British English.

---

## Dashes

Only one em-dash found (line 317, inside a table cell as "---" placeholder). No em-dashes in running prose. The paper uses commas, semicolons, and parentheses appropriately throughout. Passes the minimal-dashes requirement.

---

## Complete Issue List (Sorted by Priority)

1. **Critical:** Grammar error "were never" (line 847) -- should be "was never"
2. **Critical:** Sanskrit title "Damamukonidhi" appears incorrect (line 486) -- should be "Damamukanidanasutra"
3. **Critical:** Internal date inconsistency for sgra sbyor (line 255 "early 9th cent." vs. line 1235 "c. 783 CE")
4. **Critical:** Off-by-one: "613" should be "612" Kangyur texts without parallels (lines 923, 1420)
5. **Critical:** Bib entry `anthropic2025` title says "3.5" models but paper text uses 4.5 models (lines 1659-1660 vs. bib line 343)
6. **Style:** Bib entries `zigmond2026b` and `zigmond2026c` name target journals (bib lines 351, 358)
7. **Moderate:** "~12,346" raw entries does not match table sum (~20,201); needs explanation (line 322)
8. **Moderate:** Genre table "With Parallel" sums to 1,031 but total concordance is 1,082; no footnote explains gap
9. **Minor:** Table 1 has 11 rows but text says "ten sources"; could confuse readers
10. **Minor:** "Four independent sources" for Heart Sutra (line 1109) not reconciled with nine-source example (lines 614-624)
11. **Minor:** "Three systematic errors" after listing five errors (line 968); distinction not explicit
12. **Minor:** "Back-translation from Sanskrit" phrasing may reverse Nattier's argument (line 1119)
13. **Minor:** No explanation of why 2,455 (not 2,920) Taisho texts are in scope
14. **Minor:** Bare Chinese in verbatim block without any transliteration (line 1566)
15. **Minor:** Translator name 翔公 for T08n0234 (line 1068) flagged for verification
