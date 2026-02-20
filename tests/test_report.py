"""Tests for digest_detector/report.py -- validation and report generation."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from digest_detector.models import (
    AlignmentResult, AlignmentSegment, DigestScore, MultiSourceDigest,
    TextMetadata,
)
from digest_detector.report import (
    GROUND_TRUTH,
    _format_alignment_visualization,
    _segment_to_dict,
    generate_reports,
    validate_ground_truth,
)
from tests.helpers import make_alignment, make_metadata, make_score, make_segment


# ---------- _segment_to_dict ----------

class TestSegmentToDict:
    def test_exact_segment(self):
        seg = make_segment(0, 5, 10, 15, "exact", "你好世界人", "天地玄黃宇")
        d = _segment_to_dict(seg)
        assert d['digest_start'] == 0
        assert d['digest_end'] == 5
        assert d['source_start'] == 10
        assert d['source_end'] == 15
        assert d['match_type'] == "exact"
        assert d['digest_text'] == "你好世界人"
        assert d['source_text'] == "天地玄黃宇"
        assert 'phonetic_mapping' not in d

    def test_novel_segment(self):
        seg = make_segment(5, 10, 0, 0, "novel", "一二三四五", "")
        d = _segment_to_dict(seg)
        assert d['match_type'] == "novel"
        assert 'phonetic_mapping' not in d

    def test_phonetic_segment_with_mapping(self):
        mapping = [("竭", "ga", "揭"), ("帝", "te", "帝")]
        seg = make_segment(0, 2, 0, 2, "phonetic", "竭帝", "揭帝",
                            phonetic_mapping=mapping)
        d = _segment_to_dict(seg)
        assert d['match_type'] == "phonetic"
        assert 'phonetic_mapping' in d
        assert len(d['phonetic_mapping']) == 2
        assert d['phonetic_mapping'][0] == {
            'digest_char': '竭', 'syllable': 'ga', 'source_char': '揭'
        }

    def test_phonetic_segment_empty_mapping(self):
        seg = make_segment(0, 2, 0, 2, "phonetic", "竭帝", "揭帝",
                            phonetic_mapping=[])
        d = _segment_to_dict(seg)
        assert 'phonetic_mapping' not in d

    def test_all_fields_present(self):
        seg = make_segment(3, 8, 20, 25, "fuzzy")
        d = _segment_to_dict(seg)
        required_keys = {'digest_start', 'digest_end', 'source_start',
                         'source_end', 'match_type', 'digest_text', 'source_text'}
        assert required_keys.issubset(d.keys())


# ---------- validate_ground_truth ----------

class TestValidateGroundTruth:
    def test_both_pairs_found_and_correct(self):
        scores = [
            make_score('T08n0250', 'T08n0223', 'digest', coverage=0.732),
            make_score('T08n0251', 'T08n0223', 'digest', coverage=0.446),
        ]
        alignments = [
            make_alignment('T08n0250', 'T08n0223', 0.732),
            make_alignment('T08n0251', 'T08n0223', 0.446),
        ]
        metadata_map = {
            'T08n0250': make_metadata('T08n0250'),
            'T08n0251': make_metadata('T08n0251'),
            'T08n0223': make_metadata('T08n0223'),
        }
        report = validate_ground_truth(scores, alignments, metadata_map)
        # 2 pairs × 2 checks (classification + coverage) + 2 not-digest checks = 6
        assert report['passed'] >= 4  # at minimum both classification and coverage pass

    def test_missing_pair(self):
        """When a ground truth pair is not found in results."""
        scores = []
        alignments = []
        metadata_map = {}
        report = validate_ground_truth(scores, alignments, metadata_map)
        assert report['failed'] >= 2  # both pairs missing

    def test_wrong_classification(self):
        scores = [
            make_score('T08n0250', 'T08n0223', 'shared_tradition', coverage=0.732),
            make_score('T08n0251', 'T08n0223', 'digest', coverage=0.446),
        ]
        alignments = [
            make_alignment('T08n0250', 'T08n0223', 0.732),
            make_alignment('T08n0251', 'T08n0223', 0.446),
        ]
        metadata_map = {}
        report = validate_ground_truth(scores, alignments, metadata_map)
        assert report['failed'] >= 1

    def test_t250_not_digest_of_t251(self):
        """T250/T251 should not be classified as digests of each other."""
        scores = [
            make_score('T08n0250', 'T08n0223', 'digest', coverage=0.732),
            make_score('T08n0251', 'T08n0223', 'digest', coverage=0.446),
            make_score('T08n0250', 'T08n0251', 'retranslation', coverage=0.654),
        ]
        alignments = [
            make_alignment('T08n0250', 'T08n0223', 0.732),
            make_alignment('T08n0251', 'T08n0223', 0.446),
            make_alignment('T08n0250', 'T08n0251', 0.654),
        ]
        metadata_map = {}
        report = validate_ground_truth(scores, alignments, metadata_map)
        # retranslation is acceptable, digest would not be
        not_digest_checks = [
            t for t in report['tests']
            if any(c.get('check') == 'not_digest_of_each_other' for c in t['checks'])
        ]
        assert len(not_digest_checks) == 2
        for t in not_digest_checks:
            check = t['checks'][0]
            assert check['passed'] is True


# ---------- _format_alignment_visualization ----------

class TestFormatVisualization:
    def test_basic_visualization(self):
        segs = [
            make_segment(0, 5, 0, 5, "exact", "你好世界人", "你好世界人"),
            make_segment(5, 10, 0, 0, "novel", "一二三四五", ""),
        ]
        alignment = make_alignment("T08n0250", "T08n0223", 0.5, segments=segs)
        score = make_score("T08n0250", "T08n0223", "digest", coverage=0.5)
        metadata_map = {
            'T08n0250': make_metadata('T08n0250', title='心經'),
            'T08n0223': make_metadata('T08n0223', title='大品般若'),
        }
        viz = _format_alignment_visualization(alignment, score, metadata_map)
        assert "T08n0250" in viz
        assert "心經" in viz
        assert "T08n0223" in viz
        assert "大品般若" in viz
        assert "NOVEL" in viz
        assert "EXACT" in viz

    def test_phonetic_visualization(self):
        mapping = [("竭", "ga", "揭"), ("帝", "te", "帝")]
        segs = [
            make_segment(0, 2, 0, 2, "phonetic", "竭帝", "揭帝",
                          phonetic_mapping=mapping),
        ]
        alignment = make_alignment("T08n0250", "T18n0901", 0.8, segments=segs)
        score = make_score("T08n0250", "T18n0901", "digest", coverage=0.8)
        score = replace(score, phonetic_coverage=0.3)
        metadata_map = {}
        viz = _format_alignment_visualization(alignment, score, metadata_map)
        assert "PHONETIC" in viz
        assert "Transliteration" in viz
        assert "竭→ga←揭" in viz


# ---------- generate_reports ----------

class TestGenerateReports:
    def test_creates_output_files(self, tmp_path):
        scores = [make_score("T08n0250", "T08n0223", "digest", coverage=0.732)]
        alignments = [make_alignment("T08n0250", "T08n0223", 0.732)]
        multi_source = []
        metadata_map = {
            'T08n0250': make_metadata('T08n0250'),
            'T08n0223': make_metadata('T08n0223'),
        }
        validation = {'tests': [], 'passed': 0, 'failed': 0}

        generate_reports(scores, alignments, multi_source, metadata_map,
                         validation, results_dir=tmp_path)

        # Check JSON file was created
        json_path = tmp_path / "digest_relationships.json"
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert len(data) == 1
        assert data[0]['digest_id'] == 'T08n0250'
        assert data[0]['classification'] == 'digest'

        # Check alignment dir was created
        assert (tmp_path / "alignments").is_dir()

    def test_json_fields(self, tmp_path):
        score = make_score("T01n0001", "T01n0002", "excerpt", confidence=0.8, coverage=0.95)
        scores = [score]
        alignments = [make_alignment("T01n0001", "T01n0002", 0.95)]
        generate_reports(scores, alignments, [], {},
                         {'tests': [], 'passed': 0, 'failed': 0},
                         results_dir=tmp_path)

        data = json.loads((tmp_path / "digest_relationships.json").read_text())
        rel = data[0]
        expected_keys = {'digest_id', 'source_id', 'classification',
                         'confidence', 'coverage', 'novel_fraction',
                         'avg_segment_length', 'longest_segment',
                         'num_source_regions', 'source_span', 'has_docnumber_xref'}
        assert expected_keys.issubset(rel.keys())

    def test_phonetic_coverage_in_json(self, tmp_path):
        score = make_score("T01n0001", "T01n0002", "digest", coverage=0.5)
        score = replace(score, phonetic_coverage=0.15)
        scores = [score]
        alignments = [make_alignment("T01n0001", "T01n0002", 0.5)]
        generate_reports(scores, alignments, [], {},
                         {'tests': [], 'passed': 0, 'failed': 0},
                         results_dir=tmp_path)

        data = json.loads((tmp_path / "digest_relationships.json").read_text())
        assert 'phonetic_coverage' in data[0]
        assert data[0]['phonetic_coverage'] == 0.15

    def test_no_relationship_excluded_from_alignment_files(self, tmp_path):
        score = make_score("T01n0001", "T01n0002", "no_relationship", coverage=0.05)
        scores = [score]
        alignments = [make_alignment("T01n0001", "T01n0002", 0.05)]
        generate_reports(scores, alignments, [], {},
                         {'tests': [], 'passed': 0, 'failed': 0},
                         results_dir=tmp_path)

        # no_relationship pairs should not get alignment files
        alignment_files = list((tmp_path / "alignments").iterdir())
        assert len(alignment_files) == 0
