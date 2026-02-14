# Computational Detection of Digest Relationships in the Taisho Canon

## Findings from an Automated Five-Stage Pipeline Analysis

---

## 1. Executive Summary

We developed and ran a fully automated computational pipeline to detect **digest relationships** across the entire Taisho Tripitaka (Taisho shinshu daizokyo), the standard modern edition of the Chinese Buddhist canon containing approximately 2,920 texts across 85 volumes. A "digest" in this context is a shorter text whose content is substantially derived from a longer source text -- whether through abridgment, extraction, selective quotation, or compilation.

The pipeline analyzed all 8,982 XML files in the CBETA TEI P5b corpus and detected **2,812 significant textual relationships** involving **1,412 unique texts**. These were classified into five categories:

| Classification | Count | Description |
|----------------|------:|-------------|
| Full Digests | 181 | Shorter text draws >70% of its content from a longer source |
| Partial Digests | 484 | Shorter text draws 30--70% of its content from a longer source |
| Retranslations | 288 | Two texts of similar length sharing significant content (parallel translations from the same Indic source) |
| Commentaries | 621 | Shorter text quotes portions of a longer text with added exegetical material |
| Shared Tradition | 1,238 | Texts sharing content through common tradition rather than direct derivation |

Additionally, **63 multi-source digests** were identified -- texts that draw content from two or more distinct source texts, with combined coverage exceeding any single source.

The pipeline was validated against the well-established scholarly consensus that the Heart Sutra (T250, T251) is a digest of the Large Prajnaparamita Sutra (T223). All six validation assertions passed, correctly classifying T250 as a full digest of T223 (73.2% coverage), T251's jing section as a partial digest (44.6% coverage), and correctly identifying T250 and T251 as retranslations of each other rather than digests of one another.

This appears to be the first large-scale, corpus-wide computational analysis specifically targeting digest and text-reuse relationships across the full Taisho canon.

---

## 2. Methodology

### 2.1 Five-Stage Pipeline

The analysis proceeded through five sequential stages:

**Stage 1: Text Extraction.** All XML files in the CBETA TEI P5b corpus were parsed, extracting CJK text content while respecting TEI conventions. Character declaration tables (charDecl) were used to normalize variant characters. Editorial apparatus was handled by preferring lemma readings over variant readings. Paratextual elements (notes, bylines, document numbers, fascicle markers) were excluded. Where present, the distinction between preface (xu) and sutra body (jing) sections was preserved. Texts shorter than 20 CJK characters were excluded as fragments.

**Stage 2: Candidate Generation.** Rather than performing O(n^2) pairwise comparisons across all texts, we used a character n-gram fingerprinting approach (5-gram) to identify candidate pairs efficiently. Stop-grams appearing in more than 5% of all texts were excluded to eliminate formulaic Buddhist phrases (e.g., "Thus have I heard, at one time the Buddha was dwelling..."). A containment similarity metric was computed for each candidate pair, requiring a minimum containment of 0.10. A size ratio filter required the putative source to be at least 2x the length of the putative digest, and texts longer than 50,000 characters were excluded as unlikely digest candidates.

**Stage 3: Detailed Alignment.** For each candidate pair, a seed-and-extend alignment was performed. Exact matches of 5 or more characters seeded alignment regions, which were then extended using a fuzzy matching algorithm (match score +1, mismatch score -2, termination threshold -4). This produced a full segmentation of the shorter text into matched and novel regions.

**Stage 4: Scoring and Classification.** Each aligned pair was scored on multiple dimensions: coverage (fraction of digest text matched in source), average segment length, longest segment, number of distinct source regions covered, length asymmetry, and cross-reference presence. A weighted confidence score combined these features. Classification rules then assigned each pair to a category based primarily on coverage thresholds (>=70% for full digest, 30--70% for partial digest, 10--30% for shared tradition) with adjustments for text size ratio (retranslation detection) and average segment length (commentary detection).

**Stage 5: Reporting.** Results were output in both machine-readable (JSON) and human-readable (Markdown) formats, including alignment visualizations, cluster analysis of source texts with multiple digests, and multi-source digest detection.

### 2.2 Classification Definitions

- **Full Digest** (coverage >= 70%, avg segment >= 15 chars): The shorter text is predominantly composed of material extracted verbatim or near-verbatim from the longer text. This corresponds to what Jan Nattier, in her influential 1992 study of the Heart Sutra, termed a "Chinese digest text."

- **Partial Digest** (coverage 30--70%, avg segment >= 10 chars): A substantial but not predominant portion of the shorter text derives from the source. This may indicate selective extraction, or a digest relationship complicated by significant editorial reworking.

- **Retranslation** (coverage >= 30%, size ratio < 3.0): Two texts of comparable length sharing significant content, indicative of independent translations from a common Indic or Central Asian source.

- **Commentary** (coverage 20--70%, avg segment < 10 chars): The shorter text contains many brief quotations from the longer text interspersed with original material, characteristic of exegetical or commentary literature.

- **Shared Tradition** (coverage 10--30%): Low-level textual overlap suggestive of shared doctrinal formulae, common source traditions, or indirect transmission rather than direct derivation.

### 2.3 Confidence Scoring

Confidence scores (0--1 scale) were computed as a weighted combination of six features:

| Feature | Weight | Rationale |
|---------|--------|-----------|
| Coverage (containment) | 0.35 | Primary indicator of digest relationship |
| Longest matched segment | 0.20 | Long verbatim spans are strong evidence of direct copying |
| Number of source regions | 0.10 | Multiple scattered source regions suggest systematic extraction |
| Length asymmetry | 0.10 | Extreme size ratios are more characteristic of digest relationships |
| Document number cross-reference | 0.15 | Shared CBETA document numbers indicate known textual variants |
| Average segment length | 0.10 | Longer average segments indicate more substantial copying |

---

## 3. Key Statistics

### 3.1 Relationship Distribution

| Classification | Count | Percentage |
|----------------|------:|----------:|
| Shared Tradition | 1,238 | 44.0% |
| Commentary | 621 | 22.1% |
| Partial Digest | 484 | 17.2% |
| Retranslation | 288 | 10.2% |
| Full Digest | 181 | 6.4% |
| **Total** | **2,812** | **100%** |

### 3.2 Scope

- **Unique texts involved:** 1,412 out of approximately 2,920 texts in the Taisho (roughly 48%)
- **Texts with English title translations available:** 567 of 1,412 (40%)
- **Multi-source digests detected:** 63
- **Highest confidence score:** 0.806 (T20n1134B / T20n1134A, Vajra Longevity Dharani retranslation)
- **Highest coverage (full digest):** 100% -- multiple short sutras found entirely within larger compilations

### 3.3 Confidence Distribution

Among the top 50 results by confidence:
- 37 classified as full_digest (74%)
- 10 classified as retranslation (20%)
- 3 classified as other categories (6%)

This suggests the pipeline's highest-confidence detections are predominantly genuine digest and retranslation relationships, while lower-confidence results are more likely to contain false positives or ambiguous cases.

---

## 4. Validated Results: The Heart Sutra Test Case

The pipeline was validated against the most well-studied digest relationship in the Chinese Buddhist canon: the derivation of the Heart Sutra from the Large Prajnaparamita Sutra. Jan Nattier's seminal 1992 article "The Heart Sutra: A Chinese Apocryphal Text?" demonstrated that the Kumarajiva-attributed Heart Sutra (T250) was composed by extracting passages from Kumarajiva's translation of the Pañcavimsatisahasrika Prajnaparamita (T223) and framing them with an opening and closing formula.

### Validation Results: 6/6 Passed

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| T250 -> T223 classification | full_digest | full_digest | PASS |
| T250 -> T223 coverage | >= 0.70 | 0.732 | PASS |
| T251 jing -> T223 classification | partial_digest | partial_digest | PASS |
| T251 jing -> T223 coverage | >= 0.30 | 0.446 | PASS |
| T250 not digest of T251 | not full/partial_digest | retranslation | PASS |
| T251 not digest of T250 | not full/partial_digest | not_found | PASS |

### Detailed Findings

**T250 (Kumarajiva Heart Sutra) -> T223:** 73.2% coverage, confidence 0.660, 8 distinct source regions, longest matched segment of 156 characters. The novel fraction of 26.9% corresponds to the framing narrative and the mantra -- precisely the elements Nattier identified as additions to the extracted Prajnaparamita material.

**T251 (Xuanzang Heart Sutra) jing section -> T223:** 44.6% coverage, confidence 0.432, 6 source regions, longest segment of 62 characters. The substantially lower coverage reflects the different translator: Xuanzang's rendering of the same Prajnaparamita passages uses different Chinese phrasing than Kumarajiva's T223, reducing character-level overlap. This cross-translator gap (73% vs. 45%) is itself an important methodological finding.

**T250 <-> T251:** Correctly classified as retranslation (65.4% mutual overlap, similar text length), not as a digest relationship. This validates the pipeline's ability to distinguish parallel translations from digest derivation.

### Heart Sutra Cluster

The pipeline also correctly detected the broader Heart Sutra textual network:

- T85n2747 (Interlinear Commentary on the Heart Sutra): detected as multi-source digest with 97.0% combined coverage from five Heart Sutra commentaries
- T08n0250 (Kumarajiva Heart Sutra): detected as multi-source with 95.6% combined coverage from T223, the Dazhidu lun (T25n1509), and several commentaries
- Multiple retranslation relationships among the various Heart Sutra translations (T250, T251, T252, T253, T254)

### Novel Segment Analysis: Searching for Additional Sources

A natural follow-up question arises from the alignment data: the 27% of T250 and 55% of T251 that do *not* match T223 -- could this "novel" material come from some other text in the Taisho? If so, the Heart Sutras might be multi-source digests rather than single-source digests with original framing material.

To investigate, we extracted all novel segments from both alignments and searched for each across the full corpus of extracted texts (all ~2,920 texts in the Taisho).

#### T250 (Kumarajiva): Novel material is unique

The novel segments in T250 total approximately 80 characters and consist of:

| Novel Passage | Chars | Found elsewhere? |
|---------------|------:|-----------------|
| 觀世音菩 (opening name fragment) | 4 | **No** -- unique to T250 |
| 照見五陰空度一切苦厄 | 10 | **No** -- unique; the 五陰 phrasing (vs. 五蘊) appears nowhere else |
| 心無罣礙無罣礙故無有恐怖離一切顛倒夢想苦惱究竟涅槃三世諸佛 | 29 | **No** -- the specific phrasing with 離一切 and 苦惱 is unique |
| 能除一切苦真實不虛 | 9 | Yes -- 13 other texts, all later Heart Sutra translations and commentaries |
| 竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵 (dharani) | 19 | **No** -- this transliteration is unique to T250 |
| Small connectives (以無, 依, 故, 知) | ~5 | -- |

The only passage found elsewhere is the formulaic 能除一切苦真實不虛, which appears in later Heart Sutra translations (T252, T253, T254), commentaries (T33n1710--1714), and anthologies (T48n2009, T51n2075) -- all texts that derive this phrase *from* the Heart Sutra tradition, not vice versa. The opening scene, the framing passages, the dharani transliteration, and the distinctive 五陰 vocabulary are all without parallel in any other Taisho text.

#### T251 (Xuanzang): Novel material matches only derivative texts

T251's novel segments are more extensive (144 characters, 55% of jing text) because cross-translator matching captures less of the shared Prajnaparamita content. Searching these passages across the corpus:

| Novel Passage | Chars | Found in |
|---------------|------:|----------|
| 觀自在菩薩行 (opening) | 6 | Commentaries on T251 only (T33n1702, T33n1714, T85n2747) |
| 照見五蘊皆空度一切苦厄... | 20 | Same commentaries + T39n1791, T47n1970 |
| 空即是色受想行識亦復如是...不增不減 | 33 | Later Heart Sutra translations (T252, T253), commentaries, T07n0220 (partial) |
| 菩提薩埵依般若波羅蜜多 | 11 | Later translations (T252--T254), commentaries (T33n1710--14, T85n2746--47) |
| 心無罣礙...遠離顛倒夢想究竟涅槃三世諸佛依 | 28 | Later translations (T252, T253), commentaries |
| 是大神咒是大明咒是無上咒是無等等咒能除一切苦真實不虛 | 26 | **No** -- the 是大神咒 phrasing is unique to T251 |
| 揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶 (dharani) | 19 | **No** -- this transliteration is unique to T251 |

All matches fall into three categories: (1) later Heart Sutra translations from the Tang dynasty (T252 by Dharmacandra, T253 by Prajna, T254 by Prajnacakra), (2) Heart Sutra commentaries (T33n1710 by Kuiji, T33n1711 by Yuance, T33n1712 by Fazang, T33n1714 by Zongxie and Rujing), and (3) Dunhuang Heart Sutra manuscripts (T85n2746, T85n2747). None of these is a plausible source for T251; all are derivative.

We specifically investigated **T07n0220** (Xuanzang's own 600-fascicle Mahaprajnaparamita translation, 4.76 million characters) as a potential second source. While it contains some shared Prajnaparamita vocabulary (色不異空, 心無罣礙), it **lacks all the distinctive Heart Sutra passages**: no 照見五蘊皆空, no 遠離顛倒夢想, no 揭帝揭帝 dharani, no 是大神咒. T07n0220 is not a source for T251's novel material.

We also checked **T25n1509** (Kumarajiva's Dazhidu lun, 2.85 million characters) as a potential source for T250's novel passages. It contains only generic Buddhist vocabulary (觀世音菩薩, 心無罣礙) but none of the distinctive T250 phrasing.

#### Implications for the Heart Sutra origins debate

Neither T250 nor T251 is a multi-source digest. The novel material in both texts is **not traceable to any other extant text** in the Taisho. Structurally, the novel passages serve a consistent function: they provide the **narrative wrapper** that transforms an excerpt from Prajnaparamita philosophical discourse into a self-contained sutra:

1. **Opening scene** -- Avalokitesvara practicing Prajnaparamita (no 如是我聞 formula, no Buddha as speaker -- a highly unusual feature)
2. **Connective tissue** -- 心無罣礙, 遠離/離一切顛倒夢想, etc., linking the excerpted doctrinal passages
3. **Dharani and mantra description** -- entirely novel, with unique transliterations in each version
4. **Power attribution** -- 能除一切苦真實不虛, identifying the teaching's soteriological function

The matched material is the **doctrinal core** (negation of skandhas, sense-bases, dependent origination, the four noble truths, wisdom, and attainment) drawn from the Prajnaparamita literature. The novel material is precisely the apparatus that an editor/compiler would need to add when constructing a standalone sutra from extracted philosophical material.

This structural pattern -- doctrinal core excerpted verbatim, narrative apparatus composed fresh -- is consistent with Nattier's Chinese-composition hypothesis. It is also compatible with derivation from a Sanskrit source (now lost or unrepresented in the Taisho) that itself shared its doctrinal core with the Prajnaparamita literature. What our analysis can establish is that no *Chinese* text other than T223 served as a source, and that the novel material was not borrowed from any identifiable text in the canon.

---

## 5. Notable Discoveries

### 5.1 Highest-Confidence Digest Relationships

The top results by confidence reveal several categories of textually significant relationships:

#### Verse Digests of Prose Treatises

Several of the highest-confidence results are verse summaries (song/ji) extracted from their parent prose treatises:

- **T24n1501 Pusajie ben (Bodhisattva Precepts Text) -> T30n1579 Yuqie shidi lun (Yogacarabhumi):** 97.0% coverage, confidence 0.784. The Bodhisattva Precepts chapter is almost entirely drawn from the Yogacarabhumi's vinaya sections. The alignment shows nearly 7,000 consecutive matching characters, indicating massive verbatim extraction.

- **T31n1603 Xianyangsheng jiaolun song (Verses of the Xianyangsheng jiaolun) -> T31n1602 Xianyangsheng jiaolun:** 99.0% coverage, confidence 0.749. The verse summary is almost character-for-character present in the parent treatise, with the alignment showing extensive exact matches spread across all 11 chapters.

- **T29n1560 Abhidharmakosha Verses -> T29n1558 Abhidharmakosha:** 99.5% coverage, confidence 0.740. Vasubandhu's famous verses are faithfully embedded in the prose commentary, as expected.

- **T31n1601 Bianzhongbian lun song (Madhyantavibhaga Verses) -> T31n1600 Bianzhongbian lun:** 99.7% coverage, confidence 0.736.

- **T30n1570 Guangbailun ben (Shataka Verses) -> T30n1571 Guangbailun shi (Shataka Commentary):** 99.7% coverage, confidence 0.723.

While the relationship between verse root texts and their commentaries is well known to scholars, the pipeline's ability to detect and quantify these relationships with such precision provides computational confirmation of the traditional understanding and validates the methodology.

#### Encyclopedic Compilations as Source Reservoirs

The most striking pattern in our results concerns three Tang-dynasty encyclopedic compilations that appear as source texts for dozens of shorter works:

- **T53n2122 Fayuan zhulin (Forest of Gems in the Garden of the Dharma):** 102 digest relationships detected, including 17 full digests and 85 partial digests. This 100-fascicle compilation by Daoshi (d. 683) quotes extensively from earlier sutras, and our pipeline detected these quotations in reverse -- finding that many shorter sutras have their full text present within the Fayuan zhulin.

- **T53n2121 Jinglü yixiang (Distinctive Features of Sutras and Vinayas):** 49 digest relationships detected, compiled by Baochang in 516 CE.

- **T54n2123 Zhujing yaoji (Essential Collection from Various Sutras):** 27 digest relationships detected, compiled by Daoshi as a companion to the Fayuan zhulin.

These results are not unexpected -- these texts are known to be compilations that incorporate earlier material. However, the systematic quantification of which texts are fully vs. partially absorbed is novel. The fact that texts like the Foshuo ma you ba tai pi ren jing (T02n0115, Sutra on Eight Attitudes of Horses, 98.3% coverage) are found virtually in their entirety within the Fayuan zhulin raises important questions about textual transmission: did Daoshi have access to independent manuscript traditions, or was he working from a version already close to what survives in the Taisho?

#### Short Sutras Embedded in Agama Collections

Several short independent sutras were found to be full digests of passages within the larger Agama collections:

- **T14n0503 Biqiu bi nü e ming yu zi sha jing -> T02n0099 Samyuktagama:** 100% coverage. This short sutra about a monk avoiding a woman's bad reputation is entirely contained within the Samyuktagama.

- **T14n0502 Fo wei nianshao biqiu shuo zheng shi jing -> T02n0099 Samyuktagama:** 100% coverage. The sutra where the Buddha instructs a young monk is a direct extract.

- **T14n0499 Fo wei Azhiluojia ye zihua zuo ku jing -> T02n0099 Samyuktagama:** 100% coverage. Another individual sutra that exists as a passage in the Samyuktagama.

- **T02n0128b Xumoti nü jing -> T02n0125 Ekottaragama:** 99.7% coverage.

- **T01n0061 Shou xin sui jing -> T02n0125 Ekottaragama:** 99.7% coverage.

These results confirm what text-critical scholars have long suspected: many of the small independent sutras in the Taisho volumes 1--17 are in fact individual discourse extracts that were at some point separated from their Agama context and transmitted independently. The pipeline provides systematic evidence for this on a scale not previously attempted.

#### Chan/Zen Literature Embedded in Transmission Records

- **T48n2010 Xinxin ming (Inscription on Faith in Mind) -> T51n2076 Jingde chuandeng lu:** 100% coverage, confidence 0.717. The famous poem attributed to the Third Patriarch Sengcan is found complete within the Jingde Transmission of the Lamp record.

- **T48n2014 Yongjia zhengdao ge (Song of Enlightenment) -> T51n2076 Jingde chuandeng lu:** 99.1% coverage, confidence 0.718. Yongjia Xuanjue's celebrated verse composition is likewise fully embedded.

- **T48n2010 -> T49n2036 Fozu lidai tongzai:** 100% coverage, confidence 0.716. The Xinxin ming also appears in full in this later historical chronicle.

#### Vinaya (Monastic Rule) Derivatives

The Four-Part Vinaya (T22n1428, Dharmaguptaka Vinaya) serves as the source for an extensive network of derivative texts:

- T22n1431 (Bhikkhuni Precepts): 81.0% coverage
- T22n1434 (Bhikkhuni Karmavacana): 66.5% coverage
- T22n1429 (Bhikkhu Precepts): 65.8% coverage
- T22n1432 (Miscellaneous Karmavacana): 69.7% coverage
- T22n1430 (Sangha Precepts): 66.3% coverage
- T22n1433 (Karmavacana): 68.3% coverage

Plus 5 additional partial digest relationships with Daoxuan's later vinaya commentaries.

Similarly, the Mulasarvastivada Vinaya (T23n1442, T23n1443) and its derivative precept texts show the same pattern. The pipeline maps the full derivation network for these vinaya traditions in a way that, to our knowledge, has not been computationally quantified before.

### 5.2 Multi-Source Digests

The 63 detected multi-source digests include several noteworthy cases:

**T21n1237 Azhapo ju guishen dajiang shang fo tuoluoni shenzhou jing:** 99.4% combined coverage from T21n1336 (81.6%) and T21n1238 (74.9%). Nearly the entire text is accounted for by material from two dharani collections.

**T17n0724 Foshuo zuiye yingbao jiaohua diyu jing (Sutra on Karmic Retribution):** 96.0% combined coverage from T53n2122 (84.3%), T54n2123 (82.9%), T45n1909 (67.8%), and T14n0441 (41.1%). This short sutra on hell and karmic retribution is almost entirely present across four different larger compilations.

**T22n1429 Sifenlü biqiu jieben (Four-Part Bhikkhu Precepts):** 93.2% combined coverage from T40n1806, T22n1428, and T85n2787. The precepts text draws from multiple vinaya-related sources.

**T16n0686 Foshuo baoen fengpen jing (Sutra on Repaying Kindness with the Bon):** 95.6% combined coverage from commentary and encyclopedia sources.

**T85n2747 Interlinear Heart Sutra:** 97.0% combined coverage from five different Heart Sutra commentaries and translations, confirming its character as an annotated edition drawing from multiple sources.

### 5.3 Dharani Collection Networks

The Tuoluoni zaji (T21n1336, Miscellaneous Dharani Collection) functions as a reservoir text for dharani literature much as the Fayuan zhulin does for sutra literature. Sixteen shorter dharani texts were found to be full or partial digests of T21n1336, with coverage ranging from 100% down to 43%. Similarly, the Tuoluoni jijing (T18n0901, Dharani Collection Sutra) serves as a source for 13 shorter ritual and dharani texts.

This systematic mapping of dharani text derivation networks appears to be a novel contribution. While individual dharani texts have been studied in relation to their sources, the comprehensive identification of which dharani collections served as "parent" repositories for which shorter texts has not, to our knowledge, been previously published.

---

## 6. Patterns and Observations

### 6.1 Taisho Volume Distribution

The digest relationships are not uniformly distributed across the Taisho. Preliminary observation reveals several concentration patterns:

**Volumes most heavily involved as source texts:**
- T02 (Agama section): The Samyuktagama (T99) and Ekottaragama (T125) serve as sources for multiple independent short sutras
- T22--T24 (Vinaya section): The major vinaya texts generate extensive derivative networks of precept texts, karmavacana procedures, and commentaries
- T30--T31 (Yogacara treatises): The Yogacarabhumi (T1579) and Xianyangsheng jiaolun (T1602) are sources for verse summaries and derivative treatises
- T53--T54 (Encyclopedic compilations): The Fayuan zhulin and companion texts serve as the most prolific source texts in the entire corpus

**Volumes most heavily involved as digest texts:**
- T01--T04 (Agama and Jataka): Many short independent sutras are digests of larger collections
- T14 (Miscellaneous short sutras): Extremely high density of digest relationships, with many texts being extracts from encyclopedic compilations
- T17 (Miscellaneous short sutras): Similar pattern to T14
- T19--T21 (Dharani and ritual texts): Extensive derivation networks from dharani collections
- T85 (Dunhuang manuscripts): Several Dunhuang texts are digests of or closely related to canonical texts

### 6.2 Same-Translator vs. Cross-Translator Patterns

The Heart Sutra validation case provides a clear demonstration of how translator identity affects detection. The Kumarajiva Heart Sutra (T250) shows 73.2% coverage against Kumarajiva's own Prajnaparamita translation (T223), while the Xuanzang Heart Sutra (T251) shows only 44.6% against the same T223, despite both Heart Sutras deriving from the same underlying Prajnaparamita material.

This approximately 30-percentage-point gap between same-translator and cross-translator coverage is a systematic feature of the pipeline. It means our coverage thresholds are effectively tuned for same-translator relationships, and **cross-translator digest relationships are likely underdetected.** Many pairs classified as "partial digest" or "shared tradition" may in fact represent full digest relationships obscured by translator-dependent phrasing differences.

The retranslation detection feature partially compensates for this by identifying pairs of comparable length with moderate overlap, but genuine cross-translator digest relationships (short text from translator A derived from a source translated by translator B) remain difficult to detect at the character level.

### 6.3 The Lotus Sutra Retranslation Network

The pipeline detected the Kumarajiva Lotus Sutra (T09n0262) and the Tianpin Lotus Sutra (T09n0264) as retranslations with 92.0% coverage and confidence 0.735, ranked 15th overall. This well-known retranslation pair serves as additional validation. The high coverage reflects the fact that T264 is a revised and supplemented version of T262.

### 6.4 Commentary vs. Digest Disambiguation

The pipeline's distinction between commentary (many short quotations with added material) and digest (fewer, longer extracted passages) is a useful heuristic but not always clean. The 621 commentary classifications likely include genuine commentarial quotation patterns, but also cases where a digest relationship has been fragmented by editorial differences. The average segment length threshold of 10 characters for commentary classification is a rough heuristic that deserves further refinement.

---

## 7. What May Be Previously Unknown

While many of the individual relationships detected are known to traditional Buddhist scholarship, several aspects of our findings may contribute new knowledge:

### 7.1 Systematic Quantification of Encyclopedic Absorption

The comprehensive mapping of how the Fayuan zhulin (T53n2122) absorbed 102 texts -- with precise coverage percentages ranging from 30% to 100% -- appears to be unprecedented. While scholars have known that this encyclopedia quotes extensively from earlier sources, the systematic identification of which texts are fully (17 texts at >70% coverage) vs. partially (85 texts at 30--70% coverage) incorporated provides a new level of granularity for studying Daoshi's compilation methods. Particularly noteworthy:

- **T15n0615 Pusa he seyu fa jing:** 100% coverage in the Fayuan zhulin. This entire short text on monastic attitudes toward desire is found verbatim within Daoshi's compilation, suggesting either direct copying or shared manuscript traditions.
- **T32n1689 Qing Bintoulou fa (Inviting Pindola):** 99.4% coverage.
- **T12n0332 Foshuo Youtian wang jing:** 99.4% coverage.

### 7.2 Agama Extract Identification

The systematic identification of short independent sutras that are extracts from the Samyuktagama and Ekottaragama provides computational support for text-critical hypotheses that have often been argued on a case-by-case basis. The pipeline identified at least 7 texts with >70% coverage in the Agamas and many more in the 30--70% range. Scholars working on Agama studies can use these results to prioritize texts for closer philological examination.

### 7.3 Dharani Derivation Networks

The mapping of how T21n1336 (Dharani Miscellany) and T18n0901 (Dharani Collection Sutra) serve as reservoir texts for dozens of shorter dharani texts is, to our knowledge, a novel systematic finding. While individual dharani texts have been studied, the comprehensive view of derivation networks across the entire dharani literature of the Taisho has not previously been published.

### 7.4 Unexpected Cross-Genre Relationships

Several detected relationships cross traditional genre boundaries:

- **T48n2010 Xinxin ming -> T48n2023 (Yuanren lun):** 100% coverage. The famous Chan poem attributed to Sengcan appears complete within Zongmi's treatise on the origin of humanity. While Zongmi's use of earlier Chan texts is known, the complete embedding of the Xinxin ming in this context may not have been previously quantified.

- **T85n2918 Shijia guanhua huan yu jing -> T04n0211 Faju piyu jing:** 100% coverage, confidence 0.704. This Dunhuang text is entirely derived from the Dhammapada with commentary (Faju piyu jing), suggesting it may be an extract rather than an independent composition.

- **T12n0369 Amituo fo shuo zhou -> T85n2827 Jingtu wuhui nianfo song jing guanxing yi:** 96.6% coverage. A short Amitabha dharani text is almost entirely present within a Pure Land liturgical manual, illuminating how ritual texts were compiled from earlier dharani sources.

### 7.5 Yogacara Treatise Derivation Chain

The pipeline reveals a clear derivation chain within the Yogacara scholastic tradition:

1. T30n1579 Yogacarabhumi (source)
2. T31n1602 Xianyangsheng jiaolun (draws from Yogacarabhumi)
3. T31n1603 Xianyangsheng jiaolun song (verse summary of T1602)
4. T24n1501 Bodhisattva Precepts (extracted from Yogacarabhumi vinaya section)
5. T85n2783 Dacheng daoqie jing suitingshu jue (97.3% from Yogacarabhumi)
6. T16n0676 Jieshenmi jing (86.5% from Yogacarabhumi)
7. T31n1615 Wangfa zhengli lun (62.9% from Yogacarabhumi)

The Yogacarabhumi emerges as one of the most generative source texts in the entire Taisho, with 6 detected derivative texts at >50% coverage. The pipeline provides precise quantification of how much of each derivative text comes from this single massive source.

### 7.6 Bibliographic Catalog Relationships

The pipeline detected the expected cascade of medieval Chinese Buddhist bibliographic catalogs:

- T55n2154 Kaiyuan shijiao lu -> T55n2155 Kaiyuan shijiao lu lüechu (73.9% coverage)
- T55n2154 -> T55n2157 Zhenyuan xinding shijiao mulu (absorbed into the later catalog)
- T55n2152 Xu gujin yijing tuji is a full digest of both T55n2154 (75.1%) and T55n2157 (77.0%)

While the relationships among these catalogs are known, the precise coverage measurements may help scholars assess the degree of editorial independence in each successive catalog.

---

## 8. Limitations

### 8.1 Character-Level Matching Only

The pipeline operates at the character level, detecting verbatim or near-verbatim textual overlap. It cannot detect:

- **Paraphrase-level reuse:** Where an author restates the same ideas in entirely different words
- **Structural borrowing:** Where a text follows the same organizational pattern without verbal overlap
- **Translation-level relationships:** Cross-translator digest relationships are systematically underdetected, as demonstrated by the ~30% coverage gap between same-translator (T250->T223: 73%) and cross-translator (T251->T223: 45%) Heart Sutra comparisons
- **Conceptual dependence:** Where a shorter text depends on a longer text's ideas without quoting it

### 8.2 Directionality Assumptions

The pipeline assumes the shorter text is the digest and the longer text is the source. This is a reasonable default but not always correct:

- A short original text may have been incorporated into a later, longer compilation (the Agama extract cases illustrate this -- the short sutras likely predate the compiled Agama)
- The chronological direction of derivation cannot be determined from textual overlap alone
- Two texts may share a common source no longer extant in the Taisho

### 8.3 Size Ratio Filtering

The requirement that source texts be at least 2x the length of digest texts, combined with the 50,000-character maximum digest length, means that digest relationships between two very long texts, or between texts of similar length, may be missed. The retranslation classification partially compensates for the latter case.

### 8.4 Stop-Gram Threshold Sensitivity

The 5% document frequency threshold for stop-gram filtering eliminates very common Buddhist formulaic phrases. While necessary to prevent false positives from formulaic overlap, this may also eliminate genuine shared content that happens to use common phrasings. The threshold was tuned for the full corpus; smaller sub-corpus analyses may require adjustment (as demonstrated by the testing experience where tiny corpora required threshold=1.0).

### 8.5 False Positive Risks

Several types of false positives are possible:

- **Formulaic overlap:** Buddhist texts share extensive stock phrases (nidana, colophons, dharani formulae) that may produce spurious matches even after stop-gram filtering
- **Encyclopedic contamination:** The Fayuan zhulin and similar compilations may create transitive false positives (text A matches Fayuan zhulin, which quotes text B, creating an apparent A-B relationship that is actually mediated)
- **Shared source:** Two texts may independently derive from a common source not in the corpus, creating the appearance of a direct A-B relationship

### 8.6 Coverage of Dunhuang Materials

Volume 85 (Dunhuang manuscripts) is unevenly represented in the CBETA corpus, and many Dunhuang texts exist in fragmentary form. Relationships involving T85 texts should be treated with particular caution.

---

## 9. Future Directions

### 9.1 Chronological Analysis

Incorporating dated translator and author information (available from CBETA metadata and traditional Buddhist bibliographic catalogs) would allow the pipeline to assess the chronological plausibility of detected relationships. A digest detected from a text attributed to a 3rd-century translator to a source attributed to a 7th-century compiler is likely a reverse relationship (the compiler quoted the earlier text).

### 9.2 Cross-Translator Compensation

Developing a translation-aware matching algorithm -- perhaps using character embedding similarity rather than exact character matching -- could improve detection of cross-translator digest relationships. The known Heart Sutra case provides a calibration benchmark: the true coverage should be similar regardless of translator, but our character-level method detects 73% vs. 45%.

### 9.3 Network Visualization

The 2,812 detected relationships define a complex textual network. Graph analysis could reveal:
- Community structure (clusters of closely related texts)
- Hub texts (high betweenness centrality, connecting otherwise separate textual traditions)
- Transmission pathways (chains of digest relationships)

### 9.4 Expanded Validation

Ground truth validation could be expanded beyond the Heart Sutra case to include:
- The Diamond Sutra and its known commentary tradition
- The vinaya precepts and their known derivation from full vinaya texts
- Known retranslation pairs from Buddhist bibliographic catalogs (Kaiyuan lu classifications)

### 9.5 Sanskrit/Tibetan Cross-Reference

Where Sanskrit or Tibetan parallels exist, the detected Chinese-to-Chinese relationships could be compared against independently established relationships in those traditions. For example, the Abhidharmakosha verse/prose relationship (T1560/T1558) has a well-established Sanskrit parallel that could serve as additional validation.

### 9.6 Expansion Beyond Volume T

The current analysis covers only the "T" (main Taisho) volumes. Extending to the Xu zangjing (supplementary collection) and other CBETA-digitized collections could reveal additional relationships.

### 9.7 Scholarly Review of Novel Findings

The most promising direction is expert review of the potentially novel findings, particularly:
- The 63 multi-source digests (are these genuinely composite texts?)
- High-confidence relationships involving understudied texts (T14 and T17 miscellaneous sutras)
- The dharani derivation networks (do these reflect genuine textual history or artifact of how dharani literature was compiled?)
- Dunhuang texts detected as digests of canonical texts (can this help date or provenance Dunhuang manuscripts?)

---

## Appendix A: Technical Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| N-gram size | 5 | Character n-gram size for fingerprinting |
| Stop-gram doc freq | 0.05 | Exclude n-grams in >5% of texts |
| Min containment | 0.10 | Minimum containment to keep candidate |
| Min size ratio | 2.0 | Source must be >= 2x digest length |
| Max digest length | 50,000 | Maximum character count for digest candidate |
| Min seed length | 5 | Minimum exact match to seed alignment |
| Fuzzy match score | +1 | Character match reward |
| Fuzzy mismatch score | -2 | Character mismatch penalty |
| Fuzzy extension threshold | -4 | Score drop to terminate extension |
| Full digest threshold | 0.70 | Coverage for full digest classification |
| Partial digest threshold | 0.30 | Coverage for partial digest classification |
| Shared tradition threshold | 0.10 | Minimum coverage for any relationship |
| Retranslation size ratio | 3.0 | Maximum ratio for retranslation classification |
| Commentary avg seg length | 10 | Below this, classify as commentary |

## Appendix B: Source Code

The complete pipeline source code is organized in the following modules:

- `digest_detector/extract.py` -- Stage 1: XML parsing and text extraction
- `digest_detector/fingerprint.py` -- Stage 2a: N-gram fingerprinting
- `digest_detector/candidates.py` -- Stage 2b: Candidate pair generation
- `digest_detector/align.py` -- Stage 3: Seed-and-extend alignment
- `digest_detector/score.py` -- Stage 4: Scoring and classification
- `digest_detector/report.py` -- Stage 5: Report generation
- `digest_detector/pipeline.py` -- Main pipeline orchestrator
- `digest_detector/config.py` -- All tunable parameters
- `digest_detector/models.py` -- Data models

Test suite: 97 tests covering all stages plus integration tests on T250/T251 -> T223.

---

*Analysis conducted February 2026 using the CBETA TEI P5b XML corpus of the Taisho Tripitaka.*
