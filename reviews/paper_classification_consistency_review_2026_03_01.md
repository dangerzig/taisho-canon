# Paper Proofread: Classification-Related Consistency

**Date**: 2026-03-01
**Paper**: `zigmond-tibetan-concordance.tex`
**Focus**: Statements throughout the paper that may be misleading or
inconsistent in light of the link classification system

---

## Methodology

Read the full paper (2,124 lines) searching for every use of "parallel,"
"parallels," "link," "links," "connection," "concordance entry," and related
terminology. For each occurrence, assessed whether the language is:
- **Accurate** given that 4,647 links include 6 distinct types (genuine
  parallels, quotation artifacts, Chinese-to-Tibetan translations, etc.)
- **Consistent** with the earlier fixes (line 344 "cross-canon links,"
  line 826 "cross-canon links," classification forward references)

---

## Findings

### ISSUE 1: "new parallels" in MITRA paragraph (line 467)

**Severity: Medium**

> "only strong MITRA links (>=100 aligned sentences) are added to the
> active concordance as new parallels."

Of the 367 strong-tier links, a substantial fraction are quotation artifacts
from encyclopedic compilations (classified as `indirect:quotation`), not
genuine parallels. The forward reference at lines 480-485 (added earlier
today) explains this, but calling them "new parallels" on first mention is
misleading. Lines 644-646 already use the correct term "new concordance
entries."

**Fix**: Change "as new parallels" to "as new entries" (or "as new links").

---

### ISSUE 2: "retains only the parallel relationships" in Mahāratnakūṭa case study (line 1343)

**Severity: High**

> "Sentence-level alignment data from MITRA identifies additional Tohoku
> numbers with textual overlap, though some of these are Tengyur
> commentaries on the constituent sūtras rather than parallel translations;
> the concordance retains only the parallel relationships."

This is factually wrong after the classification system was implemented:

1. The concordance **retains all** links that pass the minimum sentence
   threshold, not just parallel ones.
2. The T11n0310 illustrative entry (lines 704-709) explicitly shows 9
   MITRA-only links classified as `indirect:quotation`, demonstrating that
   non-parallel links ARE retained.
3. The classification section (lines 735-818) describes how quotation links
   are classified rather than removed.

The statement contradicts the illustrative entry and the classification
system. A reader who sees the mixed types in §3.5 and then reads "retains
only the parallel relationships" in §5.3 will be confused.

**Fix**: Rewrite to reflect that the concordance records all connections
and classifies them:

> "Sentence-level alignment data from MITRA identifies additional Tohoku
> numbers with textual overlap, including Tengyur commentaries on the
> constituent sūtras; the link classification system
> (§\ref{sec:classification}) classifies these by relationship type."

---

### ISSUE 3: "every identifiable Taisho parallel" in Introduction (lines 250-252)

**Severity: Low**

> "every identifiable Taisho parallel in the Derge has a Tohoku number,
> every identifiable parallel in the Peking has an Otani number"

For consistency with line 344 ("838 have identified Tibetan cross-canon
links") and line 826 ("identifies Tibetan cross-canon links for 838"),
these aggregate references should use "cross-canon link" rather than
"parallel." The same point is made about individual edition coverage, where
"link" encompasses all relationship types including quotation artifacts.

**Fix**: Change "every identifiable Taisho parallel in the Derge" to "every
identifiable cross-canon link in the Derge" and similarly for Peking.

---

### ISSUE 4: Repeated edition statement in Limitations (lines 1700-1702)

**Severity: Low**

> "every identifiable parallel in the Derge carries a Tohoku number, and
> every identifiable parallel in the Peking carries an Otani number"

Same issue as #3, repeated in the Limitations section.

**Fix**: Change both "parallel" to "cross-canon link" for consistency.

---

## Statements Reviewed and Found Acceptable

The following uses of "parallel(s)" were examined and found acceptable in
context:

| Line(s) | Text | Reason OK |
|---------|------|-----------|
| 138-139 | "identify Chinese parallels for texts they study" | Individual scholar lookup; what they seek IS a parallel |
| 154 | "locating Tibetan parallels for Chinese texts" | Same |
| 178 | "A scholar seeking the Chinese parallel" | Same |
| 192 | "107 previously uncataloged Taishō–Tibetan parallels" | Title-match proposals are likely genuine parallels |
| 421 | "content parallels" | Contrastive term vs. translation relationships |
| 477 | "genuine parallels" | Already in classification-aware context |
| 857 | "Nearly half of all Kangyur texts have identified Chinese parallels" | Kangyur-side; line 829 already caveats 28 quotation-only texts |
| 882 | "identify a Chinese parallel" | Individual lookup probability |
| 1002 | "no direct Tibetan parallel" | Individual Vinaya text discussion |
| 1098 | "its Chinese parallel" | Individual lookup |
| 1122-1128 | "without identified Chinese/Tibetan parallels" | Zero-link texts; genuinely have no connections |
| 1427 | "discover new parallels" | Computational discovery section; title matches are genuine |
| 1531 | "not previously linked to Tibetan parallels" | Title-match proposals |
| 1605 | "identify Chinese parallels for Kangyur texts" | Individual lookup workflow |
| 1620 | "map to the same Tibetan parallel" | Retranslation validation |
| 1627-1628 | "without Chinese/Tibetan parallels" | Gap analysis |
| 1677-1679 | "have Tibetan parallels" | Title-match proposals |
| 1719-1720 | "identifies which texts are parallel" | Pāli context (all SuttaCentral links are genuine) |
| 1830 | "probable Tibetan parallels" | Title-match proposals |
| 1843 | "discover new parallels" | Future directions |
| 1897 | "confirmed parallels" | LLM matching validation |
| 1945-1946 | "discover parallels" | Future embedding directions |

---

## Transliteration, American English, Dashes

Not re-checked here (passed in previous review). The focus of this review
was exclusively classification-related consistency.

---

## Summary

| # | Finding | Severity | Location |
|---|---------|----------|----------|
| 1 | "as new parallels" — some are quotation artifacts | Medium | Line 467 |
| 2 | "retains only the parallel relationships" — factually wrong | High | Line 1343 |
| 3 | "every identifiable Taisho parallel" — should be "link" | Low | Lines 250-252 |
| 4 | Same as #3, repeated | Low | Lines 1700-1702 |

Total: 1 high, 1 medium, 2 low.
