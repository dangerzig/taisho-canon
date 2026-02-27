# Literature Source Fetch Results

Date: 2026-02-26

## Summary

Four sources were investigated. Two are already fully integrated into the project
(Silk 2019 and Li 2021, under different names than "Harrison 2019"). Two are new
sources with potential concordance data (AIBS database, Vierth/Felbur/Meelen 2022
GitHub, Nehrdich 2025 MITRA). Details below.

---

## 1. "Harrison 2019" / Academia.edu Link

### Clarification: This is Silk 2019, not Harrison

The Academia.edu page at the URL provided
(https://www.academia.edu/40447816/Chinese_S%C5%ABtras_in_Tibetan_Translation_A_Preliminary_Survey)
is for:

> Silk, Jonathan A. "Chinese Sutras in Tibetan Translation: A Preliminary Survey."
> *Annual Report of the International Research Institute for Advanced Buddhology at
> Soka University* (ARIRIAB) 22 (2019): 227--246.

This is **not** by Paul Harrison. Harrison is at Stanford and works on related
topics, but the specific paper at this URL is by Jonathan Silk (Leiden). The
reference "Harrison 2019" in whatever source list prompted this query is likely
a misattribution.

### The Digital Himalaya PDF (ret_60_07.pdf)

The CloudFront PDF at
`https://d1i1jdw69xsqx0.cloudfront.net/digitalhimalaya/collections/journals/ret/pdf/ret_60_07.pdf`
is a **different paper**:

> Li, Channa. "A Survey of Tibetan Sutras Translated from Chinese, as Recorded
> in Early Tibetan Catalogues." *Revue d'Etudes Tibetaines* 60 (2021): 174--219.

This is the Li 2021 paper, not a Harrison paper.

### Accessibility

- **Silk 2019**: Available on Academia.edu but requires login/account to download
  the PDF. No open-access PDF was found. The ARIRIAB journal does not appear to
  have an open digital archive.
- **Li 2021**: Freely downloadable from Digital Himalaya at the CloudFront URL above.

### Already Integrated

**Both sources are already fully integrated into the project:**

- `data/silk2019_identifications.json` (32 entries + 4 unidentified)
- `data/li2021_identifications.json` (full table extraction)
- `data/scholarly_citations/silk2019.json` (18 Taisho-Tohoku links fed into concordance)
- `data/scholarly_citations/li2021.json` (15 links fed into concordance)

The expanded concordance (`results/cross_reference_expanded.json`) already shows
`"silk2019": 18` and `"li2021": 15` in its source counts.

### New Parallels from This Source

**Zero new parallels.** Already fully integrated.

---

## 2. AIBS Buddhist Canons Research Database

### URL

- About page: http://databases.aibs.columbia.edu/?sub=about
- Sample entry: http://databases.aibs.columbia.edu/?id=1d4e5eb91e5f691e177fedd0509a6c1a&enc=sanskrit_romanized_author&coll=tengyur

### Accessibility

The web interface is accessible (no login required for browsing). WebFetch was
blocked, so I could not inspect individual entry pages directly. Based on web
search results:

- The database covers ~5,000 texts in the Tibetan Buddhist canon (Kangyur + Tengyur)
- It provides bibliographic records with Tohoku numbers as the primary identifier
- It includes cross-links to "parallel e-texts in Sanskrit and Chinese"
- It links directly to CBETA and SAT (Taisho) online repositories
- ~600 inter-relations between primary texts and commentaries are documented

### Data Format

- Web-based interface only (HTML). No API, no bulk download, no JSON/CSV export
  was found in search results.
- The database uses Tohoku numbers as its primary catalog system
- Each entry appears to contain: Tohoku number, Tibetan title, Sanskrit title,
  author/translator, volume/folio location, and links to parallel texts

### Taisho Cross-References

The database does include links to Chinese parallel texts via CBETA/SAT, which
implies Taisho numbers are present for at least some entries. However:

- The cross-references appear to be presented as hyperlinks to CBETA/SAT, not as
  structured Taisho number fields in the database schema
- It is not clear whether the "Chinese parallel" information is systematically
  tagged or just present for a subset of texts
- There is no indication of bulk export capability

### Potential New Parallels

**Uncertain, likely low.** The AIBS database appears to draw on the same underlying
scholarly sources (Tohoku catalogue, Lancaster, etc.) that are already integrated
into our concordance. The ~5,000 Tibetan texts covered include Tengyur texts, which
may have some Chinese parallels not yet in our data. However, without the ability to
bulk-extract data, the value is limited to:

1. Manual spot-checking of individual entries (labor-intensive)
2. Validating existing concordance links (useful for corroboration)
3. Potentially finding Tengyur Chinese parallels (our focus is primarily Kangyur)

**Estimated new parallels: 0--20** (primarily Tengyur entries, if any). The effort
to extract them manually would be substantial since there is no API.

---

## 3. Vierth/Felbur/Meelen 2022 GitHub Repository

### Clarification on Authorship

The correct citation is:

> Felbur, Rafal, Marieke Meelen, and Paul Vierthaler. "Crosslinguistic Semantic
> Textual Similarity of Buddhist Chinese and Classical Tibetan." *Journal of Open
> Humanities Data* 8, article 23 (2022). DOI: 10.5334/johd.86

(Not "Vierth/Meelen/Hill 2022" as stated in the query. The third author is Paul
Vierthaler, not Hill.)

### URLs

- GitHub: https://github.com/vierth/buddhist_chinese_classical_tibetan
- Paper: https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.86
- Zenodo data: https://zenodo.org/records/6782150 (MRK Alignment Scoring Guidelines)
- Zenodo embeddings: https://zenodo.org/records/6782247 (Classical Tibetan Word Embeddings)
- Zenodo embeddings: https://zenodo.org/records/6782932 (Buddhist Chinese Word Embeddings)

### Accessibility

- The GitHub repository is public and accessible
- WebFetch was blocked, so I could not directly inspect the repository contents
- The paper is open-access in JOHD

### Data Format

The repository contains:
- `embedding_pipeline.py` (code for building cross-lingual embeddings)
- Word embeddings for Buddhist Chinese (from Kanseki/CBETA/Taisho) and Classical
  Tibetan (from BDRC eKangyur/eTengyur)
- Alignment code for unsupervised sentence/paragraph-level similarity detection

### Scope and Text Coverage

The pilot study focuses on texts in the **Maharatnakuta** (MRK) collection:

- The Maharatnakuta contains 49 sutras, preserved in both Chinese (T310 + T311--T373)
  and Tibetan canons
- The study creates a bibliographic database of all 49 texts with cross-references
- The alignment is at the **sentence/paragraph level** (semantic similarity), not
  at the document-level concordance level

### Taisho-to-Tohoku Mappings

The Maharatnakuta collection provides an implicit concordance: the 49 sub-texts of
T310 map to specific Tohoku numbers (Toh 45--93 approximately). However:

- The Silk 2019 data already integrated into our concordance covers the 10
  Maharatnakuta chapters translated from Chinese (T310(7)=Toh 51, T310(13)=Toh 58,
  T310(14)=Toh 57, T310(17)=Toh 61, T310(20)=Toh 64, T310(40)=Toh 84, etc.)
- The remaining ~39 Maharatnakuta chapters were translated from Sanskrit, not
  Chinese, so they would not represent "Chinese sutras in Tibetan translation"
  parallels in the Silk/Li sense; rather they are standard Sanskrit-origin
  Kangyur texts with Taisho parallels
- Many of these T310(N) to Toh N mappings are likely already captured by our
  existing sources (84000 TEI, rKTs, Lancaster, CBETA)

### Potential New Parallels

**Low incremental value for concordance.** The repository's primary contribution is
*alignment quality* (sentence-level embeddings), not new document-level concordance
data. The Maharatnakuta T310-to-Kangyur mappings are well-known and likely already
in our data.

**Estimated new parallels: 0--5** (any unmapped Maharatnakuta sub-text chapters
that happen to be missing from our current sources). The project could be valuable
as a *validation* source for alignment quality, but not for new Taisho-Tohoku links.

Worth investigating: clone the repo and check whether `embedding_pipeline.py` or
any data files contain an explicit text-pair list with T### and Toh### identifiers
that could be compared against our concordance.

---

## 4. Nehrdich 2025 MITRA Paper (arXiv 2601.06400)

### Citation

> Nehrdich, Sebastian, et al. "MITRA: A Large-Scale Parallel Corpus and
> Multilingual Pretrained Language Model for Machine Translation and Semantic
> Retrieval for Pali, Sanskrit, Buddhist Chinese, and Tibetan." arXiv preprint
> 2601.06400 (2025).

### URLs

- Paper: https://arxiv.org/abs/2601.06400
- HTML version: https://arxiv.org/html/2601.06400
- GitHub (aligner): https://github.com/dharmamitra/mitra-aligner
- Dataset (referenced): https://github.com/dharmamitra/mitra-parallel
- Online interface: https://dharmanexus.org

### Accessibility

- The paper is freely available on arXiv
- The dataset is referenced as being available at
  `github.com/dharmamitra/mitra-parallel`, but this specific repository was not
  directly found in search results (the dharmamitra GitHub organization exists with
  related repos)
- The `mitra-aligner` repository is public (bertalign-based Buddhist text aligner)
- DharmaNexus provides an online searchable interface

### Data Format

- **1.74 million parallel sentence pairs** across Sanskrit, Chinese, and Tibetan
- Sentence-level alignments, not document-level concordance
- The parallel mining pipeline operates at the sentence level using semantic
  embeddings

### Taisho-to-Tohoku Mappings

**Critical distinction**: MITRA's primary output is *sentence-level parallel pairs*,
not document-level concordance. The document-level pairing (which Taisho texts
correspond to which Kangyur texts) is a *prerequisite* for their sentence alignment
pipeline, not an output.

From the search results, the MITRA corpus uses:
- Chinese texts from the Taisho canon (via CBETA/SAT)
- Tibetan texts from the Kangyur and Tengyur (via eKangyur/eTengyur)
- The document-level pairing metadata likely comes from existing sources (rKTs,
  SuttaCentral, 84000, or similar)

**The key question is whether the MITRA dataset includes an explicit
document-level concordance file** listing which T### texts were aligned to which
Toh### texts. Based on search results alone, this is unclear. The arXiv HTML
version and the mitra-parallel GitHub repo would need to be inspected directly.

### Potential New Parallels

**Potentially moderate.** If MITRA's document-level pairing metadata is available
and uses a broader set of pairings than our current 9 sources, it could contribute
new links. However:

1. MITRA likely uses the same upstream sources (rKTs, 84000, SuttaCentral) that
   we already integrate
2. The sentence-level alignment data could be valuable for *validating* existing
   concordance links (texts that share many aligned sentences are confirmed parallels)
3. Any novel pairings discovered through MITRA's mining process (previously unknown
   parallel passages) could theoretically yield new concordance links

**Estimated new parallels: 0--50** depending on whether novel document-level
pairings emerge from the sentence mining process. The most likely scenario is 0--10
genuinely new Taisho-Tohoku links, since the upstream concordance sources overlap
with ours.

**Recommended action**: Clone `dharmamitra/mitra-parallel` (or check if it exists)
and inspect for a document-level concordance file. Also check `dharmanexus.org`
for browsable cross-references.

---

## Overall Assessment

| Source | Accessible? | Format | Taisho-Tohoku? | Estimated New Parallels |
|--------|------------|--------|----------------|------------------------|
| Silk 2019 (= "Harrison 2019") | Academia.edu (login req.) | PDF | Yes (31 texts) | 0 (already integrated) |
| Li 2021 (ret_60_07.pdf) | Open PDF | PDF | Yes (36+ entries) | 0 (already integrated) |
| AIBS Database | Web only, no API | HTML | Partial (links to CBETA) | 0--20 (manual extraction) |
| Vierth et al. 2022 GitHub | Public repo | Python + embeddings | Implicit (MRK collection) | 0--5 |
| Nehrdich 2025 MITRA | arXiv + GitHub | Sentence pairs | Possibly (document metadata) | 0--50 |

### Priority Actions

1. **MITRA dataset** (highest potential): Attempt to access
   `github.com/dharmamitra/mitra-parallel` and inspect for a document-level
   concordance file. Also check the arXiv HTML version for appendices or tables
   listing text pairs.

2. **Vierth et al. GitHub** (quick check): Clone
   `github.com/vierth/buddhist_chinese_classical_tibetan` and look for any data
   files listing Maharatnakuta text pairs with catalog numbers.

3. **DharmaNexus** (validation): Browse https://dharmanexus.org to check whether
   it offers Chinese-Tibetan cross-references in a structured format.

4. **AIBS Database** (low priority): Manual spot-checking only, given the lack of
   API access. Could be useful for validating specific disputed links.

### Note on "Harrison 2019"

The reference "Harrison 2019" appears to be a misattribution. The paper at the
provided Academia.edu URL is by Jonathan Silk, published in ARIRIAB 22 (2019).
Paul Harrison (Stanford) does not appear to have published a paper with this exact
title in 2019. If there is a separate Harrison paper intended, additional
bibliographic details would be needed to locate it.
