"""All tunable parameters for the digest detection pipeline."""

from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
XML_DIR = BASE_DIR / "xml" / "T"
DATA_DIR = BASE_DIR / "data"
TEXTS_DIR = DATA_DIR / "texts"
METADATA_PATH = DATA_DIR / "metadata.json"
RESULTS_DIR = BASE_DIR / "results"
ALIGNMENTS_DIR = RESULTS_DIR / "alignments"

# --- Stage 1: Text Extraction ---
MIN_TEXT_LENGTH = 20  # Skip fragments shorter than this (in CJK chars)

# --- Stage 2: Candidate Generation ---
NGRAM_SIZE = 5  # Character n-gram size
STOPGRAM_DOC_FREQ = 0.05  # Exclude n-grams appearing in >5% of texts
MIN_CONTAINMENT = 0.10  # Minimum containment score to keep a candidate pair
MIN_SIZE_RATIO = 2.0  # Source must be >= 2x digest length
MAX_DIGEST_LENGTH = 50000  # Texts longer than this unlikely to be digests

# --- Stage 3: Detailed Alignment ---
MIN_SEED_LENGTH = 5  # Minimum exact match length to seed alignment
FUZZY_EXTEND_THRESHOLD = -4  # Stop fuzzy extension when score drops below this
FUZZY_MATCH_SCORE = 1  # Score for matching character during fuzzy extend
FUZZY_MISMATCH_SCORE = -2  # Score for mismatching character during fuzzy extend

# --- Stage 4: Scoring and Classification ---
FULL_DIGEST_THRESHOLD = 0.70  # Containment >= this → full digest
PARTIAL_DIGEST_THRESHOLD = 0.30  # Containment >= this → partial digest
COMMENTARY_AVG_SEG_LEN = 10  # Below this avg segment length → commentary
SHARED_TRADITION_THRESHOLD = 0.10  # Below partial, above this → shared tradition
RETRANSLATION_SIZE_RATIO = 3.0  # Texts within this ratio may be retranslations

# Confidence score weights (must sum to 1.0)
WEIGHT_CONTAINMENT = 0.35
WEIGHT_LONGEST_SEGMENT = 0.20
WEIGHT_NUM_REGIONS = 0.10
WEIGHT_LENGTH_ASYMMETRY = 0.10
WEIGHT_DOCNUMBER_XREF = 0.15
WEIGHT_AVG_SEGMENT_LEN = 0.10

# --- Pipeline ---
NUM_WORKERS = None  # None = use cpu_count()
