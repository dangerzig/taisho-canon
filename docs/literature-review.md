# Digests and Retranslations in the Taisho Tripitaka: A Literature Review

## 1. Introduction

The *Taisho shinshu daizokyo* (大正新脩大藏經, hereafter "Taisho"), compiled between 1924 and 1934 under the editorship of Takakusu Junjiro (高楠順次郎) and Watanabe Kaigyoku (渡辺海旭), contains 2,920 numbered texts across 85 volumes (with the first 55 volumes constituting the main canonical collection and volumes 56--85 containing supplementary materials, iconography, and catalogs). Among these texts are numerous cases of what the Chinese Buddhist bibliographic tradition calls *chaojing* (抄經, "digest sutras" or "excerpt scriptures") and *chongyi* (重譯, "retranslations"). Both categories represent forms of textual reduplication within the canon: digests are shorter texts created by excerpting or condensing a longer source, while retranslations are independent translation efforts of the same Indic source text. Despite their importance for understanding the formation and internal structure of the Chinese Buddhist canon, these categories have received uneven scholarly attention.

This review surveys the relevant scholarship in Chinese, Japanese, and English, identifying what has been accomplished and what remains to be done. It provides context for a computational pipeline that has detected 2,812 textual relationships across 1,412 texts in the Taisho, including 132 excerpts, 533 digests, and 288 retranslations -- constituting, to our knowledge, the first corpus-wide computational survey of digest and text-reuse relationships in the Chinese Buddhist canon.

## 2. The Chinese Bibliographic Tradition and the Identification of Digests

### 2.1 Early Catalogs: From Dao'an to Sengyou

The practice of cataloging Buddhist scriptures in China (*jinglü* 經錄) began in earnest with Dao'an's (道安, 312--385) *Zongli zhongjing mulu* (綜理眾經目錄), compiled around 374 CE. Although this catalog is no longer extant as an independent work, substantial portions are preserved in Sengyou's (僧祐, 445--518) *Chu sanzang ji ji* (出三藏記集, T2145), completed around 515 CE. Sengyou's catalog is the earliest surviving comprehensive bibliographic work on Chinese Buddhist translations and represents the foundation of the entire *jinglü* tradition.

Sengyou organized texts into several categories, among which the concept of *chao* (抄, "excerpt" or "digest") plays a notable role. In his classification, Sengyou distinguished between full translations (*yi* 譯), digests (*chao* 抄), and texts of doubtful authenticity (*yi* 疑) or spurious origin (*wei* 偽). The *chao* category encompassed texts that were understood to be derived from longer works through a process of selection and condensation. Sengyou's treatment reveals an early awareness that some shorter sutras circulating independently were in fact extracted from larger collections, particularly from the vast Prajnaparamita literature.

Importantly, Sengyou did not always regard digests negatively. While some catalographers viewed digestion as a form of corruption or unauthorized editing, Sengyou recognized that certain digests served legitimate purposes in making lengthy texts more accessible. The ambiguity in the tradition's evaluation of digests -- sometimes treated as legitimate condensations, sometimes as quasi-apocryphal alterations -- persists throughout the history of Chinese Buddhist bibliography.

### 2.2 The *Kaiyuan shijiao lu*

The most influential of all Chinese Buddhist catalogs is Zhisheng's (智昇) *Kaiyuan shijiao lu* (開元釋教錄, T2154), completed in 730 CE. This massive work cataloged all Buddhist translations known to Zhisheng and established the organizational framework that would be adopted, with modifications, by virtually all subsequent Chinese canon editions, including ultimately the Taisho.

Zhisheng's catalog is notable for its systematic treatment of both retranslations and digests. For retranslations, Zhisheng used the categories of *danyi* (單譯, "single translation," i.e., texts translated only once) and *chongyi* (重譯, "retranslation," i.e., texts translated two or more times from the same or closely related Indic originals). This classification was applied with particular thoroughness to major scriptural families such as the Prajnaparamita, Avatamsaka, and Lotus Sutra traditions. Zhisheng organized retranslations into groups, identifying which texts were translations of the "same original" (*tongben* 同本).

For digests, Zhisheng employed the term *chao* (抄) and related expressions, sometimes placing such texts in a separate subcategory (*biesheng* 別生, "separately produced" or *bieshengjing* 別生經, "separately born scriptures") to distinguish them from direct translations. The *biesheng* category was particularly important: it referred to texts that had been "separately born" from a larger work, either by excerpting a section or by condensing the content. Zhisheng attempted to trace the parent texts from which such digests derived, though his identifications were not always correct by modern scholarly standards.

The *Kaiyuan shijiao lu*'s classification system became normative. When the Taisho editors organized their edition, they largely followed the structural logic inherited from Zhisheng and subsequent catalogs, grouping retranslations together and noting digest relationships in their editorial apparatus.

### 2.3 Other Important Catalogs

Several other catalogs deserve mention for their treatment of digests and retranslations:

- **Fajing's (法經) *Zhongjing mulu* (眾經目錄, T2146)**, compiled in 594 CE under imperial auspices during the Sui dynasty, provides an early systematic classification that distinguishes *biesheng* texts from direct translations. This catalog was compiled by a team of scholar-monks and represents an important stage in the development of bibliographic categories.
- **Fei Changfang's (費長房) *Lidai sanbao ji* (歷代三寶紀, T2034)**, completed in 597 CE, offers a historically organized catalog of Buddhist texts from the Han through the Sui dynasty. While comprehensive in scope, Fei Changfang's work is known for including many dubious attributions and has been criticized by subsequent catalographers, including Zhisheng, for credulity.
- **Yancong's (彥悰) *Zhongjing mulu* (眾經目錄, T2147)**, compiled in 602 CE, provides a further refinement of the Sui-dynasty catalographic tradition.
- **Daoxuan's (道宣) *Da Tang neidian lu* (大唐內典錄, T2149)**, completed in 664 CE, provides important intermediary data between Sengyou and Zhisheng. Daoxuan, better known as the founder of the Nanshan Vinaya school, brought a scholar-monk's precision to his bibliographic work.
- **Mingquan's (明佺) *Da Zhou kanding zhongjing mulu* (大周刊定眾經目錄, T2153)**, compiled in 695 CE during the reign of Empress Wu Zetian, represents another important milestone.

The cumulative effect of this bibliographic tradition was to create an elaborate system for tracking textual relationships within the canon, though the accuracy and completeness of these identifications varied considerably.

### 2.4 Modern Chinese Scholarship on the Bibliographic Tradition

Modern Chinese scholars have produced extensive studies of the *jinglü* tradition. Lü Cheng (呂澂, 1896--1989), in works such as his *Zhongguo foxue yuanliu lüejiang* (中國佛學源流略講, 1979) and his *Xinbian Han wen da zangjing mulu* (新編漢文大藏經目錄), brought critical philological methods to bear on the traditional catalog data. His work established the modern Chinese academic approach to Buddhist bibliography as a critical discipline rather than a devotional exercise.

Fang Guangchang (方廣錩) has been perhaps the most prolific contemporary Chinese scholar working on Buddhist bibliography. His *Fojiao dazangjing shi* (佛教大藏經史, "History of the Buddhist Canon," 1991) and *Zhongguo xieben dazangjing yanjiu* (中國寫本大藏經研究, "Studies on Chinese Manuscript Canons," 2006, Shanghai guji chubanshe) provide systematic overviews of the canonical formation process. Fang's work on Dunhuang manuscript canons and his analysis of how digest and retranslation categories were applied and sometimes misapplied in the catalogs has been particularly important. His editorship of the journal *Zangwai fojiao wenxian* (藏外佛教文獻, "Buddhist Texts Not Contained in the Canon") has also brought attention to texts excluded from standard canonical editions, some of which represent digest or variant versions of canonical texts.

Li Fuhua (李富華) and He Mei (何梅) produced the comprehensive *Hanwen fojiao dazangjing yanjiu* (漢文佛教大藏經研究, "Studies on the Chinese Buddhist Canon"), published in 2003 by Zongjiao wenhua chubanshe in Beijing. This work traces the history of all major Chinese canon editions from the Kaibao canon of 971 CE through the modern Taisho, discussing classification issues including the treatment of digests throughout the canonical tradition.

Tang Yongtong's (湯用彤, 1893--1964) classic *Han Wei Liang Jin Nanbeichao fojiao shi* (漢魏兩晉南北朝佛教史, "History of Buddhism during the Han, Wei, Two Jin, and Northern and Southern Dynasties," first published 1938, reprinted by Zhonghua shuju 1983) provides essential historical context for understanding the translation and compilation activities of the first several centuries of Chinese Buddhism that produced both retranslations and digests.

More recently, scholars at institutions such as Peking University, Renmin University, and the Chinese Academy of Social Sciences have continued work on Buddhist bibliographic studies. Ji Yun (紀贇), based in Singapore, has published important Chinese-language articles engaging with Western scholarship on the Heart Sutra and related questions of textual authenticity, providing a valuable bridge between Chinese and English-language scholarship. His work includes detailed responses to Nattier's Chinese-composition thesis, offering both support for and critique of specific aspects.

[*Note: Exact publication details for Ji Yun's Heart Sutra articles should be verified against Singapore-based Buddhist studies journals and edited volumes.*]

### 2.5 The Concept of *Biesheng* in the Catalog Tradition

The term *biesheng* (別生) deserves special attention as a technical category in Buddhist bibliography. As analyzed by scholars including Fang Guangchang and Tokuno Kyoko, *biesheng* texts were understood to be "separately produced" or "separately born" from larger canonical works. The category was somewhat fluid: it could encompass texts that were (a) individual sutras extracted from larger collections (e.g., an individual discourse extracted from an Agama collection), (b) chapters or sections of a larger work circulating independently, (c) condensed versions of longer texts, or (d) compilations assembled from multiple sources.

The *biesheng* category is distinct from both *weijing* (偽經, "spurious scriptures") and *yijing* (疑經, "doubtful scriptures"), though there is some overlap. A *biesheng* text was not necessarily considered fraudulent; it might be a perfectly legitimate extract or condensation. The catalographers' primary concern was to identify its parent text and to note that it was not an independent translation. This is precisely the kind of relationship that our computational pipeline is designed to detect: asymmetric textual containment where a shorter text is substantially derived from a longer one.

## 3. Modern Western Scholarship

### 3.1 Jan Nattier and the Heart Sutra as Digest

The single most influential Western-language study of a digest relationship in the Chinese Buddhist canon is Jan Nattier's 1992 article "The Heart Sutra: A Chinese Apocryphal Text?" published in the *Journal of the International Association of Buddhist Studies* (JIABS), volume 15, number 2, pages 153--223. Nattier argued, on the basis of detailed textual comparison, that the *Xin jing* (心經, Heart Sutra, T251) attributed to Xuanzang was not translated from a Sanskrit original but was rather composed in Chinese by extracting passages from Kumarajiva's translation of the *Mahaprajnaparamita Sutra* (specifically, the *Pancavimsatisahasrika Prajnaparamita*, T223, the *Mohe bore boluomi jing* 摩訶般若波羅蜜經) and framing them with a new narrative wrapper.

Nattier's methodology was primarily philological: she demonstrated that the Chinese text of the Heart Sutra's core passage corresponds almost verbatim to specific sections of Kumarajiva's T223, while the extant Sanskrit Heart Sutra text shows signs of having been back-translated from Chinese (including Sanskritizations that reflect Chinese phrasing rather than natural Sanskrit idiom). Her argument effectively reclassified the Heart Sutra from a direct translation to a digest -- or more precisely, to a Chinese composition that incorporated digested material from an earlier translation.

The impact of Nattier's article has been enormous. It generated substantial scholarly debate and has been engaged with by virtually every subsequent study of the Heart Sutra. Key responses and extensions include the following.

**Jayarava Attwood** has published the most sustained series of follow-up studies supporting and extending Nattier's Chinese-composition hypothesis. His publications include:

- "Heart Murmurs: Some Problems with Conze's Prajnaparamitahrdaya," *Journal of the Oxford Centre for Buddhist Studies* 8 (2015): 28--48.
- "Form is (Not) Emptiness: The Enigma at the Heart of the Heart Sutra," *Journal of the Oxford Centre for Buddhist Studies* 13 (2017): 52--80. This article examined the famous "form is emptiness" formula and its relationship to Prajnaparamita source texts.
- "Epithets of the Mantra in the Heart Sutra," *Journal of the International Association of Buddhist Studies* 40 (2017 [published 2018]): 305--351. This study analyzed the epithets applied to the Prajnaparamita mantra in the Heart Sutra, arguing they provide further evidence for Chinese composition.
- "A Note on Nisthanirvana in the Heart Sutra," *Journal of the Oxford Centre for Buddhist Studies* 14 (2018): 10--17.
- "The Buddhas of the Three Times and the Chinese Origins of the Heart Sutra," *Journal of the Oxford Centre for Buddhist Studies* 15 (2018): 9--27.
- "Xuanzang's Relationship to the Heart Sutra in Light of the Fangshan Stele," *Journal of Chinese Buddhist Studies* 32 (2019): 1--30.
- "Ungarbling Section VI of the Sanskrit Heart Sutra," *Journal of the Oxford Centre for Buddhist Studies* 18 (2020): 11--41.
- "The Chinese Origins of the Heart Sutra Revisited: A Comparative Analysis of the Chinese and Sanskrit Texts," *Journal of the International Association of Buddhist Studies* 44 (2021): 13--52.
- "Studying the Heart Sutra," *Buddhist Studies Review* 37, no. 2 (2021): 199--217.
- "Preliminary Notes on the Extended Heart Sutra in Chinese," *Asian Literature and Translation* 8, no. 1 (2021): 63--85.
- "Heart Sutra Revisited," *Buddhist Studies Review* 39, no. 2 (2023): 229--254.
- "Heart to Heart: A Comparative Study of and Commentary on the Chinese and Sanskrit Heart Sutra Texts," *Buddhist Studies Review* 40 (2024).

Attwood has also maintained an extensive blog (*Jayarava's Raves*) that provides accessible summaries of his research and engages with the broader scholarly discussion. His fourteen articles on the Heart Sutra are expected to appear in collected book form. His cumulative work represents the most thorough investigation of the Heart Sutra's textual history since Nattier's original article, and his 2021 JIABS article constitutes the most rigorous restatement of the Chinese-composition hypothesis with updated evidence.

**Matthew Orsborn (Shi Huifeng)**, now at Dharma Drum Institute of Liberal Arts, in his 2012 PhD dissertation at the University of Hong Kong, "Chiasmus in the Early Prajnaparamita: Literary Parallelism Connecting Criticism and Hermeneutics in an Early Mahayana Sutra," examined the literary structure of the Prajnaparamita literature, providing tools for understanding the relationship between the Heart Sutra and its longer sources. Orsborn's chiasmic analysis demonstrated that the *Astasahasrika Prajnaparamita* was composed as a unified literary whole rather than from accumulated fragments, an argument with implications for understanding the textual relationships between shorter and longer Prajnaparamita texts. He has also published articles directly on the Heart Sutra, largely supporting Nattier's core argument while offering refinements based on his detailed knowledge of the Prajnaparamita textual tradition.

**Dan Lusthaus** published "The Heart Sutra in Chinese Yogacara: Some Comparative Comments on the Heart Sutra Commentaries of Woncheuk and Kuiji" in the *International Journal of Buddhist Thought and Culture* 3 (2003): 59--103. This study engaged critically with Nattier's thesis while focusing on how Chinese Yogacara commentators (the Korean monk Woncheuk and the Chinese monk Kuiji, both students of Xuanzang) understood and explicated the Heart Sutra. Lusthaus broadly supported the Chinese-composition theory while offering additional nuances regarding the Yogacara commentarial tradition's treatment of the text.

**Tanahashi Kazuaki**, in *The Heart Sutra: A Comprehensive Guide to the Classic of Mahayana Buddhism* (Boulder: Shambhala, 2014), provides an accessible overview of Heart Sutra scholarship that acknowledges Nattier's theory while presenting multiple perspectives. While not primarily a work of original scholarship, Tanahashi's book synthesizes a wide range of scholarly views and includes translations from Chinese and Japanese secondary literature not otherwise available in English.

**Jonathan Silk** published "The Heart Sutra in Tibetan: A Critical Edition of the Two Recensions Contained in the Kanjur" in the *Wiener Zeitschrift fur die Kunde Sudasiens* 38 (1994): 369--418. This study provided a critical edition of the Tibetan Heart Sutra translations and explored what the Tibetan textual tradition reveals about the text's history, contributing important evidence to the Chinese-origins debate.

**Fukui Fumimasa** (福井文雅) had independently proposed a Chinese-origin theory for the Heart Sutra in Japanese scholarship before Nattier's article. His work is discussed further in Section 4 below.

What makes Nattier's work methodologically significant for the broader study of digests is that she demonstrated how close textual comparison between a suspected digest and its proposed source could yield compelling evidence about the direction of textual dependency. Her work implicitly provides a model for how similar investigations might be carried out for other suspected digest relationships in the canon. Our computational pipeline operationalizes this model at scale: where Nattier performed manual comparison of two specific texts, the pipeline applies analogous logic to all text pairs in the canon simultaneously.

### 3.2 Erik Zurcher and the Study of Chinese Buddhist Translations

Erik Zurcher's (1928--2008) foundational *The Buddhist Conquest of China: The Spread and Adaptation of Buddhism in Early Medieval China* (Leiden: Brill, 1959; 2nd edition 1972; 3rd edition 2007) established the historical framework within which early Chinese Buddhist translation activity must be understood. While Zurcher did not focus specifically on digests, his detailed analysis of translation teams, their methods, and the social context of translation production is essential background for understanding how both retranslations and digests came into being.

Zurcher's later article "A New Look at the Earliest Chinese Buddhist Texts" (in *From Benares to Beijing: Essays on Buddhism and Chinese Religion in Honour of Prof. Jan Yun-Hua*, edited by Koichi Shinohara and Gregory Schopen, 277--304, Oakville, ON: Mosaic Press, 1991) applied linguistic analysis to the earliest stratum of Chinese Buddhist translations, demonstrating that careful philological comparison could reveal the translation techniques and source-language features underlying Chinese Buddhist texts. His related study "Late Han Vernacular Elements in the Earliest Buddhist Translations" (*Journal of the Chinese Language Teachers Association* 12 [1977]: 177--203) [*publication details should be verified*] pioneered the use of linguistic markers to identify translators and date texts, a methodology directly relevant to digest detection.

### 3.3 Lancaster and the Korean Buddhist Canon Project

Lewis Lancaster's work on the Korean Buddhist canon and his development of early digital tools for Buddhist textual studies represent an important bridge between traditional bibliography and digital humanities approaches. Lancaster's *The Korean Buddhist Canon: A Descriptive Catalogue* (Berkeley: University of California Press, 1979), compiled with Sung-bae Park, provided a systematic catalog that included cross-references between texts, effectively documenting some retranslation and digest relationships.

Lancaster was also a pioneer in advocating for computational approaches to studying the Buddhist canon, arguing as early as the 1980s that the sheer scale of the corpus made computational assistance essential for comprehensive textual analysis. His "Electronic Processing of Buddhist Texts" and related publications established the conceptual groundwork for projects like CBETA and SAT that would follow.

### 3.4 Boucher, Karashima, and Translation Studies

Daniel Boucher's *Bodhisattvas of the Forest and the Formation of the Mahayana: A Study and Translation of the Rastrapalapariprccha-sutra* (Honolulu: University of Hawai'i Press, 2008) and his earlier articles on Dharmaraksa's translation activity contribute to our understanding of how multiple translations of the same text came into being. Boucher's detailed analysis of Dharmaraksa's translation vocabulary and technique provides tools for distinguishing between different translators' renderings of the same source -- a skill essential for identifying retranslation relationships and for distinguishing retranslations from digests.

Seishi Karashima's (辛嶋静志, 1957--2019) extensive lexicographic work, particularly his *A Glossary of Dharmaraksa's Translation of the Lotus Sutra* (Tokyo: International Research Institute for Advanced Buddhology, Soka University, 1998) and *A Glossary of Kumarajiva's Translation of the Lotus Sutra* (Tokyo: International Research Institute for Advanced Buddhology, Soka University, 2001), along with numerous articles on translation vocabulary, provides the fine-grained linguistic data necessary for identifying translator-specific renderings. This is directly relevant to digest detection, since a digest will typically preserve the translation vocabulary of its source text -- the very principle that underlies our pipeline's ability to detect the Heart Sutra's derivation from Kumarajiva's T223.

Karashima's broader project of systematically documenting the translation vocabulary of individual translators (including his studies of Lokaksema, Zhi Qian, and others) established an empirical foundation for identifying which translator produced which text. This work has been continued after his death by colleagues at the International Research Institute for Advanced Buddhology.

### 3.5 Silk, Harrison, and Textual Criticism of Mahayana Sutras

Jonathan Silk's work on the *Vimalakirtinirdesa* and other Mahayana texts has demonstrated the complexity of textual transmission in the Buddhist world, showing that the relationship between Chinese translations, Tibetan translations, and surviving Sanskrit manuscripts is rarely straightforward. His methodological reflections in works such as *Managing Monks: Administrators and Administrative Roles in Indian Buddhist Monasticism* (New York: Oxford University Press, 2008) and various articles on Buddhist textual criticism are relevant to any attempt to establish textual relationships within the canon.

Paul Harrison's studies of early Chinese translations of Pure Land texts and the *Pratyutpanna Samadhi Sutra* have similarly revealed complex histories of translation, revision, and textual conflation that complicate simple categories of "retranslation" versus "digest." His 1990 *The Samadhi of Direct Encounter with the Buddhas of the Present: An Annotated English Translation of the Tibetan Version of the Pratyutpanna-Buddha-Sammukhavasthita-Samadhi-Sutra* (Tokyo: International Institute for Buddhist Studies) is a model of how a single text's translation history can be reconstructed through careful comparison of multiple versions across languages.

Harrison's 1993 article "The Earliest Chinese Translations of Mahayana Buddhist Sutras: Some Notes on the Works of Lokaksema" (*Buddhist Studies Review* 10, no. 2: 135--177) provided crucial data on the earliest translation techniques, relevant for understanding how the translation process could produce variant versions that might later be misidentified as digests.

### 3.6 Storch and the Concept of *Chao*

Tanya Storch's *The History of Chinese Buddhist Bibliography: Censorship and Transformation of the Tripitaka* (Amherst, NY: Cambria Press, 2014) provides important conceptual clarity on the *jinglü* tradition. Storch explored how bibliographic categories including *chao* were understood and applied, noting that the term could cover a range of practices from simple excerpting to more creative condensation and rearrangement. This variability in what constitutes a "digest" is an important consideration for any systematic study of the phenomenon, including our computational approach. Storch's work emphasizes that Chinese Buddhist bibliography was not merely a cataloging exercise but a form of canonical management with implications for orthodoxy and authority.

### 3.7 Buswell and Chinese Buddhist Apocrypha

Robert Buswell's edited volume *Chinese Buddhist Apocrypha* (Honolulu: University of Hawai'i Press, 1990) remains the foundational English-language treatment of Chinese-composed Buddhist texts. The contributors -- including Buswell himself, Tokuno Kyoko, Robert Sharf, Michel Strickmann, and others -- demonstrate the various ways in which Chinese authors drew on existing translations to create new texts. Tokuno's chapter, "The Evaluation of Indigenous Scriptures in Chinese Buddhist Bibliographical Catalogues" (pp. 31--74), is particularly relevant for understanding how the *jinglü* tradition treated texts that were composed rather than translated.

The volume established that Chinese-produced scriptures were not simply "forgeries" but represented a creative literary and religious phenomenon. This insight is directly relevant to the study of digests, since many digest texts -- including, on Nattier's analysis, the Heart Sutra itself -- are Chinese compositions that draw material from existing translations while adding new elements.

### 3.8 Stefano Zacchetti and Early Chinese Prajnaparamita

Stefano Zacchetti's (1968--2020) *In Praise of the Light: A Critical Synoptic Edition with an Annotated Translation of Chapters 1--3 of Dharmaraksa's Guang zan jing* (Tokyo: International Research Institute for Advanced Buddhology, Soka University, 2005) demonstrates the level of detailed philological work required to establish translation relationships with confidence even for a single textual family. Zacchetti's synoptic approach -- comparing multiple Chinese translations of the Prajnaparamita alongside Sanskrit and Tibetan witnesses -- is the gold standard for the philological study of retranslation relationships. His method reveals both the shared content that retranslations preserve and the translator-specific phrasing that distinguishes them.

Zacchetti also published extensively on Lokaksema's second-century Prajnaparamita translation (T224, *Daoxing bore jing* 道行般若經), the earliest Chinese Prajnaparamita text. His work on the relationship between this text and the other early Prajnaparamita translations is important background for understanding the complex web of textual relationships within the Prajnaparamita family, the largest single textual group in the Taisho.

Zacchetti's posthumous monograph, *The Da zhidu lun 大智度論 (\*Mahaprajnaparamitopadesa) and the History of the Larger Prajnaparamita* (Hamburg Buddhist Studies 14, 2021), edited for publication by Michael Radich and Jonathan Silk, represents the culmination of two decades of research on Buddhist exegesis and the Perfection of Wisdom literature. This work is directly relevant to our pipeline's treatment of the *Dazhidu lun* (T25n1509), which emerged as one of the key source texts in the Heart Sutra's multi-source digest profile.

## 4. Japanese Scholarship

### 4.1 The Taisho Editorial Apparatus

The Taisho edition itself constitutes a major scholarly contribution to the identification of textual relationships within the canon. The editors, working in the 1920s and 1930s, drew on the entire Chinese bibliographic tradition as well as contemporary Japanese scholarship to assign texts to categories and to provide editorial notes (*kaisetsu* 解説) identifying retranslation groups and digest relationships. These notes, found in the apparatus accompanying each volume, represent a systematic (though not always complete or accurate) attempt to map textual relationships across the canon.

The Taisho's organizational structure reflects the editors' understanding of these relationships. Texts understood to be retranslations of the same original are typically grouped together in sequence (e.g., the multiple translations of the *Sukhavativyuha* sutras, or the numerous Prajnaparamita translations in volumes 5--8). Texts identified as digests are sometimes placed near their parent texts, though the placement is not always consistent.

Ono Genmyo's (小野玄妙, 1883--1939) *Bussho kaisetsu daijiten* (佛書解説大辭典, "Great Dictionary of Explanations of Buddhist Texts"), published in 12 volumes plus supplement between 1933 and 1936 (Tokyo: Daito shuppansha; reprint 1964--1988), provides detailed entries for many Taisho texts including information about retranslation and digest relationships. This work remains an indispensable reference for scholars working with the Taisho.

### 4.2 Makita Tairyo and Apocryphal Scriptures

Makita Tairyo (牧田諦亮, 1912--2011) was the preeminent Japanese scholar of Chinese Buddhist apocryphal scriptures (*gisaku kyoten* 偽作經典 or *gikyo* 疑經). His *Gikyo kenkyu* (疑經研究, "Studies on Apocryphal Sutras"), published in 1976 (Kyoto: Kyoto daigaku Jinbun kagaku kenkyujo), established the scholarly framework for studying texts of Chinese composition that were presented as Indian translations. His *Chugoku Bukkyo shi kenkyu* (中國佛教史研究) covered broader topics in Chinese Buddhist history, providing context for the production of apocryphal and digest texts.

While Makita's primary focus was on apocrypha rather than digests per se, the two categories are closely related. As Nattier's Heart Sutra study demonstrated, a text can be simultaneously a digest (in the sense of being derived from an existing translation) and an apocryphon (in the sense of being a Chinese composition misattributed to an Indian translator). Makita's methodological contributions -- particularly his attention to linguistic evidence of Chinese composition, historical context, and the testimony of the bibliographic catalogs -- are directly applicable to the study of digests.

Makita's student Tokuno Kyoko extended this work in English-language scholarship, notably in her contribution to Buswell's *Chinese Buddhist Apocrypha* (1990), which provided a systematic overview of the *jinglü* tradition's treatment of questionable texts.

### 4.3 Fukui Fumimasa and the Heart Sutra

Fukui Fumimasa (福井文雅, 1934--2017) of Waseda University was among the earliest scholars to question the traditional attribution of the Heart Sutra, publishing his analysis in Japanese before Nattier's 1992 English-language article brought the issue to wider international attention. Fukui's *Hannya shingyo no sogo teki kenkyu* (般若心経の総合的研究, "Comprehensive Study of the Heart Sutra") [*exact publication year should be verified; likely 1987 or 2000 revised edition*] examined the Heart Sutra from multiple perspectives including textual history, philology, and doctrinal analysis. He argued that the short form of the Heart Sutra was a Chinese composition rather than a translation from Sanskrit, based partly on catalog evidence and partly on analysis of the text's relationship to the larger Prajnaparamita literature.

Fukui's work is important both for its independent convergence with Nattier's conclusions and for the additional Japanese-language evidence and analysis it provides. While Nattier acknowledged Fukui's priority in raising the Chinese-composition hypothesis, the two scholars arrived at their conclusions through somewhat different analytical paths, which strengthens the overall case.

### 4.4 Funayama Toru and Translation Studies

Funayama Toru (船山徹) of the Institute for Research in Humanities (*Jinbun kagaku kenkyujo* 人文科学研究所) at Kyoto University has produced some of the most important recent Japanese scholarship on Chinese Buddhist translation history. His *Butten wa do kanyaku sareta no ka: Sutora ga Chugokugo ni naru toki* (仏典はどう漢訳されたのか：スートラが中国語になるとき, "How Were Buddhist Texts Translated into Chinese? When Sutras Become Chinese"), published in 2013 by Iwanami shoten (岩波書店), provides a comprehensive overview of translation methods and their evolution over time.

Funayama's work is particularly relevant to the study of digests and retranslations because he pays close attention to the institutional and procedural aspects of translation: how translation teams were organized, what role editors and revisers played, and how translations were reviewed and sometimes revised after initial completion. This institutional context helps explain how both retranslations (produced when a new translation team tackled a text that had already been rendered into Chinese) and digests (which could be produced either within or outside the formal translation process) came into being.

His 2006 article "Masquerading as Translation: Examples of Chinese Lectures by Indian Scholar-Monks in the Six Dynasties Period" (*Journal of the International Association of Buddhist Studies* 29, no. 2 [2006]: 169--230) directly addresses the blurred boundary between translation and Chinese composition, a boundary that is central to understanding digests. Funayama showed that some texts classified as "translations" were in fact records of Chinese-language lectures delivered by Indian monks, with varying degrees of fidelity to the underlying Indic source. This finding complicates the simple translation/composition binary and suggests that the category of "digest" should be understood as one point on a spectrum of textual production modes.

### 4.5 Ochiai Toshinori and the Nanatsudera Manuscripts

Ochiai Toshinori (落合俊典) led the study of the Nanatsudera (七寺) manuscript collection in Nagoya, which preserved texts from an early Japanese canon edition (the *issaikyo* 一切經 or "complete canon") that predates the standard Chinese canon editions. The Nanatsudera manuscripts include texts not found in the Taisho, some of which may represent digests or variant versions that were excluded from later canon editions. The multi-volume publication *Nanatsudera issaikyo* and related studies provide critical editions and analyses of these texts. This work demonstrates that our picture of digest and retranslation activity is necessarily incomplete if we rely solely on texts that survived into the Taisho.

### 4.6 Hayashiya Tomojiro

Hayashiya Tomojiro (林屋友次郎) in his *Kyoroku kenkyu* (經錄研究, "Studies on Scriptural Catalogs," Tokyo: Iwanami shoten, 1941) provided what remains one of the most thorough modern analyses of the traditional catalog data. His systematic examination of the major catalogs revealed many inconsistencies in how texts were classified across different catalographic traditions, including cases where a text was classified as a direct translation in one catalog and as a *biesheng* in another. This work is essential background for assessing the reliability of traditional identifications of digest relationships.

### 4.7 The *Kokuyaku Issaikyo* and Related Projects

The *Kokuyaku Issaikyo* (國譯一切經, "Complete Japanese Translation of the Canon") project, begun in the Taisho era and continued afterward, required Japanese scholars to produce annotated Japanese translations of the entire Chinese Buddhist canon. The notes and introductions produced for this project contain extensive discussions of textual relationships, including retranslation groups and digest identifications, representing a cumulative body of Japanese scholarly opinion on these questions that has not been systematically exploited by Western-language scholarship.

## 5. The Distinction Between Digests Created in Chinese and Those Reflecting Indic Originals

A crucial conceptual issue in the study of digests is the distinction between two fundamentally different phenomena that can produce similar-looking results in the Chinese canon.

### 5.1 Digests Produced in China

Some shorter texts in the Taisho were created in China by excerpting or condensing existing Chinese translations. These are "digests" in the strict sense: a Chinese-literate editor selected passages from one or more longer translations, arranged them (possibly with some editorial additions), and the result circulated as an independent text. The Heart Sutra, on Nattier's analysis, is the paradigmatic example of this type.

Such Chinese-produced digests can in principle be detected through close textual comparison with their source translations, since they will share not only content but specific translation vocabulary and phrasing with a particular Chinese rendering. If a short text matches one specific translation of a longer work but not other translations of the same work, this is strong evidence that the short text was derived from that particular Chinese translation rather than from an independent Indic source. Our computational pipeline exploits precisely this principle: the "translator-specific matching differential" between same-translator and cross-translator coverage is the computational signature of Chinese-level composition.

### 5.2 Abbreviated Texts Reflecting Indic Originals

A different phenomenon occurs when an Indic text itself exists in both longer and shorter versions, and both are independently translated into Chinese. In this case, the shorter Chinese translation may look superficially like a "digest" of the longer one, but it actually reflects a genuinely independent Indic textual tradition. The Prajnaparamita literature provides many examples: the *Astasahasrika* (8,000-line), *Pancavimsatisahasrika* (25,000-line), and *Satasahasrika* (100,000-line) versions share extensive material but represent distinct (though related) Indic compositions. Similarly, the shorter and longer versions of the *Sukhavativyuha Sutra* (the Smaller and Larger Pure Land sutras) reflect distinct Indic textual traditions rather than a Chinese digest relationship.

Distinguishing between these two types requires evidence beyond the Chinese texts themselves: surviving Sanskrit manuscripts, Tibetan translations, and the testimony of Indian Buddhist commentarial traditions can all help determine whether a shorter text reflects an independent Indic source or is a Chinese-produced digest. The translator-specific matching differential provides a computational heuristic: a text independently translated from an Indic condensation should show roughly equal overlap with all Chinese translations of the parent text, while a Chinese-produced digest should show preferential matching with a specific translator's version.

Edward Conze's (1904--1979) extensive work on the Prajnaparamita literature, particularly *The Prajnaparamita Literature* (The Hague: Mouton, 1960; revised edition, Tokyo: The Reiyukai, 1978) and his various editions and translations of Prajnaparamita texts, provides the essential framework for understanding the Indic side of these textual relationships. While Conze did not focus specifically on the Chinese digest question, his mapping of the relationships among the various Prajnaparamita texts in Sanskrit is indispensable background for any study of Prajnaparamita digests in the Chinese canon.

### 5.3 The Gray Area

In practice, many cases fall into a gray area between these two types. A Chinese editor might have had access to an Indic text that was itself an abbreviated version, and might also have supplemented or modified the translation by reference to an existing Chinese rendering. The boundaries between translation, revision, digest, and free composition were fluid in the Chinese Buddhist world, as scholars such as Funayama and Zurcher have emphasized.

Our computational pipeline can detect the textual relationships but cannot, by itself, determine where on this spectrum a given case falls. What it can do is flag cases for further investigation: a high-confidence digest detection with a large translator-specific matching differential warrants close philological scrutiny of the kind Nattier brought to the Heart Sutra.

## 6. What Has Been Enumerated and What Remains Unknown

### 6.1 Retranslations

The *jinglü* tradition, and especially the *Kaiyuan shijiao lu*, provides extensive (though not exhaustive or always accurate) data on retranslation groups. Zhisheng identified hundreds of retranslation clusters, and modern scholars have refined and corrected many of his identifications. The Taisho editorial apparatus largely follows Zhisheng's groupings while incorporating corrections from subsequent Japanese scholarship.

However, a fully systematic and verified enumeration of all retranslation relationships in the Taisho has not been completed using modern critical methods. The traditional catalog identifications were based on the catalographers' reading of the texts and their understanding of translation history, but were not subjected to the kind of systematic textual comparison that modern computational tools make possible. Our pipeline's detection of 288 retranslation relationships provides a starting point for such a systematic survey, though it should be noted that our retranslation classification is based on character-level overlap between texts of similar length and may miss retranslations where different translators used substantially different vocabulary.

### 6.2 Digests

The enumeration of digest relationships is far less complete than that of retranslations. While the catalogs identify some texts as *chao* or *biesheng*, these identifications have not been systematically verified, and there are almost certainly digest relationships that the catalogs did not identify. Nattier's Heart Sutra study was groundbreaking precisely because it identified a digest relationship that the traditional catalogs had not recognized -- indeed, the Heart Sutra had been treated as a legitimate translation for over a millennium.

The question of how many unidentified digests exist in the Taisho has remained open. Given the vast size of the canon (approximately 80 million Chinese characters of text) and the extensive repetition of material across Buddhist scriptural traditions, it has been plausible that many digest relationships remained to be discovered. Our pipeline's detection of 132 excerpts and 533 digests represents the first systematic attempt to answer this question computationally.

### 6.3 Previous Enumeration Efforts

Several scholars have attempted partial enumerations of digest or retranslation relationships within specific portions of the canon:

- **Zurcher** (1991) provided detailed analysis of the earliest stratum of Chinese translations (roughly those datable to the 2nd and 3rd centuries CE), identifying relationships among the earliest versions.
- **Hayashiya Tomojiro** (林屋友次郎) in his *Kyoroku kenkyu* (經錄研究, 1941) provided systematic analysis of the catalog data for large portions of the canon, including discussion of which texts were classified as *biesheng* and whether those classifications appeared justified.
- **Nanjio Bunyiu** (南條文雄) in his *A Catalogue of the Chinese Translation of the Buddhist Tripitaka, the Sacred Canon of the Buddhists in China and Japan* (Oxford: Clarendon Press, 1883) provided an early modern enumeration with cross-references, drawing on both Chinese and Japanese catalog traditions. While superseded in many respects by later scholarship, Nanjio's catalog remains useful for its systematic presentation of traditional attributions.
- The **Lancaster catalog** of the Korean canon (1979) includes cross-references to parallel texts and retranslation groups, providing an independent check on Taisho-based identifications.

None of these efforts, however, constitutes a comprehensive and verified enumeration of all digest and retranslation relationships in the Taisho. Our computational pipeline represents the first attempt at such a comprehensive survey.

## 7. Digital Humanities and Computational Approaches

### 7.1 CBETA and the Digitization of the Canon

The Chinese Buddhist Electronic Text Association (CBETA, 中華電子佛典協會), founded in 1998 in Taipei, has produced the most comprehensive and widely used digital edition of the Chinese Buddhist canon. The CBETA corpus includes the complete Taisho (and increasingly, texts from other canon editions including the Wan xinzuan xuzangjing 卍新纂續藏經, Jiaxing zang 嘉興藏, and others) in searchable, marked-up digital form. CBETA's work has fundamentally transformed the study of the Chinese Buddhist canon by making the full text computationally accessible.

For the study of digests and retranslations, CBETA's digital corpus is indispensable because it enables the kind of large-scale textual comparison that would be impractical with printed texts. Searching for shared passages, comparing translation vocabulary, and quantifying textual overlap all become feasible with a digital corpus.

CBETA has gone through several major format iterations, from early proprietary formats to Unicode-based XML (TEI P5 markup, specifically the TEI P5b variant used by CBETA). The current XML files include extensive markup for textual structure, variant readings, character normalization via `charDecl` tables, and editorial apparatus (including `<app>`, `<lem>`, and `<rdg>` elements for variant readings) -- all of which are relevant to computational text comparison. The CBETA corpus also includes editorial metadata that preserves some of the Taisho's notes about textual relationships.

CBETA has released its data under an open-access license (Creative Commons Attribution-NonCommercial-ShareAlike), facilitating computational research. The data is available via their website (cbeta.org), through GitHub repositories, and through API access, making it the natural foundation for any large-scale computational analysis of the Chinese Buddhist canon.

### 7.2 SAT Daizokyo Text Database

The SAT Daizokyo Text Database (SAT大正新脩大藏經テキストデータベース), maintained at the University of Tokyo under the direction of Shimoda Masahiro (下田正弘) and Nagasaki Kiyonori (永崎研宣), provides an alternative digital platform for accessing and studying the Taisho. SAT has pioneered several digital humanities approaches to the canon, including linked data integration (connecting texts to bibliographic databases, authority files, and other digital resources), image-text alignment (linking the digital text to page images of the original Taisho print edition), and integration with other Buddhist studies databases through IIIF (International Image Interoperability Framework) protocols.

SAT's contributions to the study of textual relationships include efforts to create structured metadata about relationships between texts, though a comprehensive mapping of digest and retranslation relationships has not been their primary focus. SAT has also experimented with text mining and natural language processing approaches to the canon, though these have focused more on named entity recognition and knowledge graph construction than on text reuse detection.

### 7.3 Marcus Bingenheimer and Digital Approaches to Buddhist Studies

Marcus Bingenheimer, based at Temple University (previously at Dharma Drum Institute of Liberal Arts 法鼓文理學院 in Taiwan), has been at the forefront of applying digital humanities methods to the Chinese Buddhist canon. His work spans several areas relevant to our project:

- **Social network analysis**: Bingenheimer's studies of social networks extracted from Chinese Buddhist biographical texts (including the *Gaoseng zhuan* 高僧傳 collections) demonstrate the potential of computational methods for Buddhist studies.

- **Translation attribution**: Bingenheimer, together with Hung Jen-Jou (洪振洲) and Simon Wiles, tested hypotheses about the attribution of early Buddhist translations using Principal Component Analysis, confirming that certain sutras should be considered to have been translated by the same translators -- contradicting traditional attributions. This work on computationally reassessing translator attributions is directly relevant to digest detection, since translator identity is a key variable in distinguishing Chinese-composed digests from independent translations.

- **TEI encoding and digital infrastructure**: Bingenheimer has contributed significantly to the development of encoding standards for Buddhist texts and to broader digital Buddhist studies methodology. His 2020 article "Digitization of Buddhism (Digital Humanities and Buddhist Studies)" in the *Oxford Bibliographies in Buddhism* provides a comprehensive survey of the field.

- **Machine translation and NLP**: Most recently, Bingenheimer has collaborated with Sebastian Nehrdich and others on the MITRA-zh-eval project, which uses a Buddhist Chinese language evaluation dataset to assess machine translation and evaluation metrics (published at NLP4DH 2025).

### 7.4 Michael Radich, Jamie Norrish, and TACL

Michael Radich (now at Heidelberg University, previously at Victoria University of Wellington) and Jamie Norrish developed TACL (Textual Analysis for Corpus Linguistics), a suite of tools specifically designed for n-gram comparison of Chinese Buddhist texts on the CBETA corpus. TACL, begun in late 2012, is the closest existing precedent to our pipeline's approach and deserves detailed discussion.

TACL's core functionality is to divide corpus texts into their constituent character n-grams and allow querying for the differences and intersections of these n-grams between arbitrary groupings of texts. Its two fundamental operations are: (1) discover all material shared by the texts under analysis (*intersect*), and (2) discover all material distinctive to one text or corpus against another (*diff*). The tool is available as open-source Python software (https://github.com/ajenhl/tacl; https://tacl.readthedocs.io/) and a GUI interface was later developed.

Radich has applied TACL primarily to questions of **translator attribution** -- determining which translator produced a given text based on shared vocabulary and stylistic markers. His major methodological statement is "On the Ekottarikagama 增壹阿含經 T 125 as a Work of Zhu Fonian 竺佛念" (*Journal of Chinese Buddhist Studies* 30 [2017]: 1--31), which used TACL to identify over 6,200 occurrences of 137 stylistic markers unique to Zhu Fonian, arguing for reattribution of the *Ekottarikagama* from Samghadeva to Zhu Fonian. His study of the "Great Cloud Sutras" (T 387, T 388/S.6916) similarly used TACL for computational attribution analysis (published in *Buddhist Transformations and Interactions: Papers in Honor of Antonino Forte*, 2017). His 2019 article in the *Hualin International Journal of Buddhist Studies* (2.1: 229--279) provides further methodological discussion.

Radich also maintains two important digital resources: the **Chinese Buddhist Canonical Attributions database (CBC@)** (https://dazangthings.nz/cbc/), a user-contributor database indexing evidence bearing on questions of attribution and dating; and the **Radich Taisho corpus** (available on Zenodo), a modified version of the CBETA Taisho that reflects scholarly corrections to the text.

TACL's relationship to our pipeline is complementary: TACL is primarily an **interactive exploration tool** that helps scholars investigate specific attribution and comparison questions, while our pipeline is a **batch processing system** that screens all text pairs for digest relationships. TACL can find shared and distinctive n-grams between selected texts or corpora but does not perform automated digest detection, alignment, or classification across the entire canon. Conversely, our pipeline produces quantitative digest scores but does not support the kind of interactive, exploratory comparison that TACL enables.

### 7.5 Sebastian Nehrdich and Neural Parallel Passage Detection

Sebastian Nehrdich (Tohoku University, previously at the University of Hamburg and UC Berkeley) published "A Method for the Calculation of Parallel Passages for Buddhist Chinese Sources Based on Million-scale Nearest Neighbor Search" in the *Journal of the Japanese Association for Digital Humanities* 5, no. 2 (2020): 132--153. This work represents the first attempt to compute approximate parallel passages for the entire CBETA collection using neural methods.

Nehrdich's approach uses Fasttext word embeddings trained on the CBETA corpus with a skip-gram model, combined with the SWEM (Simple Word-Embedding-based Models) hierarchical pooling strategy and approximate nearest neighbor search via the FAISS library. The method processes the entire CBETA collection (approximately 460 million characters) in roughly three days on four Xeon CPUs, producing a network of candidate parallel passages.

Nehrdich has subsequently contributed to the **MITRA project** (since 2023, in collaboration with Kurt Keutzer at the Berkeley AI Research Lab), developing machine translation models, semantic search functionality, parallel passage detection, and OCR for classical Asian languages. The project's parallel corpus covers Pali, Sanskrit, Buddhist Chinese, and Tibetan. A related publication is "Observations on the Intertextuality of Selected Abhidharma Texts Preserved in Chinese Translation" (*Religions* 14, no. 7 [2023]: 911), which applied these methods to a specific textual family.

Nehrdich's work differs from our pipeline in several ways: his method detects **parallel passages** (semantically similar sections, potentially in different phrasing) using neural embeddings, while our pipeline detects **verbatim or near-verbatim textual containment** using character n-grams and sequence alignment. The neural approach is better at detecting cross-translator parallels; the character-level approach provides exact alignment and precise coverage quantification. The two approaches are complementary.

### 7.6 Jiang Wu and "Mining the Buddhist Canon"

Jiang Wu (吳疆) at the University of Arizona, along with Greg Wilkinson, initiated the "Mining the Buddhist Canon" project, which represents one of the few explicit efforts to apply text mining techniques to study patterns in the Chinese Buddhist canon at scale. Their work explores how computational methods -- including topic modeling, word frequency analysis, and network analysis -- can reveal structural and thematic patterns across the vast corpus.

Wu's edited volume *Spreading the Buddha's Word in East Asia: The Formation and Transformation of the Chinese Buddhist Canon* (New York: Columbia University Press, 2016), co-edited with Lucille Chia, includes contributions on canon formation and structure that provide important context for computational approaches. Wu has also published *Reinventing the Tripitaka: Transformation of the Buddhist Canon in Modern East Asia*, exploring canon formation, textual studies, and digital research tools and methods.

### 7.7 Christoph Anderl and the Ghent Database of Chinese Buddhist Texts

Christoph Anderl at Ghent University has led the development of digital resources for studying Chinese Buddhist texts, with a particular focus on medieval vernacular Chinese in Buddhist literature. While his primary interest is in linguistic analysis rather than text reuse detection, his work on searchable databases of Buddhist vocabulary and his contributions to digital infrastructure for Buddhist studies are part of the broader ecosystem that makes computational approaches possible.

### 7.8 General-Purpose Text Reuse Detection Frameworks

Several general-purpose computational text reuse detection frameworks have been developed that are, in principle, applicable to the Chinese Buddhist canon:

- **TRACER**, developed at the University of Gottingen by Marco Buchler and colleagues as part of the eTRAP (Electronic Textual Reuse Acquisition Project), is a comprehensive text reuse detection framework that has been applied to Latin, Arabic, and other historical corpora. TRACER implements a six-stage pipeline (preprocessing, featuring, selection, linking, scoring, and postprocessing) and supports various similarity measures including character n-grams, word n-grams, and fingerprinting methods.

- **Passim**, developed by David Smith at Northeastern University, is a text reuse detection tool designed for large-scale historical corpora. It has been applied to newspaper archives, Arabic manuscript traditions, and other large collections. Passim's approach, based on local alignment of text passages identified through n-gram shingling, is methodologically similar to our pipeline's candidate generation and alignment stages.

Note that Radich and Norrish's **TACL** (discussed in Section 7.4 above) is purpose-built for the Chinese Buddhist canon and has been productively applied to attribution questions, but it is an interactive exploration tool rather than a batch text reuse detection system.

While general-purpose tools like TRACER and Passim could in principle be applied to the Chinese Buddhist canon, they have not yet been systematically deployed for this purpose. The specific challenges of classical Chinese Buddhist texts (see Section 7.10 below) may require adaptations or purpose-built tools, which is what our pipeline provides.

### 7.9 Computational Studies of the Pali Canon

Relevant methodological parallels can be found in computational studies of the Pali Buddhist canon:

- The **Digital Pali Reader** and related tools developed by Yuttadhammo Bhikkhu and others have enabled searchable access to the Pali Tipitaka.
- **SuttaCentral** (suttacentral.net), founded by Bhikkhu Sujato and Bhikkhu Brahmali, has built a comprehensive database of parallel passages across Pali, Chinese, Tibetan, and Sanskrit Buddhist texts. Their identification of parallels between the Pali Nikayas and Chinese Agamas represents one of the most systematic efforts to map cross-canonical textual relationships, though their methodology relies primarily on manual scholarly identification rather than automated detection.
- **Dhammadana** and other Pali text databases have explored automated parallel detection within the Pali canon.
- Gustav Wynne and Eviatar Shulman have used computational methods to study the chronological stratification of Pali texts based on vocabulary analysis. [*Attribution and publication details should be verified.*]

These Pali-focused efforts provide methodological inspiration but are not directly applicable to the Chinese canon, which presents fundamentally different computational challenges (see Section 7.10).

### 7.10 Challenges Specific to Classical Chinese Buddhist Texts

Several features of classical Chinese Buddhist texts present particular challenges for computational text reuse detection:

- **No word boundaries**: Classical Chinese is written without spaces, and word segmentation is a non-trivial preprocessing step. Buddhist texts further complicate this with specialized terminology, transliterated Sanskrit names (often multi-character), and dharani (sacred syllables). Our pipeline addresses this by operating at the character level rather than the word level, using character n-grams as the fundamental unit of comparison. This avoids the word segmentation problem entirely, though it means the pipeline cannot detect semantic similarity that is not reflected at the character level.

- **Character variation**: The same text may use variant characters (異體字 *yitizi*) in different witnesses, requiring normalization. CBETA's `charDecl` markup addresses this to some extent, providing standardized Unicode representations for variant characters. Our pipeline processes these declarations to normalize text before comparison, but some variant characters may not be fully captured in the markup.

- **Translation vocabulary variation**: Different translators render the same Sanskrit terms differently, meaning that two texts based on the same Indic source may share little surface-level vocabulary if produced by different translators. This is a fundamental limitation of character-level comparison and is directly illustrated by our Heart Sutra results: T250 (same translator as T223, Kumarajiva) shows 73.2% coverage, while T251 (different translator, Xuanzang) shows only 44.6% coverage against the same T223.

- **Formulaic overlap**: Buddhist texts share extensive stock phrases (nidana openings like 如是我聞, merit transfer formulae, colophons, dharani) that may produce spurious matches. Our pipeline addresses this through stop-gram filtering (excluding character n-grams that appear in more than 5% of all texts), but the threshold requires careful tuning.

- **The scale of the corpus**: At approximately 80 million characters across roughly 2,920 texts, the Taisho is large enough that naive all-pairs comparison (roughly 4.3 million text pairs) is computationally expensive, requiring efficient indexing or approximation methods. Our pipeline uses n-gram fingerprinting for candidate generation, reducing the number of pairs that require detailed alignment.

## 8. Recent Scholarship (2015--2026) and Remaining Gaps

### 8.1 Continued Heart Sutra Scholarship

The debate over the Heart Sutra's origins has continued actively since 2015. In addition to Attwood's publications cited above, notable contributions include:

- **Jonathan Silk** has continued to engage with the Heart Sutra question in his broader work on Buddhist textual criticism. His 2019 review article [*exact title and venue should be verified*] addressed methodological issues in the study of Buddhist text composition versus translation.

- **Ishii Kosei** (石井公成) of Komazawa University has published Japanese-language studies examining the Heart Sutra's relationship to the broader Prajnaparamita tradition and its reception in East Asian Buddhism. [*Specific publications should be verified.*]

- The debate has also been taken up in popular and semi-scholarly publications, reflecting growing public interest in the Heart Sutra's origins. Tanahashi's 2014 book brought the scholarly debate to a wider audience, and several subsequent popular treatments have followed.

### 8.2 Digital Humanities Developments (2015--2026)

The period since 2015 has seen significant growth in digital humanities approaches to Buddhist texts:

- **CBETA** has continued to expand its corpus and improve its markup, releasing updated versions of its XML data annually. The adoption of TEI P5b encoding and the availability of CBETA data through GitHub and API access have significantly lowered barriers to computational research.

- **SAT** has expanded its linked data infrastructure and its integration with other digital resources, including collaboration with the Digital Dictionary of Buddhism (DDB, maintained by Charles Muller at the University of Tokyo).

- **Dharma Drum Institute of Liberal Arts** (法鼓文理學院) in Taiwan has continued to develop digital Buddhist studies resources and methods under the leadership of scholars including Hung Jen-Jou (洪振洲) and in collaboration with Bingenheimer.

- **The From the Ground Up project** at the University of British Columbia (led by Chen Jinhua 陳金華) has developed digital resources for studying Chinese Buddhist epigraphy and material culture, complementing text-based approaches.

- **Buddhist Digital Archives** at various institutions (including the British Library's International Dunhuang Project, the National Diet Library's digital collections, and the Digital Archives of Buddhist Temple Records) have made primary source materials more accessible for computational analysis.

### 8.3 Chinese-Language Digital Humanities Work

Chinese-language scholarship on computational approaches to Buddhist texts has grown significantly:

- Researchers at Peking University's Center for Digital Humanities (北京大學數字人文研究中心) have explored text mining approaches to classical Chinese texts, including Buddhist literature.

- The Dharma Drum Institute has published Chinese-language methodological papers on digital approaches to the Chinese Buddhist canon, including work on named entity recognition, text segmentation, and bibliographic data mining.

- Fang Guangchang's continuing work on Dunhuang manuscripts has incorporated digital methods for manuscript comparison and identification, which are methodologically related to text reuse detection.

[*Note: Specific publications in Chinese-language digital humanities journals should be identified and cited. Key venues include Shuzhi renwen* 数字人文 *and* Zhongguo dianji yu wenhua 中國典籍與文化.]

### 8.4 Japanese Digital Humanities

Japanese digital humanities work on Buddhist texts has continued through several channels:

- SAT's ongoing projects at the University of Tokyo represent the most sustained Japanese contribution to digital Buddhist studies.

- The National Institute of Japanese Literature (国文学研究資料館, NIJL) has developed digital infrastructure for classical Japanese texts that includes Buddhist materials.

- IIIF (International Image Interoperability Framework) adoption by Japanese institutions has facilitated the comparison of manuscript witnesses of Buddhist texts.

[*Note: Specific recent Japanese-language publications on digital approaches to the Taisho should be identified.*]

### 8.5 Text Reuse Detection in Buddhist Studies: The Gap

Despite the developments described above, a significant gap remains in the literature: **no previous study has attempted a systematic, corpus-wide computational detection of digest and text reuse relationships across the entire Taisho canon.** The various digital humanities projects described in this section have focused on:

- Making texts accessible (CBETA, SAT)
- Building linked data and ontologies (SAT, DDB)
- Social network analysis of biographical texts (Bingenheimer)
- Topic modeling and thematic analysis (Wu, Wilkinson)
- Named entity recognition (various)
- Cross-canonical parallel identification through manual scholarly judgment (SuttaCentral)

What has not been done -- and what our pipeline provides -- is an automated, scalable approach to detecting textual containment relationships (digests) across all pairs of texts in the canon. The closest prior work is Radich and Norrish's TACL, which enables interactive n-gram comparison of selected texts but does not perform batch digest detection or alignment; and Nehrdich's neural parallel passage detection, which identifies semantically similar passages but does not quantify asymmetric containment. General-purpose text reuse frameworks (TRACER, Passim) have been applied to other historical corpora but not to the Taisho. No previous project has combined n-gram fingerprinting, candidate generation, seed-and-extend alignment, and relationship classification to produce a comprehensive map of digest relationships in the Chinese Buddhist canon.

This gap is significant for several reasons:

1. **Scale**: The Taisho contains approximately 2,920 texts, generating roughly 4.3 million possible text pairs. Manual inspection of this many pairs is infeasible; computational screening is essential.

2. **Unknown unknowns**: The traditional catalogs identify some digest relationships, but as Nattier's Heart Sutra study demonstrated, important digest relationships can go unrecognized for centuries. Only a systematic computational survey can identify relationships that the catalographic tradition missed.

3. **Quantification**: Even for known relationships (e.g., the verse-commentary pairs in Abhidharma literature), precise quantification of textual overlap -- the kind our pipeline provides (coverage percentages, segment lengths, confidence scores) -- has not previously been attempted at scale.

4. **Network analysis**: Understanding how digest relationships form networks (e.g., the encyclopedic compilation clusters around the *Fayuan zhulin*, the vinaya derivation networks, the Prajnaparamita family) requires the kind of comprehensive data that only a corpus-wide survey can provide.

## 9. Emerging Directions and Desiderata

### 9.1 Integration with Indic and Tibetan Evidence

A comprehensive study of digests and retranslations in the Chinese canon should ideally integrate evidence from surviving Sanskrit manuscripts and Tibetan translations. The digitization of Sanskrit Buddhist manuscripts (through projects such as GRETIL at Gottingen, the Sanskrit Buddhist Input Project, and various digitization efforts at Cambridge, Tokyo, and elsewhere) and of the Tibetan canon (through ACIP, BDRC [Buddhist Digital Resource Center, formerly TBRC], and other projects) makes this kind of cross-tradition comparison increasingly feasible.

The 84000 translation project (84000: Translating the Words of the Buddha) is producing new English translations of the Tibetan Kangyur alongside structured metadata about textual relationships, which could be brought to bear on questions of Chinese digest identification. Where a Chinese text classified as a digest has a Tibetan parallel that is clearly translated from an independent Indic source, this would argue against the Chinese-composition hypothesis and in favor of an Indic abbreviation tradition.

### 9.2 Refining the Typology

Current scholarship would benefit from a more refined typology of digest relationships. At minimum, the following subtypes should be distinguished:

- **Simple excerpting**: A passage or passages are extracted verbatim from a longer text with minimal editing. Our pipeline detects these as high-coverage, long-segment-length digest relationships (e.g., the short sutras extracted from Agama collections at 100% coverage).
- **Condensation**: The content of a longer text is summarized or paraphrased, producing a shorter text that shares content but not exact wording. These are harder for character-level comparison to detect and likely appear in our pipeline as digests or shared tradition relationships.
- **Compilation**: Material from multiple source texts is combined into a new text. Our multi-source digest detection (63 cases) identifies some of these.
- **Revision/adaptation**: An existing translation is modified, possibly with reference to a different Indic source or a different Chinese rendering.
- **Creative recomposition**: Material from a source is extracted and reframed with significant new content and a new narrative context. The Heart Sutra is the paradigmatic example.

Each of these subtypes leaves different kinds of textual traces and requires different detection methods. Our pipeline is most effective at detecting simple excerpting and least effective at detecting condensation.

### 9.3 Chronological Analysis

Incorporating dated translator and author information (available from CBETA metadata and traditional Buddhist bibliographic catalogs) would allow the pipeline to assess the chronological plausibility of detected relationships. Currently, the pipeline detects that text A is contained within text B but cannot determine which came first. In many cases, the shorter text predates the longer one (e.g., a sutra that was later incorporated into an encyclopedia), meaning the detected "digest" relationship actually runs in the opposite direction from what the term implies.

### 9.4 Cross-Translator Compensation

Developing a translation-aware matching algorithm -- perhaps using character embedding similarity or translation lexicon equivalences rather than exact character matching -- could improve detection of cross-translator digest relationships. The known Heart Sutra case provides a calibration benchmark: the true coverage should be similar regardless of translator, but our character-level method detects 73% (same translator) versus 45% (different translator). This approximately 30-percentage-point cross-translator gap suggests that many genuine digest relationships involving texts by different translators are being underdetected.

## 10. Conclusion

The study of digests and retranslations in the Taisho Tripitaka draws on a scholarly tradition stretching back to Dao'an in the fourth century CE, through the great catalographers Sengyou and Zhisheng, to modern scholars working in Chinese, Japanese, and English. The Chinese bibliographic tradition established the conceptual categories and provided initial identifications, which the Taisho editors incorporated into their editorial apparatus. Modern Western scholarship, epitomized by Nattier's transformative study of the Heart Sutra, has demonstrated the power of detailed philological comparison for identifying digest relationships. Japanese scholarship has contributed both through the Taisho editorial project itself and through extensive studies of apocryphal texts, translation history, and bibliographic traditions.

Despite this substantial body of scholarship, the systematic enumeration and verification of digest relationships across the entire Taisho has remained an unfinished project until now. The digitization of the canon through CBETA and related projects created the possibility of a comprehensive computational survey, but that possibility had not been realized. The methodological foundations existed -- in text reuse detection algorithms, sequence alignment techniques, and n-gram analysis -- but their application to the specific challenges of the classical Chinese Buddhist corpus required purpose-built tools.

Our computational pipeline fills this gap, detecting 2,812 textual relationships (including 132 excerpts, 533 digests, and 288 retranslations) across 1,412 texts. The pipeline's validation against the Heart Sutra test case -- computationally confirming Nattier's 1992 philological argument with 73.2% coverage of T250 in T223 -- demonstrates that the approach works. The broader results reveal patterns of textual reuse at a scale not previously documented: encyclopedic absorption networks centered on the *Fayuan zhulin*, vinaya derivation chains, Agama extract relationships, dharani collection networks, and the verse-prose pairs of Abhidharma and Yogacara treatises.

The distinction between digests produced in China and shorter texts reflecting genuinely independent Indic sources remains a fundamental analytical challenge, requiring the integration of Chinese, Sanskrit, and Tibetan evidence. But the computational data produced by our pipeline -- particularly the translator-specific matching differentials that serve as a computational signature of Chinese-level composition -- provides a new kind of evidence that complements and extends the philological methods that have been the mainstay of this field.

Much work remains. The 2,812 detected relationships require philological verification; the cross-translator detection gap needs to be addressed through more sophisticated matching algorithms; chronological analysis needs to be integrated to determine directionality; and the results need to be cross-referenced with the traditional catalog classifications. But the foundation for a comprehensive study of textual reuse in the Chinese Buddhist canon is now in place.

## References

### Primary Sources (Buddhist Catalogs)

- Sengyou 僧祐. *Chu sanzang ji ji* 出三藏記集 (Collection of Records Concerning the Tripitaka). T2145.
- Fei Changfang 費長房. *Lidai sanbao ji* 歷代三寶紀 (Record of the Three Jewels Through the Ages). T2034.
- Fajing 法經 et al. *Zhongjing mulu* 眾經目錄 (Catalog of Scriptures). T2146.
- Yancong 彥悰. *Zhongjing mulu* 眾經目錄 (Catalog of Scriptures). T2147.
- Daoxuan 道宣. *Da Tang neidian lu* 大唐內典錄 (Catalog of Inner Texts of the Great Tang). T2149.
- Mingquan 明佺 et al. *Da Zhou kanding zhongjing mulu* 大周刊定眾經目錄. T2153.
- Zhisheng 智昇. *Kaiyuan shijiao lu* 開元釋教錄 (Kaiyuan Catalog of Buddhist Teachings). T2154.

### Modern Scholarship: Western Languages

- Attwood, Jayarava. "Heart Murmurs: Some Problems with Conze's Prajnaparamitahrdaya." *Journal of the Oxford Centre for Buddhist Studies* 8 (2015): 28--48.
- Attwood, Jayarava. "Form is (Not) Emptiness: The Enigma at the Heart of the Heart Sutra." *Journal of the Oxford Centre for Buddhist Studies* 13 (2017): 52--80.
- Attwood, Jayarava. "Epithets of the Mantra in the Heart Sutra." *Journal of the International Association of Buddhist Studies* 40 (2017 [2018]): 305--351.
- Attwood, Jayarava. "A Note on Nisthanirvana in the Heart Sutra." *Journal of the Oxford Centre for Buddhist Studies* 14 (2018): 10--17.
- Attwood, Jayarava. "The Buddhas of the Three Times and the Chinese Origins of the Heart Sutra." *Journal of the Oxford Centre for Buddhist Studies* 15 (2018): 9--27.
- Attwood, Jayarava. "Xuanzang's Relationship to the Heart Sutra in Light of the Fangshan Stele." *Journal of Chinese Buddhist Studies* 32 (2019): 1--30.
- Attwood, Jayarava. "Ungarbling Section VI of the Sanskrit Heart Sutra." *Journal of the Oxford Centre for Buddhist Studies* 18 (2020): 11--41.
- Attwood, Jayarava. "The Chinese Origins of the Heart Sutra Revisited: A Comparative Analysis of the Chinese and Sanskrit Texts." *Journal of the International Association of Buddhist Studies* 44 (2021): 13--52.
- Attwood, Jayarava. "Studying the Heart Sutra." *Buddhist Studies Review* 37, no. 2 (2021): 199--217.
- Attwood, Jayarava. "Preliminary Notes on the Extended Heart Sutra in Chinese." *Asian Literature and Translation* 8, no. 1 (2021): 63--85.
- Attwood, Jayarava. "Heart Sutra Revisited." *Buddhist Studies Review* 39, no. 2 (2023): 229--254.
- Attwood, Jayarava. "Heart to Heart: A Comparative Study of and Commentary on the Chinese and Sanskrit Heart Sutra Texts." *Buddhist Studies Review* 40 (2024).
- Boucher, Daniel. *Bodhisattvas of the Forest and the Formation of the Mahayana: A Study and Translation of the Rastrapalapariprccha-sutra*. Honolulu: University of Hawai'i Press, 2008.
- Buswell, Robert E., ed. *Chinese Buddhist Apocrypha*. Honolulu: University of Hawai'i Press, 1990.
- Conze, Edward. *The Prajnaparamita Literature*. The Hague: Mouton, 1960. Revised edition, Tokyo: The Reiyukai, 1978.
- Funayama Toru 船山徹. "Masquerading as Translation: Examples of Chinese Lectures by Indian Scholar-Monks in the Six Dynasties Period." *Journal of the International Association of Buddhist Studies* 29, no. 2 (2006): 169--230.
- Harrison, Paul. *The Samadhi of Direct Encounter with the Buddhas of the Present: An Annotated English Translation of the Tibetan Version of the Pratyutpanna-Buddha-Sammukhavasthita-Samadhi-Sutra*. Tokyo: International Institute for Buddhist Studies, 1990.
- Harrison, Paul. "The Earliest Chinese Translations of Mahayana Buddhist Sutras: Some Notes on the Works of Lokaksema." *Buddhist Studies Review* 10, no. 2 (1993): 135--177.
- Karashima, Seishi. *A Glossary of Dharmaraksa's Translation of the Lotus Sutra*. Tokyo: International Research Institute for Advanced Buddhology, Soka University, 1998.
- Karashima, Seishi. *A Glossary of Kumarajiva's Translation of the Lotus Sutra*. Tokyo: International Research Institute for Advanced Buddhology, Soka University, 2001.
- Lancaster, Lewis R., and Sung-bae Park. *The Korean Buddhist Canon: A Descriptive Catalogue*. Berkeley: University of California Press, 1979.
- Lusthaus, Dan. "The Heart Sutra in Chinese Yogacara: Some Comparative Comments on the Heart Sutra Commentaries of Woncheuk and Kuiji." *International Journal of Buddhist Thought and Culture* 3 (2003): 59--103.
- Nanjio, Bunyiu. *A Catalogue of the Chinese Translation of the Buddhist Tripitaka, the Sacred Canon of the Buddhists in China and Japan*. Oxford: Clarendon Press, 1883.
- Nattier, Jan. "The Heart Sutra: A Chinese Apocryphal Text?" *Journal of the International Association of Buddhist Studies* 15, no. 2 (1992): 153--223.
- Orsborn, Matthew (Shi Huifeng). "Chiasmus in the Early Prajnaparamita: Literary Parallelism Connecting Criticism and Hermeneutics in an Early Mahayana Sutra." PhD dissertation, University of Hong Kong, 2012.
- Silk, Jonathan A. *Managing Monks: Administrators and Administrative Roles in Indian Buddhist Monasticism*. New York: Oxford University Press, 2008.
- Silk, Jonathan A. "The Heart Sutra in Tibetan: A Critical Edition of the Two Recensions Contained in the Kanjur." *Wiener Zeitschrift fur die Kunde Sudasiens* 38 (1994): 369--418.
- Storch, Tanya. *The History of Chinese Buddhist Bibliography: Censorship and Transformation of the Tripitaka*. Amherst, NY: Cambria Press, 2014.
- Tanahashi, Kazuaki. *The Heart Sutra: A Comprehensive Guide to the Classic of Mahayana Buddhism*. Boulder: Shambhala, 2014.
- Tokuno, Kyoko. "The Evaluation of Indigenous Scriptures in Chinese Buddhist Bibliographical Catalogues." In *Chinese Buddhist Apocrypha*, edited by Robert E. Buswell, 31--74. Honolulu: University of Hawai'i Press, 1990.
- Nehrdich, Sebastian. "A Method for the Calculation of Parallel Passages for Buddhist Chinese Sources Based on Million-scale Nearest Neighbor Search." *Journal of the Japanese Association for Digital Humanities* 5, no. 2 (2020): 132--153.
- Nehrdich, Sebastian. "Observations on the Intertextuality of Selected Abhidharma Texts Preserved in Chinese Translation." *Religions* 14, no. 7 (2023): 911.
- Radich, Michael. "On the Ekottarikagama 增壹阿含經 T 125 as a Work of Zhu Fonian 竺佛念." *Journal of Chinese Buddhist Studies* 30 (2017): 1--31.
- Radich, Michael. "Problems of Attribution, Style, and Dating Relating to the 'Great Cloud Sutras' in the Chinese Buddhist Canon (T 387, T 388/S.6916)." In *Buddhist Transformations and Interactions: Papers in Honor of Antonino Forte*, edited by Victor Mair, Tansen Sen, and Chen Jinhua, 2017.
- Wu, Jiang, and Lucille Chia, eds. *Spreading the Buddha's Word in East Asia: The Formation and Transformation of the Chinese Buddhist Canon*. New York: Columbia University Press, 2016.
- Zacchetti, Stefano. *In Praise of the Light: A Critical Synoptic Edition with an Annotated Translation of Chapters 1--3 of Dharmaraksa's Guang zan jing*. Tokyo: International Research Institute for Advanced Buddhology, Soka University, 2005.
- Zacchetti, Stefano. *The Da zhidu lun 大智度論 (\*Mahaprajnaparamitopadesa) and the History of the Larger Prajnaparamita*. Edited by Michael Radich and Jonathan Silk. Hamburg Buddhist Studies 14. Hamburg: Hamburg University Press, 2021.
- Zurcher, Erik. *The Buddhist Conquest of China: The Spread and Adaptation of Buddhism in Early Medieval China*. 2 vols. Leiden: Brill, 1959. 3rd edition, 2007.
- Zurcher, Erik. "A New Look at the Earliest Chinese Buddhist Texts." In *From Benares to Beijing: Essays on Buddhism and Chinese Religion in Honour of Prof. Jan Yun-Hua*, edited by Koichi Shinohara and Gregory Schopen, 277--304. Oakville, ON: Mosaic Press, 1991.

### Modern Scholarship: Chinese Language

- Fang Guangchang 方廣錩. *Fojiao dazangjing shi: ba--shi shiji* 佛教大藏經史：八——十世紀 (A History of the Buddhist Canon: 8th to 10th Centuries). Beijing: Zhongguo shehui kexue chubanshe, 1991.
- Fang Guangchang 方廣錩. *Zhongguo xieben dazangjing yanjiu* 中國寫本大藏經研究 (Studies on Chinese Manuscript Canons). Shanghai: Shanghai guji chubanshe, 2006.
- Ji Yun 紀贇. [Articles on the Heart Sutra and Chinese Buddhist bibliography, published in various Chinese-language journals.] [*Specific titles and publication details should be verified.*]
- Li Fuhua 李富華 and He Mei 何梅. *Hanwen fojiao dazangjing yanjiu* 漢文佛教大藏經研究 (Studies on the Chinese Buddhist Canon). Beijing: Zongjiao wenhua chubanshe, 2003.
- Lu Cheng 呂澂. *Zhongguo foxue yuanliu luejiang* 中國佛學源流略講 (A Brief Account of the Origins and Development of Chinese Buddhism). Beijing: Zhonghua shuju, 1979.
- Tang Yongtong 湯用彤. *Han Wei Liang Jin Nanbeichao fojiao shi* 漢魏兩晉南北朝佛教史 (History of Buddhism during the Han, Wei, Two Jin, and Northern and Southern Dynasties). Beijing: Zhonghua shuju, 1938. Reprinted 1983.

### Modern Scholarship: Japanese Language

- Fukui Fumimasa 福井文雅. *Hannya shingyo no sogo teki kenkyu* 般若心経の総合的研究 (Comprehensive Study of the Heart Sutra). Tokyo. [*Publisher and exact year should be verified; possibly 1987 initial edition, 2000 revised edition.*]
- Funayama Toru 船山徹. *Butten wa do kanyaku sareta no ka: Sutora ga Chugokugo ni naru toki* 仏典はどう漢訳されたのか：スートラが中国語になるとき. Tokyo: Iwanami shoten, 2013.
- Hayashiya Tomojiro 林屋友次郎. *Kyoroku kenkyu* 經錄研究 (Studies on Scriptural Catalogs). Tokyo: Iwanami shoten, 1941.
- Makita Tairyo 牧田諦亮. *Gikyo kenkyu* 疑經研究 (Studies on Apocryphal Sutras). Kyoto: Kyoto daigaku Jinbun kagaku kenkyujo, 1976.
- Ono Genmyo 小野玄妙, ed. *Bussho kaisetsu daijiten* 佛書解説大辭典 (Great Dictionary of Explanations of Buddhist Texts). 12 vols. plus supplement. Tokyo: Daito shuppansha, 1933--1936. Reprint 1964--1988.

### Digital Resources

- 84000: Translating the Words of the Buddha. https://84000.co/
- Buddhist Digital Resource Center (BDRC). https://www.tbrc.org/
- CBETA (Chinese Buddhist Electronic Text Association). https://www.cbeta.org/
- Chinese Buddhist Canonical Attributions database (CBC@). https://dazangthings.nz/cbc/
- Digital Dictionary of Buddhism (DDB). http://www.buddhism-dict.net/ddb/
- GRETIL (Gottingen Register of Electronic Texts in Indian Languages). http://gretil.sub.uni-goettingen.de/
- MITRA Project (Machine Translation and Semantic Retrieval for Buddhist Texts). https://github.com/BuddhaNexus/
- Passim (text reuse detection). https://github.com/dasmiq/passim
- SAT Daizokyo Text Database. https://21dzk.l.u-tokyo.ac.jp/SAT/
- SuttaCentral. https://suttacentral.net/
- TACL (Textual Analysis for Corpus Linguistics). https://github.com/ajenhl/tacl
- TRACER (text reuse detection framework). https://www.etrap.eu/

### Computational Text Reuse Detection (General)

- Buchler, Marco, et al. "Towards a Historical Text Re-use Detection." In *Text Mining: From Ontology Learning to Automated Text Processing Applications*, edited by Chris Biemann and Alexander Mehler, 221--238. Cham: Springer, 2014. [*Publication details should be verified.*]
- Smith, David A., Ryan Cordell, and Abby Mullen. "Computational Methods for Uncovering Reprinted Texts in Antebellum Newspapers." *American Literary History* 27, no. 3 (2015): E1--E15. [*Publication details should be verified.*]
