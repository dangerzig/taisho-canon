"""Tests for Stage 2: Fingerprinting and candidate generation."""

import pytest

from digest_detector.fingerprint import (
    generate_ngrams,
    compute_document_frequencies,
    identify_stopgrams,
    build_inverted_index,
    fingerprint_text,
)
from digest_detector.models import ExtractedText, TextMetadata


def _make_text(text_id: str, content: str) -> ExtractedText:
    """Helper to create a minimal ExtractedText."""
    return ExtractedText(
        text_id=text_id,
        full_text=content,
        segments=[],
        metadata=TextMetadata(
            text_id=text_id, title='', author='',
            extent_juan=1, char_count=len(content),
            file_count=1,
        ),
    )


class TestGenerateNgrams:
    def test_basic(self):
        ngrams = generate_ngrams("般若波羅蜜多心經", n=5)
        assert len(ngrams) == 4  # 8 - 5 + 1
        assert ngrams[0] == "般若波羅蜜"
        # 般若波羅蜜, 若波羅蜜多, 波羅蜜多心, 羅蜜多心經
        assert ngrams[-1] == "羅蜜多心經"

    def test_too_short(self):
        assert generate_ngrams("般若", n=5) == []

    def test_exact_length(self):
        assert len(generate_ngrams("般若波羅蜜", n=5)) == 1

    def test_custom_n(self):
        ngrams = generate_ngrams("般若波羅蜜多", n=3)
        assert len(ngrams) == 4  # 6 - 3 + 1


class TestDocumentFrequencies:
    def test_basic(self):
        texts = [
            _make_text("t1", "般若波羅蜜多心經"),
            _make_text("t2", "般若波羅蜜大明呪"),
            _make_text("t3", "觀自在菩薩行深"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)

        # "般若波羅蜜" appears in t1 and t2
        h = hash("般若波羅蜜")
        assert doc_freq.get(h, 0) == 2

        # "觀自在菩薩" appears only in t3
        h = hash("觀自在菩薩")
        assert doc_freq.get(h, 0) == 1


class TestStopgrams:
    def test_identifies_common_grams(self):
        # 3 texts, threshold 0.5, so any gram in >1.5 texts is a stopgram
        texts = [
            _make_text("t1", "般若波羅蜜多心經色空"),
            _make_text("t2", "般若波羅蜜大明呪色空"),
            _make_text("t3", "般若波羅蜜多心經玄奘"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=0.5)

        # "般若波羅蜜" appears in all 3 → stopgram
        assert hash("般若波羅蜜") in stopgrams


class TestInvertedIndex:
    def test_basic_structure(self):
        texts = [
            _make_text("t1", "般若波羅蜜多心經大明"),
            _make_text("t2", "觀自在菩薩行深般若波"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        # With threshold=1.0, nothing is a stopgram
        assert len(stopgrams) == 0

        index = build_inverted_index(texts, stopgrams, n=5)
        # Should contain entries
        assert len(index) > 0

        # Each entry should be a list of (text_id, position) tuples
        for h, postings in index.items():
            for text_id, pos in postings:
                assert isinstance(text_id, str)
                assert isinstance(pos, int)


class TestFingerprintText:
    def test_excludes_stopgrams(self):
        stopgrams = {hash("般若波羅蜜")}
        hashes = fingerprint_text("般若波羅蜜多心經", stopgrams, n=5)
        # "般若波羅蜜" should be excluded
        assert hash("般若波羅蜜") not in hashes
        # But other n-grams should be present
        assert len(hashes) == 3  # 4 total - 1 stopgram
