# Paper Review: Link Classification Additions

**Date**: 2026-03-01
**Paper**: `zigmond-tibetan-concordance.tex`
**Focus**: Three new sections added for link classification feature

## Sections Reviewed

1. **New subsection** `\subsection{Link Classification}` (lines 709-789)
2. **Updated Chan footnote** (lines 988-996)
3. **New limitations paragraph** (lines 1693-1705)

---

## 1. Accuracy

### Table 7 statistics verified against JSON output

| Type | Paper (Table 7) | JSON (`cross_reference_expanded.json`) | Match? |
|------|-----------------|----------------------------------------|--------|
| `parallel` | 2,700 | 2,700 | YES |
| `parallel:computational` | 239 | 239 | YES |
| `indirect:quotation` | 1,150 | 1,150 | YES |
| `chinese_to_tibetan` | 46 | 46 | YES |
| `indirect:inherited` | 46 | 46 | YES |
| `uncertain` | 466 | 466 | YES |
| **Total** | **4,647** | **4,647** | **YES** |
| Schema version | 3 | 3 | YES |

### FINDING: Inconsistent counts between Table 7 and paragraph (lines 773-782)

**Severity: Medium**

The paragraph at lines 773-782 reads:

> "Of the 367 new active links contributed by MITRA's strong tier (plus
> 12 from Sanskrit title matching), 239 links from 92 non-encyclopedic
> texts are classified as likely genuine parallel discoveries
> (parallel:computational). [...] The remaining computational-only links
> fall into either the encyclopedic quotation pattern (252 links from 72
> texts) or the uncertain category (466 links with confidence below 0.9)."

Two problems:

1. **The 252 quotation figure conflicts with Table 7's 1,150.** The table
   (correctly) counts all classified links including Otani-inherited entries.
   The paragraph's 252 appears to be a Toh-only count (from the original
   plan's pre-implementation estimate). A reader who sees 1,150 in the
   table and then reads "252 links" two paragraphs later will be confused.
   The paragraph should either cite the table's 1,150 figure or explicitly
   note that 252 is the count before Otani inheritance ("252 Toh-level
   links from 72 texts, expanding to 1,150 including Otani-inherited
   entries").

2. **Misleading arithmetic framing.** The paragraph structure ("Of the
   367+12... 239 are X. The remaining... fall into Y (252) or Z (466).")
   strongly implies 239 + 252 + 466 = 379, i.e., the 252 and 466 are the
   remainder of the 379 new computational links. But 239 + 252 + 466 = 957,
   far exceeding 379. The "remaining computational-only links" silently
   switches scope from "new active links" to "all computational-only links
   in the concordance." This needs rewording to avoid the false implication.

**Suggested fix:** Restructure the paragraph to clearly separate the new-link
narrative from the full-classification totals. For example:

> "The classification system (Table 7) identifies 2,700 catalog-backed
> parallels, 239 likely genuine computational discoveries, 1,150 quotation
> artifacts from encyclopedic compilations, 46 Chinese-to-Tibetan translations,
> 46 inherited parallels, and 466 uncertain links, for a total of 4,647
> classified entries (including Otani-inherited classifications). The 239
> parallel:computational links, drawn from 92 non-encyclopedic texts, represent
> the primary contribution of computational methods: texts where sentence-level
> alignment or title matching has identified a Tibetan parallel that no
> traditional catalog records."

### Chan footnote: "38 computational-only Toh links" (line 994)

This figure (38 Toh links for T48n2016) was verified in the original plan
analysis. **Correct.**

### Limitations paragraph: "239 parallel:computational links" and "466 uncertain" (lines 1697-1702)

These figures match Table 7. **Correct** but redundant (see below).

---

## 2. Consistency with Existing Text

### Classification section integrates well with existing methodology narrative

The new section (lines 709-789) sits between "Illustrative Concordance
Entries" and "Tibetan Canon Coverage." The transition is natural: after
showing how provenance data resolves conflicts (the T15n0586 example at
lines 685-707), the text explains how provenance patterns also reveal
different relationship types. **Good placement.**

### Source category terminology is consistent

The paper's description of "catalog sources" and "computational sources"
(lines 725-733) matches the terminology used elsewhere:
- Line 448: "Unlike the preceding catalog sources, which record bibliographic
  correspondences, MITRA identifies parallels computationally"
- Line 627: "nine catalog sources" and "MITRA, is a computational source"
- Table 1 (line 303): "Authoritative catalogs" vs. "Computational"

**Consistent throughout.**

### "Ten sources" count remains correct

The paper consistently refers to "ten data sources" (lines 103, 284, 629,
803). The classification section doesn't change this count, since
classification is a post-processing step, not a new data source. **No
inconsistency.**

### T48n2016 Zongjinglu appears in two places

The Zongjinglu is discussed in both the classification section (line 768,
as a calibration example) and the Chan footnote (line 988, as a specific
case study). These serve different purposes: the first explains the
heuristic threshold, the second explains why Chan texts have near-zero
coverage. The slight repetition is acceptable because readers may
encounter either section independently. **Acceptable overlap.**

---

## 3. Flow

### Classification section flow: GOOD

- **Entry**: Opens with a clear problem statement ("The concordance conflates
  several distinct relationship types"). This follows naturally from the
  preceding concrete examples.
- **Structure**: Problem → source categories → classification types (table)
  → key heuristic → impact → extensibility. Logical progression.
- **Exit**: Ends with extensibility, then transitions cleanly to Coverage
  section. The `% =====` divider and new `\section` provide visual
  separation.

### Integration with paper's overall arc: GOOD

The paper's arc is: Sources → Methodology → Coverage → Reliability →
Cases → Discovery → Applications → Limitations → Conclusion. The
classification section sits within Methodology and is referenced later
in the Chan footnote (Coverage) and Limitations. These forward references
work well.

### One flow note

The transition from the T15n0586 error propagation example (lines
685-707) to Link Classification (line 709) is slightly abrupt. The error
example ends with a parenthetical reference to Section 5, then immediately
the next subsection begins. A brief transitional sentence could help, but
this is minor. The LaTeX subsection header provides sufficient visual
separation.

---

## 4. Repetitiveness

### FINDING: Limitations paragraph (1693-1705) is significantly redundant

**Severity: Medium**

The limitations paragraph repeats three points already made in the
classification section:

| Point | Classification section | Limitations section |
|-------|----------------------|-------------------|
| 239 parallel:computational links | Line 775 | Line 1697 |
| 466 uncertain links | Line 782 | Line 1701 |
| Framework extensibility | Lines 784-788 | Lines 1703-1705 |

The only genuinely new content in the limitations paragraph is:
- The classification system is "itself heuristic" (line 1693-1694)
- The threshold is "conservative; some texts with three or four such links
  may also be quotation sources" (lines 1695-1696)
- parallel:computational links are "strong but unverified" (lines 1697-1700)

**Suggested fix:** Trim the limitations paragraph to its unique content:

> "The link classification system (\S\ref{sec:classification}) is itself
> heuristic. The encyclopedic threshold of five computational-only Toh
> links is conservative: some texts with three or four such links may
> also be quotation sources rather than genuine parallels. Conversely,
> the \texttt{parallel:computational} links, while supported by high
> confidence scores and non-encyclopedic provenance, remain unverified
> by traditional scholarship; only philological examination can confirm
> these as genuine parallels."

This removes the redundant count citations and the extensibility restatement,
cutting the paragraph from 13 lines to 7 while preserving all unique content.

### Extensibility mentioned twice in classification section itself

Lines 784-788 ("The framework is designed to be extensible...") make the
extensibility point. This is fine as a standalone mention. But combined
with the limitations paragraph's restatement (1703-1705), the reader
encounters the same point three times if counting the plan's original
mention. Trimming the limitations paragraph (as above) solves this.

---

## 5. Transliteration Compliance

Every Chinese, Sanskrit, and Tibetan term in the three new sections has
proper transliteration:

- `\zh{宗鏡錄} \py{Z\=ongj\`ingl\`u}` (line 768) YES
- `\zh{法苑珠林} \py{F\v{a}yu\'an Zh\=ul\'in}` (line 769) YES
- All `\skt{...}` terms are in IAST italics YES
- Chan footnote: all CJK terms have `\py{...}` YES
- Limitations paragraph: no CJK/Sanskrit/Tibetan script (N/A)

**PASS: Full compliance.**

---

## 6. American English

Checked all three sections for British spellings:

- No instances of "catalogue" (uses "catalog" consistently)
- No instances of "favour," "colour," etc.
- No instances of "analyse" or "organise"
- "heuristic" used correctly (same in both dialects)

**PASS: Consistent American English.**

---

## 7. Dashes

Checked all three sections for em-dashes:

- No em-dashes (---) found in any of the three new sections
- Volume ranges use en-dashes (--) correctly (e.g., "20--99")
- The classification section uses commas, colons, semicolons, and
  parentheses for all subordinate clauses

**PASS: No dash violations.**

---

## 8. Additional Observations

### Abstract and conclusion don't mention classification

The abstract (lines 99-132) and conclusion (lines 1776-1796) don't mention
the link classification system. This is acceptable: the abstract is already
substantial (34 lines), and the classification is a methodological
refinement rather than a headline finding. The conclusion's five
enumerated findings focus on coverage, reliability, and discovery, all of
which are higher-level contributions than the classification scheme.
**No change needed.**

### Table numbering

The classification table is `Table~\ref{tab:classification}`. Assuming the
preceding tables are numbered 1-6 (sources, tibetan, genre, allerrors,
scholarly, sanskrit), this becomes Table 7. This is correct within the
paper's numbering sequence.

### The six classification types are well-chosen

The type taxonomy (parallel, parallel:computational, indirect:quotation,
chinese_to_tibetan, indirect:inherited, uncertain) is:
- Mutually exclusive (every link gets exactly one type)
- Exhaustive (every link is classified)
- Meaningful for downstream use (scholars can filter by type)
- Consistent with the paper's existing distinction between catalog and
  computational sources

### `\texttt{}` formatting for type names

Classification types are consistently formatted in `\texttt{}` throughout
all three sections (lines 748-753, 777, 994-995, 1697, 1701). **Consistent.**

---

## Summary of Findings

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | Table 7 statistics match JSON output | - | Verified |
| 2 | Paragraph (773-782) cites 252 quotation links but Table 7 shows 1,150 | Medium | **Fixed** |
| 3 | Paragraph (773-782) arithmetic framing implies 957 = 379 | Medium | **Fixed** |
| 4 | Limitations paragraph (1693-1705) is redundant with classification section | Medium | **Fixed** |
| 5 | T53n2122 count: paper said 42, actual is 44 | Low | **Fixed** |
| 6 | Transliteration compliance | - | PASS |
| 7 | American English | - | PASS |
| 8 | Minimal dashes | - | PASS |
| 9 | Consistency with existing text | - | PASS |
| 10 | Flow between sections | - | PASS |

## Fixes Applied

1. **Line 770**: Changed "42 computational-only Toh links" to "44" (verified
   against actual classification data: T53n2122 has 44 quotation Toh links).

2. **Lines 773-786**: Rewrote paragraph to reference Table 7 directly, use
   verified counts (1,150 quotation from 86 texts, 239 parallel:computational
   from 96 texts, 466 uncertain), and avoid the misleading "Of the 367..."
   framing that implied 239+252+466 was a subset of 379.

3. **Lines 1697-1704**: Trimmed limitations paragraph from 13 lines to 7,
   removing redundant restatements of the 239, 466, and extensibility points.

Paper compiles cleanly (31 pages).

## Verdict: A

After fixes, the new classification content is accurate, consistent with the
table, and free of redundancy. All statistics verified against the actual JSON
output.
