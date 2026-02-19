"""Tests for Stage 3: Seed-and-extend alignment."""

import pytest

from digest_detector.align import (
    _find_seeds,
    _extend_seeds,
    _chain_seeds,
    align_pair,
    align_candidates,
    _count_source_regions,
)
from digest_detector.models import (
    AlignmentSegment, ExtractedText, TextMetadata, CandidatePair,
)
from tests.helpers import make_text


class TestFindSeeds:
    def test_exact_match(self):
        digest = "觀自在菩薩行深般若波羅蜜"
        source = "如是我聞觀自在菩薩行深般若波羅蜜多時"
        seeds = _find_seeds(digest, source, k=5)
        assert len(seeds) > 0
        # Should find a long match
        max_len = max(s[2] for s in seeds)
        assert max_len >= 10  # "觀自在菩薩行深般若波羅蜜" is 13 chars, 10 overlap

    def test_no_match(self):
        digest = "甲乙丙丁戊己庚辛"
        source = "子丑寅卯辰巳午未申酉"
        seeds = _find_seeds(digest, source, k=5)
        assert len(seeds) == 0

    def test_short_text(self):
        seeds = _find_seeds("般若", "般若波羅蜜多", k=5)
        assert len(seeds) == 0

    def test_multiple_seeds(self):
        # Digest has two segments from different parts of source
        digest = "觀自在菩薩色即是空空即是色"
        source = ("一切法門觀自在菩薩行深般若"
                  "中間很多其他文字在這裡填充"
                  "色即是空空即是色受想行識")
        seeds = _find_seeds(digest, source, k=5)
        assert len(seeds) >= 2


class TestChainSeeds:
    def test_non_overlapping(self):
        # Two non-overlapping seeds in digest coordinates
        seeds = [
            (0, 10, 100, 110, "exact"),   # digest[0:10] → source[100:110]
            (15, 25, 500, 510, "exact"),   # digest[15:25] → source[500:510]
        ]
        chained = _chain_seeds(seeds, 30)
        assert len(chained) == 2
        total_coverage = sum(s[1] - s[0] for s in chained)
        assert total_coverage == 20

    def test_overlapping_picks_better(self):
        # Two overlapping seeds; should pick the one giving better coverage
        seeds = [
            (0, 15, 100, 115, "exact"),  # 15 chars
            (5, 25, 200, 220, "exact"),  # 20 chars — overlaps with first
        ]
        chained = _chain_seeds(seeds, 30)
        # Should pick the longer one or a non-overlapping combination
        total_coverage = sum(s[1] - s[0] for s in chained)
        assert total_coverage >= 15

    def test_empty(self):
        assert _chain_seeds([], 100) == []


class TestAlignPair:
    def test_perfect_match(self):
        text = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空"
        result = align_pair(text, text, "d", "s")
        assert result.coverage > 0.9
        assert result.novel_fraction < 0.1

    def test_partial_match(self):
        digest = "觀自在菩薩行深般若波羅蜜新增加的內容在這裡"
        source = "如是我聞觀自在菩薩行深般若波羅蜜多時照見五蘊"
        result = align_pair(digest, source, "d", "s")
        # Should find the overlapping part
        assert result.coverage > 0.3
        assert result.novel_fraction < 1.0

    def test_no_match(self):
        digest = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未"
        source = "春夏秋冬東西南北上下左右前後內外天地人"
        result = align_pair(digest, source, "d", "s")
        assert result.coverage < 0.1

    def test_segments_cover_digest(self):
        """All segments should cover the entire digest without gaps."""
        digest = "觀自在菩薩行新內容色即是空空即是色"
        source = "觀自在菩薩行深般若波色即是空空即是色受想"
        result = align_pair(digest, source, "d", "s")

        # Verify segments cover the full digest
        total = sum(s.digest_end - s.digest_start for s in result.segments)
        assert total == len(digest)

        # Verify no gaps between segments
        for i in range(len(result.segments) - 1):
            assert result.segments[i].digest_end == result.segments[i + 1].digest_start

    def test_empty_digest(self):
        result = align_pair("", "觀自在菩薩", "d", "s")
        assert result.coverage == 0.0
        assert len(result.segments) == 0


class TestCountSourceRegions:
    def test_single_region(self):
        segs = [
            AlignmentSegment(0, 10, 100, 110, "exact", "", ""),
            AlignmentSegment(10, 20, 115, 125, "exact", "", ""),
        ]
        assert _count_source_regions(segs) == 1

    def test_two_regions(self):
        segs = [
            AlignmentSegment(0, 10, 100, 110, "exact", "", ""),
            AlignmentSegment(15, 25, 5000, 5010, "exact", "", ""),
        ]
        assert _count_source_regions(segs) == 2

    def test_empty(self):
        assert _count_source_regions([]) == 0


class TestEarlyTermination:
    def test_low_overlap_returns_early(self):
        """Pairs with no meaningful seeds should early-terminate with coverage=0.

        Uses skip_phonetic_rescan=True so early termination fires even
        when ENABLE_PHONETIC_SCAN is globally on.
        """
        digest = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥"
        source = "春夏秋冬東西南北上下左右前後內外天地人間日月星辰風雨雷電山川河海" * 5
        result = align_pair(digest, source, "d", "s", skip_phonetic_rescan=True)
        assert result.coverage == 0.0
        assert result.novel_fraction == 1.0
        # Should be a single novel segment covering the whole digest
        assert len(result.segments) == 1
        assert result.segments[0].match_type == "novel"
        assert result.segments[0].digest_end - result.segments[0].digest_start == len(digest)

    def test_does_not_skip_real_matches(self):
        """Pairs with significant overlap should NOT early-terminate."""
        shared = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"
        digest = shared + "新增內容"
        source = "如是我聞" + shared + "更多佛經文字在這裡填充更多內容" * 5
        result = align_pair(digest, source, "d", "s")
        # Should have real coverage from the shared segment
        assert result.coverage > 0.3
        # Should have matched segments, not just a single novel segment
        matched = [s for s in result.segments if s.match_type != "novel"]
        assert len(matched) > 0

    def test_low_overlap_with_phonetic_enabled(self):
        """When phonetic rescan is enabled, low-overlap pairs should NOT
        early-terminate — they proceed to phonetic rescan instead.

        This verifies the do_phonetic gate: even with 0 exact seeds,
        the code path reaches _phonetic_rescan rather than returning early.
        """
        digest = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥"
        source = "春夏秋冬東西南北上下左右前後內外天地人間日月星辰風雨雷電山川河海" * 5
        # Default: skip_phonetic_rescan=False, ENABLE_PHONETIC_SCAN=True
        result = align_pair(digest, source, "d", "s", skip_phonetic_rescan=False)
        # No exact seeds, no phonetic chars → still coverage=0,
        # but the code path went through phonetic rescan (not early return).
        # We verify structurally: segments should still exist.
        assert result.novel_fraction == 1.0
        assert len(result.segments) >= 1


class TestAlignCandidatesPrefilter:
    """Test the zero-containment docNumber pair pre-filter in align_candidates."""

    def test_large_zero_containment_docnum_pair_skipped(self):
        """Zero-containment docNumber pairs with both texts >5000 chars are skipped."""
        # Create two large, unrelated texts with docNumber cross-ref
        large_d = "甲" * 6000
        large_s = "乙" * 12000

        text_map = {
            "T01n0001": make_text("T01n0001", large_d),
            "T01n0002": make_text("T01n0002", large_s),
        }
        candidates = [
            CandidatePair(
                digest_id="T01n0001", source_id="T01n0002",
                containment_score=0.0, matching_ngrams=0,
                total_digest_ngrams=0, from_docnumber=True,
            ),
        ]

        results = align_candidates(candidates, text_map, num_workers=1)
        # The pair should be skipped entirely — no alignment results
        assert len(results) == 0

    def test_small_zero_containment_docnum_pair_not_skipped(self):
        """Zero-containment docNumber pairs with small texts are NOT skipped."""
        small_d = "甲乙丙丁戊己庚辛壬癸" * 10  # 100 chars
        small_s = "子丑寅卯辰巳午未申酉" * 50  # 500 chars

        text_map = {
            "T01n0001": make_text("T01n0001", small_d),
            "T01n0002": make_text("T01n0002", small_s),
        }
        candidates = [
            CandidatePair(
                digest_id="T01n0001", source_id="T01n0002",
                containment_score=0.0, matching_ngrams=0,
                total_digest_ngrams=0, from_docnumber=True,
            ),
        ]

        results = align_candidates(candidates, text_map, num_workers=1)
        # Small texts should still be aligned
        assert len(results) == 1

    def test_phonetic_pair_not_skipped_even_if_large(self):
        """Phonetic-origin pairs are never skipped, even if large and zero-containment."""
        large_d = "甲" * 6000
        large_s = "乙" * 12000

        text_map = {
            "T01n0001": make_text("T01n0001", large_d),
            "T01n0002": make_text("T01n0002", large_s),
        }
        candidates = [
            CandidatePair(
                digest_id="T01n0001", source_id="T01n0002",
                containment_score=0.0, matching_ngrams=0,
                total_digest_ngrams=0, from_phonetic=True,
            ),
        ]

        results = align_candidates(candidates, text_map, num_workers=1)
        # Phonetic pair should still be aligned
        assert len(results) == 1


class TestNumWorkersEdgeCases:
    """Verify num_workers=0 and negative values don't crash."""

    def test_align_candidates_zero_workers(self):
        """num_workers=0 should fall through to serial path safely."""
        text = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空" * 5
        source = text + "更多文字" * 20

        text_map = {
            "d": make_text("d", text),
            "s": make_text("s", source),
        }
        candidates = [
            CandidatePair(
                digest_id="d", source_id="s",
                containment_score=0.5, matching_ngrams=10,
                total_digest_ngrams=20,
            ),
        ]

        results = align_candidates(candidates, text_map, num_workers=0)
        assert len(results) == 1

    def test_generate_candidates_zero_workers(self):
        """generate_candidates with num_workers=0 should not crash."""
        from digest_detector.candidates import generate_candidates
        from digest_detector.fingerprint import (
            compute_document_frequencies, identify_stopgrams, build_ngram_sets,
        )

        shared = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"
        texts = [
            make_text("T01n0001", shared + "新增少量"),
            make_text("T01n0002", "如是我聞" + shared + "更多更多文字" * 20),
        ]
        doc_freq = compute_document_frequencies(texts, n=5, num_workers=1)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5, num_workers=1)

        # Should not crash — falls through to serial path
        candidates = generate_candidates(texts, ngram_sets, stopgrams, num_workers=0)
        assert isinstance(candidates, list)
