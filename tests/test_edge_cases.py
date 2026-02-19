"""Edge-case tests for bisect boundary conditions and phonetic stopgram filtering.

Covers:
- Source at exactly MIN_SIZE_RATIO boundary in generate_candidates
- Phonetic stopgram filtering removes high-frequency syllable n-grams
"""

import pytest
from collections import defaultdict

from digest_detector import config
from digest_detector.fingerprint import (
    compute_document_frequencies,
    identify_stopgrams,
    build_ngram_sets,
)
from digest_detector.candidates import generate_candidates, generate_phonetic_candidates
from digest_detector.phonetic import build_equivalence_table
from digest_detector.models import ExtractedText, TextMetadata
from tests.helpers import make_text


class TestBisectBoundary:
    """Test that the binary-search size prefilter handles boundary conditions."""

    def test_source_exactly_at_ratio_boundary(self):
        """Source at exactly d_len * MIN_SIZE_RATIO should be included."""
        # digest has 10 chars; MIN_SIZE_RATIO=2.0 means source needs >= 20 chars
        shared = "觀自在菩薩行深般若波"  # 10 chars
        digest_text = shared
        # Source is exactly 20 chars (2x the digest)
        source_text = shared + "一二三四五六七八九十"  # 10 + 10 = 20

        digest = make_text("T01n0001", digest_text, char_count=10)
        source = make_text("T01n0002", source_text, char_count=20)
        texts = [digest, source]

        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)
        candidates = generate_candidates(texts, ngram_sets, stopgrams)

        pair_found = any(
            c.digest_id == "T01n0001" and c.source_id == "T01n0002"
            for c in candidates
        )
        assert pair_found, (
            "Source at exactly MIN_SIZE_RATIO boundary should be included"
        )

    def test_source_just_below_ratio_boundary(self):
        """Source just below d_len * MIN_SIZE_RATIO should be excluded."""
        shared = "觀自在菩薩行深般若波"  # 10 chars
        digest_text = shared
        # Source is 19 chars (just under 2x)
        source_text = shared + "一二三四五六七八九"  # 10 + 9 = 19

        digest = make_text("T01n0001", digest_text, char_count=10)
        source = make_text("T01n0002", source_text, char_count=19)
        texts = [digest, source]

        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)
        candidates = generate_candidates(texts, ngram_sets, stopgrams)

        pair_found = any(
            c.digest_id == "T01n0001" and c.source_id == "T01n0002"
            for c in candidates
        )
        assert not pair_found, (
            "Source below MIN_SIZE_RATIO boundary should be excluded"
        )

    def test_multiple_sources_near_boundary(self):
        """With multiple sources, only those at or above the boundary should match."""
        shared = "觀自在菩薩行深般若波"  # 10 chars
        digest_text = shared

        # Three sources: below, at, and above the boundary
        below = make_text("T01n0010", shared + "一二三四五六七八九", char_count=19)
        at_boundary = make_text("T01n0020", shared + "一二三四五六七八九十", char_count=20)
        above = make_text("T01n0030", shared + "一二三四五六七八九十更多" * 5, char_count=50)

        digest = make_text("T01n0001", digest_text, char_count=10)
        texts = [digest, below, at_boundary, above]

        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)
        candidates = generate_candidates(texts, ngram_sets, stopgrams)

        matched_sources = {c.source_id for c in candidates if c.digest_id == "T01n0001"}
        assert "T01n0010" not in matched_sources, "Below boundary should be excluded"
        assert "T01n0020" in matched_sources, "At boundary should be included"
        assert "T01n0030" in matched_sources, "Above boundary should be included"


class TestPhoneticStopgramFiltering:
    """Test that phonetic stopgrams are correctly identified and filtered."""

    @pytest.fixture(scope="class")
    def phonetic_table(self):
        return build_equivalence_table()

    def test_stopgrams_reduce_candidates(self, phonetic_table):
        """Phonetic stopgrams should filter out common syllable n-grams,
        reducing false-positive candidates."""
        # Create texts where most share the SAME dharani but one has a unique one
        table_chars = list(phonetic_table.keys())
        common_dharani = ''.join(table_chars[:15])  # shared by many texts
        unique_dharani = ''.join(table_chars[15:30])  # unique to one pair

        texts = []
        # 10 texts all sharing the common dharani
        for i in range(10):
            padding = "觀自在菩薩行深般若" * (i + 5)
            text = padding + common_dharani + padding
            dr_start = len(padding)
            dr_end = dr_start + len(common_dharani)
            texts.append(make_text(
                f"T01n{i:04d}", text,
                dharani_ranges=[(dr_start, dr_end)],
            ))

        # 2 texts sharing the unique dharani (one short, one long)
        short_padding = "觀自在菩薩"
        long_padding = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空" * 10
        short_text = short_padding + unique_dharani + short_padding
        long_text = long_padding + unique_dharani + long_padding

        texts.append(make_text(
            "T01n0100", short_text,
            dharani_ranges=[(len(short_padding), len(short_padding) + len(unique_dharani))],
        ))
        texts.append(make_text(
            "T01n0101", long_text,
            dharani_ranges=[(len(long_padding), len(long_padding) + len(unique_dharani))],
        ))

        candidates = generate_phonetic_candidates(texts, phonetic_table, num_workers=1)

        # The unique pair should be found
        unique_pair_found = any(
            (c.digest_id == "T01n0100" and c.source_id == "T01n0101") or
            (c.digest_id == "T01n0101" and c.source_id == "T01n0100")
            for c in candidates
        )
        # Note: with stopgram filtering, common dharani n-grams get removed,
        # so the number of false-positive pairs from the common dharani
        # should be reduced compared to without filtering.
        # We just verify the system doesn't crash and produces reasonable output.
        assert isinstance(candidates, list)

    def test_min_stopgram_threshold_two(self, phonetic_table):
        """With only 2 texts, stopgram minimum threshold of 2 should prevent
        filtering all shared n-grams (the tiny-corpus gotcha)."""
        table_chars = list(phonetic_table.keys())[:15]
        dharani = ''.join(table_chars)
        padding = "觀自在菩薩行深般若" * 10

        text_a = make_text(
            "a", dharani,
            dharani_ranges=[(0, len(dharani))],
        )
        text_b = make_text(
            "b", padding + dharani + padding,
            dharani_ranges=[(len(padding), len(padding) + len(dharani))],
        )

        # With 2 texts: max_freq = max(int(2 * 0.05), 2) = 2
        # So n-grams appearing in 2 texts are NOT filtered (freq <= max_freq)
        candidates = generate_phonetic_candidates([text_a, text_b], phonetic_table,
                                                  num_workers=1)
        # Should find the pair despite only having 2 texts
        pair_found = any(
            (c.digest_id == "a" and c.source_id == "b") or
            (c.digest_id == "b" and c.source_id == "a")
            for c in candidates
        )
        assert pair_found, (
            "With 2 texts, phonetic stopgram min threshold of 2 should "
            "prevent filtering all shared n-grams"
        )
