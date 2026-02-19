"""Integration tests for phonetic transliteration detection.

Tests the full phonetic alignment pipeline on actual Taisho texts:
- T250 (Kumārajīva Heart Sutra) dharani: 竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵
- T251 (Xuanzang Heart Sutra) dharani: 揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶
- T901 (Dhāraṇī Collection) contains: 揭帝揭帝波羅揭帝波羅僧揭帝菩提莎訶
- T223 (Kumārajīva Prajñāpāramitā) — T250's source text
"""

import pytest
from pathlib import Path

from digest_detector.align import align_pair, _phonetic_rescan, _get_phonetic_table
from digest_detector.phonetic import (
    build_equivalence_table,
    are_phonetically_equivalent,
)
from digest_detector.score import classify_relationship
from digest_detector.models import AlignmentSegment


XML_DIR = Path(__file__).resolve().parent.parent / "xml" / "T"


def _extract_full_text(text_id):
    """Reuse the extraction helper from test_known_pairs."""
    from tests.test_known_pairs import _extract_full_text as extract
    return extract(text_id, XML_DIR)


@pytest.fixture(scope="module")
def phonetic_table():
    return build_equivalence_table()


@pytest.fixture(scope="module")
def t250():
    text = _extract_full_text("T08n0250")
    if text is None:
        pytest.skip("T250 XML file not found")
    return text


@pytest.fixture(scope="module")
def t251():
    text = _extract_full_text("T08n0251")
    if text is None:
        pytest.skip("T251 XML file not found")
    return text


@pytest.fixture(scope="module")
def t901():
    text = _extract_full_text("T18n0901")
    if text is None:
        pytest.skip("T901 XML files not found")
    return text


@pytest.fixture(scope="module")
def t223():
    text = _extract_full_text("T08n0223")
    if text is None:
        pytest.skip("T223 XML files not found")
    return text


class TestPhoneticDharaniDetection:
    """Test phonetic matching of dharani passages across texts."""

    def test_t250_dharani_in_t251(self, phonetic_table):
        """T250's dharani (竭帝竭帝...) should phonetically match T251's (揭帝揭帝...).

        These are the same Sanskrit mantra (gate gate paragate parasamgate
        bodhi svaha) rendered with different Chinese characters.
        """
        # T250 uses: 竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵
        # T251 uses: 揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶
        t250_dharani = "竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵"
        t251_dharani = "揭帝揭帝般羅揭帝般羅僧揭帝菩提莎婆訶"

        # Verify char-by-char phonetic equivalence for overlapping portion
        overlap = min(len(t250_dharani), len(t251_dharani))
        equiv_count = sum(
            1 for i in range(overlap)
            if are_phonetically_equivalent(
                t250_dharani[i], t251_dharani[i], phonetic_table)
        )
        # Most chars should be phonetically equivalent
        assert equiv_count >= overlap * 0.6, (
            f"Only {equiv_count}/{overlap} chars are phonetically equivalent"
        )

    def test_t250_vs_t901_dharani_phonetic_match(self):
        """Align T250's dharani against T901's — should detect phonetic match."""
        # T250: 竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵
        # T901: 揭帝揭帝波羅揭帝波羅僧揭帝菩提莎訶
        t250_dharani = "竭帝竭帝波羅竭帝波羅僧竭帝菩提僧莎呵"
        t901_dharani = "其他文字揭帝揭帝波羅揭帝波羅僧揭帝菩提莎訶更多文字"

        result = align_pair(t250_dharani, t901_dharani, "T250", "T901")

        # Should have non-trivial coverage (via phonetic + exact matches)
        assert result.coverage > 0.5, (
            f"Coverage {result.coverage:.1%} too low for dharani match"
        )

        # Should contain at least one phonetic segment
        phonetic_segs = [s for s in result.segments
                         if s.match_type == "phonetic"]
        assert len(phonetic_segs) > 0, "No phonetic segments found"

        # Verify phonetic mapping contains expected char→syllable→char triples
        for seg in phonetic_segs:
            assert seg.phonetic_mapping, "Phonetic segment missing mapping"
            for d_ch, syl, s_ch in seg.phonetic_mapping:
                if d_ch != s_ch:
                    # Different chars should share a syllable
                    assert syl != "?", (
                        f"No shared syllable for {d_ch}↔{s_ch}"
                    )

    def test_t250_vs_t901_full_text(self, t250, t901):
        """Align full T250 against full T901 — dharani should be detected."""
        result = align_pair(
            t250.full_text, t901.full_text,
            "T08n0250", "T18n0901",
        )

        # Check that phonetic segments exist
        phonetic_segs = [s for s in result.segments
                         if s.match_type == "phonetic"]
        # The dharani portion should trigger phonetic matching
        # even though the rest of T250 is unrelated to T901
        phonetic_chars = sum(s.digest_end - s.digest_start
                             for s in phonetic_segs)
        assert phonetic_chars > 0, (
            f"No phonetic matches found in T250→T901 alignment. "
            f"Coverage: {result.coverage:.1%}"
        )

    def test_segments_cover_full_digest(self, t250, t901):
        """Segments should cover the entire digest without gaps."""
        result = align_pair(
            t250.full_text, t901.full_text,
            "T08n0250", "T18n0901",
        )

        total = sum(s.digest_end - s.digest_start for s in result.segments)
        assert total == len(t250.full_text)

        for i in range(len(result.segments) - 1):
            assert result.segments[i].digest_end == result.segments[i + 1].digest_start


class TestPhoneticFalsePositives:
    """Ensure phonetic matching doesn't fire on regular Chinese prose."""

    def test_no_phonetic_on_prose(self, phonetic_table):
        """Regular Chinese prose should NOT produce phonetic matches.

        Characters like 羅 appear in the transliteration table but require
        consecutive seed matches to trigger, preventing false positives
        on normal text.
        """
        # Regular prose containing some chars that happen to be in the table
        digest = "般若波羅蜜多心經觀自在菩薩行深般若"
        source = "摩訶般若波羅蜜經舍利弗色不異空空不異色"

        result = align_pair(digest, source, "d", "s")

        phonetic_segs = [s for s in result.segments
                         if s.match_type == "phonetic"]
        # Any phonetic segments should be short (accidental overlap from
        # transliteration chars appearing in regular prose)
        phonetic_chars = sum(s.digest_end - s.digest_start
                             for s in phonetic_segs)
        # Allow minor accidental matches but not large ones
        assert phonetic_chars < len(digest) * 0.3, (
            f"Too many phonetic chars ({phonetic_chars}) in prose — "
            f"likely false positives"
        )

    def test_exact_match_preferred_over_phonetic(self):
        """When text matches exactly, it should be classified as exact, not phonetic."""
        text = "揭帝揭帝波羅揭帝波羅僧揭帝菩提莎婆訶"
        result = align_pair(text, text, "d", "s")

        # All matched segments should be exact (or fuzzy), NOT phonetic
        for seg in result.segments:
            if seg.match_type != "novel":
                assert seg.match_type in ("exact", "fuzzy"), (
                    f"Identical text should be exact, got {seg.match_type}"
                )


class TestPhoneticMapping:
    """Test that phonetic_mapping field is correctly populated."""

    def test_mapping_records_char_triples(self):
        """Phonetic segments should record (digest_char, syllable, source_char)."""
        digest = "竭帝竭帝波羅竭帝"
        source = "揭諦揭諦波羅揭諦"

        result = align_pair(digest, source, "d", "s")

        phonetic_segs = [s for s in result.segments
                         if s.match_type == "phonetic"]
        assert len(phonetic_segs) > 0

        for seg in phonetic_segs:
            assert len(seg.phonetic_mapping) == len(seg.digest_text)
            for d_ch, syl, s_ch in seg.phonetic_mapping:
                assert len(d_ch) == 1
                assert len(s_ch) == 1
                assert isinstance(syl, str)

    def test_mapping_not_on_exact_segments(self):
        """Exact/fuzzy segments should have empty phonetic_mapping."""
        text = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空"
        result = align_pair(text, text, "d", "s")

        for seg in result.segments:
            if seg.match_type in ("exact", "fuzzy"):
                assert seg.phonetic_mapping == []


class TestPhoneticWithExactOverlap:
    """Test texts that have both exact and phonetic overlap."""

    def test_mixed_exact_and_phonetic(self):
        """A text with both exact Chinese overlap and phonetic dharani overlap."""
        # First part: exact Chinese match; second part: phonetic dharani
        digest = "觀自在菩薩行深般若波羅蜜多竭帝竭帝波羅竭帝"
        source = "觀自在菩薩行深般若波羅蜜多揭諦揭諦波羅揭諦"

        result = align_pair(digest, source, "d", "s")

        exact_segs = [s for s in result.segments if s.match_type == "exact"]
        phonetic_segs = [s for s in result.segments if s.match_type == "phonetic"]

        # Should have both types
        assert len(exact_segs) > 0, "Should have exact matches"
        assert len(phonetic_segs) > 0, "Should have phonetic matches"

        # Total coverage should be high
        assert result.coverage > 0.8
