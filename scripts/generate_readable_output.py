#!/usr/bin/env python3
"""
Generate a human-readable Markdown report of digest relationships.

Reads:
  - results/digest_relationships.json
  - data/metadata.json

Writes:
  - results/digest_relationships_readable.md

Usage:
  python3 scripts/generate_readable_output.py

Requires:
  pip3 install pypinyin
"""

import json
from pathlib import Path
from pypinyin import pinyin, Style

# ---------------------------------------------------------------------------
# Hardcoded lookup: text_id -> English translation of the title.
#
# Covers ALL T08 texts (Prajnaparamita volume) and every text appearing 3+
# times in the relationship data, plus other important texts.
#
# Pinyin is generated automatically from the Chinese title via pypinyin.
# ---------------------------------------------------------------------------

ENGLISH_LOOKUP = {
    # =====================================================================
    # T08 -- Prajnaparamita Section (complete volume)
    # =====================================================================
    "T08n0221": "Prajnaparamita Sutra (Pancavimsatisahasrika, tr. Mokshala)",
    "T08n0222": "Sutra of Radiant Praise (Prajnaparamita, tr. Dharmaraksha)",
    "T08n0223": "Mahaprajnaparamita Sutra (tr. Kumarajiva)",
    "T08n0224": "Sutra on the Practice of Prajna (Ashtasahasrika, tr. Lokakshema)",
    "T08n0225": "Sutra of Great Illumination (Ashtasahasrika, tr. Zhi Qian)",
    "T08n0226": "Abridged Mahaprajnaparamita Sutra",
    "T08n0227": "Small Section Prajnaparamita Sutra (tr. Kumarajiva)",
    "T08n0228": "Sutra of the Buddha-Mother Producing the Three Dharma Treasuries (Ashtasahasrika, tr. Shihu)",
    "T08n0229": "Sutra of the Buddha-Mother's Treasury of Precious Virtues",
    "T08n0230": "Holy Ashtasahasrika Prajnaparamita 108 True Meanings Dharani Sutra",
    "T08n0231": "Devaraja Prajnaparamita Sutra (tr. Upasunyata)",
    "T08n0232": "Manjusri's Mahaprajnaparamita Sutra (tr. Mandrasena)",
    "T08n0233": "Manjusri's Prajnaparamita Sutra (tr. Samghavarman)",
    "T08n0234": "Sutra on Bodhisattva Rushou's Supreme Pure Alms-Gathering",
    "T08n0235": "Diamond Sutra (Vajracchedika, tr. Kumarajiva)",
    "T08n0236a": "Diamond Sutra (Vajracchedika, tr. Bodhiruci)",
    "T08n0236b": "Diamond Sutra (Vajracchedika, tr. Bodhiruci, alt.)",
    "T08n0237": "Diamond Sutra (Vajracchedika, tr. Paramartha)",
    "T08n0238": "Diamond Cutter Prajnaparamita Sutra (tr. Dharmagupta)",
    "T08n0239": "Diamond Cutter Prajnaparamita Sutra (tr. Xuanzang)",
    "T08n0240": "True Nature Prajnaparamita Sutra",
    "T08n0241": "Vajrasekhara Yoga Principle Prajna Sutra",
    "T08n0242": "Sutra of All-Illuminating Prajnaparamita",
    "T08n0243": "Adhyardhasatika Prajnaparamita (Great Bliss Vajra True Samaya Sutra)",
    "T08n0244": "Supreme Fundamental Great Bliss Vajra Amoghavajra Samadhi Sutra",
    "T08n0245": "Benevolent King Prajnaparamita Sutra (tr. Kumarajiva)",
    "T08n0246": "Benevolent King Prajnaparamita Sutra for National Protection (tr. Amoghavajra)",
    "T08n0247": "Sutra of Definitive-Meaning Prajnaparamita",
    "T08n0248": "Fifty-Verse Holy Prajnaparamita Sutra",
    "T08n0249": "Indra's Prajnaparamita Heart Sutra",
    "T08n0250": "Great Prajnaparamita Dharani Sutra (Heart Sutra, tr. Kumarajiva)",
    "T08n0251": "Heart Sutra (Prajnaparamitahrdaya, tr. Xuanzang)",
    "T08n0252": "Heart Sutra of Universal Wisdom Treasury (tr. Dharma Master Fabao)",
    "T08n0253": "Heart Sutra (tr. Prajnacakra)",
    "T08n0254": "Heart Sutra (tr. Prajna)",
    "T08n0255": "Heart Sutra (tr. Zhimingzang)",
    "T08n0256": "Chinese-Sanskrit Phonetic Heart Sutra",
    "T08n0257": "Holy Buddha-Mother Prajnaparamita Sutra (tr. Shihu)",
    "T08n0258": "Holy Buddha-Mother Short-form Prajnaparamita Sutra",
    "T08n0259": "Visualization of Buddha-Mother Prajnaparamita Bodhisattva Sutra",
    "T08n0260": "Sutra of Awakening to Self-Nature Prajnaparamita",
    "T08n0261": "Mahayana Principle of the Six Paramitas Sutra",
    # =====================================================================
    # Mahaprajnaparamita (other volumes of T0220)
    # =====================================================================
    "T05n0220": "Mahaprajnaparamita Sutra (fasc. 1-200, tr. Xuanzang)",
    "T06n0220": "Mahaprajnaparamita Sutra (fasc. 201-400, tr. Xuanzang)",
    "T07n0220": "Mahaprajnaparamita Sutra (fasc. 401-600, tr. Xuanzang)",
    # =====================================================================
    # Encyclopedias, anthologies, catalogues
    # =====================================================================
    "T53n2122": "Forest of Gems in the Garden of the Dharma (encyclopedia by Daoshi)",
    "T53n2121": "Anomalous Features of Sutras and Vinaya (compiled by Baochang)",
    "T54n2123": "Essential Collection from Various Sutras",
    "T54n2128": "Pronunciations and Meanings in All Sutras (by Huilin)",
    "T54n2129": "Continuation of Pronunciations and Meanings in All Sutras",
    "T55n2145": "Catalogue of All Sutras (by Fajing)",
    "T55n2146": "Catalogue of All Sutras (by Yancong)",
    "T55n2147": "Catalogue of All Sutras (by Jingtai)",
    "T55n2148": "Great Tang Inner Canon Record (by Daoxuan)",
    "T55n2149": "Record of Ancient and Modern Sutra Translations",
    "T55n2150": "Continuation of the Great Tang Inner Canon Record",
    "T55n2151": "Great Zhou Catalogue of All Sutras",
    "T55n2152": "Abridged Kaiyuan Catalogue of Buddhist Teachings",
    "T55n2153": "Zhenyuan Era Newly Revised Catalogue (Abridged)",
    "T55n2154": "Kaiyuan Era Catalogue of Buddhist Teachings (by Zhisheng)",
    "T55n2155": "Buddhist Catalogue (T55n2155)",
    "T55n2156": "Great Tang Zhenyuan Continuation of the Kaiyuan Buddhist Catalogue",
    "T55n2157": "Zhenyuan Era Newly Revised Catalogue of Buddhist Teachings",
    "T55n2158": "Buddhist Catalogue (T55n2158)",
    "T55n2161": "Catalogue of Items Requested (Goshorai Mokuroku, by Kukai)",
    "T55n2162": "Catalogue of the Great Master's Authentic Writings",
    "T55n2165": "Buddhist Catalogue (T55n2165)",
    "T55n2166": "Buddhist Catalogue (T55n2166)",
    "T55n2167": "Catalogue of Newly Sought Teachings Brought to Japan",
    "T55n2168A": "Catalogue of Texts by Vinaya Master Eun (A)",
    "T55n2168B": "Catalogue of Texts by Vinaya Master Eun (B)",
    "T55n2169": "Buddhist Catalogue (T55n2169)",
    "T55n2171": "Catalogue of Dharma Sought at Qinglong Temple",
    "T55n2172": "Catalogue of Dharma Sought in China by Japanese Monk Enchin",
    "T55n2173": "Catalogue of Items Brought Back by Great Master Chisho",
    "T55n2174A": "Buddhist Catalogue (A)",
    "T55n2174B": "Buddhist Catalogue (B)",
    "T55n2175": "Catalogue of Extra-Canonical Texts",
    "T55n2176": "Buddhist Catalogue (T55n2176)",
    "T55n2178": "Buddhist Catalogue (T55n2178)",
    "T55n2182": "Buddhist Catalogue (T55n2182)",
    "T55n2183": "Buddhist Catalogue (T55n2183)",
    # =====================================================================
    # Chan / Zen texts
    # =====================================================================
    "T48n2016": "Records of the Mirror of the Source (by Yongming Yanshou)",
    "T48n2010": "Platform Sutra of the Sixth Patriarch",
    "T48n2009": "Inscription on Faith in Mind (by Sengcan)",
    "T48n2013": "Gateless Gate (Wumen Guan / Mumonkan)",
    "T48n2014": "Record of the Congrong Hermitage (Book of Serenity)",
    "T48n2023": "Records of the Ancestral Mirror",
    "T51n2076": "Jingde Era Record of the Transmission of the Lamp",
    "T51n2077": "Continued Lamp Record of the Jianzhong Jingguo Era",
    "T51n2079": "Record of Spreading Fragrance",
    "T47n1958": "Treatise on the Pure Land",
    "T47n1961": "Ten Essentials of Pure Land",
    "T47n1963": "Nagarjuna's Expanded Pure Land Texts",
    "T47n1965": "Essentials Record of Pure Land Sutras",
    "T47n1969A": "Collected Writings on the Land of Bliss",
    "T47n1978": "Collection on the Return of All Good to One Goal",
    "T47n1980": "Guishan's Admonitions",
    "T47n1982": "Collected Repentance Liturgies from Various Sutras",
    "T47n1994B": "Preface to Chan Source Collection (B)",
    "T47n1998A": "Song of Realizing the Way",
    # =====================================================================
    # Hua-yen / Avatamsaka
    # =====================================================================
    "T09n0278": "Avatamsaka Sutra (60 fasc., tr. Buddhabhadra)",
    "T10n0279": "Avatamsaka Sutra (80 fasc., tr. Sikshananda)",
    "T10n0286": "Sutra of the Ten Stages (Dasabhumika)",
    "T10n0287": "Sutra of the Ten Stages (alt. tr.)",
    "T10n0289": "Sutra of the Treasure of Luomona",
    "T10n0290": "Tathagata's Heart Dharani Sutra",
    "T10n0293": "Avatamsaka Sutra (40 fasc. Gandavyuha, tr. Prajna)",
    "T10n0294": "Inconceivable Buddha-Realm Chapter of the Avatamsaka",
    "T10n0295": "Avatamsaka: Entering the Dharma-Realm Chapter",
    "T10n0298": "Avatamsaka: Entering the Dharma-Realm Chapter (tr. Divakara)",
    "T10n0302": "Avatamsaka Sutra (partial)",
    "T35n1733": "Commentary on the Avatamsaka Sutra",
    "T36n1736": "Sub-commentary on the Avatamsaka Sutra (by Chengguan)",
    "T36n1737": "Commentary on the Avatamsaka Sutra (by Chengguan)",
    "T36n1739": "Record of Exploring the Profundities of the Avatamsaka (by Fazang)",
    "T36n1742": "Internal Chapters of the Avatamsaka",
    "T36n1743": "Record of Exploring Profundities (alt.)",
    # =====================================================================
    # Lotus Sutra
    # =====================================================================
    "T09n0262": "Lotus Sutra (Saddharmapundarika, tr. Kumarajiva)",
    # =====================================================================
    # Mahaparinirvana
    # =====================================================================
    "T12n0374": "Mahaparinirvana Sutra (tr. Dharmakshema, 40 fasc.)",
    "T12n0375": "Mahaparinirvana Sutra (tr. Huiyan et al., 36 fasc.)",
    # =====================================================================
    # Pure Land
    # =====================================================================
    "T12n0336": "Akshobhya Buddha's Realm Sutra",
    "T12n0339": "Srimaladevi Sutra (Queen Srimala)",
    "T12n0340": "Srimala Lion's Roar Sutra",
    "T12n0341": "Great Vaipulya Three-Levels Assembly Sutra",
    "T12n0348": "Sutra of Perfect Enlightenment (Yuanjue Jing)",
    "T12n0353": "Medicine Buddha (Bhaisajyaguru) Sutra",
    "T12n0355": "Sutra of Immeasurable Life (tr. Samghavarman)",
    "T12n0357": "Amitabha Root Secret Mantra Sutra",
    "T12n0358": "Radiance Dharani Sutra",
    "T12n0360": "Sutra of Immeasurable Life (Larger Sukhavativyuha)",
    "T12n0361": "Sutra of Immeasurable Purity and Equal Enlightenment",
    "T12n0362": "Amitabha Triple-Sutra Translation",
    "T12n0364": "Amitabha Sutra (alt. tr.)",
    "T12n0366": "Amitabha Sutra (Smaller Sukhavativyuha, tr. Kumarajiva)",
    "T12n0367": "Amitabha Sutra (Amitabha section)",
    "T12n0369": "Mahayana Sutra of Immeasurable Life Adornment",
    "T12n0370": "Greater Amitabha Sutra",
    "T12n0387": "Nirvana Sutra (shorter)",
    "T12n0389": "Great Golden Peacock King Mantra Sutra",
    "T12n0396": "Great Katyayana's Questions Sutra",
    # =====================================================================
    # Agamas
    # =====================================================================
    "T01n0026": "Middle-Length Discourses (Madhyamagama)",
    "T01n0053": "Sutra in Forty-Two Sections",
    "T01n0060": "Collection of Original Acts of the Buddha Sutra",
    "T01n0079": "Sutra of the Buddha's Birth",
    "T01n0082": "Sutra of Heaven and Earth",
    "T01n0093": "Sutra of the Saintly Person",
    "T02n0099": "Connected Discourses (Samyuktagama)",
    "T02n0102": "Miscellaneous Agama Sutra",
    "T02n0110": "Sutra of the Three Turnings of the Dharma Wheel",
    "T02n0115": "Sutra of the Horse with Eight Faults as a Metaphor for People",
    "T02n0119": "Sutra of Corresponding Connections",
    "T02n0122": "Varanasi Sutra",
    "T02n0124": "Middle-Length Agama Sutra (selected)",
    "T02n0125": "Numerical Discourses (Ekottaragama, tr. Gautama Sanghadeva)",
    "T02n0128b": "Sutra of Arising Practice (B)",
    "T02n0131": "Sutra of Distinguishing Good Deeds",
    "T02n0132a": "Sutra of the Four Truths (A)",
    "T02n0132b": "Sutra of the Four Truths (B)",
    "T02n0133": "Sutra of the Original Signs (Itivuttaka)",
    "T02n0134": "Sutra of the Dharma Ocean",
    "T02n0136": "Sutra of One Foot",
    "T02n0138": "Sutra of Eleven Contemplations on the Tathagata",
    "T02n0139": "Sutra in Forty-Two Sections (alt.)",
    "T02n0140": "Sutra of Dharma Worship",
    "T02n0146": "Sutra of Six Collections",
    "T02n0147": "Sutra of Auspicious Collections",
    "T02n0148": "Sutra of Auspicious Treasury",
    "T02n0149": "Sutra of Ananda Asking about Auspicious and Inauspicious",
    "T02n0150B": "Sutra of Seven Places and Three Contemplations (B)",
    # =====================================================================
    # Vinaya texts
    # =====================================================================
    "T22n1421": "Five-Part Vinaya of the Mahishasaka School",
    "T22n1422a": "Five-Part Precepts (A)",
    "T22n1422b": "Five-Part Precepts (B)",
    "T22n1423": "Mahishasaka Bhikkhuni Precepts",
    "T22n1424": "Mahishasaka Karmavacana",
    "T22n1425": "Mahasanghika Vinaya",
    "T22n1426": "Mahasanghika Bhikkhu Precepts",
    "T22n1427": "Mahasanghika Bhikkhuni Precepts",
    "T22n1428": "Four-Part Vinaya (Dharmaguptaka Vinaya)",
    "T22n1429": "Four-Part Vinaya Bhikkhu Precepts",
    "T22n1430": "Four-Part Sangha Precepts",
    "T22n1431": "Four-Part Bhikkhuni Precepts",
    "T22n1432": "Dharmaguptaka Miscellaneous Karmavacana",
    "T22n1433": "Karmavacana (Sangha Proceedings)",
    "T22n1434": "Four-Part Bhikkhuni Karmavacana",
    "T23n1435": "Ten-Recitation Vinaya (Sarvastivada Vinaya)",
    "T23n1436": "Sarvastivada Pratimoksha",
    "T23n1437": "Sarvastivada Bhikkhuni Pratimoksha",
    "T23n1438": "Sarvastivada Karmavacana",
    "T23n1439": "Sarvastivada Karmavacana (alt.)",
    "T23n1442": "Mulasarvastivada Vinaya",
    "T23n1443": "Mulasarvastivada Vinaya: Going Forth",
    "T24n1449": "Sarvastivada Vinaya Abstract",
    "T24n1450": "Mulasarvastivada Vinaya: Sangha Miscellany",
    "T24n1451": "Mulasarvastivada Bhikkhuni Vinaya",
    "T24n1453": "Sarvastivada Vinaya Abstract (alt.)",
    "T24n1454": "Mulasarvastivada Vinaya Sutra",
    "T24n1455": "Mulasarvastivada Vinaya Verses",
    "T24n1458": "Brahmajala Sutra (Bodhisattva Precepts)",
    "T24n1460": "Bodhisattva Necklace Original Karma Sutra",
    "T24n1462": "Upasaka Precepts Sutra",
    "T24n1467a": "Sutra on the Gravity of Offenses Against the Precepts (A)",
    "T24n1467b": "Sutra on the Gravity of Offenses Against the Precepts (B)",
    "T24n1468": "Bodhisattva Precepts",
    "T24n1483a": "Maudgalyayana's Questions on 500 Vinaya Matters (A)",
    "T24n1483b": "Maudgalyayana's Questions on 500 Vinaya Matters (B)",
    "T24n1484": "Karmavacana",
    "T24n1487": "Supplementary Karmavacana to the Four-Part Vinaya",
    "T24n1490": "Three Thousand Deportments of a Great Bhikkhu",
    "T24n1499": "Four-Part Bhikkhu Nidana Karmavacana",
    "T24n1500": "Miscellaneous Notes on the Four-Part Vinaya",
    "T24n1501": "Commentary on the Bodhisattva Precepts (Bodhisattva-sila-sutra Upadesa)",
    "T24n1502": "Commentary on the Bodhisattva Precepts (alt.)",
    "T40n1804": "Abridged and Supplemented Commentary on the Four-Part Vinaya (by Daoxuan)",
    "T40n1805": "Sub-commentary on Daoxuan's Vinaya Commentary",
    "T40n1806": "Correction Notes on Daoxuan's Vinaya Commentary",
    "T40n1808": "Vinaya Commentary",
    "T40n1809": "Sangha Karmavacana (by Daoxuan)",
    "T40n1810": "Bhikkhuni Karmavacana (by Daoxuan)",
    "T40n1814": "Commentary on the Bhikkhu Precepts",
    "T40n1816": "Record of Aid for the Four-Part Vinaya Commentary",
    "T85n2783": "Dunhuang Document (vinaya-related)",
    "T85n2787": "Excerpts from the Four-Part Vinaya (Dunhuang)",
    "T85n2788": "Excerpts from the Four-Part Vinaya (Dunhuang, alt.)",
    "T85n2791": "Abridged Bhikkhu Deportment Following the Four-Part Vinaya (Dunhuang)",
    # =====================================================================
    # Major Mahayana sutras
    # =====================================================================
    "T11n0310": "Great Jewel-Heap Sutra (Maharatnakuta, tr. Bodhiruci et al.)",
    "T11n0312": "Mahayana Bodhisattva Treasury True Dharma Sutra (by Shaoli)",
    "T11n0314": "Inconceivable Secrets of the Tathagata Mahayana Sutra",
    "T11n0316": "Mahayana Bodhisattva Treasury True Dharma Sutra (by Tianxizai)",
    "T11n0319": "Great Jewel-Heap Sutra (partial)",
    "T13n0397": "Great Vaipulya Collection Sutra (Mahasannipata)",
    "T13n0405": "Great Collection: Questions of Akashagarbha Bodhisattva Sutra",
    "T13n0406": "Akashagarbha Bodhisattva Sutra (continued)",
    "T13n0407": "Akashagarbha Bodhisattva Sutra (tr. Buddhasanta)",
    "T13n0408": "Akashagarbha Bodhisattva Dharani Sutra",
    "T14n0475": "Vimalakirti Sutra (tr. Kumarajiva)",
    "T16n0663": "Suvarnaprabhasa-sutra (Golden Light Sutra, tr. Dharmakshema)",
    "T16n0664": "Combined Golden Light Sutra",
    "T16n0665": "Sutra of Deep Secret Liberation (Samdhinirmocana)",
    "T16n0668": "Mahayana Questions of Maitreya Sutra",
    "T16n0670": "Mahayana Sutra of Shared Practice",
    "T16n0672": "Lankavatara Sutra (Mahayana Entering Lanka)",
    "T16n0675": "Mahayana Madhyamaka Treatise",
    "T16n0676": "Mahayana Sun-Moon Radiance Sutra",
    "T16n0678": "Mahayana Six Paramitas Sutra",
    "T16n0680": "Mahayana Mind-Ground Contemplation Sutra",
    "T16n0684": "Kasyapa Sutra",
    "T16n0685": "Sutra of Firm Purity",
    "T16n0686": "Manjusri Anomalous Features Sutra",
    "T16n0688": "Sutra of the Merit of Flower Garlands",
    "T16n0689": "Sutra of Rare and Comparative Merits (tr. Shihu)",
    "T16n0690": "Sutra of Rare and Comparative Merits",
    "T16n0691": "Supreme Root Mahayana True Dharma Sutra",
    "T16n0701": "Sutra on the Merits of Making Images",
    "T16n0709": "Heaven-Earth Eight Aspects Divine Mantra Sutra",
    "T16n0711": "Abhiseka Sutra (T16 version)",
    "T16n0712": "Abhiseka Karmavacana",
    # =====================================================================
    # Yogacara / Madhyamaka / Treatises
    # =====================================================================
    "T25n1509": "Great Treatise on the Perfection of Wisdom (Mahaprajnaparamita-sastra, attr. Nagarjuna)",
    "T25n1510a": "Treatise on the Diamond Sutra (A)",
    "T25n1510b": "Treatise on the Diamond Sutra (B)",
    "T25n1511": "Treatise on the Diamond Sutra (tr. Bodhiruci)",
    "T25n1512": "Diamond Immortal Treatise (Vajra Commentary)",
    "T25n1515": "Commentary on the Benevolent King Prajnaparamita Sutra",
    "T26n1520": "Dasabhumika-vibhasha-sastra (Ten-Stage Commentary, attr. Nagarjuna)",
    "T26n1524": "Mulamadhyamaka-karika (Middle Treatise, tr. Kumarajiva)",
    "T26n1525": "Twelve Gate Treatise (Dvadasamukha-sastra)",
    "T26n1531": "Tattvasiddhi-sastra (Treatise on Establishing the Truth)",
    "T26n1537": "Four Agamas Outline Commentary",
    "T26n1540": "Abhidharma Dharmajnana Treatise",
    "T27n1545": "Abhidharma Mahavibhasha-sastra",
    "T28n1554": "Abhidharma Vibhasha Treatise",
    "T29n1558": "Abhidharmakosa-sastra (tr. Xuanzang)",
    "T29n1560": "Commentary on the Abhidharmakosa",
    "T29n1561": "Abhidharma Nyayanusara-sastra",
    "T29n1562": "Abhidharma Summary Treatise",
    "T30n1579": "Treatise on the Stages of Yoga Practice (Yogacarabhumi-sastra, tr. Xuanzang)",
    "T30n1580": "Commentary on the Yogacarabhumi (by Jinaprabha)",
    "T30n1581": "Commentary on the Yogacarabhumi (alt.)",
    "T30n1582": "Treatise on the Establishment of Consciousness-Only (Vijnaptimatratasiddhi)",
    "T31n1585": "Summary of the Great Vehicle (Mahayanasamgraha, tr. Buddhasanta)",
    "T31n1586": "Summary of the Great Vehicle (tr. Paramartha)",
    "T31n1590": "Commentary on the Mahayanasamgraha",
    "T31n1593": "Commentary on the Summary of the Great Vehicle (by Vasubandhu, tr. Paramartha)",
    "T31n1594": "Commentary on the Summary of the Great Vehicle (by Vasubandhu, tr. Xuanzang)",
    "T31n1595": "Commentary on the Summary of the Great Vehicle (by Asvabhava, tr. Paramartha)",
    "T31n1596": "Commentary on the Summary of the Great Vehicle (by Asvabhava, tr. Xuanzang)",
    "T31n1597": "Commentary on the Summary of the Great Vehicle (by Dharmapala)",
    "T31n1598": "Commentary on the Summary of the Great Vehicle (by Jinaprabha)",
    "T31n1601": "Treatise on Discriminating the Middle from the Extremes (Madhyantavibhaga-karika)",
    "T31n1614": "Mahayana Ornament Treatise (Mahayanasutralamkara)",
    "T31n1624": "Treatise on the Middle Way (Madhyamaka-sastra extract)",
    "T32n1628": "Hetuvidya Nyayamukha (Treatise on the Gate of Correct Reasoning)",
    "T32n1666": "Awakening of Faith in the Mahayana (attr. Asvaghosa)",
    "T32n1667": "Awakening of Faith in the Mahayana (tr. Sikshananda)",
    "T32n1668": "Commentary on the Awakening of Faith (by Fazang)",
    # =====================================================================
    # Diamond Sutra commentaries
    # =====================================================================
    "T33n1699": "Commentary and Panegyric on the Diamond Sutra",
    "T33n1700": "Panegyric Commentary on the Diamond Sutra",
    "T33n1701": "Essentials from Commentaries on the Diamond Sutra",
    "T33n1702": "Diamond Sutra Essentials Definitive Record",
    "T33n1703": "Annotated Diamond Sutra",
    "T33n1704": "Diamond Sutra Annotations (alt.)",
    "T85n2732": "Layman Fu's (Liang Dynasty) Verses on the Diamond Sutra",
    "T85n2733": "Imperial Commentary on the Diamond Sutra",
    "T85n2735": "Diamond Sutra Commentary (Dunhuang)",
    "T85n2736": "Diamond Sutra Commentary (Dunhuang, alt.)",
    "T85n2737": "Commentary on the Diamond Sutra (Dunhuang)",
    "T85n2739": "Interlinear Commentary on the Diamond Sutra",
    # =====================================================================
    # Heart Sutra commentaries
    # =====================================================================
    "T33n1707": "Commentary on the Benevolent King Sutra (by Jizang)",
    "T33n1708": "Commentary on the Benevolent King Sutra (by Liangbi)",
    "T33n1709": "Sub-commentary on the Benevolent King Sutra",
    "T33n1710": "Brief Commentary on the Heart Sutra (by Fazang)",
    "T33n1711": "Praising the Heart Sutra (by Kuiji)",
    "T33n1712": "Commentary on the Heart Sutra (by Jingmai)",
    "T33n1714": "Annotated Heart Sutra",
    "T85n2745": "Heart Sutra Commentary (Dunhuang)",
    "T85n2746": "Heart Sutra Commentary (Dunhuang, alt.)",
    "T85n2747": "Interlinear Commentary on the Heart Sutra",
    # =====================================================================
    # Esoteric / Tantric texts
    # =====================================================================
    "T18n0848": "Mahavairocana Sutra (Mahavairochana-abhisambodhi-tantra)",
    "T18n0850": "Abhiseka Sutra",
    "T18n0852a": "Mahavairocana Lotus Womb Mandala Great Accomplishment Ritual (A)",
    "T18n0852b": "Mahavairocana Lotus Womb Mandala Great Accomplishment Ritual (B)",
    "T18n0853": "Great Akashagarbha Bodhisattva Recitation Method",
    "T18n0856": "Commentary on the Sutra of Resolving the Deep Secrets",
    "T18n0857": "Surangama Sutra (Shurangama Tantra)",
    "T18n0858": "Abbreviated Five-Branch Recitation of the Mahavairocana",
    "T18n0864A": "Amoghapasa Dharani (A)",
    "T18n0876": "Amoghapasa Heart Dharani Sutra",
    "T18n0878": "Amoghapasa Dharani Sovereign King Mantra Sutra",
    "T18n0879": "Amoghapasa Dharani Ritual Sutra",
    "T18n0880": "Nirvana Dharani Sutra for Becoming a Buddha",
    "T18n0900": "Cintamani-cakra Dharani Sutra",
    "T18n0901": "Dharani Collection Sutra",
    "T19n0923": "Surangama Sutra",
    "T19n0924A": "Surangama Sutra (A)",
    "T19n0924C": "Surangama Sutra (C)",
    "T19n0934": "Usnisa White Light Samadhi Sutra",
    "T19n0939": "Sutra of Knowing Measures and Cultivating Practice",
    "T19n0950": "Dharani Sutra (T19 version)",
    "T19n0954A": "Mahayana Adornment Jewel-King Sutra (A)",
    "T19n0974A": "Usnisa Vijaya Dharani Sutra (A)",
    "T19n0974C": "Usnisa Vijaya Dharani Sutra (C)",
    "T19n0974D": "Usnisa Vijaya Dharani Sutra (D)",
    "T19n0974E": "Usnisa Vijaya Dharani Sutra (E)",
    "T19n0987": "Dharani Collection Sutra (T19 version)",
    "T19n0988": "Miscellaneous Dharani Collection",
    "T19n0989": "Six-Syllable Sovereign Mantra Sutra",
    "T19n0991": "Sutra of Great Cloud Wheel Requesting Rain",
    "T19n0992": "Great Vaipulya Great Cloud Sutra: Rain-Requesting Chapter",
    "T19n0993": "Vetala Sutra",
    "T19n1002": "Thousand-Armed Avalokitesvara Dharani Sutra",
    "T19n1009": "Avalokitesvara Secret Cintamani Dharani Sutra",
    "T19n1012": "Eleven-Faced Avalokitesvara Heart Dharani Sutra",
    "T19n1014": "Eleven-Faced Avalokitesvara Secret Recitation Ritual Sutra",
    "T19n1016": "Never-Falling Avalokitesvara",
    "T19n1017": "Avalokitesvara Dharani for Quelling Evil Sutra",
    "T19n1018": "Padmapani Dharani Sutra",
    "T19n1019": "Avalokitesvara Cintamani Heart Dharani Sutra",
    "T19n1028A": "Skanda Deva Dharani (A)",
    "T19n1029": "Maha Sita-tapatra Dharani Sutra",
    "T20n1060": "Thousand-Armed Thousand-Eyed Avalokitesvara Great Compassion Dharani Sutra",
    "T20n1064": "Thousand-Armed Avalokitesvara Great Compassion Heart Dharani",
    "T20n1066": "Amoghapasa Dharani Sutra",
    "T20n1070": "Matangi Sutra (Dharani)",
    "T20n1071": "Dharani Collection Sutra (by Atigupta)",
    "T20n1072A": "Holy Hayagriva Great Wrathful King Practice and Offering Ritual",
    "T20n1073": "Vajra-Elephant Bodhisattva Great Name Dharani Sutra",
    "T20n1074": "Mahayana Avalokitesvara Heart Dharani Sutra",
    "T20n1076": "Holy Tara Dharani Sutra",
    "T20n1080": "Sutra of All Tathagata Names",
    "T20n1081": "Amitayus Visualization Offering Ritual",
    "T20n1082": "Great Amitabha Sutra (dharani version)",
    "T20n1085": "Amitabha Crown Dharani Sutra",
    "T20n1092": "Amoghapasa Supernormal True Words Sutra",
    "T20n1112": "Sukyedi Sutra (Dharani)",
    "T20n1118": "Root Ritual Sutra of Manjusri",
    "T20n1120B": "Manjusri Dharma-Treasure Dharani Sutra (B)",
    "T20n1134A": "Vajra Longevity Dharani Sutra Ritual (A)",
    "T20n1134B": "Vajra Longevity Dharani Sutra (B)",
    "T20n1138a": "Ksitigarbha Dharani Sutra (A)",
    "T20n1143": "Laksmi Dharani Method",
    "T20n1153": "Dharani Sutra for Overcoming Calamities",
    "T20n1162": "Jewel Seal Dharani Sutra",
    "T20n1163": "Dharani Sutra Transcending All Destinies",
    "T20n1168A": "Great Dharani Mantra Sutra Spoken by Sages (A)",
    "T20n1172": "Seven Buddhas Dharani Mantra Sutra",
    "T20n1175": "Dharani Sutra",
    "T20n1195": "Buddha-Mother Mahamayuri Vidyarajni Sutra",
    "T21n1237": "Usnisa Vijaya Dharani",
    "T21n1238": "Usnisa Vijaya Dharani (alt.)",
    "T21n1255b": "Nilakantha Dharani (B)",
    "T21n1287": "Avalokitesvara At-Will Mantra Sutra",
    "T21n1296": "Dharani Collection Sutra (T21 version)",
    "T21n1298": "Dharani Collection Sutra (partial)",
    "T21n1313": "Dharani Sutra (T21 version)",
    "T21n1318": "Yoga Essential Dharani Flame-Mouth Ritual for Saving Ananda",
    "T21n1326": "Dharani Sutra (T21n1326)",
    "T21n1327": "Sutra of Eye-Blessing Mantras",
    "T21n1329": "Sutra of Mantras for Children",
    "T21n1332": "Medicine Master Sutra (Dharani version)",
    "T21n1336": "Miscellaneous Dharani Collection",
    "T21n1344": "Akashagarbha Dharani",
    "T21n1345": "Akashagarbha Fulfilling-All-Wishes Supreme Heart Dharani",
    "T21n1352": "Marici Dharani Mantra Sutra",
    "T21n1353": "Marici Sutra",
    "T21n1354": "Great Marici Bodhisattva Sutra",
    "T21n1357": "Vaisravana Dharani Sutra",
    "T21n1358": "Vaisravana King Sutra",
    "T21n1364": "Four-Faced Dharani Sutra",
    "T21n1365": "Four-Faced Mahesvara Female Mantra Sutra",
    "T21n1382": "Dharani for Knowledge of Past Lives",
    "T21n1383": "Method of Recitation for Longevity",
    "T21n1384": "Dharani Sutra for Extending Life",
    "T21n1389": "Abhiseka Sutra (Dharani Section)",
    "T21n1390": "Seven-Star Cintamani Secret Ritual Sutra",
    "T21n1395": "Vetala Dharani Sutra",
    "T21n1406": "Miscellaneous Dharani Collection (alt.)",
    # =====================================================================
    # Other sutras T14-T17
    # =====================================================================
    "T14n0430": "Ullambana Sutra",
    "T14n0431": "Requiting Kindness Ullambana Sutra",
    "T14n0434": "Sutra of Praising the Virtues of All Buddhas",
    "T14n0435": "Sutra of Flower-Moon Bodhisattva",
    "T14n0436": "Sutra on Merits of Receiving the Seven Buddhas' Names",
    "T14n0438": "Akashagarbha Bodhisattva Sutra",
    "T14n0440": "Medicine Buddha Original Vow Sutra",
    "T14n0441": "Sutra of Buddha Names",
    "T14n0443": "Sutra of Buddha Names (alt.)",
    "T14n0444": "Sutra of Buddha Names (version C)",
    "T14n0446a": "Sutra of Thousand Buddha Names of the Past Adornment Kalpa (A)",
    "T14n0446b": "Sutra of Thousand Buddha Names of the Past Adornment Kalpa (B)",
    "T14n0447a": "Sutra of Thousand Buddha Names of the Present Wise Kalpa (A)",
    "T14n0447b": "Sutra of Thousand Buddha Names of the Present Wise Kalpa (B)",
    "T14n0448a": "Samantabhadra Dharani Sutra (A)",
    "T14n0448b": "Samantabhadra Dharani Sutra (B)",
    "T14n0450": "Medicine Buddha Sutra (Bhaisajyaguru Original Vow)",
    "T14n0451": "Medicine Buddha Seven Buddhas Original Vow Merit Sutra",
    "T14n0463": "Buddha-Mother Sutra",
    "T14n0464": "Sutra of Questions from Zhiyi Devaputra",
    "T14n0465": "Vimalakirti Sutra (tr. Zhi Qian)",
    "T14n0466": "Vimalakirti Sutra (tr. Xuanzang)",
    "T14n0467": "Vimalakirti Sutra Commentary (by Sengzhao)",
    "T14n0468": "Sutra of the Great Compassionate One's Question (Ugra)",
    "T14n0470": "Sutra of the Youth Chandraprabha",
    "T14n0490": "Manjusri's Parinirvana Sutra",
    "T14n0502": "Sutra on the Proper Affairs for Young Bhikshus",
    "T14n0503": "Sutra of a Bhikshu Avoiding Ill Repute with Women and Wanting to Kill Himself",
    "T14n0506": "Sutra of the Original Nature of Dharma",
    "T14n0510": "Sutra of the Bodhisattva Ten Stages",
    "T14n0523": "Sutra of Liberation",
    "T14n0540a": "Sutra of Supreme Reliance (A)",
    "T14n0540b": "Sutra of Supreme Reliance (B)",
    "T14n0559": "Ramagaka Sutra",
    "T14n0568": "Sutra of Cutting Off Afflictions",
    "T14n0574": "Sutra of Sarva-deva",
    "T14n0575": "Sutra of Turning the Dharma Wheel",
    "T15n0587": "Sutra of the Elder's Daughter Instructing the Hungry Ghost",
    "T15n0609": "Sutra of the Auspicious Radiance Devaputra",
    "T15n0615": "Sutra of Bodhisattva's Reproval of Desire for Form",
    "T15n0641": "Moon Lamp Samadhi Sutra (Candrapradipa-samadhi)",
    "T15n0647": "Sutra of the Ocean-Like Samadhi of Buddha Visualization",
    "T15n0650": "Sutra of Abhiseka",
    "T15n0655": "Sutra of Supreme Emptiness (Paramarthasunyata)",
    "T17n0724": "Sutra of Mindfulness of the True Dharma (Saddharma-smrtyupasthana)",
    "T17n0745": "Sutra of the Wise and the Foolish (Damamuka-nidana-sutra)",
    "T17n0747a": "Sutra of Karmic Retribution for Offenses and Merits (A)",
    "T17n0751b": "Verses on the Buddha's Deeds (Buddhacharita, B)",
    "T17n0762": "Great Skillful Means Requiting Kindness Sutra",
    "T17n0772": "Sutra of Outstanding Essentials (Dharmapada commentary)",
    "T17n0776": "Anomalous Features of Sutras and Vinaya (alt.)",
    "T17n0781": "Jingde Lamp Transmission Record (alt.)",
    "T17n0786": "Layperson's Abhidharma Treatise",
    "T17n0794a": "Great Tang Records of the Western Regions (by Xuanzang, A)",
    "T17n0794b": "Great Tang Records of the Western Regions (by Xuanzang, B)",
    "T17n0800": "Dharmapada Sutra",
    "T17n0802": "Sutra of a Hundred Parables",
    "T17n0805": "Miscellaneous Parable Sutra",
    "T17n0822": "Collection of the Six Paramitas",
    "T17n0823": "Old Miscellaneous Parable Sutra",
    "T17n0825": "Great Adornment Sutra Treatise (Sutralankara)",
    "T17n0829": "Dharmapada Parable Sutra",
    "T17n0830": "Miscellaneous Jewel Treasury Sutra",
    "T17n0832": "Sutra of the Arising of Practices",
    "T17n0847": "Essential Collection from Various Sutras (alt.)",
    # =====================================================================
    # Jatakas and biographies
    # =====================================================================
    "T03n0175a": "Sutra of the Filial Shanzi (A)",
    "T03n0175b": "Sutra of the Filial Shanzi (B)",
    "T03n0175c": "Sutra of the Filial Shanzi (C)",
    "T03n0181a": "Lalitavistara Sutra (A)",
    "T03n0181b": "Lalitavistara Sutra (B)",
    "T03n0183": "Sutra of the Crown Prince's Origins",
    "T04n0195": "Sutra of the Twelve Games",
    "T04n0211": "Dharmapada (Chinese version)",
    "T04n0212": "Outstanding Essentials Sutra (Dharmapada Commentary)",
    # =====================================================================
    # Tiantai
    # =====================================================================
    "T46n1927": "Meaning of the Four Teachings (by Zhiyi)",
    "T46n1934": "Great Calming and Contemplation (Mohe Zhiguan, by Zhiyi)",
    "T46n1942": "Essential Meaning of the Tiantai Eight Teachings",
    "T46n1944": "Hundred Records of Guoqing Temple",
    "T46n1946": "Separate Biography of Great Master Zhiyi of Tiantai",
    "T46n1951": "Profound Meaning of the Lotus Sutra (by Zhiyi)",
    "T46n1953": "Textual Commentary on the Lotus Sutra (by Zhiyi)",
    "T46n1955": "Record of Textual Commentary on the Lotus Sutra (by Zhanran)",
    "T46n1956": "Notes on the Profound Meaning of the Lotus Sutra (by Zhanran)",
    # =====================================================================
    # Treatise commentaries
    # =====================================================================
    "T44n1836": "Commentary on the Middle Treatise",
    "T44n1840": "Profound Treatise on the Pure Name (Vimalakirti commentary)",
    "T44n1844": "Commentary on the Awakening of Faith (by Wonhyo)",
    "T44n1845": "Commentary on the Awakening of Faith (alt.)",
    "T44n1846": "Sub-commentary on the Awakening of Faith (by Fazang)",
    "T44n1848": "Separate Commentary on the Awakening of Faith",
    "T44n1849": "Exposition of the Inner Meaning of the Awakening of Faith",
    "T45n1858": "Divisions of the Huayan One-Vehicle Teaching (by Fazang)",
    "T45n1861": "Various Discourses on the Avatamsaka",
    "T45n1862": "Topical Outline of the Avatamsaka Discourses",
    "T45n1909": "Profound Treatise on the Mahayana (by Jizang)",
    # =====================================================================
    # Sutra commentaries
    # =====================================================================
    "T34n1720": "Textual Commentary on the Lotus Sutra (by Zhiyi)",
    "T34n1721": "Record of the Textual Commentary on the Lotus (by Zhanran)",
    "T34n1723": "Commentary on the Lotus Sutra",
    "T37n1750": "Commentary on the Visualization of Amitayus Sutra (by Shandao)",
    "T37n1754": "Commentary on the Amitabha Sutra",
    "T37n1755": "Commentary on the Amitabha Sutra (by Kuiji)",
    "T37n1756": "Commentary on the Amitabha Sutra (alt.)",
    "T37n1757": "Commentary on the Amitabha Sutra (by Yuanzhao)",
    "T37n1758": "Commentary on the Amitabha Sutra (by Zhiyi)",
    "T37n1762": "Commentary on the Amitayus Visualization Sutra (by Jiacai)",
    "T38n1772": "Commentary on the Vimalakirti Sutra (by Sengzhao)",
    "T38n1774": "Commentary on the Vimalakirti Sutra",
    "T38n1775": "Brief Commentary on the Vimalakirti Sutra",
    "T38n1776": "Commentary on the Vimalakirti Sutra (by Zhanran)",
    "T38n1778": "Commentary on the Vimalakirti Sutra (Xuanzang tr. version)",
    "T38n1781": "Profound Treatise on the Pure Name",
    "T39n1788": "Commentary on the Benevolent King Sutra",
    "T39n1792": "Commentary on the Heart Sutra",
    "T39n1796": "Praising Commentary on the Heart Sutra",
    "T41n1821": "Commentary on the Four-Part Vinaya (by Fali)",
    "T41n1822": "Explanation of the Four-Part Vinaya Commentary",
    "T41n1823": "Record of the School's Commentary on the Four-Part Vinaya",
    "T42n1828": "Commentary on the Middle Treatise",
    "T43n1830": "Commentary on the Vijnaptimatratasiddhi",
    "T43n1833": "Record on the Yogacarabhumi",
    # =====================================================================
    # Biographies and histories
    # =====================================================================
    "T49n2030": "Comprehensive Record of Buddhist Patriarchs Through the Ages",
    "T49n2031": "General Record of Buddhist Patriarchs (by Zhipan)",
    "T49n2034": "Record of the Three Jewels Through the Ages",
    "T49n2035": "General Record of Buddhist Patriarchs (alt.)",
    "T49n2036": "General Record of Buddhist Patriarchs (yet alt.)",
    "T50n2040": "Biographies of Eminent Monks (by Huijiao)",
    "T50n2047a": "Continued Biographies of Eminent Monks (A, by Daoxuan)",
    "T50n2047b": "Continued Biographies of Eminent Monks (B, by Daoxuan)",
    "T50n2058": "Record of Spreading and Praising the Lotus Sutra",
    "T50n2060": "Records of Pure Land Rebirth",
    "T50n2061": "Records of Auspicious Signs of Rebirth in the Western Pure Land",
    "T51n2067": "Record of Monasteries of Luoyang (by Yang Xuanzhi)",
    "T51n2068": "Record of Monasteries of Luoyang (alt.)",
    "T51n2069": "Great Tang Records of the Western Regions (by Xuanzang)",
    # =====================================================================
    # Miscellaneous important texts
    # =====================================================================
    "T52n2103": "Expanded Collection on the Propagation of Light (by Daoxuan)",
    "T52n2109": "Collection on the Propagation of Light (by Sengyou)",
    "T52n2120": "Treatise on Discrimination of the Correct",
    "T20n1057b": "Thousand-Eyed Thousand-Armed Avalokitesvara Dharani Sutra (B)",
    # =====================================================================
    # Dunhuang texts (T85)
    # =====================================================================
    "T85n2763": "Dunhuang Transformation Text",
    "T85n2769": "Dunhuang Document (narrative)",
    "T85n2773": "Dunhuang Document (ritual)",
    "T85n2777": "Dunhuang Document",
    "T85n2778": "Dunhuang Document (alt.)",
    "T85n2795": "Dunhuang Document (meditation-related)",
    "T85n2797": "Dunhuang Document (Chan-related)",
    "T85n2804": "Dunhuang Document (liturgy-related)",
    "T85n2810": "Dunhuang Document (dharani-related)",
    "T85n2813": "Dunhuang Document (ritual-related)",
    "T85n2815": "Dunhuang Document (commentary-related)",
    "T85n2819": "Dunhuang Document (doctrinal)",
    "T85n2820": "Dunhuang Document (doctrinal, alt.)",
    "T85n2827": "Dunhuang Document (historical)",
    "T85n2843": "Dunhuang Document (miscellaneous)",
    "T85n2854": "Dunhuang Document (literary)",
    "T85n2862": "Dunhuang Document (Buddhist verse)",
    "T85n2874": "Dunhuang Document (catalogue-related)",
    "T85n2882": "Dunhuang Document (dharma-assembly-related)",
    "T85n2912": "Dunhuang Document (Pure Land)",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def chinese_to_pinyin(title: str) -> str:
    """Convert Chinese title to capitalized pinyin using pypinyin."""
    result = pinyin(title, style=Style.TONE)
    syllables = [s[0] for s in result]
    return " ".join(s.capitalize() for s in syllables)


def format_text_entry(text_id: str, title: str) -> str:
    """Format a text entry with Chinese title, pinyin, and English."""
    py = chinese_to_pinyin(title)
    if text_id in ENGLISH_LOOKUP:
        english = ENGLISH_LOOKUP[text_id]
        return f"{text_id} {title} ({py} / {english})"
    else:
        return f"{text_id} {title} ({py} / [translation needed])"


def escape_md_pipe(s: str) -> str:
    """Escape pipe characters for Markdown table cells."""
    return s.replace("|", "\\|")


def main():
    # Resolve paths relative to the project root
    project_root = Path(__file__).resolve().parent.parent
    relationships_path = project_root / "results" / "digest_relationships.json"
    metadata_path = project_root / "data" / "metadata.json"
    output_path = project_root / "results" / "digest_relationships_readable.md"

    # Load data
    with open(relationships_path) as f:
        relationships = json.load(f)

    with open(metadata_path) as f:
        metadata_list = json.load(f)

    # Build metadata lookup
    meta = {m["text_id"]: m for m in metadata_list}

    def get_title(text_id: str) -> str:
        if text_id in meta:
            return meta[text_id]["title"]
        return "[title unknown]"

    # Group relationships by classification
    classifications = [
        ("retranslation", "Retranslations"),
        ("excerpt", "Excerpts"),
        ("digest", "Digests"),
        ("commentary", "Commentaries"),
        ("shared_tradition", "Shared Tradition"),
    ]

    grouped = {}
    for cls_key, _ in classifications:
        grouped[cls_key] = []
    for r in relationships:
        cls = r["classification"]
        if cls in grouped:
            grouped[cls].append(r)

    # Sort each group by confidence descending
    for cls_key in grouped:
        grouped[cls_key].sort(key=lambda r: -r["confidence"])

    # Count unique text IDs
    all_ids = set()
    for r in relationships:
        all_ids.add(r["digest_id"])
        all_ids.add(r["source_id"])

    # Count how many have English translations
    has_english = sum(1 for tid in all_ids if tid in ENGLISH_LOOKUP)

    # Generate output
    lines = []
    lines.append("# Digest Relationships in the Taisho Canon")
    lines.append("")
    lines.append(f"Total relationships: **{len(relationships)}**  ")
    lines.append(f"Unique texts involved: **{len(all_ids)}**  ")
    lines.append(f"Texts with English translations: **{has_english}** / {len(all_ids)}  ")
    lines.append("Pinyin romanization: auto-generated for all texts via pypinyin")
    lines.append("")
    lines.append("### Breakdown by Classification")
    lines.append("")
    lines.append("| Classification | Count | Description |")
    lines.append("|----------------|------:|-------------|")
    descs = {
        "excerpt": "Shorter text draws >=80% of its content from the longer text (verbatim extraction)",
        "digest": "Shorter text draws 30-80% of its content from the longer text (condensed derivation)",
        "retranslation": "Two texts of similar length sharing significant content (different translations of the same source)",
        "commentary": "Shorter text quotes portions of the longer text with added material",
        "shared_tradition": "Texts sharing content through common tradition rather than direct derivation",
    }
    for cls_key, cls_label in classifications:
        count = len(grouped[cls_key])
        desc = descs.get(cls_key, "")
        lines.append(f"| {cls_label} | {count} | {desc} |")
    lines.append("")
    lines.append("Format: `Text_ID Chinese_Title (Pinyin / English Translation)`")
    lines.append("")
    lines.append("---")
    lines.append("")

    for cls_key, cls_label in classifications:
        rels = grouped[cls_key]
        if not rels:
            continue

        lines.append(f"## {cls_label} ({len(rels)} pairs)")
        lines.append("")
        lines.append("| # | Digest | Source | Coverage | Confidence |")
        lines.append("|---|--------|--------|----------|------------|")

        for i, r in enumerate(rels, 1):
            digest_id = r["digest_id"]
            source_id = r["source_id"]
            digest_title = get_title(digest_id)
            source_title = get_title(source_id)

            digest_str = escape_md_pipe(format_text_entry(digest_id, digest_title))
            source_str = escape_md_pipe(format_text_entry(source_id, source_title))
            coverage = f"{r['coverage'] * 100:.1f}%"
            confidence = f"{r['confidence']:.4f}"

            lines.append(
                f"| {i} | {digest_str} | {source_str} | {coverage} | {confidence} |"
            )

        lines.append("")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print(f"Generated: {output_path}")
    print(f"  {len(relationships)} relationships across {len(all_ids)} unique texts")
    print(f"  {has_english}/{len(all_ids)} texts have English translations in lookup table")
    print(f"  All texts have auto-generated pinyin romanization")


if __name__ == "__main__":
    main()
