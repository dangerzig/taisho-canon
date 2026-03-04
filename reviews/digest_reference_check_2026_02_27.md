# Bibliography Verification Report

**File:** `references.bib` for `zigmond-digest-detection.tex`
**Date:** 2026-02-27
**Method:** Each entry checked against web sources (publisher catalogs, Google Scholar, Semantic Scholar, academia.edu, JSTOR, journal websites, Springer, Oxford Academic, Cambridge Core). All URLs tested with HTTP status checks.

---

## Summary

- **Total bib entries:** 36
- **Entries cited in paper:** 22
- **Uncited entries:** 14
- **Missing from bib:** 0 (all `\parencite` keys resolve)
- **Entries with serious issues:** 5
- **Entries with minor issues:** 5
- **Entries confirmed OK:** 26

---

## Citation Cross-Reference

All 22 unique `\parencite` keys in the paper have matching entries in `references.bib`. No missing keys.

Fourteen bib entries are **not cited** anywhere in the paper:
- `lancaster1979` (Lancaster & Park, Korean Buddhist Canon)
- `nanjio1883` (Nanjio, Catalogue of Chinese Translation)
- `ui1934` (Ui et al., Complete Catalogue of Tibetan Buddhist Canons)
- `akanuma1929` (Akanuma, Comparative Catalogue)
- `hackett2013` (Hackett, Catalogue of the Comparative Kangyur)
- `herrmannpfandt2008` (Herrmann-Pfandt, Die lHan kar ma)
- `rkts` (rKTs)
- `84000` (84000)
- `copp2014` (Copp, Dharani Collections)
- `silk2019` (Silk, Chinese Sutras in Tibetan Translation)
- `buswell2014` (Buswell & Lopez, Princeton Dictionary of Buddhism)
- `tokuno1990` (Tokuno, Evaluation of Indigenous Scriptures)
- `storch2014` (Storch, Chinese Buddhist Historiography and Orality)
- `funayama2006` (Funayama, Masquerading as Translation)

These will generate "unused reference" warnings and will not appear in the bibliography unless `\nocite{*}` is used.

---

## Entry-by-Entry Verification

| Key | Type | Status | Notes |
|-----|------|--------|-------|
| `nattier1992` | article | OK | Nattier, Jan. "The Heart Sutra: A Chinese Apocryphal Text?" JIABS 15(2):153-223, 1992. Confirmed via Heidelberg JIABS archive and Semantic Scholar. All details correct. |
| `attwood2021a` | article | OK | Attwood, Jayarava. "The Chinese Origins of the Heart Sutra Revisited." JIABS 44:13-52, 2021. Confirmed via PhilArchive, ResearchGate, and PhilPapers. All details correct. |
| `huifeng2014` | article | **SERIOUS** | The article titled "Is the Heart Sutra an Apocryphal Text? -- A Re-examination" attributed to Shi Huifeng in Numen 61(5-6):659-692 **could not be verified**. Shi Huifeng's confirmed 2014 publication is "Apocryphal Treatment for Conze's Heart Problems" in JOCBS 6:72-105. The article "Is the Heart Sutra an Apocryphal Text?" is by Ji Yun (released 2012 in Fuyan Buddhist Studies 7:115-182; English translation 2017 in Singapore Journal of Buddhist Studies 4:9-113). No Numen article by Shi Huifeng matching this title or page range was found. The journal, title, volume, and pages all appear incorrect. See Issues section. |
| `silk1994` | incollection | **MINOR** | Silk, Jonathan A. "The Heart Sutra in Tibetan." WSTB 34, 1994, Vienna. This is a standalone monograph (xi + 204 pp.), not a chapter in a larger work. The `@incollection` type with `pages = {1--144}` is misleading. It should be `@book` with total pages xi + 204. The page range 1-144 is not verifiable as a chapter range; the work is a single-author book in a monograph series. Publisher and address confirmed correct. |
| `zigmond2021` | article | **MINOR** | The confirmed JOCBS article by Zigmond is titled "Toward a Computational Analysis of the Pali Canon" (JOCBS vol. 21, 2021). The bib title "Frequency-Based Text Mining in the Pali Canon" does not match the published title. Volume 21 and year 2021 appear correct. Pages listed as 178-205 could not be independently verified from web sources (JOCBS does not expose page numbers in metadata). |
| `zigmond2023` | article | **MINOR** | A second Zigmond JOCBS article is plausible but the title "Textual Strata in the Pali Canon: A Computational Approach" was not found in web searches or JOCBS volume 25 table of contents. Only one Zigmond article ("Toward a Computational Analysis of the Pali Canon") was found in JOCBS. Author should verify title, volume, and pages. |
| `zigmond2026b` | unpublished | OK | Self-citation, in preparation. No external verification needed. |
| `bingenheimer2006` | misc | OK | Bingenheimer, Marcus. "A Digital Comparative Catalog of Agama Literature." Version 3, 2006. URL http://mbingenheimer.net/tools/comcat/ returns HTTP 301 (redirects to indexComcat.html). The resource is functional. Confirmed via mbingenheimer.net publications page. |
| `hung2015` | article | **SERIOUS** | Listed as JJADH vol. 1, no. 1, pp. 27-43, 2015. The JJADH Vol. 1, No. 1 (2015) table of contents does not include an article by Hung and Bingenheimer with this title. Bingenheimer's own publications page lists a social network article in Literary and Linguistic Computing 26(3):271-278 (2011), co-authored with Hung and Wiles, and a JJADH article "On the Use of Historical Social Network Analysis in the Study of Chinese Buddhism" in JJADH 5:84-131 (2020). An article titled "Social Network Analysis of Buddhist Biographical Collections" in JJADH vol. 1, no. 1, 2015 was not found. Journal title, volume, year, or title may be wrong. See Issues section. |
| `lancaster1979` | book | OK | Lancaster, Lewis R. and Park, Sung-bae. "The Korean Buddhist Canon: A Descriptive Catalogue." University of California Press, Berkeley, 1979. Confirmed via Cambridge Core review, Internet Archive, and Amazon. (Note: Park is listed as "in collaboration with" on title page, not full co-author.) Not cited. |
| `nanjio1883` | book | OK | Nanjio, Bunyiu. "A Catalogue of the Chinese Translation of the Buddhist Tripitaka." Clarendon Press, Oxford, 1883. Confirmed via Internet Archive, HathiTrust, Open Library. Not cited. |
| `ui1934` | book | OK | Ui, Hakuju et al. "A Complete Catalogue of the Tibetan Buddhist Canons." Tohoku Imperial University, Sendai, 1934. Confirmed. Not cited. |
| `akanuma1929` | book | OK | Akanuma, Chizen. "The Comparative Catalogue of Chinese Agamas and Pali Nikayas." Hajinkaku Shobo, Nagoya, 1929 (reprinted 1990). Confirmed via Amazon, mbingenheimer.net. Not cited. |
| `hackett2013` | book | OK | Hackett, Paul. "A Catalogue of the Comparative Kangyur." American Institute of Buddhist Studies / Columbia University Press, New York, 2013. Confirmed via Amazon, AbeBooks. Not cited. |
| `herrmannpfandt2008` | book | OK | Herrmann-Pfandt, Adelheid. "Die lHan kar ma." Verlag der Osterreichischen Akademie der Wissenschaften, Vienna, 2008. Confirmed via publisher website (verlag.oeaw.ac.at), AbeBooks, Google Books. Not cited. |
| `cbeta` | misc | OK | CBETA Electronic Texts Collection. URL https://www.cbeta.org/ returns HTTP 200 (after redirect). Site operational. |
| `suttacentral` | misc | OK | SuttaCentral. URL https://suttacentral.net/ returns HTTP 200. Site operational. |
| `sat` | misc | OK | SAT Daizokyo Text Database. URL https://21dzk.l.u-tokyo.ac.jp/SAT/ returns HTTP 200. Site operational. |
| `ddb` | misc | OK | Digital Dictionary of Buddhism. URL http://www.buddhism-dict.net/ddb/ returns HTTP 200. Site operational. |
| `rkts` | misc | OK | rKTs. URL http://www.rkts.org/ returns HTTP 200. Site operational. Not cited. |
| `84000` | misc | OK | 84000. URL https://84000.co/ returns HTTP 200. Site operational. Not cited. |
| `smith2015` | article | OK | Smith, David A., Cordell, Ryan, and Mullen, Abby. "Computational Methods for Uncovering Reprinted Texts in Antebellum Newspapers." American Literary History 27(3):E1-E15, 2015. Confirmed via Oxford Academic, Illinois Experts, MUSE. All details correct. |
| `buechler2014` | inproceedings | **SERIOUS** | Author list incorrect. The bib entry lists "Geser, Emily" but the correct fifth author is "Franzini, Emily." The full author list should be: Buchler, Marco; Burns, Patrick R.; Muller, Martin; Franzini, Emily; Franzini, Greta. Confirmed via Springer, Semantic Scholar. Booktitle, pages (221-238), publisher (Springer), and year (2014) are all correct. |
| `forstall2015` | article | **SERIOUS** | Author list incorrect. The bib entry lists only three authors: "Forstall, Christopher and Scheirer, Walter and Coffee, Neil." The published article has five authors: Christopher Forstall, Neil Coffee, Thomas Buck, Katherine Roache, and Sarah Jacobson. Forstall and Coffee are correct but Scheirer is not an author on this paper (though he has co-authored related work with some of these authors). Walter Scheirer is incorrectly included while Buck, Roache, and Jacobson are missing. DSH 30(4):503-515, 2015 confirmed correct. |
| `ganascia2014` | inproceedings | **SERIOUS** | Entry type and author list both wrong. (1) This is a journal article, not a conference paper. It was published in Literary and Linguistic Computing (now Digital Scholarship in the Humanities) 29(3):412-421, 2014. The entry type should be `@article`. (2) Author list incorrect. The bib lists "Ganascia, Jean-Gabriel and Leblanc, Pierre and Molin, Martin." The actual authors are Jean-Gabriel Ganascia, Pierre Glaudes, and Andrea Del Lungo. Confirmed via HAL, arXiv (1404.2997), Oxford Academic. Volume, number, pages, and year are correct. |
| `bamman2008` | inproceedings | **MINOR** | The bib lists booktitle as "Proceedings of the Second Workshop on Language Technology for Cultural Heritage Data." The actual workshop was the 2008 LREC Workshop on Language Technology for Cultural Heritage Data (LaTeCH 2008), held in Marrakech. The workshop is sometimes informally called "LaTeCH 2008" rather than "Second Workshop on Language Technology for Cultural Heritage Data." The publisher is listed as ACL, which is acceptable. Pages 1-8 could not be independently verified from web sources (many sources do not list page numbers for this paper). Authors and year correct. |
| `lee2007` | inproceedings | OK | Lee, John. "A Computational Model of Text Reuse in Ancient Literary Texts." ACL 2007, pp. 472-479. Confirmed via ACL Anthology (P07-1060). All details correct. |
| `jockers2013` | book | OK | Jockers, Matthew L. "Macroanalysis: Digital Methods and Literary History." University of Illinois Press, Urbana, 2013. Confirmed via publisher website, Amazon, Google Books. All details correct. |
| `moretti2013` | book | OK | Moretti, Franco. "Distant Reading." Verso, London, 2013. Confirmed via Verso Books, Oxford Academic review, Amazon. All details correct. |
| `mcrae2003` | book | OK | McRae, John R. "Seeing through Zen." University of California Press, Berkeley, 2003. Confirmed via UC Press, Amazon, Internet Archive. All details correct. |
| `copp2014` | incollection | **MINOR** | The bib entry year was originally listed as 2014 in the task prompt, but examining the actual bib file shows `year = {2015}`. Brill's Encyclopedia of Buddhism volume 1 was published 21 October 2015, edited by Jonathan A. Silk. The year 2015 in the bib is correct. Author, title, pages (808-815), publisher (Brill), and address (Leiden) all confirmed. Not cited. |
| `silk2019` | incollection | OK | Silk, Jonathan A. "Chinese Sutras in Tibetan Translation: A Preliminary Survey." ARIRIAB 22:227-246, 2019. Confirmed via academia.edu and Leiden University publications. Entry type `@incollection` is acceptable; ARIRIAB functions as both an annual report and a peer-reviewed journal. All details correct. Not cited. |
| `buswell2014` | book | OK | Buswell, Robert E. and Lopez, Donald S. "The Princeton Dictionary of Buddhism." Princeton University Press, Princeton, 2014. Confirmed via PUP, Amazon, Google Books. Not cited. |
| `tokuno1990` | incollection | OK | Tokuno, Kyoko. "The Evaluation of Indigenous Scriptures in Chinese Buddhist Bibliographical Catalogues." In "Chinese Buddhist Apocrypha," ed. Buswell. University of Hawaii Press, Honolulu, 1990, pp. 31-74. Confirmed via De Gruyter Brill, Google Books. All details correct. Not cited. |
| `storch2014` | incollection | **SERIOUS (uncited)** | The booktitle "Spreading the Dharma with the Right Accent" does not appear to exist as a published book. No web search results found for this title. Tanya Storch has published: (a) "Chinese Buddhist historiography and orality" in Sino-Platonic Papers (1993); (b) a chapter in "Spreading Buddha's Word in East Asia" (ed. Jiang Wu and Lucille Chia, Columbia UP, 2016); (c) "The History of Chinese Buddhist Bibliography" (Cambria Press, 2014). The bib booktitle appears to be fabricated or confused. Since this entry is uncited, it will not affect the paper, but should be corrected or removed. |
| `funayama2006` | article | **SERIOUS (uncited)** | The journal is wrong. The bib lists JIABS 29(1):49-68, but the actual publication is: Funayama, Toru. "Masquerading as Translation: Examples of Chinese Lectures by Indian Scholar-Monks in the Six Dynasties Period." **Asia Major**, Third Series, 19(1/2):39-55, 2006. Confirmed via JSTOR (stable/41649913), Kyoto University activity database. Funayama's only JIABS article is "The work of Paramartha" in JIABS 31(1-2), 2008. Journal, volume, number, and pages are all wrong. Since uncited, does not affect the paper directly. |

---

## Issues Requiring Attention

### 1. `huifeng2014` -- Likely fabricated or misattributed entry (CITED)

This is the most serious issue. The bib entry claims:

> Shi Huifeng, "Is the Heart Sutra an Apocryphal Text? -- A Re-examination," Numen 61(5-6):659-692, 2014.

No such article exists. Shi Huifeng's confirmed 2014 publication is "Apocryphal Treatment for Conze's Heart Problems: 'Non-attainment', 'Apprehension' and 'Mental Hanging' in the Prajnaparamita Hrdaya," published in the Journal of the Oxford Centre for Buddhist Studies 6:72-105, 2014.

An article titled "Is the Heart Sutra an Apocryphal Text? A Re-examination" exists but is by **Ji Yun** (not Shi Huifeng), originally published in Chinese in Fuyan Buddhist Studies 7:115-182 (2012), with an English translation in Singapore Journal of Buddhist Studies 4:9-113 (2017).

**Action required:** Determine which publication is intended and correct the entry. If citing Shi Huifeng's 2014 JOCBS article, all fields need updating (title, journal, volume, pages). If citing Ji Yun, the author and all publication details need updating.

### 2. `hung2015` -- Unverifiable publication (CITED)

The bib entry claims:

> Hung, Jen-Jou and Bingenheimer, Marcus, "Social Network Analysis of Buddhist Biographical Collections," JJADH 1(1):27-43, 2015.

This could not be verified. Bingenheimer's publications page lists related social network work in Literary and Linguistic Computing 26(3):271-278 (2011) and a JJADH article in vol. 5 (2020). No JJADH vol. 1 (2015) article by these authors with this title was found.

**Action required:** Verify the correct journal, volume, year, and title. The article may exist in a different venue or with different details.

### 3. `ganascia2014` -- Wrong entry type and wrong authors (CITED)

Three problems:
- **Entry type:** Listed as `@inproceedings` but should be `@article` (published in Literary and Linguistic Computing, a journal).
- **Author 2:** "Leblanc, Pierre" should be "Glaudes, Pierre."
- **Author 3:** "Molin, Martin" should be "Del Lungo, Andrea."

Correct citation: Ganascia, Jean-Gabriel; Glaudes, Pierre; Del Lungo, Andrea. "Automatic Detection of Reuses and Citations in Literary Texts." Literary and Linguistic Computing 29(3):412-421, 2014.

### 4. `forstall2015` -- Wrong author list (CITED)

The bib lists three authors: Forstall, Scheirer, Coffee. The published article has five authors: **Forstall, Christopher; Coffee, Neil; Buck, Thomas; Roache, Katherine; Jacobson, Sarah.** Walter Scheirer is not an author on this paper and should be removed. Buck, Roache, and Jacobson should be added.

### 5. `buechler2014` -- Wrong author name (CITED)

"Geser, Emily" should be "Franzini, Emily." The five correct authors are: Buchler, Marco; Burns, Patrick R.; Muller, Martin; **Franzini, Emily**; Franzini, Greta.

### 6. `funayama2006` -- Wrong journal and wrong details (uncited)

Published in Asia Major (Third Series) 19(1/2):39-55, 2006. NOT JIABS 29(1):49-68. Since uncited, does not affect the paper. Should be corrected or removed.

### 7. `storch2014` -- Nonexistent booktitle (uncited)

"Spreading the Dharma with the Right Accent" (Brill, 2014) does not appear to be a real publication. Since uncited, does not affect the paper. Should be corrected or removed.

### 8. `zigmond2021` -- Title may not match published title (CITED, self-citation)

The bib title "Frequency-Based Text Mining in the Pali Canon" does not match the JOCBS article title found online, which is "Toward a Computational Analysis of the Pali Canon." Author should verify exact published title.

### 9. `zigmond2023` -- Could not verify (CITED, self-citation)

A second JOCBS article "Textual Strata in the Pali Canon: A Computational Approach" in vol. 25 (2023) could not be confirmed from web sources. Only one Zigmond JOCBS article was found. Author should confirm this exists as published.

### 10. `silk1994` -- Entry type issue (CITED)

Listed as `@incollection` with pages 1-144, but this is a standalone monograph (xi + 204 pp.) in the WSTB series. Should be `@book`. The page range 1-144 is unclear; the work is a self-contained book.

### 11. Uncited entries

Fourteen entries are defined in the bib but not cited in the paper. Unless `\nocite{*}` is used, these will not appear in the bibliography and some tools will warn about unused entries. Consider adding citations or removing the entries, especially the ones with errors (`storch2014`, `funayama2006`).

### 12. `bamman2008` -- Minor booktitle discrepancy

The workshop name is given as "Proceedings of the Second Workshop on Language Technology for Cultural Heritage Data" but is more commonly cited as "Proceedings of the Workshop on Language Technology for Cultural Heritage Data (LaTeCH 2008)." Pages 1-8 could not be independently confirmed. Minor issue.

---

## Specific Checks Requested

| Check | Result |
|-------|--------|
| `ganascia2014` entry type | **WRONG.** `@inproceedings` should be `@article`. The journal fields (volume, number, pages) are journal-style because it IS a journal article in Literary and Linguistic Computing. Authors also wrong. |
| `silk2019` entry type | **OK.** `@incollection` is acceptable for ARIRIAB, which is an annual report/collected volume. `@article` would also be defensible. Details verified correct. |
| `lee2007` existence | **CONFIRMED.** Real publication. ACL Anthology P07-1060. John Lee, ACL 2007, pp. 472-479. |
| `attwood2021a` JIABS 44, pp. 13-52 | **CONFIRMED.** Via PhilArchive and ResearchGate. |
| `huifeng2014` Numen 61(5-6):659-692 | **NOT CONFIRMED.** See Issue 1 above. |
| `silk1994` Wiener Studien details | **Partially confirmed.** WSTB 34, Vienna, 1994 correct. But it is a monograph (xi + 204 pp.), not a chapter with pp. 1-144. |
| `copp2014` year | **OK.** The bib file actually says `year = {2015}`, which is correct. Brill's Encyclopedia of Buddhism vol. 1 was published October 2015. |
| `storch2014` existence | **NOT CONFIRMED.** The booktitle "Spreading the Dharma with the Right Accent" does not appear to exist. |
| `funayama2006` JIABS details | **WRONG.** Published in Asia Major, not JIABS. Different volume, pages. |
| `hung2015` JJADH details | **NOT CONFIRMED.** No matching article found in JJADH vol. 1 (2015). |
| `zigmond2021` JOCBS details | **Title mismatch.** Published title appears to be "Toward a Computational Analysis of the Pali Canon," not "Frequency-Based Text Mining in the Pali Canon." |
| `zigmond2023` JOCBS details | **UNVERIFIABLE** from web sources. Author should confirm. |
| `smith2015` ALH details | **CONFIRMED.** ALH 27(3):E1-E15, 2015. All correct. |
| `buechler2014` existence | **CONFIRMED** but author "Geser, Emily" should be "Franzini, Emily." |
| `bamman2008` ACL workshop | **Confirmed** with minor booktitle variation. Workshop was LaTeCH 2008 at LREC, not strictly an ACL workshop (though published by ACL). |

---

## Conclusion

**Five cited entries have serious issues that require correction before publication:**

1. **`huifeng2014`**: Appears to be a ghost reference. The title, journal, volume, and pages cannot be verified. This is the most critical issue.
2. **`ganascia2014`**: Wrong entry type and two of three author names are wrong.
3. **`forstall2015`**: Wrong author list (three listed, five actual; one listed author is not an author).
4. **`buechler2014`**: One author name wrong ("Geser" should be "Franzini").
5. **`hung2015`**: Publication details could not be verified in the claimed venue.

**Two uncited entries have serious issues** (`storch2014` nonexistent booktitle; `funayama2006` wrong journal) but since they are uncited, they will not appear in the published paper if standard biblatex is used.

**Three cited entries have minor issues** requiring author verification (`zigmond2021` title mismatch, `zigmond2023` unverifiable, `silk1994` entry type).

No other fabricated or ghost references were found among the remaining 26 entries. All URLs for digital resources are functional (HTTP 200 or 200 after redirect).
