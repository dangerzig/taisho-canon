# Critical Review: "Mapping the Chinese and Tibetan Canons"

Full proofread and critical review of `zigmond-tibetan-concordance.tex`.

---

## CRITICAL: `known_errors.json` Has Wrong Taisho IDs

**This is the most urgent issue.** The `data/known_errors.json` file I
created uses the Taisho IDs from the implementation plan, but these
conflict with the paper's Appendix A (Table 8) and with the actual source
data. I verified against the raw source files (Lancaster, CBETA Sanskrit,
rKTs). **The paper is correct; the plan was wrong for 7 of 8 entries.**

| # | Paper (CORRECT) | known_errors.json (WRONG) | Source data confirms |
|---|----------------|--------------------------|---------------------|
| 1 | T15n0586 | T15n0586 | Lancaster T586 has Toh 16. Match. |
| 2 | **T15n0650** | T15n0587 | Lancaster T650 has Toh 18, not T587. |
| 3 | **T25n1518** | T32n1645 | Lancaster T1518 has Toh 3908, not T1645. |
| 4 | **T09n0278** | T21n1340 | Lancaster T278 has Toh 0, not T1340. |
| 5 | **T13n0397** | T21n1341 | Lancaster T397 has Toh 0, not T1341. |
| 6 | **T31n1612** | T30n1579 | CBETA Skt entry 618: T1612 has Toh 4066. |
| 7 | **T31n1613** | T31n1585 | CBETA Skt entry 619: T1613 has Toh 4059. |
| 8 | **T19n0945** | T15n0639 | rKTs entry 237: T945 has Toh 237. |

This explains why 7 of 8 errors showed "NO ATTESTATIONS" when the
concordance builder ran: the wrong Taisho IDs were being looked up.

**Action required:** Fix `data/known_errors.json` to use the paper's IDs,
then re-run the concordance builder. After the fix, all 8 errors should
show attestations being flagged and removed.

---

## Proofreading Issues

### Lines ~110-111: Awkward line break in abstract

> "na\"ive majority-based conflict resolution"

Not an error per se, but `naïve` is more natural. Consider using the
`\namark` or just typing it as `na\"{\i}ve` consistently. Currently it
appears as `na\"\i ve` (with a space before "ve") which could produce odd
rendering depending on the TeX engine. Check the PDF output.

### Line 157: Tibetan script for bka' 'gyur

> `\tib{བཀའ་འགྱུར} \wy{bka' 'gyur}`

The Tibetan spelling has `འགྱུར` with a ya-btags, which is the correct
standard spelling. Fine.

### Line 207: "2,920 texts across 100 volumes"

The Taisho has 100 volumes total but only 55 contain canonical texts
(vols. 1-55); vols. 56-100 are supplementary catalogs, indexes, etc. The
2,455-text corpus used in this paper covers vols. 1-55. The paper should
probably say "55 volumes" (for the canonical portion) or clarify that the
100-volume figure includes supplements. As written, a reader might wonder
why the concordance only covers 2,455 of 2,920 texts.

### Line 265: sgra sbyor bam po gnyis pa

> `\tib{སྒྲ་སྦྱོར་བམ་པོ་གཉིས་པ}`

Fine, standard rendering.

### Lines 488-489: Source merging order

> "SuttaCentral first (as baseline), then Lancaster, Muller, CBETA Jinglu
> Tibetan, CBETA Jinglu Sanskrit..."

But looking at the actual code (`build_expanded_concordance.py`), the
order is: (1) existing/SuttaCentral, (2) Lancaster original, (3) acmuller
Tohoku, (4) CBETA Sanskrit, (5) Lancaster full, (6) CBETA Tibetan, (7)
rKTs, (8/8b) 84000, (9) Sanskrit title matches, (10) Scholarly. The paper
lists a different order (Muller before CBETA Tibetan, CBETA Tibetan before
CBETA Sanskrit). Since the paper correctly notes "The fixed ordering does
not affect the final result" (line 498), this is not a substantive error,
but the description doesn't match the code. Minor issue; could be left
as-is since the order genuinely doesn't matter.

### Line 557: "Eight independent sources"

The verbatim example for T08n0251 shows 8 sources, but the paper says
"nine" sources throughout. This specific entry happens to be attested by
8 of the 9. Not an error, but the juxtaposition of "eight independent
sources agree" with "nine sources" elsewhere could confuse a reader.
Consider "Eight of the nine sources agree" or similar.

### Lines 574-595: Conflict example for T15n0586

The verbatim block shows:

```
"T15n0586": ["Toh 16", "Toh 160"]
```

But with the error-flagging code now active, the output JSON has:

```
"T15n0586": ["Otani 739", "Otani 827", "Toh 160"]
```

"Toh 16" is now removed from `tibetan_parallels` (kept only in provenance
with `flagged_error`). The example in the paper should still show the
pre-flagging state to illustrate the error detection, but a note could
mention that the released data flags this error. Alternatively, show the
provenance (which still contains Toh 16 with the flag). Minor issue; the
example is pedagogically clear as-is.

### Line 622-624: Footnote about 607 + 3 = 610

> "The rows sum to 607; the remaining 3 Tohoku numbers fall outside the
> standard Kangyur/Tengyur ranges due to data entry anomalies."

Verify this arithmetic is still current. 491 + 116 = 607, so if total
unique Toh is still 610, the footnote is correct.

### Lines 889-891: Lancaster errors count

> "contained three confirmed errors in Tohoku numbers"

But Appendix A lists 5 Lancaster errors (#1-5). Three are the ones
described in detail (trailing zeros + transposition); the two spurious
zeros are also Lancaster errors. The text should probably say "five
confirmed errors" or "three systematic errors in Tohoku numbers plus two
spurious zero entries."

### Lines 925-927: "six most clear-cut errors"

> "Table~\ref{tab:conflicts} details the six most clear-cut errors"

Table 5 lists 6 errors, Appendix A lists 8. The difference is the two
"Toh 0" spurious entries (errors #4 and #5 from Appendix A). This is
fine: those are excluded from Table 5 because they're trivial (obvious
non-numbers). The phrasing is clear.

### Lines 939-944: Table 5 (tab:conflicts) Taisho IDs

The table uses T15n0650, T25n1518, T19n0945, T31n1612, T31n1613, which
I've now confirmed are **correct** per the source data. No change needed
in the paper.

### Lines 1029-1030: Heart Sutra pinyin

> `\py{M\'oh\=e b\=oru\`o b\=olu\'om\`i d\`am\'ingzh\`ou j\={\i}ng}`

This is a romanization of 摩訶般若波羅蜜大明呪經. The pinyin should be
`Móhē bōruò bōluómì dàmíngzhòu jīng`. The current encoding looks correct
but is dense. Verify it renders properly in the PDF.

### Line 1326: Self-citation

> `\citep{zigmond2026a}`

Make sure this reference exists in `references.bib` and renders properly.

### Line 1408: "762 Taishō texts with Tohoku numbers"

> "752 of the 762 Taishō texts with Tohoku numbers (98.7%)"

Check: the concordance output says 768 texts with Tibetan parallels.
Are 762 the ones with *Tohoku* specifically (excluding texts that have
only Otani or other Tibetan refs)? Verify this number is current.

---

## Structural and Substantive Issues

### 1. The new Future Work section (lines 1492-1570)

**LLM subsection (lines 1495-1537)**: Well written. Concrete numbers are
now included. Two concerns:

- **"Claude Haiku 4.5" and "Claude Sonnet 4.5"**: These are Anthropic
  model names. Since this is an academic paper, consider whether naming
  specific commercial products is appropriate for the venue. The current
  phrasing is fine for a DH journal but might raise eyebrows elsewhere.
  Not necessarily a change needed, just flagging.

- **Line 1519**: "The high-confidence new matches are concentrated in
  \skt{dhāraṇī} and ritual literature (Taishō vols. 18--21)." This
  claim should be verified against the stats file. Looking at the 17
  high-confidence new matches: T21n1372, T21n1400, T21n1233, T18n0909,
  T21n1287, T21n1249 (x2), T25n1513, T20n1119 (x2), T20n1055 (x4),
  T18n0908, T20n1067. Indeed vols. 18-21 plus vol. 20 (also
  dhāraṇī/tantra) and vol. 25 (one outlier). The claim is accurate
  enough, though vol. 25 is śāstra, not dhāraṇī.

**Word Embedding subsection (lines 1539-1559)**: Unchanged from before,
reads well.

**Other Directions subsection (lines 1561-1570)**: This subsection feels
thin. It's essentially just the "living resource" paragraph. Consider
whether it needs to be a subsection at all, or whether it could be folded
into the section-level introduction of §9 before the first subsection.

### 2. Conclusion (lines 1572-1627)

The restructured conclusion reads well. The updated enumeration item 4
(lines 1594-1599) cleanly references §9 for the LLM results. The "dozens
of additional parallels" language from the old version has been replaced
with the concrete "61 Taishō texts... 17 at high confidence," which is a
significant improvement.

### 3. Data Availability section is now very short

§8 "Data Availability" is now ~55 lines of mostly verbatim code examples.
This is fine for a DH journal that expects data descriptions. No issue.

### 4. Abstract may need updating

The abstract (lines 97-128) says:

> "preliminary experiments with computational semantic matching... suggest
> that dozens more remain to be discovered"

Now that §9 reports concrete LLM numbers (61 new texts, 17
high-confidence), the abstract could be strengthened. Consider:

> "...and preliminary LLM-based catalog matching identifies an additional
> 61 Taishō texts with probable Tibetan parallels, 17 at high
> confidence."

This would make the abstract reflect the paper's actual results rather
than the vague "dozens more."

### 5. Consistency of "nine sources" count

The paper consistently says "nine" sources (e.g., lines 102, 284, 524,
1581), but Table 1 lists 9 rows (with 84000 split into "TEI titles" and
"TEI cross-refs"). The scholarly citations are listed as a separate
source. So the count depends on how you group things. Currently it's
consistent as presented.

---

## Style / Convention Issues

### Dashes

I found one em-dash equivalent in line 1453:

> `Taish\=o--Tohoku mapping`

This is an en-dash (--) used for a range/relationship, which is correct
LaTeX usage for joining related items. Not the same as an em-dash. No
issue.

### American English

Checked: "catalog" (not "catalogue") throughout. "analyze" appears where
needed. Looks correct.

### Transliteration

Spot-checked throughout: every Chinese character has pinyin, every Tibetan
has Wylie, every Sanskrit has IAST. First uses include English
translations. Looks complete and consistent.

---

## Summary of Required Actions

1. **CRITICAL**: Fix `data/known_errors.json` to use the paper's (correct)
   Taisho IDs. Then re-run `build_expanded_concordance.py` and exports.

2. **Recommended**: Update the abstract to include the concrete LLM
   matching numbers (61 texts, 17 high-confidence) instead of "dozens."

3. **Recommended**: Line 889, change "three confirmed errors" to "five
   confirmed errors" or rephrase to distinguish the three systematic
   errors from the two spurious zeros.

4. **Minor**: Line 557, "Eight independent sources" could say "Eight of
   the nine sources" for clarity.

5. **Minor**: Consider whether the "Other Directions" subsection of
   Future Work needs to be a full subsection or could be introductory
   text for §9.

6. **Verify**: Line 1408, "762 Taishō texts" number is current.

7. **Verify**: Line 207, "2,920 texts across 100 volumes" vs. the
   concordance's 2,455 texts across 55 volumes. Clarify if needed.
