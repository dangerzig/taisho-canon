# Proofreading Review: Mapping the Chinese and Tibetan Canons

**Date:** 2026-02-26
**File:** `zigmond-tibetan-concordance.tex`
**Overall:** The paper reads well. The argument is clearly structured, the prose is strong, and the technical content is well-presented for a Tibetan studies audience. The transliteration convention is followed consistently throughout, and American English spellings are used. Below are issues organized by severity.

---

## Errors (Must Fix)

### 1. Inconsistent expansion percentage in Conclusion (line 1660)

The Conclusion says "representing a potential **13.9%** expansion" but the Sanskrit matching section (line 1336-1337) correctly says "**12.8%** expansion" (107/838 = 12.8%). The Conclusion figure is stale from before the Option A MITRA update.

**Fix:** Line 1660, change `13.9\%` to `12.8\%`.

### 2. Inconsistent Mahāratnakūṭa Toh count (lines 626-632)

The verbatim block on line 626-627 shows `"...(63 Toh entries)..."`, but the explanatory text on line 631 says "The **54** Tohoku numbers arise because..." The reader sees 63 in the code block and 54 in the text with no explanation. Lines 875 and 1117-1120 correctly explain the distinction (54 from catalogs, 63 total including MITRA), but lines 631-632 don't.

**Fix:** Line 631, change to something like: "The Tohoku numbers include 54 from catalog sources (arising because this Chinese collection bundles 49 separate sūtras, each cataloged independently in the Kangyur), with additional related texts identified through MITRA sentence-level alignment."

### 3. Appendix title uses British "Catalogue" (line 1699)

`\section{Catalogue Errors Identified}` uses British spelling, while the rest of the paper consistently uses American "catalog."

**Fix:** Change to `\section{Catalog Errors Identified}`.

### 4. Pinyin error: 目録學 (line 205)

`\py{m\`ul\`ux\'ue}` renders as *mùlùxúe*, but the correct pinyin for 學 is *xué* (tone mark on the *e*, not the *u*). Standard pinyin tone placement rule: when *u* and *e* appear together, the mark goes on the *e*.

**Fix:** Change `x\'ue` to `xu\'e`, giving `\py{m\`ul\`uxu\'e}` → *mùlùxué*.

### 5. Comma splice in source family description (line 1030-1031)

"Lancaster, Muller, CBETA Sanskrit, these should count as a single witness when they agree" is a comma splice.

**Fix:** Change the comma before "these" to a semicolon: "Lancaster, Muller, CBETA Sanskrit; these should count as a single witness when they agree".

---

## Clarity Issues (Should Fix)

### 6. MITRA numbers: 1,564 vs 1,401 moderate (lines 454 vs 580-585)

The MITRA source description says "825 strong, **1,564** moderate" (line 454), while the source agreement section says "**1,401** moderate-tier links" (line 584). The discrepancy arises because 1,564 counts files while 1,401 counts unique Taishō-to-Tohoku pairs (163 files map to duplicate pairs). This is never explained, and the reader will notice the inconsistent numbers.

**Suggestion:** Either use the same number in both places (the unique pair count, 1,401) or add a parenthetical in one location explaining the difference. Simplest fix: change line 454 to "825 strong, 1,401 moderate" and adjust the total: "2,226 document pairs remain" (or drop the breakdown by tier from this location and let the source agreement section carry it).

### 7. "1,031" vs "838" distinction (lines 324-332)

The source table's bottom row says "After removing duplicates --- **1,031**" but the abstract and §4 focus on **838** texts with *Tibetan* parallels. The 1,031 figure includes texts with Pali or Sanskrit parallels but no Tibetan. This is never stated explicitly. A reader comparing the table total (1,031) to the abstract (838) will be confused.

**Suggestion:** Add a note to the table's bottom row or the paragraph below it: e.g., "The 1,031 unique Taishō texts include all texts with any cross-canon parallel (Tibetan, Pāli, or Sanskrit); of these, 838 have identified Tibetan parallels specifically."

### 8. LLM results in Abstract (lines 115-116)

The abstract highlights "preliminary LLM-based catalog matching identifies an additional 61 Taishō texts with probable Tibetan parallels, 17 at high confidence." But this work appears in §11 (Future Work) and is explicitly described as "a preliminary experiment" (line 1575). Highlighting future/preliminary work as a key result in the abstract is unusual and may confuse readers or reviewers about the paper's actual contributions.

**Suggestion:** Either move the LLM results out of the abstract, or soften the language to make clear it's preliminary. Or promote the LLM section from "Future Work" to its own results section if you want it in the abstract.

### 9. 84000 TEI cross-references explanation (lines 410-412)

"The extraction yielded 457 Taishō cross-references from 193 Tohoku entries, making this one of the largest single sources of new cross-canon links and contributing 350 per-text attestations." The relationship between 457, 193, and 350 is unclear. Are there 457 individual references, 193 Tohoku source texts, and 350 unique Taishō texts linked? A brief clarification would help.

### 10. 834 vs 838 Tibetan parallel texts (line 1473)

"823 of the **834** Taishō texts with Tohoku numbers (98.7%)" — this implies 4 texts have Tibetan parallels without Tohoku numbers (838 - 834 = 4). This is never explained. Are these Otani-only texts? Texts with Tibetan titles but no catalog number?

**Suggestion:** Add a brief parenthetical: "834 Taishō texts with Tohoku numbers (four additional texts have Tibetan parallels recorded via Otani numbers or titles only)."

---

## Minor / Stylistic (Nice to Fix)

### 11. Unicode "sūtra" instead of `\skt{s\=utra}` (line 450)

"shared sūtra content" uses a Unicode ū rather than the `\skt{}` macro used everywhere else for Sanskrit terms. Minor inconsistency.

**Fix:** Change `sūtra` to `s\=utra` or `\skt{s\=utra}`.

### 12. rKTs source description sentence structure (lines 392-397)

"drawing on entries explicitly cataloged as Chinese-to-Tibetan translations, cases where scholars have determined the Tibetan text was translated from a Chinese source rather than from Sanskrit, the \tib{...} \wy{rgya nag nas bsgyur} (``translated from Chinese'') category."

This sentence stacks three appositives and reads awkwardly. The "cases where" phrase restates what "entries explicitly cataloged as Chinese-to-Tibetan translations" already says.

**Suggestion:** Simplify to something like: "drawing on entries in the \tib{...} \wy{rgya nag nas bsgyur} ('translated from Chinese') category, where scholars have determined the Tibetan text was translated from a Chinese source rather than from Sanskrit."

### 13. Pinyin for 律 missing tone (line 808)

`\py{S\`if\=enl\"{u}}` renders as *Sìfēnlü* but the correct pinyin for 律 is *lǜ* (4th tone). Combining an umlaut with a tone mark on ü is notoriously difficult in LaTeX. This is a known limitation and may not be worth fighting.

### 14. Missing apostrophe in Sìshí'èr (line 493)

`\py{S\`ish\'i\`erzh\=angj\={\i}ng}` renders without the standard pinyin apostrophe before *èr* (needed when a syllable starting with *a/o/e* follows another syllable). Should be *Sìshí'èr*.

### 15. GitHub username (line 1505)

`\url{https://github.com/dangerzig/taisho-canon}` — verify this is the correct/intended GitHub username.

---

## What Works Well

- **Transliteration compliance** is excellent throughout. Every non-Latin script instance has transliteration, and first uses have English translations.
- **No em-dashes** anywhere in the paper. En-dashes are used correctly for number ranges only.
- **American English** is consistent ("catalog," "analyze," etc.) except the one appendix title slip.
- **Source table with tier labels** reads clearly and the ordering by confidence is well-motivated.
- **MITRA conservative approach** justification (lines 440-456) is well-argued.
- **Case studies** (§6) are strong and bring the concordance to life with concrete examples.
- **Source reliability analysis** (§5) is one of the paper's most original contributions and is clearly presented.
- **Genre-stratified coverage** discussion (§4.2) provides excellent practical guidance for Tibetan studies scholars.
- The paper successfully balances methodological description with substantive analysis, serving both DH and Tibetan studies audiences.

---

## Summary

5 errors that need fixing (inconsistent number, British spelling, pinyin, comma splice), 5 clarity issues that would strengthen the paper, and 5 minor stylistic points. The paper is in good shape overall and the argument is compelling.
