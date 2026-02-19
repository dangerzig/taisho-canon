"""Tests for Stage 2: Fingerprinting and candidate generation."""

import pytest

from digest_detector.fingerprint import (
    generate_ngrams,
    compute_document_frequencies,
    identify_stopgrams,
    build_ngram_sets,
    fingerprint_text,
    stable_hash,
)
from digest_detector.models import ExtractedText, TextMetadata
from tests.helpers import make_text


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
            make_text("t1", "般若波羅蜜多心經"),
            make_text("t2", "般若波羅蜜大明呪"),
            make_text("t3", "觀自在菩薩行深"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)

        # "般若波羅蜜" appears in t1 and t2
        h = stable_hash("般若波羅蜜")
        assert doc_freq.get(h, 0) == 2

        # "觀自在菩薩" appears only in t3
        h = stable_hash("觀自在菩薩")
        assert doc_freq.get(h, 0) == 1


class TestStopgrams:
    def test_identifies_common_grams(self):
        # 3 texts, threshold 0.5, so any gram in >1.5 texts is a stopgram
        texts = [
            make_text("t1", "般若波羅蜜多心經色空"),
            make_text("t2", "般若波羅蜜大明呪色空"),
            make_text("t3", "般若波羅蜜多心經玄奘"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=0.5)

        # "般若波羅蜜" appears in all 3 → stopgram
        assert stable_hash("般若波羅蜜") in stopgrams


class TestNgramSets:
    def test_basic_structure(self):
        texts = [
            make_text("t1", "般若波羅蜜多心經大明"),
            make_text("t2", "觀自在菩薩行深般若波"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        # With threshold=1.0, nothing is a stopgram
        assert len(stopgrams) == 0

        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)
        # Should have one entry per text
        assert len(ngram_sets) == 2
        assert "t1" in ngram_sets
        assert "t2" in ngram_sets

        # Each entry should be a frozenset of ints
        for text_id, hashes in ngram_sets.items():
            assert isinstance(hashes, frozenset)
            for h in hashes:
                assert isinstance(h, int)

    def test_shared_ngrams(self):
        """Texts sharing an n-gram should have that hash in both sets."""
        texts = [
            make_text("t1", "般若波羅蜜多心經大明"),
            make_text("t2", "觀自在菩薩行深般若波羅蜜"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)

        # "般若波羅蜜" appears in both texts
        shared_hash = stable_hash("般若波羅蜜")
        assert shared_hash in ngram_sets["t1"]
        assert shared_hash in ngram_sets["t2"]

    def test_excludes_stopgrams(self):
        """Stopgram hashes should not appear in n-gram sets."""
        texts = [
            make_text("t1", "般若波羅蜜多心經大明"),
        ]
        stopgrams = {stable_hash("般若波羅蜜")}
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)
        assert stable_hash("般若波羅蜜") not in ngram_sets["t1"]


class TestStableHash:
    def test_deterministic(self):
        """Same input always produces the same hash."""
        assert stable_hash("般若波羅蜜") == stable_hash("般若波羅蜜")
        assert stable_hash("abc") == stable_hash("abc")

    def test_different_inputs(self):
        """Different strings produce different hashes."""
        assert stable_hash("般若波羅蜜") != stable_hash("觀自在菩薩")
        assert stable_hash("abc") != stable_hash("def")


class TestNumWorkersEdgeCases:
    """Verify num_workers=0 doesn't crash fingerprint functions."""

    def test_compute_doc_freq_zero_workers(self):
        texts = [
            make_text("t1", "般若波羅蜜多心經大明"),
            make_text("t2", "觀自在菩薩行深般若波"),
        ]
        result = compute_document_frequencies(texts, n=5, num_workers=0)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_build_ngram_sets_zero_workers(self):
        texts = [
            make_text("t1", "般若波羅蜜多心經大明"),
            make_text("t2", "觀自在菩薩行深般若波"),
        ]
        doc_freq = compute_document_frequencies(texts, n=5, num_workers=1)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        result = build_ngram_sets(texts, stopgrams, n=5, num_workers=0)
        assert len(result) == 2
        assert all(isinstance(v, frozenset) for v in result.values())


class TestFingerprintText:
    def test_excludes_stopgrams(self):
        stopgrams = {stable_hash("般若波羅蜜")}
        hashes = fingerprint_text("般若波羅蜜多心經", stopgrams, n=5)
        # "般若波羅蜜" should be excluded
        assert stable_hash("般若波羅蜜") not in hashes
        # But other n-grams should be present
        assert len(hashes) == 3  # 4 total - 1 stopgram
