# Literature Search: Chinese-Tibetan Buddhist Canon Concordance Scholarship

Date: 2026-02-26

## Purpose

Comprehensive survey of published scholarship that systematically identifies Chinese-Tibetan textual parallels (Taisho-Tohoku concordances), to identify new data sources for incorporation into the taisho-canon concordance project.

## Already Incorporated Sources (NOT new findings)

The project already uses data from:
- Lancaster & Park 1979 (Korean Buddhist Canon catalog)
- Ui et al. 1934 (Tohoku catalog)
- Nanjio 1883
- Li Channa 2021 (translations from Chinese in the Kangyur)
- Silk, Jonathan A. 2019 (Chinese Sutras in Tibetan Translation)
- SuttaCentral, CBETA jinglu, rKTs, 84000 TEI, Muller DDB, Sanskrit title matching

---

## NEW FINDINGS

### 1. HIGH PRIORITY: Harrison 2019 (or earlier) - "Chinese Sutras in Tibetan Translation: A Preliminary Survey"

- **Author**: Paul Harrison (Stanford University, formerly U. Canterbury)
- **Title**: "Chinese Sutras in Tibetan Translation: A Preliminary Survey"
- **Publication**: Appears to be published in ARIRIAB (Annual Report of the International Research Institute for Advanced Buddhology at Soka University), possibly same year or earlier than Silk 2019
- **Content**: Preliminary survey of Chinese sutras that appear in Tibetan translation within the Kangyur. Harrison is one of the foremost scholars of Kangyur stemma and textual history.
- **Parallels identified**: Not fully determined from web search alone, but the paper identifies specific Taisho-to-Kangyur correspondences. Li 2021 and Silk 2019 both cite Harrison's work, so there may be overlap, but Harrison may contain additional identifications or corrections.
- **Data availability**: PDF available on Academia.edu: https://www.academia.edu/40447816/
- **Already used?**: Not directly incorporated. Li 2021 and Silk 2019 cite Harrison, so some data may be indirectly present, but Harrison's own identifications should be checked for any additional links.
- **Action**: Download and extract any Taisho-Tohoku links not already in li2021.json or silk2019.json.

### 2. HIGH PRIORITY: MITRA-parallel (Nehrdich et al. 2025)

- **Authors**: Sebastian Nehrdich and collaborators (University of Hamburg / Khyentse Center for Tibetan Buddhist Textual Scholarship)
- **Title**: "MITRA: A Large-Scale Parallel Corpus and Multilingual Pretrained Language Model for Machine Translation and Semantic Retrieval for Pali, Sanskrit, Buddhist Chinese, and Tibetan"
- **Publication**: arXiv:2601.06400 (January 2025)
- **Content**: Novel pipeline for multilingual parallel passage mining. Created **1,742,786 parallel sentence pairs** between Sanskrit, Chinese, and Tibetan. For Chinese-Tibetan specifically, this is **the first large-scale dedicated digital parallel dataset**.
- **Parallels identified**: The dataset contains sentence-level alignments, not document-level concordances. However, the underlying document-level mapping (which Taisho texts are aligned to which Kangyur texts) would be extremely valuable as a data source.
- **Data availability**: YES. GitHub: https://github.com/dharmamitra/mitra-parallel. Also searchable via https://dharmanexus.org (DharmaNexus).
- **Already used?**: NO
- **Action**: Clone the mitra-parallel repository. Extract the document-level metadata showing which Taisho texts have sentence-level alignments with which Kangyur/Tohoku texts. This could potentially yield hundreds of new concordance links with computational evidence.

### 3. HIGH PRIORITY: DharmaNexus / Dharmamitra (Nehrdich, ongoing)

- **Author**: Sebastian Nehrdich et al.
- **Title**: DharmaNexus: Interactive database for Buddhist parallel text detection
- **URL**: https://dharmamitra.org/nexus (also https://dharmanexus.org)
- **Content**: Multilingual text database finding intertextual connections within and between texts in Pali, Sanskrit, Chinese, and Tibetan. Uses "modernized algorithms that combine multilingual matching with deep semantic similarity from Gemma 2 MITRA-E."
- **Parallels identified**: The system identifies cross-canonical parallels computationally. The Chinese corpus is from CBETA (Taisho), and the Tibetan corpus includes the Kangyur (from ACIP and Tsadra Foundation's Dharma Cloud).
- **Data availability**: Web interface is searchable. Underlying data may be available through the dharmamitra GitHub organization: https://github.com/dharmamitra
- **Already used?**: NO
- **Action**: Query DharmaNexus systematically to extract Chinese-Tibetan document-level parallel identifications. This is the most advanced computational tool currently available for this task.

### 4. MEDIUM PRIORITY: Vierth, Meelen, Hill 2022 - Cross-linguistic STS

- **Authors**: Bryan Vierth, Marieke Meelen, Nathan W. Hill (Cambridge University)
- **Title**: "Crosslinguistic Semantic Textual Similarity of Buddhist Chinese and Classical Tibetan"
- **Publication**: Journal of Open Humanities Data (2022). DOI: 10.5334/johd.86
- **Content**: First-ever procedure for identifying highly similar sequences of text in Chinese and Tibetan translations of Buddhist sutra literature, using cross-lingual embedding space.
- **Parallels identified**: Pilot study with three Chinese sutras from the Maharatnakuta (MRK) collection manually divided into sections and aligned with Tibetan. This is a methodological proof-of-concept rather than a large-scale concordance.
- **Data availability**: YES. GitHub: https://github.com/vierth/buddhist_chinese_classical_tibetan
- **Already used?**: NO
- **Action**: Low priority for direct concordance data (small pilot), but the methodology and any text-level identifications should be reviewed. The MITRA project (above) supersedes this work at scale.

### 5. MEDIUM PRIORITY: Li Channa 2021 - Additional data beyond what's extracted

- The project already has `li2021.json` with 25 links, but Li 2021 contains:
  - **Table 1**: 36 entries (some without Taisho numbers)
  - **Appendix I**: 21 entries (texts in Kanjur catalogued as "from Chinese" but NOT confirmed)
  - **Appendix II**: 29 entries (additional texts with Chinese connections)
  - Footnotes with additional identifications
- The `li2021_identifications.json` file appears to have more data than `li2021.json` in the scholarly_citations folder.
- **Action**: Verify that ALL identifications from Li 2021 (Table 1, Appendixes I and II, footnotes) are fully incorporated. Some may be tentative or lack Taisho numbers, but those with both Taisho and Tohoku should be included.

### 6. MEDIUM PRIORITY: ICABS Taisho Canon Concordance Series

- **Institution**: International College for Postgraduate Buddhist Studies (ICABS), Tokyo
- **Publications**:
  - **Series I** (2004): A Concordance to the Taisho Canon and the Zhonghua Canon (Beijing Edition)
  - **Series II** (2006, 2015): A Concordance to the Taisho Canon and Dunhuang Buddhist Manuscripts (edited by Sueki Fumihiko)
  - **Series III** (date unclear): A Concordance to the Taisho Canon and Nine Other Buddhist Canons: Preliminary Edition
- **Content**: Series III is the most relevant. It covers "Buddhist Sanskrit texts and various editions of the Chinese Tripitaka and their Japanese versions; important Tibetan editions of Kanjur and/or Tanjur; single editions of the Pali Tipitaka; and Mongolian Kanjur."
- **Parallels identified**: Potentially comprehensive Taisho-to-Kangyur/Tengyur concordance, but scope unclear from web searches alone.
- **Data availability**: Published as print volumes. NOT available digitally (as far as can be determined).
- **Already used?**: NO
- **Action**: Obtain access to Series III. If it contains systematic Taisho-Tohoku concordance data, this could be one of the most comprehensive sources available. The ICABS library page is at https://www.icabs.ac.jp/en/library/publication

### 7. MEDIUM PRIORITY: Hackett 2012 - Catalogue of the Comparative Kangyur

- **Author**: Paul G. Hackett
- **Title**: A Catalogue of the Comparative Kangyur (bka' 'gyur dpe bsdur ma)
- **Publication**: 2012, AIBS / Columbia University Center for Buddhist Studies / Tibet House US (Treasury of the Buddhist Sciences series)
- **Content**: Detailed cataloging of the Comparative (dpe bsdur ma) Kangyur with concordance tables aligning catalog numbers between various recensions (including Derge, Narthang, Peking, Cone, Lhasa, Urga, Phudrak, Litang). Includes indices to Tibetan and Sanskrit titles.
- **Parallels identified**: Primarily a within-Kangyur concordance (aligning different Kangyur editions), but may include Chinese cross-references.
- **Data availability**: Published as a print volume. NOT available digitally.
- **Already used?**: NO
- **Action**: Check whether this catalogue includes Taisho cross-references. If so, it would be valuable. The within-Kangyur concordance data is less directly useful but could help validate Tohoku number assignments.

### 8. MEDIUM PRIORITY: AIBS Buddhist Canons Research Database

- **Institution**: American Institute of Buddhist Studies (AIBS) / Columbia University
- **URL**: http://databases.aibs.columbia.edu/
- **Content**: "Complete bibliographic information (with internal crosslinks and links to external resources) for the roughly 5,000 texts contained in the Tibetan Buddhist canon." Launched 2010.
- **Parallels identified**: Unknown from web search, but the database may contain Chinese cross-references for Kangyur/Tengyur texts.
- **Data availability**: Online searchable database, but unclear whether data can be exported or scraped systematically.
- **Already used?**: NO
- **Action**: Investigate whether this database contains Taisho cross-references. If so, systematically extract them. The database covers ~5,000 texts.

### 9. MEDIUM PRIORITY: Analayo & Bucknell - Correspondence Table for Agama Parallels

- **Authors**: Bhikkhu Analayo and Roderick S. Bucknell
- **Title**: "Correspondence Table for Parallels to the Discourses of the Majjhima Nikaya: Toward a Revision of Akanuma's Comparative Catalogue"
- **Publication**: Published in academic journal (date unclear from search, likely 2000s-2010s)
- **Content**: Systematic concordance of Majjhima-nikaya discourses with their parallels in Chinese Agamas, Sanskrit fragments, and Tibetan texts. Uses Taisho serial numbers (T followed by number).
- **Parallels identified**: Covers primarily Agama/Nikaya parallels. The Tibetan column may contain Tohoku numbers for any Tibetan parallels.
- **Data availability**: PDF available from University of Hamburg: https://www.buddhismuskunde.uni-hamburg.de/pdf/5-personen/analayo/correspondence-table.pdf
- **Already used?**: NO (SuttaCentral may partially incorporate this data)
- **Action**: Download the PDF and check whether it contains Chinese-Tibetan parallels (Taisho-Tohoku links). Most Agama material has limited Tibetan parallels, but any that exist would be valuable.

### 10. MEDIUM PRIORITY: Analayo - Comparative Study of the Majjhima-nikaya (2011)

- **Author**: Bhikkhu Analayo
- **Title**: A Comparative Study of the Majjhima-nikaya (2 volumes)
- **Publication**: 2011 (habilitation thesis, University of Marburg, 2007)
- **Content**: Systematic sutta-by-sutta comparison of all 152 Majjhima-nikaya discourses with parallels in Chinese Agamas, Sanskrit fragments, AND Tibetan texts. Goes through every discourse identifying parallels.
- **Parallels identified**: Potentially significant for Agama-class texts that have Tibetan parallels.
- **Data availability**: PDF of Vol. 1 available at http://wiswo.org/books/
- **Already used?**: NO (SuttaCentral may partially incorporate this data)
- **Action**: Review for any Taisho-Tohoku links involving Chinese Agamas with Tibetan Kangyur parallels.

### 11. LOWER PRIORITY: Skilling 1994-1997 - Mahasutras

- **Author**: Peter Skilling
- **Title**: Mahasutras: Great Discourses of the Buddha (2 volumes)
- **Publication**: Pali Text Society, 1994-1997
- **Content**: Critical editions of 10 Tibetan Mahasutras with Pali and Sanskrit counterparts. Charts of variations across Buddhist textual lineages (pp. 54-61). Complete list of Mahasutras translated into Tibetan (p. 12).
- **Parallels identified**: Limited scope (10 texts), and focuses on Tibetan-Pali-Sanskrit, not Chinese specifically. However, Chinese parallels may be mentioned.
- **Data availability**: Print volumes only.
- **Already used?**: NO
- **Action**: Low priority. Check whether any Chinese (Taisho) cross-references are included for the 10 Mahasutras.

### 12. LOWER PRIORITY: Bibliotheca Polyglotta / Thesaurus Litteraturae Buddhicae (Oslo)

- **Author/Institution**: Jens Braarvig, University of Oslo
- **URL**: https://www2.hf.uio.no/polyglotta/
- **Content**: Multilingual presentation of Buddhist literature sentence by sentence in Sanskrit, Chinese, Tibetan, English. Texts presented in synoptic format. Contains major texts from the Buddhist canon.
- **Parallels identified**: Unknown count, but texts are presented with cross-linguistic parallel alignments.
- **Data availability**: Online searchable database.
- **Already used?**: NO
- **Action**: Low priority for concordance building. The texts are aligned at sentence level, not catalogued as document-level concordances.

### 13. LOWER PRIORITY: Akanuma 1929 - Comparative Catalogue of Chinese Agamas and Pali Nikayas

- **Author**: Akanuma Chizen
- **Title**: The Comparative Catalogue of Chinese Agamas and Pali Nikayas
- **Publication**: Nagoya, 1929 (reprinted 1958, 1990)
- **Content**: Foundational concordance of Chinese Agamas with Pali Nikayas.
- **Parallels identified**: Primarily Pali-Chinese. May contain occasional Tibetan references.
- **Data availability**: Partially incorporated into SuttaCentral's parallel data.
- **Already used?**: Indirectly via SuttaCentral.
- **Action**: Very low priority. Primarily Pali-Chinese, not Chinese-Tibetan.

### 14. LOWER PRIORITY: Brill Concordance A & B (Taisho/Tohoku Reference)

- A Brill publication includes back-matter concordance tables mapping Taisho reference numbers to Tohoku reference numbers.
- **URL**: https://brill.com/display/book/9789004598560/back-1.xml
- **Content**: A concordance table in the back matter of a Brill book (ISBN 9789004598560).
- **Data availability**: Behind Brill paywall.
- **Already used?**: NO
- **Action**: Identify which Brill publication this is (likely an encyclopedia or handbook of Buddhism) and check whether it contains new parallels not in other sources.

### 15. LOWER PRIORITY: Otani University Peking Tripitaka concordance

- **Institution**: Otani University, Shin Buddhist Comprehensive Research Institute
- **URL**: https://web.otani.ac.jp/cri/twrpe/peking/
- **Content**: Concordance of numbers for Peking, Derge, and Golden Manuscript editions of the Tibetan canon. Based on comparative analytical catalogues published 1930-1997.
- **Parallels identified**: Within-Kangyur concordance (Peking-Derge-Golden Manuscript), not Chinese cross-references.
- **Data availability**: Online database.
- **Already used?**: Indirectly (rKTs includes Peking/Derge concordance data).
- **Action**: Very low priority for Chinese-Tibetan concordance specifically.

### 16. LOWER PRIORITY: Kanakura et al. 1953 - Catalogue of the Tohoku University Collection

- **Authors**: Yensho Kanakura, Ryujo Yamada, Tokan Tada, Hakuyu Hadano
- **Title**: A Catalogue of the Tohoku University Collection of Tibetan Works on Buddhism
- **Publication**: Sendai, 1953
- **Content**: Bilingual Japanese-English catalogue of Tibetan Buddhist works. Successor to the 1934 Ui et al. catalogue. Provides Tibetan titles, transliterations, and Japanese/English translations.
- **Data availability**: Print volume only.
- **Already used?**: Partially, via Tohoku numbers already in the system.
- **Action**: Low priority. May contain Chinese cross-references not in the 1934 edition.

### 17. INFORMATIONAL: Bingenheimer - Shorter Chinese Samyuktagama Digital Edition

- **Author**: Marcus Bingenheimer
- **Content**: TEI edition of T.100 (Bieyi za ahan jing) with all Chinese, Pali, Sanskrit, and Tibetan parallels aligned.
- **Data availability**: Digital (TEI XML).
- **Already used?**: Partially via SuttaCentral.
- **Action**: Very low priority. Covers one text (T.100) thoroughly.

### 18. INFORMATIONAL: SansTib Corpus (Nehrdich 2022)

- **Author**: Sebastian Nehrdich
- **Title**: "SansTib, a Sanskrit-Tibetan Parallel Corpus and Bilingual Sentence Embedding Model"
- **Publication**: LREC 2022
- **Content**: 317,289 automatically aligned Sanskrit-Tibetan sentence pairs. Now superseded by MITRA (see item 2 above).
- **Already used?**: NO, but MITRA supersedes it.

---

## DIGITAL PROJECTS AND TOOLS (not direct data sources, but relevant)

### A. Michael Radich - TACL and CBC@ (dazangthings.nz)

- TACL: Python tool for detecting parallel passages within the Chinese Buddhist canon (intra-Chinese, not Chinese-Tibetan).
- CBC@: Chinese Buddhist Canonical Attributions database, indexing evidence for attribution and dating of Chinese Buddhist texts.
- NOT directly relevant for Chinese-Tibetan concordance, but useful for text identification.

### B. SAT Daizokyo Text Database (University of Tokyo)

- URL: https://21dzk.l.u-tokyo.ac.jp/SAT/index_en.html
- Contains full-text searchable Taisho, with links to DDB and BDK translations. Plans to extend Tibetan cross-referencing.
- Not currently a source of systematic Taisho-Tohoku concordance data.

### C. BDRC (Buddhist Digital Resource Center)

- World's largest online archive of Tibetan/Buddhist texts.
- Entry for the Taisho Tripitaka at https://library.bdrc.io/show/bdr:MW0TTT0542 reportedly "gives parallels between the Tibetan canon and the Taisho."
- **Action**: Check whether BDRC's Taisho entry contains structured parallel data that could be extracted.

---

## SUMMARY OF RECOMMENDED ACTIONS (by priority)

### Immediate (high-value, digitally available)

1. **MITRA-parallel dataset** (Nehrdich 2025): Clone https://github.com/dharmamitra/mitra-parallel and extract document-level Chinese-Tibetan concordance metadata. This is likely the single largest new source of parallel identifications.

2. **DharmaNexus** (Nehrdich, ongoing): Query the web interface at https://dharmamitra.org/nexus systematically for Chinese-Tibetan document-level parallels.

3. **Harrison 2019**: Download from Academia.edu and extract any Taisho-Tohoku links not already in Li 2021 or Silk 2019.

4. **BDRC Taisho entry**: Check https://library.bdrc.io/show/bdr:MW0TTT0542 for structured parallel data.

### Near-term (require library access or careful extraction)

5. **ICABS Series III** (Concordance to the Taisho Canon and Nine Other Buddhist Canons): Obtain and check for Taisho-Tibetan concordance data.

6. **AIBS Buddhist Canons Research Database**: Investigate for Chinese cross-references at http://databases.aibs.columbia.edu/

7. **Analayo & Bucknell correspondence table**: Download PDF and check for Chinese-Tibetan parallels.

8. **Brill Concordance tables**: Identify the book (ISBN 9789004598560) and check content.

### Lower priority (partial overlap with existing sources or limited scope)

9. **Li 2021 completeness check**: Verify all Appendix I and II entries are incorporated.
10. **Hackett 2012**: Check for Chinese cross-references in the Comparative Kangyur catalogue.
11. **Skilling 1994-1997**: Check for Chinese cross-references in Mahasutras volumes.
12. **Analayo 2011**: Review for Agama-class Chinese-Tibetan parallels.

---

## ESTIMATED NEW PARALLELS

- **MITRA-parallel**: Potentially hundreds of new document-level Chinese-Tibetan correspondences (the dataset contains 1.74M sentence pairs; the number of distinct Taisho-to-Kangyur document pairs is unknown but likely substantial).
- **Harrison 2019**: Likely 0-10 new links beyond Li/Silk (since they cite Harrison).
- **ICABS Series III**: Potentially comprehensive, but scope unknown.
- **AIBS database**: Potentially significant, but scope unknown.
- **Others**: Likely small incremental additions (0-5 links each).

The MITRA-parallel dataset and DharmaNexus represent the most promising sources for large-scale new data. The ICABS Series III, if it proves to contain systematic Taisho-Tibetan concordance data, could also be transformative.
