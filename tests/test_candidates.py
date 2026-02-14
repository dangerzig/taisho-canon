"""Tests for Stage 2b: Candidate pair selection."""

import pytest

from digest_detector.candidates import (
    _parse_docnumber_to_text_ids,
    _find_docnumber_pairs,
    generate_candidates,
)
from digest_detector.fingerprint import (
    compute_document_frequencies,
    identify_stopgrams,
    build_inverted_index,
)
from digest_detector.models import ExtractedText, TextMetadata, DivSegment


def _make_text(text_id: str, content: str, **meta_overrides) -> ExtractedText:
    """Helper to create a minimal ExtractedText."""
    meta_kwargs = dict(
        text_id=text_id, title='', author='',
        extent_juan=1, char_count=len(content),
        file_count=1,
    )
    meta_kwargs.update(meta_overrides)
    return ExtractedText(
        text_id=text_id,
        full_text=content,
        segments=[],
        metadata=TextMetadata(**meta_kwargs),
    )


def _make_metadata(text_id: str, char_count: int, **overrides) -> TextMetadata:
    """Helper to create a minimal TextMetadata."""
    kwargs = dict(
        text_id=text_id, title='', author='',
        extent_juan=1, char_count=char_count,
        file_count=1,
    )
    kwargs.update(overrides)
    return TextMetadata(**kwargs)


class TestParseDocnumberToTextIds:
    def test_basic_self_reference(self):
        meta_map = {
            'T08n0250': _make_metadata('T08n0250', 300),
        }
        result = _parse_docnumber_to_text_ids(meta_map)
        # Leading zeros stripped: "0250" → "250"
        assert 'T08n0250' in result.get('T08:250', set())

    def test_cross_reference(self):
        meta_map = {
            'T08n0250': _make_metadata('T08n0250', 300,
                                        docnumber_refs=['251', '252']),
            'T08n0251': _make_metadata('T08n0251', 1000),
        }
        result = _parse_docnumber_to_text_ids(meta_map)
        # Both T08n0250 (via ref) and T08n0251 (via self) share key "T08:251"
        assert 'T08n0250' in result.get('T08:251', set())
        assert 'T08n0251' in result.get('T08:251', set())

    def test_malformed_text_id_skipped(self):
        meta_map = {
            'bad_id': _make_metadata('bad_id', 100),
            'T08n0250': _make_metadata('T08n0250', 300),
        }
        result = _parse_docnumber_to_text_ids(meta_map)
        # bad_id should not appear in any docnum entry
        for text_ids in result.values():
            assert 'bad_id' not in text_ids

    def test_empty_refs(self):
        meta_map = {
            'T08n0250': _make_metadata('T08n0250', 300,
                                        docnumber_refs=[]),
        }
        result = _parse_docnumber_to_text_ids(meta_map)
        # Should only have self-reference (leading zeros stripped)
        assert 'T08n0250' in result.get('T08:250', set())
        assert len(result) == 1


class TestFindDocnumberPairs:
    def test_pair_ordering_by_size(self):
        """Shorter text should be first (potential digest)."""
        meta_map = {
            'T08n0250': _make_metadata('T08n0250', 300,
                                        docnumber_refs=['251']),
            'T08n0251': _make_metadata('T08n0251', 1000,
                                        docnumber_refs=['250']),
        }
        pairs = _find_docnumber_pairs(meta_map)
        # T250 (300 chars) should come first as the shorter text
        assert ('T08n0250', 'T08n0251') in pairs
        assert ('T08n0251', 'T08n0250') not in pairs

    def test_reverse_ordering_when_second_is_shorter(self):
        """If the second text is shorter, it should come first."""
        meta_map = {
            'T08n0300': _make_metadata('T08n0300', 50000,
                                        docnumber_refs=['301']),
            'T08n0301': _make_metadata('T08n0301', 500),
        }
        pairs = _find_docnumber_pairs(meta_map)
        assert ('T08n0301', 'T08n0300') in pairs

    def test_no_self_pairs(self):
        """A text should not be paired with itself."""
        meta_map = {
            'T08n0250': _make_metadata('T08n0250', 300,
                                        docnumber_refs=['250']),
        }
        pairs = _find_docnumber_pairs(meta_map)
        assert ('T08n0250', 'T08n0250') not in pairs

    def test_no_pairs_without_cross_ref(self):
        """Texts without cross-references should not be paired."""
        meta_map = {
            'T08n0250': _make_metadata('T08n0250', 300),
            'T08n0251': _make_metadata('T08n0251', 1000),
        }
        pairs = _find_docnumber_pairs(meta_map)
        assert len(pairs) == 0


class TestGenerateCandidates:
    def test_finds_similar_texts(self):
        """Texts sharing significant content should become candidates."""
        shared = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"
        digest = shared + "新增加的少量內容"
        source = "如是我聞" + shared + "更多更多的佛經文字" * 20

        texts = [
            _make_text("T01n0001", digest),
            _make_text("T01n0002", source),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        index = build_inverted_index(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, index, stopgrams)
        pair_ids = [(c.digest_id, c.source_id) for c in candidates]
        assert ('T01n0001', 'T01n0002') in pair_ids

    def test_size_ratio_filter(self):
        """Source must be at least MIN_SIZE_RATIO times larger than digest."""
        content = "觀自在菩薩行深般若波羅蜜多時照見五蘊"
        texts = [
            _make_text("T01n0001", content),
            _make_text("T01n0002", content + "少"),  # barely longer, not 2x
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        index = build_inverted_index(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, index, stopgrams)
        # Should not produce a pair since source is not 2x longer
        assert len(candidates) == 0

    def test_docnumber_pairs_included(self):
        """DocNumber cross-refs should add pairs even with low containment."""
        digest_content = "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未"
        source_content = "春夏秋冬東西南北上下左右前後" * 20

        texts = [
            _make_text("T08n0250", digest_content,
                        docnumber_refs=['251']),
            _make_text("T08n0251", source_content),
        ]
        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        index = build_inverted_index(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, index, stopgrams)
        docnum_cands = [c for c in candidates if c.from_docnumber]
        assert len(docnum_cands) >= 1
        assert docnum_cands[0].digest_id == 'T08n0250'
        assert docnum_cands[0].source_id == 'T08n0251'

    def test_jing_text_used_for_digest_side(self):
        """When digest has jing segments, containment should use jing_text."""
        shared = "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄"
        xu_text = "完全不同的前言序文內容與佛經正文完全無關的材料充數"
        jing_text = shared + "新增加的少量內容"
        source = "如是我聞" + shared + "更多更多的佛經文字" * 20

        digest = ExtractedText(
            text_id="T01n0001",
            full_text=xu_text + jing_text,
            segments=[
                DivSegment(div_type='xu', text=xu_text, start=0, end=len(xu_text)),
                DivSegment(div_type='jing', text=jing_text,
                           start=len(xu_text), end=len(xu_text) + len(jing_text)),
            ],
            metadata=TextMetadata(
                text_id="T01n0001", title='', author='',
                extent_juan=1, char_count=len(xu_text) + len(jing_text),
                file_count=1,
            ),
        )
        source_text = _make_text("T01n0002", source)
        texts = [digest, source_text]

        doc_freq = compute_document_frequencies(texts, n=5)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        index = build_inverted_index(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, index, stopgrams)
        pair = [c for c in candidates
                if c.digest_id == "T01n0001" and c.source_id == "T01n0002"]
        assert len(pair) == 1
        # Containment should be based on jing_text, not full_text
        # jing shares ~25 of ~33 chars → high containment
        assert pair[0].containment_score > 0.3
