"""Tests for phonetic equivalence table and transliteration detection."""

import pytest

from digest_detector.phonetic import (
    _split_syllables,
    _extract_sanskrit,
    _is_cjk,
    _normalize_sanskrit,
    build_equivalence_table,
    are_phonetically_equivalent,
    get_equivalence_groups,
    phonetic_mapping_for_pair,
)


class TestSplitSyllables:
    def test_gate(self):
        assert _split_syllables("gate") == ["ga", "te"]

    def test_paragate(self):
        assert _split_syllables("pāragate") == ["pa", "ra", "ga", "te"]

    def test_bodhi(self):
        assert _split_syllables("bodhi") == ["bod", "hi"]

    def test_svaha(self):
        assert _split_syllables("svāhā") == ["sva", "ha"]

    def test_gandharva(self):
        assert _split_syllables("gandharva") == ["gand", "har", "va"]

    def test_vajra(self):
        assert _split_syllables("vajra") == ["vaj", "ra"]

    def test_samadhi(self):
        syls = _split_syllables("samādhi")
        assert len(syls) == 3

    def test_empty(self):
        assert _split_syllables("") == []


class TestExtractSanskrit:
    def test_explicit_skt(self):
        assert _extract_sanskrit("(Skt. gandharva)") == "gandharva"

    def test_skt_with_star(self):
        result = _extract_sanskrit("(Skt. *Mahāsāṁghika)")
        assert result is not None
        assert "ghika" in result

    def test_skt_with_gloss(self):
        # Should take only the Sanskrit term, not the English gloss
        assert _extract_sanskrit("(Skt. Nirmāṇarati) heaven") == "Nirmāṇarati"

    def test_bare_diacritical(self):
        assert _extract_sanskrit("saṁpatti") == "saṁpatti"

    def test_bare_english_rejected(self):
        assert _extract_sanskrit("one") is None
        assert _extract_sanskrit("king of a continent") is None
        assert _extract_sanskrit("monk") is None

    def test_no_sanskrit(self):
        assert _extract_sanskrit("enlightenment") is None


class TestNormalizeSanskrit:
    def test_strips_diacritics(self):
        assert _normalize_sanskrit("pāramitā") == "paramita"
        assert _normalize_sanskrit("saṁbodhi") == "sambodhi"

    def test_lowercase(self):
        assert _normalize_sanskrit("Gandharva") == "gandharva"

    def test_removes_hyphens(self):
        assert _normalize_sanskrit("samyak-saṁbuddha") == "samyaksambuddha"


class TestBuildEquivalenceTable:
    @pytest.fixture(scope="class")
    def table(self):
        return build_equivalence_table()

    def test_table_not_empty(self, table):
        assert len(table) > 100

    def test_jie_maps_to_ga(self, table):
        """揭 should map to 'ga' (as in gate/揭帝)."""
        assert "ga" in table.get("揭", set())

    def test_jie2_maps_to_ga(self, table):
        """竭 should also map to 'ga'."""
        assert "ga" in table.get("竭", set())

    def test_non_transliteration_absent(self, table):
        """Common semantic characters should not be in the table."""
        # 我 (wǒ, "I") is never used as a transliteration character
        assert "我" not in table

    def test_key_dharani_chars_present(self, table):
        """Core transliteration characters should be in the table.

        Note: highly ambiguous chars like 波 (13 syllables), 羅 (12),
        提 (7), 薩 (6), 婆 (21) are filtered out by PHONETIC_MAX_SYLLABLES
        to prevent false positives.
        """
        for ch in ["揭", "竭", "帝", "僧", "菩", "訶"]:
            assert ch in table, f"{ch} should be in equivalence table"


class TestPhoneticEquivalence:
    @pytest.fixture(scope="class")
    def table(self):
        return build_equivalence_table()

    def test_same_char(self, table):
        assert are_phonetically_equivalent("揭", "揭", table)

    def test_jie_jie2_equivalent(self, table):
        """揭 and 竭 both transliterate 'ga'."""
        assert are_phonetically_equivalent("揭", "竭", table)

    def test_di_di2_equivalent(self, table):
        """帝 and 諦 both transliterate 'ti'."""
        assert are_phonetically_equivalent("帝", "諦", table)

    def test_luo_luo2_equivalent(self, table):
        """囉 transliterates 'ra'; 羅 is filtered (>5 syllables)."""
        assert "囉" in table
        assert "ra" in table.get("囉", set())

    def test_unrelated_chars_not_equivalent(self, table):
        """Characters with no shared syllable should not be equivalent."""
        assert not are_phonetically_equivalent("揭", "波", table)

    def test_non_transliteration_not_equivalent(self, table):
        """Non-transliteration chars should not be equivalent."""
        assert not are_phonetically_equivalent("我", "你", table)

    def test_one_missing_not_equivalent(self, table):
        """If one char is not in the table, they're not equivalent."""
        assert not are_phonetically_equivalent("揭", "我", table)


class TestEquivalenceGroups:
    @pytest.fixture(scope="class")
    def groups(self):
        table = build_equivalence_table()
        return get_equivalence_groups(table)

    def test_ga_group_has_multiple(self, groups):
        """The 'ga' group should contain both 揭 and 竭."""
        ga_chars = groups.get("ga", set())
        assert "揭" in ga_chars
        assert "竭" in ga_chars
        assert len(ga_chars) >= 2

    def test_groups_not_empty(self, groups):
        assert len(groups) > 50


class TestPhoneticMapping:
    @pytest.fixture(scope="class")
    def table(self):
        return build_equivalence_table()

    def test_gate_gate_mapping(self, table):
        """揭諦 vs 竭帝 should produce phonetic mapping with shared syllables."""
        mapping = phonetic_mapping_for_pair("揭諦", "竭帝", table)
        assert len(mapping) == 2
        # First pair: 揭/竭 → both ga
        assert mapping[0][0] == "揭"
        assert mapping[0][2] == "竭"
        assert mapping[0][1] == "ga"
        # Second pair: 諦/帝 → both ti
        assert mapping[1][0] == "諦"
        assert mapping[1][2] == "帝"
        assert mapping[1][1] == "ti"

    def test_exact_match_mapping(self, table):
        """Identical chars should use '=' or actual syllable."""
        mapping = phonetic_mapping_for_pair("波", "波", table)
        assert len(mapping) == 1
        assert mapping[0][0] == "波"
        assert mapping[0][2] == "波"
