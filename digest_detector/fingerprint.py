"""Stage 2a: N-gram fingerprinting and inverted index construction.

Generates character n-gram fingerprints for each text, filters stop-grams
(common Buddhist formulae), and builds an inverted index for fast lookup.
"""

import logging
from collections import defaultdict

from . import config
from .models import ExtractedText

logger = logging.getLogger(__name__)


def generate_ngrams(text: str, n: int = None) -> list[str]:
    """Generate all overlapping character n-grams from text."""
    if n is None:
        n = config.NGRAM_SIZE
    if len(text) < n:
        return []
    return [text[i:i + n] for i in range(len(text) - n + 1)]



def compute_document_frequencies(
    texts: list[ExtractedText],
    n: int = None,
) -> dict[int, int]:
    """Compute document frequency for each n-gram hash.

    Returns dict mapping ngram_hash → number of texts containing it.
    """
    if n is None:
        n = config.NGRAM_SIZE
    doc_freq = defaultdict(int)

    for text in texts:
        # Use a set to count each n-gram only once per document
        seen = set()
        # full_text is used intentionally: document frequencies should reflect
        # all content (including prefaces) since stop-gram identification must
        # be based on actual corpus-wide frequencies.
        content = text.full_text
        for i in range(len(content) - n + 1):
            h = hash(content[i:i + n])
            if h not in seen:
                seen.add(h)
                doc_freq[h] += 1

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


def build_inverted_index(
    texts: list[ExtractedText],
    stopgrams: set[int],
    n: int = None,
) -> dict[int, list[tuple[str, int]]]:
    """Build inverted index: ngram_hash → [(text_id, position), ...].

    Excludes stop-grams. Only indexes non-stop n-grams.
    """
    if n is None:
        n = config.NGRAM_SIZE
    index = defaultdict(list)

    for text in texts:
        # full_text is used intentionally: the inverted index should reflect
        # all content (including prefaces) since texts can serve as sources
        # using their full text.
        content = text.full_text
        for i in range(len(content) - n + 1):
            h = hash(content[i:i + n])
            if h not in stopgrams:
                index[h].append((text.text_id, i))

    logger.info("Built inverted index with %d distinct n-gram hashes", len(index))
    return dict(index)


def fingerprint_text(
    text: str,
    stopgrams: set[int],
    n: int = None,
) -> list[int]:
    """Get the non-stop n-gram hashes for a single text."""
    if n is None:
        n = config.NGRAM_SIZE
    result = []
    for i in range(len(text) - n + 1):
        h = hash(text[i:i + n])
        if h not in stopgrams:
            result.append(h)
    return result
