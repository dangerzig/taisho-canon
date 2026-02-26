# Paper Proofread: zigmond-tibetan-concordance.tex

Comprehensive review against current concordance data (`results/cross_reference_expanded.json`, rebuilt 2026-02-26) and code.

---

## 1. CRITICAL: Statistics Out of Date

The paper was written when the expanded concordance showed 733 Tibetan parallels. After adding 84000 TEI Taisho cross-references, scholarly citations (Li 2021, Silk 2019), multi-volume ID matching fixes, and CBETA Tibetan multi-variant resolution, the current numbers are substantially different.

### 1a. Abstract (lines 99-122)

| Claim in paper | Current value | Line |
|---|---|---|
| "733 of 2,455 Taishō texts" | **768 of 2,455** | 103 |
| "478 of 1,108 Kangyur texts (43.1%)" | **490 of 1,108 (44.2%)** | 103-104 |
| "116 of 3,461 Tengyur texts (3.4%)" | 116 of 3,461 (3.4%) — unchanged | 104 |
| "eight independent data sources" | Now **ten or more** sources (see §2) | 101-102 |
| "596 multi-source texts shows 67.4% full agreement" | Needs recalculation | 109 |
| "130 Taishō texts with probable Tibetan parallels" | 130 proposals, **107 unique Taishō texts** | 112-113 |

### 1b. Section 4: Tibetan Canon Coverage (lines 577-580)

Same "733 of 2,455" / "478 of 1,108" / "598 unique Tohoku" claims repeated:

| Claim | Current | Lines |
|---|---|---|
| "733 of 2,455 Taishō texts" | **768** | 577 |
| "478 of 1,108 Kangyur (43.1%)" | **490 of 1,108 (44.2%)** | 578 |
| "116 of 3,461 Tengyur (3.4%)" | unchanged | 578-579 |
| "598 unique Tohoku numbers" | **609** (606 in standard range, 3 anomalies) | 579 |

### 1c. Table 2: Coverage from the Tibetan side (lines 586-599)

Entire table needs updating:

| Row | Paper | Current |
|---|---|---|
| Kangyur | 478 / 1,108 / 43.1% | **490 / 1,108 / 44.2%** |
| Tengyur | 116 / 3,461 / 3.4% | unchanged |
| Total unique Toh | 598 / 4,569 / 13.1% | **609 / 4,569 / 13.3%** |
| Footnote "rows sum to 594; remaining 4" | Need to recount: **606 in range, 3 anomalies** |

### 1d. Table 3: Genre coverage (lines 642-664)

The genre table counts texts with ANY parallel (Tibetan, Pali, or Sanskrit), not just Tibetan. This is confusing given the section title "Tibetan Canon Coverage." Current numbers:

| Genre | Paper | Current | Change |
|---|---|---|---|
| Prajñāpāramitā | 40/45 (88.9%) | 40/45 (88.9%) | — |
| Śāstra | 129/190 (67.9%) | 129/190 (67.9%) | — |
| Mahāyāna sūtra | 348/597 (58.3%) | **355/597 (59.5%)** | +7 |
| Āgama | 83/155 (53.5%) | **86/155 (55.5%)** | +3 |
| Vinaya | 44/87 (50.6%) | **45/87 (51.7%)** | +1 |
| Jātaka/Avadāna | 33/72 (45.8%) | **34/72 (47.2%)** | +1 |
| Tantra/dhāraṇī | 251/610 (41.1%) | **258/610 (42.3%)** | +7 |
| History/biography | 9/96 (9.4%) | **10/96 (10.4%)** | +1 |
| Catalogues | 6/68 (8.8%) | 6/68 (8.8%) | — |
| Commentary | 5/159 (3.1%) | 5/159 (3.1%) | — |
| Dunhuang | 5/192 (2.6%) | 5/192 (2.6%) | — |
| Schools | 1/184 (0.5%) | 1/184 (0.5%) | — |
| **Total** | **954** | **974** | **+20** |

Recommendation: Clarify that Table 3 counts "any parallel" (not just Tibetan), or recalculate for Tibetan-only.

### 1e. Table 1: Data sources (lines 300-322)

"After removing duplicates: 954" → **974**

The table itself also needs updating for new sources (see §2 below).

### 1f. Sanskrit title matching (Section 5, lines 1160-1187)

Major changes from precision improvements:

| Statistic | Paper | Current |
|---|---|---|
| Total matches | 326 | **231** |
| Exact | 192 | 192 (same) |
| Fuzzy | 134 | **39** |
| Confirmed by concordance | 104 | **77** |
| Contradicted | 57 | **24** |
| Validation rate | 64.6% | **76.2%** |
| New proposals | 165 | **130** |
| Unique Taishō texts | 130 | **107** |

Table 4 (lines 1167-1187) and all surrounding text (lines 1160-1252) need rewriting with new numbers. The improved validation rate is a better result and should be highlighted.

The text at line 1407 says "64.6% validation rate" — update to **76.2%**.

### 1g. Otani coverage (lines 1387-1394)

Paper says: "716 of the 727 Taishō texts with Tohoku numbers (98.5%)"

This is wrong. Current data shows **518 texts with Otani numbers** out of 762 with Tohoku (67.8%). The "716" figure was from a previous session's Otani merge that used the `tohoku_otani_concordance.json` file (4,301 Toh→Otani mappings from rKTs), but this merge is **not integrated into the current build script** (`build_expanded_concordance.py`). Either:
- (a) Integrate the Otani concordance into the build script (recommended), which would restore ~716+ Otani mappings, or
- (b) Update the paper to reflect current (lower) Otani coverage.

The "12 Taishō texts lacking Otani numbers correspond to just five Tohoku numbers" claim also needs re-verification after any fix.

### 1h. Kangyur gaps (line 822)

"630 Kangyur texts without identified Chinese parallels" → now **1108 - 490 = 618**

### 1i. Chinese side gaps (line 828)

"approximately 1,500 Taishō texts without Tibetan parallels" → now **2455 - 768 = 1,687**

### 1j. Concordance entry examples (lines 510-569)

The illustrative JSON examples show the OLD format without `link_provenance`. They should be updated to reflect schema v2, which has per-link attestation. For example, the T08n0251 entry now shows source attestations per Tohoku link, not just a flat list of sources.

Also, the source list `["lancaster", "cbeta_tibetan", "acmuller", "manual"]` for T08n0251 is now `["84000_tei_refs", "acmuller_tohoku", "cbeta_sanskrit", "cbeta_tibetan", "existing", "lancaster", "lancaster_full", "standard_parallels"]` (8 sources, not 4).

### 1k. Source agreement (lines 500-508)

"596 texts with Tohoku data from two or more independent sources" with "67.4% full agreement" — these numbers need recalculation with the current provenance data.

### 1l. "130 newly identified Taishō texts represent a potential 18% expansion" (line 1251)

With 768 current Tibetan parallels + 107 unique new proposals: 107/768 = **13.9%**, not 18%.

---

## 2. Structural: Data Sources Description Needs Updating

### 2a. Number of sources

The paper consistently says "eight independent data sources" (abstract line 101, section 2 line 284, section 7 lines 1472-1473, conclusion enumeration). The concordance now has:

1. SuttaCentral
2. Lancaster catalog
3. Muller Tohoku index (acmuller)
4. CBETA Jinglu Tibetan
5. CBETA Jinglu Sanskrit/Pāli
6. rKTs
7. 84000 TEI (title enrichment)
8. **84000 TEI Taisho cross-references** (NEW: 457 links from bibliography/notes in 84000 translation files)
9. Sanskrit title matching
10. **Scholarly citations** (NEW: Li 2021, Silk 2019, standard parallels — 45 links total)

Sources 8 and 10 are genuinely new since the paper was written. The "eight" should become "ten" throughout, and Table 1 needs rows for these sources.

### 2b. "Manual scholarship" description (lines 394-397)

The paper says: "A small set of ~10 mappings from published scholarship not captured by any automated source, including Nattier (1992)'s Heart Sūtra analysis. Manual entries are marked with `source="manual"` in the concordance JSON for transparency."

This is now outdated. "Manual scholarship" has been replaced by:
- `data/scholarly_citations/li2021.json` (25 links, Li Channa 2021)
- `data/scholarly_citations/silk2019.json` (28 links, Silk 2019)
- `data/scholarly_citations/standard_parallels.json` (9 links + 3 flagged errors)
- Per-link provenance with proper scholarly citations (Frauwallner 1956, Conze 1978, Nattier 1992, etc.)

The source is no longer "manual" but properly cited scholarly identifications with `source="li2021"`, `source="silk2019"`, `source="standard_parallels"` in the provenance.

### 2c. 84000 TEI description (lines 387-392)

The paper says 84000 TEI was "used primarily for title enrichment ... rather than for new Taishō-Tibetan mappings." This is no longer accurate. The new `84000_tei_refs` source extracts 457 Taisho cross-references from the bibliographic notes and inline references in 84000's TEI translation files, making 84000 one of the largest single sources of provenance attestations (490 links). This is a substantial contribution beyond title enrichment.

### 2d. Per-link provenance (schema v2)

The concordance now uses schema v2 with per-link attestation (`link_provenance` section), which the paper doesn't describe. Each (Taishō, Tohoku) pair now has its own list of attestations with source, confidence score, and optional note. This is a stronger provenance model than the per-text source tracking described in the paper. Consider describing this in §3 (Merging Methodology).

---

## 3. Content Gaps

### 3a. Li 2021 and Silk 2019 as data sources

Li Channa (2021) is cited in the paper (line 200, 405) but only in passing as a survey reference. Silk (2015) is cited (line 405, 442). Neither is described as a DATA SOURCE contributing to the concordance. Since we now have 25 links from Li 2021 and 28 from Silk 2019 integrated as scholarly citations, these should be mentioned as contributing sources.

### 3b. Multi-source corroboration statistics

The concordance now has **1,293 links with 2+ source corroboration** out of 1,402 total (92.2%). This is a strong result worth mentioning: it means the vast majority of concordance links are independently confirmed by multiple catalogs.

### 3c. Tohoku-to-Otani concordance

The `tohoku_otani_concordance.json` file (4,301 Toh→Otani mappings from rKTs collection data) is not loaded by the build script but is referenced in the paper. This needs to be either integrated or the paper's claims about Otani coverage need to be revised.

---

## 4. Style and Language Issues

### 4a. American English

Overall good. A few items to check:
- Line 813: "cataloguing" → **"cataloging"** (American English)
- Line 866: "catalogers" → OK (American)
- Line 942: "cataloguing" → **"cataloging"**
- Line 966: "catalogues" → acceptable in "print catalogs" context, but consider **"catalogs"** for consistency
- Line 968: "catalogues" → **"catalogs"**
- Line 1573: "catalogers" → OK
- Line 1577: "cataloguing" → **"cataloging"**

Search the file for all instances of "catalogu" and normalize to American spelling except in cited work titles.

### 4b. Em-dashes

No em-dashes found. Good.

### 4c. Dashes in general

Line 949: "these should count as a single witness when they agree" — missing punctuation after "Family A" designation. The sentence runs on. Consider: "...CBETA Sanskrit. These should count as a single witness..."

### 4d. Transliteration convention

Generally well-followed. A few checks:

- Line 161: `\zh{經錄} \py{j\={\i}ngl\`u}` — first use, but no English translation in parentheses. Should add: `("catalog of scriptures")` — WAIT, it IS there: "``catalog of scriptures''" on line 162. OK.
- Line 206: `\zh{目録學} \py{m\`ul\`ux\'ue}` — first use with English translation "``cataloguing studies''" → should be **"cataloging studies"** (American English)
- Line 364: `\zh{大藏經} \py{d\`az\`angj\={\i}ng}` — first use with translation. OK.
- Line 434: `\zh{四十二章經} \py{S\`ish\'i\`erzh\=angj\={\i}ng}` — OK with English in parentheses.
- Line 692: `\zh{阿含經} \py{\=Ah\'anj\={\i}ng}` — OK with English translation.

### 4e. Consistency: "Taishō" accent

Consistent throughout as `Taish\=o`. Good.

### 4f. No venue references

No journal names or venue references found in the text or filename. Good.

---

## 5. Minor Issues

### 5a. Line 207

"2,920 texts across 100 volumes" — our corpus has 2,455 texts. The 2,920 figure is the total Taishō count including texts not in our corpus (we only include vols 1-55 and 85). This is fine but could be confusing. Consider clarifying: "2,920 texts across 100 volumes (of which 2,455 fall within volumes 1-55 and 85, comprising the core canonical texts)."

### 5b. Line 247

"rKTs (Resources for Kanjur and Tanjur Studies)" — this is the first use with full name. Good.

### 5c. Line 274

"23 texts flagged as rgya nag nas bsgyur" — current rKTs data still shows ~23 entries. OK.

### 5d. Line 525

Example entry shows `"sources": ["lancaster", "cbeta_tibetan", "acmuller", "manual"]` — source names don't match current names. "acmuller" is now "acmuller_tohoku"; "manual" is now "standard_parallels" or individual citation keys.

### 5e. Lines 832-843: Mahāprajñāpāramitāsūtra gap

The paper says T05-07n0220 "lacks a Tohoku mapping in the concordance." This may no longer be accurate: the expanded concordance now maps T05n0220, T06n0220, and T07n0220 to multiple Toh numbers via both CBETA Tibetan and 84000 TEI refs (the multi-volume matching fix). Check whether this "notable gap" still exists.

### 5f. Lines 1516-1517

"at least 60 additional Taishō texts" from LLM matching — check if this number is still accurate or if it has been superseded by the concordance improvements.

### 5g. Line 1420

GitHub URL "dangerzig" — verify this is the correct repository name.

---

## 6. Recommended Priority

All items below have been COMPLETED (2026-02-26):

1. **Fix statistics** (§1a-1l): DONE. All numerical claims updated to current data (768 Tibetan, 491/1108 Kangyur, 610 Toh, 231 Sanskrit matches, 76.2% validation, etc.).
2. **Update source descriptions** (§2a-2d): DONE. Added 84000 TEI cross-refs and scholarly citations as sources; "eight" → "nine" throughout.
3. **Integrate Otani concordance** (§1g, §3c): DONE. Added Tohoku-Otani concordance post-processing to build script. 752/762 (98.7%) Otani coverage.
4. **Update Sanskrit matching section** (§1f): DONE. All numbers rewritten (231 total, 76.2% validation, 107 unique new proposals).
5. **American English** (§4a): DONE. All "cataloguing" → "cataloging" via replace-all.
6. **Update concordance entry examples** (§1j): DONE. Schema v2 format with per-link provenance.
7. **Content enrichment** (§3a-3b): DONE. Li/Silk cited as data sources; 92.0% multi-source corroboration mentioned.
8. **Notable gaps updated** (§5e): DONE. T05-07n0220 gap removed (now mapped via multi-volume fix).
9. **Genre table updated** (§1d): DONE. All genre counts updated.
10. **Bibliography updated**: DONE. Added Conze 1978 and Frauwallner 1956 entries.
