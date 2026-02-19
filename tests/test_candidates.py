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
    build_ngram_sets,
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


class TestGenerateCandidatesDegenerate:
    def test_empty_ngram_sets(self):
        """Empty ngram_sets dict produces no candidates."""
        texts = [
            _make_text("T01n0001", "般若波羅蜜多心經觀自在菩薩"),
        ]
        candidates = generate_candidates(texts, ngram_sets={}, stopgrams=set())
        assert candidates == []

    def test_text_with_empty_frozenset(self):
        """A text whose frozenset is empty doesn't cause errors."""
        texts = [
            _make_text("T01n0001", "般若波羅蜜多心經觀自在菩薩"),
            _make_text("T01n0002", "觀自在菩薩行深般若波羅蜜多" * 20),
        ]
        ngram_sets = {
            "T01n0001": frozenset(),
            "T01n0002": frozenset(),
        }
        candidates = generate_candidates(texts, ngram_sets, stopgrams=set())
        # No matches possible with empty sets
        assert candidates == []


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
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, ngram_sets, stopgrams)
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
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, ngram_sets, stopgrams)
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
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, ngram_sets, stopgrams)
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
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5)

        candidates = generate_candidates(texts, ngram_sets, stopgrams)
        pair = [c for c in candidates
                if c.digest_id == "T01n0001" and c.source_id == "T01n0002"]
        assert len(pair) == 1
        # Containment should be based on jing_text, not full_text
        # jing shares ~25 of ~33 chars → high containment
        assert pair[0].containment_score > 0.3


class TestGenerateCandidatesParallel:
    """Verify serial and parallel paths produce identical results."""

    def test_parallel_equivalence(self):
        """generate_candidates with num_workers=1 and 2 should match."""
        # Create 15 texts (above the threshold for parallel execution)
        base_texts = [
            "觀自在菩薩行深般若波羅蜜多時照見五蘊皆空度一切苦厄舍利子色不異空空不異色",
            "如是我聞一時佛在舍衛國祇樹給孤獨園與大比丘衆千二百五十人俱爾時世尊告諸比丘",
            "舍利弗白佛言世尊云何菩薩摩訶薩行般若波羅蜜多時應觀色受想行識無常苦空非我",
            "爾時世尊告阿難言汝今諦聽善思念之吾當為汝分別解說阿難白佛唯然世尊願樂欲聞",
            "佛告須菩提諸菩薩摩訶薩應如是降伏其心所有一切衆生之類若卵生若胎生若濕生若化生",
            "文殊師利言世尊一切法無生無滅無相無為無得無失是為法界無二無別如虛空故",
            "爾時長老須菩提即從座起偏袒右肩右膝著地合掌恭敬而白佛言希有世尊如來善護念諸菩薩",
            "觀世音菩薩即時觀察音聲即得解脫若三千大千國土衆生受諸苦惱聞是觀世音菩薩威神力故",
            "地藏菩薩本願經如來讚歎品第六爾時世尊舉身放大光明遍照百千萬億恒河沙等諸佛世界",
            "普賢菩薩行願品入不思議解脫境界善財童子五十三參第四十回參普賢菩薩處得一切佛功德海",
            "藥師琉璃光如來本願功德經如是我聞一時薄伽梵遊化諸國至廣嚴城住樂音樹下與大苾芻衆八千人俱",
            "維摩詰所說經佛國品第一如是我聞一時佛在毘耶離菴羅樹園與大比丘衆八千人俱菩薩三萬二千",
            "大般涅槃經序品第一如是我聞一時佛在拘尸那國力士生地阿利羅跋提河邊娑羅雙樹間爾時世尊",
            "妙法蓮華經方便品第二爾時世尊從三昧安詳而起告舍利弗諸佛智慧甚深無量其智慧門難解難入",
            "華嚴經入法界品善財童子參德雲比丘善財童子漸次南行至勝樂國妙峰山上見德雲比丘經行往來",
        ]
        # First text is shared across a longer "source" to create real candidates
        shared = base_texts[0]
        source_content = shared + "更多更多更多更多的佛經文字填充" * 20
        texts = [_make_text(f"T01n{i:04d}", t) for i, t in enumerate(base_texts)]
        texts.append(_make_text("T01n0099", source_content))

        doc_freq = compute_document_frequencies(texts, n=5, num_workers=1)
        stopgrams = identify_stopgrams(doc_freq, len(texts), threshold=1.0)
        ngram_sets = build_ngram_sets(texts, stopgrams, n=5, num_workers=1)

        serial = generate_candidates(texts, ngram_sets, stopgrams, num_workers=1)
        parallel = generate_candidates(texts, ngram_sets, stopgrams, num_workers=2)

        serial_pairs = {(c.digest_id, c.source_id) for c in serial}
        parallel_pairs = {(c.digest_id, c.source_id) for c in parallel}
        assert serial_pairs == parallel_pairs, (
            f"Serial found {len(serial_pairs)} pairs, parallel found {len(parallel_pairs)}. "
            f"Serial-only: {serial_pairs - parallel_pairs}, "
            f"Parallel-only: {parallel_pairs - serial_pairs}"
        )

        # Also verify containment scores match
        serial_scores = {(c.digest_id, c.source_id): c.containment_score for c in serial}
        parallel_scores = {(c.digest_id, c.source_id): c.containment_score for c in parallel}
        for key in serial_scores:
            assert abs(serial_scores[key] - parallel_scores[key]) < 1e-9, (
                f"Score mismatch for {key}: serial={serial_scores[key]}, "
                f"parallel={parallel_scores[key]}"
            )
