# Code Review: Classification Restructure (full_digest/partial_digest → excerpt/digest)

## Overview

Reviewed all 17 modified files for the classification rename and threshold change:
- `full_digest` (>=70%) → `excerpt` (>=80%)
- `partial_digest` (30-70%) → `digest` (30-80%)

---

## CRITICAL: summary.md has 40 wrong classifications

**Severity: HIGH**

The `results/summary.md` was updated with a naive string replacement (`full_digest` → `excerpt`), but this is wrong for entries with coverage between 70-80%. These should be `digest`, not `excerpt`, under the new scheme. The authoritative `digest_relationships.json` was reclassified correctly (using proper logic checking both coverage >= 0.80 AND avg_seg_len >= 15), but summary.md has **40 entries** where it says "excerpt" but the JSON correctly says "digest".

Examples of mismatches:
- T14n0571 → T53n2122: summary="excerpt", JSON="digest" (coverage=0.7796)
- T12n0370 → T53n2122: summary="excerpt", JSON="digest" (coverage=0.7438)
- T19n1029 → T21n1336: summary="excerpt", JSON="digest" (coverage=0.7971)
- T08n0250 → T08n0223: summary="excerpt", JSON="digest" (coverage=0.7315)

**Fix:** Rerun the pipeline (at least stages 4-5), or write a script that regenerates summary.md from the correctly-classified JSON.

---

## Documentation Issues

### findings.md

#### Issue 1 (MEDIUM): T250→T223 in retranslation validation table (line ~628)

Section 10.3's table of "validated retranslation pairs" includes:

> | T08n0250 (Heart Sutra, Kumarajiva) | T08n0223 (Prajnaparamita) | 73.2% | Toh 21 |

But T250→T223 is classified as a **digest**, not a retranslation. It doesn't belong in the retranslation validation table. The paragraph at line 631 correctly discusses it as a separate observation — the table row should be removed.

#### Issue 2 (MEDIUM): Dharani network diagrams have items in wrong columns

**T21n1336 network (lines 338-349):** The middle column "Excerpt/retrans." includes T19n1029 at "80%", but its actual coverage is 79.7% → classified as **digest**, not excerpt. It should move to the "Digests" column.

**T18n0901 network (lines 356-370):** The left column "Excerpts (84-71%)" includes T21n1254 at 71%, but 70.6% coverage → classified as **digest**, not excerpt. It should move to the "Digests" column.

#### Issue 3 (MINOR): Commentary range "20--70%" (line ~99)

The classification definition says "coverage 20--70%" for Commentary, but the code has no 70% upper bound — commentary fires whenever coverage >= 0.20 AND avg_seg_len < 10. The "70%" cap is misleading.

### heart-sutra-analysis.md

#### Issue 4 (MEDIUM): Old terminology at line 145

> "with 16 texts detected as full or partial digests"

Should be "excerpts or digests".

#### Issue 5 (MEDIUM): Table header mismatch at line ~448

The comparison table column header says "Typical digest (median)" but the values (~80-90% coverage) describe **excerpts**. The header should say "Typical excerpt (median)" since those coverage values are above the 80% threshold.

#### Issue 6 (MEDIUM): Date says "2025" at line 550

Should be "2026" per the git history and findings.md.

### literature-review.md (not in scope but flagged)

This file was not updated at all and still references "181 full digests, 484 partial digests" with old counts and terminology throughout (~4 occurrences). Needs a separate pass.

---

## Pipeline Code

### score.py

#### Issue 7 (LOW): Unreachable dead code at line 78

```python
else:
    classification = "digest"
```

This `else` branch can never execute. At that point in the decision tree, coverage >= 0.30 and avg_seg_len < 10, so the commentary branch (line 75, `coverage >= 0.20`) always fires first.

#### Issue 8 (LOW): Hardcoded magic numbers

The values `15` (excerpt avg_seg_len threshold, line 71) and `0.20` (commentary coverage floor, line 75) are not in `config.py`, unlike their counterparts `COMMENTARY_AVG_SEG_LEN = 10` and the other thresholds.

#### Issue 9 (LOW): Docstring slightly inaccurate

The `classify_relationship` docstring says commentary covers "0.20-0.80" — there is no 0.80 upper bound in the code. Also omits that the retranslation check fires before all other classifications when size_ratio < 3.0.

#### Issue 10 (LOW): Redundant condition on line 68

```python
elif size_ratio < config.RETRANSLATION_SIZE_RATIO and coverage >= config.DIGEST_THRESHOLD:
```

The `coverage >= config.DIGEST_THRESHOLD` is always true at this point (the previous branch already caught coverage < 0.30).

### report.py

No issues found. Ground truth correctly expects "digest" for both T250→T223 and T251→T223.

### config.py, models.py

No issues found. Clean and correct.

---

## Tests

### test_score.py

No issues found. All 8 classification tests trace correctly through the new decision tree. The boundary test at coverage=0.80 (test_includes_valid_relationships) is good.

### test_known_pairs.py

#### Issue 11 (MINOR): Overly permissive assertion at line 313

```python
assert score.classification in ("digest", "excerpt")
```

At ~44% coverage, T251 jing→T223 can only ever be "digest", never "excerpt" (would need >= 80%). Could be tightened to `== "digest"`.

#### Issue 12 (LOW): Missing test for excerpt blocked by low avg_seg_len

Coverage 0.85 with avg_seg_len=12 should yield "digest" (not "excerpt"), since the excerpt rule requires avg_seg_len >= 15. No test covers this edge case.

---

## Scripts

### generate_readable_output.py

No issues found. Classification names and descriptions are correct.

### cross_reference_analysis.py

No issues found. Classification name lists are complete and correct.

---

## Results Files

### digest_relationships.json — CORRECT

Programmatic verification: all 132 "excerpt" entries have coverage >= 0.80 AND avg_seg_len >= 15. All 533 "digest" entries correctly lack at least one of those conditions. Boundary cases verified. The Heart Sutra (T250→T223) at 73.2% is correctly "digest".

### cross_reference_analysis.json — CORRECT

Regenerated with new names. Counts match (132/533/288/621/1238).

### validation.md — CORRECT

All classification names updated. All 6 tests pass.

### summary.md — INCORRECT (see Critical issue above)

40 entries misclassified due to naive string replacement.

---

## Summary

| # | Severity | File | Issue |
|---|----------|------|-------|
| — | **CRITICAL** | results/summary.md | 40 entries say "excerpt" but should be "digest" |
| 1 | MEDIUM | findings.md | T250→T223 in retranslation table (it's a digest) |
| 2 | MEDIUM | findings.md | Dharani networks: items in wrong columns |
| 3 | MINOR | findings.md | Commentary range "20-70%" misleading |
| 4 | MEDIUM | heart-sutra-analysis.md | "full or partial digests" old terminology |
| 5 | MEDIUM | heart-sutra-analysis.md | Table header "digest" but values are excerpt-range |
| 6 | MEDIUM | heart-sutra-analysis.md | Date "2025" → "2026" |
| — | HIGH | literature-review.md | Not updated at all (out of scope) |
| 7 | LOW | score.py | Unreachable `else` dead code |
| 8 | LOW | score.py | Hardcoded magic numbers 15, 0.20 |
| 9 | LOW | score.py | Docstring inaccuracy on commentary range |
| 10 | LOW | score.py | Redundant condition |
| 11 | MINOR | test_known_pairs.py | Overly permissive assertion |
| 12 | LOW | test_score.py | Missing edge case test |
