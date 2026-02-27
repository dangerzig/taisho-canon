"""Tests for export_csv.py and export_tei.py: cross-checks against JSON and each other."""

import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
JSON_PATH = RESULTS_DIR / "cross_reference_expanded.json"
CSV_PATH = RESULTS_DIR / "cross_reference.csv"
TEI_PATH = RESULTS_DIR / "cross_reference.tei.xml"

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI_NS}


# ---- Fixtures ----

@pytest.fixture(scope="module")
def json_data():
    """Load the expanded concordance JSON."""
    if not JSON_PATH.exists():
        pytest.skip("cross_reference_expanded.json not found")
    with open(JSON_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def csv_rows():
    """Load all CSV rows as list of dicts."""
    if not CSV_PATH.exists():
        pytest.skip("cross_reference.csv not found")
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


@pytest.fixture(scope="module")
def tei_tree():
    """Parse the TEI XML file."""
    if not TEI_PATH.exists():
        pytest.skip("cross_reference.tei.xml not found")
    return ET.parse(TEI_PATH)


@pytest.fixture(scope="module")
def json_all_ids(json_data):
    """Set of all Taisho IDs with any parallel in the JSON."""
    ids = set()
    for section in ("tibetan_parallels", "pali_parallels", "sanskrit_parallels"):
        ids.update(json_data.get(section, {}).keys())
    return ids


@pytest.fixture(scope="module")
def csv_taisho_ids(csv_rows):
    """Set of unique Taisho IDs in the CSV."""
    return set(r["taisho_id"] for r in csv_rows)


@pytest.fixture(scope="module")
def tei_entries(tei_tree):
    """List of <entry> elements from the TEI."""
    root = tei_tree.getroot()
    return root.findall(f".//{{{TEI_NS}}}linkGrp/{{{TEI_NS}}}entry")


@pytest.fixture(scope="module")
def tei_taisho_ids(tei_entries):
    """Set of xml:id values from TEI entry elements."""
    return set(e.get(f"{{{XML_NS}}}id") for e in tei_entries)


@pytest.fixture(scope="module")
def tei_entry_map(tei_entries):
    """Map from taisho_id to <entry> element in the TEI."""
    return {e.get(f"{{{XML_NS}}}id"): e for e in tei_entries}


@pytest.fixture(scope="module")
def csv_rows_by_taisho(csv_rows):
    """Map from taisho_id to list of CSV rows for that text."""
    result = {}
    for r in csv_rows:
        result.setdefault(r["taisho_id"], []).append(r)
    return result


# ---- JSON: helper sets ----

@pytest.fixture(scope="module")
def json_tibetan_ids(json_data):
    return set(json_data.get("tibetan_parallels", {}).keys())


@pytest.fixture(scope="module")
def json_pali_ids(json_data):
    return set(json_data.get("pali_parallels", {}).keys())


@pytest.fixture(scope="module")
def json_sanskrit_ids(json_data):
    return set(json_data.get("sanskrit_parallels", {}).keys())


# ---- 1. Entry count ----

class TestEntryCountJSON:
    def test_tei_entry_count_matches_json(self, tei_taisho_ids, json_all_ids):
        """TEI should have one <entry> for each Taisho text with any parallel (954)."""
        assert len(tei_taisho_ids) == len(json_all_ids)

    def test_csv_covers_tibetan_and_pali(
        self, csv_taisho_ids, json_tibetan_ids, json_pali_ids,
    ):
        """CSV should include all texts with Tibetan or Pali parallels."""
        expected = json_tibetan_ids | json_pali_ids
        assert csv_taisho_ids == expected


# ---- 2. Tohoku completeness ----

class TestTohokuCompleteness:
    def test_csv_has_all_tohoku_from_json(self, json_data, csv_rows_by_taisho):
        """For each Taisho text in JSON that has Tohoku numbers, CSV should have them."""
        tibetan = json_data.get("tibetan_parallels", {})
        for taisho_id, parallels in tibetan.items():
            json_tohs = {p for p in parallels if p.startswith("Toh ")}
            if not json_tohs:
                continue
            csv_rows = csv_rows_by_taisho.get(taisho_id)
            assert csv_rows is not None, f"{taisho_id} missing from CSV"
            csv_tohs = {r["tohoku"] for r in csv_rows if r["tohoku"]}
            assert json_tohs == csv_tohs, (
                f"{taisho_id}: JSON Tohs {json_tohs} != CSV Tohs {csv_tohs}"
            )

    def test_tei_has_all_tohoku_from_json(self, json_data, tei_entry_map):
        """For each Taisho text in JSON with Tohoku numbers, TEI should have them."""
        tibetan = json_data.get("tibetan_parallels", {})
        for taisho_id, parallels in tibetan.items():
            json_tohs = {p for p in parallels if p.startswith("Toh ")}
            if not json_tohs:
                continue
            entry = tei_entry_map.get(taisho_id)
            assert entry is not None, f"{taisho_id} missing from TEI"
            # TEI target uses Toh_NNN format
            tei_tohs = set()
            for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
                target = link.get("target", "")
                if target.startswith("Toh_"):
                    tei_tohs.add(target.replace("_", " "))
            assert json_tohs == tei_tohs, (
                f"{taisho_id}: JSON Tohs {json_tohs} != TEI Tohs {tei_tohs}"
            )


# ---- 3. No phantom entries ----

class TestNoPhantomEntries:
    def test_csv_ids_subset_of_json(self, csv_taisho_ids, json_all_ids):
        """Every Taisho ID in CSV must exist in the JSON."""
        phantoms = csv_taisho_ids - json_all_ids
        assert phantoms == set(), f"Phantom CSV IDs: {phantoms}"

    def test_tei_ids_subset_of_json(self, tei_taisho_ids, json_all_ids):
        """Every Taisho ID in TEI must exist in the JSON."""
        phantoms = tei_taisho_ids - json_all_ids
        assert phantoms == set(), f"Phantom TEI IDs: {phantoms}"


# ---- 4. Pali parallels ----

class TestPaliParallels:
    def test_csv_has_pali_from_json(self, json_data, csv_rows_by_taisho):
        """Texts with Pali parallels in JSON should have them in CSV."""
        pali = json_data.get("pali_parallels", {})
        for taisho_id, pali_refs in pali.items():
            csv_rows = csv_rows_by_taisho.get(taisho_id)
            assert csv_rows is not None, f"{taisho_id} with Pali missing from CSV"
            # All rows for a given taisho_id have the same pali_parallel field
            csv_pali_str = csv_rows[0]["pali_parallel"]
            csv_pali_set = {p.strip() for p in csv_pali_str.split(";") if p.strip()}
            json_pali_set = set(pali_refs)
            assert json_pali_set == csv_pali_set, (
                f"{taisho_id}: JSON Pali {json_pali_set} != CSV Pali {csv_pali_set}"
            )

    def test_tei_has_pali_from_json(self, json_data, tei_entry_map):
        """Texts with Pali parallels in JSON should have pali links in TEI."""
        pali = json_data.get("pali_parallels", {})
        for taisho_id, pali_refs in pali.items():
            entry = tei_entry_map.get(taisho_id)
            assert entry is not None, f"{taisho_id} with Pali missing from TEI"
            tei_pali = set()
            for link in entry.findall(f"{{{TEI_NS}}}link[@type='pali']"):
                tei_pali.add(link.get("target"))
            json_pali_set = set(pali_refs)
            assert json_pali_set == tei_pali, (
                f"{taisho_id}: JSON Pali {json_pali_set} != TEI Pali {tei_pali}"
            )


# ---- 5. Otani/Nanjio spot checks ----

class TestOtaniNanjio:
    def test_csv_otani_for_t01n0001(self, csv_rows_by_taisho):
        """T01n0001 should have known Otani numbers in CSV."""
        rows = csv_rows_by_taisho.get("T01n0001")
        assert rows is not None
        otani_str = rows[0]["otani"]
        for ot in ("Otani 750", "Otani 879", "Otani 962", "Otani 997", "Otani 1021"):
            assert ot in otani_str, f"Missing {ot} for T01n0001 in CSV"

    def test_tei_otani_for_t01n0001(self, tei_entry_map):
        """T01n0001 should have known Otani numbers in TEI."""
        entry = tei_entry_map.get("T01n0001")
        assert entry is not None
        tei_otani = set()
        for idno in entry.findall(f"{{{TEI_NS}}}idno[@type='otani']"):
            tei_otani.add(idno.text)
        for ot in ("Otani 750", "Otani 879", "Otani 962", "Otani 997", "Otani 1021"):
            assert ot in tei_otani, f"Missing {ot} for T01n0001 in TEI"

    def test_csv_nanjio_for_t01n0001(self, csv_rows_by_taisho):
        """T01n0001 should have known Nanjio numbers in CSV."""
        rows = csv_rows_by_taisho.get("T01n0001")
        assert rows is not None
        nanjio_str = rows[0]["nanjio"]
        for nj in ("Nj 545", "Nj 546", "Nj 851"):
            assert nj in nanjio_str, f"Missing {nj} for T01n0001 in CSV"

    def test_tei_nanjio_for_t01n0001(self, tei_entry_map):
        """T01n0001 should have known Nanjio numbers in TEI."""
        entry = tei_entry_map.get("T01n0001")
        assert entry is not None
        tei_nanjio = set()
        for idno in entry.findall(f"{{{TEI_NS}}}idno[@type='nanjio']"):
            tei_nanjio.add(idno.text)
        for nj in ("Nj 545", "Nj 546", "Nj 851"):
            assert nj in tei_nanjio, f"Missing {nj} for T01n0001 in TEI"


# ---- 6. Same Taisho ID sets between CSV and TEI ----

class TestCSVTEITaishoSets:
    def test_csv_is_subset_of_tei(self, csv_taisho_ids, tei_taisho_ids):
        """All CSV Taisho IDs should be present in TEI."""
        missing = csv_taisho_ids - tei_taisho_ids
        assert missing == set(), f"CSV IDs missing from TEI: {missing}"

    def test_tei_minus_csv_is_sanskrit_only(
        self, csv_taisho_ids, tei_taisho_ids,
        json_tibetan_ids, json_pali_ids, json_sanskrit_ids,
    ):
        """TEI IDs not in CSV should be texts with only Sanskrit parallels."""
        tei_only = tei_taisho_ids - csv_taisho_ids
        sanskrit_only = json_sanskrit_ids - json_tibetan_ids - json_pali_ids
        assert tei_only == sanskrit_only


# ---- 7. Same Tohoku mappings between CSV and TEI ----

class TestCSVTEITohokuMappings:
    def test_tohoku_sets_agree(self, csv_rows_by_taisho, tei_entry_map):
        """For texts in both CSV and TEI, Tohoku number sets should be identical."""
        for taisho_id, rows in csv_rows_by_taisho.items():
            csv_tohs = {r["tohoku"] for r in rows if r["tohoku"]}

            entry = tei_entry_map.get(taisho_id)
            if entry is None:
                continue  # sanskrit-only texts may not be in CSV but should be in TEI
            tei_tohs = set()
            for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
                target = link.get("target", "")
                if target.startswith("Toh_"):
                    tei_tohs.add(target.replace("_", " "))
            assert csv_tohs == tei_tohs, (
                f"{taisho_id}: CSV Tohs {csv_tohs} != TEI Tohs {tei_tohs}"
            )


# ---- 8. Source counts agree ----

class TestSourceCountsAgree:
    def test_csv_source_count_matches_sources_field(self, csv_rows):
        """CSV source_count should match the number of sources listed in the sources field."""
        for i, row in enumerate(csv_rows):
            count = int(row["source_count"])
            if row["sources"]:
                sources_list = row["sources"].split("; ")
                assert count == len(sources_list), (
                    f"Row {i} ({row['taisho_id']} {row['tohoku']}): "
                    f"source_count={count} but sources has {len(sources_list)} entries"
                )
            else:
                assert count == 0, (
                    f"Row {i} ({row['taisho_id']} {row['tohoku']}): "
                    f"source_count={count} but sources is empty"
                )

    def test_tei_source_note_non_empty_when_cert_not_low(self, tei_entries):
        """TEI entries with cert != 'low' should have a non-empty source note."""
        for entry in tei_entries:
            xmlid = entry.get(f"{{{XML_NS}}}id")
            for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
                cert = link.get("cert")
                note = link.find(f"{{{TEI_NS}}}note[@type='sources']")
                if cert in ("high", "medium"):
                    assert note is not None and note.text, (
                        f"{xmlid} {link.get('target')}: cert={cert} but no sources"
                    )

    def test_csv_tei_source_counts_mostly_agree(self, csv_rows_by_taisho, tei_entry_map):
        """CSV and TEI source counts should agree for the vast majority of mappings.

        The two export scripts reconstruct provenance independently, so minor
        discrepancies are possible. This test ensures agreement exceeds 95%.
        """
        total = 0
        agree = 0
        for taisho_id, rows in csv_rows_by_taisho.items():
            entry = tei_entry_map.get(taisho_id)
            if entry is None:
                continue
            for row in rows:
                toh = row["tohoku"]
                if not toh:
                    continue
                csv_count = int(row["source_count"])
                tei_target = toh.replace(" ", "_")
                for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
                    if link.get("target") == tei_target:
                        note = link.find(f"{{{TEI_NS}}}note[@type='sources']")
                        if note is not None and note.text:
                            tei_count = len(note.text.split("; "))
                        else:
                            tei_count = 0
                        total += 1
                        if csv_count == tei_count:
                            agree += 1
                        break
        assert total > 0
        pct = agree / total
        assert pct >= 0.95, (
            f"Only {agree}/{total} ({pct:.1%}) source counts agree between CSV and TEI"
        )


# ---- 9. Certainty mapping ----

class TestCertaintyMapping:
    def test_tei_cert_matches_own_source_count(self, tei_entries):
        """TEI cert should match the number of sources in its own note element.

        high = 3+ sources, medium = 2 sources, low = 0-1 sources.
        """
        for entry in tei_entries:
            xmlid = entry.get(f"{{{XML_NS}}}id")
            for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
                cert = link.get("cert")
                note = link.find(f"{{{TEI_NS}}}note[@type='sources']")
                if note is not None and note.text:
                    count = len(note.text.split("; "))
                else:
                    count = 0
                if count >= 3:
                    expected = "high"
                elif count == 2:
                    expected = "medium"
                else:
                    expected = "low"
                assert cert == expected, (
                    f"{xmlid} {link.get('target')}: "
                    f"count={count} but cert={cert} (expected {expected})"
                )


# ---- 10. Heart Sutra (T08n0251) spot check ----

class TestHeartSutra:
    def test_json_has_toh_21(self, json_data):
        """T08n0251 should have Toh 21 in JSON."""
        parallels = json_data["tibetan_parallels"]["T08n0251"]
        assert "Toh 21" in parallels

    def test_csv_has_toh_21(self, csv_rows_by_taisho):
        """T08n0251 should have Toh 21 in CSV."""
        rows = csv_rows_by_taisho["T08n0251"]
        tohs = {r["tohoku"] for r in rows}
        assert "Toh 21" in tohs

    def test_tei_has_toh_21(self, tei_entry_map):
        """T08n0251 should have Toh 21 in TEI."""
        entry = tei_entry_map["T08n0251"]
        tei_tohs = set()
        for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
            target = link.get("target", "")
            if target.startswith("Toh_"):
                tei_tohs.add(target.replace("_", " "))
        assert "Toh 21" in tei_tohs

    def test_csv_toh_21_source_count(self, csv_rows_by_taisho):
        """T08n0251 Toh 21 should have 6 sources in CSV."""
        rows = csv_rows_by_taisho["T08n0251"]
        toh21_rows = [r for r in rows if r["tohoku"] == "Toh 21"]
        assert len(toh21_rows) == 1
        assert int(toh21_rows[0]["source_count"]) == 6

    def test_tei_toh_21_cert_high(self, tei_entry_map):
        """T08n0251 Toh 21 should have cert='high' in TEI (6 sources)."""
        entry = tei_entry_map["T08n0251"]
        for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
            if link.get("target") == "Toh_21":
                assert link.get("cert") == "high"
                break
        else:
            pytest.fail("Toh_21 link not found in TEI for T08n0251")


# ---- 11. Maharatnakuta (T11n0310) spot check ----

class TestMaharatnakuta:
    def test_json_has_at_least_54_tohoku(self, json_data):
        """T11n0310 should have at least 54 Tohoku numbers in JSON (base catalog sources)."""
        parallels = json_data["tibetan_parallels"]["T11n0310"]
        tohs = [p for p in parallels if p.startswith("Toh ")]
        assert len(tohs) >= 54

    def test_csv_has_at_least_54_tohoku(self, csv_rows_by_taisho):
        """T11n0310 should have at least 54 Tohoku rows in CSV."""
        rows = csv_rows_by_taisho["T11n0310"]
        tohs = {r["tohoku"] for r in rows if r["tohoku"]}
        assert len(tohs) >= 54

    def test_tei_has_at_least_54_tohoku(self, tei_entry_map):
        """T11n0310 should have at least 54 Tohoku links in TEI."""
        entry = tei_entry_map["T11n0310"]
        tei_tohs = set()
        for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
            target = link.get("target", "")
            if target.startswith("Toh_"):
                tei_tohs.add(target)
        assert len(tei_tohs) >= 54

    def test_all_three_formats_agree(self, json_data, csv_rows_by_taisho, tei_entry_map):
        """T11n0310 Tohoku sets should be identical across JSON, CSV, and TEI."""
        json_tohs = {
            p for p in json_data["tibetan_parallels"]["T11n0310"]
            if p.startswith("Toh ")
        }
        csv_tohs = {
            r["tohoku"] for r in csv_rows_by_taisho["T11n0310"]
            if r["tohoku"]
        }
        entry = tei_entry_map["T11n0310"]
        tei_tohs = set()
        for link in entry.findall(f"{{{TEI_NS}}}link[@type='tibetan']"):
            target = link.get("target", "")
            if target.startswith("Toh_"):
                tei_tohs.add(target.replace("_", " "))
        assert json_tohs == csv_tohs == tei_tohs


# ---- 12. A text with Pali parallel spot check ----

class TestPaliSpotCheck:
    def test_t01n0003_pali_in_json(self, json_data):
        """T01n0003 should have dn14 and sn12.65 as Pali parallels in JSON."""
        pali = json_data["pali_parallels"]["T01n0003"]
        assert "dn14" in pali
        assert "sn12.65" in pali

    def test_t01n0003_pali_in_csv(self, csv_rows_by_taisho):
        """T01n0003 should have dn14 and sn12.65 in CSV pali_parallel field."""
        rows = csv_rows_by_taisho["T01n0003"]
        pali_str = rows[0]["pali_parallel"]
        assert "dn14" in pali_str
        assert "sn12.65" in pali_str

    def test_t01n0003_pali_in_tei(self, tei_entry_map):
        """T01n0003 should have pali links for dn14 and sn12.65 in TEI."""
        entry = tei_entry_map["T01n0003"]
        tei_pali = set()
        for link in entry.findall(f"{{{TEI_NS}}}link[@type='pali']"):
            tei_pali.add(link.get("target"))
        assert "dn14" in tei_pali
        assert "sn12.65" in tei_pali


# ---- 13. CSV well-formedness ----

class TestCSVWellFormedness:
    EXPECTED_COLUMNS = [
        "taisho_id", "tohoku", "otani", "nanjio",
        "sanskrit_title", "chinese_title", "tibetan_title",
        "pali_parallel", "sources", "source_count",
    ]

    def test_parseable_by_csv_module(self):
        """CSV should be parseable by the standard csv module."""
        if not CSV_PATH.exists():
            pytest.skip("cross_reference.csv not found")
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0

    def test_correct_column_count(self, csv_rows):
        """Every row should have the correct number of columns."""
        for i, row in enumerate(csv_rows):
            assert set(row.keys()) == set(self.EXPECTED_COLUMNS), (
                f"Row {i} has wrong columns: {set(row.keys())}"
            )

    def test_no_empty_taisho_id(self, csv_rows):
        """No row should have an empty taisho_id."""
        for i, row in enumerate(csv_rows):
            assert row["taisho_id"].strip() != "", f"Row {i} has empty taisho_id"

    def test_taisho_id_format(self, csv_rows):
        """All taisho_id values should match the expected format."""
        # CBETA IDs: T{vol}n{number} with optional letter suffix (a-z or A-Z)
        pattern = re.compile(r'^T\d{2}n\d{4}[a-zA-Z]?$')
        for i, row in enumerate(csv_rows):
            assert pattern.match(row["taisho_id"]), (
                f"Row {i}: invalid taisho_id format: {row['taisho_id']}"
            )

    def test_source_count_is_numeric(self, csv_rows):
        """source_count should be a non-negative integer."""
        for i, row in enumerate(csv_rows):
            count = int(row["source_count"])
            assert count >= 0, f"Row {i}: negative source_count {count}"


# ---- 14. TEI well-formedness ----

class TestTEIWellFormedness:
    def test_valid_xml(self):
        """TEI file should be valid XML."""
        if not TEI_PATH.exists():
            pytest.skip("cross_reference.tei.xml not found")
        tree = ET.parse(TEI_PATH)
        assert tree.getroot() is not None

    def test_correct_namespace(self, tei_tree):
        """Root element should be TEI with the correct namespace."""
        root = tei_tree.getroot()
        assert root.tag == f"{{{TEI_NS}}}TEI"

    def test_has_tei_header(self, tei_tree):
        """TEI should have a teiHeader element."""
        root = tei_tree.getroot()
        header = root.find(f"{{{TEI_NS}}}teiHeader")
        assert header is not None

    def test_has_link_grp(self, tei_tree):
        """TEI should have a linkGrp element."""
        root = tei_tree.getroot()
        link_grp = root.find(f".//{{{TEI_NS}}}linkGrp")
        assert link_grp is not None
        assert link_grp.get("type") == "concordance"

    def test_header_has_title(self, tei_tree):
        """TEI header should contain a title element."""
        root = tei_tree.getroot()
        title = root.find(
            f".//{{{TEI_NS}}}teiHeader/{{{TEI_NS}}}fileDesc/"
            f"{{{TEI_NS}}}titleStmt/{{{TEI_NS}}}title"
        )
        assert title is not None
        assert title.text and len(title.text) > 0

    def test_header_has_author(self, tei_tree):
        """TEI header should contain an author element."""
        root = tei_tree.getroot()
        author = root.find(
            f".//{{{TEI_NS}}}teiHeader/{{{TEI_NS}}}fileDesc/"
            f"{{{TEI_NS}}}titleStmt/{{{TEI_NS}}}author"
        )
        assert author is not None
        assert author.text == "Dan Zigmond"

    def test_entries_have_xml_id(self, tei_entries):
        """Every <entry> should have an xml:id attribute."""
        for entry in tei_entries:
            xmlid = entry.get(f"{{{XML_NS}}}id")
            assert xmlid is not None and xmlid.strip() != "", (
                "Entry found without xml:id"
            )

    def test_link_elements_have_required_attrs(self, tei_entries):
        """Every <link> element should have type and target attributes."""
        for entry in tei_entries:
            for link in entry.findall(f"{{{TEI_NS}}}link"):
                assert link.get("type") is not None, (
                    f"Link without type in {entry.get(f'{{{XML_NS}}}id')}"
                )
                assert link.get("target") is not None, (
                    f"Link without target in {entry.get(f'{{{XML_NS}}}id')}"
                )
