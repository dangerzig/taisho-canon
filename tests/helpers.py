"""Shared test helpers for creating model instances."""

from digest_detector.models import ExtractedText, TextMetadata


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
