"""All tunable parameters for the digest detection pipeline."""

from multiprocessing import cpu_count
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
EXCERPT_THRESHOLD = 0.80  # Containment >= this → excerpt (verbatim extraction)
DIGEST_THRESHOLD = 0.30  # Containment >= this → digest (condensed derivation)
COMMENTARY_AVG_SEG_LEN = 10  # Below this avg segment length → commentary
EXCERPT_AVG_SEG_LEN = 15  # Excerpt requires avg segment >= this
SHARED_TRADITION_THRESHOLD = 0.10  # Below digest, above this → shared tradition
RETRANSLATION_SIZE_RATIO = 3.0  # Texts within this ratio may be retranslations

# Confidence score weights (must sum to 1.0)
WEIGHT_CONTAINMENT = 0.35
WEIGHT_LONGEST_SEGMENT = 0.20
WEIGHT_NUM_REGIONS = 0.10
WEIGHT_LENGTH_ASYMMETRY = 0.10
WEIGHT_DOCNUMBER_XREF = 0.15
WEIGHT_AVG_SEGMENT_LEN = 0.10

# --- Stage 3b: Phonetic Transliteration Detection ---
ENABLE_PHONETIC_SCAN = True  # Enable post-hoc phonetic rescan of novel segments
PHONETIC_SEED_LENGTH = 5  # Min consecutive phonetically equivalent chars to seed
PHONETIC_COVERAGE_WEIGHT = 0.8  # Weight for phonetic matches in coverage (vs 1.0 for exact/fuzzy)
PHONETIC_MAX_SYLLABLES = 5  # Max syllable values per char (more → too ambiguous)

# --- Stage 2b: Phonetic Candidate Generation ---
PHONETIC_NGRAM_SIZE = 3  # Syllable n-gram size for phonetic inverted index
PHONETIC_STOPGRAM_DOC_FREQ = 0.05  # Exclude syllable n-grams in >5% of indexed texts
MIN_PHONETIC_CONTAINMENT = 0.25  # Minimum phonetic containment to keep pair
TRANSLITERATION_DENSITY = 0.6  # Min fraction of table chars in a window
TRANSLITERATION_WINDOW = 20  # Sliding window size for density-based detection
MIN_TRANSLITERATION_LENGTH = 10  # Minimum region length (chars) to index

# --- Stage 3: Alignment Pre-filtering ---
# Skip zero-containment docNumber pairs where both texts exceed this length.
# Such pairs have no n-gram overlap and are expensive to align for no benefit.
# Small texts (<5000 chars) are cheap to align so we keep them just in case.
DOCNUM_PREFILTER_MIN_LEN = 5000

# --- Pipeline ---
NUM_WORKERS = None  # None = use resolve_worker_count()
DEFAULT_MAX_WORKERS = 4  # Cap default workers to limit memory on 16 GB machines
ALIGN_NUM_WORKERS = None  # None = use cpu_count() (alignment is memory-light)
CACHE_DIR = BASE_DIR / "data" / "cache"
MAXTASKSPERCHILD = 100  # Periodically restart workers to reclaim leaked memory


def resolve_worker_count(num_workers: int | None = None,
                         memory_intensive: bool = True) -> int:
    """Resolve the effective number of parallel workers.

    If num_workers is explicitly provided (e.g. via --workers), use it.
    Otherwise, use NUM_WORKERS from config, or default to
    min(cpu_count(), DEFAULT_MAX_WORKERS).

    For memory-light stages (alignment), set memory_intensive=False to
    default to cpu_count() instead of DEFAULT_MAX_WORKERS.
    """
    if num_workers is not None:
        return max(1, num_workers)
    if NUM_WORKERS is not None:
        return max(1, NUM_WORKERS)
    if not memory_intensive:
        return max(1, min(cpu_count(), 16))
    return max(1, min(cpu_count(), DEFAULT_MAX_WORKERS))
