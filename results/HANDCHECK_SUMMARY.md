# Hand-verification of the 204 MITRA "verified new parallels"

Every one of the 204 candidate parallels (169 coverage-filtered + 35 Sanskrit-title)
was examined by hand. Rejections, confirmations, uncertains, and title matches were
all adversarially cross-checked (rejects got a rescue pass; confirms got a refutation
pass; uncertains and titles were web-verified against 84000/rKTs/DDB).

## Result
- SOLID parallels: 121  (same-work translations, or a Chinese sutra genuinely
  embedded as a chapter of a Kangyur collection)
- Quotation-witness parallels: 13  (the Chinese sutra is quoted inside a Tengyur
  commentary/anthology -- Szamathadeva's Abhidharmakosa-Upayika Toh 4094,
  Mahasutrasamuccaya Toh 3961, Karmaprajnapti Toh 4088, Toh 4357 -- a real but
  weaker witness, not a canonical Kangyur text)
- TOTAL genuine: 134
- REJECTED: 70 of 204 (34%)

## Why the coverage filter failed (the 70 rejects)
- root-vs-commentary (~30): the Chinese ROOT text matched to a Tibetan COMMENTARY
  (tika/vrtti/bhasya/vyakhya/panjika/vivarana/pindartha) that quotes it in full,
  so coverage is high but they are different works (e.g. Heart Sutra vs a
  *commentary on* the Heart Sutra).
- root-vs-devotional (~14): root matched to a derived stotra/sadhana/kalpa.
- formulaic coincidence (~15): shared stock lists (62 views, ten unwholesome deeds,
  posadha vows, dharani syllables, gnomic verses).
- generic-title / mislabeled / wrong-Toh / duplicate (~11): esp. among the title
  matches ("Seven Buddhas", "Mahaparinirvana", "Tathagatagarbha", "Amoghapasa"
  names each cover two different works).

## Coverage (catalog -> +solid harvest)
- Taisho w/ Tibetan parallel: 754 (30.7%) -> 818 (33.3%)   [64 newly linked]
- Kangyur: 488 (44.0%) -> 513 (46.3%)
- Tengyur: 115 (3.3%)  -> 135 (3.9%)     (was inflated to 5.2% by commentary false positives)

Data: handcheck_locked.json (solid / quotation_witness / refuted),
handcheck_final.json, mitra_169_handcheck.json, mitra_169_dossier.json.
