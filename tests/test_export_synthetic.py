"""Synthetic tests for export modules and _export_common utilities.

Tests build_tei and CSV export logic with minimal synthetic data,
independent of pipeline output files.
"""

import csv
import io
import json
import tempfile
from collections import defaultdict
from pathlib import Path
from xml.etree.ElementTree import indent

import pytest

from digest_detector._export_common import (
    build_number_to_id,
    load_json,
    resolve_taisho,
)
from digest_detector.export_tei import build_tei, cert_from_count, toh_to_target

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"


# ---- Fixtures ----

@pytest.fixture
def synthetic_expanded():
    """Minimal concordance data for testing."""
    return {
        "tibetan_parallels": {
            "T01n0001": ["Toh 1", "Otani 1"],
            "T08n0250": ["Toh 21", "Toh 22"],
        },
        "pali_parallels": {
            "T01n0001": ["dn1", "dn2"],
            "T02n0099": ["sn12.1"],
        },
        "sanskrit_parallels": {
            "T08n0250": ["Prajnaparamitahrdaya"],
            "T15n0600": ["Vimalakirtinirdesa"],
        },
        "no_parallel_found": ["T99n9999"],
        "summary": {
            "total_texts": 5,
            "with_tibetan": 2,
            "with_any_parallel": 4,
            "pct_tibetan": 40.0,
            "pct_any": 80.0,
        },
    }


@pytest.fixture
def synthetic_provenance():
    prov = defaultdict(set)
    prov[("T01n0001", "Toh 1")] = {"lancaster", "existing"}
    prov[("T08n0250", "Toh 21")] = {"cbeta_sanskrit", "cbeta_tibetan", "lancaster"}
    prov[("T08n0250", "Toh 22")] = {"acmuller"}
    prov[("T01n0001", "Otani 1")] = {"rkts_concordance"}
    prov[("T01n0001", "dn1")] = {"suttacentral_parallels"}
    prov[("T01n0001", "dn2")] = {"suttacentral_parallels"}
    prov[("T02n0099", "sn12.1")] = {"suttacentral_parallels"}
    return prov


@pytest.fixture
def synthetic_titles():
    titles = defaultdict(lambda: {
        "chinese_title": "",
        "sanskrit_title": "",
        "tibetan_title": "",
    })
    titles["T01n0001"]["chinese_title"] = "長阿含經"
    titles["T08n0250"]["chinese_title"] = "般若波羅蜜多心經"
    titles["T08n0250"]["sanskrit_title"] = "Prajnaparamitahrdaya"
    return titles


@pytest.fixture
def synthetic_nanjio():
    nj = defaultdict(set)
    nj["T01n0001"] = {"Nj 545", "Nj 546"}
    return nj


@pytest.fixture
def synthetic_otani():
    ot = defaultdict(set)
    ot["T01n0001"] = {"Otani 1"}
    return ot


# ---- _export_common tests ----

class TestLoadJson:
    def test_existing_file(self, tmp_path):
        p = tmp_path / "test.json"
        p.write_text('{"key": "value"}', encoding="utf-8")
        result = load_json(p)
        assert result == {"key": "value"}

    def test_missing_file(self, tmp_path):
        p = tmp_path / "nonexistent.json"
        assert load_json(p) is None

    def test_unicode_content(self, tmp_path):
        p = tmp_path / "unicode.json"
        p.write_text('{"title": "般若波羅蜜多心經"}', encoding="utf-8")
        result = load_json(p)
        assert result["title"] == "般若波羅蜜多心經"


class TestBuildNumberToId:
    def test_basic_mapping(self):
        ids = ["T01n0001", "T08n0250", "T08n0251"]
        mapping = build_number_to_id(ids)
        assert mapping[1] == "T01n0001"
        assert mapping[250] == "T08n0250"
        assert mapping[251] == "T08n0251"

    def test_first_occurrence_wins(self):
        ids = ["T05n0220", "T06n0220", "T07n0220"]
        mapping = build_number_to_id(ids)
        assert mapping[220] == "T05n0220"

    def test_suffixed_ids(self):
        ids = ["T32n1670A", "T32n1670B"]
        mapping = build_number_to_id(ids)
        assert mapping[1670] == "T32n1670A"


class TestResolveTaisho:
    def test_canonical_id(self):
        valid = {"T08n0250", "T08n0251"}
        num_to_id = {250: "T08n0250", 251: "T08n0251"}
        assert resolve_taisho("T08n0250", num_to_id, valid) == "T08n0250"

    def test_bare_number(self):
        valid = {"T08n0250"}
        num_to_id = {250: "T08n0250"}
        assert resolve_taisho("T250", num_to_id, valid) == "T08n0250"

    def test_unknown_returns_none(self):
        assert resolve_taisho("T99999", {}, set()) is None

    def test_suffix_stripping(self):
        valid = {"T19n0974"}
        num_to_id = {}
        assert resolve_taisho("T19n0974A", num_to_id, valid) == "T19n0974"


class TestCertFromCount:
    def test_values(self):
        assert cert_from_count(1) == "low"
        assert cert_from_count(2) == "medium"
        assert cert_from_count(3) == "high"
        assert cert_from_count(10) == "high"


class TestTohToTarget:
    def test_space_replacement(self):
        assert toh_to_target("Toh 21") == "Toh_21"
        assert toh_to_target("Toh 1108") == "Toh_1108"


# ---- TEI export tests ----

class TestBuildTeiSynthetic:
    def test_entry_count(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        """TEI should have one entry per unique Taisho ID with any parallel."""
        tree, entry_count, _ = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
        )
        # IDs with parallels: T01n0001 (tib+pali), T08n0250 (tib+skt),
        # T02n0099 (pali), T15n0600 (skt) = 4
        assert entry_count == 4

    def test_tibetan_links(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        tree, _, link_count = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
        )
        root = tree.getroot()
        entries = {
            e.get(f"{{{XML_NS}}}id"): e
            for e in root.iter("entry")
        }

        # T08n0250 should have Toh 21 and Toh 22
        e250 = entries["T08n0250"]
        toh_links = [
            l.get("target") for l in e250.findall("link")
            if l.get("type") == "tibetan"
        ]
        assert "Toh_21" in toh_links
        assert "Toh_22" in toh_links

    def test_certainty_from_provenance(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        tree, _, _ = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
        )
        root = tree.getroot()
        entries = {
            e.get(f"{{{XML_NS}}}id"): e
            for e in root.iter("entry")
        }

        # T08n0250's Toh 21 has 3 sources → high
        e250 = entries["T08n0250"]
        toh21 = [
            l for l in e250.findall("link")
            if l.get("target") == "Toh_21"
        ]
        assert len(toh21) == 1
        assert toh21[0].get("cert") == "high"

        # Toh 22 has 1 source → low
        toh22 = [
            l for l in e250.findall("link")
            if l.get("target") == "Toh_22"
        ]
        assert len(toh22) == 1
        assert toh22[0].get("cert") == "low"

    def test_sanskrit_idno(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        tree, _, _ = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
        )
        root = tree.getroot()
        entries = {
            e.get(f"{{{XML_NS}}}id"): e
            for e in root.iter("entry")
        }

        # T08n0250 should have Sanskrit idno
        e250 = entries["T08n0250"]
        skt = [
            i.text for i in e250.findall("idno")
            if i.get("type") == "sanskrit"
        ]
        assert "Prajnaparamitahrdaya" in skt

    def test_pali_links(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        tree, _, _ = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
        )
        root = tree.getroot()
        entries = {
            e.get(f"{{{XML_NS}}}id"): e
            for e in root.iter("entry")
        }

        # T01n0001 has dn1, dn2
        e001 = entries["T01n0001"]
        pali = [
            l.get("target") for l in e001.findall("link")
            if l.get("type") == "pali"
        ]
        assert "dn1" in pali
        assert "dn2" in pali

    def test_error_pairs_excluded(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        """Known error pairs should be excluded from TEI output."""
        error_pairs = {("T01n0001", "Toh 1")}
        tree, _, _ = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
            error_pairs=error_pairs,
        )
        root = tree.getroot()
        entries = {
            e.get(f"{{{XML_NS}}}id"): e
            for e in root.iter("entry")
        }

        e001 = entries["T01n0001"]
        toh_links = [
            l.get("target") for l in e001.findall("link")
            if l.get("type") == "tibetan"
        ]
        assert "Toh_1" not in toh_links

    def test_no_parallel_texts_excluded(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        """Texts with no parallels should NOT appear in TEI."""
        tree, _, _ = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
        )
        root = tree.getroot()
        ids = {
            e.get(f"{{{XML_NS}}}id")
            for e in root.iter("entry")
        }
        assert "T99n9999" not in ids

    def test_nanjio_numbers(
        self, synthetic_expanded, synthetic_provenance,
        synthetic_titles, synthetic_nanjio, synthetic_otani,
    ):
        tree, _, _ = build_tei(
            synthetic_expanded, synthetic_provenance,
            synthetic_titles, synthetic_nanjio, synthetic_otani,
        )
        root = tree.getroot()
        entries = {
            e.get(f"{{{XML_NS}}}id"): e
            for e in root.iter("entry")
        }

        e001 = entries["T01n0001"]
        nj = [
            i.text for i in e001.findall("idno")
            if i.get("type") == "nanjio"
        ]
        assert "Nj 545" in nj
        assert "Nj 546" in nj
