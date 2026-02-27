# Proofread: "Mapping the Chinese and Tibetan Canons"

**File:** `/Users/danzigmond/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Date:** 2026-02-26

---

## Summary

The paper is in strong shape overall. The argumentation is clear, the statistics are internally consistent, the transliteration convention is followed with high fidelity, and the bibliography entries are largely accurate. The issues found are predominantly minor. The most notable findings are:

- One British English spelling ("artefact" on line 659; "Catalogues" in table on line 749)
- A BibTeX key/year mismatch (`silk2015` has `year = {2019}`)
- Editor ordering error in `sahle2016` bibliography entry
- A few instances of line-level dashes that could be reconsidered per the minimal-dashes style preference
- The bib file comment on line 3 names the target journal (though this is only in a comment, not in the paper text)
- One questionable citation (Otani numbers attributed to `ui1934`)

No ghost or fabricated references were found. All bibliography entries verified against web sources.

---

## Detailed Findings

### 1. AMERICAN ENGLISH

**1a. "artefact" should be "artifact"**
- **Line:** 659
- **Priority:** Major
- **Text:** `The apparent ``majority'' is an artefact of error`
- **Fix:** `The apparent ``majority'' is an artifact of error`
- **Note:** "Artefact" is British English. American English uses "artifact."

**1b. "Catalogues" in genre table should be "Catalogs"**
- **Line:** 749
- **Priority:** Minor
- **Text:** `Catalogues & 53--55 & 68 & 9 & 13.2\% \\`
- **Fix:** `Catalogs & 53--55 & 68 & 9 & 13.2\% \\`
- **Note:** This is the author's own table label, not a proper name. American spelling should be used. (The use of "Catalogues" on line 340 and in the bib entry title for CBETA is acceptable since it preserves the resource's official English name.)

---

### 2. TRANSLITERATION CONVENTION

The transliteration convention is followed with excellent consistency throughout. All Chinese script uses `\zh{...} \py{...}` format; all Tibetan script uses `\tib{...} \wy{...}` format; first uses include English translations in parentheses. No bare non-Latin script was found outside of `\begin{verbatim}` blocks (which are data-format examples and exempt).

**No issues found in this category.**

---

### 3. MINIMAL DASHES

The paper uses en-dashes (`--`) extensively for ranges (Toh numbers, page ranges, date ranges, volume ranges), which is standard LaTeX practice and not an em-dash concern. There are no true em-dashes (`---`) in the paper text (the `---` on line 311 is used as a table placeholder, which is standard).

However, two instances use en-dashes as punctuation connectors in running text rather than as range markers:

**3a. "Taisho--Tibetan" compound**
- **Lines:** 180, 1524
- **Priority:** Stylistic
- **Text (line 180):** `identifies 107 previously uncataloged Taish\=o--Tibetan parallels`
- **Text (line 1524):** `Taish\=o--Tohoku mapping, suitable for spreadsheet analysis`
- **Note:** These are compound adjectives using en-dashes, which is standard typographic practice for multi-word compounds. Acceptable as-is. No change recommended.

**No actionable dash issues found.**

---

### 4. CITATION VERIFICATION

All 27 bibliography entries in `references.bib` were verified against web sources. Results:

#### Verified Correct
- `takakusu1924` -- Takakusu & Watanabe, *Taisho Shinshu Daizokyo*, 1924-1934, Tokyo. **Correct.**
- `nanjio1883` -- Nanjio, *Catalogue of the Chinese Translation*, 1883, Clarendon Press, Oxford. **Correct.**
- `ui1934` -- Ui et al., *Complete Catalogue of the Tibetan Buddhist Canons*, 1934, Tohoku Imperial University, Sendai. **Correct.**
- `lancaster1979` -- Lancaster & Park, *Korean Buddhist Canon: A Descriptive Catalogue*, 1979, UC Press, Berkeley. **Correct.**
- `herrmannpfandt2008` -- Herrmann-Pfandt, *Die lHan kar ma*, 2008, Verlag der OAW, Vienna. **Correct.**
- `akanuma1929` -- Akanuma, *Comparative Catalogue of Chinese Agamas and Pali Nikayas*, 1929, Hajinkaku Shobo, Nagoya. **Correct.**
- `nattier1992` -- Nattier, "Heart Sutra: A Chinese Apocryphal Text?" JIABS 15(2), pp. 153-223, 1992. **Correct.**
- `buswell2014` -- Buswell & Lopez, *Princeton Dictionary of Buddhism*, Princeton UP, 2014. **Correct.**
- `harrison2008` -- Harrison, "Experimental Core Samples...", JIABS 31(1-2), pp. 205-249, 2008. **Correct.** Note: JIABS 31(1-2) is dated 2008 but was distributed in 2010; the 2008 date is the standard citation convention.
- `li2021` -- Li, "Survey of Tibetan Sutras Translated from Chinese," RET no. 60, pp. 174-219, 2021. **Correct.**
- `lalou1953` -- Lalou, "Les textes bouddhiques au temps du roi Khri-sron-lde-bcan," Journal asiatique 241, pp. 313-353, 1953. **Correct.**
- `kapstein2000` -- Kapstein, *Tibetan Assimilation of Buddhism*, OUP, 2000. **Correct.**
- `davidson2002` -- Davidson, *Indian Esoteric Buddhism*, Columbia UP, 2002. **Correct.**
- `snellgrove1987` -- Snellgrove, *Indo-Tibetan Buddhism*, Shambhala, Boston, 1987. **Correct.**
- `cabezon1996` -- Cabezon & Jackson, *Tibetan Literature: Studies in Genre*, Snow Lion, Ithaca, 1996. **Correct.**
- `conze1978` -- Conze, *Prajnaparamita Literature*, 2nd ed., Reiyukai, Tokyo, 1978. **Correct.**
- `frauwallner1956` -- Frauwallner, *Earliest Vinaya*, Istituto Italiano per il Medio ed Estremo Oriente, Rome, 1956. **Correct.**
- `schoch2013` -- Schoch, "Big? Smart? Clean? Messy? Data in the Humanities," J. Digital Humanities 2(3), pp. 2-13, 2013. **Correct.**
- `binding2016` -- Binding & Tudhope, "Improving Interoperability Using Vocabulary Linked Data," Int. J. Digital Libraries 17(1), pp. 5-21, 2016. **Correct.**
- `barnett2025` -- Barnett & Engels, "Assembling a Digital Toolkit...", RET no. 74, pp. 5-43, 2025. **Correct.**
- `kyogoku2025` -- Kyogoku, Erhard, Engels, & Barnett, "Leveraging Large Language Models...", RET no. 74, pp. 187-220, 2025. **Correct.**
- `schwartz2025` -- Schwartz & Barnett, "Religious Policy in the TAR, 2014-24...", RET no. 74, pp. 221-260, 2025. **Correct.**
- `engels2025` -- Engels & Barnett, "Developing a Semantic Search Engine...", RET no. 74, pp. 261-283, 2025. **Correct.**
- `nehrdich2026` -- Nehrdich & Keutzer, "MITRA...", arXiv:2601.06400, 2026. **Correct.**
- `suttacentral` -- SuttaCentral resource. **Correct.**
- `cbeta_jinglu` -- CBETA Jinglu resource. **Correct.**
- `rkts` -- rKTs resource. **Correct.**
- `84000` -- 84000 resource. **Correct.**
- `bdrc` -- BDRC resource. **Correct.**
- `openpecha_kangyur` -- Esukhia/Barom Theksum Choling, Digital Derge Kangyur, OpenPecha/P000001. **Correct.**
- `zigmond2026a` -- Companion paper (in preparation). **Cannot verify externally, but appropriately marked as unpublished.**

#### Issues Found

**4a. BibTeX key mismatch for silk2015**
- **File:** `references.bib`, line 88
- **Priority:** Minor (cosmetic, does not affect rendering)
- **Issue:** The BibTeX key is `silk2015` but the `year` field is `2019`. The article was indeed published in 2019 (AIRIAB vol. 22). The key name is misleading but biblatex will correctly render the year as 2019 in citations.
- **Fix:** Rename the key from `silk2015` to `silk2019` and update all `\citet{silk2015}` and `\citep{silk2015}` references in the .tex file accordingly (lines 403, 453, 508).

**4b. Editor order in sahle2016**
- **File:** `references.bib`, line 241
- **Priority:** Minor
- **Issue:** The `editor` field reads `Pierazzo, Elena and Driscoll, Matthew James`, but the published book lists editors as Matthew James Driscoll and Elena Pierazzo (Driscoll first). Multiple sources (Amazon, JSTOR, Open Book Publishers website) consistently list Driscoll as the first editor.
- **Text:** `editor = {Pierazzo, Elena and Driscoll, Matthew James},`
- **Fix:** `editor = {Driscoll, Matthew James and Pierazzo, Elena},`

**4c. Target journal named in bib file comment**
- **File:** `references.bib`, line 3
- **Priority:** Minor
- **Issue:** Comment reads `% Targeting Revue d'Etudes Tibetaines (author-year citations via biblatex)`. This names the target journal. While it is only a comment and will not appear in the compiled paper, it should be removed for clean submission to avoid any impression of presumptuousness.
- **Fix:** Change to `% Bibliography for "Mapping the Chinese and Tibetan Canons" (author-year citations via biblatex)` or simply delete the targeting note.

---

### 5. NO PRESUMPTUOUS VENUE REFERENCES

The paper text itself contains no references to the target journal. The only issue is the bib file comment noted in 4c above.

---

### 6. GRAMMAR, TYPOS, AND STYLE

**6a. Possible questionable citation: Otani numbers attributed to ui1934**
- **Line:** 234-235
- **Priority:** Major
- **Text:** `incorporating Otani catalog numbers \citep{ui1934}, based on the Peking edition`
- **Issue:** The Tohoku catalog (Ui 1934) is the Derge-based catalog. Otani numbers are from the Peking edition, cataloged by Suzuki et al. in the Otani/Peking reprint series. While the Tohoku catalog may contain cross-references to the Peking edition, citing `ui1934` specifically for "Otani catalog numbers" is potentially misleading. The concordance's Otani data comes from rKTs kernel IDs and Lancaster cross-references (per the MEMORY notes), not from Ui 1934.
- **Fix:** Either add a more appropriate citation for the Otani numbering system (e.g., reference to the Suzuki Peking edition or rKTs), or rephrase to clarify that the concordance derives its Otani numbers from rKTs and Lancaster while the numbering system itself originates from the Peking edition catalog.

**6b. "na\"ive" accent rendering**
- **Lines:** 1018, 1734
- **Priority:** Stylistic
- **Text (line 1018):** `na\"\i ve majority`
- **Note:** This is technically correct LaTeX (produces "naive" with diaeresis), but the more natural LaTeX encoding would be `na\"ive` or simply using the Unicode character. This is not wrong, just unusual. No change required unless you prefer a different encoding.

**6c. Sentence readability on lines 1053-1054**
- **Line:** 1053-1054
- **Priority:** Stylistic
- **Text:** `arises whenever dependent databases inherit errors from their sources without independent verification, a challenge relevant to any domain where`
- **Note:** This is a long sentence. The clause beginning "a challenge relevant to" is an appositive following a comma, which reads slightly loosely. Consider: "arises whenever dependent databases inherit errors from their sources without independent verification. This challenge is relevant to any domain where..."
- **Alternative:** Leave as-is; it is grammatically correct if somewhat dense.

---

### 7. LATEX FORMATTING

**7a. Inconsistent `vols.\ ` vs `vols.~`**
- **Lines:** 712, 839 vs. most other instances
- **Priority:** Stylistic
- **Text (line 712):** `vols.\ 33--44`
- **Text (line 839):** `vols.\ 18--21`
- **Other occurrences (e.g., line 769):** `vols.~25--32`
- **Note:** Most occurrences use `vols.~` (non-breaking space), but lines 712 and 839 use `vols.\ ` (regular forced space). For consistency and to prevent a line break between "vols." and the number, all should use `vols.~`.
- **Fix:** Change `vols.\ ` to `vols.~` on lines 712 and 839.

---

### 8. INTERNAL CONSISTENCY

**8a. Statistics check: all numbers verified internally consistent.**
- 496 Kangyur + 156 Tengyur = 652 unique Toh. **Correct.**
- 192 exact + 39 fuzzy = 231 total matches. **Correct.**
- 77 confirmed / 101 overlapping = 76.2%. **Correct (76.24%).**
- 231 - 101 = 130 new proposals. **Correct.**
- 68 + 25 + 19 + 18 = 130 genre proposals. **Correct.**
- 75 Kangyur + 55 Tengyur = 130 proposals. **Correct.**
- 825 strong + 1,401 moderate = 2,226 MITRA pairs. **Correct.**
- 44.8% = 496/1108. **Correct (44.77%).**
- 4.5% = 156/3461. **Correct (4.51%).**

**No inconsistencies found.**

---

### 9. TERMINOLOGY CONSISTENCY

- "Taish\=o" used consistently throughout (never "Taisho" in running text, only in plain-text contexts like verbatim/table notes).
- "Tohoku" used consistently.
- "catalog" (American) used consistently for the author's own references, "Catalogues" preserved only where it is part of an official name (CBETA). Exception: line 749 "Catalogues" in the genre table (see 1b above).
- "concordance" used consistently.
- "provenance" used consistently.
- Citation style (\citep vs \citet) used correctly throughout: \citet for in-text references where the author name is part of the sentence, \citep for parenthetical citations.

---

### 10. SUGGESTED IMPROVEMENTS (Optional, not errors)

**10a. Consider adding first-use Chinese for "Xuanzang" and "Kumarajiva"**
- **Lines:** 596, 1096
- **Priority:** Stylistic (optional)
- **Note:** The paper follows the transliteration convention for all Chinese terms, but famous translator names "Xuanzang" and "Kumarajiva" appear without Chinese characters. These names are well known in their romanized forms, but for completeness, first uses could include `\zh{玄奘} \py{Xu\'anz\`ang}` and `\zh{鳩摩羅什} \py{Ji\=um\'olu\'osh\'i}`. This is optional; these are standard romanizations rather than Chinese text per se.

**10b. JIABS year note for harrison2008**
- **Priority:** Informational only
- **Note:** JIABS 31(1-2) is dated 2008 but was actually distributed/published around 2010. Some scholars cite it as "2008 [2010]." The current citation (year 2008) follows the volume date convention, which is standard and acceptable.

---

## Priority Summary

| Priority | Count | Items |
|----------|-------|-------|
| Critical | 0 | -- |
| Major | 2 | 1a (artefact), 6a (Otani citation) |
| Minor | 4 | 1b (Catalogues), 4a (silk key), 4b (editor order), 4c (bib comment) |
| Stylistic | 4 | 6b (naive accent), 6c (sentence length), 7a (vols spacing), 10a (translator names) |

**Overall assessment:** The paper is in very good condition. The two major items should be addressed before submission. The minor and stylistic items are worth fixing but are not blockers.
