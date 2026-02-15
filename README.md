# Taisho Canon Digest Detection Pipeline

Computational detection of digest (*chaojing* 抄經) relationships across the Taisho Tripitaka. A "digest" is a shorter text derived by excerpting or condensing a longer source.

The pipeline processes the CBETA TEI P5b XML corpus through five sequential stages:

```
XML corpus → Extract → Fingerprint/Candidates → Align → Score → Report
```

See [docs/architecture.md](docs/architecture.md) for full technical details and [docs/findings.md](docs/findings.md) for results.

## Quick Start

```bash
# 1. Clone this repository
git clone https://github.com/dangerzig/taisho-canon.git
cd taisho-canon

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Download the CBETA XML corpus (~2.4 GB)
./setup.sh

# 4. Run the pipeline
python3 -m digest_detector.pipeline

# 5. View results
open results/summary.md
```

## Setup

### Prerequisites

- Python 3.10+
- Git (for cloning the CBETA corpus)
- ~5 GB free disk space (2.4 GB corpus + generated data)

### Installing Dependencies

```bash
pip install -r requirements.txt
```

Required packages: `lxml`, `tqdm`, `numpy`, `pytest` (for testing).

### Downloading the Corpus

Run the setup script to download the CBETA TEI P5b XML corpus:

```bash
./setup.sh
```

This clones the [CBETA XML P5 repository](https://github.com/cbeta-org/xml-p5) and symlinks the Taisho (T) volume into `xml/T/` as expected by the pipeline. The download is ~2.4 GB.

Alternatively, download manually:

```bash
git clone --depth 1 https://github.com/cbeta-org/xml-p5.git cbeta-xml-p5
mkdir -p xml
ln -s "$(pwd)/cbeta-xml-p5/T" xml/T
```

### Running Tests

```bash
python3 -m pytest tests/ -v
```

97 tests covering all pipeline stages plus integration tests on the Heart Sutra (T250/T251 → T223).

## Pipeline Stages

1. **Extract** — Parse CBETA TEI P5b XML, resolve character declarations, normalize to CJK
2. **Fingerprint** — Build character 5-gram inverted index with stop-gram filtering
3. **Candidates** — Generate candidate pairs via containment similarity + docNumber cross-references
4. **Align** — Seed-and-extend alignment with weighted interval scheduling
5. **Score** — Classify relationships and compute confidence scores
6. **Report** — Generate JSON results, alignment data, summary, and ground truth validation

## Output

Results are written to `results/`:

- `digest_relationships.json` — All scored relationships with full feature vectors
- `alignments/*.json` — Per-pair segment-level alignment data
- `summary.md` — Human-readable statistics, top results, cluster analysis
- `validation.md` — Ground truth validation (Heart Sutra test case)

## Key Findings

The pipeline detected **2,812 relationships** involving **1,412 texts**:

| Classification | Count |
|----------------|------:|
| Full Digest | 181 |
| Partial Digest | 484 |
| Retranslation | 288 |
| Commentary | 621 |
| Shared Tradition | 1,238 |

Plus 63 multi-source digests. See [docs/findings.md](docs/findings.md) for details.

## Documentation

- [docs/architecture.md](docs/architecture.md) — Technical architecture and design decisions
- [docs/findings.md](docs/findings.md) — Full results and analysis
- [docs/heart-sutra-analysis.md](docs/heart-sutra-analysis.md) — Heart Sutra uniqueness analysis
- [docs/chinese-vs-sanskrit-origins.md](docs/chinese-vs-sanskrit-origins.md) — Chinese vs Sanskrit origin signatures
- [docs/literature-review.md](docs/literature-review.md) — Literature review of related scholarship

## License

Pipeline code is provided for research purposes. The CBETA XML corpus is subject to [CBETA's terms of use](https://www.cbeta.org/).
