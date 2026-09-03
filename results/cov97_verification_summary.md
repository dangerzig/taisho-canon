# Verification of the 97 coverage-harvest parallels — triple adjudication

Three independent LLM adjudications with external documentary research
(84000 / rKTs / DDB / CBETA / Bibliotheca Polyglotta / scholarship):

1. **Pass 1** — relation classification of all 97 (5 agents).
2. **Pass 2** — blind, adversarial re-classification of all 97 (6 agents), no
   access to pass-1 verdicts.
3. **Tiebreak** — a deciding third pass on the 23 items where passes 1 and 2
   disagreed on genuine-vs-not, each judge shown both prior verdicts.

## Inter-adjudicator agreement (pass 1 vs pass 2)
- Exact relation-label agreement: 66/97 (68%)
- Genuine-vs-not agreement: 74/97 (76%)
- Both passes WHOLE: 16 (of 17; 94% agreement on the strongest claim)
- Both passes genuine (WHOLE+SECTION): 46
- Both passes not-genuine: 28
- Contested (one genuine, one not): 23

## Tiebreak outcome
Of the 23 contested, the deciding pass ruled **22 not-genuine, 1 genuine**
(T30n1574 ↔ Toh 2277, a documented Bhavasaṃkrānti recension). When two
independent passes disagreed, the strict/adversarial reading won almost
every time — direct evidence that single-pass adjudication over-accepts.

## FINAL RESOLVED RESULT
- **Genuine new parallels: 47 = 16 whole-text + 31 section-level**
- Across **45 distinct Taishō texts**
- Rejected: 50 (quotation, formulaic dhāraṇī/stock-passage overlap, or
  mislabeled Tōhoku)

The single-pass harvest reported 97 "confirmed"; triple adjudication reduces
this to 47 genuine — the number to report, framed as a conservative lower
bound. Per-parallel evidence for all 97 is released for scrutiny.

## Dominant rejection modes
- Root/commentary or sūtra/ritual-manual: a Tengyur liturgy or śāstra quotes
  the sūtra it is built on (Medicine Buddha → Toh 3132; seven-Tathāgata pūjā).
- Formulaic dhāraṇī / stock passage: a mobile dhāraṇī or standard doctrinal
  list (35-Buddha confession; Great-Compassion dhāraṇī; ten-bhūmi block).
- Mislabeled Tōhoku: the Chinese text has a real Tibetan parallel, but a
  DIFFERENT Toh than the one aligned (Vasudhārā → Toh 662 not 661;
  Bhavasaṃkrānti → Toh 3840; Adbhutadharmaparyāya T704 → Toh 332).

## Files
- `cov97_verdicts.json` — pass 1 (97, relation + evidence)
- `cov97_pass2_reconcile.json` — pass 2 verdicts + reconciliation
- `cov97_final_resolved.json` — final per-parallel resolved verdicts (47 genuine)

## Caveat
All three passes are LLM adjudications, documentary but not human-expert.
An independent Buddhologist sample (reviewer's suggestion) remains the
strongest possible confirmation and is a live option (Bingenheimer / Muller).
