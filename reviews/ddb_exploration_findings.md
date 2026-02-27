# DDB (Digital Dictionary of Buddhism) Data Exploration Findings

## Date: 2026-02-26

## Overview

Explored the Digital Dictionary of Buddhism (DDB) at buddhism-dict.net to
extract Taisho-to-Tohoku cross-references. The DDB contains over 73,000
entries including text entries that are documented as storing both Taisho
(T.####) and Tohoku (To.####) numbers.

## Key Findings

### 1. DDB Site Architecture

The DDB has several publicly accessible index pages:

- **Taisho / SAT Availability Table** (`indexes/taisho-ddb.html`)
  - 2,876 Taisho text entries (T1 through T2920)
  - Maps Chinese text titles to T numbers
  - Links to SAT online text database
  - 1,048 entries with DDB "blue links" (full DDB entries)
  - Updated 2018-10-11
  - **Does NOT contain Tohoku numbers**

- **Tibetan Texts Index** (`indexes/text-bo.html`)
  - 199 entries (page header says 214; some are navigation elements)
  - Maps Tibetan text titles (in Wylie) to Chinese text titles via DDB links
  - Updated 2019-01-03
  - **Does NOT contain Taisho or Tohoku numbers directly**

- **Sanskrit Texts Index** (`indexes/text-sa.html`)
  - 742 entries mapping Sanskrit titles to Chinese text titles
  - Updated 2015-08-04
  - **No T or To numbers**

- **English Text Titles Index**, **Japanese Texts Index**, etc.
  - Similar format, no canon numbers

### 2. Authentication Requirements

Individual DDB entries require authentication:
- **Guest access**: username "guest", no password, 20 searches per day
- **Unlimited access**: requires content contribution (1 A4 page of entry
  material) or institutional subscription ($300/year) or individual payment
- The Wayback Machine archived copies of individual entries return 401
  Unauthorized

### 3. DDB Entry XML Structure

Based on the DDB TEI paper (2010), individual text entries have this structure:
- `<entry>` with `<hdwd>` (Chinese headword)
- `<pron_list>` (pronunciations in Chinese, Korean, Japanese)
- `<sense_area>` with `<trans>` and `<sense>` nodes
- `<dictrefs>` / `<dictref>` area for cross-references to other dictionaries
- Canon references use `<xref canonref="...">T 262.9.9a13</xref>` format
- The Tohoku numbers (To.####) are stored **inside individual entries**, not
  on any public index page

### 4. Cross-Reference Extraction Results

By cross-referencing the Taisho table (Chinese titles to T numbers) with the
Tibetan texts index (Tibetan titles to Chinese titles), we extracted:

- **158 cross-referenced pairs** (Taisho text with Tibetan title)
- **154 unique Taisho texts** matched
- **47 unmatched** Tibetan entries (titles not found in Taisho table)
- Match methods: 152 by title, 6 by substring

Comparing with the existing concordance (838 Taisho texts with Tibetan parallels):
- **143 overlap** with existing concordance (providing DDB as additional source)
- **11 new** texts not previously in our concordance

### 5. Why Tohoku Numbers Are Inaccessible

The DDB's Taisho table is a flat HTML table with three columns:
1. Text Name(s) (Chinese, with DDB/K-canon links)
2. Taisho Number (with SAT link)
3. Modern Translations (Bingenheimer bibliography link)

There is no Tohoku column. The DDB stores Tohoku numbers inside individual
entry pages, which are behind authentication. The Tibetan Texts Index similarly
links to entry pages (not directly to T or To numbers).

To extract Tohoku numbers from the DDB, one would need to:
1. Obtain DDB credentials (guest or registered)
2. For each of the ~1,048 DDB text entries with blue links, query the
   individual entry page
3. Parse the entry XML/HTML for Tohoku references
4. Rate-limit appropriately (guest: 20/day; registered: unlimited but
   polite delays needed)

### 6. Related Resources at acmuller.net

- Lancaster's Descriptive Catalogue (already scraped: `scrape_lancaster_full.py`)
  provides much richer cross-reference data including T, K, To, Nj, O numbers
- The CJKV-English Dictionary (separate from DDB) has no canon cross-references
- No additional structured concordance data found beyond what we already use

## Output Files

- **Script**: `/Users/danzigmond/taisho-canon/scripts/scrape_ddb.py`
- **Results**: `/Users/danzigmond/taisho-canon/results/ddb_taisho_tibetan.json`

## Recommendations

1. The 11 new Taisho-Tibetan correspondences should be reviewed manually
   before integrating into the concordance, since they come from title
   matching only (no Tohoku numbers to validate against).

2. To get actual Tohoku numbers from DDB, consider contacting A. Charles
   Muller directly (ddbcjkvedictionary@gmail.com) to request the
   cross-reference data. An academic data-sharing request would be more
   respectful and efficient than automated scraping of authenticated pages.

3. The DDB's value for our project is primarily as a corroborating source
   (143 existing concordance entries confirmed) rather than a source of new
   cross-references. The Lancaster catalogue and CBETA jinglu already provide
   far more comprehensive Taisho-Tohoku cross-reference coverage.
