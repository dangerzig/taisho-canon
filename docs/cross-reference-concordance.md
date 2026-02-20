# Cross-Canon Concordance: Taisho↔Tibetan/Pali/Sanskrit

## 1. Introduction

This document describes a unified cross-canon concordance that maps texts in the
Taisho Tripitaka (大正新脩大藏經) to their parallels in the Tibetan Buddhist canon
(Kangyur/Tengyur), the Pali Tipitaka, and surviving Sanskrit sources. The
concordance was compiled by programmatically merging eight independent data
sources into a single machine-readable lookup table with provenance tracking.

The result covers 954 of 2,455 Taisho texts (38.9%), including Tibetan parallels
for 733 texts, Sanskrit identifications for 859, and Pali parallels for 75. To
our knowledge, this is the first project to systematically merge all of these
sources into a single unified concordance with per-mapping provenance.

### 1.1 Why a Concordance Matters

The Chinese Buddhist canon and the Tibetan Buddhist canon represent the two
largest surviving collections of Buddhist literature, both ultimately derived
from Indic originals that are in most cases lost. Knowing which Chinese text
corresponds to which Tibetan text is fundamental for:

- **Textual criticism**: Comparing Chinese and Tibetan translations of the same
  Indic source reveals translation choices, scribal errors, and textual variants.
- **Validating computational results**: Our digest detection pipeline identifies
  retranslation pairs (different Chinese translations of the same source) based
  on character-level overlap. The concordance provides independent validation: if
  two Chinese texts are correctly identified as retranslations, they should map to
  the same Tohoku number.
- **Identifying Chinese compositions**: Texts that appear to be digests of other
  Chinese texts and have *no* Tibetan or Sanskrit parallel may be Chinese
  compositions rather than translations from Indic originals.
- **Cross-tradition scholarship**: The concordance enables researchers to move
  between the Chinese, Tibetan, and Pali canonical traditions using a single
  lookup, without needing to consult multiple separate catalogues.

## 2. Prior Work on Cross-Canon Concordances

### 2.1 Print Concordances

The problem of mapping texts across Buddhist canonical traditions has a long
scholarly history, though no single prior work has achieved comprehensive
coverage.

**Nanjio Bunyiu** (南條文雄, 1849--1927) produced the earliest modern
Western-language catalogue of the Chinese canon: *A Catalogue of the Chinese
Translation of the Buddhist Tripitaka* (Oxford: Clarendon Press, 1883). This
assigned "Nanjio numbers" (Nj) that became a standard reference system and
included Sanskrit title identifications where known. However, the Nanjio
catalogue predates the Taisho edition (1924--1934) and does not include
Tibetan cross-references.

**Ui Hakuju** (宇井伯壽) and colleagues at Tohoku University produced *A Complete
Catalogue of the Tibetan Buddhist Canons (Bkah-hgyur and Bstan-hgyur)* (Sendai,
1934), which established the now-standard "Tohoku numbers" (Toh 1--4569): Toh
1--1108 for the Kangyur, Toh 1109--4569 for the Tengyur. This catalogue includes
Sanskrit title reconstructions and occasional Chinese cross-references but was
not designed as a systematic Taisho-to-Tohoku concordance.

**Akanuma Chizen** (赤沼智善) published *The Comparative Catalogue of Chinese
Āgamas and Pāli Nikāyas* (Nagoya: Hajinkaku shobo, 1929; reprinted 1958, 1990),
the first comprehensive concordance between the Chinese Āgama collections
(Taisho vols. 1--2) and the Pali Nikāyas. This pioneering work covers only the
early Buddhist texts (Āgamas/Nikāyas) and does not include Tibetan parallels.
Akanuma's data has been corrected and extended by Rod Bucknell, Bhikkhu
Anālayo, and Marcus Bingenheimer, and is now incorporated into SuttaCentral's
parallel database.

**D.T. Suzuki** supervised the photographic reprint of the Peking edition of the
Tibetan Tripitaka (168 volumes, Tibetan Tripitaka Research Institute, Kyoto,
1955--1961). The Otani University Library produced *A Comparative Analytical
Catalogue of the Kanjur Division* (3 vols., 1930--1932) and *Tanjur Division* (9
vols., 1965--1997), using the Peking/Otani (P/Q) numbering system. These are
primarily intra-Tibetan concordances between different Kangyur editions, not
Tibetan-to-Chinese mappings.

**Lewis R. Lancaster** and Sung-bae Park produced *The Korean Buddhist Canon: A
Descriptive Catalogue* (Berkeley: University of California Press, 1979), which
is the closest thing to a multi-system concordance in print. Each entry in the
Korean Tripitaka (K-number system) is cross-referenced with Taisho numbers
(T.), Tohoku numbers (To.), Nanjio numbers (Nj.), and Otani numbers (O.), along
with Sanskrit titles. Lancaster's catalogue thus provides a Taisho-to-Tohoku
bridge via the Korean canon's K-numbers. However, its coverage is limited to
texts present in the Korean Tripitaka: approximately 1,521 K-number entries, of
which ~790 have Taisho data and ~590 have Tohoku numbers.

**Adelheid Herrmann-Pfandt** published *Die lHan kar ma: Ein früher Katalog der
ins Tibetische übersetzten buddhistischen Texte* (Vienna: Verlag der
österreichischen Akademie der Wissenschaften, 2008), a critical edition of the
Denkarma (lHan kar ma), one of three ninth-century Tibetan imperial catalogues.
The apparatus includes cross-references to Chinese canon editions, documenting
the earliest historical layer of Tibetan-Chinese textual correspondence.

**Paul Hackett** produced *A Catalogue of the Comparative Kangyur* (AIBS/Columbia,
Treasury of the Buddhist Sciences series, 2013), providing concordance tables
across seven Kangyur recensions (Derge, Lhasa, Narthang, Cone, Peking, Urga,
Litang). This is primarily an intra-Kangyur concordance and does not map to
Taisho numbers.

### 2.2 Digital Projects

Several digital projects provide partial cross-canon reference data:

**SuttaCentral** (suttacentral.net), founded by Bhikkhu Sujato and Bhikkhu
Brahmali, maintains a database of parallel passages across Pali, Chinese,
Tibetan, and Sanskrit sources. Data is stored as structured JSON at
github.com/suttacentral/sc-data. Parallels are manually curated by scholars,
building on Akanuma's 1929 catalogue. Coverage is strongest for early Buddhist
texts (Āgamas/Nikāyas) and thinner for Mahāyāna, Tantra, and Abhidharma.

**rKTs (Resources for Kanjur and Tanjur Studies)**, maintained by the Tibetan
Manuscript Project Vienna (TMPV) at the University of Vienna, is the largest
database of Tibetan canonical literature, covering over 100 Kanjur, Tanjur, and
Tantra collections. The database includes a `translation-taisho` field for texts
identified as translations from Chinese, but this covers only the small subset
explicitly identified as Chinese-to-Tibetan translations (~23 entries with
Taisho cross-references), not the much larger set of texts sharing a common
Indic original. Data is available on GitHub in XML format.

**84000: Translating the Words of the Buddha** (84000.co) is translating the
entire Kangyur and Tengyur into English. TEI XML data on GitHub provides
structured metadata including Tohoku numbers and Sanskrit/Tibetan titles.
However, Taisho correspondences appear only as individual scholarly notes
within translation introductions, not as a systematic concordance table.

**CBETA Jinglu** (jinglu.cbeta.org), the Digital Database of Buddhist Tripitaka
Catalogues, contains ~33,700 Chinese catalogue entries, ~4,569 Tibetan entries,
~7,003 Pali entries, and Sanskrit catalogues, with cross-references between
them. This is the richest single source of Tibetan-to-Taisho mappings, but
the interface is a CGI-based web application with no API or bulk download,
requiring systematic scraping for programmatic access.

**SAT Daizōkyō Text Database** (University of Tokyo) provides the full Taisho
text with linked data integration but has not been systematically extended to
cross-canon concordance. **BDRC** (Buddhist Digital Resource Center) is the
largest online archive of Tibetan Buddhist materials but focuses on Tibetan
texts, not cross-canon mapping.

**Marcus Bingenheimer's Digital Comparative Catalog of Āgama Literature**
(mbingenheimer.net/tools/comcat/, v3, 2006) reworks Akanuma's concordance
digitally but is limited to Āgama/Nikāya texts.

The **AIBS Buddhist Canons Research Database** (Columbia University) and **DILA
Buddhist Studies Authority Database** (Dharma Drum Institute) provide
bibliographic cross-referencing but do not offer systematic Taisho-to-Tohoku
mappings in bulk-processable form.

### 2.3 The Gap

Despite this substantial body of prior work, **no previous project has
systematically merged multiple independent cross-canon data sources into a
single unified concordance with provenance tracking.** Each existing resource
covers a different subset of the correspondence, uses different identifier
formats, and has different coverage patterns:

| Source | Taisho Coverage | Tibetan Coverage | Format |
|--------|:-:|:-:|--------|
| Lancaster (1979) | ~790 texts | ~590 with Toh | Print / HTML |
| SuttaCentral | ~500 (mainly Āgamas) | Partial | JSON/GitHub |
| CBETA Jinglu Tibetan | Varies | ~4,569 entries | CGI/web only |
| CBETA Jinglu Sanskrit | Varies | Partial | CGI/web only |
| rKTs | ~23 texts | ~5,000+ kernels | XML/GitHub |
| 84000 TEI | Ad hoc | ~1,108 Kangyur | TEI/GitHub |
| acmuller Tohoku index | ~560 texts | ~590 Toh numbers | HTML |

Key challenges that a unified concordance must address include:

- **ID format inconsistency**: Lancaster uses "T250"; CBETA uses "T08n0250";
  rKTs uses kernel IDs; 84000 uses "Toh" prefixes. Resolving these to a common
  format requires knowing that T250 lives in Taisho volume 08.
- **One-to-many mappings**: A single Taisho text may correspond to multiple
  Tohoku numbers (and vice versa), requiring list-valued lookups.
- **Source disagreement**: Different sources occasionally disagree on
  correspondences. A unified concordance should track provenance so users can
  assess confidence.
- **Uneven genre coverage**: Early Buddhist texts (Āgamas) are well served by
  SuttaCentral and Akanuma; Mahāyāna sūtras are partially covered by Lancaster;
  Tantric, Abhidharma, and commentarial literature remains sparse.

## 3. Data Sources and Acquisition

Our concordance merges eight independent data sources. Each was obtained through
a dedicated Python script in `scripts/`, using polite rate-limited HTTP requests
for web scraping and standard XML parsing for structured data.

### 3.1 SuttaCentral (Baseline)

**Script**: Manual download from github.com/suttacentral/sc-data

**Data**: `sc-data/relationship/parallels.json` -- structured JSON mapping Pali
sutta IDs (e.g., SN 22.59) to Chinese Āgama IDs (e.g., SA 34) and Tibetan
parallels where known.

**Coverage**: ~500 Taisho texts, strongest for Āgama sections (vols. 1--2).
Provides Pali, Tibetan, and partial Sanskrit identifications.

**Processing**: Pali sutta IDs were retained as-is. Chinese references were
resolved to CBETA Taisho IDs (T##n####) using volume-number lookup tables.

### 3.2 Lancaster Korean Buddhist Canon Catalogue

**Script**: `scripts/scrape_lancaster_full.py`

**Source**: Charles Muller's digitization of Lancaster's catalogue at
acmuller.net/descriptive_catalogue/. The script fetched all ~1,521 K-number
detail pages (`files/k####.html`), parsing header lines for Taisho numbers
(T.), cross-reference sections for Tohoku (To.), Otani (O.), and Nanjio (Nj.)
numbers, and body text for Sanskrit and Chinese titles.

**Output**: `results/lancaster_full.json` -- 1,478 entries with Taisho
cross-references.

**Coverage**: The broadest single source for multi-system cross-references.
Covers ~790 texts with Taisho data and ~590 with Tohoku numbers. Particularly
strong for Mahāyāna sūtras and Vinaya literature present in the Korean
Tripitaka.

**Note**: A smaller initial extraction (`lancaster_taisho_crossref.json`, 790
entries) was performed first from a partial scrape; the full scrape expanded this
to 1,478 entries. Both are merged into the concordance as separate sources to
track provenance.

### 3.3 acmuller Tohoku→Taisho Index

**Script**: `scripts/scrape_tohoku_index.py`

**Source**: The Tohoku index page at acmuller.net, which lists Tohoku numbers and
links to the corresponding K-number detail pages. This works from the Tibetan
side: for each Tohoku number, the script follows links to K-number pages and
extracts Taisho cross-references.

**Output**: `results/tohoku_taisho_crossref.json` -- 382 Tohoku entries, 360
with Taisho cross-references.

**Coverage**: ~560 Taisho texts. This source catches Taisho↔Tibetan mappings
reachable via the Tohoku→K→Taisho path that the Chinese-side Lancaster scrape
may have missed.

### 3.4 CBETA Jinglu Tibetan Catalogue

**Script**: `scripts/scrape_cbeta_jinglu_tibetan.py`

**Source**: The CBETA Digital Database of Buddhist Tripitaka Catalogues at
jinglu.cbeta.org. The script fetched all 4,569 Tibetan detail pages
(`/cgi-bin/tibet_detail.pl?lang=&id=NNNN`, NNNN=0001--4569), parsing
structured fields for:

- 經碼 (No.): Entry number (corresponding to Tohoku number)
- 大正藏: Linked Taisho numbers
- 南條文雄: Nanjio number
- 梵文經名: Sanskrit title
- 中文經名: Chinese title
- 藏文經名: Tibetan title (Unicode)
- 藏語羅馬轉寫經名: Tibetan Wylie transliteration

**Output**: `results/cbeta_jinglu_tibetan.json` -- ~613 entries with Taisho
cross-references.

**Coverage**: This is the most authoritative Chinese-language source for
Tibetan↔Taisho correspondences, compiled by CBETA scholars from multiple
traditional catalogue sources.

### 3.5 CBETA Jinglu Sanskrit/Pali Catalogue

**Script**: `scripts/scrape_cbeta_jinglu_sanskrit.py`

**Source**: The CBETA Jinglu Sanskrit/Pali section at jinglu.cbeta.org
(`/cgi-bin/jl_san_detail.pl?lang=&id=NNNN`, NNNN=0001--~1395), providing
Taisho cross-references from the Sanskrit/Pali tradition angle, including
Tohoku, Otani, and Nanjio numbers.

**Output**: `results/cbeta_jinglu_sanskrit.json` -- ~703 entries with Taisho
cross-references.

**Coverage**: Complements the Tibetan catalogue by providing mappings from
surviving Sanskrit and Pali sources. Particularly useful for texts where the
Sanskrit manuscript tradition is better documented than the Tibetan.

### 3.6 rKTs (Resources for Kanjur and Tanjur Studies)

**Script**: `scripts/parse_rkts.py`

**Source**: The rKTs XML data from GitHub (github.com/brunogml/rKTs), maintained
by the Tibetan Manuscript Project Vienna (TMPV). The script parsed:

- `Kernel/rkts.xml` -- Kanjur kernel entries with `<cmp>` comparison tags of type
  `translation-taisho`, mapping Tibetan texts to their Chinese translations
- `Collections/D Derge Kanjur/D.xml` -- rKTs→Dergé/Tohoku mapping

**Output**: `results/rkts_taisho.json` -- ~23 entries with Taisho
cross-references.

**Coverage**: Small but uniquely authoritative. rKTs is the most comprehensive
database of Tibetan canonical literature, and its `translation-taisho` tags
specifically identify texts explicitly catalogued as Chinese-to-Tibetan or
Tibetan-to-Chinese translations. However, this covers only translations
identified as such by Tibetan cataloguers, not the much larger set of texts
that share a common Indic ancestor.

### 3.7 84000 TEI Data

**Script**: `scripts/extract_84000_tohoku.py`

**Source**: The 84000 project's TEI XML data at github.com/84000/data-tei.
The script extracted Tohoku numbers from filenames (e.g., `035-018_toh44-18-...`)
and TEI metadata, along with English, Sanskrit, and Tibetan titles.

**Output**: `results/84000_tohoku_extract.json` -- Title and metadata enrichment
for existing Tohoku entries.

**Coverage**: Used primarily for title enrichment rather than new
Taisho↔Tibetan mappings, since 84000 does not maintain a systematic Taisho
concordance. When an existing concordance entry already had a Tohoku number
present in the 84000 data, Sanskrit titles from 84000 were added.

### 3.8 Manual Scholarship Mappings

A small set of mappings was added from published scholarship, including
Nattier's Heart Sutra analysis and other well-established correspondences not
captured by the above sources. These are recorded with source tag `"existing"` in
the concordance.

## 4. Merging Methodology

### 4.1 ID Normalization

The central technical challenge is resolving different identifier formats to a
single canonical form. The concordance uses the CBETA format `T##n####` (e.g.,
T08n0250) as the canonical Taisho identifier. The merging script
(`scripts/build_expanded_concordance.py`) performs the following normalizations:

- **Bare Lancaster numbers** (e.g., "T250", "T0250"): Resolved to full CBETA
  format by looking up the bare number in a map built from all known corpus IDs.
  For example, bare number 250 resolves to T08n0250.
- **Letter-suffixed IDs** (e.g., "T08n0236a"): Retained as-is when the suffixed
  form exists in the corpus; otherwise the base form is used.
- **CBETA format IDs**: Passed through unchanged.

Tibetan identifiers are normalized to "Toh NNN" or "Otani NNN" format. Nanjio
numbers use "Nj NNN" format.

### 4.2 Source Merging

Each source is loaded in sequence, and for each Taisho text, its Tibetan, Pali,
Sanskrit, and Nanjio identifiers are added to a master lookup as sets
(preventing duplicates). A `sources` set tracks which data sources contributed
information for each text.

When multiple sources provide the same mapping (e.g., both Lancaster and CBETA
Jinglu map T01n0001 to Toh 34), the mapping is recorded once but both sources
are listed in the provenance.

### 4.3 Conflict Handling

Sources occasionally disagree on correspondences. The current strategy is
**union**: all mappings from all sources are included. When a Taisho text maps
to multiple Tohoku numbers, all are recorded. This is often correct rather
than conflicting -- a single Chinese text can legitimately correspond to
multiple Tibetan canon entries (e.g., different sections of a large work may
have separate Tohoku numbers, or different Kangyur editions may assign
different numbers). The provenance tracking allows users to assess confidence
based on source agreement.

## 5. Results

### 5.1 Coverage Summary

The expanded concordance covers 954 of 2,455 Taisho texts (38.9%):

| Parallel Tradition | Texts with Parallel | Coverage |
|-------------------|--------------------:|--------:|
| Sanskrit | 859 | 35.0% |
| Tibetan | 733 | 29.9% |
| Pali | 75 | 3.1% |
| **Any parallel** | **954** | **38.9%** |
| No known parallel | 1,501 | 61.1% |

The relatively low Pali coverage reflects the fundamental split between the
Theravāda and Chinese Mahāyāna canons; the 75 texts with Pali parallels are
concentrated in the Āgama sections (Taisho vols. 1--2).

### 5.2 Source Contributions

Each source contributed mappings for the following number of Taisho texts:

| Source | Texts Covered | Unique Contribution |
|--------|:---:|---|
| Lancaster full K-number scrape | 1,478 | Broadest single source |
| Baseline (SuttaCentral + manual) | 941 | Foundation layer |
| CBETA Jinglu Sanskrit/Pali | 703 | Sanskrit/Pali angle |
| CBETA Jinglu Tibetan | 613 | Authoritative Chinese-language source |
| Lancaster (initial extraction) | 790 | Multi-system cross-refs |
| acmuller Tohoku index | 560 | Tibetan-side Toh→K→T path |
| rKTs kernel | 23 | Explicit translation-taisho tags |

The baseline expanded from 941 to 954 texts with the addition of the extra
sources. Most of the "expansion" was in enrichment (adding Tohoku/Otani/Sanskrit
data to texts that already had some parallel information) rather than discovering
entirely new text-level correspondences.

### 5.3 Coverage from the Tibetan Side

From the Tibetan perspective, the concordance covers:

| Tibetan Canon Section | Texts in Concordance | Total in Canon | Coverage |
|----------------------|:---:|:---:|:---:|
| Kangyur (Toh 1--1108) | 478 | 1,108 | 43.1% |
| Tengyur (Toh 1109--4569) | 116 | 3,461 | 3.4% |
| **Total unique Toh numbers** | **598** | **4,569** | **13.1%** |

The Kangyur coverage (43.1%) is substantially higher than Tengyur coverage
(3.4%), reflecting the fact that sūtra-level correspondences are better
documented than śāstra/commentary correspondences. The concordance also contains
395 unique Otani (Peking edition) numbers.

Most Taisho texts map to 1--2 Tohoku numbers, but some map to many more:

| Toh numbers per Taisho text | Count |
|:---:|:---:|
| 1 | 438 |
| 2 | 183 |
| 3--5 | 86 |
| 6--12 | 16 |
| 54 | 1 (T11n0310, *Ratnakūṭa* collection) |

The extreme case of T11n0310 (*Mahāratnakūṭa*, 大寶積經) mapping to 54 Tohoku
numbers reflects the fact that this Chinese collection gathers 49 individual
sūtras that are catalogued separately in the Tibetan Kangyur.

### 5.4 Source Agreement

Of 596 texts with Tohoku data from two or more independent sources:

| Agreement Level | Count | % |
|----------------|:---:|:---:|
| Full agreement (all sources give identical Toh sets) | 402 | 67.4% |
| Partial overlap (shared core, some sources list extra Tohs) | 180 | 30.2% |
| No overlap (sources give completely different Toh numbers) | 14 | 2.3% |

The 180 partial-overlap cases are almost all instances where more comprehensive
sources (CBETA Jinglu, Lancaster) list additional Tohoku numbers that narrower
sources (acmuller Tohoku index) omit. These are not disagreements but
differences in completeness.

The 14 apparent conflicts include several probable data entry errors:

| Taisho Text | Majority View | Outlier Source | Outlier Value | Likely Cause |
|-------------|:---:|---|:---:|---|
| T15n0586 | Toh 16 (5 sources) | CBETA Tibetan | Toh 160 | Trailing zero |
| T15n0650 | Toh 18 (5 sources) | CBETA Tibetan | Toh 180 | Trailing zero |
| T25n1518 | Toh 3908 (3 sources) | CBETA Tibetan | Toh 3809 | Digit transposition |
| T19n0945 | Toh 236 (5 sources) | rKTs | Toh 237 | Adjacent entry |
| T31n1612 | Toh 4059 (4 sources) | CBETA Sanskrit | Toh 4066 | Swap with T31n1613 |
| T31n1613 | Toh 4066 (4 sources) | CBETA Sanskrit | Toh 4059 | Swap with T31n1612 |

The T31n1612/T31n1613 case is the clearest genuine error: the CBETA Sanskrit
catalogue has the Tohoku numbers for these two Yogācāra treatises exactly
reversed compared to all other sources. The T15n0586/T15n0650 cases (Toh 16→160,
Toh 18→180) appear to be data entry errors in the CBETA Tibetan catalogue where
a trailing zero was accidentally appended.

These conflicts demonstrate the value of multi-source provenance tracking: by
comparing across sources, data entry errors that would be invisible in any
single source become detectable.

### 5.5 Expansion from Baseline

Comparing the expanded concordance against the initial baseline
(SuttaCentral + manual mappings only):

| Category | Baseline | Expanded | Delta |
|----------|:---:|:---:|:---:|
| Tibetan parallels | 722 | 733 | +11 |
| Pali parallels | 75 | 75 | 0 |
| Sanskrit parallels | 845 | 859 | +14 |
| Any parallel | 941 | 954 | +13 |

The modest expansion in text-level coverage reflects the fact that the baseline
already captured most texts with known parallels. The greater value of the
expansion lies in **depth**: many texts that already had one Tohoku number now
have additional Tohoku, Otani, and Nanjio numbers from the new sources, enabling
richer cross-referencing.

### 5.4 Illustrative Entry

A typical concordance entry, for the *Dīrghāgama* (T01n0001):

```json
"T01n0001": {
  "tibetan": ["Otani 1021", "Otani 750", "Otani 879", "Otani 962",
              "Otani 997", "Toh 287", "Toh 34", "Toh 352", "Toh 94"],
  "pali": ["DN"],
  "sanskrit": ["Dīrghāgama"],
  "sources": ["existing", "lancaster", "lancaster_full",
              "acmuller_tohoku", "cbeta_tibetan"]
}
```

This text maps to four Tohoku numbers and five Otani numbers -- reflecting the
fact that the *Dīrghāgama* (a collection of 30 sūtras) corresponds to multiple
individual texts in the Tibetan Kangyur, which catalogues sūtras individually
rather than in Āgama collections. Five sources independently contributed data
for this text.

## 6. Validation Against Digest Detection

### 6.1 Retranslation Validation

The concordance provides an independent check on the pipeline's retranslation
detection. If two Chinese texts are correctly identified as retranslations
(parallel translations from the same Indic source), they will often -- though
not always -- map to the same Tohoku number in the Tibetan Kangyur. The
correspondence is not guaranteed: the Tibetan canon has its own retranslation
tradition (*snga 'gyur* "old translation" vs. *phyi 'gyur* "new translation"),
and the same Indic source may have been translated into Tibetan multiple times,
with each translation receiving a separate Tohoku number. Two Chinese
retranslations could therefore legitimately map to different Tohoku numbers if
the Tibetan catalogue independently associates each with a different Tibetan
rendering of the same source. Nevertheless, a shared Tohoku number between two
Chinese texts constitutes strong independent evidence that they derive from
the same Indic original.

Of the 224 detected retranslation pairs:

| Tibetan Parallel Status | Count | % |
|------------------------|------:|----:|
| Shared Tibetan ID (validated) | 88 | 39.3% |
| Different Tibetan parallels | 6 | 2.7% |
| Only one text has Tibetan parallel | 71 | 31.7% |
| Neither text has Tibetan parallel | 59 | 26.3% |

**88 retranslation pairs (39.3%)** are independently confirmed by sharing at
least one Tohoku or Otani catalogue number. Among pairs where both texts have
Tibetan parallels, the validation rate is **93.6%**, strongly supporting the
pipeline's retranslation detection accuracy. The remaining 6.4% (6 pairs) have
different Tibetan parallels, but these are not necessarily errors in
either our pipeline or the catalogues -- they
represent cases where the same Indic source was translated into Tibetan more
than once (each translation receiving its own Tohoku number), where the Tibetan
canon catalogues closely related texts under different entries, or where
Chinese and Tibetan cataloguing traditions simply drew different boundaries
around overlapping textual traditions.

Notable validated retranslation pairs include:

| Digest | Source | Coverage | Shared Tibetan |
|--------|--------|--------:|---------------|
| T09n0262 (Lotus, Kumārajīva) | T09n0264 (Lotus, Jñānagupta) | 92.0% | Toh 113, Otani 781 |
| T16n0663 (Saṃdhinirmocana, Bodhiruci) | T16n0664 (Saṃdhinirmocana, Xuanzang) | 89.8% | Toh 555--557, Otani 174--176 |
| T12n0334 (Smaller Sukhāvatīvyūha) | T12n0335 (Smaller Sukhāvatīvyūha) | 89.2% | Toh 74 |
| T19n1013 (Uṣṇīṣavijayā Dhāraṇī) | T19n1015 (Uṣṇīṣavijayā Dhāraṇī) | 85.3% | Toh 140, 525, 914 |

### 6.2 The Heart Sutra Case

T250 (Heart Sutra, attributed to Kumārajīva) and T223 (Large Prajñāpāramitā,
Kumārajīva) share Toh 21 in the Tibetan canon. While classified as a digest
rather than a retranslation in our pipeline (due to extreme length asymmetry),
the shared Tohoku number confirms their common Indic ancestry through a
completely independent data source -- complementing the computational evidence
for Nattier's thesis.

### 6.3 Pairs with Different Tibetan Parallels

The 6 retranslation pairs with different Tibetan parallels are all from
Yogācāra or Prajñāpāramitā literature where catalogue boundaries are fluid:

| Pair | Digest Tibetan | Source Tibetan |
|------|:---:|:---:|
| T31n1605 / T31n1606 | Toh 4049 | Toh 4054 |
| T31n1597 / T31n1598 | Toh 4050 | Toh 4051 |
| T08n0227 / T08n0221 | Toh 12 | Toh 9 |
| T08n0226 / T08n0222 | Toh 12 | Toh 9 |
| T10n0286 / T26n1522 | Toh 44 | Toh 3993 |
| T08n0236a / T25n1510a | Toh 16 | Toh 3816 |

The Prajñāpāramitā cases (Toh 9 vs. Toh 12) are particularly illuminating:
these represent different *lengths* of the Prajñāpāramitā sūtra (8,000-verse
vs. 25,000-verse), which are distinct texts in the Tibetan catalogue but share
extensive content.

### 6.4 Concordance Coverage of Digest Relationships

Of the 1,558 unique texts involved in the 3,610 detected digest/excerpt/
retranslation/commentary/shared tradition relationships, a larger proportion
have cross-canon parallels than the corpus-wide average. This is expected: widely
transmitted Indic texts generate both retranslations and derivative works.

Texts involved in digest relationships that have Tibetan parallels are natural
candidates for comparative philological study, as the Tibetan version can help
disambiguate whether a Chinese relationship reflects direct textual derivation
or independent translation from a common source.

## 7. What Is Novel About This Concordance

### 7.1 Unified Multi-Source Merging

No previous project has programmatically merged the Lancaster catalogue,
SuttaCentral, CBETA Jinglu (both Tibetan and Sanskrit), the acmuller Tohoku
index, rKTs, and 84000 data into a single concordance. Each prior resource
existed as an independent silo, requiring researchers to manually consult
multiple sources.

### 7.2 Provenance Tracking

For each Taisho↔Tibetan mapping, the concordance records which sources assert
the correspondence. A mapping supported by four independent sources (e.g.,
Lancaster + CBETA Jinglu + acmuller + SuttaCentral) is more reliable than one
supported by a single source. No previous concordance provides this kind of
multi-source provenance.

### 7.3 Machine-Readable Format

The output (`results/cross_reference_expanded.json`) is a single JSON file
suitable for programmatic use -- direct import into Python, JavaScript, or any
language with JSON support. Previous concordances exist as print catalogues,
HTML pages, or proprietary CGI databases that require manual lookup or scraping.

### 7.4 Integration with Computational Text Analysis

The concordance was built specifically to validate and enrich the results of
computational digest detection. This integration -- using cross-canon data to
validate character-level text analysis -- is, to our knowledge, the first
application of a unified concordance for this purpose.

## 8. Limitations

### 8.1 Coverage Gaps

The concordance covers 38.9% of Taisho texts. The remaining 61.1% lack known
parallels in any of our eight sources. This does not necessarily mean these
texts have no parallels -- it may reflect gaps in the source databases,
particularly for:

- **Chan/Zen literature** (Taisho vols. 47--48): Largely Chinese-origin texts
  with few Tibetan or Pali parallels.
- **Chinese commentaries** (vols. 33--44): Indigenous Chinese works.
- **Tantric texts** (vols. 18--21): The Tibetan canon has extensive Tantric
  literature, but systematic Chinese↔Tibetan Tantric concordances are sparse.
- **Encyclopedic compilations** (vols. 51--54): Chinese compilations like the
  *Fayuan zhulin* (T2122) that aggregate material from many sources.

### 8.2 Accuracy of Source Data

The concordance inherits inaccuracies from its sources. Known issues include:

- **Lancaster**: Some traditional catalogue identifications have been questioned
  by modern scholarship. Lancaster relied on the Kaiyuan shijiao lu
  classifications, which are not always accurate.
- **CBETA Jinglu**: The web interface has occasional errors in Taisho number
  linking.
- **rKTs**: Coverage of Chinese cross-references is minimal (~23 entries).

### 8.3 One-to-Many Ambiguity

When a Taisho text maps to multiple Tohoku numbers, it is not always clear
whether these represent (a) different Tibetan translations of the same text,
(b) different sections of a larger work catalogued separately, or (c) errors in
the source data. The concordance records all mappings without attempting to
resolve this ambiguity.

### 8.4 Absence ≠ Negative Evidence

The absence of a parallel for a given Taisho text does **not** confirm that no
parallel exists. It means only that none of our eight sources identified one.
A text without a Tibetan parallel in the concordance may still have a Tibetan
translation that has not been catalogued, or may correspond to a Tibetan text
under a different title or section boundary.

## 9. Output Files

### 9.1 Primary Concordance

**`results/cross_reference_expanded.json`** -- The unified concordance (11,618
lines). Structure:

```json
{
  "summary": { "total_texts": 2455, "with_tibetan": 733, ... },
  "sources": { "lancaster_full": 1478, "cbeta_tibetan": 613, ... },
  "tibetan_parallels": { "T01n0001": ["Toh 34", "Toh 94", ...], ... },
  "pali_parallels": { "T01n0001": ["DN"], ... },
  "sanskrit_parallels": { "T01n0001": "Dīrghāgama", ... },
  "no_parallel_found": ["T01n0032", ...]
}
```

### 9.2 Cross-Reference Analysis

**`results/cross_reference_analysis.json`** -- Analysis of concordance data
against digest detection results. Includes retranslation validation, coverage
by classification type, and pair-level parallel status.

### 9.3 Intermediate Data Files

| File | Description | Size |
|------|-------------|------|
| `lancaster_taisho_crossref.json` | Initial Lancaster extraction | 129 KB |
| `lancaster_taisho_crossref.csv` | Tabular Lancaster data | 84 KB |
| `results/lancaster_full.json` | Full Lancaster K-number scrape | ~300 KB |
| `results/tohoku_taisho_crossref.json` | acmuller Tohoku→K→Taisho | ~129 KB |
| `results/cbeta_jinglu_tibetan.json` | CBETA Jinglu Tibetan | ~161 KB |
| `results/cbeta_jinglu_sanskrit.json` | CBETA Jinglu Sanskrit/Pali | ~150 KB |
| `results/rkts_taisho.json` | rKTs kernel cross-refs | ~5 KB |
| `results/84000_tohoku_extract.json` | 84000 TEI Tohoku extraction | ~80 KB |

### 9.4 Scripts

| Script | Purpose |
|--------|---------|
| `scripts/build_expanded_concordance.py` | Merges all sources into unified concordance |
| `scripts/cross_reference_analysis.py` | Analyzes concordance against digest results |
| `scripts/scrape_lancaster_full.py` | Scrapes full Lancaster K-number catalogue |
| `scripts/scrape_tohoku_index.py` | Scrapes acmuller Tohoku→K→Taisho index |
| `scripts/scrape_cbeta_jinglu_tibetan.py` | Scrapes CBETA Jinglu Tibetan pages |
| `scripts/scrape_cbeta_jinglu_sanskrit.py` | Scrapes CBETA Jinglu Sanskrit/Pali pages |
| `scripts/parse_rkts.py` | Parses rKTs XML data |
| `scripts/extract_84000_tohoku.py` | Extracts Tohoku data from 84000 TEI XML |

## 10. Future Directions

### 10.1 Expanding Coverage

The most direct path to increased coverage is incorporating additional data
sources:

- **Taishō shinshū daizōkyō editorial apparatus**: The Taisho edition itself
  contains cross-reference notes that have not been systematically digitized.
- **SAT linked data**: The SAT project at the University of Tokyo has been
  building linked data infrastructure that may include structured
  cross-references.
- **Dunhuang manuscript concordances**: The International Dunhuang Project has
  produced concordances between Dunhuang manuscripts and Taisho texts.
- **Tengyur expansion**: Our current Tibetan coverage focuses on the Kangyur
  (Toh 1--1108). Extending to the full Tengyur (Toh 1109--4569) would add
  commentary and śāstra correspondences.

### 10.2 Conflict Resolution

The current union strategy for merging sources could be refined with confidence
scoring based on source agreement. Mappings supported by multiple independent
sources would receive higher confidence than single-source mappings.

### 10.3 Community Contribution

Publishing the concordance as an open dataset, possibly integrated with existing
platforms like SuttaCentral or BDRC, would allow scholars to verify, correct,
and extend the mappings. The provenance tracking infrastructure is already in
place to support this.

---

## References

### Primary Catalogue Sources

- Lancaster, Lewis R., and Sung-bae Park. *The Korean Buddhist Canon: A
  Descriptive Catalogue*. Berkeley: University of California Press, 1979.
- Nanjio, Bunyiu. *A Catalogue of the Chinese Translation of the Buddhist
  Tripitaka*. Oxford: Clarendon Press, 1883.
- Ui Hakuju et al. *A Complete Catalogue of the Tibetan Buddhist Canons
  (Bkah-hgyur and Bstan-hgyur)*. Sendai: Tohoku University, 1934.
- Akanuma, Chizen. *The Comparative Catalogue of Chinese Āgamas and Pāli
  Nikāyas*. Nagoya: Hajinkaku shobo, 1929. Reprinted 1990.
- Hackett, Paul. *A Catalogue of the Comparative Kangyur*. AIBS/Columbia, 2013.
- Herrmann-Pfandt, Adelheid. *Die lHan kar ma: Ein früher Katalog der ins
  Tibetische übersetzten buddhistischen Texte*. Vienna: Verlag der
  österreichischen Akademie der Wissenschaften, 2008.

### Digital Resources

- 84000: Translating the Words of the Buddha. https://84000.co/
- CBETA Digital Database of Buddhist Tripitaka Catalogues. https://jinglu.cbeta.org/
- Lancaster Descriptive Catalogue (digitized by Charles Muller).
  http://www.acmuller.net/descriptive_catalogue/
- rKTs: Resources for Kanjur and Tanjur Studies. http://www.rkts.org/
- SuttaCentral. https://suttacentral.net/
