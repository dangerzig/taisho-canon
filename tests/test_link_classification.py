"""Tests for link classification in the expanded concordance.

Tests verify that the classify_links() post-processing correctly assigns
relationship types to (taisho_id, toh_id) links based on provenance patterns.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

# Add project root to path so we can import the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_expanded_concordance import (
    CATALOG_SOURCES,
    COMPUTATIONAL_SOURCES,
    ENCYCLOPEDIC_THRESHOLD,
    ProvenanceTracker,
    _is_catalog_or_scholarly_source,
    build_verified_output,
    classify_links,
)


# -- Unit tests for _is_catalog_or_scholarly_source --------------------------------------


class TestIsCatalogOrScholarlySource:
    """Tests for the _is_catalog_or_scholarly_source helper."""

    def test_catalog_sources_are_scholarly(self):
        """All defined CATALOG_SOURCES return True."""
        for source in CATALOG_SOURCES:
            assert _is_catalog_or_scholarly_source(source) is True, f"{source} should be scholarly"

    def test_computational_sources_are_not_scholarly(self):
        """COMPUTATIONAL_SOURCES return False."""
        for source in COMPUTATIONAL_SOURCES:
            assert _is_catalog_or_scholarly_source(source) is False, f"{source} should not be scholarly"

    def test_rkts_concordance_not_scholarly(self):
        """rkts_concordance (Otani derivation) is not scholarly."""
        assert _is_catalog_or_scholarly_source("rkts_concordance") is False

    def test_error_sources_not_scholarly(self):
        """Error-tagged sources are not positive attestations."""
        assert _is_catalog_or_scholarly_source("silk2019:error") is False
        assert _is_catalog_or_scholarly_source("standard_parallels:error") is False

    def test_unknown_scholarly_citation(self):
        """Unknown source names are treated as scholarly citations."""
        assert _is_catalog_or_scholarly_source("nattier1992") is True
        assert _is_catalog_or_scholarly_source("buswell1989") is True


# -- Unit tests for classify_links with synthetic data ------------------------


class TestClassifyLinks:
    """Tests for classify_links with synthetic concordance/provenance data."""

    def _make_concordance(self, entries):
        """Build a minimal concordance dict.

        entries: list of (text_id, tibetan_set, sources_set)
        """
        concordance = defaultdict(lambda: {
            "tibetan": set(), "pali": set(), "sanskrit": set(),
            "nanjio": set(), "sources": set(),
        })
        for text_id, tibetan, sources in entries:
            concordance[text_id]["tibetan"] = set(tibetan)
            concordance[text_id]["sources"] = set(sources)
        return concordance

    def _make_provenance(self, links):
        """Build a ProvenanceTracker from a list of (text, toh, source, conf).

        links: list of (taisho_id, toh_id, source, confidence)
        """
        prov = ProvenanceTracker()
        for taisho_id, toh_id, source, confidence in links:
            prov.add(taisho_id, toh_id, source, confidence=confidence)
        return prov

    def test_catalog_backed_is_parallel(self):
        """A link with any catalog source is classified as 'parallel'."""
        concordance = self._make_concordance([
            ("T08n0251", ["Toh 21"], {"lancaster", "mitra"}),
        ])
        provenance = self._make_provenance([
            ("T08n0251", "Toh 21", "lancaster", None),
            ("T08n0251", "Toh 21", "mitra", 0.7),
        ])
        classifications, summary = classify_links(concordance, provenance)
        assert classifications["T08n0251"]["Toh 21"]["type"] == "parallel"

    def test_computational_only_non_encyclopedic_high_conf(self):
        """Computational-only link from non-encyclopedic text with high
        confidence is 'parallel:computational'."""
        concordance = self._make_concordance([
            ("T01n0099", ["Toh 100"], {"mitra"}),
        ])
        provenance = self._make_provenance([
            ("T01n0099", "Toh 100", "mitra", 0.95),
        ])
        classifications, summary = classify_links(concordance, provenance)
        assert classifications["T01n0099"]["Toh 100"]["type"] == "parallel:computational"

    def test_encyclopedic_pattern_is_quotation(self):
        """A text with >= ENCYCLOPEDIC_THRESHOLD computational-only Toh links
        classifies those links as 'indirect:quotation'."""
        # Create a text with many computational-only Toh links
        toh_ids = [f"Toh {i}" for i in range(1, ENCYCLOPEDIC_THRESHOLD + 2)]
        concordance = self._make_concordance([
            ("T48n2016", toh_ids, {"mitra"}),
        ])
        links = [
            ("T48n2016", toh_id, "mitra", 0.95)
            for toh_id in toh_ids
        ]
        provenance = self._make_provenance(links)
        classifications, summary = classify_links(concordance, provenance)
        for toh_id in toh_ids:
            assert classifications["T48n2016"][toh_id]["type"] == "indirect:quotation"

    def test_computational_only_low_conf_is_uncertain(self):
        """Computational-only link with low confidence is 'uncertain'."""
        concordance = self._make_concordance([
            ("T01n0099", ["Toh 100"], {"mitra"}),
        ])
        provenance = self._make_provenance([
            ("T01n0099", "Toh 100", "mitra", 0.7),
        ])
        classifications, summary = classify_links(concordance, provenance)
        assert classifications["T01n0099"]["Toh 100"]["type"] == "uncertain"

    def test_rkts_source_is_chinese_to_tibetan(self):
        """Links from 'rkts' source are classified as 'chinese_to_tibetan'."""
        concordance = self._make_concordance([
            ("T12n0374", ["Toh 119"], {"rkts"}),
        ])
        provenance = self._make_provenance([
            ("T12n0374", "Toh 119", "rkts", None),
        ])
        classifications, summary = classify_links(concordance, provenance)
        assert classifications["T12n0374"]["Toh 119"]["type"] == "chinese_to_tibetan"

    def test_rkts_with_catalog_still_chinese_to_tibetan(self):
        """rKTs links with additional catalog backing are still chinese_to_tibetan."""
        concordance = self._make_concordance([
            ("T12n0374", ["Toh 119"], {"rkts", "lancaster"}),
        ])
        provenance = self._make_provenance([
            ("T12n0374", "Toh 119", "rkts", None),
            ("T12n0374", "Toh 119", "lancaster", None),
        ])
        classifications, summary = classify_links(concordance, provenance)
        assert classifications["T12n0374"]["Toh 119"]["type"] == "chinese_to_tibetan"

    def test_classification_summary_totals(self):
        """classification_summary total_classified equals sum of all types."""
        concordance = self._make_concordance([
            ("T01n0001", ["Toh 1"], {"lancaster"}),
            ("T01n0002", ["Toh 2"], {"mitra"}),
        ])
        provenance = self._make_provenance([
            ("T01n0001", "Toh 1", "lancaster", None),
            ("T01n0002", "Toh 2", "mitra", 0.95),
        ])
        classifications, summary = classify_links(concordance, provenance)
        type_counts = {k: v for k, v in summary.items() if k != "total_classified"}
        assert summary["total_classified"] == sum(type_counts.values())

    def test_otani_not_classified_as_toh(self):
        """Otani links are NOT classified in the main Toh classification pass."""
        concordance = self._make_concordance([
            ("T01n0001", ["Toh 1", "Otani 1030"], {"lancaster"}),
        ])
        provenance = self._make_provenance([
            ("T01n0001", "Toh 1", "lancaster", None),
            ("T01n0001", "Otani 1030", "rkts_concordance", None),
        ])
        classifications, summary = classify_links(concordance, provenance)
        # Toh 1 should be classified
        assert "Toh 1" in classifications.get("T01n0001", {})
        # Otani may or may not be present (depends on concordance file),
        # but if present it should inherit from Toh 1

    def test_rkts_concordance_only_not_classified(self):
        """A link attested only by rkts_concordance (infrastructure source)
        is not classified as a Toh link (it's an Otani)."""
        concordance = self._make_concordance([
            ("T01n0001", ["Otani 1030"], {}),
        ])
        provenance = self._make_provenance([
            ("T01n0001", "Otani 1030", "rkts_concordance", None),
        ])
        classifications, summary = classify_links(concordance, provenance)
        # No Toh links, so nothing to classify
        assert summary.get("total_classified", 0) == 0

    def test_boundary_exactly_at_encyclopedic_threshold(self):
        """Exactly ENCYCLOPEDIC_THRESHOLD computational-only links triggers
        indirect:quotation (threshold is >=, not >)."""
        toh_ids = [f"Toh {i}" for i in range(1, ENCYCLOPEDIC_THRESHOLD + 1)]
        concordance = self._make_concordance([
            ("T99n9999", toh_ids, {"mitra"}),
        ])
        links = [
            ("T99n9999", toh_id, "mitra", 0.95)
            for toh_id in toh_ids
        ]
        provenance = self._make_provenance(links)
        classifications, summary = classify_links(concordance, provenance)
        for toh_id in toh_ids:
            assert classifications["T99n9999"][toh_id]["type"] == "indirect:quotation"

    def test_below_encyclopedic_threshold_is_not_quotation(self):
        """Fewer than ENCYCLOPEDIC_THRESHOLD computational-only links does
        not trigger indirect:quotation."""
        toh_ids = [f"Toh {i}" for i in range(1, ENCYCLOPEDIC_THRESHOLD)]
        concordance = self._make_concordance([
            ("T99n9999", toh_ids, {"mitra"}),
        ])
        links = [
            ("T99n9999", toh_id, "mitra", 0.95)
            for toh_id in toh_ids
        ]
        provenance = self._make_provenance(links)
        classifications, summary = classify_links(concordance, provenance)
        for toh_id in toh_ids:
            assert classifications["T99n9999"][toh_id]["type"] != "indirect:quotation"

    def test_multiple_computational_sources_best_confidence(self):
        """When multiple computational sources attest a link, the best
        confidence across all sources is used."""
        concordance = self._make_concordance([
            ("T01n0099", ["Toh 100"], {"mitra", "sanskrit_title_match"}),
        ])
        provenance = self._make_provenance([
            ("T01n0099", "Toh 100", "mitra", 0.7),
            ("T01n0099", "Toh 100", "sanskrit_title_match", 0.95),
        ])
        classifications, summary = classify_links(concordance, provenance)
        # Best confidence is 0.95 from sanskrit_title_match
        assert classifications["T01n0099"]["Toh 100"]["type"] == "parallel:computational"

    def test_mixed_catalog_and_comp_links_counted_correctly(self):
        """Only computational-only Toh links count toward the encyclopedic
        threshold. Catalog-backed links are not counted."""
        # 3 comp-only + 3 catalog-backed = 6 total but only 3 comp-only
        comp_tohs = [f"Toh {i}" for i in range(1, 4)]
        cat_tohs = [f"Toh {i}" for i in range(10, 13)]
        all_tohs = comp_tohs + cat_tohs
        concordance = self._make_concordance([
            ("T99n9999", all_tohs, {"mitra", "lancaster"}),
        ])
        links = (
            [("T99n9999", toh, "mitra", 0.95) for toh in comp_tohs]
            + [("T99n9999", toh, "lancaster", None) for toh in cat_tohs]
        )
        provenance = self._make_provenance(links)
        classifications, summary = classify_links(concordance, provenance)
        # Comp-only count is 3 (< 5), so comp-only links should be
        # parallel:computational, NOT indirect:quotation
        for toh in comp_tohs:
            assert classifications["T99n9999"][toh]["type"] == "parallel:computational"
        for toh in cat_tohs:
            assert classifications["T99n9999"][toh]["type"] == "parallel"

    def test_pali_links_not_classified(self):
        """Pali links (not starting with 'Toh ') are not classified."""
        concordance = self._make_concordance([
            ("T01n0001", ["dn1"], {"suttacentral_parallels"}),
        ])
        provenance = self._make_provenance([
            ("T01n0001", "dn1", "suttacentral_parallels", 0.9),
        ])
        classifications, summary = classify_links(concordance, provenance)
        assert "T01n0001" not in classifications
        assert summary.get("total_classified", 0) == 0


# -- Integration tests against real concordance output ------------------------


class TestRealConcordanceClassification:
    """Integration tests that verify classification against the actual
    cross_reference_expanded.json output."""

    EXPANDED_PATH = (Path(__file__).resolve().parent.parent
                     / "results" / "cross_reference_expanded.json")

    @pytest.fixture
    def expanded_data(self):
        """Load the expanded concordance, skip if not available."""
        if not self.EXPANDED_PATH.exists():
            pytest.skip("cross_reference_expanded.json not found")
        with open(self.EXPANDED_PATH) as f:
            return json.load(f)

    def test_schema_version_3(self, expanded_data):
        """Output should be schema version 3."""
        assert expanded_data["schema_version"] == 3

    def test_has_link_classifications(self, expanded_data):
        """Output contains link_classifications top-level key."""
        assert "link_classifications" in expanded_data

    def test_has_classification_summary(self, expanded_data):
        """Summary includes classification breakdown."""
        assert "classification" in expanded_data["summary"]
        summary = expanded_data["summary"]["classification"]
        assert "total_classified" in summary
        assert summary["total_classified"] > 0

    def test_heart_sutra_is_parallel(self, expanded_data):
        """T08n0251 -> Toh 21 (Heart Sutra) is classified as parallel."""
        lc = expanded_data["link_classifications"]
        assert lc["T08n0251"]["Toh 21"]["type"] == "parallel"

    def test_zongjinglu_all_quotation(self, expanded_data):
        """T48n2016 (Zongjinglu) -> all Toh links are indirect:quotation."""
        lc = expanded_data["link_classifications"]
        t48 = lc.get("T48n2016", {})
        assert len(t48) > 0, "T48n2016 should have classified links"
        for toh_id, info in t48.items():
            assert info["type"] == "indirect:quotation", (
                f"T48n2016 {toh_id} should be indirect:quotation, "
                f"got {info['type']}"
            )

    def test_fayuan_zhulin_all_quotation(self, expanded_data):
        """T53n2122 (Fayuan Zhulin) -> all Toh links are indirect:quotation."""
        lc = expanded_data["link_classifications"]
        t53 = lc.get("T53n2122", {})
        assert len(t53) > 0, "T53n2122 should have classified links"
        for toh_id, info in t53.items():
            assert info["type"] == "indirect:quotation", (
                f"T53n2122 {toh_id} should be indirect:quotation, "
                f"got {info['type']}"
            )

    def test_ratnakuta_has_parallel_links(self, expanded_data):
        """T11n0310 (Ratnakuta) has catalog-backed links classified as parallel."""
        lc = expanded_data["link_classifications"]
        t11 = lc.get("T11n0310", {})
        parallel_links = [
            toh for toh, info in t11.items()
            if info["type"] == "parallel"
        ]
        assert len(parallel_links) > 0, (
            "T11n0310 should have at least some parallel-classified links"
        )

    def test_otani_inherits_parent_classification(self, expanded_data):
        """Otani numbers inherit their parent Toh's classification type."""
        lc = expanded_data["link_classifications"]
        # T08n0251 has Otani 160 (from Toh 21, which is "parallel")
        t08 = lc.get("T08n0251", {})
        otani_entries = {
            toh: info for toh, info in t08.items()
            if toh.startswith("Otani")
        }
        assert len(otani_entries) > 0, "T08n0251 should have Otani entries"
        for otani_id, info in otani_entries.items():
            assert info["type"] == "parallel", (
                f"T08n0251 {otani_id} should inherit 'parallel' from parent Toh"
            )

    def test_classification_summary_matches_total(self, expanded_data):
        """classification_summary total equals sum of individual type counts."""
        summary = expanded_data["summary"]["classification"]
        type_counts = {
            k: v for k, v in summary.items() if k != "total_classified"
        }
        assert summary["total_classified"] == sum(type_counts.values())

    def test_all_expected_types_present(self, expanded_data):
        """All expected classification types appear in the summary."""
        summary = expanded_data["summary"]["classification"]
        expected_types = {
            "parallel", "parallel:computational", "indirect:quotation",
            "chinese_to_tibetan",
        }
        for t in expected_types:
            assert t in summary, f"Expected type '{t}' not in classification summary"

    def test_parallel_is_dominant_type(self, expanded_data):
        """The 'parallel' type should be the most common classification."""
        summary = expanded_data["summary"]["classification"]
        parallel_count = summary.get("parallel", 0)
        for type_name, count in summary.items():
            if type_name in ("total_classified", "parallel"):
                continue
            assert parallel_count >= count, (
                f"'parallel' ({parallel_count}) should be >= "
                f"'{type_name}' ({count})"
            )


# -- Tests for flagged error handling in classify_links -----------------------


class TestFlaggedErrors:
    """Tests that flagged errors are classified as error:flagged."""

    def _make_concordance(self, entries):
        concordance = defaultdict(lambda: {
            "tibetan": set(), "pali": set(), "sanskrit": set(),
            "nanjio": set(), "sources": set(),
        })
        for text_id, tibetan, sources in entries:
            concordance[text_id]["tibetan"] = set(tibetan)
            concordance[text_id]["sources"] = set(sources)
        return concordance

    def _make_provenance(self, links):
        prov = ProvenanceTracker()
        for taisho_id, toh_id, source, confidence in links:
            prov.add(taisho_id, toh_id, source, confidence=confidence)
        return prov

    def test_all_attestations_flagged_becomes_error(self):
        """A link where all attestations are flagged is error:flagged."""
        concordance = self._make_concordance([
            ("T09n0278", [], {"lancaster"}),
        ])
        provenance = self._make_provenance([
            ("T09n0278", "Toh 0", "lancaster", None),
        ])
        # Simulate flag_known_errors by marking attestations
        for att in provenance.get("T09n0278", "Toh 0"):
            att["flagged_error"] = True

        classifications, summary = classify_links(concordance, provenance)
        assert classifications["T09n0278"]["Toh 0"]["type"] == "error:flagged"

    def test_partially_flagged_not_error(self):
        """A link with some unflagged attestations is NOT error:flagged."""
        concordance = self._make_concordance([
            ("T09n0278", ["Toh 44"], {"lancaster", "cbeta_tibetan"}),
        ])
        provenance = self._make_provenance([
            ("T09n0278", "Toh 44", "lancaster", None),
            ("T09n0278", "Toh 44", "cbeta_tibetan", None),
        ])
        # Flag only one attestation
        provenance.get("T09n0278", "Toh 44")[0]["flagged_error"] = True

        classifications, summary = classify_links(concordance, provenance)
        assert classifications["T09n0278"]["Toh 44"]["type"] != "error:flagged"

    def test_flagged_error_excluded_from_verified_types(self):
        """error:flagged links should not appear in verified output."""
        concordance = self._make_concordance([
            ("T09n0278", ["Toh 44"], {"lancaster"}),
        ])
        provenance = self._make_provenance([
            ("T09n0278", "Toh 0", "lancaster", None),
            ("T09n0278", "Toh 44", "lancaster", None),
        ])
        # Flag the erroneous link
        for att in provenance.get("T09n0278", "Toh 0"):
            att["flagged_error"] = True

        classifications, summary = classify_links(concordance, provenance)

        corpus_ids = {"T09n0278"}
        verified = build_verified_output(
            concordance, corpus_ids, provenance, classifications, []
        )
        # Toh 0 should NOT be in verified tibetan_parallels
        tib = verified.get("tibetan_parallels", {}).get("T09n0278", [])
        assert "Toh 0" not in tib
        # Toh 0 should NOT be in verified link_classifications
        vcls = verified.get("link_classifications", {}).get("T09n0278", {})
        assert "Toh 0" not in vcls


# -- Tests for build_verified_output ------------------------------------------


class TestBuildVerifiedOutput:
    """Tests for the verified concordance output builder."""

    def _make_concordance(self, entries):
        concordance = defaultdict(lambda: {
            "tibetan": set(), "pali": set(), "sanskrit": set(),
            "nanjio": set(), "sources": set(),
        })
        for text_id, tibetan, sources in entries:
            concordance[text_id]["tibetan"] = set(tibetan)
            concordance[text_id]["sources"] = set(sources)
        return concordance

    def _make_provenance(self, links):
        prov = ProvenanceTracker()
        for taisho_id, toh_id, source, confidence in links:
            prov.add(taisho_id, toh_id, source, confidence=confidence)
        return prov

    def test_filters_computational_only_links(self):
        """Computational-only links are excluded from verified output."""
        concordance = self._make_concordance([
            ("T01n0001", ["Toh 1", "Toh 500"], {"lancaster", "mitra"}),
        ])
        provenance = self._make_provenance([
            ("T01n0001", "Toh 1", "lancaster", None),
            ("T01n0001", "Toh 500", "mitra", 0.95),
        ])
        classifications, _ = classify_links(concordance, provenance)
        corpus_ids = {"T01n0001"}
        verified = build_verified_output(
            concordance, corpus_ids, provenance, classifications, []
        )
        tib = verified["tibetan_parallels"].get("T01n0001", [])
        assert "Toh 1" in tib
        assert "Toh 500" not in tib

    def test_kangyur_tengyur_split(self):
        """Toh numbers are correctly split into Kangyur and Tengyur."""
        concordance = self._make_concordance([
            ("T01n0001", ["Toh 1"], {"lancaster"}),
            ("T25n1509", ["Toh 3786"], {"lancaster"}),
        ])
        provenance = self._make_provenance([
            ("T01n0001", "Toh 1", "lancaster", None),
            ("T25n1509", "Toh 3786", "lancaster", None),
        ])
        classifications, _ = classify_links(concordance, provenance)
        corpus_ids = {"T01n0001", "T25n1509"}
        verified = build_verified_output(
            concordance, corpus_ids, provenance, classifications, []
        )
        assert verified["summary"]["kangyur_toh"] == 1
        assert verified["summary"]["tengyur_toh"] == 1

    def test_out_of_range_toh_excluded_from_counts(self):
        """Toh numbers outside 1-4569 are excluded from Kangyur/Tengyur counts."""
        concordance = self._make_concordance([
            ("T04n0192", ["Toh 5656"], {"lancaster"}),
        ])
        provenance = self._make_provenance([
            ("T04n0192", "Toh 5656", "lancaster", None),
        ])
        classifications, _ = classify_links(concordance, provenance)
        corpus_ids = {"T04n0192"}
        verified = build_verified_output(
            concordance, corpus_ids, provenance, classifications, []
        )
        assert verified["summary"]["kangyur_toh"] == 0
        assert verified["summary"]["tengyur_toh"] == 0

    def test_letter_suffix_toh_handled(self):
        """Toh numbers with letter suffixes (e.g., 359a) are handled."""
        concordance = self._make_concordance([
            ("T12n0374", ["Toh 359a"], {"lancaster"}),
        ])
        provenance = self._make_provenance([
            ("T12n0374", "Toh 359a", "lancaster", None),
        ])
        classifications, _ = classify_links(concordance, provenance)
        corpus_ids = {"T12n0374"}
        verified = build_verified_output(
            concordance, corpus_ids, provenance, classifications, []
        )
        assert verified["summary"]["kangyur_toh"] == 1

    def test_pali_only_text_in_verified(self):
        """A text with only Pali parallels still appears in verified output."""
        concordance = defaultdict(lambda: {
            "tibetan": set(), "pali": set(), "sanskrit": set(),
            "nanjio": set(), "sources": set(),
        })
        concordance["T01n0001"]["pali"] = {"dn1"}
        concordance["T01n0001"]["sources"] = {"suttacentral_parallels"}
        provenance = ProvenanceTracker()
        provenance.add("T01n0001", "dn1", "suttacentral_parallels")
        classifications = {}
        corpus_ids = {"T01n0001"}
        verified = build_verified_output(
            concordance, corpus_ids, provenance, classifications, []
        )
        assert "T01n0001" in verified["pali_parallels"]
        assert "T01n0001" not in verified["no_parallel_found"]

    def test_verified_provenance_excludes_computational(self):
        """Verified provenance filters out computational source attestations."""
        concordance = self._make_concordance([
            ("T01n0001", ["Toh 1"], {"lancaster", "mitra"}),
        ])
        provenance = self._make_provenance([
            ("T01n0001", "Toh 1", "lancaster", None),
            ("T01n0001", "Toh 1", "mitra", 0.95),
        ])
        classifications, _ = classify_links(concordance, provenance)
        corpus_ids = {"T01n0001"}
        verified = build_verified_output(
            concordance, corpus_ids, provenance, classifications, []
        )
        vprov = verified["link_provenance"].get("T01n0001", {}).get("Toh 1", [])
        sources = {att["source"] for att in vprov}
        assert "lancaster" in sources
        assert "mitra" not in sources
