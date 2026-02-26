"""Tests for Tohoku-to-Otani concordance building and merging."""

import json
import sys
import textwrap
from pathlib import Path

import pytest

# Add project root to path so we can import the scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_otani_concordance import parse_collection_xml, build_concordance
from merge_otani_into_concordance import merge_otani_numbers


# -- XML parsing tests --------------------------------------------------------


class TestParseCollectionXml:
    """Tests for parse_collection_xml."""

    def test_basic_kanjur_parsing(self):
        """Parse a minimal Kanjur D.xml with two items."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <outline>
            <name>Derge</name>
            <item>
            <rkts>1</rkts>
            <ref>D1</ref>
            <tib>some title</tib>
            </item>
            <item>
            <rkts>2</rkts>
            <ref>D2</ref>
            <tib>another title</tib>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {"1": ["1"], "2": ["2"]}

    def test_basic_kanjur_q_parsing(self):
        """Parse a minimal Kanjur Q.xml."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <outline>
            <item>
            <rkts>1</rkts>
            <ref>Q1030</ref>
            <tib>title</tib>
            </item>
            <item>
            <rkts>2</rkts>
            <ref>Q1031</ref>
            <tib>title</tib>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {"1": ["1030"], "2": ["1031"]}

    def test_tanjur_uses_rktst_tag(self):
        """Tanjur files use <rktst> instead of <rkts>."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <outline>
            <item>
            <rktst>1</rktst>
            <ref>D1109</ref>
            <tib>title</tib>
            </item>
            <item>
            <rktst>2</rktst>
            <ref>D1110</ref>
            <tib>title</tib>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "tanjur")
        assert result == {"1": ["1109"], "2": ["1110"]}

    def test_tanjur_q_parsing(self):
        """Parse Tanjur Q.xml with <rktst> and Q-prefixed refs."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <outline>
            <item>
            <rktst>1</rktst>
            <ref>Q2001</ref>
            </item>
            <item>
            <rktst>2</rktst>
            <ref>Q2002</ref>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "tanjur")
        assert result == {"1": ["2001"], "2": ["2002"]}

    def test_letter_suffix_refs(self):
        """Refs with letter suffixes like D7a are parsed correctly."""
        xml = textwrap.dedent("""\
            <outline>
            <item>
            <rkts>739</rkts>
            <ref>D7a</ref>
            <tib>title</tib>
            </item>
            <item>
            <rkts>945</rkts>
            <ref>D359a</ref>
            <tib>title</tib>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {"739": ["7a"], "945": ["359a"]}

    def test_duplicate_kernel_ids(self):
        """Multiple items with the same kernel ID produce a list of refs."""
        xml = textwrap.dedent("""\
            <outline>
            <item>
            <rkts>529</rkts>
            <ref>D21</ref>
            <tib>first location</tib>
            </item>
            <item>
            <rkts>529</rkts>
            <ref>D531</ref>
            <tib>second location</tib>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {"529": ["21", "531"]}

    def test_subitems_are_skipped(self):
        """Subitems like D1-1 inside <subitem> tags should NOT appear."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <outline>
            <item>
            <rkts>1</rkts>
            <ref>D1</ref>
            <tib>main item</tib>
            <subitem>
            <rkts>1-1</rkts>
            <ref>D1-1</ref>
            <tib>sub item</tib>
            </subitem>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        # Only the main item should be parsed; subitem has non-integer rkts "1-1"
        assert result == {"1": ["1"]}

    def test_empty_xml(self):
        """Empty XML yields empty dict."""
        xml = '<?xml version="1.0"?><outline></outline>'
        result = parse_collection_xml(xml, "kanjur")
        assert result == {}

    def test_missing_ref_tag(self):
        """Items without a <ref> tag are skipped."""
        xml = textwrap.dedent("""\
            <outline>
            <item>
            <rkts>42</rkts>
            <tib>no ref here</tib>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {}

    def test_missing_kernel_id_tag(self):
        """Items without the kernel ID tag are skipped."""
        xml = textwrap.dedent("""\
            <outline>
            <item>
            <ref>D100</ref>
            <tib>no rkts here</tib>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {}

    def test_loc_and_extra_tags_ignored(self):
        """Extra tags like <loc>, <skttrans>, <coloph> are ignored."""
        xml = textwrap.dedent("""\
            <outline>
            <item>
            <rkts>360</rkts>
            <ref>D14</ref>
            <loc><set>MW22084</set><vol>ka</vol></loc>
            <tib>some title</tib>
            <skttrans>manyju shri</skttrans>
            <sanskrit>foo</sanskrit>
            <coloph>long colophon text</coloph>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {"360": ["14"]}

    def test_kanjur_tag_not_found_in_tanjur_mode(self):
        """When parsing as tanjur, <rkts> tags are not recognized."""
        xml = textwrap.dedent("""\
            <outline>
            <item>
            <rkts>1</rkts>
            <ref>D1</ref>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "tanjur")
        assert result == {}

    def test_tanjur_tag_not_found_in_kanjur_mode(self):
        """When parsing as kanjur, <rktst> tags are not recognized."""
        xml = textwrap.dedent("""\
            <outline>
            <item>
            <rktst>1</rktst>
            <ref>D1109</ref>
            </item>
            </outline>
        """)
        result = parse_collection_xml(xml, "kanjur")
        assert result == {}


# -- Concordance building tests ------------------------------------------------


class TestBuildConcordance:
    """Tests for build_concordance."""

    def test_basic_kanjur_join(self):
        """Two items sharing a kernel ID produce a Toh->Otani mapping."""
        d_kanjur = {"1": ["1"], "2": ["2"]}
        q_kanjur = {"1": ["1030"], "2": ["1031"]}
        concordance, stats = build_concordance(d_kanjur, q_kanjur, {}, {})
        assert concordance == {
            "Toh 1": ["Otani 1030"],
            "Toh 2": ["Otani 1031"],
        }
        assert stats["kanjur_mappings"] == 2
        assert stats["tanjur_mappings"] == 0

    def test_basic_tanjur_join(self):
        """Tanjur items join on shared kernel IDs too."""
        d_tanjur = {"1": ["1109"], "2": ["1110"]}
        q_tanjur = {"1": ["2001"], "2": ["2002"]}
        concordance, stats = build_concordance({}, {}, d_tanjur, q_tanjur)
        assert concordance == {
            "Toh 1109": ["Otani 2001"],
            "Toh 1110": ["Otani 2002"],
        }
        assert stats["tanjur_mappings"] == 2
        assert stats["kanjur_mappings"] == 0

    def test_mixed_kanjur_and_tanjur(self):
        """Kanjur and Tanjur mappings are combined."""
        d_kanjur = {"1": ["1"]}
        q_kanjur = {"1": ["1030"]}
        d_tanjur = {"1": ["1109"]}
        q_tanjur = {"1": ["2001"]}
        concordance, stats = build_concordance(d_kanjur, q_kanjur, d_tanjur, q_tanjur)
        assert "Toh 1" in concordance
        assert "Toh 1109" in concordance
        assert stats["kanjur_mappings"] == 1
        assert stats["tanjur_mappings"] == 1

    def test_unmatched_kernel_ids_excluded(self):
        """Kernel IDs present in D but not Q (or vice versa) are excluded."""
        d_kanjur = {"1": ["1"], "999": ["999"]}
        q_kanjur = {"1": ["1030"]}
        concordance, stats = build_concordance(d_kanjur, q_kanjur, {}, {})
        assert concordance == {"Toh 1": ["Otani 1030"]}
        assert stats["kanjur_mappings"] == 1

    def test_empty_inputs(self):
        """All-empty inputs produce empty concordance."""
        concordance, stats = build_concordance({}, {}, {}, {})
        assert concordance == {}
        assert stats["total_tohoku_numbers"] == 0

    def test_multiple_otani_for_same_tohoku(self):
        """If Kanjur and Tanjur both map to the same Toh, Otani numbers merge."""
        d_kanjur = {"1": ["100"]}
        q_kanjur = {"1": ["200"]}
        d_tanjur = {"5": ["100"]}  # Same Toh 100 from Tanjur
        q_tanjur = {"5": ["300"]}
        concordance, stats = build_concordance(d_kanjur, q_kanjur, d_tanjur, q_tanjur)
        assert concordance == {"Toh 100": ["Otani 200", "Otani 300"]}

    def test_duplicate_kernel_ids_expand(self):
        """Multiple D refs per kernel ID all get Otani mappings."""
        d_kanjur = {"529": ["21", "531"]}
        q_kanjur = {"529": ["160"]}
        concordance, _ = build_concordance(d_kanjur, q_kanjur, {}, {})
        assert concordance == {
            "Toh 21": ["Otani 160"],
            "Toh 531": ["Otani 160"],
        }

    def test_output_sorted_by_tohoku_number(self):
        """Concordance keys are sorted by Tohoku number."""
        d_kanjur = {"3": ["300"], "1": ["100"], "2": ["200"]}
        q_kanjur = {"3": ["3300"], "1": ["1100"], "2": ["2200"]}
        concordance, _ = build_concordance(d_kanjur, q_kanjur, {}, {})
        assert list(concordance.keys()) == ["Toh 100", "Toh 200", "Toh 300"]

    def test_letter_suffix_sorting(self):
        """Letter-suffixed refs sort after their base number."""
        d_kanjur = {"1": ["7"], "2": ["7a"], "3": ["8"]}
        q_kanjur = {"1": ["100"], "2": ["100a"], "3": ["101"]}
        concordance, _ = build_concordance(d_kanjur, q_kanjur, {}, {})
        assert list(concordance.keys()) == ["Toh 7", "Toh 7a", "Toh 8"]

    def test_stats_counts(self):
        """Stats reflect correct item and mapping counts."""
        d_kanjur = {"1": ["1"], "2": ["2"], "3": ["3"]}
        q_kanjur = {"1": ["1030"], "2": ["1031"]}
        d_tanjur = {"10": ["1109"]}
        q_tanjur = {"10": ["2001"], "11": ["2002"]}
        _, stats = build_concordance(d_kanjur, q_kanjur, d_tanjur, q_tanjur)
        assert stats["d_kanjur_items"] == 3
        assert stats["q_kanjur_items"] == 2
        assert stats["d_tanjur_items"] == 1
        assert stats["q_tanjur_items"] == 2
        assert stats["shared_kanjur_kernel_ids"] == 2
        assert stats["shared_tanjur_kernel_ids"] == 1
        assert stats["kanjur_mappings"] == 2
        assert stats["tanjur_mappings"] == 1
        assert stats["total_tohoku_numbers"] == 3
        assert stats["total_mappings"] == 3


# -- Merge tests ---------------------------------------------------------------


class TestMergeOtaniNumbers:
    """Tests for merge_otani_numbers."""

    def _write_concordance(self, tmp_path, tibetan_parallels):
        """Write a test concordance file and return its path."""
        path = tmp_path / "concordance.json"
        data = {
            "summary": {"total_texts": len(tibetan_parallels)},
            "sources": {},
            "tibetan_parallels": tibetan_parallels,
        }
        with open(path, "w") as f:
            json.dump(data, f)
        return path

    def _read_concordance(self, path):
        """Read back the concordance file."""
        with open(path) as f:
            return json.load(f)

    def test_adds_new_otani_for_existing_toh(self, tmp_path):
        """Adds Otani numbers for a text that has Toh but no Otani."""
        path = self._write_concordance(tmp_path, {
            "T01n0004": ["Toh 1"],
        })
        toh_otani = {"Toh 1": ["Otani 1030"]}

        texts_updated, new_added, new_texts, _ = merge_otani_numbers(path, toh_otani)

        assert texts_updated == 1
        assert new_added == 1
        assert new_texts == 1

        result = self._read_concordance(path)
        assert "Otani 1030" in result["tibetan_parallels"]["T01n0004"]

    def test_no_duplicates(self, tmp_path):
        """Does not add Otani numbers that already exist."""
        path = self._write_concordance(tmp_path, {
            "T01n0004": ["Otani 1030", "Toh 1"],
        })
        toh_otani = {"Toh 1": ["Otani 1030"]}

        texts_updated, new_added, _, _ = merge_otani_numbers(path, toh_otani)

        assert texts_updated == 0
        assert new_added == 0

        result = self._read_concordance(path)
        # Should still have exactly one Otani 1030
        otani_count = result["tibetan_parallels"]["T01n0004"].count("Otani 1030")
        assert otani_count == 1

    def test_multiple_toh_numbers(self, tmp_path):
        """A text with multiple Toh numbers gets Otani from each."""
        path = self._write_concordance(tmp_path, {
            "T01n0026": ["Toh 289", "Toh 290"],
        })
        toh_otani = {
            "Toh 289": ["Otani 955"],
            "Toh 290": ["Otani 956"],
        }

        texts_updated, new_added, _, _ = merge_otani_numbers(path, toh_otani)

        assert texts_updated == 1
        assert new_added == 2

        result = self._read_concordance(path)
        parallels = result["tibetan_parallels"]["T01n0026"]
        assert "Otani 955" in parallels
        assert "Otani 956" in parallels

    def test_text_without_toh_not_touched(self, tmp_path):
        """Texts with only Otani or other refs are not modified."""
        path = self._write_concordance(tmp_path, {
            "T01n0001": ["Otani 1021", "up3.050"],
        })
        toh_otani = {"Toh 1": ["Otani 1030"]}

        texts_updated, new_added, _, _ = merge_otani_numbers(path, toh_otani)

        assert texts_updated == 0
        assert new_added == 0

    def test_toh_not_in_concordance(self, tmp_path):
        """Toh numbers in the concordance that are NOT in toh_otani are ignored."""
        path = self._write_concordance(tmp_path, {
            "T99n9999": ["Toh 9999"],
        })
        toh_otani = {"Toh 1": ["Otani 1030"]}

        texts_updated, new_added, _, _ = merge_otani_numbers(path, toh_otani)

        assert texts_updated == 0
        assert new_added == 0

    def test_preserves_existing_entries(self, tmp_path):
        """Merge preserves all existing parallel entries."""
        path = self._write_concordance(tmp_path, {
            "T01n0004": ["Toh 1", "Toh 235", "up3.050"],
        })
        toh_otani = {"Toh 1": ["Otani 1030"]}

        merge_otani_numbers(path, toh_otani)

        result = self._read_concordance(path)
        parallels = result["tibetan_parallels"]["T01n0004"]
        assert "Toh 1" in parallels
        assert "Toh 235" in parallels
        assert "up3.050" in parallels
        assert "Otani 1030" in parallels

    def test_output_sorted(self, tmp_path):
        """After merge, parallels list is sorted."""
        path = self._write_concordance(tmp_path, {
            "T01n0004": ["Toh 1", "Toh 235"],
        })
        toh_otani = {"Toh 1": ["Otani 1030"], "Toh 235": ["Otani 500"]}

        merge_otani_numbers(path, toh_otani)

        result = self._read_concordance(path)
        parallels = result["tibetan_parallels"]["T01n0004"]
        assert parallels == sorted(parallels)

    def test_sources_tracking_updated(self, tmp_path):
        """The sources dict gets a rkts_otani entry."""
        path = self._write_concordance(tmp_path, {
            "T01n0004": ["Toh 1"],
        })
        toh_otani = {"Toh 1": ["Otani 1030"]}

        merge_otani_numbers(path, toh_otani)

        result = self._read_concordance(path)
        assert "rkts_otani" in result["sources"]
        assert result["sources"]["rkts_otani"] == 1

    def test_multiple_otani_per_toh(self, tmp_path):
        """A single Toh can map to multiple Otani numbers."""
        path = self._write_concordance(tmp_path, {
            "T01n0004": ["Toh 1"],
        })
        toh_otani = {"Toh 1": ["Otani 1030", "Otani 1031"]}

        texts_updated, new_added, _, _ = merge_otani_numbers(path, toh_otani)

        assert texts_updated == 1
        assert new_added == 2

        result = self._read_concordance(path)
        parallels = result["tibetan_parallels"]["T01n0004"]
        assert "Otani 1030" in parallels
        assert "Otani 1031" in parallels

    def test_partial_overlap(self, tmp_path):
        """Only new Otani numbers are added when some already exist."""
        path = self._write_concordance(tmp_path, {
            "T01n0004": ["Otani 1030", "Toh 1"],
        })
        toh_otani = {"Toh 1": ["Otani 1030", "Otani 1031"]}

        texts_updated, new_added, new_texts, _ = merge_otani_numbers(path, toh_otani)

        assert texts_updated == 1
        assert new_added == 1  # Only 1031 is new
        assert new_texts == 0  # Already had Otani

        result = self._read_concordance(path)
        parallels = result["tibetan_parallels"]["T01n0004"]
        assert parallels.count("Otani 1030") == 1  # No duplicate
        assert "Otani 1031" in parallels


# -- Integration test with real XML files --------------------------------------


class TestRealXmlFiles:
    """Integration tests using actual downloaded rKTs XML files."""

    DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "rkts_collections"

    @pytest.fixture
    def xml_files_available(self):
        """Skip if XML files are not downloaded."""
        for name in ["D_kanjur.xml", "Q_kanjur.xml", "D_tanjur.xml", "Q_tanjur.xml"]:
            if not (self.DATA_DIR / name).exists():
                pytest.skip(f"rKTs XML files not downloaded: {name}")

    def _load_xml(self, filename):
        with open(self.DATA_DIR / filename, encoding="utf-8") as f:
            return f.read()

    def test_d_kanjur_has_expected_items(self, xml_files_available):
        """D Kanjur should have 800+ items (some share kernel IDs with subitems)."""
        xml = self._load_xml("D_kanjur.xml")
        result = parse_collection_xml(xml, "kanjur")
        assert len(result) > 800
        # Toh 1 should be present
        assert "1" in result
        assert "1" in result["1"]

    def test_d_kanjur_letter_suffix(self, xml_files_available):
        """D Kanjur includes letter-suffixed entries like D7a."""
        xml = self._load_xml("D_kanjur.xml")
        result = parse_collection_xml(xml, "kanjur")
        # rkts 739 -> D7a
        assert "739" in result
        assert "7a" in result["739"]

    def test_d_kanjur_duplicate_kernel_ids(self, xml_files_available):
        """D Kanjur has texts appearing at multiple locations (shared kernel IDs)."""
        xml = self._load_xml("D_kanjur.xml")
        result = parse_collection_xml(xml, "kanjur")
        # kernel 529 -> D21 and D531
        assert "529" in result
        assert "21" in result["529"]
        assert "531" in result["529"]

    def test_q_kanjur_has_expected_items(self, xml_files_available):
        """Q Kanjur should have 750+ items."""
        xml = self._load_xml("Q_kanjur.xml")
        result = parse_collection_xml(xml, "kanjur")
        assert len(result) > 750

    def test_d_tanjur_has_expected_items(self, xml_files_available):
        """D Tanjur should have 3300+ items."""
        xml = self._load_xml("D_tanjur.xml")
        result = parse_collection_xml(xml, "tanjur")
        assert len(result) > 3300
        # rktst 1 -> D1109
        assert "1" in result
        assert "1109" in result["1"]

    def test_q_tanjur_has_expected_items(self, xml_files_available):
        """Q Tanjur should have 3700+ items."""
        xml = self._load_xml("Q_tanjur.xml")
        result = parse_collection_xml(xml, "tanjur")
        assert len(result) > 3700

    def test_kanjur_join_produces_mappings(self, xml_files_available):
        """Joining D and Q Kanjur produces a substantial concordance."""
        d_xml = self._load_xml("D_kanjur.xml")
        q_xml = self._load_xml("Q_kanjur.xml")
        d_kanjur = parse_collection_xml(d_xml, "kanjur")
        q_kanjur = parse_collection_xml(q_xml, "kanjur")

        concordance, stats = build_concordance(d_kanjur, q_kanjur, {}, {})
        assert stats["kanjur_mappings"] > 750
        # Toh 1 -> should map to some Otani number
        assert "Toh 1" in concordance

    def test_full_concordance(self, xml_files_available):
        """Full concordance (Kanjur + Tanjur) has substantial coverage."""
        d_kj = parse_collection_xml(self._load_xml("D_kanjur.xml"), "kanjur")
        q_kj = parse_collection_xml(self._load_xml("Q_kanjur.xml"), "kanjur")
        d_tj = parse_collection_xml(self._load_xml("D_tanjur.xml"), "tanjur")
        q_tj = parse_collection_xml(self._load_xml("Q_tanjur.xml"), "tanjur")

        concordance, stats = build_concordance(d_kj, q_kj, d_tj, q_tj)
        assert stats["total_tohoku_numbers"] > 3900
        assert stats["total_otani_numbers"] > 3900
        # Verify both Kanjur and Tanjur contributed
        assert stats["kanjur_mappings"] > 700
        assert stats["tanjur_mappings"] > 3000
