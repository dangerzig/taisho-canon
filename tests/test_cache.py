"""Tests for PipelineCache: save/load roundtrip and invalidation."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from digest_detector.cache import PipelineCache, CACHE_VERSION, _config_snapshot
# CACHE_VERSION is checked dynamically from import, so this test stays current
from digest_detector.models import (
    ExtractedText, TextMetadata, CandidatePair,
)


@pytest.fixture
def cache_dir(tmp_path):
    return tmp_path / "cache"


@pytest.fixture
def xml_dir(tmp_path):
    """Create a tiny XML corpus directory for hashing."""
    d = tmp_path / "xml"
    d.mkdir()
    (d / "sample.xml").write_text("<root>hello</root>")
    return d


@pytest.fixture
def sample_data():
    texts = [
        ExtractedText(
            text_id="T01n0001",
            full_text="測試文字內容",
            segments=[],
            metadata=TextMetadata(
                text_id="T01n0001", title="Test", author="Author",
                extent_juan=1, char_count=6, file_count=1,
            ),
        ),
    ]
    candidates = [
        CandidatePair(
            digest_id="T01n0001", source_id="T01n0002",
            containment_score=0.5, matching_ngrams=10,
            total_digest_ngrams=20,
        ),
    ]
    return texts, candidates


class TestCacheRoundtrip:
    def test_save_and_load(self, cache_dir, xml_dir, sample_data):
        """Saving and loading should roundtrip correctly."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data

        cache.save(texts, candidates, xml_dir)
        loaded_texts, loaded_candidates = cache.load()

        assert len(loaded_texts) == 1
        assert loaded_texts[0].text_id == "T01n0001"
        assert loaded_texts[0].full_text == "測試文字內容"

        assert len(loaded_candidates) == 1
        assert loaded_candidates[0].digest_id == "T01n0001"
        assert loaded_candidates[0].containment_score == 0.5

    def test_manifest_written(self, cache_dir, xml_dir, sample_data):
        """Manifest should record cache_version, config, corpus hash, and counts."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)

        manifest = json.loads(cache.manifest_path.read_text())
        assert manifest["num_texts"] == 1
        assert manifest["num_candidates"] == 1
        assert "corpus_hash" in manifest
        assert manifest["cache_version"] == CACHE_VERSION
        assert manifest["config"] == _config_snapshot()

    def test_manifest_config_snapshot_complete(self):
        """Config snapshot should contain all expected Stage 1-2b parameters."""
        snapshot = _config_snapshot()
        expected_keys = {
            "NGRAM_SIZE", "STOPGRAM_DOC_FREQ", "MIN_CONTAINMENT",
            "MIN_SIZE_RATIO", "MAX_DIGEST_LENGTH", "ENABLE_PHONETIC_SCAN",
            "MIN_PHONETIC_CONTAINMENT", "PHONETIC_STOPGRAM_DOC_FREQ",
            "PHONETIC_NGRAM_SIZE", "TRANSLITERATION_DENSITY",
            "TRANSLITERATION_WINDOW", "MIN_TRANSLITERATION_LENGTH",
            "MIN_TEXT_LENGTH",
        }
        assert set(snapshot.keys()) == expected_keys


class TestCacheValidation:
    def test_valid_cache(self, cache_dir, xml_dir, sample_data):
        """Cache should be valid when corpus hasn't changed."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)

        assert cache.is_valid(xml_dir) is True

    def test_invalid_when_empty(self, cache_dir, xml_dir):
        """Cache should be invalid when no files exist."""
        cache = PipelineCache(cache_dir)
        assert cache.is_valid(xml_dir) is False

    def test_invalid_when_corpus_changes(self, cache_dir, xml_dir, sample_data):
        """Cache should be invalid after corpus changes."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)

        # Modify a file
        (xml_dir / "sample.xml").write_text("<root>changed</root>")

        assert cache.is_valid(xml_dir) is False

    def test_invalid_when_file_added(self, cache_dir, xml_dir, sample_data):
        """Cache should be invalid when a new XML file is added."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)

        # Add a new file
        (xml_dir / "new.xml").write_text("<root>new</root>")

        assert cache.is_valid(xml_dir) is False

    def test_invalid_when_file_deleted(self, cache_dir, xml_dir, sample_data):
        """Cache should be invalid when an XML file is deleted."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data

        # Add a second file so we can delete one
        (xml_dir / "extra.xml").write_text("<root>extra</root>")
        cache.save(texts, candidates, xml_dir)
        assert cache.is_valid(xml_dir) is True

        # Delete the extra file
        (xml_dir / "extra.xml").unlink()
        assert cache.is_valid(xml_dir) is False

    def test_invalid_when_config_changes(self, cache_dir, xml_dir, sample_data):
        """Cache should be invalid when a config parameter changes."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)
        assert cache.is_valid(xml_dir) is True

        # Patch a config value to simulate a change
        import digest_detector.config as cfg
        original = cfg.NGRAM_SIZE
        try:
            cfg.NGRAM_SIZE = 7
            assert cache.is_valid(xml_dir) is False
        finally:
            cfg.NGRAM_SIZE = original

    def test_invalid_when_cache_version_changes(self, cache_dir, xml_dir, sample_data):
        """Cache should be invalid when CACHE_VERSION is bumped."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)

        # Tamper with the version in the manifest
        manifest = json.loads(cache.manifest_path.read_text())
        manifest["cache_version"] = CACHE_VERSION - 1
        cache.manifest_path.write_text(json.dumps(manifest))

        assert cache.is_valid(xml_dir) is False

    def test_invalid_when_pickle_deleted(self, cache_dir, xml_dir, sample_data):
        """Cache should be invalid when a pickle file is missing."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)
        assert cache.is_valid(xml_dir) is True

        # Delete texts.pkl
        cache.texts_path.unlink()
        assert cache.is_valid(xml_dir) is False

    def test_invalid_when_manifest_corrupted(self, cache_dir, xml_dir, sample_data):
        """Cache should be invalid when manifest JSON is corrupted."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data
        cache.save(texts, candidates, xml_dir)

        # Corrupt the manifest
        cache.manifest_path.write_text("{corrupt json")
        assert cache.is_valid(xml_dir) is False


class TestCorpusHash:
    def test_deterministic(self, xml_dir):
        """Same corpus should produce same hash."""
        cache = PipelineCache(Path("/tmp/unused"))
        h1 = cache.corpus_hash(xml_dir)
        h2 = cache.corpus_hash(xml_dir)
        assert h1 == h2

    def test_changes_with_content(self, xml_dir):
        """Hash should change when file content changes."""
        cache = PipelineCache(Path("/tmp/unused"))
        h1 = cache.corpus_hash(xml_dir)
        (xml_dir / "sample.xml").write_text("<root>modified</root>")
        h2 = cache.corpus_hash(xml_dir)
        assert h1 != h2

    def test_cached_between_is_valid_and_save(self, cache_dir, xml_dir, sample_data):
        """corpus_hash should be cached between is_valid() and save() calls."""
        cache = PipelineCache(cache_dir)
        texts, candidates = sample_data

        # First save (computes hash)
        cache.save(texts, candidates, xml_dir)

        # Create fresh cache instance
        cache2 = PipelineCache(cache_dir)
        assert cache2._corpus_hash is None

        # is_valid computes and caches the hash
        cache2.is_valid(xml_dir)
        assert cache2._corpus_hash is not None
        cached_hash = cache2._corpus_hash

        # save should reuse the cached hash
        cache2.save(texts, candidates, xml_dir)
        manifest = json.loads(cache2.manifest_path.read_text())
        assert manifest["corpus_hash"] == cached_hash
