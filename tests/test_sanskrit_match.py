"""Tests for the Sanskrit title matching pipeline."""

import pytest

from digest_detector.sanskrit_match import (
    normalize_title,
    tokenize_title,
    levenshtein_ratio,
    levenshtein_ratio_threshold,
    jaccard_similarity,
    find_matches,
    validate_matches,
    _normalize_taisho_id,
    FUZZY_THRESHOLD,
    _is_section_mismatch,
    annotate_section_preference,
)


# ---------------------------------------------------------------------------
# Title normalisation
# ---------------------------------------------------------------------------


class TestNormalizeTitle:
    def test_iast_diacritics(self):
        assert normalize_title("Prajñāpāramitā") == "prajnaparamita"

    def test_lowercase(self):
        assert normalize_title("SUTRA") == "sutra"
        assert normalize_title("Sūtra") == "sutra"

    def test_remove_hyphens(self):
        assert normalize_title("Mahā-parinirvāṇa-sūtra") == "mahaparinirvanasutra"

    def test_remove_spaces(self):
        assert normalize_title("Mahā yāna sūtra") == "mahayanasutra"

    def test_remove_parentheses(self):
        # ī→i, ā→a: "Dīrghāgama" → "dirghagama" (not "dirghaagama")
        assert normalize_title("Dīrghāgama(sūtra).") == "dirghagamasutra"

    def test_html_entities(self):
        """Lancaster data may contain HTML entities like &ntilde;."""
        result = normalize_title("Praj&ntilde;āpāramitā")
        assert result == "prajnaparamita"

    def test_numeric_html_entities(self):
        """Handle &#7789; (= ṭ) etc."""
        result = normalize_title("A&#7779;&#7789;a")
        assert result == "asta"

    def test_soft_hyphen(self):
        """84000 TEI uses soft hyphens (U+00AD) in titles."""
        result = normalize_title("Mahā\u00admegha")
        assert result == "mahamegha"

    def test_zero_width_chars(self):
        """84000 TEI uses zero-width joiners."""
        result = normalize_title("Vajra\u200bhṛdaya")
        assert result == "vajrahrdaya"

    def test_empty(self):
        assert normalize_title("") == ""

    def test_none_like(self):
        assert normalize_title("") == ""

    def test_period_removal(self):
        """Lancaster titles often end with period."""
        assert normalize_title("Saptabuddhaka.") == "saptabuddhaka"

    def test_asterisk_removal(self):
        """Some titles have asterisks for reconstructed forms."""
        assert normalize_title("*Mahāsāṁghika") == "mahasamghika"

    def test_visarga(self):
        """ḥ should map to h."""
        assert normalize_title("Ḥ") == "h"

    def test_retroflex_nasal(self):
        """ṇ → n."""
        assert normalize_title("Pañcaviṃśatisāhasrikā") == "pancavimsatisahasrika"


class TestTokenizeTitle:
    def test_basic(self):
        tokens = tokenize_title("Mahā-parinirvāṇa-sūtra")
        assert "maha" in tokens
        assert "parinirvana" in tokens
        assert "sutra" in tokens

    def test_compound(self):
        tokens = tokenize_title("Prajñāpāramitāhṛdayasūtra")
        assert "prajnaparamitahrdayasutra" in tokens

    def test_empty(self):
        assert tokenize_title("") == set()

    def test_short_tokens_filtered(self):
        """Tokens shorter than 2 chars should be filtered."""
        tokens = tokenize_title("A-B-Sūtra")
        assert "sutra" in tokens
        assert "a" not in tokens


# ---------------------------------------------------------------------------
# Similarity metrics
# ---------------------------------------------------------------------------


class TestLevenshteinRatio:
    def test_identical(self):
        assert levenshtein_ratio("hello", "hello") == 1.0

    def test_empty(self):
        assert levenshtein_ratio("", "") == 1.0

    def test_one_empty(self):
        assert levenshtein_ratio("abc", "") == 0.0

    def test_one_char_diff(self):
        ratio = levenshtein_ratio("abc", "abd")
        assert abs(ratio - 2 / 3) < 0.01

    def test_symmetry(self):
        r1 = levenshtein_ratio("kitten", "sitting")
        r2 = levenshtein_ratio("sitting", "kitten")
        assert abs(r1 - r2) < 0.001

    def test_similar_titles(self):
        """Close Sanskrit titles should have high ratio."""
        r = levenshtein_ratio(
            normalize_title("Mahāparinirvāṇasūtra"),
            normalize_title("Mahāparinirvāṇa-sūtra"),
        )
        assert r == 1.0  # after normalisation they're identical


class TestLevenshteinRatioThreshold:
    def test_above_threshold(self):
        ratio = levenshtein_ratio_threshold("abcdefghij", "abcdefghik", 0.85)
        assert ratio >= 0.85

    def test_below_threshold_returns_zero(self):
        ratio = levenshtein_ratio_threshold("abc", "xyz", 0.85)
        assert ratio == 0.0

    def test_identical(self):
        assert levenshtein_ratio_threshold("test", "test", 0.85) == 1.0


class TestJaccardSimilarity:
    def test_identical(self):
        assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0

    def test_disjoint(self):
        assert jaccard_similarity({"a"}, {"b"}) == 0.0

    def test_partial(self):
        j = jaccard_similarity({"a", "b", "c"}, {"a", "b", "d"})
        assert abs(j - 0.5) < 0.01

    def test_empty(self):
        assert jaccard_similarity(set(), {"a"}) == 0.0


# ---------------------------------------------------------------------------
# Taishō ID normalisation
# ---------------------------------------------------------------------------


class TestNormalizeTaishoId:
    def test_already_canonical(self):
        assert _normalize_taisho_id("T08n0250") == "T08n0250"

    def test_bare_t_number(self):
        result = _normalize_taisho_id("T250")
        assert result == "T08n0250"

    def test_t1(self):
        result = _normalize_taisho_id("T1")
        assert result == "T01n0001"

    def test_t220(self):
        result = _normalize_taisho_id("T220")
        # Volume 5-7 range
        assert "n0220" in result


# ---------------------------------------------------------------------------
# Known matches
# ---------------------------------------------------------------------------


class TestKnownMatches:
    """Test that known parallel pairs match via normalisation."""

    def test_heart_sutra_titles_differ(self):
        """Lancaster T250 and 84000 Toh 21 Heart Sutra have genuinely different titles.

        Lancaster: Prajñāpāramitāhṛdayasūtra
        84000:     Bhagavatīprajñāpāramitāhṛdaya

        The 84000 title adds "Bhagavatī" prefix and drops "sūtra".
        These correctly do NOT match at our thresholds -- they represent
        a known limitation of title-based matching.
        """
        t_title = "Prajñāpāramitāhṛdayasūtra"
        k_title = "Bhagavatī\u00adprajñā\u00adpāramitā\u00adhṛdaya"
        t_norm = normalize_title(t_title)
        k_norm = normalize_title(k_title)
        assert t_norm != k_norm
        ratio = levenshtein_ratio(t_norm, k_norm)
        # Ratio is ~0.52 due to prefix/suffix differences
        assert ratio > 0.4
        assert ratio < FUZZY_THRESHOLD  # below our fuzzy threshold

    def test_diamond_sutra_exact_match(self):
        """Vajracchedikā titles should exact-match after normalisation."""
        t_title = "Vajracchedikāprajñāpāramitāsūtra"
        k_title = "Vajracchedikā­prajñāpāramitā­sūtra"
        assert normalize_title(t_title) == normalize_title(k_title)

    def test_astasahasrika_near_match(self):
        """Aṣṭasāhasrikā with/without 'sūtra' suffix: below fuzzy threshold.

        The 5-char difference ('sutra') on a 32-char string gives ratio ~0.84,
        which is below our FUZZY_THRESHOLD (0.90). This is a known edge case
        where the suffix difference prevents matching.
        """
        t_title = "Aṣṭasāhasrikāprajñāpāramitāsūtra"
        k_title = "Aṣṭasāhasrikā­prajñā­pāramitā"
        t_norm = normalize_title(t_title)
        k_norm = normalize_title(k_title)
        assert t_norm != k_norm
        ratio = levenshtein_ratio(t_norm, k_norm)
        # Well below FUZZY_THRESHOLD (0.90)
        assert 0.80 <= ratio <= 0.86

    def test_lotus_sutra_match(self):
        """Saddharmapuṇḍarīka should match across sources."""
        t_title = "Saddharmapuṇḍarīkasūtra"
        k_title = "Saddharma­puṇḍarīka­sūtra"
        assert normalize_title(t_title) == normalize_title(k_title)

    def test_html_entity_match(self):
        """Lancaster HTML-encoded title should match 84000 Unicode title."""
        t_title = "Vajracchedik&#257;praj&ntilde;&#257;p&#257;ramit&#257;s&#363;tra"
        k_title = "Vajracchedikāprajñāpāramitāsūtra"
        assert normalize_title(t_title) == normalize_title(k_title)


# ---------------------------------------------------------------------------
# Find matches integration
# ---------------------------------------------------------------------------


class TestFindMatches:
    def test_exact_match(self):
        taisho = {"T08n0235": ["Vajracchedikāprajñāpāramitāsūtra"]}
        kangyur = [(16, "Vajracchedikā­prajñāpāramitā­sūtra", "84000")]
        matches = find_matches(taisho, kangyur)
        assert len(matches) >= 1
        assert matches[0]["match_type"] == "exact"
        assert matches[0]["taisho_id"] == "T08n0235"
        assert matches[0]["tohoku"] == 16

    def test_fuzzy_match(self):
        """Titles differing by a small suffix should fuzzy-match (ratio ~0.94)."""
        taisho = {"T08n0228": ["Daśabhūmikasūtra"]}
        # 'm' suffix gives ratio ~0.94, well above FUZZY_THRESHOLD (0.90)
        kangyur = [(44, "Daśabhūmikasūtram", "84000")]
        matches = find_matches(taisho, kangyur)
        assert len(matches) >= 1
        assert any(m["match_type"] == "fuzzy" for m in matches)

    def test_no_match(self):
        taisho = {"T99n9999": ["CompletelyUniqueTitleXYZ"]}
        kangyur = [(1, "TotallyDifferentTitle", "test")]
        matches = find_matches(taisho, kangyur)
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# Fuzzy threshold
# ---------------------------------------------------------------------------


class TestFuzzyThreshold:
    def test_threshold_value(self):
        assert FUZZY_THRESHOLD == 0.90

    def test_below_threshold_no_match(self):
        """A pair with ratio ~0.85 should NOT match at FUZZY_THRESHOLD=0.90."""
        taisho = {"T08n0228": ["Saddharmapuṇḍarīkasūtra"]}
        kangyur = [(134, "Āryasaddharmapuṇḍarīkasūtra", "84000")]
        matches = find_matches(taisho, kangyur)
        # Ratio ~0.852, below 0.90 threshold
        assert len(matches) == 0

    def test_above_threshold_matches(self):
        """A pair with ratio ~0.94 should match at FUZZY_THRESHOLD=0.90."""
        taisho = {"T08n0228": ["Daśabhūmikasūtra"]}
        kangyur = [(44, "Daśabhūmikasūtram", "84000")]
        matches = find_matches(taisho, kangyur)
        assert len(matches) >= 1
        assert any(m["match_type"] == "fuzzy" for m in matches)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidateMatches:
    def test_confirmed(self):
        matches = [{
            "taisho_id": "T08n0235",
            "tohoku": 16,
            "taisho_sanskrit": "Vajracchedikā",
            "kangyur_sanskrit": "Vajracchedikā",
            "match_type": "exact",
            "match_score": 1.0,
            "sources": ["test"],
        }]
        concordance = {"T08n0235": {16, 17}}
        validated, contradicted, new, filtered = validate_matches(
            matches, concordance
        )
        assert len(validated) == 1
        assert len(contradicted) == 0
        assert len(new) == 0
        assert len(filtered) == 0

    def test_contradicted(self):
        matches = [{
            "taisho_id": "T08n0235",
            "tohoku": 999,
            "taisho_sanskrit": "Title",
            "kangyur_sanskrit": "Title",
            "match_type": "exact",
            "match_score": 1.0,
            "sources": ["test"],
        }]
        concordance = {"T08n0235": {16}}
        validated, contradicted, new, filtered = validate_matches(
            matches, concordance
        )
        assert len(validated) == 0
        assert len(contradicted) == 1
        assert 16 in contradicted[0]["known_tohoku"]
        assert len(filtered) == 0

    def test_new_proposal(self):
        matches = [{
            "taisho_id": "T99n9999",
            "tohoku": 42,
            "taisho_sanskrit": "Title",
            "kangyur_sanskrit": "Title",
            "match_type": "exact",
            "match_score": 1.0,
            "sources": ["test"],
        }]
        concordance = {}
        validated, contradicted, new, filtered = validate_matches(
            matches, concordance
        )
        assert len(validated) == 0
        assert len(contradicted) == 0
        assert len(new) == 1
        assert len(filtered) == 0

    def test_negative_toh_skipped(self):
        """CBETA Tibetan entries with negative Toh IDs should be skipped."""
        matches = [{
            "taisho_id": "T01n0001",
            "tohoku": -42,
            "taisho_sanskrit": "Title",
            "kangyur_sanskrit": "Title",
            "match_type": "exact",
            "match_score": 1.0,
            "sources": ["cbeta-tibetan"],
        }]
        concordance = {"T01n0001": {34}}
        validated, contradicted, new, filtered = validate_matches(
            matches, concordance
        )
        assert len(validated) == 0
        assert len(contradicted) == 0
        assert len(new) == 0
        assert len(filtered) == 0


# ---------------------------------------------------------------------------
# Section mismatch filtering
# ---------------------------------------------------------------------------


class TestSectionMismatch:
    """Test sūtra↔commentary section mismatch detection."""

    def test_sutra_to_tengyur_fuzzy_filtered(self):
        """Sūtra text (vol 8) fuzzy-matching Tengyur commentary should be filtered."""
        reason = _is_section_mismatch("T08n0221", 3790, "fuzzy")
        assert reason is not None
        assert "sūtra" in reason
        assert "Tengyur" in reason

    def test_exact_cross_section_exempt(self):
        """Exact matches across sections should NOT be filtered."""
        reason = _is_section_mismatch("T10n0296", 4377, "exact")
        assert reason is None

    def test_kangyur_match_ok(self):
        """Sūtra text matching Kangyur sūtra is fine."""
        reason = _is_section_mismatch("T08n0235", 16, "fuzzy")
        assert reason is None

    def test_sastra_to_kangyur_filtered(self):
        """Śāstra text (vol 25-32) fuzzy-matching Kangyur should be filtered."""
        reason = _is_section_mismatch("T25n1509", 100, "fuzzy")
        assert reason is not None
        assert "śāstra" in reason
        assert "Kangyur" in reason

    def test_unresolved_volume_passes(self):
        """Unknown volume (0) should not be filtered."""
        reason = _is_section_mismatch("T00n0000", 1200, "fuzzy")
        assert reason is None

    def test_negative_toh_passes(self):
        """CBETA Tibetan entries (negative Toh) should not be filtered."""
        reason = _is_section_mismatch("T08n0221", -42, "fuzzy")
        assert reason is None

    def test_vinaya_neutral(self):
        """Vinaya volumes (22-24) matching either section should pass."""
        # Vol 22 is between sūtra (<=21) and śāstra (>=25)
        reason = _is_section_mismatch("T22n1421", 1200, "fuzzy")
        assert reason is None
        reason = _is_section_mismatch("T22n1421", 100, "fuzzy")
        assert reason is None

    def test_section_mismatch_in_validate(self):
        """Section-mismatched fuzzy match should go to filtered, not contradicted."""
        matches = [{
            "taisho_id": "T08n0221",
            "tohoku": 3790,
            "taisho_sanskrit": "Pañcaviṃśatisāhasrikā",
            "kangyur_sanskrit": "Pañcaviṃśatisāhasrikāṭīkā",
            "match_type": "fuzzy",
            "match_score": 0.92,
            "sources": ["84000-tengyur"],
        }]
        concordance = {"T08n0221": {9}}
        validated, contradicted, new, filtered = validate_matches(
            matches, concordance
        )
        assert len(filtered) == 1
        assert len(contradicted) == 0
        assert "filter_reason" in filtered[0]


# ---------------------------------------------------------------------------
# Section preference annotation
# ---------------------------------------------------------------------------


class TestSectionPreference:
    """Test section preference (Kangyur > Tengyur) annotation."""

    def test_both_divisions_demotes_tengyur(self):
        """When a sūtra text has both Kangyur and Tengyur matches, Tengyur is demoted."""
        matches = [
            {
                "taisho_id": "T08n0235",
                "tohoku": 16,  # Kangyur
                "taisho_sanskrit": "Vajracchedikā",
                "kangyur_sanskrit": "Vajracchedikā",
                "match_type": "exact",
                "match_score": 1.0,
                "sources": ["84000-kangyur"],
            },
            {
                "taisho_id": "T08n0235",
                "tohoku": 3790,  # Tengyur
                "taisho_sanskrit": "Vajracchedikā",
                "kangyur_sanskrit": "Vajracchedikāṭīkā",
                "match_type": "fuzzy",
                "match_score": 0.92,
                "sources": ["84000-tengyur"],
            },
        ]
        annotate_section_preference(matches)
        assert matches[0].get("section_demoted") is None
        assert matches[1]["section_demoted"] is True

    def test_tengyur_only_not_demoted(self):
        """If a sūtra text only has Tengyur matches, don't demote."""
        matches = [
            {
                "taisho_id": "T08n0235",
                "tohoku": 3790,  # Tengyur only
                "taisho_sanskrit": "Vajracchedikā",
                "kangyur_sanskrit": "Vajracchedikāṭīkā",
                "match_type": "fuzzy",
                "match_score": 0.92,
                "sources": ["84000-tengyur"],
            },
        ]
        annotate_section_preference(matches)
        assert matches[0].get("section_demoted") is None

    def test_sastra_section_not_affected(self):
        """Śāstra texts (vol 25-32) should not get annotation."""
        matches = [
            {
                "taisho_id": "T25n1509",
                "tohoku": 100,  # Kangyur
                "taisho_sanskrit": "Title",
                "kangyur_sanskrit": "Title",
                "match_type": "exact",
                "match_score": 1.0,
                "sources": ["84000-kangyur"],
            },
            {
                "taisho_id": "T25n1509",
                "tohoku": 3800,  # Tengyur
                "taisho_sanskrit": "Title",
                "kangyur_sanskrit": "Title",
                "match_type": "fuzzy",
                "match_score": 0.92,
                "sources": ["84000-tengyur"],
            },
        ]
        annotate_section_preference(matches)
        assert matches[0].get("section_demoted") is None
        assert matches[1].get("section_demoted") is None


# ---------------------------------------------------------------------------
# Integration: validate against real concordance
# ---------------------------------------------------------------------------


class TestConcordanceIntegration:
    """Integration tests using real data files (if available)."""

    @pytest.fixture
    def real_data(self):
        """Load real data, skip if files not available."""
        try:
            from digest_detector.sanskrit_match import (
                load_taisho_sanskrit_titles,
                load_kangyur_sanskrit_titles,
                load_concordance,
            )
            taisho = load_taisho_sanskrit_titles()
            kangyur = load_kangyur_sanskrit_titles()
            concordance = load_concordance()
            if not taisho or not kangyur:
                pytest.skip("Data files not available")
            return taisho, kangyur, concordance
        except Exception:
            pytest.skip("Data files not available")

    def test_data_loads(self, real_data):
        taisho, kangyur, concordance = real_data
        assert len(taisho) > 700
        assert len(kangyur) > 5000
        assert len(concordance) > 600

    def test_heart_sutra_has_title(self, real_data):
        taisho, _, _ = real_data
        assert "T08n0250" in taisho
        titles = taisho["T08n0250"]
        assert any("hṛdaya" in t.lower() or "hrdaya" in t.lower()
                    for t in titles)

    def test_diamond_sutra_title_gap(self, real_data):
        """Diamond Sutra: 84000 uses abbreviated title 'Vajracchedikā' (Toh 16).

        Lancaster has 'Vajracchedikāprajñāpāramitāsūtra' -- much longer.
        This is a known gap: abbreviated Kangyur titles prevent matching.
        The CBETA Tibetan entry has the full form but it's already a concordance.
        """
        taisho, kangyur, _ = real_data
        assert "T08n0235" in taisho
        matches = find_matches(
            {"T08n0235": taisho["T08n0235"]},
            kangyur,
        )
        # Expect matches (possibly to CBETA Tibetan entries with negative Toh)
        # but not to the real Toh 16 (abbreviated title)
        toh_16_matches = [m for m in matches if m["tohoku"] == 16]
        assert len(toh_16_matches) == 0, (
            "Abbreviated '84000 Vajracchedikā' should NOT match full "
            "'Vajracchedikāprajñāpāramitāsūtra'"
        )

    def test_validation_rate_reasonable(self, real_data):
        """Validation rate should be meaningfully above random chance."""
        taisho, kangyur, concordance = real_data
        matches = find_matches(taisho, kangyur)
        real_matches = [m for m in matches if m["tohoku"] > 0]
        validated, contradicted, _, _ = validate_matches(real_matches, concordance)
        if validated or contradicted:
            rate = len(validated) / (len(validated) + len(contradicted))
            # Should be well above random chance (~70%+)
            assert rate > 0.7, f"Validation rate {rate:.1%} is suspiciously low"
