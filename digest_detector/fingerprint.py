"""Stage 2a: N-gram fingerprinting and n-gram set construction.

Generates character n-gram fingerprints for each text, filters stop-grams
(common Buddhist formulae), and builds per-text n-gram sets for fast
set-intersection containment scoring.
"""

import logging
import zlib
from collections import Counter, defaultdict
from multiprocessing import Pool

from . import config
from .fast import fast_ngram_hashes
from .models import ExtractedText

logger = logging.getLogger(__name__)


def stable_hash(s: str) -> int:
    """Deterministic hash for n-gram strings, stable across processes.

    Python's built-in hash() is randomized per-process (PEP 456). On macOS,
    multiprocessing uses 'spawn' which creates fresh processes with different
    hash seeds, making hash() inconsistent across workers. This function
    uses zlib.crc32 which is deterministic, C-level fast, and sufficient
    for n-gram fingerprinting (32-bit output).
    """
    return zlib.crc32(s.encode('utf-8'))

# --- Pool worker state (set via initializer, avoids per-task pickling) ---
_worker_stopgrams: set[int] = set()
_worker_n: int = 5


def _ngram_set_init(stopgrams: set[int], n: int):
    """Pool initializer: set shared stopgrams and n for all workers."""
    global _worker_stopgrams, _worker_n
    _worker_stopgrams = stopgrams
    _worker_n = n


def generate_ngrams(text: str, n: int = None) -> list[str]:
    """Generate all overlapping character n-grams from text."""
    if n is None:
        n = config.NGRAM_SIZE
    if len(text) < n:
        return []
    return [text[i:i + n] for i in range(len(text) - n + 1)]


def _doc_freq_worker(args: tuple) -> frozenset[int]:
    """Worker: return set of unique n-gram hashes for one text."""
    full_text, n = args
    return fast_ngram_hashes(full_text, n)


def compute_document_frequencies(
    texts: list[ExtractedText],
    n: int = None,
    num_workers: int = None,
) -> dict[int, int]:
    """Compute document frequency for each n-gram hash.

    Returns dict mapping ngram_hash → number of texts containing it.
    Uses multiprocessing to compute per-text hash sets in parallel.
    """
    if n is None:
        n = config.NGRAM_SIZE
    num_workers = config.resolve_worker_count(num_workers)

    # full_text is used intentionally: document frequencies should reflect
    # all content (including prefaces) since stop-gram identification must
    # be based on actual corpus-wide frequencies.
    args_list = [(text.full_text, n) for text in texts]

    doc_freq: Counter[int] = Counter()
    if num_workers <= 1 or len(texts) < 10:
        for args in args_list:
            doc_freq.update(_doc_freq_worker(args))
    else:
        chunksize = max(1, len(args_list) // (num_workers * 4))
        with Pool(num_workers, maxtasksperchild=config.MAXTASKSPERCHILD) as pool:
            for hash_set in pool.imap_unordered(_doc_freq_worker, args_list,
                                                chunksize=chunksize):
                doc_freq.update(hash_set)

    return dict(doc_freq)


def identify_stopgrams(
    doc_freq: dict[int, int],
    num_texts: int,
    threshold: float = None,
) -> set[int]:
    """Identify n-gram hashes that appear in too many documents (stop-grams).

    These are common Buddhist formulae and boilerplate that would produce
    false matches.
    """
    if threshold is None:
        threshold = config.STOPGRAM_DOC_FREQ
    max_docs = int(num_texts * threshold)
    stopgrams = {h for h, freq in doc_freq.items() if freq > max_docs}
    logger.info("Identified %d stop-grams (appearing in >%d texts)",
                len(stopgrams), max_docs)
    return stopgrams


def _ngram_set_worker(args: tuple) -> tuple[str, frozenset[int]]:
    """Worker: return (text_id, frozenset of non-stop n-gram hashes).

    Uses module-level _worker_stopgrams and _worker_n set by _ngram_set_init
    to avoid pickling shared data per task.
    """
    text_id, full_text = args
    return (text_id, fast_ngram_hashes(full_text, _worker_n, _worker_stopgrams))


def build_ngram_sets(
    texts: list[ExtractedText],
    stopgrams: set[int],
    n: int = None,
    num_workers: int = None,
) -> dict[str, frozenset[int]]:
    """Build per-text n-gram hash sets (no positions stored).

    Returns dict mapping text_id → frozenset of non-stop n-gram hashes.
    Uses full_text for source texts (so they can match against any digest content).
    Uses multiprocessing to build sets in parallel.
    """
    if n is None:
        n = config.NGRAM_SIZE
    num_workers = config.resolve_worker_count(num_workers)

    args_list = [(text.text_id, text.full_text) for text in texts]

    result = {}
    if num_workers <= 1 or len(texts) < 10:
        # Serial path: set module globals directly for the worker
        global _worker_stopgrams, _worker_n
        _worker_stopgrams = stopgrams
        _worker_n = n
        for args in args_list:
            text_id, hash_set = _ngram_set_worker(args)
            result[text_id] = hash_set
    else:
        chunksize = max(1, len(args_list) // (num_workers * 4))
        with Pool(num_workers, initializer=_ngram_set_init,
                  initargs=(stopgrams, n),
                  maxtasksperchild=config.MAXTASKSPERCHILD) as pool:
            for text_id, hash_set in pool.imap_unordered(
                _ngram_set_worker, args_list, chunksize=chunksize,
            ):
                result[text_id] = hash_set

    total_hashes = sum(len(s) for s in result.values())
    logger.info("Built n-gram sets for %d texts (%d total hashes)",
                len(result), total_hashes)

    if logger.isEnabledFor(logging.DEBUG):
        all_hashes: set[int] = set()
        for s in result.values():
            all_hashes.update(s)
        unique = len(all_hashes)
        logger.debug("Hash space: %d unique hashes out of %d total "
                     "(%.2f%% overlap from shared n-grams + collisions)",
                     unique, total_hashes,
                     (1 - unique / total_hashes) * 100 if total_hashes else 0)

    return result


def fingerprint_text(
    text: str,
    stopgrams: set[int],
    n: int = None,
) -> list[int]:
    """Get the non-stop n-gram hashes for a single text."""
    if n is None:
        n = config.NGRAM_SIZE
    return list(fast_ngram_hashes(text, n, stopgrams))
