"""Disk cache for expensive pipeline stage outputs.

Caches Stage 1-2 results (extracted texts + candidate pairs) so that
subsequent runs can skip straight to Stage 3 (alignment) when the
XML corpus hasn't changed.
"""

import hashlib
import json
import logging
import pickle
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

# Bump this when dataclass fields change (ExtractedText, CandidatePair, etc.)
# to force cache invalidation rather than silent pickle breakage.
CACHE_VERSION = 3


def _config_snapshot() -> dict:
    """Capture config parameters that affect Stage 1-2b outputs.

    If any of these change, cached candidates are stale.
    """
    return {
        "NGRAM_SIZE": config.NGRAM_SIZE,
        "STOPGRAM_DOC_FREQ": config.STOPGRAM_DOC_FREQ,
        "MIN_CONTAINMENT": config.MIN_CONTAINMENT,
        "MIN_SIZE_RATIO": config.MIN_SIZE_RATIO,
        "MAX_DIGEST_LENGTH": config.MAX_DIGEST_LENGTH,
        "ENABLE_PHONETIC_SCAN": config.ENABLE_PHONETIC_SCAN,
        "MIN_PHONETIC_CONTAINMENT": config.MIN_PHONETIC_CONTAINMENT,
        "PHONETIC_STOPGRAM_DOC_FREQ": config.PHONETIC_STOPGRAM_DOC_FREQ,
        "PHONETIC_NGRAM_SIZE": config.PHONETIC_NGRAM_SIZE,
        "TRANSLITERATION_DENSITY": config.TRANSLITERATION_DENSITY,
        "TRANSLITERATION_WINDOW": config.TRANSLITERATION_WINDOW,
        "MIN_TRANSLITERATION_LENGTH": config.MIN_TRANSLITERATION_LENGTH,
        "MIN_TEXT_LENGTH": config.MIN_TEXT_LENGTH,
    }


class PipelineCache:
    """Disk cache for expensive pipeline stage outputs."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.texts_path = cache_dir / "texts.pkl"
        self.candidates_path = cache_dir / "candidates.pkl"
        self.manifest_path = cache_dir / "manifest.json"
        self._corpus_hash: str | None = None  # cached between is_valid/save

    def corpus_hash(self, xml_dir: Path) -> str:
        """SHA256 of sorted (relative_path, mtime, size) for all XML files."""
        entries = []
        for xml_file in sorted(xml_dir.rglob("*.xml")):
            stat = xml_file.stat()
            rel = str(xml_file.relative_to(xml_dir))
            entries.append(f"{rel}:{stat.st_mtime_ns}:{stat.st_size}")
        digest = hashlib.sha256("\n".join(entries).encode()).hexdigest()
        self._corpus_hash = digest
        return digest

    def is_valid(self, xml_dir: Path) -> bool:
        """Check if cache exists and matches current corpus + config."""
        if not all(p.exists() for p in
                   [self.texts_path, self.candidates_path, self.manifest_path]):
            return False
        try:
            with open(self.manifest_path) as f:
                manifest = json.load(f)
            if manifest.get("cache_version") != CACHE_VERSION:
                return False
            if manifest.get("config") != _config_snapshot():
                return False
            return manifest.get("corpus_hash") == self.corpus_hash(xml_dir)
        except (json.JSONDecodeError, OSError):
            return False

    def save(self, texts, candidates, xml_dir: Path):
        """Save texts and candidates to disk cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self.texts_path, "wb") as f:
            pickle.dump(texts, f, protocol=pickle.HIGHEST_PROTOCOL)
        with open(self.candidates_path, "wb") as f:
            pickle.dump(candidates, f, protocol=pickle.HIGHEST_PROTOCOL)
        # Reuse hash from is_valid() if available, else compute
        c_hash = self._corpus_hash or self.corpus_hash(xml_dir)
        manifest = {
            "cache_version": CACHE_VERSION,
            "corpus_hash": c_hash,
            "config": _config_snapshot(),
            "num_texts": len(texts),
            "num_candidates": len(candidates),
        }
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info("Saved cache: %d texts, %d candidates to %s",
                     len(texts), len(candidates), self.cache_dir)

    def load(self) -> tuple[list, list]:
        """Load texts and candidates from disk cache.

        Returns:
            Tuple of (list[ExtractedText], list[CandidatePair]).
        """
        with open(self.texts_path, "rb") as f:
            texts = pickle.load(f)
        with open(self.candidates_path, "rb") as f:
            candidates = pickle.load(f)
        return texts, candidates
