# Architecture: Taisho Canon Digest Detection Pipeline

## Overview

The pipeline detects digest (*chaojing* 抄經) relationships across ~2,459 texts in the Taisho Tripitaka. A "digest" is a shorter text derived by excerpting or condensing a longer source. The pipeline processes the CBETA TEI P5b XML corpus through five sequential stages:

```
XML corpus → Extract → Fingerprint/Candidates → Phonetic Candidates → Align → Score → Report
              (1)           (2a/2b)                    (2c)            (3)     (4)     (5)
```

Entry point: `python3 -m digest_detector.pipeline`

## Project Layout

```
digest_detector/
  __init__.py          Public API and __all__
  config.py            All tunable parameters (paths, thresholds, weights)
  models.py            Dataclasses: ExtractedText, CandidatePair, AlignmentResult, etc.
  extract.py           Stage 1: XML parsing, charDecl resolution, normalization
  fingerprint.py       Stage 2a: N-gram fingerprinting, stop-gram filtering, inverted index
  candidates.py        Stage 2b: Candidate pair selection via containment + docNumber refs
  align.py             Stage 3: Seed-and-extend alignment with weighted interval scheduling
  score.py             Stage 4: Classification and confidence scoring
  report.py            Stage 5: Ground truth validation and report generation
  phonetic.py          Stage 2c: Phonetic transliteration equivalence table and detection
  cache.py             Disk cache for Stages 1–2c (invalidates on config/corpus changes)
  fast.py              Cython/fallback dispatcher for performance-critical inner loops
  _fast.pyx            Cython implementations (fuzzy_extend, find_seeds, phonetic seeds)
  _fast_fallback.py    Pure-Python fallbacks when Cython is not compiled
  pipeline.py          Orchestrator: runs stages 1–5 sequentially

tests/
  test_extract.py      XML parsing, charDecl, normalization, div tracking
  test_fingerprint.py  N-gram generation, document frequencies, stop-grams, inverted index
  test_candidates.py   DocNumber parsing, pair ordering, containment scoring, jing_text
  test_align.py        Seeds, fuzzy extension, chaining, full alignment
  test_score.py        Classification branches, confidence, multi-source detection
  test_known_pairs.py  Integration tests on T250/T251→T223 (Heart Sutra ground truth)
  test_phonetic.py     Phonetic equivalence table, transliteration detection, seed finding
  test_fast.py         Cython vs. fallback equivalence, edge cases for optimized functions
  test_cache.py        Cache save/load, invalidation on config/corpus changes

docs/                  Research documents (literature review, findings, analyses)
xml/T/                 CBETA TEI P5b XML corpus (~8,982 files across 58 volumes)
data/                  Extracted plain texts and metadata.json (generated)
results/               Pipeline output: JSON relationships, alignments, summary, validation
```

## Data Model

All inter-stage data flows through dataclasses defined in `models.py`:

```
TextMetadata          Per-text metadata (title, author, juan count, char count, docNumber refs,
                      dharani_ranges)
  ↓
DivSegment            A contiguous text region with its cb:div type ("jing", "xu", etc.)
  ↓
ExtractedText         Full extracted text + segments + metadata; has jing_text property
  ↓
CandidatePair         A (digest_id, source_id) pair with containment score from Stage 2
  ↓
AlignmentSegment      One aligned segment: digest range, source range, match type
  ↓
AlignmentResult       Full alignment: list of segments + coverage/span/region stats
  ↓
DigestScore           Classification + confidence + all quantitative features
  ↓
MultiSourceDigest     A text with combined coverage from multiple sources
```

## Stage 1: Text Extraction (`extract.py`)

**Input:** CBETA TEI P5b XML files in `xml/T/`

**Output:** List of `ExtractedText` objects

### Process

1. **File grouping.** XML files are grouped by text ID (e.g., `T08n0223_001.xml` through `T08n0223_027.xml` form one text). Files are sorted by fascicle number to preserve text order.

2. **Character map construction.** All `<charDecl>` elements across the corpus are scanned to build a global map from CBETA character IDs (e.g., `CB00001`) to Unicode characters. Priority order:
   - `<charProp><localName>normalized form</localName>` → use `<value>`
   - `<mapping type="normal_unicode">` → decode hex (`U+XXXX`)
   - `<mapping type="unicode">` → decode hex
   - Fallback: skip with warning

3. **Recursive text extraction.** Each XML body is walked recursively:
   - **Skip tags** (text/tail/children ignored): `<note>`, `<rdg>`, `<byline>`, `<cb:docNumber>`, `<cb:juan>`, `<lb>`, `<pb>`, `<milestone>`, `<cb:mulu>`
   - **`<app>` handling**: Only `<lem>` text is used; `<rdg>` variants are skipped
   - **`<g ref="#CBnnnnn"/>`**: Resolved via the character map
   - **`<cb:div>` tracking**: A stack tracks the current div type; text is annotated with its enclosing div type (`jing`, `xu`, `pin`, etc.)

4. **Normalization.** All extracted text is stripped to CJK ideographs only (regex matching Unicode ranges U+4E00–9FFF, U+3400–4DBF, U+20000–2A6DF, U+2A700–2B81F).

5. **Segment construction.** Consecutive text regions with the same div type are merged into `DivSegment` objects, with character offsets into the concatenated full text.

6. **Metadata extraction.** Title (zh-Hant, level="m"), author, extent (juan count), docNumber cross-references (parsed from bracket notation like `[Nos. 251-255, 257]`), dharani presence, dharani character ranges (`dharani_ranges`), and div types are extracted from the TEI header and body. Dharani ranges record the start/end character offsets of `<cb:div type="dharani">` content within the full text, enabling precise targeting of transliterated passages in later stages.

7. **Parallelization.** Text groups are processed in parallel via `multiprocessing.Pool`.

### Key Design Decision: jing_text

The `ExtractedText.jing_text` property returns only `jing`-type (sutra body) segments, falling back to `full_text` when no jing segments exist. This is used on the **digest side** of alignment (Stages 2b and 3) to exclude preface material that would dilute coverage scores. Source texts always use `full_text`.

## Stage 2a: Fingerprinting (`fingerprint.py`)

**Input:** List of `ExtractedText` objects

**Output:** Document frequencies, stop-grams set, per-text n-gram sets

### Process

1. **Document frequency computation.** For each text's `full_text`, generate all character 5-grams, hash them with `stable_hash()` (zlib.crc32, deterministic across processes), and count how many texts contain each hash. Uses a per-document `seen` set to count each n-gram at most once per document.

2. **Stop-gram identification.** Any n-gram hash appearing in more than `STOPGRAM_DOC_FREQ` (5%) of all texts is flagged as a stop-gram. These are common Buddhist formulae (如是我聞, etc.) that would produce spurious matches.

3. **N-gram set construction.** For each text's `full_text`, build a `frozenset[int]` of all non-stop 5-gram hashes. Candidate generation then uses C-level set intersection to compute containment scores, avoiding the memory overhead of a full inverted index.

### Why full_text for indexing?

Both document frequencies and n-gram sets use `full_text` (not `jing_text`). Stop-gram identification must reflect actual corpus-wide frequencies, and source texts need their full content indexed since digests can draw from any part (including prefaces).

## Stage 2b: Candidate Generation (`candidates.py`)

**Input:** Texts, per-text n-gram sets, stop-grams

**Output:** List of `CandidatePair` objects, sorted by containment score

### Process

Two mechanisms generate candidates:

**Fingerprint-based containment:**
1. For each potential digest (texts with `char_count <= MAX_DIGEST_LENGTH` = 50,000):
   - Generate 5-grams from `jing_text` (not full_text — excludes prefaces)
   - Skip stop-grams; count total non-stop n-grams
   - Compute set intersection with each source text's n-gram set
   - `containment = |digest_set ∩ source_set| / |digest_set|`
2. Filter: source must be at least `MIN_SIZE_RATIO` (2x) the digest length
3. Filter: containment must exceed `MIN_CONTAINMENT` (0.10)
4. Binary search prefiltering: candidates are sorted by size, skipping sources below `MIN_SIZE_RATIO`

**DocNumber cross-references:**
1. Parse `docNumber` refs from metadata (e.g., T250 references T251–T255)
2. Normalize leading zeros: `"0250"` → `"250"`
3. Build map: `"T08:250"` → `{T08n0250}`; `"T08:251"` → `{T08n0250, T08n0251}`
4. Any docNumber key with 2+ text IDs generates candidate pairs
5. Pairs are ordered shorter-first (potential digest)
6. DocNumber pairs are added even if their containment score is below threshold

### Complexity

Set intersection via `frozenset` operations runs at C level, making candidate generation efficient. Only texts whose n-gram sets overlap with the digest are scored, avoiding full O(n²) computation.

## Stage 2c: Phonetic Candidate Generation (`candidates.py`, `phonetic.py`)

**Input:** Texts, phonetic equivalence table

**Output:** Additional `CandidatePair` objects (merged with Stage 2b output)

### Purpose

Buddhist texts contain transliterated Sanskrit passages (dharani, mantras) where different translators used different Chinese characters to represent the same Sanskrit syllables. Character-level n-gram matching misses these relationships entirely. Stage 2c detects them using phonetic equivalence.

### Process

1. **Equivalence table construction** (`phonetic.py`). The Digital Dictionary of Buddhism (DDB) is parsed to build a `char → frozenset[str]` table mapping Chinese characters to the Sanskrit syllables they transliterate. Characters with more than `PHONETIC_MAX_SYLLABLES` (5) possible readings are excluded as too ambiguous. Result: 559 characters, ~200 syllable groups.

2. **Transliteration region detection.** For each text, regions containing transliterated Sanskrit are identified via two methods:
   - XML-annotated `dharani_ranges` from `<cb:div type="dharani">` markup (precise)
   - Density-based detection: sliding window over the text; regions where >40% of characters appear in the equivalence table are flagged (approximate, higher false-positive rate)

3. **Syllable n-gram fingerprinting.** Within transliteration regions, each character is mapped to its syllable set. Syllable 3-grams are generated and hashed. Per-text syllable n-gram sets are built (analogous to Stage 2a's character n-gram sets).

4. **Phonetic containment scoring.** Set intersection computes phonetic containment between text pairs. Pairs exceeding `PHONETIC_MIN_CONTAINMENT` (0.25) are added as candidates, after stopgram filtering to remove common syllable sequences (appearing in >`PHONETIC_STOPGRAM_DOC_FREQ` texts).

5. **Deduplication.** Phonetic candidates are merged with Stage 2b candidates; pairs already present from character-level matching are not duplicated.

## Stage 3: Alignment (`align.py`)

**Input:** Candidate pairs + text map

**Output:** List of `AlignmentResult` objects with segment-by-segment mappings

This is the computational core. For each candidate pair, the algorithm aligns the digest's `jing_text` against the source's `full_text`.

### Algorithm: Seed-and-Extend with Weighted Interval Scheduling

**Step 1: Find seeds.** Build a k-gram hash table on the source text. For each position in the digest, look up the k-gram (k = `MIN_SEED_LENGTH` = 5) in the table. If found, extend greedily by exact character matching. Keep only the longest match at each digest position.

**Step 2: Fuzzy extension.** Each exact seed is extended in both directions using a simple scoring model:
- Match: +1
- Mismatch: -2
- Single-character gap (insertion/deletion in either text): try both options, take the one that realigns
- Stop when cumulative score drops below threshold (-4)
- Track the best-scoring extension point (prevents degrading past a good boundary)

**Step 3: Chain seeds (Weighted Interval Scheduling DP).** Seeds may overlap in digest coordinates. The algorithm selects a non-overlapping subset maximizing total digest coverage:
1. Sort seeds by digest end position
2. Pre-filter: remove seeds contained within larger seeds
3. DP: `dp[i]` = max coverage using seeds 0..i where seed i is included
4. For each seed i, find the rightmost non-overlapping predecessor j
5. `dp[i] = max(weight[i], dp[j] + weight[i])`
6. Backtrack to recover the selected seed set

Seeds do NOT need to be monotonic in source coordinates — digests can rearrange material from their source.

**Step 4: Build segments.** The chained seeds become matched segments (exact or fuzzy). Gaps between matched segments become "novel" segments. Together they partition the entire digest text.

**Step 5: Phonetic rescan of novel segments.**
If `ENABLE_PHONETIC_SCAN` is set and a phonetic equivalence table is available, novel segments (gaps between matched seeds) are rescanned for phonetic matches. For each novel segment of sufficient length, the algorithm searches the source text for positions where characters are phonetically equivalent (mapping to overlapping syllable sets). Phonetic seeds require at least `PHONETIC_SEED_LENGTH` (5) consecutive phonetically-equivalent characters with at least 2 differing characters (to avoid trivially identical matches). Discovered phonetic seeds are appended to the matched segment list with match type `phonetic`.

**Step 6: Compute statistics.**
- `coverage` = fraction of digest characters explained by matched segments (exact + fuzzy + phonetic)
- `novel_fraction` = 1 - coverage
- `source_span` = fraction of source text that contributes (computed via interval merging)
- `num_source_regions` = number of disjoint source regions (gaps > 100 chars define region boundaries)

### Parallelization

Alignment pairs are independent and processed in parallel via `multiprocessing.Pool`.

## Stage 4: Scoring and Classification (`score.py`)

**Input:** Alignment results, metadata, docNumber pairs, text map

**Output:** List of `DigestScore` objects (filtered: no_relationship excluded), list of `MultiSourceDigest` objects

### Classification

Each alignment is classified based on coverage, average segment length, and size ratio. The size ratio uses **jing lengths** when available (prevents preface-inflated lengths from distorting the ratio).

```
coverage < 0.10                              → no_relationship (filtered out)
0.10 ≤ coverage < 0.30                       → shared_tradition
size_ratio < 3.0 and coverage ≥ 0.30         → retranslation
coverage ≥ 0.80 and avg_seg_len ≥ 15         → excerpt
coverage ≥ 0.30 and avg_seg_len ≥ 10         → digest
coverage ≥ 0.20 and avg_seg_len < 10         → commentary
else                                          → digest
```

### Confidence Score

A weighted sum of six normalized features:

| Feature | Weight | Normalization |
|---------|--------|---------------|
| Containment (coverage) | 0.35 | min(coverage, 1.0) |
| Longest segment | 0.20 | min(longest_seg / digest_length, 1.0) |
| DocNumber cross-ref | 0.15 | 1.0 if present, 0.0 otherwise |
| Avg segment length | 0.10 | min(avg_seg_len / 20, 1.0) |
| Number of source regions | 0.10 | min((regions - 1) / 4, 1.0) |
| Length asymmetry | 0.10 | min(log2(size_ratio) / 10, 1.0) |

Weights sum to 1.0. Confidence ranges from 0 to 1.

### Multi-Source Digest Detection

For each text that appears as a digest in 2+ relationships, compute the **union coverage** across all sources by merging matched digest intervals. If the combined coverage exceeds the best single-source coverage by at least 10%, flag as a multi-source digest.

## Stage 5: Validation and Reporting (`report.py`)

**Input:** Scores, alignments, metadata, multi-source digests

**Output:** Files in `results/`

### Ground Truth Validation

Hardcoded test expectations for the Heart Sutra:

| Pair | Expected Class | Min Coverage |
|------|---------------|-------------|
| T08n0250 → T08n0223 | digest | 0.70 |
| T08n0251 → T08n0223 | digest | 0.30 |
| T08n0250 ↔ T08n0251 | NOT digest of each other | — |

6 checks total (2 classification + 2 coverage + 2 not-digest).

### Output Files

- `results/digest_relationships.json` — All scored relationships with full feature vectors
- `results/alignments/*.json` — Per-pair segment-level alignment data
- `results/summary.md` — Human-readable: statistics, top-50 table, cluster analysis, multi-source digests, alignment visualizations for top 20
- `results/validation.md` — Ground truth check results

## Configuration (`config.py`)

All tunable parameters are centralized in `config.py`. Key groups:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `NGRAM_SIZE` | 5 | Character n-gram length |
| `STOPGRAM_DOC_FREQ` | 0.05 | Exclude n-grams in >5% of texts |
| `MIN_CONTAINMENT` | 0.10 | Minimum containment to keep candidate |
| `MIN_SIZE_RATIO` | 2.0 | Source must be ≥ 2x digest length |
| `MAX_DIGEST_LENGTH` | 50,000 | Max chars for a digest candidate |
| `MIN_SEED_LENGTH` | 5 | Minimum exact match to seed alignment |
| `FUZZY_MATCH_SCORE` | +1 | Character match reward |
| `FUZZY_MISMATCH_SCORE` | -2 | Character mismatch penalty |
| `FUZZY_EXTEND_THRESHOLD` | -4 | Stop extension when score drops below |
| `EXCERPT_THRESHOLD` | 0.80 | Coverage for excerpt |
| `DIGEST_THRESHOLD` | 0.30 | Coverage for digest |
| `RETRANSLATION_SIZE_RATIO` | 3.0 | Max ratio for retranslation |
| `COMMENTARY_AVG_SEG_LEN` | 10 | Below this → commentary |
| `PHONETIC_SEED_LENGTH` | 5 | Min consecutive phonetically-equivalent chars |
| `PHONETIC_NGRAM_SIZE` | 3 | Syllable n-gram length for fingerprinting |
| `PHONETIC_MIN_CONTAINMENT` | 0.25 | Min phonetic containment for candidates |
| `PHONETIC_STOPGRAM_DOC_FREQ` | 50 | Exclude common syllable n-grams |
| `PHONETIC_MAX_SYLLABLES` | 5 | Max syllable readings per character |
| `ENABLE_PHONETIC_SCAN` | True | Enable phonetic rescan in alignment |

## Test Suite

245 tests across 9 files:

- **test_extract.py** — charDecl resolution, CJK normalization, div type tracking, app/lem handling, metadata extraction
- **test_fingerprint.py** — n-gram generation, document frequencies, stop-gram thresholds, inverted index structure
- **test_candidates.py** — DocNumber key normalization (leading-zero stripping), pair ordering (shorter-first), size ratio filtering, containment scoring, jing_text usage on digest side
- **test_align.py** — Seed finding, fuzzy extension, seed chaining (DP), full alignment with novel segments, coverage/span computation
- **test_score.py** — All 6 classification branches, jing-aware size ratios, confidence weight sum = 1.0, score_all filtering, multi-source detection (union coverage, 10% threshold)
- **test_known_pairs.py** — Integration tests on real T250/T251/T223 extractions: T250→T223 coverage ≥ 0.50, T251 jing→T223 coverage ≥ 0.30, T250/T251 classified as retranslation not digest
- **test_phonetic.py** — Phonetic equivalence table construction, transliteration region detection, phonetic seed finding, known dharani pairs (T250→T901)
- **test_fast.py** — Cython vs. pure-Python fallback equivalence tests, edge cases for optimized functions
- **test_cache.py** — Cache save/load round-tripping, invalidation on config or corpus changes

Run: `python3 -m pytest tests/ -v`

## Dependencies

- **lxml** — XML parsing
- **tqdm** — Progress bars
- **pytest** — Testing
- **Cython** — Optional; compiles `_fast.pyx` for ~3-5x speedup on inner loops

No ML frameworks, no GPU requirements. The pipeline runs on CPU using Python's `multiprocessing` for parallelism.

## Key Architectural Decisions

1. **Character-level, not word-level.** Classical Chinese has no word boundaries. Operating on character n-grams avoids the word segmentation problem entirely, at the cost of missing semantic-level paraphrase.

2. **Asymmetric containment.** The pipeline measures what fraction of the *digest* appears in the *source*, not vice versa. This captures the defining property of digests: a short text largely contained within a longer one.

3. **Jing-aware on digest side only.** Digest texts use `jing_text` (excluding prefaces) for fingerprinting and alignment, since prefaces are not part of the digest relationship. Source texts use `full_text`, since digests can draw from any part of the source.

4. **Two candidate generation paths.** Fingerprint-based containment catches high-overlap pairs efficiently. DocNumber cross-references catch pairs that might have low character overlap (e.g., cross-translator relationships) but are known to be related from the Taisho editorial apparatus.

5. **Weighted interval scheduling for seed chaining.** Digest authors may rearrange material from the source, so seeds are not required to be monotonic in source coordinates. The DP selects the coverage-maximizing non-overlapping subset regardless of source order.

6. **No Smith-Waterman.** Full dynamic programming alignment (O(nm)) is infeasible for large texts (T223 has ~286,000 characters). The seed-and-extend approach achieves near-linear time in practice by only examining regions anchored by exact k-gram matches.

7. **Cython with pure-Python fallback.** Performance-critical inner loops (fuzzy extension, seed finding, phonetic seed finding) have Cython implementations in `_fast.pyx`. The `fast.py` dispatcher tries to import the compiled module; if unavailable, it falls back to equivalent pure-Python implementations in `_fast_fallback.py`. This ensures the pipeline works without a C compiler while benefiting from ~3-5x speedups when Cython is compiled.

8. **Disk cache for Stages 1-2c.** Text extraction and candidate generation are deterministic given the same corpus and config. `cache.py` saves results to `data/cache/` with a version stamp, config snapshot hash, and corpus content hash. On subsequent runs, the cache is loaded in ~1 second instead of re-running Stages 1-2c (~15 minutes). The cache auto-invalidates when any config parameter, code version, or XML file changes.

9. **Deterministic hashing.** `stable_hash()` uses `zlib.crc32` instead of Python's built-in `hash()`. This is critical for multiprocessing on macOS, where `spawn`-based workers get different hash seeds (PEP 456), breaking cross-process consistency.
