"""Tests for phonetic candidate generation (Stage 2b).

Unit tests for canonical_syllable(), find_transliteration_regions(),
text_to_syllable_ngrams(), and generate_phonetic_candidates().
Integration test verifying T250→T901 discovery via phonetic fingerprinting.
"""

import pytest
from pathlib import Path

from digest_detector.phonetic import (
    build_equivalence_table,
    canonical_syllable,
    find_transliteration_regions,
    text_to_syllable_ngrams,
)
from digest_detector.candidates import generate_phonetic_candidates
from digest_detector.models import ExtractedText, TextMetadata


XML_DIR = Path(__file__).resolve().parent.parent / "xml" / "T"


@pytest.fixture(scope="module")
def table():
    return build_equivalence_table()


# ---- Unit tests: canonical_syllable ----

class TestCanonicalSyllable:
    def test_known_char(self, table):
        """揭 maps to 'ga'; canonical = alphabetically first."""
        syl = canonical_syllable("揭", table)
        assert syl is not None
        assert syl == sorted(table["揭"])[0]

    def test_another_char(self, table):
        """帝 should have a canonical syllable."""
        syl = canonical_syllable("帝", table)
        assert syl is not None

    def test_non_table_char(self, table):
        """A character not in the table should return None."""
        assert canonical_syllable("我", table) is None

    def test_consistent(self, table):
        """Calling twice should give the same result."""
        assert canonical_syllable("揭", table) == canonical_syllable("揭", table)


# ---- Unit tests: find_transliteration_regions ----

class TestFindTransliterationRegions:
    def test_xml_dharani_ranges(self, table):
        """Pre-annotated dharani ranges should be included."""
        text = "一二三四五六七八九十" * 10  # 100 chars of non-table text
        dharani_ranges = [(20, 40)]
        regions = find_transliteration_regions(
            text, table, dharani_ranges=dharani_ranges)
        assert (20, 40) in regions

    def test_density_detection(self, table):
        """A run of transliteration chars should be detected."""
        # Build a string that's mostly transliteration characters
        table_chars = list(table.keys())[:30]
        dense_region = ''.join(table_chars)
        # Pad with non-table chars
        padding = "我你他她它" * 10
        text = padding + dense_region + padding
        pad_len = len(padding)

        regions = find_transliteration_regions(text, table)
        # Should find a region covering the dense area
        assert len(regions) > 0
        # At least one region should overlap with the dense chars
        found_overlap = any(
            s < pad_len + len(dense_region) and e > pad_len
            for s, e in regions
        )
        assert found_overlap, (
            f"No region overlaps dense area [{pad_len}:{pad_len + len(dense_region)}], "
            f"got regions: {regions}"
        )

    def test_no_regions_in_prose(self, table):
        """Regular prose should produce no or very short regions."""
        # Text with mostly non-table characters (avoid chars like 三/色/是
        # which happen to appear in the DDB transliteration table)
        prose = "觀自在菩薩行深般若時照見五蘊皆空度一切苦厄舍利弗不異空不異受想行識亦復如是"
        regions = find_transliteration_regions(prose, table)
        total_len = sum(e - s for s, e in regions)
        # Any density-detected regions should cover less than half the prose
        assert total_len < len(prose) * 0.5, (
            f"Density detection found too much in prose: {total_len}/{len(prose)} chars"
        )

    def test_merge_overlapping(self, table):
        """Overlapping dharani ranges should be merged."""
        text = "x" * 100
        dharani_ranges = [(10, 30), (25, 50), (60, 80)]
        regions = find_transliteration_regions(
            text, table, dharani_ranges=dharani_ranges)
        # First two should merge
        assert (10, 50) in regions
        assert (60, 80) in regions

    def test_empty_text(self, table):
        """Empty text should return no regions."""
        assert find_transliteration_regions("", table) == []


# ---- Unit tests: text_to_syllable_ngrams ----

class TestTextToSyllableNgrams:
    def test_basic_ngrams(self, table):
        """Should produce n-gram tuples from a transliteration region."""
        # Use known transliteration chars
        chars = [ch for ch in table.keys()][:10]
        text = ''.join(chars)
        regions = [(0, len(text))]

        ngrams = text_to_syllable_ngrams(text, regions, table, n=3)
        assert len(ngrams) > 0
        # Each n-gram is a (string, position) tuple
        for ngram_str, pos in ngrams:
            assert "-" in ngram_str or len(ngram_str) > 0
            assert 0 <= pos < len(text)

    def test_ngram_count(self, table):
        """Number of n-grams should be len(syllables) - n + 1."""
        # Use 10 chars all in the table
        chars = list(table.keys())[:10]
        text = ''.join(chars)
        regions = [(0, len(text))]

        ngrams = text_to_syllable_ngrams(text, regions, table, n=3)
        # All 10 chars are in table → 10 syllables → 10-3+1 = 8 n-grams
        assert len(ngrams) == 8

    def test_gap_chars_excluded(self, table):
        """Non-table chars should not contribute syllables to n-grams."""
        chars = list(table.keys())[:5]
        text = chars[0] + "我" + chars[1] + chars[2] + chars[3] + chars[4]
        regions = [(0, len(text))]

        ngrams = text_to_syllable_ngrams(text, regions, table, n=3)
        # 5 table chars → 5 syllables → 5-3+1 = 3 n-grams (我 is skipped)
        assert len(ngrams) == 3

    def test_empty_regions(self, table):
        """No regions should produce no n-grams."""
        ngrams = text_to_syllable_ngrams("test", [], table, n=3)
        assert ngrams == []


# ---- Unit tests: generate_phonetic_candidates ----

class TestGeneratePhoneticCandidates:
    def _make_text(self, text_id, full_text, dharani_ranges=None, char_count=None):
        """Helper to create an ExtractedText for testing."""
        if char_count is None:
            char_count = len(full_text)
        return ExtractedText(
            text_id=text_id,
            full_text=full_text,
            metadata=TextMetadata(
                text_id=text_id,
                title="",
                author="",
                extent_juan=1,
                char_count=char_count,
                file_count=1,
            ),
            dharani_ranges=dharani_ranges or [],
        )

    def test_synthetic_phonetic_pair(self, table):
        """Two texts with different transliterations of the same dharani → candidate pair."""
        # T250 dharani chars (Kumārajīva): 竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵
        # T251 dharani chars (Xuanzang):    揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶
        dharani_a = "竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵"
        dharani_b = "揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶"

        # Create a short "digest" with the dharani and a longer "source"
        padding = "觀自在色不異空空不異色色即是空空即是色受想行識亦復如是" * 5
        digest_text = dharani_a
        source_text = padding + dharani_b + padding

        digest = self._make_text("digest", digest_text,
                                 dharani_ranges=[(0, len(dharani_a))])
        source = self._make_text("source", source_text,
                                 dharani_ranges=[(len(padding), len(padding) + len(dharani_b))])

        candidates = generate_phonetic_candidates([digest, source], table)
        pair_ids = {(c.digest_id, c.source_id) for c in candidates}
        assert ("digest", "source") in pair_ids, (
            f"Expected ('digest', 'source') in candidates, got {pair_ids}"
        )

    def test_prose_no_candidates(self, table):
        """Regular Chinese prose should not produce phonetic candidates."""
        prose_a = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"
        prose_b = ("舍利子色不異空空不異色色即是空空即是色受想行識亦復如是"
                   "舍利子是諸法空相不生不滅不垢不淨不增不減是故空中無色無受想行識")

        text_a = self._make_text("a", prose_a)
        text_b = self._make_text("b", prose_b)

        candidates = generate_phonetic_candidates([text_a, text_b], table)
        assert len(candidates) == 0

    def test_from_phonetic_flag(self, table):
        """Phonetic candidates should have from_phonetic=True."""
        dharani = "竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵"
        dharani2 = "揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶"
        padding = "我你他她它一二三四五六七八九十" * 10

        digest = self._make_text("d", dharani,
                                 dharani_ranges=[(0, len(dharani))])
        source = self._make_text("s", padding + dharani2 + padding,
                                 dharani_ranges=[(len(padding), len(padding) + len(dharani2))])

        candidates = generate_phonetic_candidates([digest, source], table)
        for c in candidates:
            assert c.from_phonetic is True


# ---- Integration test: T250 → T901 ----

class TestPhoneticCandidateIntegration:
    """Integration test extracting real texts and running phonetic candidate generation."""

    @pytest.fixture(scope="class")
    def t250(self):
        from tests.test_known_pairs import _extract_full_text
        text = _extract_full_text("T08n0250", XML_DIR)
        if text is None:
            pytest.skip("T250 XML file not found")
        return text

    @pytest.fixture(scope="class")
    def t901(self):
        from tests.test_known_pairs import _extract_full_text
        text = _extract_full_text("T18n0901", XML_DIR)
        if text is None:
            pytest.skip("T901 XML files not found")
        return text

    def test_t250_has_dharani_ranges(self, t250):
        """T250 should have dharani ranges from XML markup."""
        assert len(t250.dharani_ranges) > 0, (
            "T250 should have XML-annotated dharani ranges"
        )

    def test_t901_has_dharani_ranges(self, t901):
        """T901 (dharani collection) should have dharani ranges."""
        assert len(t901.dharani_ranges) > 0, (
            "T901 should have XML-annotated dharani ranges"
        )

    def test_t250_t901_phonetic_candidate(self, t250, t901, table):
        """Phonetic candidate generation should discover T250 → T901 pair."""
        candidates = generate_phonetic_candidates([t250, t901], table)
        pair_ids = {(c.digest_id, c.source_id) for c in candidates}
        assert (t250.text_id, t901.text_id) in pair_ids, (
            f"Expected ({t250.text_id}, {t901.text_id}) in phonetic candidates. "
            f"Got {len(candidates)} candidates: {pair_ids}"
        )

    def test_t250_t901_containment_score(self, t250, t901, table):
        """Check the actual phonetic containment for T250↔T901.

        Measured score is ~0.286 — just above the MIN_PHONETIC_CONTAINMENT
        threshold of 0.25.  Assert it stays above 0.25 so we know our
        threshold is safe.
        """
        candidates = generate_phonetic_candidates([t250, t901], table)
        pair = [c for c in candidates
                if c.digest_id == t250.text_id and c.source_id == t901.text_id]
        assert pair, "T250↔T901 pair not found"
        score = pair[0].containment_score
        print(f"\nT250↔T901 phonetic containment: {score:.4f}")
        assert score >= 0.25, f"Score {score:.4f} too low for 0.25 threshold"


class TestPhoneticCandidatesParallel:
    """Verify serial and parallel paths produce identical results."""

    def _make_text(self, text_id, full_text, dharani_ranges=None, char_count=None):
        if char_count is None:
            char_count = len(full_text)
        return ExtractedText(
            text_id=text_id,
            full_text=full_text,
            metadata=TextMetadata(
                text_id=text_id, title="", author="",
                extent_juan=1, char_count=char_count, file_count=1,
            ),
            dharani_ranges=dharani_ranges or [],
        )

    def test_parallel_equivalence(self, table):
        """generate_phonetic_candidates with num_workers=1 and 2 should match."""
        # Build enough texts with dharani regions to trigger parallel path
        dharani_variants = [
            "竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵",
            "揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶",
            "竭諦竭諦波羅竭諦波羅僧竭諦菩提薩婆訶",
            "揭諦揭諦波羅揭諦波羅僧揭諦菩提薩婆訶",
        ]
        padding_base = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"

        texts = []
        for i, dharani in enumerate(dharani_variants):
            # Short "digest" texts
            texts.append(self._make_text(
                f"short{i}", dharani,
                dharani_ranges=[(0, len(dharani))],
            ))
            # Longer "source" texts with dharani embedded
            padding = padding_base * (5 + i * 2)
            full = padding + dharani + padding
            dr_start = len(padding)
            texts.append(self._make_text(
                f"long{i}", full,
                dharani_ranges=[(dr_start, dr_start + len(dharani))],
            ))

        serial = generate_phonetic_candidates(texts, table, num_workers=1)
        parallel = generate_phonetic_candidates(texts, table, num_workers=2)

        serial_pairs = {(c.digest_id, c.source_id) for c in serial}
        parallel_pairs = {(c.digest_id, c.source_id) for c in parallel}
        assert serial_pairs == parallel_pairs, (
            f"Serial found {len(serial_pairs)} pairs, parallel found {len(parallel_pairs)}. "
            f"Serial-only: {serial_pairs - parallel_pairs}, "
            f"Parallel-only: {parallel_pairs - serial_pairs}"
        )

        serial_scores = {(c.digest_id, c.source_id): c.containment_score for c in serial}
        parallel_scores = {(c.digest_id, c.source_id): c.containment_score for c in parallel}
        for key in serial_scores:
            assert abs(serial_scores[key] - parallel_scores[key]) < 1e-9, (
                f"Score mismatch for {key}: serial={serial_scores[key]}, "
                f"parallel={parallel_scores[key]}"
            )
