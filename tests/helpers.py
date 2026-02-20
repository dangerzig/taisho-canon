"""Shared test helpers for creating model instances."""

from digest_detector.models import (
    AlignmentResult, AlignmentSegment, CandidatePair, DigestScore,
    ExtractedText, TextMetadata,
)


def make_text(
    text_id: str,
    content: str,
    char_count: int = None,
    dharani_ranges: list[tuple[int, int]] = None,
    **meta_overrides,
) -> ExtractedText:
    """Create a minimal ExtractedText for testing.

    Args:
        text_id: Text identifier (e.g. "T08n0250").
        content: Full text content (used as both full_text and jing_text).
        char_count: Override character count (defaults to len(content)).
        dharani_ranges: Optional dharani range annotations.
        **meta_overrides: Additional TextMetadata field overrides.
    """
    if char_count is None:
        char_count = len(content)
    meta_kwargs = dict(
        text_id=text_id, title='', author='',
        extent_juan=1, char_count=char_count,
        file_count=1,
    )
    meta_kwargs.update(meta_overrides)
    return ExtractedText(
        text_id=text_id,
        full_text=content,
        segments=[],
        metadata=TextMetadata(**meta_kwargs),
        dharani_ranges=dharani_ranges or [],
    )


def make_metadata(text_id: str, char_count: int = 100,
                  title: str = "", **overrides) -> TextMetadata:
    """Create a minimal TextMetadata for testing."""
    kwargs = dict(
        text_id=text_id, title=title, author='',
        extent_juan=1, char_count=char_count,
        file_count=1,
    )
    kwargs.update(overrides)
    return TextMetadata(**kwargs)


def make_segment(d_start: int, d_end: int,
                 s_start: int = 0, s_end: int = 0,
                 match_type: str = "exact",
                 digest_text: str = "", source_text: str = "",
                 phonetic_mapping=None) -> AlignmentSegment:
    """Create a minimal AlignmentSegment for testing."""
    return AlignmentSegment(
        digest_start=d_start, digest_end=d_end,
        source_start=s_start, source_end=s_end,
        match_type=match_type,
        digest_text=digest_text or "x" * (d_end - d_start),
        source_text=source_text or ("y" * (s_end - s_start) if match_type != "novel" else ""),
        phonetic_mapping=phonetic_mapping or [],
    )


def make_alignment(digest_id: str = "d", source_id: str = "s",
                   coverage: float = 0.0, novel_fraction: float = 1.0,
                   source_span: float = 0.0, num_source_regions: int = 0,
                   segments: list = None) -> AlignmentResult:
    """Create a minimal AlignmentResult for testing."""
    return AlignmentResult(
        digest_id=digest_id, source_id=source_id,
        segments=segments if segments is not None else [],
        coverage=coverage, novel_fraction=novel_fraction,
        source_span=source_span, num_source_regions=num_source_regions,
    )


def make_score(digest_id: str = "d", source_id: str = "s",
               classification: str = "digest", confidence: float = 0.6,
               coverage: float = 0.50, **overrides) -> DigestScore:
    """Create a minimal DigestScore for testing."""
    kwargs = dict(
        digest_id=digest_id, source_id=source_id,
        classification=classification, confidence=confidence,
        containment=coverage, coverage=coverage,
        novel_fraction=1.0 - coverage,
        avg_segment_length=15.0, longest_segment=30,
        num_source_regions=2, source_span=0.01,
        has_docnumber_xref=False, phonetic_coverage=0.0,
    )
    kwargs.update(overrides)
    return DigestScore(**kwargs)


def make_candidate(digest_id: str, source_id: str,
                   **overrides) -> CandidatePair:
    """Create a minimal CandidatePair for testing."""
    kwargs = dict(
        digest_id=digest_id, source_id=source_id,
        containment_score=0.5, matching_ngrams=10,
        total_digest_ngrams=20,
    )
    kwargs.update(overrides)
    return CandidatePair(**kwargs)
