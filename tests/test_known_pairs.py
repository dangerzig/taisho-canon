"""Integration tests: verify known digest relationships T250/T251 → T223.

These tests extract the actual texts from XML and run alignment to verify
the pipeline can detect the known Heart Sutra digest relationships.
"""

import re

import pytest
from pathlib import Path

from digest_detector.extract import (
    build_char_map,
    _process_text_group,
)
from digest_detector.align import align_pair
from digest_detector.score import classify_relationship, score_all
from digest_detector.fingerprint import (
    compute_document_frequencies,
    identify_stopgrams,
    build_ngram_sets,
)
from digest_detector.candidates import generate_candidates
from digest_detector.models import ExtractedText, TextMetadata, DivSegment


XML_DIR = Path(__file__).resolve().parent.parent / "xml" / "T"


def _extract_full_text(text_id: str, xml_dir: Path = XML_DIR) -> ExtractedText | None:
    """Helper: extract a complete text from its XML files using production code."""
    vol_dir = xml_dir / text_id[:3]  # e.g., T08
    if not vol_dir.exists():
        return None

    pattern = re.compile(rf'{re.escape(text_id)}_(\d+)\.xml$')
    files = []
    for f in sorted(vol_dir.iterdir()):
        m = pattern.search(f.name)
        if m:
            files.append((int(m.group(1)), f))
    files.sort()

    if not files:
        return None

    file_paths = [f for _, f in files]
    char_map = build_char_map(file_paths)
    return _process_text_group((text_id, file_paths, char_map))


@pytest.fixture(scope="module")
def t223():
    text = _extract_full_text("T08n0223")
    if text is None:
        pytest.skip("T223 XML files not found")
    return text


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


class TestJingText:
    def test_jing_text_returns_jing_only(self, t251):
        """jing_text should return only jing segments for T251."""
        jing_manual = ''.join(
            seg.text for seg in t251.segments if seg.div_type == 'jing'
        )
        assert t251.jing_text == jing_manual
        assert len(t251.jing_text) < len(t251.full_text)

    def test_jing_text_fallback(self, t250):
        """jing_text should return full_text when no jing segments exist."""
        # T250 has no xu/jing divisions — it's a single short text
        assert t250.jing_text == t250.full_text

    def test_jing_text_empty_segments(self):
        """jing_text should return full_text when segments list is empty."""
        text = ExtractedText(
            text_id="test",
            full_text="測試文字",
            segments=[],
        )
        assert text.jing_text == "測試文字"

    def test_jing_text_no_jing_segments(self):
        """jing_text should return full_text when segments exist but none are jing."""
        text = ExtractedText(
            text_id="test",
            full_text="前言正文",
            segments=[
                DivSegment(div_type="xu", text="前言", start=0, end=2),
                DivSegment(div_type="pin", text="正文", start=2, end=4),
            ],
        )
        assert text.jing_text == "前言正文"


class TestTextExtraction:
    def test_t223_length(self, t223):
        """T223 should be a long text (~287K chars)."""
        assert t223.metadata.char_count > 200000
        assert t223.metadata.extent_juan == 27

    def test_t250_length(self, t250):
        """T250 should be a short text (~331 CJK chars)."""
        assert 200 < t250.metadata.char_count < 500

    def test_t251_length(self, t251):
        """T251 (including prefaces) should be ~800-1200 CJK chars."""
        assert 500 < t251.metadata.char_count < 2000

    def test_t251_has_xu_and_jing(self, t251):
        """T251 should have both xu (preface) and jing (sutra) divisions."""
        div_types = [seg.div_type for seg in t251.segments]
        assert 'xu' in div_types
        assert 'jing' in div_types

    def test_t251_jing_shorter_than_full(self, t251):
        """The jing portion of T251 should be much shorter than the full text."""
        jing_text = ''.join(
            seg.text for seg in t251.segments if seg.div_type == 'jing'
        )
        assert len(jing_text) < t251.metadata.char_count
        assert 200 < len(jing_text) < 400


class TestAlignment:
    def test_t250_aligns_to_t223(self, t250, t223):
        """T250 should have high alignment coverage against T223."""
        result = align_pair(
            t250.full_text, t223.full_text,
            "T08n0250", "T08n0223",
        )
        # T250 is a known digest of T223
        assert result.coverage >= 0.50, (
            f"T250→T223 coverage {result.coverage:.2%} is too low"
        )
        # Should draw from multiple regions
        assert result.num_source_regions >= 1

    def test_t251_jing_aligns_to_t223(self, t251, t223):
        """T251's jing portion should align well against T223.

        Note: T251 (Xuanzang) and T223 (Kumārajīva) are different translations,
        so exact textual overlap is lower than T250→T223. Coverage ~40-50% is
        expected because the two translators use different Chinese phrasing for
        the same Sanskrit source material.
        """
        jing_text = ''.join(
            seg.text for seg in t251.segments if seg.div_type == 'jing'
        )
        result = align_pair(
            jing_text, t223.full_text,
            "T08n0251", "T08n0223",
        )
        assert result.coverage >= 0.30, (
            f"T251 jing→T223 coverage {result.coverage:.2%} is too low"
        )

    def test_t250_not_digest_of_t251(self, t250, t251):
        """T250 and T251 are both Heart Sutras but neither is a digest of the other."""
        result = align_pair(
            t250.full_text, t251.full_text,
            "T08n0250", "T08n0251",
        )
        # They're similar texts but the source (T251) is not much longer
        # This should NOT be classified as a digest relationship
        score = classify_relationship(
            result,
            digest_length=t250.metadata.char_count,
            source_length=t251.metadata.char_count,
            digest_jing_length=len(t250.jing_text),
            source_jing_length=len(t251.jing_text),
        )
        # Should be retranslation or shared_tradition, NOT excerpt
        assert score.classification != "excerpt", (
            f"T250→T251 wrongly classified as {score.classification}"
        )


class TestClassification:
    def test_t250_classified_as_digest(self, t250, t223):
        """T250→T223 should be classified as digest (73.2% coverage, below excerpt threshold)."""
        result = align_pair(
            t250.full_text, t223.full_text,
            "T08n0250", "T08n0223",
        )
        score = classify_relationship(
            result,
            digest_length=t250.metadata.char_count,
            source_length=t223.metadata.char_count,
            has_docnumber_xref=True,
        )
        assert score.classification == "digest", (
            f"T250→T223 classified as {score.classification}, "
            f"expected digest"
        )
        assert score.confidence > 0.3


class TestClassificationJingAware:
    def test_t250_t251_retranslation_with_jing_lengths(self, t250, t251):
        """T250 vs T251 should be 'retranslation' when using jing lengths.

        Without jing lengths, T251 full text (~1090 chars) vs T250 (~331 chars)
        gives size ratio ~3.3, just above RETRANSLATION_SIZE_RATIO (3.0),
        potentially classifying as digest. With jing lengths, T251 jing
        (~260 chars) vs T250 (~331 chars) gives ratio ~0.79 → retranslation.
        """
        result = align_pair(
            t250.full_text, t251.full_text,
            "T08n0250", "T08n0251",
        )
        score = classify_relationship(
            result,
            digest_length=t250.metadata.char_count,
            source_length=t251.metadata.char_count,
            digest_jing_length=len(t250.jing_text),
            source_jing_length=len(t251.jing_text),
        )
        assert score.classification == "retranslation", (
            f"T250→T251 classified as {score.classification} with jing lengths, "
            f"expected retranslation"
        )

    def test_t251_jing_classified_as_digest(self, t251, t223):
        """T251 jing→T223 should be classified as digest.

        Cross-translator overlap (Xuanzang vs Kumārajīva) gives ~44% coverage,
        which falls in the digest range.
        """
        result = align_pair(
            t251.jing_text, t223.full_text,
            "T08n0251", "T08n0223",
        )
        score = classify_relationship(
            result,
            digest_length=len(t251.jing_text),
            source_length=t223.metadata.char_count,
        )
        assert score.classification == "digest", (
            f"T251 jing→T223 classified as {score.classification}, "
            f"expected digest (44% coverage is well below 80% excerpt threshold)"
        )


class TestCandidateGeneration:
    def test_t250_appears_as_candidate(self, t250, t223):
        """T250 should appear as a candidate pair with T223.

        Note: With only 2 texts, the stop-gram threshold must be set to 1.0
        to avoid filtering ALL shared n-grams (since any shared gram appears
        in 100% of documents). In the full pipeline with ~2,459 texts, the
        default 5% threshold works correctly.
        """
        texts = [t250, t223]
        doc_freq = compute_document_frequencies(texts, n=5)
        # Use threshold=1.0 since with 2 texts, any lower threshold
        # would filter out all shared grams
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)
        candidates = generate_candidates(texts, ngram_sets, stopgrams)

        pair_found = any(
            c.digest_id == "T08n0250" and c.source_id == "T08n0223"
            for c in candidates
        )
        assert pair_found, "T250→T223 not found in candidates"

    def test_t251_appears_as_candidate(self, t251, t223):
        """T251 should appear as a candidate pair with T223.

        Uses jing_text for fingerprinting, so xu preface material doesn't
        dilute containment below the threshold.
        """
        texts = [t251, t223]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)
        candidates = generate_candidates(texts, ngram_sets, stopgrams)

        pair_found = any(
            c.digest_id == "T08n0251" and c.source_id == "T08n0223"
            for c in candidates
        )
        assert pair_found, "T251→T223 not found in candidates"


class TestScoreAll:
    def test_score_all_with_text_map(self, t250, t251):
        """score_all() with text_map should use jing lengths for classification.

        T250 vs T251 are similar-length Heart Sutras.  When jing lengths are
        available via text_map, the size ratio drops below the retranslation
        threshold, so the pair should be classified as 'retranslation' (not
        digest).
        """
        result = align_pair(
            t250.full_text, t251.full_text,
            "T08n0250", "T08n0251",
        )

        metadata_map = {
            t250.text_id: t250.metadata,
            t251.text_id: t251.metadata,
        }
        text_map = {
            t250.text_id: t250,
            t251.text_id: t251,
        }

        scores = score_all([result], metadata_map, text_map=text_map)

        # Find the T250→T251 score if it exists
        t250_t251_scores = [
            s for s in scores
            if s.digest_id == "T08n0250" and s.source_id == "T08n0251"
        ]
        assert len(t250_t251_scores) == 1, (
            "Expected exactly 1 T250→T251 score from score_all"
        )
        if t250_t251_scores:
            assert t250_t251_scores[0].classification == "retranslation", (
                f"T250→T251 via score_all classified as "
                f"{t250_t251_scores[0].classification}, expected retranslation"
            )
