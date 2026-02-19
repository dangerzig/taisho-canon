"""Tests for fast (Cython/fallback) implementations of hot-path functions.

Covers:
- Direct unit tests for fast_ngram_hashes, fast_find_seeds, fast_fuzzy_extend
- Cython/fallback equivalence (when both are available)
- Edge cases: empty text, n > len(text), multi-byte chars, pre-built source table,
  backward fuzzy extend, gap-d/gap-s both matching, text boundaries
"""

import os
import pytest
from collections import defaultdict

from digest_detector._fast_fallback import (
    fast_ngram_hashes as py_ngram_hashes,
    fast_find_seeds as py_find_seeds,
    fast_fuzzy_extend as py_fuzzy_extend,
)
from digest_detector.fast import (
    fast_ngram_hashes,
    fast_find_seeds,
    fast_fuzzy_extend,
)


# ---- Helpers ----

def _build_kgram_table(text: str, k: int) -> dict[str, list[int]]:
    """Build a k-gram table matching the one in align.py."""
    table = defaultdict(list)
    for i in range(len(text) - k + 1):
        table[text[i:i + k]].append(i)
    return table


def _has_cython():
    """Check if Cython extension is available (not just fallback)."""
    try:
        from digest_detector._fast import fast_ngram_hashes as _  # noqa: F401
        return True
    except ImportError:
        return False


# ---- fast_ngram_hashes ----

class TestFastNgramHashes:
    def test_basic(self):
        result = fast_ngram_hashes("ABCDE", 3)
        assert isinstance(result, frozenset)
        assert len(result) == 3  # ABC, BCD, CDE

    def test_empty_text(self):
        result = fast_ngram_hashes("", 3)
        assert result == frozenset()

    def test_text_shorter_than_n(self):
        result = fast_ngram_hashes("AB", 3)
        assert result == frozenset()

    def test_text_equal_to_n(self):
        result = fast_ngram_hashes("ABC", 3)
        assert len(result) == 1

    def test_single_char_ngrams(self):
        result = fast_ngram_hashes("AABA", 1)
        # Unique: A, B → 2 hashes
        assert len(result) == 2

    def test_stopgrams_none(self):
        without = fast_ngram_hashes("ABCDE", 3, None)
        also_without = fast_ngram_hashes("ABCDE", 3)
        assert without == also_without

    def test_stopgrams_empty_set(self):
        without = fast_ngram_hashes("ABCDE", 3)
        with_empty = fast_ngram_hashes("ABCDE", 3, set())
        assert without == with_empty

    def test_stopgrams_filtering(self):
        all_hashes = fast_ngram_hashes("ABCDE", 3)
        # Pick one hash to filter
        one_hash = next(iter(all_hashes))
        filtered = fast_ngram_hashes("ABCDE", 3, {one_hash})
        assert len(filtered) == len(all_hashes) - 1
        assert one_hash not in filtered

    def test_cjk_text(self):
        """CJK characters (multi-byte UTF-8) should hash correctly."""
        text = "般若波羅蜜多心經"  # 8 CJK chars
        result = fast_ngram_hashes(text, 3)
        assert len(result) == 6  # 8 - 3 + 1

    def test_mixed_multibyte(self):
        """Mix of ASCII, CJK, and other multi-byte characters."""
        text = "A般若B波C"  # 6 chars
        result = fast_ngram_hashes(text, 3)
        assert len(result) == 4  # 6 - 3 + 1

    def test_deterministic_across_calls(self):
        """Same input should always produce same hashes."""
        a = fast_ngram_hashes("般若波羅蜜多心經", 5)
        b = fast_ngram_hashes("般若波羅蜜多心經", 5)
        assert a == b


# ---- fast_find_seeds ----

class TestFastFindSeeds:
    def test_basic_exact_match(self):
        digest = "XYZABCXYZ"
        source = "000ABC000"
        seeds = fast_find_seeds(digest, source, 3)
        assert any(s[2] >= 3 for s in seeds)
        # Should find "ABC" match
        found = [(d, s, l) for d, s, l in seeds if digest[d:d+l] == "ABC"]
        assert len(found) >= 1

    def test_empty_digest(self):
        assert fast_find_seeds("", "ABCDE", 3) == []

    def test_empty_source(self):
        assert fast_find_seeds("ABCDE", "", 3) == []

    def test_digest_shorter_than_k(self):
        assert fast_find_seeds("AB", "ABCDE", 3) == []

    def test_source_shorter_than_k(self):
        assert fast_find_seeds("ABCDE", "AB", 3) == []

    def test_no_match(self):
        seeds = fast_find_seeds("AAAA", "BBBB", 3)
        assert seeds == []

    def test_full_match(self):
        """Digest is a substring of source."""
        seeds = fast_find_seeds("BCDE", "ABCDEF", 3)
        assert len(seeds) >= 1
        # Should find the full 4-char match
        assert any(l >= 4 for _, _, l in seeds)

    def test_multiple_matches(self):
        """Multiple non-overlapping matches in source."""
        digest = "ABCXYZDEF"
        source = "000ABC111DEF222"
        seeds = fast_find_seeds(digest, source, 3)
        assert len(seeds) >= 2

    def test_best_match_selected(self):
        """When a k-gram appears multiple times in source, best match is kept."""
        digest = "ABCDE"
        source = "ABCXABCDE"  # ABC at pos 0 (extends to 3), ABC at pos 4 (extends to 5)
        seeds = fast_find_seeds(digest, source, 3)
        # Should find the longer match
        assert any(l >= 5 for _, _, l in seeds)

    def test_with_prebuilt_source_table(self):
        """Using a pre-built source table should give identical results."""
        digest = "般若波羅蜜多"
        source = "大般若波羅蜜多經卷第一"
        k = 3
        table = _build_kgram_table(source, k)
        with_table = fast_find_seeds(digest, source, k, table)
        without_table = fast_find_seeds(digest, source, k)
        # Same seeds (order may differ)
        assert sorted(with_table) == sorted(without_table)

    def test_cjk_seeds(self):
        """CJK character matching should work correctly."""
        digest = "般若波羅蜜多心經"
        source = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空"
        seeds = fast_find_seeds(digest, source, 3)
        assert len(seeds) >= 1
        # Should find "般若波羅蜜多"
        assert any(l >= 6 for _, _, l in seeds)


# ---- fast_fuzzy_extend ----

class TestFastFuzzyExtend:
    def test_forward_exact_match(self):
        """Forward extension with matching characters."""
        d_ext, s_ext = fast_fuzzy_extend("ABCD", "ABCD", 0, 0, 1, 1, -2, -4)
        assert d_ext == 4
        assert s_ext == 4

    def test_forward_mismatch(self):
        """Forward extension stops after too many mismatches."""
        d_ext, s_ext = fast_fuzzy_extend("AXXXX", "AYYYY", 0, 0, 1, 1, -2, -4)
        # First char matches (+1), then mismatches drive score below threshold
        assert d_ext >= 1
        assert s_ext >= 1

    def test_backward_extension(self):
        """Backward extension (direction=-1) from end of match."""
        digest = "XYZABC"
        source = "XYZABC"
        # Start at position 5 (last char), extend backward
        d_ext, s_ext = fast_fuzzy_extend(digest, source, 5, 5, -1, 1, -2, -4)
        assert d_ext == 6  # extends all the way to position 0
        assert s_ext == 6

    def test_backward_at_start(self):
        """Backward extension from position 0 should extend 0 chars."""
        d_ext, s_ext = fast_fuzzy_extend("ABCDE", "XYZWV", 0, 0, -1, 1, -2, -4)
        # Position -1 is out of bounds immediately
        assert d_ext == 0
        assert s_ext == 0

    def test_forward_at_end(self):
        """Forward extension from last position should extend 0-1 chars."""
        d_ext, s_ext = fast_fuzzy_extend("ABCDE", "ABCDE", 4, 4, 1, 1, -2, -4)
        assert d_ext == 1  # matches position 4
        assert s_ext == 1

    def test_gap_in_digest(self):
        """Gap detection: skip one char in digest after initial matches."""
        # Start with matches to build positive score, then a gap
        digest = "ABCXDEF"
        source = "ABCDEF"
        # Forward from position 0: ABC matches (+3), then X vs D (gap_d: digest[4]=D==source[3]=D)
        d_ext, s_ext = fast_fuzzy_extend(digest, source, 0, 0, 1, 1, -2, -4)
        # Should match ABC (3 chars), then gap + DEF
        assert d_ext >= 3
        assert s_ext >= 3

    def test_gap_in_source(self):
        """Gap detection: skip one char in source after initial matches."""
        digest = "ABCDEF"
        source = "ABCXDEF"
        d_ext, s_ext = fast_fuzzy_extend(digest, source, 0, 0, 1, 1, -2, -4)
        assert d_ext >= 3
        assert s_ext >= 3

    def test_boundary_checks(self):
        """Extension should not go out of bounds."""
        d_ext, s_ext = fast_fuzzy_extend("A", "A", 0, 0, 1, 1, -2, -4)
        assert d_ext == 1
        assert s_ext == 1

    def test_completely_different(self):
        """Completely different texts should extend minimally."""
        d_ext, s_ext = fast_fuzzy_extend("AAAA", "BBBB", 0, 0, 1, 1, -2, -4)
        # Score drops below -4 quickly
        assert d_ext <= 3
        assert s_ext <= 3


# ---- Cython/fallback equivalence ----

@pytest.mark.skipif(not _has_cython(), reason="Cython extension not compiled")
class TestCythonFallbackEquivalence:
    """Verify that Cython and pure-Python implementations produce identical results."""

    def _import_cython(self):
        from digest_detector._fast import (
            fast_ngram_hashes as cy_ngram_hashes,
            fast_find_seeds as cy_find_seeds,
            fast_fuzzy_extend as cy_fuzzy_extend,
        )
        return cy_ngram_hashes, cy_find_seeds, cy_fuzzy_extend

    def test_ngram_hashes_equivalence(self):
        cy_ngram_hashes, _, _ = self._import_cython()
        texts = [
            "ABCDEFGH",
            "般若波羅蜜多心經",
            "A般若B波C",
            "",
            "AB",
        ]
        for text in texts:
            for n in [1, 3, 5]:
                cy_result = cy_ngram_hashes(text, n)
                py_result = py_ngram_hashes(text, n)
                assert cy_result == py_result, f"Mismatch for text={text!r}, n={n}"

    def test_ngram_hashes_with_stopgrams_equivalence(self):
        cy_ngram_hashes, _, _ = self._import_cython()
        text = "般若波羅蜜多心經觀自在菩薩"
        all_hashes = py_ngram_hashes(text, 3)
        stopgrams = set(list(all_hashes)[:3])

        cy_result = cy_ngram_hashes(text, 3, stopgrams)
        py_result = py_ngram_hashes(text, 3, stopgrams)
        assert cy_result == py_result

    def test_find_seeds_equivalence(self):
        _, cy_find_seeds, _ = self._import_cython()
        pairs = [
            ("般若波羅蜜多心經", "觀自在菩薩行深般若波羅蜜多時"),
            ("ABCXYZDEF", "000ABC111DEF222"),
            ("ABCDE", "FGHIJ"),
            ("", "ABCDE"),
        ]
        for digest, source in pairs:
            for k in [3, 5]:
                cy_result = sorted(cy_find_seeds(digest, source, k))
                py_result = sorted(py_find_seeds(digest, source, k))
                assert cy_result == py_result, (
                    f"Mismatch for digest={digest!r}, source={source!r}, k={k}")

    def test_find_seeds_with_table_equivalence(self):
        _, cy_find_seeds, _ = self._import_cython()
        digest = "般若波羅蜜多"
        source = "大般若波羅蜜多經卷第一"
        k = 3
        table = _build_kgram_table(source, k)
        cy_result = sorted(cy_find_seeds(digest, source, k, table))
        py_result = sorted(py_find_seeds(digest, source, k, table))
        assert cy_result == py_result

    def test_fuzzy_extend_equivalence(self):
        _, _, cy_fuzzy_extend = self._import_cython()
        cases = [
            # (digest, source, d_pos, s_pos, direction, match, mismatch, threshold)
            ("ABCDE", "ABCDE", 0, 0, 1, 1, -2, -4),
            ("ABCDE", "ABCDE", 4, 4, -1, 1, -2, -4),
            ("AXBCD", "ABCD", 0, 0, 1, 1, -2, -4),
            ("ABCD", "AXBCD", 0, 0, 1, 1, -2, -4),
            ("AAAA", "BBBB", 0, 0, 1, 1, -2, -4),
            ("A", "A", 0, 0, 1, 1, -2, -4),
            ("般若波", "般若波", 0, 0, 1, 1, -2, -4),
        ]
        for args in cases:
            cy_result = cy_fuzzy_extend(*args)
            py_result = py_fuzzy_extend(*args)
            assert cy_result == py_result, f"Mismatch for args={args}"


# ---- Source table compatibility ----

class TestSourceTableCompatibility:
    def test_build_kgram_table_and_fast_find_seeds(self):
        """_build_kgram_table (defaultdict) and fast_find_seeds internal table
        should produce identical seed results."""
        source = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"
        digest = "般若波羅蜜多"
        k = 3
        table = _build_kgram_table(source, k)
        with_table = sorted(fast_find_seeds(digest, source, k, table))
        without_table = sorted(fast_find_seeds(digest, source, k))
        assert with_table == without_table

    def test_repeated_calls_same_source(self):
        """Calling fast_find_seeds multiple times with same source should be
        consistent (regression test for caching bugs)."""
        source = "大般若波羅蜜多經卷第一"
        k = 3
        table = _build_kgram_table(source, k)

        digests = ["般若波", "波羅蜜", "蜜多經", "大般若"]
        results = []
        for d in digests:
            seeds = fast_find_seeds(d, source, k, table)
            results.append(sorted(seeds))

        # Run again — should get identical results
        for i, d in enumerate(digests):
            seeds = fast_find_seeds(d, source, k, table)
            assert sorted(seeds) == results[i]


# ---- _chain_seeds edge cases ----

class TestChainSeedsContainedSeeds:
    """Test that _chain_seeds correctly handles contained seeds via its pre-filter."""

    def test_contained_seed_removed(self):
        """A seed fully contained within another should be handled."""
        from digest_detector.align import _chain_seeds
        # Seed B (5,8) is contained within seed A (3,10)
        seeds = [
            (3, 10, 0, 7, "exact"),   # covers digest 3-10
            (5, 8, 10, 13, "exact"),   # covers digest 5-8 (contained in above)
        ]
        result = _chain_seeds(seeds, 20)
        total_coverage = sum(s[1] - s[0] for s in result)
        # Should select the larger seed (coverage 7) not the smaller (coverage 3)
        assert total_coverage == 7

    def test_three_seeds_abc_containment(self):
        """Three seeds where A contains C but B (between) does not."""
        from digest_detector.align import _chain_seeds
        seeds = [
            (0, 15, 0, 15, "exact"),   # A: covers 0-15
            (5, 12, 20, 27, "exact"),  # B: covers 5-12 (overlaps A, not contained)
            (2, 10, 40, 48, "exact"),  # C: covers 2-10 (contained in A)
        ]
        result = _chain_seeds(seeds, 20)
        total_coverage = sum(s[1] - s[0] for s in result)
        # Best chain is A alone (15), since B and C both overlap with A
        assert total_coverage == 15
