# Proofread: Mapping the Chinese and Tibetan Canons
**File:** `~/taisho-canon-papers/zigmond-tibetan-ret/zigmond-tibetan-concordance.tex`
**Bib:** `~/taisho-canon-papers/zigmond-tibetan-ret/references.bib`
**Date:** 2026-03-02

---

## Summary of Findings

The paper is in strong shape overall. The narrative flows coherently after the restructuring, transliteration conventions are followed with great consistency, American English is used throughout (with appropriate exceptions for cited titles), and there are no em-dashes in the text. The bibliography entries are overwhelmingly accurate against web sources. The issues found are:

- **1 internal statistics inconsistency** (Vinaya coverage: 51.7% in table vs 56.3% in body text)
- **1 number inconsistency** (T11n0310 referred to as having "63 Tohoku numbers" in one place but "54 Tohoku numbers from catalog sources" elsewhere, without clarification)
- **1 orphan bibliography entry** (ishikawa1990 never cited)
- **1 possible bibliography page-range issue** (Lalou 1953 pages)
- **Several minor grammar/style issues**
- **No transliteration violations found** (all Chinese, Tibetan, and Devanagari script is accompanied by transliteration)
- **No em-dashes or en-dashes used as punctuation** (only in number ranges and comments, as expected)
- **No presumptuous venue references** found
- **No ghost or fabricated references** found

---

## 1. Internal Statistics Inconsistency

### Vinaya coverage: 51.7% vs 56.3%

**Line 843 (Table 3):**
```
\skt{Vinaya} & 22--24 & 87 & 45 & 51.7\% \\
```

**Line 911 (body text):**
```
The \skt{Vinaya} section (vols.~22--24, 56.3\%) shows a similar pattern.
```

**Line 925 (body text):**
```
The 51.7\% coverage reflects cases where the same
```

**Issue:** The table gives 51.7% (45/87 = 51.7%), but the body text at line 911 introduces the section with 56.3%. Then line 925 reverts to 51.7%. The table value (51.7%) is mathematically correct (45/87). The 56.3% appears to be an error. **Fix:** Change line 911 to read `(vols.~22--24, 51.7\%)`.

### T11n0310 Tohoku number count: 54 vs 63

**Lines 707, 998, 1244:** Refer to "54 Tohoku numbers from catalog sources."

**Line 702 (verbatim example):** Shows `"...(63 Toh entries)..."` in the JSON.

**Line 1414:**
```
When the concordance records that T11n0310 corresponds to 63 Tohoku numbers, it does not
```

**Issue:** Line 1414 says "63 Tohoku numbers" without the "from catalog sources" qualification used elsewhere. Since the paper states that computational links are not included in the verified concordance counts, this creates confusion about whether the concordance contains 54 or 63 entries for this text. The verbatim JSON at line 702 shows 63, which presumably includes computational supplement entries. **Fix:** Either qualify line 1414 (e.g., "63 Tohoku numbers across catalog and computational sources") or use 54 consistently when referring to the verified concordance.

---

## 2. Transliteration Convention Check

**Result: PASS.** Every use of Chinese characters (`\zh{...}`) is followed by `\py{...}`, every use of Tibetan script (`\tib{...}`) is followed by `\wy{...}`, and first uses include English translations in parentheses. The convention is followed meticulously throughout the paper.

One minor note: The Chinese characters inside `\begin{verbatim}` blocks (line 1488: `長阿含經`) are bare, but this is correct because they appear in a code example. The transliterated form is provided immediately after the verbatim block (line 1494).

---

## 3. American English Check

**Result: PASS.** The paper consistently uses American spellings: "catalog" (not "catalogue"), "analyze," etc.

The only appearances of "Catalogue/Catalogues" are in the titles of cited works (Nanjio's *Catalogue*, Lancaster's *Descriptive Catalogue*, Ui's *Complete Catalogue*, Akanuma's *Comparative Catalogue*, Li's "Catalogues", CBETA's "Catalogues"), where British spellings in the original titles are correctly preserved.

Similarly, "Analysed" appears only in the title of Harrison 2008, preserving the original spelling.

---

## 4. Minimal Dashes Check

**Result: PASS.** No em-dashes (---) are used as punctuation anywhere in the paper text. The only `---` occurrence is in Table 1, line 350, used as a placeholder for a missing value in a table cell (which is conventional). En-dashes (--) appear only in number ranges (e.g., "815--838", "1--55", "Toh{1}--Toh{1108}"), which is standard LaTeX and not punctuation use.

---

## 5. No Presumptuous Venue References

**Result: PASS.** The paper does not name any target journal anywhere in the text or filename.

---

## 6. Citation Verification

### All bibliography entries verified against web sources:

| Entry | Status | Notes |
|---|---|---|
| takakusu1924 | **OK** | Takakusu & Watanabe, Taishō edition, 1924-1934, Tokyo. Confirmed. |
| nanjio1883 | **OK** | Nanjio, Clarendon Press, Oxford, 1883. Confirmed. |
| ui1934 | **OK** | Ui et al., Tōhoku Imperial University, Sendai, 1934. Confirmed. |
| lancaster1979 | **OK** | Lancaster (with Park), UC Press, Berkeley, 1979. Confirmed. |
| herrmannpfandt2008 | **OK** | Herrmann-Pfandt, Verlag der ÖAW, Vienna, 2008. Confirmed. |
| akanuma1929 | **OK** | Akanuma, Hajinkaku Shobō, Nagoya, 1929. Confirmed. Note says "Reprinted 1990"; some sources say 1991 (very minor). |
| nattier1992 | **OK** | JIABS 15(2), pp. 153-223, 1992. Confirmed. |
| buswell1989 | **OK** | Princeton University Press, 1989. Confirmed. |
| harrison2008 | **Minor flag** | JIABS 31(1-2), 2008. Pages listed as 205-249. Some web sources give 205-249, others 205-250. The difference may be a final blank page. Likely correct as-is, but verify against the physical article if possible. |
| silk2019 | **OK** | ARIRIAB at Soka University, vol. 22, pp. 227-246, 2019. Confirmed. |
| li2021 | **OK** | RET no. 60, pp. 174-219, 2021. Confirmed. |
| zigmond2026a | **OK** | Unpublished, "In preparation." N/A for verification. |
| suttacentral | **OK** | Bhikkhu Sujato, suttacentral.net. Confirmed. |
| cbeta_jinglu | **OK** | CBETA, jinglu.cbeta.org. Confirmed. |
| rkts | **OK** | Tibetan Manuscript Project Vienna, rkts.org. Confirmed. |
| 84000 | **OK** | 84000.co. Confirmed. |
| bdrc | **OK** | BDRC/BUDA, bdrc.io. Confirmed. |
| conze1978 | **OK** | Reiyukai, Tokyo, 1978, 2nd ed. Confirmed. |
| frauwallner1956 | **OK** | IsMEO, Rome, 1956. Confirmed. (Publisher name in bib: "Istituto Italiano per il Medio ed Estremo Oriente" -- correct.) |
| shimoda1997 | **OK** | Shunjūsha, Tokyo, 1997. Confirmed (limited English web presence, but author and publisher verified). |
| lalou1953 | **Minor flag** | Journal asiatique 241, 1953. Pages listed as 313-353. One source gives 313-354; another 313-353. The bib may be off by one page. Verify against the physical article. |
| kapstein2000 | **OK** | Oxford University Press, 2000. Confirmed. |
| vanschaik2015 | **OK** | Shambhala, Boston, 2015. Confirmed. |
| davidson2002 | **OK** | Columbia University Press, New York, 2002. Confirmed. |
| snellgrove1987 | **OK** | Serindia Publications and Shambhala, London and Boston, 1987. Confirmed. |
| cabezon1996 | **OK** | Snow Lion, Ithaca, NY, 1996. Confirmed. (Note: Some sources list first edition as 1996, hardcover as 1995. 1996 is the standard citation year.) |
| openpecha_kangyur | **OK** | Esukhia/Barom Theksum Choling, GitHub, 2022. Project ongoing since 2012-2018; 2022 is reasonable as a recent access/publication date. |
| schoch2013 | **OK** | Journal of Digital Humanities 2(3), 2013. Confirmed. |
| sahle2016 | **OK** | In Driscoll & Pierazzo (eds.), Open Book Publishers, pp. 19-40, 2016. Confirmed. |
| binding2016 | **OK** | Int. J. Digit. Libr. 17(1), pp. 5-21, 2016. Confirmed. |
| barnett2025 | **OK** | RET no. 74, pp. 5-43, 2025. Confirmed. |
| kyogoku2025 | **OK** | RET no. 74, pp. 187-220, 2025. Confirmed. |
| schwartz2025 | **OK** | RET no. 74, pp. 221-260, 2025. Confirmed. |
| engels2025 | **OK** | RET no. 74, pp. 261-283, 2025. Confirmed. |
| zurcher2007 | **OK** | Brill, Leiden, 3rd ed., 2007. Confirmed. |
| braarvig1993 | **OK** | Solum Forlag, Oslo, 1993. 2 vols. Confirmed. |
| nattier2003 | **OK** | University of Hawaiʻi Press, Honolulu, 2003. Confirmed. |
| zacchetti2021 | **OK** | Hamburg Buddhist Studies 14, projektverlag, Bochum and Freiburg, 2021. Confirmed (posthumous publication). |
| radich2015 | **OK** | Buddhist Studies Review 32(2), pp. 245-270, 2015. Confirmed. |
| anthropic2025 | **OK** | Anthropic, Claude. URL confirmed. |
| zigmond2026b | **OK** | Unpublished. N/A. |
| zigmond2026c | **OK** | Unpublished. N/A. |
| ishikawa1990 | **ORPHAN** | Never cited in the paper. Entry should be either cited or removed. Studia Tibetica 18, Toyo Bunko, Tokyo, 1990. The reference itself is verified as accurate. |
| nehrdich2026 | **OK** | arXiv:2601.06400, 2026. Confirmed. |

### Summary:
- **0 ghost/fabricated references**
- **1 orphan entry** (ishikawa1990)
- **2 minor page-range uncertainties** (harrison2008, lalou1953)

---

## 7. Grammar, Spelling, and Punctuation

### Line 127 (Abstract): Sentence length

```
A unified digital concordance mapping texts in the
Taishō ... identifies Tibetan parallels and cross-canon links for 754 of
the 2,455 Taishō texts ... covering 488 of 1,108 Kangyur ... texts ...
and 117 of 3,461 Tengyur ... texts ... .
```

**Issue:** The first sentence of the abstract runs from line 126 to approximately line 143 (the period after "resolution"). At roughly 120 words, it is extremely long and syntactically complex, with multiple nested clauses. Consider breaking it into two or three sentences for readability. For example, the final clause starting with "source agreement analysis across 721 multi-source texts" (line 139-143) could be separated as its own sentence.

### Line 143-144: Missing sentence break between topics

```
resolution.
This article presents both the computational methodology and its implications
```

**Issue:** There is no paragraph break or transitional word between the concordance results paragraph and the methodological summary paragraph. A `\medskip` or blank line before "This article" would improve readability, or at minimum add a sentence break. As written, the abstract runs two distinct themes (results, then article structure) back-to-back.

### Line 389-390: Repeated proper name

```
pages from the CBETA Digital Database of Buddhist Tripiṭaka Catalogues
(\zh{經錄} \py{jīnglù}).
```

**Issue:** The full name "CBETA Digital Database of Buddhist Tripiṭaka Catalogues" was already given (with citation) at line 194. By line 389, the shortened form "CBETA Jinglu" (already introduced) would suffice. This is a minor wordiness issue.

### Line 707: "The 54 Tohoku numbers from catalog sources arise because..."

**Suggestion:** "arise" is slightly awkward here. Consider "The 54 Tohoku numbers from catalog sources reflect the fact that..." or simply "The 54 catalog-source Tohoku numbers arise because..."

### Line 810: "developed largely in parallel"

```
The result is two commentarial traditions that developed largely in parallel
```

**Issue:** The word "parallel" here creates a potential double meaning (the paper is fundamentally about "parallels" in a different sense). Consider "independently" or "along separate lines."

### Line 1047: "scholarly informative"

```
These ``non-overlapping zones'' are themselves scholarly informative.
```

**Issue:** "scholarly informative" is an unusual collocation. Consider "themselves informative for scholars" or "themselves of scholarly interest."

### Line 1451: Repository URL placeholder

```
\url{https://github.com/dangerzig/taisho-canon} [to be released on
acceptance]
```

**Issue:** The GitHub username is "dangerzig" rather than something like "danzigmond" (the user's name). Verify this is the intended public repository URL.

### Line 1356: "scholarly interesting"

```
These zones are themselves scholarly interesting
```

**Issue:** Same unusual adjectival construction as line 1047. Consider "of scholarly interest" or "informative."

---

## 8. Coherence and Narrative Flow

**Result: GOOD.** The paper reads coherently after the restructuring. Computational methods (MITRA, Sanskrit title matching, LLM-based matching) are properly contained in the Future Directions section (Section 7.1). The main body focuses on catalog-based concordance results and their implications.

### Minor coherence issues:

**Line 215-216:**
```
The article also explores computational approaches for expanding coverage
further, including sentence-level alignment and Sanskrit title matching.
```

**Issue:** This sentence in the introduction promises that the article "explores" these approaches. But in the restructured paper, these are presented as "Future Directions" (Section 7.1). The word "explores" slightly overstates the treatment. Consider "outlines" or "briefly surveys" to match the actual depth of treatment.

**Line 148-149 (Abstract):**
```
Computational approaches for expanding coverage, including sentence-level
alignment and Sanskrit title matching, are explored as future directions.
```

Same point as above: "explored" is somewhat strong for what is a concise Future Directions subsection. "Outlined" or "surveyed" would be more precise.

**Line 752-758:**
```
The downloadable concordance data also include a computational
supplement containing links discovered through MITRA sentence-level
alignment and Sanskrit title matching
(\S\ref{sec:conclusion}). These computational candidates are provided
separately for researchers interested in exploring them but are not
included in the verified concordance counts or coverage statistics
presented in this article.
```

**Issue:** This paragraph appears in the Link Classification subsection (Section 4.4) and provides a forward reference to `\S\ref{sec:conclusion}`. This placement is slightly disruptive to the classification discussion. Consider moving it to the end of the section or to the Data Availability subsection.

---

## 9. LaTeX Issues

**Result: No compilation-breaking issues found.** All braces appear properly matched, all `\begin{}` / `\end{}` environments are paired, and cross-references point to defined labels.

### Minor suggestions:

**Line 350:** The `---` used as a dash in the table cell is fine but could also be represented as `\textemdash` for consistency, or simply left blank.

**Line 88:** `\newcommand{\zh}[1]{#1}` -- This command does nothing (passes text through unchanged). This is presumably intentional for styling flexibility, but it means `\zh{大正}` produces the same output as bare `大正`. If the intent is to eventually style Chinese text differently (e.g., a different font), the command is a useful hook. As-is, it works correctly.

---

## 10. Orphan Bibliography Entry

**ishikawa1990** is defined in `references.bib` (lines 380-388) but never cited anywhere in the paper. This entry should either be:
- Cited somewhere appropriate (e.g., when discussing the `sgra sbyor bam po gnyis pa` "Two-Volume Lexicon" at lines 285-288 or 507-508, where the lexicon is discussed but only a parenthetical translation is given), or
- Removed from `references.bib`

The natural citation point would be line 287:
```
\wy{sgra sbyor bam po gnyis pa} (``Two-Volume Lexicon,'' c.~783~CE)
```
which could become:
```
\wy{sgra sbyor bam po gnyis pa} (``Two-Volume Lexicon,'' c.~783~CE; \citealp{ishikawa1990})
```

---

## 11. Additional Observations

### The abstract's Kangyur definition

**Lines 134:**
```
covering 488 of 1,108 Kangyur (``translated word [of the Buddha]'')
```

**Lines 188:**
```
\Toh{1}--\Toh{1108} for the Kangyur
(\tib{བཀའ་འགྱུར} \wy{bka' 'gyur}, ``translated word [of the Buddha]''),
```

The abstract gives the Kangyur definition in English only (no Tibetan script/Wylie), while the introduction gives it with full Tibetan. This is standard practice for abstracts, where full transliteration would be excessive. No action needed.

### The `\Toh{}` macro

The `\Toh{}` macro (line 89) inserts a non-breaking space (`~`) between "Toh" and the number, which is correct and consistent throughout.

### Table numbering

The paper has five tables (sources, tibetan, genre, allerrors, scholarly) and one figure (pipeline). All are correctly numbered and cross-referenced.

### The Cabezon 1996 entry type

Line 227: `@collection{cabezon1996}` uses the `@collection` entry type, which is a biblatex type for edited volumes. The `editor` field is used correctly. This is fine for biblatex but would not work with BibTeX. Since the paper uses biblatex, this is correct.

---

## Summary of Required Fixes

| Priority | Issue | Location | Fix |
|---|---|---|---|
| **High** | Vinaya coverage 56.3% should be 51.7% | Line 911 | Change `56.3\%` to `51.7\%` |
| **Medium** | T11n0310: "63 Tohoku numbers" unqualified | Line 1414 | Add "across catalog and computational sources" or use "54" with qualification |
| **Medium** | Orphan bib entry ishikawa1990 | references.bib line 380 | Cite it (at line 287 or 507) or remove it |
| **Low** | "scholarly informative" awkward phrasing | Line 1047 | Change to "of scholarly interest" |
| **Low** | "scholarly interesting" awkward phrasing | Line 1356 | Change to "of scholarly interest" |
| **Low** | "explores" slightly overstates Future Directions | Lines 148, 215 | Consider "outlines" or "surveys" |
| **Low** | "developed largely in parallel" ambiguous | Line 810 | Consider "independently" |
| **Low** | Verify Harrison 2008 pages (205-249 vs 205-250) | references.bib line 86 | Verify against physical copy |
| **Low** | Verify Lalou 1953 pages (313-353 vs 313-354) | references.bib line 191 | Verify against physical copy |
| **Low** | GitHub username "dangerzig" | Line 1450 | Confirm this is the intended public URL |
| **Low** | Long first sentence in abstract | Lines 126-143 | Consider splitting |
