# Validation Report: Ground Truth Comparison

**Passed:** 6 | **Failed:** 0

## [PASS] T08n0250 → T08n0223

_T250 (Kumārajīva Heart Sutra) is a digest of T223_

- [PASS] classification: expected=digest, actual=digest
- [PASS] coverage: expected=>= 0.7, actual=0.7315

Detailed scores:
  - classification: digest
  - confidence: 0.6598
  - coverage: 0.7315
  - novel_fraction: 0.2685
  - avg_segment_length: 27.25
  - longest_segment: 156
  - num_source_regions: 8

## [PASS] T08n0251 → T08n0223

_T251 (Xuanzang Heart Sutra) jing section is a digest of T223_

- [PASS] classification: expected=digest, actual=digest
- [PASS] coverage: expected=>= 0.3, actual=0.4462

Detailed scores:
  - classification: digest
  - confidence: 0.4683
  - coverage: 0.4462
  - novel_fraction: 0.5538
  - avg_segment_length: 12.89
  - longest_segment: 62
  - num_source_regions: 6

## [PASS] T08n0250 → T08n0251

_T08n0250 should NOT be classified as digest of T08n0251_

- [PASS] not_digest_of_each_other: actual=retranslation

## [PASS] T08n0251 → T08n0250

_T08n0251 should NOT be classified as digest of T08n0250_

- [PASS] not_digest_of_each_other: actual=not_found
