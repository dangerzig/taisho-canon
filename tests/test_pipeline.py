"""Tests for pipeline cache-bypass orchestration logic."""

import json
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from digest_detector.cache import PipelineCache, CACHE_VERSION, _config_snapshot
from digest_detector.models import (
    ExtractedText, TextMetadata, CandidatePair, AlignmentResult, DigestScore,
)
from digest_detector.pipeline import run_pipeline
from tests.helpers import make_text


def _make_candidate(digest_id: str, source_id: str) -> CandidatePair:
    return CandidatePair(
        digest_id=digest_id,
        source_id=source_id,
        containment_score=0.5,
        matching_ngrams=10,
        total_digest_ngrams=20,
    )


def _save_valid_cache(cache_dir: Path, xml_dir: Path, texts, candidates):
    """Write a valid cache that PipelineCache.is_valid() will accept."""
    cache = PipelineCache(cache_dir)
    cache.save(texts, candidates, xml_dir)


@pytest.fixture
def tmp_dirs(tmp_path):
    """Create temp directories for xml, results, and cache."""
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    # Create a minimal XML file so corpus_hash() works
    (xml_dir / "dummy.xml").write_text("<root/>")

    results_dir = tmp_path / "results"
    results_dir.mkdir()

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    return xml_dir, results_dir, cache_dir


# Patches for all pipeline stages so we don't need the real XML corpus
_STAGE_PATCHES = {
    "digest_detector.pipeline.extract_all": None,
    "digest_detector.pipeline.save_results": None,
    "digest_detector.pipeline.compute_document_frequencies": None,
    "digest_detector.pipeline.identify_stopgrams": None,
    "digest_detector.pipeline.build_ngram_sets": None,
    "digest_detector.pipeline.generate_candidates": None,
    "digest_detector.pipeline.align_candidates": None,
    "digest_detector.pipeline.score_all": None,
    "digest_detector.pipeline.detect_multi_source_digests": None,
    "digest_detector.pipeline.validate_ground_truth": None,
    "digest_detector.pipeline.generate_reports": None,
    "digest_detector.pipeline._save_timing": None,
}


def _patch_all_stages(texts, candidates):
    """Return a dict of patch targets → return values for all stages."""
    return {
        "digest_detector.pipeline.extract_all": texts,
        "digest_detector.pipeline.save_results": None,
        "digest_detector.pipeline.compute_document_frequencies": {},
        "digest_detector.pipeline.identify_stopgrams": set(),
        "digest_detector.pipeline.build_ngram_sets": {},
        "digest_detector.pipeline.generate_candidates": candidates,
        "digest_detector.pipeline.align_candidates": [],
        "digest_detector.pipeline.score_all": [],
        "digest_detector.pipeline.detect_multi_source_digests": [],
        "digest_detector.pipeline.validate_ground_truth": {"passed": 0, "failed": 0},
        "digest_detector.pipeline.generate_reports": None,
        "digest_detector.pipeline._save_timing": None,
    }


class TestPipelineCacheBypass:
    def test_no_cache_bypasses_valid_cache(self, tmp_dirs):
        """With no_cache=True, extract_all is called even when cache is valid."""
        xml_dir, results_dir, cache_dir = tmp_dirs
        texts = [make_text("T01n0001", "般若波羅蜜多心經觀自在菩薩")]
        candidates = [_make_candidate("T01n0001", "T01n0002")]

        _save_valid_cache(cache_dir, xml_dir, texts, candidates)

        patches = _patch_all_stages(texts, candidates)
        with patch("digest_detector.pipeline.config") as mock_config:
            mock_config.XML_DIR = xml_dir
            mock_config.RESULTS_DIR = results_dir
            mock_config.CACHE_DIR = cache_dir
            mock_config.NUM_WORKERS = 1
            mock_config.ENABLE_PHONETIC_SCAN = False

            managers = {}
            for target, return_value in patches.items():
                p = patch(target, return_value=return_value)
                managers[target] = p.start()

            try:
                run_pipeline(
                    xml_dir=xml_dir,
                    results_dir=results_dir,
                    no_cache=True,
                )
                # extract_all SHOULD have been called (cache bypassed)
                managers["digest_detector.pipeline.extract_all"].assert_called_once()
            finally:
                for p_target in patches:
                    patch.stopall()
                    break

    def test_cache_used_when_valid(self, tmp_dirs):
        """With no_cache=False, extract_all is NOT called when cache is valid."""
        xml_dir, results_dir, cache_dir = tmp_dirs
        texts = [make_text("T01n0001", "般若波羅蜜多心經觀自在菩薩")]
        candidates = [_make_candidate("T01n0001", "T01n0002")]

        _save_valid_cache(cache_dir, xml_dir, texts, candidates)

        patches = _patch_all_stages(texts, candidates)
        with patch("digest_detector.pipeline.config") as mock_config:
            mock_config.XML_DIR = xml_dir
            mock_config.RESULTS_DIR = results_dir
            mock_config.CACHE_DIR = cache_dir
            mock_config.NUM_WORKERS = 1
            mock_config.ENABLE_PHONETIC_SCAN = False

            managers = {}
            for target, return_value in patches.items():
                p = patch(target, return_value=return_value)
                managers[target] = p.start()

            try:
                run_pipeline(
                    xml_dir=xml_dir,
                    results_dir=results_dir,
                    no_cache=False,
                )
                # extract_all should NOT have been called (cache was used)
                managers["digest_detector.pipeline.extract_all"].assert_not_called()
            finally:
                patch.stopall()

    def test_cache_saved_after_fresh_run(self, tmp_dirs):
        """After a fresh run (no existing cache), cache files are written."""
        xml_dir, results_dir, cache_dir = tmp_dirs
        texts = [make_text("T01n0001", "般若波羅蜜多心經觀自在菩薩")]
        candidates = [_make_candidate("T01n0001", "T01n0002")]

        # No cache saved — verify cache dir starts empty
        assert not (cache_dir / "manifest.json").exists()

        patches = _patch_all_stages(texts, candidates)
        with patch("digest_detector.pipeline.config") as mock_config:
            mock_config.XML_DIR = xml_dir
            mock_config.RESULTS_DIR = results_dir
            mock_config.CACHE_DIR = cache_dir
            mock_config.NUM_WORKERS = 1
            mock_config.ENABLE_PHONETIC_SCAN = False

            managers = {}
            for target, return_value in patches.items():
                p = patch(target, return_value=return_value)
                managers[target] = p.start()

            try:
                run_pipeline(
                    xml_dir=xml_dir,
                    results_dir=results_dir,
                    no_cache=False,
                )
            finally:
                patch.stopall()

        # Cache files should now exist
        assert (cache_dir / "manifest.json").exists()
        assert (cache_dir / "texts.pkl").exists()
        assert (cache_dir / "candidates.pkl").exists()
