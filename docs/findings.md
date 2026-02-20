# Computational Detection of Digest Relationships in the Taisho Canon

## Findings from an Automated Five-Stage Pipeline Analysis

---

## 1. Executive Summary

We developed and ran a fully automated computational pipeline to detect **digest relationships** across the entire Taisho Tripitaka (Taisho shinshu daizokyo), the standard modern edition of the Chinese Buddhist canon containing approximately 2,920 texts across 85 volumes. A "digest" in this context is a shorter text whose content is substantially derived from a longer source text -- whether through abridgment, extraction, selective quotation, or compilation.

The pipeline analyzed all 8,982 XML files in the CBETA TEI P5b corpus and detected **7,169 significant textual relationships** involving **1,814 unique texts**. These were classified into five categories:

| Classification | Count | Description |
|----------------|------:|-------------|
| Excerpts | 138 | Shorter text draws >=80% of its content verbatim from a longer source |
| Digests | 549 | Shorter text draws 30--80% of its content from a longer source |
| Retranslations | 224 | Two texts of similar length sharing significant content (parallel translations from the same Indic source) |
| Commentaries | 669 | Shorter text quotes portions of a longer text with added exegetical material |
| Shared Tradition | 5,589 | Texts sharing content through common tradition rather than direct derivation |

Additionally, **58 multi-source digests** were identified -- texts that draw content from two or more distinct source texts, with combined coverage exceeding any single source.

A notable methodological contribution is the pipeline's **phonetic transliteration detection**, which identifies relationships between texts that use different Chinese characters to transliterate the same Sanskrit sounds. This technique, based on a character-to-syllable mapping derived from the Digital Dictionary of Buddhism (DDB), found 634 text pairs with phonetically equivalent passages -- the first corpus-wide computational detection of cross-transliterator relationships in Chinese Buddhist literature. However, the phonetic candidate generation also produced a large number of low-confidence shared tradition pairs (see Section 6.5), reflecting general Buddhist vocabulary overlap rather than textual derivation. The higher-confidence categories (excerpt, digest, retranslation, commentary) were only modestly affected by phonetic matching.

The pipeline was validated against the well-established scholarly consensus that the Heart Sutra (T250, T251) is a digest of the Large Prajnaparamita Sutra (T223). All six validation assertions passed, correctly classifying T250 as a digest of T223 (73.2% coverage), T251's jing section as a digest (44.6% coverage), and correctly identifying T250 and T251 as retranslations of each other rather than digests of one another.

This appears to be the first large-scale, corpus-wide computational analysis specifically targeting digest and text-reuse relationships across the full Taisho canon.

---

## 2. Methodology

### 2.1 Five-Stage Pipeline

The analysis proceeded through five sequential stages:

**Stage 1: Text Extraction.** All XML files in the CBETA TEI P5b corpus were parsed, extracting CJK text content while respecting TEI conventions. Character declaration tables (charDecl) were used to normalize variant characters. Editorial apparatus was handled by preferring lemma readings over variant readings. Paratextual elements (notes, bylines, document numbers, fascicle markers) were excluded. Where present, the distinction between preface (xu) and sutra body (jing) sections was preserved. Texts shorter than 20 CJK characters were excluded as fragments.

**Stage 2: Candidate Generation.** Rather than performing O(n^2) pairwise comparisons across all texts, we used a character n-gram fingerprinting approach to identify candidate pairs efficiently.

*N-gram size.* We used 5-character n-grams (5-grams). This choice balances sensitivity against specificity: shorter n-grams (3 or 4 characters) generate excessive false positives because many common Buddhist terms and phrases are only 3--4 characters long (e.g., 菩薩 *púsà*, "bodhisattva"; 波羅蜜 *bōluómì*, "pāramitā"), while longer n-grams (8 or 10 characters) require longer verbatim spans to seed a match, causing the pipeline to miss relationships where scribal variants, editorial changes, or character normalization differences break the chain. At n=5, a matching gram represents a sequence long enough to be textually distinctive but short enough to survive minor transmission variants. The choice of 5 is also standard in computational text-reuse detection for logographic scripts, where each character carries more semantic weight than in alphabetic writing systems.

*Stop-gram filtering.* To prevent false positives from formulaic Buddhist stock phrases, we excluded 5-grams appearing in more than 5% of all documents (i.e., in more than 122 of the 2,455 texts). This removed 381 stop-grams from the index. The most common stop-grams are the formulaic phrases that open and structure virtually all Buddhist sutras:

| Stop-gram | Pinyin | Translation/Context | Texts |
|-----------|--------|-------------------|------:|
| 如是我聞一 | *rúshì wǒ wén yī* | "Thus have I heard: at one [time]..." (opening formula) | 693 (28%) |
| 菩薩摩訶薩 | *púsà móhēsà* | "bodhisattva mahāsattva" (honorific address) | 726 (30%) |
| 阿耨多羅三 | *ānòuduōluó sān* | "anuttara-sam-" (part of *anuttarā samyaksaṃbodhi*, "supreme perfect enlightenment") | 580 (24%) |
| 三千大千世 | *sānqiān dàqiān shì* | "three-thousand great-thousand world[-system]" (cosmological formula) | 588 (24%) |
| 般若波羅蜜 | *bōrě bōluómì* | "*prajñāpāramitā*" (perfection of wisdom) | 550 (22%) |
| 善男子善女 | *shàn nánzǐ shàn nǚ* | "good men and good women" (standard audience address) | 525 (21%) |
| 爾時世尊告 | *ěrshí shìzūn gào* | "at that time the World-Honored One told..." (narrative transition) | 466 (19%) |

These are precisely the formulaic elements that make Buddhist texts *sound* similar without indicating a direct textual relationship. Filtering them allows the pipeline to focus on content-bearing passages.

A containment similarity metric was computed for each candidate pair, requiring a minimum containment of 0.10. A size ratio filter required the putative source to be at least 2x the length of the putative digest, and texts longer than 50,000 characters were excluded as unlikely digest candidates.

**Stage 2b: Phonetic Candidate Generation.** Character-level n-gram matching cannot detect relationships between texts that transliterate the same Sanskrit content using different Chinese characters -- a common phenomenon when different translators render dharani, mantra, or proper names. To address this, a phonetic transliteration detection stage was added after the character-level candidate generation.

A character-to-syllable mapping table was derived from the Digital Dictionary of Buddhism (DDB), extracting 559 Chinese characters used for Sanskrit transliteration, grouped into approximately 200 canonical syllable classes. Characters representing the same Sanskrit syllable (e.g., 竭 *jié* and 揭 *jiē*, both rendering Sanskrit *ga*) are treated as phonetically equivalent. To limit ambiguity, characters mapping to more than 5 distinct syllables were excluded from the table, removing highly polysemous characters like 波 (13 readings), 羅 (12), and 婆 (21) that appear frequently in ordinary prose.

Transliteration regions within each text were identified from two sources: (1) XML-annotated dharani ranges in the CBETA TEI markup, and (2) density-based detection of character regions where transliteration characters cluster. Each text's transliteration regions were converted to syllable 3-gram fingerprints, and containment similarity was computed between all pairs, requiring a minimum phonetic containment of 0.25. A phonetic stopgram filter excluded syllable n-grams appearing in more than 5% of texts to prevent false matches from common Buddhist terms. Seeds were required to contain at least 5 consecutive phonetically equivalent characters with at least 2 differing characters per seed, preventing false positives from single-character coincidences.

This stage generated 22,467 candidate pairs (77% of all candidates), of which 30 produced high-confidence relationships (excerpts, digests, or retranslations) invisible to character-level matching, 195 produced commentary relationships, and 4,780 produced shared tradition classifications. The majority (17,462) fell below the 10% coverage threshold after alignment. The high ratio of candidates to high-confidence findings reflects the fundamental sensitivity/specificity tradeoff of phonetic matching: the same characters used for Sanskrit transliteration (薩 in bodhisattva, 羅 in pāramitā) are pervasive in ordinary Buddhist prose, causing the phonetic fingerprinting to function partly as a broad Buddhist text similarity detector.

**Stage 3: Detailed Alignment.** For each candidate pair, a seed-and-extend alignment was performed in five steps:

1. *Seed finding.* A hash table of all 5-character substrings in the source text was built. The digest text was scanned left to right; at each position where a 5-gram matched the source, the match was greedily extended character-by-character in both directions to find the longest exact match starting from that position. This produced a set of "seeds" -- maximal exact matching substrings, each defined by its start position in both the digest and the source and its length.

2. *Fuzzy extension.* Each seed boundary was then extended with a fuzzy matching algorithm to capture near-matches caused by scribal variants, character substitutions, or minor editorial differences. The algorithm scored each character: +1 for a match, -2 for a mismatch, with single-character gaps (insertions or deletions) allowed at a cost of -2. Extension terminated when the cumulative score dropped below -4, ensuring that two consecutive mismatches with no intervening match would end the extension. The algorithm tracked the highest-scoring extension point and returned that boundary, preventing a lucky match after a long mismatch region from artificially inflating the aligned span.

3. *Optimal chaining.* The extended seeds often overlapped in digest coordinates (multiple source positions matching the same digest region). A weighted interval scheduling algorithm selected the non-overlapping subset of seeds that maximized total digest coverage, using dynamic programming. This step was critical for producing clean, non-redundant alignments: it ensured each character in the digest was assigned to at most one source match.

4. *Segmentation.* The chained seeds were used to partition the digest text into alternating "matched" and "novel" segments, producing a complete map of which portions of the digest correspond to which positions in the source, and which portions are original to the digest.

5. *Phonetic rescan.* After segmentation, each "novel" segment (unmatched portion of the digest) was rescanned for phonetically equivalent matches in the source text. This post-hoc phonetic pass used the same character-to-syllable table as Stage 2b, searching each novel segment against the full source text using phonetic seed-finding -- where `are_phonetically_equivalent()` replaces exact character comparison. Seeds required at least 5 consecutive phonetically equivalent characters with at least 2 differing characters, ensuring that only genuine cross-transliterator matches (not near-exact matches already captured in step 1) were detected. Phonetic matches were spliced into the segment map as "phonetic" match segments, with character-level phonetic mappings recorded for each. This step found 2,881 individual phonetic match segments across 634 text pairs (8.8% of all aligned pairs).

**Stage 4: Scoring and Classification.** Each aligned pair was scored on six dimensions:

- **Coverage** (weight 0.35): The fraction of the digest text that aligns to the source. This is the primary indicator -- a coverage of 0.73 means 73% of the shorter text's characters were found in the longer text.
- **Longest matched segment** (weight 0.20): The length of the single longest contiguous aligned region, normalized by digest length. Long verbatim spans are strong evidence of direct copying rather than coincidental formulaic overlap.
- **Document number cross-reference** (weight 0.15): A binary feature indicating whether the CBETA metadata links the two texts (e.g., variant editions catalogued under the same document number).
- **Number of distinct source regions** (weight 0.10): How many separated positions in the source text contributed material. Multiple scattered regions suggest systematic extraction from different parts of the source, characteristic of a deliberate digest.
- **Length asymmetry** (weight 0.10): The log-ratio of source length to digest length. Extreme size ratios (a 500-character text matched against a 500,000-character source) are more characteristic of digest relationships.
- **Average segment length** (weight 0.10): The mean length of matched segments. Short average segments (many brief quotations) suggest commentary; long average segments suggest wholesale extraction.

These six features were combined into a weighted confidence score (0--1 scale), then classification rules assigned each pair to a category. The classification follows a decision tree that considers coverage, text size ratio, and segment length:

| Condition | Classification |
|-----------|---------------|
| Coverage < 10% | No relationship (excluded) |
| Coverage 10--30% | Shared tradition |
| Coverage >= 30% and source/digest size ratio < 3.0 | Retranslation |
| Coverage >= 80% and avg segment >= 15 chars | Excerpt |
| Coverage >= 30% and avg segment >= 10 chars | Digest |
| Coverage >= 20% and avg segment < 10 chars | Commentary |

The size ratio test fires first for texts of comparable length: when the source is less than 3x the digest length and coverage exceeds 30%, the pair is classified as a retranslation (parallel translations of similar scope) rather than a digest (extraction from a much longer source). The average segment length test distinguishes commentaries (many short quotations interspersed with original exegesis) from digests (fewer, longer verbatim extractions).

**Stage 5: Reporting.** Results were output in both machine-readable (JSON) and human-readable (Markdown) formats, including alignment visualizations, cluster analysis of source texts with multiple digests, and multi-source digest detection.

### 2.2 Classification Definitions

- **Excerpt** (coverage >= 80%, avg segment >= 15 chars): The shorter text is almost entirely composed of material extracted verbatim or near-verbatim from the longer text. At the upper end (approaching 100% coverage, novel fraction near zero), the text is a passage lifted from the source with little or nothing added.

- **Digest** (coverage 30--80%, avg segment >= 10 chars): A substantial portion of the shorter text derives from the source, but significant material has been rearranged, condensed, or supplemented with original additions. This category encompasses both selective extraction with creative reframing (e.g., the Heart Sutra at 73.2% coverage) and more modest textual overlap indicating partial derivation.

- **Retranslation** (coverage >= 30%, size ratio < 3.0): Two texts of comparable length sharing significant content, indicative of independent translations from a common Indic or Central Asian source.

- **Commentary** (coverage >= 20%, avg segment < 10 chars): The shorter text contains many brief quotations from the longer text interspersed with original material, characteristic of exegetical or commentary literature. (In practice, the retranslation and digest rules fire first at higher coverages, so commentary is most common in the 20--50% range.)

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
| Shared Tradition | 5,589 | 78.0% |
| Commentary | 669 | 9.3% |
| Digest | 549 | 7.7% |
| Retranslation | 224 | 3.1% |
| Excerpt | 138 | 1.9% |
| **Total** | **7,169** | **100%** |

The large share of shared tradition reflects the inclusion of phonetic candidate generation (Stage 2b), which added many low-overlap pairs; see Section 6.5 for discussion. Excluding shared tradition, the pipeline found **1,580 higher-confidence relationships** (excerpt, digest, retranslation, or commentary).

### 3.2 Scope

- **Unique texts involved:** 1,814 out of 2,455 extracted texts (roughly 74%)
- **Multi-source digests detected:** 58
- **Highest confidence score:** 0.829 (T20n1134B / T20n1134A, Vajra Longevity Dharani retranslation)
- **Highest coverage:** 100% -- multiple short sutras found entirely within larger compilations, functioning as verbatim excerpts rather than condensed digests

### 3.3 Phonetic Detection Statistics

| Metric | Value |
|--------|------:|
| Phonetic candidates generated | 22,467 (77% of all candidates) |
| Character-level candidates generated | 6,678 (23% of all candidates) |
| Text pairs with phonetic match segments | 634 (8.8% of relationships) |
| Individual phonetic match segments | 2,881 |
| Phonetic-only high-confidence findings | 30 (4 excerpts, 17 digests, 9 retranslations) |

Among relationships containing phonetic match segments, the distribution by classification is: 224 shared tradition (35%), 206 commentary (33%), 137 digest (22%), 54 retranslation (9%), 13 excerpt (2%). Phonetic segments are most prevalent in commentary relationships (31% of all commentaries contain phonetic matches), followed by digests (25%) and retranslations (24%).

### 3.4 Confidence Distribution

Among the top 50 results by confidence:
- 37 classified as excerpt or digest (74%)
- 10 classified as retranslation (20%)
- 3 classified as other categories (6%)

This suggests the pipeline's highest-confidence detections are predominantly genuine digest and retranslation relationships, while lower-confidence results are more likely to contain false positives or ambiguous cases.

---

## 4. Validated Results: The Heart Sutra Test Case

The pipeline was validated against the most well-studied digest relationship in the Chinese Buddhist canon: the derivation of the Heart Sutra from the Large Prajnaparamita Sutra. Jan Nattier's seminal 1992 article "The Heart Sutra: A Chinese Apocryphal Text?" demonstrated that the Kumarajiva-attributed Heart Sutra (T250) was composed by extracting passages from Kumarajiva's translation of the Pañcavimsatisahasrika Prajnaparamita (T223) and framing them with an opening and closing formula.

### Validation Results: 6/6 Passed

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| T250 -> T223 classification | digest | digest | PASS |
| T250 -> T223 coverage | >= 0.70 | 0.732 | PASS |
| T251 jing -> T223 classification | digest | digest | PASS |
| T251 jing -> T223 coverage | >= 0.30 | 0.446 | PASS |
| T250 not digest of T251 | not excerpt/digest | retranslation | PASS |
| T251 not digest of T250 | not excerpt/digest | not_found | PASS |

### Detailed Findings

**T250 (Kumarajiva Heart Sutra) -> T223:** 73.2% coverage, confidence 0.660, 8 distinct source regions, longest matched segment of 156 characters. The novel fraction of 26.9% corresponds to the framing narrative and the mantra -- precisely the elements Nattier identified as additions to the extracted Prajnaparamita material.

**T251 (Xuanzang Heart Sutra) jing section -> T223:** 44.6% coverage, confidence 0.432, 6 source regions, longest segment of 62 characters. The substantially lower coverage reflects the different translator: Xuanzang's rendering of the same Prajnaparamita passages uses different Chinese phrasing than Kumarajiva's T223, reducing character-level overlap. This cross-translator gap (73% vs. 45%) is itself an important methodological finding.

**T250 <-> T251:** Correctly classified as retranslation (65.4% mutual overlap, similar text length), not as a digest relationship. This validates the pipeline's ability to distinguish parallel translations from digest derivation.

### Heart Sutra Cluster

The pipeline also correctly detected the broader Heart Sutra textual network:

- T85n2747 (Interlinear Commentary on the Heart Sutra): detected as multi-source digest with 97.0% combined coverage from five Heart Sutra commentaries
- T08n0250 (Kumarajiva Heart Sutra): detected as multi-source with 95.6% combined coverage from T223, the Dazhidu lun (Treatise on the Great Perfection of Wisdom, T25n1509), and several commentaries
- Multiple retranslation relationships among the various Heart Sutra translations (T250, T251, T252, T253, T254)

### Novel Segment Analysis: Searching for Additional Sources

A natural follow-up question arises from the alignment data: the 27% of T250 and 55% of T251 that do *not* match T223 -- could this "novel" material come from some other text in the Taisho? If so, the Heart Sutras might be multi-source digests rather than single-source digests with original framing material.

To investigate, we extracted all novel segments from both alignments and searched for each across the full corpus of extracted texts (all ~2,920 texts in the Taisho).

#### T250 (Kumarajiva): Novel material is unique

The novel segments in T250 total approximately 80 characters and consist of:

| Novel Passage | Chars | Found elsewhere? |
|---------------|------:|-----------------|
| 觀世音菩 *Guānshìyīn pú-* (opening fragment of Avalokitesvara's name) | 4 | **No** -- unique to T250 |
| 照見五陰空度一切苦厄 *zhàojiàn wǔyīn kōng dù yīqiè kǔ è* ("perceived the five aggregates are empty, transcending all suffering") | 10 | **No** -- unique; the 五陰 *wǔyīn* phrasing (vs. 五蘊 *wǔyùn*) appears nowhere else |
| 心無罣礙無罣礙故無有恐怖離一切顛倒夢想苦惱究竟涅槃三世諸佛 *xīn wú guà'ài... lí yīqiè diāndǎo mèngxiǎng kǔnǎo jiūjìng nièpán sānshì zhūfó* ("mind without obstruction... free from all inverted dreams and suffering, ultimately attaining nirvana, all Buddhas of the three times") | 29 | **No** -- the specific phrasing with 離一切 *lí yīqiè* ("free from all") and 苦惱 *kǔnǎo* ("suffering") is unique |
| 能除一切苦真實不虛 *néng chú yīqiè kǔ zhēnshí bùxū* ("able to remove all suffering, true and not false") | 9 | Yes -- 13 other texts, all later Heart Sutra translations and commentaries |
| 竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵 *jiédì jiédì bōluó jiédì bōluó sēng jiédì pútí sēng suōhē* (dharani: *gate gate pāragate pārasaṃgate bodhi svāhā*) | 19 | **No** at the character level -- this specific transliteration is unique to T250. However, T18n0901 (see note below) contains the same dharani in a different transliteration (揭帝 *jiēdì* for 竭帝 *jiédì*) |
| Small connectives (以無 *yǐwú*, 依 *yī*, 故 *gù*, 知 *zhī*) | ~5 | -- |

The only passage found elsewhere is the formulaic 能除一切苦真實不虛 (*néng chú yīqiè kǔ zhēnshí bùxū*, "able to remove all suffering, true and not false"), which appears in later Heart Sutra translations (T252, T253, T254), commentaries (T33n1710--1714), and anthologies (T48n2009, T51n2075) -- all texts that derive this phrase *from* the Heart Sutra tradition, not vice versa. The opening scene, the framing passages, and the distinctive 五陰 (*wǔyīn*, "five aggregates," using the older translation vs. the standard 五蘊 *wǔyùn*) vocabulary are without parallel in any other Taisho text.

**Note on T18n0901 and the dharani.** The Tuoluoni jijing (*Dhāraṇīsaṃgraha*, Dharani Collection Sutra, T18n0901), attributed to Atikūṭa (阿地瞿多, ca. 654 CE), contains the Prajnaparamita dharani under the heading 般若大心陀羅尼第十六 (*bōrě dàxīn tuóluóní dì shíliù*, "Prajnaparamita Great Heart Dharani, number 16"). Its version reads: 揭帝揭帝波羅揭帝波囉僧揭帝菩提莎訶 -- the same Sanskrit *gate gate pāragate pārasaṃgate bodhi svāhā*, but transliterated with different Chinese characters (揭 *jiē* for T250's 竭 *jié*, 波羅 *bōluó* for T251's 般羅 *bānluó*). Our character-level pipeline correctly reports that T250's specific character sequence is unique, but this is an instance of the cross-translator limitation discussed in Section 8.1: variant transliterations of the same Sanskrit phonemes use different Chinese characters, making them invisible to character-level matching. The relationship between the Heart Sutra dharani and T901's version merits further study, as noted by Atwood and others.

#### T251 (Xuanzang): Novel material matches only derivative texts

T251's novel segments are more extensive (144 characters, 55% of jing text) because cross-translator matching captures less of the shared Prajnaparamita content. Searching these passages across the corpus:

| Novel Passage | Chars | Found in |
|---------------|------:|----------|
| 觀自在菩薩行 *Guānzìzai púsà xíng* ("Avalokitesvara Bodhisattva practicing...") | 6 | Commentaries on T251 only (T33n1702, T33n1714, T85n2747) |
| 照見五蘊皆空度一切苦厄 *zhàojiàn wǔyùn jiēkōng dù yīqiè kǔ è* ("perceived that the five aggregates are all empty, transcending all suffering") | 20 | Same commentaries + T39n1791, T47n1970 |
| 空即是色受想行識亦復如是...不增不減 *kōng jí shì sè... bùzēng bùjiǎn* ("emptiness is form... neither increasing nor decreasing") | 33 | Later Heart Sutra translations (T252, T253), commentaries, T07n0220 (partial) |
| 菩提薩埵依般若波羅蜜多 *pútísàduǒ yī bōrě bōluómìduō* ("the bodhisattva relies on Prajnaparamita") | 11 | Later translations (T252--T254), commentaries (T33n1710--14, T85n2746--47) |
| 心無罣礙...遠離顛倒夢想究竟涅槃三世諸佛依 *xīn wú guà'ài... yuǎnlí diāndǎo mèngxiǎng* ("mind without obstruction... far from inverted dreams, ultimately nirvana, relying on all Buddhas of the three times") | 28 | Later translations (T252, T253), commentaries |
| 是大神咒是大明咒是無上咒是無等等咒能除一切苦真實不虛 (*shì dà shénzhòu shì dà míngzhòu shì wúshàng zhòu shì wúděngděng zhòu néng chú yīqiè kǔ zhēnshí bùxū*, "is the great divine mantra, the great illuminating mantra, the unsurpassed mantra, the unequalled mantra, able to remove all suffering, true and not false") | 26 | **No** -- this specific phrasing is unique to T251; T18n0901 echoes it as 是大心呪 (*shì dàxīn zhòu*, "this is the great heart mantra") but with different wording |
| 揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶 *jiēdì jiēdì bānluó jiēdì bānluó sēng jiēdì pútí suōpóhē* (dharani: *gate gate pāragate pārasaṃgate bodhi svāhā*) | 19 | **No** at the character level -- T18n0901 contains the same dharani but with 波羅 *bōluó* for T251's 般羅 *bānluó* and different final syllables |

All matches fall into three categories: (1) later Heart Sutra translations from the Tang dynasty (T252 by Dharmacandra, T253 by Prajna, T254 by Prajnacakra), (2) Heart Sutra commentaries (T33n1710 by Kuiji, T33n1711 by Yuance, T33n1712 by Fazang, T33n1714 by Zongxie and Rujing), and (3) Dunhuang Heart Sutra manuscripts (T85n2746, T85n2747). None of these is a plausible source for T251; all are derivative.

We specifically investigated **T07n0220** (Xuanzang's own 600-fascicle Mahaprajnaparamita translation, 4.76 million characters) as a potential second source. While it contains some shared Prajnaparamita vocabulary (色不異空 *sè bù yì kōng*, "form is not different from emptiness"; 心無罣礙 *xīn wú guà'ài*, "mind without obstruction"), it **lacks all the distinctive Heart Sutra passages**: no 照見五蘊皆空 (*zhàojiàn wǔyùn jiēkōng*, "perceived the five aggregates are all empty"), no 遠離顛倒夢想 (*yuǎnlí diāndǎo mèngxiǎng*, "far from inverted dreams"), no 揭帝揭帝 (*jiēdì jiēdì*) dharani, no 是大神咒 (*shì dà shénzhòu*, "is the great divine mantra"). T07n0220 is not a source for T251's novel material.

We also checked **T25n1509** (Kumarajiva's Dazhidu lun, *Dàzhìdù lùn*, "Treatise on the Great Perfection of Wisdom," 2.85 million characters) as a potential source for T250's novel passages. It contains only generic Buddhist vocabulary (觀世音菩薩 *Guānshìyīn púsà*, "Avalokitesvara Bodhisattva"; 心無罣礙 *xīn wú guà'ài*, "mind without obstruction") but none of the distinctive T250 phrasing.

#### Implications for the Heart Sutra origins debate

Neither T250 nor T251 is a multi-source digest. The novel material in both texts is **not traceable to any other extant text** in the Taisho. Structurally, the novel passages serve a consistent function: they provide the **narrative wrapper** that transforms an excerpt from Prajnaparamita philosophical discourse into a self-contained sutra:

1. **Opening scene** -- Avalokitesvara practicing Prajnaparamita (no 如是我聞 *rúshì wǒ wén* "Thus have I heard" formula, no Buddha as speaker -- a highly unusual feature)
2. **Connective tissue** -- 心無罣礙 (*xīn wú guà'ài*, "mind without obstruction"), 遠離/離一切顛倒夢想 (*yuǎnlí/lí yīqiè diāndǎo mèngxiǎng*, "far from / free from all inverted dreams"), etc., linking the excerpted doctrinal passages
3. **Dharani and mantra description** -- the specific transliterations are unique to each version, though the underlying Sanskrit mantra (*gate gate pāragate pārasaṃgate bodhi svāhā*) also appears in T18n0901 under a different transliteration (see note above)
4. **Power attribution** -- 能除一切苦真實不虛 (*néng chú yīqiè kǔ zhēnshí bùxū*, "able to remove all suffering, true and not false"), identifying the teaching's soteriological function

The matched material is the **doctrinal core** (negation of skandhas, sense-bases, dependent origination, the four noble truths, wisdom, and attainment) drawn from the Prajnaparamita literature. The novel material is precisely the apparatus that an editor/compiler would need to add when constructing a standalone sutra from extracted philosophical material.

This structural pattern -- doctrinal core excerpted verbatim, narrative apparatus composed fresh -- is consistent with Nattier's Chinese-composition hypothesis. It is also compatible with derivation from a Sanskrit source (now lost or unrepresented in the Taisho) that itself shared its doctrinal core with the Prajnaparamita literature. What our analysis can establish is that no *Chinese* text other than T223 served as a source, and that the novel material was not borrowed from any identifiable text in the canon.

---

## 5. Notable Discoveries

### 5.1 Highest-Confidence Digest Relationships

The top results by confidence reveal several categories of textually significant relationships:

#### Verse Digests of Prose Treatises

Several of the highest-confidence results are verse summaries (song/ji) extracted from their parent prose treatises:

- **T24n1501 Pusajie ben (Bodhisattva Precepts Text) -> T30n1579 Yuqie shidi lun (Yogacarabhumi):** 97.0% coverage, confidence 0.784. The Bodhisattva Precepts chapter is almost entirely drawn from the Yogacarabhumi's vinaya sections. The alignment shows nearly 7,000 consecutive matching characters, indicating massive verbatim extraction.

- **T31n1603 Xianyangsheng jiaolun song (Verses Elucidating the Holy Teaching) -> T31n1602 Xianyangsheng jiaolun (Treatise Elucidating the Holy Teaching):** 99.0% coverage, confidence 0.749. The verse summary is almost character-for-character present in the parent treatise, with the alignment showing extensive exact matches spread across all 11 chapters.

- **T29n1560 Abhidharmakosha Verses -> T29n1558 Abhidharmakosha:** 99.5% coverage, confidence 0.740. Vasubandhu's famous verses are faithfully embedded in the prose commentary, as expected.

- **T31n1601 Bianzhongbian lun song (Verses Distinguishing the Middle from the Extremes) -> T31n1600 Bianzhongbian lun (Treatise Distinguishing the Middle from the Extremes):** 99.7% coverage, confidence 0.736.

- **T30n1570 Guangbailun ben (Shataka Verses) -> T30n1571 Guangbailun shi (Shataka Commentary):** 99.7% coverage, confidence 0.723.

While the relationship between verse root texts and their commentaries is well known to scholars, the pipeline's ability to detect and quantify these relationships with such precision provides computational confirmation of the traditional understanding and validates the methodology.

#### Encyclopedic Compilations as Source Reservoirs

The most striking pattern in our results concerns three Tang-dynasty encyclopedic compilations that appear as source texts for dozens of shorter works:

- **T53n2122 Fayuan zhulin (Forest of Gems in the Garden of the Dharma):** 102 digest relationships detected, including 17 at >80% coverage (many of them verbatim excerpts at or near 100%) and 85 digests. This 100-fascicle compilation by Daoshi (d. 683) quotes extensively from earlier sutras, and our pipeline detected these quotations in reverse -- finding that many shorter sutras have their full text present within the Fayuan zhulin.

- **T53n2121 Jinglü yixiang (Distinctive Features of Sutras and Vinayas):** 49 digest relationships detected, compiled by Baochang in 516 CE.

- **T54n2123 Zhujing yaoji (Essential Collection from Various Sutras):** 27 digest relationships detected, compiled by Daoshi as a companion to the Fayuan zhulin.

These results are not unexpected -- these texts are known to be compilations that incorporate earlier material. However, the systematic quantification of which texts are fully vs. partially absorbed is novel. The fact that texts like the Foshuo ma you ba tai pi ren jing (T02n0115, Sutra on Eight Attitudes of Horses, 98.3% coverage) are found virtually in their entirety within the Fayuan zhulin raises important questions about textual transmission: did Daoshi have access to independent manuscript traditions, or was he working from a version already close to what survives in the Taisho?

#### Short Sutras Embedded in Agama Collections

Several short independent sutras were found to be verbatim excerpts of passages within the larger Agama collections:

- **T14n0503 Biqiu bi nü e ming yu zi sha jing (Sutra on a Monk Avoiding a Woman's Slander) -> T02n0099 Samyuktagama:** 100% coverage. This short sutra about a monk avoiding a woman's bad reputation is entirely contained within the Samyuktagama -- a verbatim excerpt, not a condensed digest.

- **T14n0502 Fo wei nianshao biqiu shuo zheng shi jing (Sutra of the Buddha's Teaching to a Young Monk on Right Conduct) -> T02n0099 Samyuktagama:** 100% coverage. The sutra where the Buddha instructs a young monk is a direct extract.

- **T14n0499 Fo wei Azhiluojia ye zihua zuo ku jing (Sutra of the Buddha's Words to Ajirakāśyapa on Self-Inflicted Suffering) -> T02n0099 Samyuktagama:** 100% coverage. Another individual sutra that exists as a passage in the Samyuktagama.

- **T02n0128b Xumoti nü jing (Sutra of the Girl Sumatī) -> T02n0125 Ekottaragama:** 99.7% coverage.

- **T01n0061 Shou xin sui jing (Sutra on Receiving the New Year) -> T02n0125 Ekottaragama:** 99.7% coverage.

These results confirm what text-critical scholars have long suspected: many of the small independent sutras in the Taisho volumes 1--17 are in fact individual discourse excerpts that were at some point separated from their Agama context and transmitted independently. The pipeline provides systematic evidence for this on a scale not previously attempted.

#### Chan/Zen Literature Embedded in Transmission Records

- **T48n2010 Xinxin ming (Inscription on Faith in Mind) -> T51n2076 Jingde chuandeng lu (Record of the Transmission of the Lamp):** 100% coverage, confidence 0.717. The famous poem attributed to the Third Patriarch Sengcan is found as a complete excerpt within the Jingde Transmission of the Lamp record.

- **T48n2014 Yongjia zhengdao ge (Song of Enlightenment) -> T51n2076 Jingde chuandeng lu (Record of the Transmission of the Lamp):** 99.1% coverage, confidence 0.718. Yongjia Xuanjue's celebrated verse composition is likewise fully embedded as an excerpt.

- **T48n2010 -> T49n2036 Fozu lidai tongzai (Comprehensive Chronicle of Buddhas and Patriarchs):** 100% coverage, confidence 0.716. The Xinxin ming also appears in full in this later historical chronicle.

#### Vinaya (Monastic Rule) Derivatives

The Four-Part Vinaya (T22n1428, Dharmaguptaka Vinaya) serves as the source for an extensive network of derivative texts:

- T22n1431 (Bhikkhuni Precepts): 81.0% coverage
- T22n1434 (Bhikkhuni Karmavacana): 66.5% coverage
- T22n1429 (Bhikkhu Precepts): 65.8% coverage
- T22n1432 (Miscellaneous Karmavacana): 69.7% coverage
- T22n1430 (Sangha Precepts): 66.3% coverage
- T22n1433 (Karmavacana): 68.3% coverage

Plus 5 additional digest relationships with Daoxuan's later vinaya commentaries.

Similarly, the Mulasarvastivada Vinaya (T23n1442, T23n1443) and its derivative precept texts show the same pattern. The pipeline maps the full derivation network for these vinaya traditions in a way that, to our knowledge, has not been computationally quantified before.

### 5.2 Multi-Source Digests

The 63 detected multi-source digests include several noteworthy cases:

**T21n1237 Azhapo ju guishen dajiang shang fo tuoluoni shenzhou jing (Dhāraṇī Incantation Sutra of Āṭavaka, Great General of Ghost-Spirits):** 99.4% combined coverage from T21n1336 (81.6%) and T21n1238 (74.9%). Nearly the entire text is accounted for by material from two dharani collections.

**T17n0724 Foshuo zuiye yingbao jiaohua diyu jing (Sutra on Karmic Retribution):** 96.0% combined coverage from T53n2122 (84.3%), T54n2123 (82.9%), T45n1909 (67.8%), and T14n0441 (41.1%). This short sutra on hell and karmic retribution is almost entirely present across four different larger compilations.

**T22n1429 Sifenlü biqiu jieben (Four-Part Bhikkhu Precepts):** 93.2% combined coverage from T40n1806, T22n1428, and T85n2787. The precepts text draws from multiple vinaya-related sources.

**T16n0686 Foshuo baoen fengpen jing (Sutra on Repaying Kindness with the Bowl):** 95.6% combined coverage from commentary and encyclopedia sources.

**T85n2747 Interlinear Heart Sutra:** 97.0% combined coverage from five different Heart Sutra commentaries and translations, confirming its character as an annotated edition drawing from multiple sources.

### 5.3 Dharani Collection Networks

The Tuoluoni zaji (*Tuóluóní zájí*, T21n1336, Miscellaneous Dharani Collection) functions as a reservoir text for dharani literature much as the Fayuan zhulin does for sutra literature. Sixteen shorter dharani texts were found to be excerpts or digests of T21n1336, with coverage ranging from 100% down to 43%. Similarly, the Tuoluoni jijing (*Tuóluóní jí jīng*, T18n0901, Dharani Collection Sutra) serves as a source for 13 shorter ritual and dharani texts.

The two derivation networks are shown below. Arrows point from source to derivative; percentages indicate coverage (fraction of the shorter text found in the source).

**T21n1336 (Miscellaneous Dharani Collection) derivation network:**

```
                   T21n1336  (Tuoluoni zaji)
                   =========================
                  /            |             \
          Excerpts       Excerpt/retrans.     Digests
          (100-87%)         (85-82%)         (80-43%)
              |                |                |
    T21n1368 (100%)    T21n1332 (85%)    T19n1029 (80%)
    T20n1046 (100%)    T21n1391 (85%)    T21n1393 (69%)
    T20n1138b (100%)   T21n1237 (82%)    T21n1327 (62%)
    T21n1367 (100%)                      T21n1329 (56%)
    T21n1352 (100%)                      T21n1353 (44%)
    T12n0370 (100%)                      T20n1178 (43%)
    T19n1028A (99%)
    T21n1326 (87%)
```

**T18n0901 (Dharani Collection Sutra) derivation network:**

```
                   T18n0901  (Tuoluoni jijing)
                   ============================
                  /            |              \
          Excerpts          Digests        Commentaries
           (84-81%)        (71-32%)         (49-30%)
              |                |                |
    T20n1073 (84%)    T21n1254 (71%)    T21n1256 (49%)
    T20n1035 (81%)    T20n1070 (65%)    T21n1255b (30%)
                      T20n1074 (60%)
                      T20n1180 (58%)
                      T20n1110 (55%)
                      T21n1338 (54%)
                      T21n1255a (52%)
                      T21n1266 (51%)
                      T19n0924B (49%)
                      T20n1084 (38%)
                      T21n1291 (32%)
```

This systematic mapping of dharani text derivation networks appears to be a novel contribution. While individual dharani texts have been studied in relation to their sources, the comprehensive identification of which dharani collections served as "parent" repositories for which shorter texts has not, to our knowledge, been previously published.

### 5.4 Phonetic Transliteration Detection

The phonetic detection stage identified 634 text pairs containing 2,881 individual phonetic match segments -- passages where different Chinese characters encode the same Sanskrit sounds. This represents the first corpus-wide computational detection of cross-transliterator relationships in Chinese Buddhist literature.

#### The T250/T901 Dharani Connection

The most illustrative result is the phonetic link between the Heart Sutra (T08n0250) and the Dharani Collection Sutra (T18n0901). The Heart Sutra's dharani -- 竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵 (*jiédì jiédì bōluó jiédì bōluó sēng jiédì pútí sēng suōhē*) -- encodes the Sanskrit *gate gate pāragate pārasaṃgate bodhi svāhā*. The same mantra appears in T901 under a different transliteration: 揭帝揭帝波羅揭帝波囉僧揭帝菩提莎訶. Character-level matching detects no relationship because the characters differ (竭 vs. 揭, 呵 vs. 訶). Phonetic matching identifies them as equivalent because both characters map to the same Sanskrit syllable *ga* through the DDB transliteration table.

This phonetically-detected relationship confirms computationally what scholars have noted through close reading: that different Chinese translators systematically used different character sets for the same Sanskrit sounds, and that the Heart Sutra dharani belongs to a broader family of Prajnaparamita dharani transliterations preserved across multiple texts in the Taisho.

#### Cross-Transliterator Variation at Scale

Beyond dharani passages, the 634 phonetically-linked pairs reveal the pervasiveness of transliteration variation across the corpus. Phonetic match segments appear in 25% of digest relationships, 31% of commentary relationships, and 24% of retranslation pairs. These segments typically correspond to transliterated proper names (bodhisattvas, buddhas, places), technical terms, and ritual formulae where different translators rendered the same Sanskrit content using different Chinese character choices.

The enrichment of commentary and retranslation categories is particularly noteworthy. When a commentary quotes a text translated by a different translator, the quotation may use different transliteration characters for names and terms, causing character-level matching to undercount the actual overlap. Phonetic matching recovers some of this lost coverage, though the effect is modest (typically 1--3 percentage points of additional coverage per pair).

---

## 6. Patterns and Observations

### 6.1 Taisho Volume Distribution

The digest relationships are not uniformly distributed across the Taisho. Preliminary observation reveals several concentration patterns:

**Volumes most heavily involved as source texts:**
- T02 (Agama section): The Samyuktagama (T99) and Ekottaragama (T125) serve as sources for multiple independent short sutras
- T22--T24 (Vinaya section): The major vinaya texts generate extensive derivative networks of precept texts, karmavacana procedures, and commentaries
- T30--T31 (Yogacara treatises): The Yogacarabhumi (T1579) and Xianyangsheng jiaolun (Treatise Elucidating the Holy Teaching, T1602) are sources for verse summaries and derivative treatises
- T53--T54 (Encyclopedic compilations): The Fayuan zhulin and companion texts serve as the most prolific source texts in the entire corpus

**Volumes most heavily involved as digest texts:**
- T01--T04 (Agama and Jataka): Many short independent sutras are digests of larger collections
- T14 (Miscellaneous short sutras): Extremely high density of digest relationships, with many texts being extracts from encyclopedic compilations
- T17 (Miscellaneous short sutras): Similar pattern to T14
- T19--T21 (Dharani and ritual texts): Extensive derivation networks from dharani collections
- T85 (Dunhuang manuscripts): Several Dunhuang texts are digests of or closely related to canonical texts

### 6.2 Same-Translator vs. Cross-Translator Patterns

The Heart Sutra validation case provides a clear demonstration of how translator identity affects detection. The Kumarajiva Heart Sutra (T250) shows 73.2% coverage against Kumarajiva's own Prajnaparamita translation (T223), while the Xuanzang Heart Sutra (T251) shows only 44.6% against the same T223, despite both Heart Sutras deriving from the same underlying Prajnaparamita material.

This approximately 30-percentage-point gap between same-translator and cross-translator coverage is a systematic feature of the pipeline. It means our coverage thresholds are effectively tuned for same-translator relationships, and **cross-translator digest relationships are likely underdetected.** Many pairs classified as "digest" or "shared tradition" may in fact represent excerpt relationships obscured by translator-dependent phrasing differences.

The retranslation detection feature partially compensates for this by identifying pairs of comparable length with moderate overlap, but genuine cross-translator digest relationships (short text from translator A derived from a source translated by translator B) remain difficult to detect at the character level.

### 6.3 The Lotus Sutra Retranslation Network

The pipeline detected the Kumarajiva Lotus Sutra (T09n0262) and the Tianpin Lotus Sutra (T09n0264) as retranslations with 92.0% coverage and confidence 0.735, ranked 15th overall. This well-known retranslation pair serves as additional validation. The high coverage reflects the fact that T264 is a revised and supplemented version of T262.

### 6.4 Commentary vs. Digest Disambiguation

The pipeline's distinction between commentary (many short quotations with added material) and digest (fewer, longer extracted passages) is a useful heuristic but not always clean. The 669 commentary classifications likely include genuine commentarial quotation patterns, but also cases where a digest relationship has been fragmented by editorial differences. The average segment length threshold of 10 characters for commentary classification is a rough heuristic that deserves further refinement.

### 6.5 Shared Tradition Inflation from Phonetic Candidates

The most dramatic change in the current results compared to character-level-only analysis is the increase in shared tradition relationships from approximately 1,200 to 5,589. This increase is almost entirely attributable to phonetic candidate generation (Stage 2b), which produced 4,780 shared tradition classifications.

The mechanism is straightforward: the phonetic fingerprinting identifies pairs of texts that share transliterated Sanskrit terms in their transliteration regions. Because many of the same Chinese characters used for Sanskrit transliteration (e.g., 薩 *sà* in 菩薩 *púsà* "bodhisattva," 羅 *luó* in 波羅蜜 *bōluómì* "pāramitā") are pervasive in Buddhist prose, the phonetic fingerprinting effectively functions as a broad Buddhist text similarity detector. When these phonetically-matched pairs are aligned at the character level, they typically show 10--30% textual overlap from shared Buddhist formulae and stock phrases -- enough to cross the shared tradition threshold, but reflecting general Buddhist vocabulary overlap rather than direct textual derivation.

The coverage distribution of shared tradition relationships illustrates this:

| Coverage Range | Count | Percentage |
|---------------|------:|----------:|
| 10--15% | 2,583 | 46.2% |
| 15--20% | 1,548 | 27.7% |
| 20--25% | 933 | 16.7% |
| 25--30% | 525 | 9.4% |

Nearly half of all shared tradition pairs have coverage between 10--15%, barely above the minimum threshold. These represent texts that share some common Buddhist language but have no evidence of direct textual relationship.

**Interpretation.** The shared tradition category should be understood as a catch-all for low-level textual similarity. The inflated count from phonetic matching is a genuine measurement of textual overlap, but it does not indicate derivation or deliberate reuse. For analyses focused on digest and excerpt relationships, the shared tradition category can be excluded; the higher-confidence categories (excerpt, digest, retranslation, commentary) total 1,580 relationships and are only modestly affected by phonetic matching (+6, +16, -64, +48 respectively compared to character-only analysis).

---

## 7. What May Be Previously Unknown

While many of the individual relationships detected are known to traditional Buddhist scholarship, several aspects of our findings may contribute new knowledge:

### 7.1 Systematic Quantification of Encyclopedic Absorption

The comprehensive mapping of how the Fayuan zhulin (T53n2122) absorbed 102 texts -- with precise coverage percentages ranging from 30% to 100% -- appears to be unprecedented. While scholars have known that this encyclopedia quotes extensively from earlier sources, the systematic identification of which texts are fully incorporated as excerpts (17 texts at >80% coverage) vs. partially absorbed (85 texts at 30--80% coverage) provides a new level of granularity for studying Daoshi's compilation methods. Particularly noteworthy:

- **T15n0615 Pusa he seyu fa jing (Sutra on the Bodhisattva's Reproach of Sensual Desire):** 100% coverage in the Fayuan zhulin. This entire short text on monastic attitudes toward desire is found verbatim as an excerpt within Daoshi's compilation, suggesting either direct copying or shared manuscript traditions.
- **T32n1689 Qing Bintoulou fa (Inviting Pindola):** 99.4% coverage.
- **T12n0332 Foshuo Youtian wang jing (Sutra of King Udayana):** 99.4% coverage.

### 7.2 Agama Extract Identification

The systematic identification of short independent sutras that are extracts from the Samyuktagama and Ekottaragama provides computational support for text-critical hypotheses that have often been argued on a case-by-case basis. The pipeline identified at least 7 texts with >80% coverage in the Agamas and many more in the 30--80% range. Scholars working on Agama studies can use these results to prioritize texts for closer philological examination.

### 7.3 Dharani Derivation Networks

The mapping of how T21n1336 (Dharani Miscellany) and T18n0901 (Dharani Collection Sutra) serve as reservoir texts for dozens of shorter dharani texts is, to our knowledge, a novel systematic finding. While individual dharani texts have been studied, the comprehensive view of derivation networks across the entire dharani literature of the Taisho has not previously been published.

### 7.4 Unexpected Cross-Genre Relationships

Several detected relationships cross traditional genre boundaries:

- **T48n2010 Xinxin ming -> T48n2023 Yuanren lun (Treatise on the Origin of Humanity):** 100% coverage. The famous Chan poem attributed to Sengcan appears as a complete excerpt within Zongmi's treatise on the origin of humanity. While Zongmi's use of earlier Chan texts is known, the complete embedding of the Xinxin ming in this context may not have been previously quantified.

- **T85n2918 Shijia guanhua huan yu jing (Sutra of Śākyamuni's Parables of Illusory Transformation) -> T04n0211 Faju piyu jing:** 100% coverage, confidence 0.704. This Dunhuang text is a verbatim excerpt from the Dhammapada with Parables (Faju piyu jing), suggesting it is an extract rather than an independent composition.

- **T12n0369 Amituo fo shuo zhou (Dhāraṇī Spoken by Amitābha Buddha) -> T85n2827 Jingtu wuhui nianfo song jing guanxing yi (Liturgical Manual for Five-Assembly Pure Land Buddha-Recitation):** 96.6% coverage. A short Amitabha dharani text is almost entirely present within a Pure Land liturgical manual, illuminating how ritual texts were compiled from earlier dharani sources.

### 7.5 Yogacara Treatise Derivation Chain

The pipeline reveals a clear derivation chain within the Yogacara scholastic tradition:

1. T30n1579 Yogacarabhumi (source)
2. T31n1602 Xianyangsheng jiaolun (Treatise Elucidating the Holy Teaching; draws from Yogacarabhumi)
3. T31n1603 Xianyangsheng jiaolun song (verse summary of T1602)
4. T24n1501 Bodhisattva Precepts (extracted from Yogacarabhumi vinaya section)
5. T85n2783 Dacheng daoqie jing suitingshu jue (Lecture Notes on the Mahāyāna Yogācāra Sūtra; 97.3% from Yogacarabhumi)
6. T16n0676 Jieshenmi jing (Sūtra Unraveling the Thought, Saṃdhinirmocana; 86.5% from Yogacarabhumi)
7. T31n1615 Wangfa zhengli lun (Treatise on the Correct Principles of Governance; 62.9% from Yogacarabhumi)

The Yogacarabhumi emerges as one of the most generative source texts in the entire Taisho, with 6 detected derivative texts at >50% coverage. The pipeline provides precise quantification of how much of each derivative text comes from this single massive source.

### 7.6 Bibliographic Catalog Relationships

The pipeline detected the expected cascade of medieval Chinese Buddhist bibliographic catalogs:

- T55n2154 Kaiyuan shijiao lu (Catalogue of Buddhist Teachings of the Kaiyuan Era) -> T55n2155 Kaiyuan shijiao lu lüechu (Abridged Kaiyuan Catalogue) (73.9% coverage)
- T55n2154 -> T55n2157 Zhenyuan xinding shijiao mulu (Catalogue of Buddhist Teachings of the Zhenyuan Era) (absorbed into the later catalog)
- T55n2152 Xu gujin yijing tuji (Continuation of the Record of Translated Scriptures) is a digest of both T55n2154 (75.1%) and T55n2157 (77.0%)

While the relationships among these catalogs are known, the precise coverage measurements may help scholars assess the degree of editorial independence in each successive catalog.

---

## 8. Limitations

### 8.1 Character-Level Matching with Phonetic Extension

The pipeline primarily operates at the character level, detecting verbatim or near-verbatim textual overlap. The phonetic transliteration detection (Stages 2b and 3) partially extends this to cross-transliterator relationships, but only for passages long enough to form phonetic seeds (5+ characters). The pipeline still cannot detect:

- **Paraphrase-level reuse:** Where an author restates the same ideas in entirely different words
- **Structural borrowing:** Where a text follows the same organizational pattern without verbal overlap
- **Translation-level relationships:** Cross-translator digest relationships remain systematically underdetected for prose content, as demonstrated by the ~30% coverage gap between same-translator (T250->T223: 73%) and cross-translator (T251->T223: 45%) Heart Sutra comparisons. Phonetic matching helps with transliterated passages (dharani, names, technical terms) but not with translated prose.
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

### 8.7 Phonetic Detection Limitations

The phonetic transliteration detection has several inherent limitations:

- **High false positive rate in region detection.** The density-based transliteration region detector identifies regions where characters from the phonetic table cluster. However, many common Buddhist terms (菩薩 *púsà*, 般若 *bōrě*, 涅槃 *nièpán*) use characters that appear in the transliteration table, causing the detector to flag ordinary prose as "transliteration regions." In one measured case, the detector identified 36% of a 286,000-character sutra as transliteration content when actual dharani passages comprised less than 0.1%. The XML-annotated dharani ranges from CBETA TEI markup are far more reliable.

- **Performance cost.** The phonetic rescan of novel segments (Stage 3, Step 5) consumes approximately 87% of alignment time for pairs involving large source texts. This is because the rescan builds a syllable-to-position index over the entire source text and searches it exhaustively for each novel segment. For a 286K-character source, this takes approximately 0.85 seconds per pair -- and with thousands of such pairs, the aggregate cost dominates pipeline runtime. Restricting the phonetic index to XML-annotated dharani ranges (rather than the full source text) would dramatically reduce this cost with minimal impact on detection quality.

- **Transliteration table coverage.** The DDB-derived table covers 559 characters and approximately 200 syllable groups. This is not exhaustive -- rare or archaic transliteration characters may be missing, and the table does not account for regional variation in character-to-sound mappings across different time periods and geographic areas of Chinese Buddhist translation.

- **Seed length tradeoff.** The minimum phonetic seed length of 5 characters prevents false positives from common short Buddhist terms but may miss genuine phonetic relationships in very short transliterated passages (e.g., 2--3 character proper name variants).

---

## 9. Future Directions

### 9.1 Chronological Analysis

Incorporating dated translator and author information (available from CBETA metadata and traditional Buddhist bibliographic catalogs) would allow the pipeline to assess the chronological plausibility of detected relationships. A digest detected from a text attributed to a 3rd-century translator to a source attributed to a 7th-century compiler is likely a reverse relationship (the compiler quoted the earlier text).

### 9.2 Cross-Translator Compensation

Developing a translation-aware matching algorithm -- perhaps using character embedding similarity rather than exact character matching -- could improve detection of cross-translator digest relationships. The known Heart Sutra case provides a calibration benchmark: the true coverage should be similar regardless of translator, but our character-level method detects 73% vs. 45%.

### 9.3 Network Visualization

The 7,169 detected relationships define a complex textual network. Graph analysis could reveal:
- Community structure (clusters of closely related texts)
- Hub texts (high betweenness centrality, connecting otherwise separate textual traditions)
- Transmission pathways (chains of digest relationships)

### 9.4 Expanded Validation

Ground truth validation could be expanded beyond the Heart Sutra case to include:
- The Diamond Sutra and its known commentary tradition
- The vinaya precepts and their known derivation from full vinaya texts
- Known retranslation pairs from Buddhist bibliographic catalogs (Kaiyuan lu classifications)

### 9.5 Sanskrit/Tibetan Cross-Reference

A multi-canon concordance has now been compiled from five independent sources (SuttaCentral, 84000, Lancaster catalogue, CBETA Jinglu, and manual scholarship), mapping 941 Taisho texts to Tibetan, Sanskrit, and/or Pali parallels. This concordance has been cross-referenced against the digest detection results; the analysis is presented in Section 10 below. Further expansion of this concordance -- particularly through additional Tibetan canonical catalogues and Sanskrit manuscript databases -- could increase coverage beyond the current 38%.

### 9.6 Expansion Beyond Volume T

The current analysis covers only the "T" (main Taisho) volumes. Extending to the Xu zangjing (supplementary collection) and other CBETA-digitized collections could reveal additional relationships.

### 9.7 Phonetic Detection Refinement

Several improvements to the phonetic detection are possible:

- **Restrict phonetic source indexing to dharani ranges.** The current phonetic rescan indexes the entire source text, but phonetic matches can only occur in transliteration regions. Restricting the source index to XML-annotated dharani ranges would reduce Stage 3 runtime dramatically (estimated 5--10x speedup) while preserving detection quality for genuine dharani relationships. For a 286K-character source with 289 characters of annotated dharani content, this would reduce the index from hundreds of thousands of entries to hundreds.

- **Cythonize phonetic inner loops.** The `_find_phonetic_seeds` and `are_phonetically_equivalent` functions are tight character-comparison loops similar to the already-Cythonized `fast_find_seeds` and `fast_fuzzy_extend`. Implementing them in Cython would provide an additional constant-factor speedup.

- **Tune phonetic candidate thresholds.** The current phonetic containment threshold of 0.25 produces 22,467 candidates, 78% of which yield no detectable relationship. Raising this threshold (or adjusting the phonetic stopgram filter) would reduce the candidate count and the shared tradition inflation at the cost of potentially missing marginal phonetic relationships.

### 9.8 Scholarly Review of Novel Findings

The most promising direction is expert review of the potentially novel findings, particularly:
- The 58 multi-source digests (are these genuinely composite texts?)
- High-confidence relationships involving understudied texts (T14 and T17 miscellaneous sutras)
- The dharani derivation networks (do these reflect genuine textual history or artifact of how dharani literature was compiled?)
- The 30 phonetically-detected high-confidence relationships (do these represent genuine cross-transliterator derivation?)
- Dunhuang texts detected as digests of canonical texts (can this help date or provenance Dunhuang manuscripts?)

---

## 10. Cross-Canon Concordance

### 10.1 Concordance Sources and Coverage

A concordance of Taisho texts with parallels in the Tibetan, Pali, and Sanskrit traditions was compiled from eight independent data sources:

| Source | Data Provided | Texts Covered |
|--------|--------------|--------------|
| SuttaCentral parallels.json | Pali sutta parallels, Sanskrit fragment IDs | ~500 |
| 84000 data-tei (Kangyur) | Tohoku numbers for translated texts | ~350 |
| Lancaster Korean Buddhist Canon catalogue | Tohoku and Taisho cross-references | ~590 |
| Lancaster full K-number catalogue | Complete K-number scrape with all cross-refs | ~1,478 |
| CBETA Jinglu Tibetan catalogue | Tohoku, Nanjio, and Sanskrit titles | ~613 |
| CBETA Jinglu Sanskrit/Pali catalogue | Tohoku, Otani, and Nanjio numbers | ~703 |
| acmuller Tohoku→K→Taisho index | Tohoku-to-Taisho mappings via K numbers | ~560 |
| rKTs kernel (Vienna) | Kanjur Taisho cross-references | ~23 |

The combined concordance covers 954 of 2,455 unique Taisho texts (38.9%):

| Parallel Tradition | Texts with Parallel | Coverage |
|-------------------|--------------------:|--------:|
| Sanskrit | 859 | 35.0% |
| Tibetan | 733 | 29.9% |
| Pali | 75 | 3.1% |
| **Any parallel** | **954** | **38.9%** |
| No known parallel | 1,501 | 61.1% |

The relatively low Pali coverage reflects the fundamental difference between the Theravada and Chinese Mahayana canons; the 75 texts with Pali parallels are concentrated in the Agama section (volumes 1--2), which overlaps with the Pali Nikayas.

### 10.2 Cross-Referencing Digest Results

Of the 1,814 unique texts involved in the 7,169 detected relationships, a substantial proportion have at least one known parallel in another tradition. This is modestly higher than the corpus-wide rate of 38.9%, suggesting that texts involved in intra-Chinese textual relationships are also somewhat more likely to have cross-canon parallels -- as expected, since widely transmitted Indic texts tend to generate both retranslations and derivative works.

| Parallel Type | Texts | % of 1,814 |
|--------------|------:|-----------:|
| Any parallel | 622 | 44.1% |
| Sanskrit | 541 | 38.3% |
| Tibetan | 487 | 34.5% |
| Pali | 75 | 5.3% |

At the relationship level, at least one text in the pair has a known parallel in a substantial majority of the 7,169 relationships. The high proportion of shared tradition pairs (most from phonetic candidate generation) means that many low-confidence relationships involve texts that share Buddhist vocabulary without having known cross-canon parallels.

**Coverage by classification type** (at least one text in the pair has a parallel):

| Classification | Total | With Parallel | % |
|----------------|------:|--------------:|----:|
| Commentary | 621 | 503 | 81.0% |
| Retranslation | 288 | 193 | 67.0% |
| Shared Tradition | 1,238 | 798 | 64.5% |
| Excerpt | 132 | 81 | 61.4% |
| Digest | 533 | 274 | 51.4% |

The high parallel rate for commentaries (81.0%) reflects the fact that commentarial literature tends to focus on important translated texts that are well-attested across traditions. Retranslations also show high parallel rates (67.0%), as expected -- parallel translations from the same Indic source are likely to have that source attested in other canons as well.

Conversely, the lower rates for excerpts (61.4%) and digests (51.2%) may indicate that digest relationships are more common among texts without well-known Indic originals -- potentially including Chinese-origin compositions, compilations, and texts from traditions less well-represented in the Tibetan and Pali canons.

### 10.3 Retranslation Validation via Tibetan Parallels

The concordance provides an independent check on the pipeline's retranslation detection. If two Chinese texts are correctly identified as retranslations (parallel translations from the same Indic source), they should map to the same entry in the Tibetan Kangyur -- since the Tibetan translation would also derive from the same source.

Of the 224 detected retranslations:

| Tibetan Parallel Status | Count | % |
|------------------------|------:|----:|
| Shared Tibetan ID (validated) | 88 | 30.6% |
| Different Tibetan parallels | 6 | 2.1% |
| Only one text has Tibetan parallel | 71 | 24.7% |
| Neither text has Tibetan parallel | 123 | 42.7% |

**88 retranslation pairs (30.6%) are independently confirmed** by sharing at least one Tohoku or Otani catalogue number. This is a strong validation signal: the pipeline's character-level analysis of Chinese texts identified these as parallel translations, and an entirely independent dataset (Tibetan canonical catalogues) confirms they derive from the same Indic source.

Among the 87 validated pairs, notable examples include:

| Digest | Source | Coverage | Shared Tibetan ID |
|--------|--------|--------:|-------------------|
| T09n0262 (Lotus Sutra, Kumarajiva) | T09n0264 (Lotus, Jnanagupta/Dharmagupta) | 92.0% | Toh 113, Otani 781 |
| T16n0663 (Samdhinirmocana, Bodhiruci) | T16n0664 (Samdhinirmocana, Xuanzang) | 89.8% | Toh 555--557, Otani 174--176 |
| T12n0334 (Smaller Sukhavativyuha) | T12n0335 (Smaller Sukhavativyuha) | 89.2% | Toh 74 |
| T19n1013 (Ushnishavijaya Dharani) | T19n1015 (Ushnishavijaya Dharani) | 85.3% | Toh 140, 525, 914 |
| T12n0362 (Amitayurdhyana Sutra) | T12n0361 (Amitabha Sutra) | 79.9% | Toh 49, Otani 760 |

A notable related case is T250 (Heart Sutra) and T223 (Prajnaparamita), which share Toh 21 in the Tibetan canon. While classified as a digest rather than a retranslation in our pipeline (due to their extreme length asymmetry), the shared Tohoku number confirms their common Indic ancestry through a completely independent data source.

**6 retranslation pairs (2.1%) have different Tibetan parallels.** These are not necessarily errors -- they may represent cases where the Tibetan canon catalogued the texts under different entries despite shared Indic ancestry, or where the Chinese and Tibetan cataloguing traditions diverge. All 6 cases involve Yogacara or Prajnaparamita literature where catalogue boundaries are known to be fluid:

| Digest | Source | Coverage | Digest Tibetan | Source Tibetan |
|--------|--------|--------:|---------------|---------------|
| T31n1605 | T31n1606 | 83.2% | Toh 4049 | Toh 4054 |
| T31n1597 | T31n1598 | 49.8% | Toh 4050 | Toh 4051 |
| T08n0227 | T08n0221 | 35.4% | Toh 12 | Toh 9 |
| T08n0226 | T08n0222 | 34.6% | Toh 12 | Toh 9 |
| T10n0286 | T26n1522 | 43.6% | Toh 44 | Toh 3993 |
| T08n0236a | T25n1510a | 36.8% | Toh 16 | Toh 3816 |

The Prajnaparamita cases (T08 texts mapping to Toh 9 vs. Toh 12) are particularly illuminating: these represent different *lengths* of the Prajnaparamita sutra (the 8,000-verse and 25,000-verse versions), which are distinct texts in the Tibetan catalogue but share extensive content due to their common tradition. The pipeline correctly detects the textual overlap, and the different Tohoku numbers correctly reflect the Tibetan cataloguing distinction.

### 10.4 Implications

The cross-reference analysis yields several methodological and substantive findings:

**Independent validation of retranslation detection.** The 30.6% confirmation rate (88 of 288) is limited by concordance coverage -- 42.7% of retranslation pairs have no Tibetan parallel data for either text. Among the 165 pairs where at least one text has a Tibetan parallel, 53.3% are validated by a shared catalogue number. Among the 94 pairs where both texts have Tibetan parallels, 93.6% share at least one catalogue number. The near-total validation rate when data is available (93.6%) strongly supports the pipeline's retranslation detection accuracy.

**Texts without parallels may be Chinese-origin.** The 963 relationships (34.2%) where neither text has a known cross-canon parallel are enriched for Chinese-origin literature: encyclopedic compilations, indigenous commentaries, and texts from traditions (dharani collections, Chan literature) that are less well-represented in the Tibetan and Pali canons. These relationships are the most likely to reveal previously unrecognized Chinese compositional practices.

**Digest texts with Tibetan parallels deserve closer attention.** Among the 319 relationships where both texts share a Tibetan parallel, 8 are classified as excerpts and 24 as digests. These cases are particularly interesting because they suggest that a shorter Chinese text, which our pipeline identifies as derived from a longer Chinese source, may also have an independent Indic pedigree. For example, if text A is detected as an excerpt of text B, but both map to the same Tohoku number, the apparent "excerpt" relationship may in fact reflect parallel translation from the same source rather than Chinese-level extraction.

**The concordance can prioritize further investigation.** Texts involved in digest relationships that have Tibetan parallels are natural candidates for comparative philological study, as the Tibetan version can help disambiguate whether the Chinese relationship reflects direct textual derivation or independent translation from a common source.

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
| Excerpt threshold | 0.80 | Coverage for excerpt classification |
| Digest threshold | 0.30 | Coverage for digest classification |
| Shared tradition threshold | 0.10 | Minimum coverage for any relationship |
| Retranslation size ratio | 3.0 | Maximum ratio for retranslation classification |
| Commentary avg seg length | 10 | Below this, classify as commentary |
| Phonetic seed length | 5 | Minimum phonetically equivalent characters for seed |
| Phonetic n-gram size | 3 | Syllable n-gram size for phonetic fingerprinting |
| Min phonetic containment | 0.25 | Minimum phonetic containment for candidate |
| Phonetic stopgram doc freq | 0.05 | Exclude syllable n-grams in >5% of texts |
| Phonetic max syllables | 5 | Max syllable readings per character (ambiguity cap) |
| Min transliteration length | 10 | Minimum transliteration region size (characters) |

## Appendix B: Source Code

The complete pipeline source code is organized in the following modules:

- `digest_detector/extract.py` -- Stage 1: XML parsing and text extraction
- `digest_detector/fingerprint.py` -- Stage 2a: N-gram fingerprinting
- `digest_detector/candidates.py` -- Stage 2a/2b: Candidate pair generation (character + phonetic)
- `digest_detector/phonetic.py` -- Stage 2b/3: Phonetic transliteration detection (DDB table, syllable mapping, equivalence testing)
- `digest_detector/align.py` -- Stage 3: Seed-and-extend alignment with phonetic rescan
- `digest_detector/score.py` -- Stage 4: Scoring and classification
- `digest_detector/report.py` -- Stage 5: Report generation
- `digest_detector/pipeline.py` -- Main pipeline orchestrator
- `digest_detector/config.py` -- All tunable parameters
- `digest_detector/models.py` -- Data models
- `digest_detector/cache.py` -- Disk cache for Stages 1--2b results
- `digest_detector/fast.py` -- Cython/fallback import router
- `digest_detector/_fast.pyx` -- Cython C extensions for hot-path functions
- `digest_detector/_fast_fallback.py` -- Pure-Python fallback implementations

Test suite: 245 tests covering all stages, phonetic detection, parallel equivalence, caching, and integration tests on T250/T251 -> T223.

---

*Analysis conducted February 2026 using the CBETA TEI P5b XML corpus of the Taisho Tripitaka.*
