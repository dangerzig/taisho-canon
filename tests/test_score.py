"""Tests for Stage 4: Scoring and classification."""

import pytest

from digest_detector.score import (
    classify_relationship,
    _compute_confidence,
    _avg_segment_length,
    _longest_segment,
    score_all,
    detect_multi_source_digests,
)
from digest_detector.models import (
    AlignmentResult, AlignmentSegment, DigestScore, TextMetadata,
    ExtractedText, MultiSourceDigest,
)


def _make_alignment(
    digest_id: str = "d",
    source_id: str = "s",
    coverage: float = 0.0,
    novel_fraction: float = 1.0,
    source_span: float = 0.0,
    num_source_regions: int = 0,
    segments: list = None,
) -> AlignmentResult:
    """Helper to build an AlignmentResult with defaults."""
    return AlignmentResult(
        digest_id=digest_id,
        source_id=source_id,
        segments=segments or [],
        coverage=coverage,
        novel_fraction=novel_fraction,
        source_span=source_span,
        num_source_regions=num_source_regions,
    )


def _make_segment(
    d_start: int, d_end: int,
    s_start: int = 0, s_end: int = 0,
    match_type: str = "exact",
) -> AlignmentSegment:
    """Helper to build an AlignmentSegment."""
    return AlignmentSegment(
        digest_start=d_start, digest_end=d_end,
        source_start=s_start, source_end=s_end,
        match_type=match_type,
        digest_text="x" * (d_end - d_start),
        source_text="x" * (s_end - s_start) if match_type != "novel" else "",
    )


def _make_metadata(text_id: str, char_count: int) -> TextMetadata:
    return TextMetadata(
        text_id=text_id, title='', author='',
        extent_juan=1, char_count=char_count,
        file_count=1,
    )


class TestAvgSegmentLength:
    def test_basic(self):
        segs = [
            _make_segment(0, 10, 0, 10),
            _make_segment(15, 25, 50, 60),
        ]
        assert _avg_segment_length(segs) == 10.0

    def test_ignores_novel(self):
        segs = [
            _make_segment(0, 10, 0, 10),
            _make_segment(10, 20, match_type="novel"),
            _make_segment(20, 30, 100, 110),
        ]
        assert _avg_segment_length(segs) == 10.0

    def test_empty(self):
        assert _avg_segment_length([]) == 0.0

    def test_all_novel(self):
        segs = [_make_segment(0, 10, match_type="novel")]
        assert _avg_segment_length(segs) == 0.0


class TestLongestSegment:
    def test_basic(self):
        segs = [
            _make_segment(0, 5, 0, 5),
            _make_segment(10, 30, 50, 70),
        ]
        assert _longest_segment(segs) == 20

    def test_empty(self):
        assert _longest_segment([]) == 0


class TestClassifyRelationship:
    def _make_classified(self, coverage, avg_seg_len, digest_len=300,
                         source_len=50000, num_regions=1, **kwargs):
        """Build an alignment and classify it."""
        # Build segments to achieve desired avg length and coverage
        seg_count = max(1, int(coverage * digest_len / max(avg_seg_len, 1)))
        seg_len = int(avg_seg_len)
        segments = []
        d_pos = 0
        for i in range(seg_count):
            segments.append(_make_segment(d_pos, d_pos + seg_len, i * 100, i * 100 + seg_len))
            d_pos += seg_len + 2  # small gap

        alignment = _make_alignment(
            coverage=coverage,
            novel_fraction=1.0 - coverage,
            num_source_regions=num_regions,
            segments=segments,
        )
        return classify_relationship(alignment, digest_len, source_len, **kwargs)

    def test_excerpt(self):
        score = self._make_classified(coverage=0.85, avg_seg_len=20)
        assert score.classification == "excerpt"

    def test_digest(self):
        score = self._make_classified(coverage=0.50, avg_seg_len=15)
        assert score.classification == "digest"

    def test_commentary(self):
        """Low avg segment length with moderate coverage → commentary."""
        score = self._make_classified(coverage=0.40, avg_seg_len=5)
        assert score.classification == "commentary"

    def test_shared_tradition(self):
        score = self._make_classified(coverage=0.15, avg_seg_len=8)
        assert score.classification == "shared_tradition"

    def test_no_relationship(self):
        score = self._make_classified(coverage=0.05, avg_seg_len=3)
        assert score.classification == "no_relationship"

    def test_retranslation(self):
        """Similar-length texts with significant overlap → retranslation."""
        score = self._make_classified(
            coverage=0.50, avg_seg_len=15,
            digest_len=300, source_len=400,  # ratio < 3.0
        )
        assert score.classification == "retranslation"

    def test_retranslation_with_jing_lengths(self):
        """When jing lengths are provided, size ratio uses them."""
        # Full text ratio is 50000/300 = 166x (not retranslation)
        # But jing ratio is 400/300 = 1.3x (retranslation)
        score = self._make_classified(
            coverage=0.50, avg_seg_len=15,
            digest_len=300, source_len=50000,
            digest_jing_length=300, source_jing_length=400,
        )
        assert score.classification == "retranslation"

    def test_excerpt_blocked_by_low_avg_seg_len(self):
        """High coverage but low avg segment length → digest, not excerpt."""
        score = self._make_classified(coverage=0.85, avg_seg_len=12)
        assert score.classification == "digest"

    def test_docnumber_xref_boosts_confidence(self):
        score_without = self._make_classified(coverage=0.50, avg_seg_len=15)
        score_with = self._make_classified(
            coverage=0.50, avg_seg_len=15, has_docnumber_xref=True,
        )
        assert score_with.confidence > score_without.confidence


class TestComputeConfidence:
    def test_all_zeros(self):
        conf = _compute_confidence(
            coverage=0.0, longest_seg=0, num_regions=0,
            size_ratio=1.0, has_docnumber_xref=False,
            avg_seg_len=0.0, digest_length=100,
        )
        assert conf == 0.0

    def test_perfect_scores(self):
        conf = _compute_confidence(
            coverage=1.0, longest_seg=100, num_regions=5,
            size_ratio=1024.0, has_docnumber_xref=True,
            avg_seg_len=20.0, digest_length=100,
        )
        assert conf == 1.0

    def test_weights_sum_to_one(self):
        """Verify all components at max produce exactly 1.0."""
        from digest_detector import config
        total = (config.WEIGHT_CONTAINMENT +
                 config.WEIGHT_LONGEST_SEGMENT +
                 config.WEIGHT_NUM_REGIONS +
                 config.WEIGHT_LENGTH_ASYMMETRY +
                 config.WEIGHT_DOCNUMBER_XREF +
                 config.WEIGHT_AVG_SEGMENT_LEN)
        assert abs(total - 1.0) < 1e-10

    def test_docnumber_component(self):
        """DocNumber xref should contribute WEIGHT_DOCNUMBER_XREF to confidence."""
        base = _compute_confidence(
            coverage=0.5, longest_seg=50, num_regions=1,
            size_ratio=10.0, has_docnumber_xref=False,
            avg_seg_len=10.0, digest_length=100,
        )
        with_xref = _compute_confidence(
            coverage=0.5, longest_seg=50, num_regions=1,
            size_ratio=10.0, has_docnumber_xref=True,
            avg_seg_len=10.0, digest_length=100,
        )
        from digest_detector import config
        diff = with_xref - base
        assert abs(diff - config.WEIGHT_DOCNUMBER_XREF) < 1e-10


class TestScoreAll:
    def test_filters_no_relationship(self):
        """score_all should exclude 'no_relationship' from results."""
        alignment = _make_alignment(
            digest_id="d", source_id="s",
            coverage=0.01, novel_fraction=0.99,
            segments=[_make_segment(0, 1, 0, 1)],
        )
        meta_map = {
            "d": _make_metadata("d", 100),
            "s": _make_metadata("s", 10000),
        }
        scores = score_all([alignment], meta_map)
        assert len(scores) == 0

    def test_includes_valid_relationships(self):
        segments = [
            _make_segment(0, 80, 0, 80),
            _make_segment(80, 100, match_type="novel"),
        ]
        alignment = _make_alignment(
            digest_id="d", source_id="s",
            coverage=0.80, novel_fraction=0.20,
            num_source_regions=1,
            segments=segments,
        )
        meta_map = {
            "d": _make_metadata("d", 100),
            "s": _make_metadata("s", 50000),
        }
        scores = score_all([alignment], meta_map)
        assert len(scores) == 1
        assert scores[0].classification == "excerpt"

    def test_skips_missing_metadata(self):
        alignment = _make_alignment(
            digest_id="d", source_id="s", coverage=0.80,
            segments=[_make_segment(0, 80, 0, 80)],
        )
        # Only digest metadata, no source metadata
        meta_map = {"d": _make_metadata("d", 100)}
        scores = score_all([alignment], meta_map)
        assert len(scores) == 0

    def test_sorted_by_confidence_descending(self):
        segs_high = [_make_segment(0, 80, 0, 80)]
        segs_low = [_make_segment(0, 30, 0, 30)]
        alignments = [
            _make_alignment("d1", "s", coverage=0.30, segments=segs_low,
                            num_source_regions=1),
            _make_alignment("d2", "s", coverage=0.80, segments=segs_high,
                            num_source_regions=3),
        ]
        meta_map = {
            "d1": _make_metadata("d1", 100),
            "d2": _make_metadata("d2", 100),
            "s": _make_metadata("s", 50000),
        }
        scores = score_all(alignments, meta_map)
        assert len(scores) == 2
        assert scores[0].confidence >= scores[1].confidence


class TestDetectMultiSourceDigests:
    def test_single_source_not_flagged(self):
        """A digest with only one source should not be flagged."""
        scores = [
            DigestScore(
                digest_id="d", source_id="s1",
                classification="excerpt", confidence=0.9,
                containment=0.8, coverage=0.8, novel_fraction=0.2,
                avg_segment_length=20, longest_segment=50,
                num_source_regions=1, source_span=0.01,
            ),
        ]
        alignments = [_make_alignment("d", "s1", coverage=0.8,
                                       segments=[_make_segment(0, 80, 0, 80)])]
        meta_map = {"d": _make_metadata("d", 100)}
        result = detect_multi_source_digests(scores, alignments, meta_map)
        assert len(result) == 0

    def test_multi_source_detected(self):
        """A digest drawing from two sources with improved combined coverage."""
        # Source 1 covers digest[0:50], source 2 covers digest[50:100]
        scores = [
            DigestScore(
                digest_id="d", source_id="s1",
                classification="digest", confidence=0.6,
                containment=0.5, coverage=0.5, novel_fraction=0.5,
                avg_segment_length=25, longest_segment=50,
                num_source_regions=1, source_span=0.01,
            ),
            DigestScore(
                digest_id="d", source_id="s2",
                classification="digest", confidence=0.6,
                containment=0.5, coverage=0.5, novel_fraction=0.5,
                avg_segment_length=25, longest_segment=50,
                num_source_regions=1, source_span=0.01,
            ),
        ]
        # Non-overlapping segments from different sources
        alignments = [
            _make_alignment("d", "s1", coverage=0.5,
                            segments=[_make_segment(0, 50, 0, 50)]),
            _make_alignment("d", "s2", coverage=0.5,
                            segments=[_make_segment(50, 100, 0, 50)]),
        ]
        meta_map = {"d": _make_metadata("d", 100)}
        result = detect_multi_source_digests(scores, alignments, meta_map)
        assert len(result) == 1
        assert result[0].digest_id == "d"
        # Combined coverage should be ~1.0 (both halves)
        assert result[0].combined_coverage > 0.9

    def test_overlapping_sources_not_flagged(self):
        """Two sources covering the same region shouldn't inflate coverage."""
        scores = [
            DigestScore(
                digest_id="d", source_id="s1",
                classification="digest", confidence=0.6,
                containment=0.5, coverage=0.5, novel_fraction=0.5,
                avg_segment_length=25, longest_segment=50,
                num_source_regions=1, source_span=0.01,
            ),
            DigestScore(
                digest_id="d", source_id="s2",
                classification="digest", confidence=0.6,
                containment=0.5, coverage=0.5, novel_fraction=0.5,
                avg_segment_length=25, longest_segment=50,
                num_source_regions=1, source_span=0.01,
            ),
        ]
        # Both sources cover the same digest region
        alignments = [
            _make_alignment("d", "s1", coverage=0.5,
                            segments=[_make_segment(0, 50, 0, 50)]),
            _make_alignment("d", "s2", coverage=0.5,
                            segments=[_make_segment(0, 50, 200, 250)]),
        ]
        meta_map = {"d": _make_metadata("d", 100)}
        result = detect_multi_source_digests(scores, alignments, meta_map)
        # Combined coverage (0.5) is not > best_single (0.5) * 1.1
        assert len(result) == 0

    def test_ignores_non_digest_classifications(self):
        """Only excerpt and digest should be considered."""
        scores = [
            DigestScore(
                digest_id="d", source_id="s1",
                classification="shared_tradition", confidence=0.3,
                containment=0.2, coverage=0.2, novel_fraction=0.8,
                avg_segment_length=5, longest_segment=10,
                num_source_regions=1, source_span=0.01,
            ),
            DigestScore(
                digest_id="d", source_id="s2",
                classification="commentary", confidence=0.4,
                containment=0.3, coverage=0.3, novel_fraction=0.7,
                avg_segment_length=8, longest_segment=15,
                num_source_regions=1, source_span=0.01,
            ),
        ]
        alignments = [
            _make_alignment("d", "s1", coverage=0.2,
                            segments=[_make_segment(0, 20, 0, 20)]),
            _make_alignment("d", "s2", coverage=0.3,
                            segments=[_make_segment(20, 50, 0, 30)]),
        ]
        meta_map = {"d": _make_metadata("d", 100)}
        result = detect_multi_source_digests(scores, alignments, meta_map)
        assert len(result) == 0
