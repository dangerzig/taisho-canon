# Tibetan-Chinese Match Spot-Check Analysis

Date: 2025-02-25
Source: `results/tibetan_chinese_matches.json`
Total matches: 620 (103 high-confidence >= 90, 517 medium-confidence 60-89)

---

## 1. Confidence Distribution of Medium-Confidence Matches

| Bin   | Count | Bar                               |
|-------|------:|-----------------------------------|
| 60-64 |     0 |                                   |
| 65-69 |     5 | ##                                |
| 70-74 |    20 | ########                          |
| 75-79 |   124 | ################################################# |
| 80-84 |   163 | ################################################################# |
| 85-89 |   205 | #################################################################################### |

The distribution is heavily right-skewed: 71% of medium-confidence matches (368/517) score 80-89, just below the high-confidence threshold. Only 5 matches score below 70. This suggests the LLM is generally confident about its positive verdicts, and the 60-89 "medium" band is really dominated by the 75-89 range.

### Without cbeta_id=865 (the generic "dharani" entry)

| Bin   | Count |
|-------|------:|
| 60-64 |     0 |
| 65-69 |     5 |
| 70-74 |    20 |
| 75-79 |   104 |
| 80-84 |   115 |
| 85-89 |   123 |

Removing the 150 medium-confidence matches from cbeta_id=865 flattens the distribution noticeably in the 80-89 range, indicating that the 865 matches are disproportionately scoring in the upper medium band.

---

## 2. Distinct CBETA Entries

**Total distinct CBETA entries in matches: 271**

### CBETA entries matching >5 Taisho texts

| cbeta_id | Tibetan Chinese Title | Matches |
|----------|----------------------|--------:|
| 865      | 陀羅尼               | **183** |
| 4363     | 法門                 | 12      |
| 1979     | 成就儀軌             | 10      |
| 3822     | 般若波羅蜜多心（經）義正知 | 7  |
| 568      | 聖有勝陀羅尼         | 6       |
| 3101     | 護摩                 | 6       |

**cbeta_id=865 is by far the most problematic entry.** It is a single Tibetan catalogue entry titled simply "陀羅尼" (dharani) with no Sanskrit title. This single generic entry has been matched to 183 distinct Taisho texts -- **29.5% of all 620 matches**. While each individual Taisho text IS a dharani text, the Tibetan entry is too generic to constitute a meaningful cross-reference. It is essentially saying "some dharani in the Tibetan canon corresponds to some dharani in the Chinese canon" without identifying which specific text maps to which.

Similarly, cbeta_id=4363 ("法門", Dharmaparyaya) is a generic title that has been matched to 12 unrelated sutras that happen to contain 法門 in their titles. cbeta_id=1979 ("成就儀軌", sadhana ritual) and cbeta_id=3101 ("護摩", homa) suffer from the same generic-title problem.

---

## 3. Distinct Taisho Texts

**Total distinct Taisho texts in matches: 321**

### Taisho texts matching >5 CBETA entries

| Taisho ID  | Title                                         | Author         | CBETA Matches |
|------------|-----------------------------------------------|----------------|--------------|
| T18n0912   | 建立曼荼羅護摩儀軌                             | 唐 法全集       | 16           |
| T18n0908   | 金剛頂瑜伽護摩儀軌                             | 唐 不空譯       | 15           |
| T18n0901   | 陀羅尼集經                                     | 唐 阿地瞿多譯   | 14           |
| T18n0909   | 金剛頂瑜伽護摩儀軌                             | 唐 不空譯       | 14           |
| T21n1416   | 金剛摧碎陀羅尼                                 | 宋 慈賢譯       | 13           |
| T19n0959   | 頂輪王大曼荼羅灌頂儀軌                         | 唐              | 11           |
| T20n1119   | 大樂金剛薩埵修行成就儀軌                       | 唐 不空譯       | 9            |
| T21n1259   | 摩利支天一印法                                 |                | 9            |
| T20n1067   | 攝無礙大悲心大陀羅尼經計一法中出無量義...       | 唐 不空譯       | 8            |
| T21n1417   | 佛說壞相金剛陀羅尼經                           | 元 沙囉巴譯     | 7            |
| T21n1400   | 佛說消除一切災障寶髻陀羅尼經                   | 宋 法賢譯       | 7            |
| T21n1372   | 增慧陀羅尼經                                   | 宋 施護譯       | 7            |
| T20n1185A  | 佛說文殊師利法寶藏陀羅尼經                     | 唐 菩提流志譯   | 6            |
| T20n1197   | 佛說文殊師利一百八名梵讚                       | 宋 法天譯       | 6            |
| T21n1323   | 除一切疾病陀羅尼經                             | 唐 不空譯       | 6            |
| T20n1162   | 持世陀羅尼經                                   | 唐 玄奘譯       | 6            |
| T21n1255b  | 佛說摩利支天經                                 | 唐 不空譯       | 6            |

The Taisho-side over-matching is driven by the same generic-title phenomenon. Texts like T18n0912 (曼荼羅護摩儀軌) get matched by multiple generic Tibetan entries for "homa ritual", "mandala ritual", etc. T18n0901 (陀羅尼集經, "Dharani Collection Sutra") is matched by cbeta_id=865 plus other generic dharani-titled entries.

---

## 4. Random Sample of 30 Medium-Confidence Matches (seed=42)

| # | cbeta_id | Tibetan Title | Taisho ID | Taisho Title | Conf | Signals | Reason (first 100 chars) |
|---|----------|--------------|-----------|-------------|------|---------|-------------------------|
| 1 | 865 | 陀羅尼 | T21n1408 | 佛說最上意陀羅尼經 | 80 | chinese_title_substring | Title T21n1408 '佛說最上意陀羅尼經' contains 陀羅尼. Standard sutra opening (如是我聞). Narrative presentation of si... |
| 2 | 328 | 難陀出家經 | T02n0113 | 佛說難提釋經 | 82 | sanskrit_exact | T02n0113 is titled '佛說難提釋經' - 難提 (Nandi/Nanda) directly matches the protagonist name in the Tibetan ... |
| 3 | 1048 | 不忘陀羅尼 | T18n0901 | 陀羅尼集經 | 78 | chinese_title_overlap | T18n0901 '陀羅尼集經' (Dharani Collection Sutra) is the primary dharani collection text. The Tibetan cata... |
| 4 | 920 | 菩提心莊嚴十萬陀羅尼 | T21n1376 | 佛說聖莊嚴陀羅尼經 | 80 | chinese_title_overlap | Tibetan '菩提心莊嚴十萬陀羅尼' (Bodhicitta/Bodhigarbha Adornment Hundred-Thousand dharani) with Sanskrit Bodhi... |
| 5 | 865 | 陀羅尼 | T19n1016 | 舍利弗陀羅尼經 | 87 | chinese_title_substring | Title 舍利弗陀羅尼經 contains 陀羅尼經. T19n1016 has proper sutra opening (如是我聞), closes with multiple names fo... |
| 6 | 865 | 陀羅尼 | T20n1082 | 觀世音菩薩祕密藏如意輪陀羅尼神呪經 | 87 | chinese_title_substring | Title '觀世音菩薩祕密藏如意輪陀羅尼神呪經' is clearly an Avalokitesvara Wish-Fulfilling Wheel dharani sutra. Opening ... |
| 7 | 865 | 陀羅尼 | T21n1402 | 消除一切閃電障難隨求如意陀羅尼經 | 86 | chinese_title_substring | T21n1402 '消除一切閃電障難隨求如意陀羅尼經' (Sutra on Dharani for Removing Lightning Obstacles and Obtaining All Wis... |
| 8 | 865 | 陀羅尼 | T21n1379 | 佛說大愛陀羅尼經 | 89 | chinese_title_substring | Tibetan '陀羅尼' matches T21n1379 '佛說大愛陀羅尼經'. Opening '如是我聞' and closing '歡喜踊躍禮佛而退' confirm sutra forma... |
| 9 | 3535 | 摩利支天成就法 | T21n1259 | 摩利支天一印法 | 82 | chinese_title_overlap | Both are tantric texts on Marici. T21n1259 (摩利支天一印法) matches the Maricisadhana entry well: it contai... |
| 10 | 517 | 聖無垢陀羅尼 | T19n1024 | 無垢淨光大陀羅尼經 | 75 | chinese_title_overlap | Title semantic match: Tibetan 聖無垢陀羅尼 (Arya-vimala-nama-dharani, 'immaculate') aligns closely with Ta... |
| 11 | 515 | 聖佛心陀羅尼 | T19n0919 | 諸佛心印陀羅尼經 | 78 | chinese_title_overlap | T19n0919 '諸佛心印陀羅尼經' (All Buddhas' Heart-seal Dharani Sutra) shows significant semantic overlap with ... |
| 12 | 865 | 陀羅尼 | T20n1117 | 佛說觀自在菩薩母陀羅尼經 | 86 | chinese_title_substring | Title 佛說觀自在菩薩母陀羅尼經 directly matches 陀羅尼 catalogue entry. Opens with standard sutra formula (如是我聞) wi... |
| 13 | 865 | 陀羅尼 | T20n1078 | 七佛俱胝佛母心大准提陀羅尼法 | 88 | chinese_title_substring | T20n1078 'Seven Buddhas, Mother of Koti Buddhas, Heart Great Cundi Dharani Method' explicitly focuse... |
| 14 | 891 | 聖障除陀羅尼 | T21n1400 | 佛說消除一切災障寶髻陀羅尼經 | 70 | chinese_title_overlap | Possible match: Tibetan '聖障除陀羅尼' (Avaranaviskambhi, obstacle-removing) and T21n1400 '消除一切災障寶髻陀羅尼經' (... |
| 15 | 497 | 聖八天女陀羅尼 | T21n1366 | 佛說祕密八名陀羅尼經 | 78 | chinese_title_overlap | Both texts concern secret eight names and dharani. T21n1366 title '佛說祕密八名陀羅尼經' aligns with the eight... |
| 16 | 865 | 陀羅尼 | T21n1255a | 佛說摩利支天菩薩陀羅尼經 | 88 | chinese_title_substring | The Tibetan entry '陀羅尼' corresponds to '佛說摩利支天菩薩陀羅尼經'. Opens with standard sutra formula (如是我聞), fea... |
| 17 | 3464 | 文殊師利成就法 | T21n1218 | 文殊師利耶曼德迦呪法 | 78 | chinese_title_overlap | Title semantics: Tibetan 'Manjusrisadhana' (文殊師利成就法) directly parallels the generic Manjusri sadhana... |
| 18 | 865 | 陀羅尼 | T21n1365 | 八名普密陀羅尼經 | 89 | chinese_title_substring | T21n1365 'Eight Names Universal Secret Dharani Sutra' explicitly includes '陀羅尼' in the title and is ... |
| 19 | 3817 | 聖薄伽梵母般若波羅蜜多金剛能斷廣註 | T08n0236b | 金剛般若波羅蜜經 | 88 | chinese_title_overlap | Tibetan entry is Diamond Sutra commentary. T08n0236b is a Diamond Sutra translation (base text), one... |
| 20 | 1051 | 一切毒害消滅陀羅尼 | T21n1400 | 佛說消除一切災障寶髻陀羅尼經 | 82 | chinese_title_overlap | Title semantics match closely: Tibetan '一切毒害消滅陀羅尼' (dharani for eliminating all poisons) aligns with... |
| 21 | 29 | 聖般若波羅蜜多金剛手大乘經 | T05n0220 | 大般若波羅蜜多經(第1卷-第200卷) | 78 | chinese_title_overlap | T05n0220 is the massive 大般若波羅蜜多經 (Great Prajnaparamita Sutra) translation by Xuanzang. While the Tib... |
| 22 | 865 | 陀羅尼 | T20n1183 | 一髻文殊師利童子陀羅尼念誦儀軌 | 76 | chinese_title_substring | T20n1183 (One-Topknot Manjusri Dharani Recitation Ritual) is a dharani ritual text with proper openi... |
| 23 | 2119 | 護摩儀軌 | T18n0912 | 建立曼荼羅護摩儀軌 | 78 | chinese_title_substring | T18n0912 'Building Mandala Homa Ritual' directly matches homa ritual category. Text systematically d... |
| 24 | 865 | 陀羅尼 | T20n1049 | 聖六字增壽大明陀羅尼經 | 75 | chinese_title_substring | Both texts are dharani-related. T20n1049 (Six-Character Great Bright Dharani) is a standalone dharani... |
| 25 | 865 | 陀羅尼 | T20n1135 | 佛說一切如來金剛壽命陀羅尼經 | 86 | chinese_title_substring | Tibetan entry '陀羅尼' matches T20n1135 '佛說一切如來金剛壽命陀羅尼經'. Section 'dharani collection' appropriate. Vol... |
| 26 | 1983 | 曼荼羅儀軌 | T18n0912 | 建立曼荼羅護摩儀軌 | 76 | chinese_title_overlap | Both are mandala ritual texts (曼荼羅儀軌/Mandalavidhi). T18n0912 is titled 建立曼荼羅護摩儀軌 (establishing manda... |
| 27 | 865 | 陀羅尼 | T21n1397 | 智炬陀羅尼經 | 81 | chinese_title_substring | Title 智炬陀羅尼經 directly includes 陀羅尼. Opens with standard sutra formula (如是我聞) in elaborate Buddhist a... |
| 28 | 2718 | 聖,文殊師利讚 | T20n1195 | 大聖文殊師利菩薩讚佛法身禮 | 85 | chinese_title_overlap | Direct match: Tibetan Arya-manjusristotra-nama corresponds to Taisho T20n1195 大聖文殊師利菩薩讚佛法身禮. Sanskri... |
| 29 | 865 | 陀羅尼 | T21n1390 | 佛說洛叉陀羅尼經 | 82 | chinese_title_substring | T21n1390 is titled '佛說洛叉陀羅尼經' (Buddha-spoken Laksa Dharani Sutra). The Tibetan entry generically lis... |
| 30 | 2659 | 護摩儀軌 | T18n0909 | 金剛頂瑜伽護摩儀軌 | 88 | chinese_title_substring | Tibetan entry specifies Homavidhi (護摩儀軌). T18n0909 (金剛頂瑜伽護摩儀軌) is a foundational homa ritual te... |

### Observations from random sample

- **14 of 30 sampled matches (47%) involve cbeta_id=865** ("陀羅尼"), reflecting its 29% share of all matches.
- The cbeta_id=865 matches are all genre-level associations ("this dharani text maps to some dharani"), not text-level identifications.
- Non-865 matches show more genuine title correspondence (e.g., #2 難陀出家經 -> 佛說難提釋經, #9 摩利支天成就法 -> 摩利支天一印法).
- Sample #19 matches a Tibetan *commentary* on the Diamond Sutra (廣註 = "extensive commentary") to the base *sutra text* (T08n0236b) -- arguably a genre mismatch.
- Sample #15 matches "八天女陀羅尼" (8-goddess dharani) to "祕密八名陀羅尼經" (secret 8-name dharani) -- the "eight" is coincidental; these are likely different texts.

---

## 5. Systematic Quality Concerns

### Concern 1: Generic Tibetan Titles Dominating Matches (CRITICAL)

The single most important quality issue. **183 of 620 matches (29.5%) come from a single generic Tibetan entry cbeta_id=865 titled merely "陀羅尼"** with no Sanskrit title. Additional generic titles:

| Generic Title | cbeta_ids involved | Total matches |
|--------------|-------------------|--------------|
| 陀羅尼 (dharani) | 865 | 183 |
| 法門 (dharma-gate) | 4363 | 12 |
| 成就儀軌 (sadhana ritual) | 1979 | 10 |
| 護摩 (homa) | 3101, 1502 | 10 |
| 護摩儀軌 (homa ritual) | 1223, 1255, 1965, 2119, 2659, 2844 | 18 |
| 曼荼羅儀軌 (mandala ritual) | 1933, 1934, 3760, 3767 | 12 |

Approximately **245 matches (39.5%)** involve Tibetan entries with titles of 5 or fewer Chinese characters -- essentially genre labels, not specific text identifications. These are one-to-many matches that inflate the count without providing precise cross-references.

**Recommendation:** Filter out or flag matches where the Tibetan Chinese title is <= 5 characters AND there is no Sanskrit title, or where a single cbeta_id matches > 10 Taisho texts. These could be reported separately as "genre-level associations" rather than text-level matches.

### Concern 2: Only Chinese-Title-Based Signals

Every single match has exactly 1 signal:

| Signal | Count | % of matches |
|--------|------:|-----:|
| chinese_title_overlap | 336 | 54.2% |
| chinese_title_substring | 276 | 44.5% |
| sanskrit_fuzzy | 6 | 1.0% |
| sanskrit_exact | 2 | 0.3% |

No match has more than 1 signal. The `section_match` and `nanjio_match` signals never appear at all. The `sanskrit_exact` and `sanskrit_fuzzy` signals together account for only 8 matches (1.3%). This means **98.7% of matches rely solely on Chinese title similarity**, which is inherently fragile for Buddhist texts with highly formulaic titles (many sutras share phrases like 陀羅尼, 般若波羅蜜多, 大乘經, etc.).

**Recommendation:** Investigate why Sanskrit matching contributes so little. Many Tibetan catalogue entries have Sanskrit titles that should provide strong disambiguation. Consider adding Taisho-side Sanskrit data (from Nanjio, Lancaster, or CBETA jinglu) to enable Sanskrit-Sanskrit matching.

### Concern 3: LLM Confidence Calibration

The LLM (predominantly Claude Haiku 4.5) gives surprisingly high confidence to generic matches:
- cbeta_id=865 matches: mean confidence 85.3, range 75-95
- 33 matches scored 90+ (high confidence) from the generic "陀羅尼" entry

The LLM appears to be answering "is this Taisho text a dharani text?" (yes, obviously) rather than "is this the *specific* Tibetan dharani text described by cbeta_id=865?" The confidence scores do not adequately distinguish genre-level matches from text-level identifications.

**Recommendation:** Modify the LLM prompt to explicitly penalize cases where the Tibetan title is too generic to identify a specific text. Or add a post-processing step that caps confidence when the Tibetan title length is very short and multiple Taisho matches exist for the same cbeta_id.

### Concern 4: Over-Matching to Large Compilation Texts

12 matches involve Taisho texts with > 1 million characters:
- T05n0220 (大般若波羅蜜多經, vols 1-200): 5 matches
- T06n0220 (大般若波羅蜜多經, vols 201-400): 4 matches
- T07n0220 (大般若波羅蜜多經, vols 401-600): 3 matches

Xuanzang's massive Mahaprajnaparamita compilation (1.5M+ chars per volume segment) gets matched by multiple Tibetan Prajnaparamita entries. While some of these are likely valid (the 大般若 does contain translations of multiple Prajnaparamita texts), matching a specific Tibetan sutra to a 200-fascicle compilation is imprecise unless the specific assembly (hui) or fascicle range is identified.

### Concern 5: Commentary-to-Sutra Mismatches

Sample #19 shows the Tibetan entry 聖薄伽梵母般若波羅蜜多金剛能斷廣註 ("extensive commentary on the Diamond Sutra") matched to T08n0236b (金剛般若波羅蜜經, the Diamond Sutra base text itself). A commentary should not be matched to a base sutra as if they are the same text. The LLM gave this 88 confidence, noting it is a commentary-to-base-text match but still calling it a MATCH.

**Recommendation:** Distinguish commentary/annotation matches from text-level equivalences in the matching criteria.

### Concern 6: Model Heterogeneity

- 587 matches (94.7%) used Claude Haiku 4.5
- 33 matches (5.3%) used Claude Sonnet 4.5

Mean confidence for Sonnet (86.3) is slightly higher than Haiku (83.4). The mix of models introduces potential inconsistency in scoring standards. It is unclear what triggered Sonnet usage for those 33 cases.

### Concern 7: No Duplicate Pairs, but Many-to-Many Relationships

There are no duplicate (cbeta_id, taisho_id) pairs, which is good. However, the many-to-many relationships (one CBETA entry matching many Taisho texts, and one Taisho text matching many CBETA entries) create a tangled graph rather than clean cross-references. The 17 Taisho texts with >5 CBETA matches and 6 CBETA entries with >5 Taisho matches suggest the matcher is operating at the genre level rather than the text level for a significant portion of results.

---

## Summary Assessment

| Metric | Value |
|--------|-------|
| Total matches | 620 |
| Likely genuine text-level matches | ~375 (matches excluding generic titles) |
| Genre-level associations (questionable) | ~245 (generic Tibetan titles <= 5 chars) |
| Signal diversity | Very low (98.7% Chinese title only) |
| Duplicate pairs | 0 (good) |
| Distinct CBETA entries | 271 |
| Distinct Taisho texts | 321 |

**Bottom line:** Roughly 60% of matches appear to be genuine text-level cross-references supported by meaningful title correspondence. The remaining 40% are inflated by generic Tibetan catalogue entries (especially "陀羅尼") that produce many-to-many genre-level associations. The match count of 620 significantly overstates the number of actionable cross-references. After filtering generic titles, the effective match count would be closer to 375.

The most impactful improvements would be: (1) filter or reclassify generic-title matches, (2) integrate Sanskrit-title matching, and (3) adjust LLM prompting to penalize under-specified Tibetan entries.
