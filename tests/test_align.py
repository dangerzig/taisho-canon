"""Tests for Stage 3: Seed-and-extend alignment."""

import pytest

from digest_detector.align import (
    _find_seeds,
    _extend_seeds,
    _chain_seeds,
    align_pair,
    _count_source_regions,
)
from digest_detector.models import AlignmentSegment


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
