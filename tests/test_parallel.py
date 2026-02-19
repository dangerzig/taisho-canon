"""Tests verifying parallel and serial code paths produce identical results.

These ensure that multiprocessing workers (with Pool initializer pattern)
produce the same output as the serial fallback path.
"""

import pytest

from digest_detector.fingerprint import (
    compute_document_frequencies,
    build_ngram_sets,
    identify_stopgrams,
)
from digest_detector.candidates import generate_phonetic_candidates
from digest_detector.phonetic import build_equivalence_table
from digest_detector.models import ExtractedText, TextMetadata


def _make_text(text_id: str, content: str, dharani_ranges=None) -> ExtractedText:
    """Helper to create a minimal ExtractedText."""
    return ExtractedText(
        text_id=text_id,
        full_text=content,
        segments=[],
        metadata=TextMetadata(
            text_id=text_id, title='', author='',
            extent_juan=1, char_count=len(content),
            file_count=1,
        ),
        dharani_ranges=dharani_ranges or [],
    )


@pytest.fixture(scope="module")
def sample_texts():
    """A set of 15 texts (above the threshold for parallel execution)."""
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
    return [_make_text(f"T01n{i:04d}", text) for i, text in enumerate(base_texts)]


@pytest.fixture(scope="module")
def phonetic_table():
    return build_equivalence_table()


class TestDocFreqParallel:
    def test_serial_vs_parallel(self, sample_texts):
        """compute_document_frequencies: serial (1 worker) == parallel (2 workers)."""
        serial = compute_document_frequencies(sample_texts, n=5, num_workers=1)
        parallel = compute_document_frequencies(sample_texts, n=5, num_workers=2)
        assert serial == parallel

    def test_parallel_nonzero(self, sample_texts):
        """Parallel path should produce non-trivial output."""
        result = compute_document_frequencies(sample_texts, n=5, num_workers=2)
        assert len(result) > 100


class TestNgramSetsParallel:
    def test_serial_vs_parallel(self, sample_texts):
        """build_ngram_sets: serial (1 worker) == parallel (2 workers)."""
        doc_freq = compute_document_frequencies(sample_texts, n=5, num_workers=1)
        stopgrams = identify_stopgrams(doc_freq, len(sample_texts), threshold=1.0)

        serial = build_ngram_sets(sample_texts, stopgrams, n=5, num_workers=1)
        parallel = build_ngram_sets(sample_texts, stopgrams, n=5, num_workers=2)

        assert serial.keys() == parallel.keys()
        for text_id in serial:
            assert serial[text_id] == parallel[text_id], (
                f"Mismatch for {text_id}: "
                f"serial has {len(serial[text_id])} hashes, "
                f"parallel has {len(parallel[text_id])} hashes"
            )


class TestPhoneticCandidatesParallel:
    def _make_dharani_texts(self, phonetic_table):
        """Create 15 texts with dharani regions for phonetic candidate testing."""
        # Use actual transliteration characters from the table
        table_chars = list(phonetic_table.keys())[:20]
        dharani_block = ''.join(table_chars)

        texts = []
        for i in range(15):
            # Vary padding to give different char_counts
            padding = "觀自在菩薩行深般若波羅蜜多時" * (i + 3)
            full_text = padding + dharani_block + padding
            dr_start = len(padding)
            dr_end = dr_start + len(dharani_block)
            texts.append(_make_text(
                f"T01n{i:04d}", full_text,
                dharani_ranges=[(dr_start, dr_end)],
            ))
        return texts

    def test_serial_vs_parallel(self, phonetic_table):
        """generate_phonetic_candidates: serial (1 worker) == parallel (2 workers)."""
        texts = self._make_dharani_texts(phonetic_table)

        serial = generate_phonetic_candidates(texts, phonetic_table, num_workers=1)
        parallel = generate_phonetic_candidates(texts, phonetic_table, num_workers=2)

        serial_pairs = {(c.digest_id, c.source_id) for c in serial}
        parallel_pairs = {(c.digest_id, c.source_id) for c in parallel}
        assert serial_pairs == parallel_pairs, (
            f"Serial found {len(serial_pairs)} pairs, parallel found {len(parallel_pairs)}. "
            f"Serial-only: {serial_pairs - parallel_pairs}, "
            f"Parallel-only: {parallel_pairs - serial_pairs}"
        )
