"""Dataclasses for the digest detection pipeline."""

from dataclasses import dataclass, field


@dataclass
class TextMetadata:
    """Metadata for a single extracted text."""
    text_id: str  # e.g. "T08n0223"
    title: str  # e.g. "摩訶般若波羅蜜經"
    author: str  # e.g. "後秦 鳩摩羅什譯"
    extent_juan: int  # e.g. 27
    char_count: int  # after normalization
    file_count: int
    docnumber_refs: list[str] = field(default_factory=list)  # e.g. ["251", "252"]
    div_types: list[str] = field(default_factory=list)  # e.g. ["jing", "xu"]
    has_dharani: bool = False


@dataclass
class DivSegment:
    """A segment of text with its div type annotation."""
    div_type: str  # "jing", "xu", "pin", etc.
    text: str  # normalized CJK text
    start: int  # char offset in the full concatenated text
    end: int


@dataclass
class ExtractedText:
    """Full extracted text with div-level segmentation."""
    text_id: str
    full_text: str  # all CJK chars concatenated
    segments: list[DivSegment] = field(default_factory=list)
    metadata: TextMetadata | None = None

    @property
    def jing_text(self) -> str:
        """Return only jing-segment text, falling back to full_text."""
        jing_segs = [seg.text for seg in self.segments if seg.div_type == 'jing']
        if jing_segs:
            return ''.join(jing_segs)
        return self.full_text


@dataclass
class CandidatePair:
    """A candidate digest-source pair from Stage 2."""
    digest_id: str
    source_id: str
    containment_score: float
    matching_ngrams: int
    total_digest_ngrams: int
    from_docnumber: bool = False  # True if pair came from docNumber cross-ref


@dataclass
class AlignmentSegment:
    """A single aligned segment between digest and source."""
    digest_start: int  # char position in digest
    digest_end: int
    source_start: int  # char position in source (-1 if novel)
    source_end: int
    match_type: str  # "exact", "fuzzy", "novel"
    digest_text: str
    source_text: str  # empty if novel


@dataclass
class AlignmentResult:
    """Full alignment result for a digest-source pair."""
    digest_id: str
    source_id: str
    segments: list[AlignmentSegment] = field(default_factory=list)
    coverage: float = 0.0  # fraction of digest explained by source
    novel_fraction: float = 1.0
    source_span: float = 0.0  # fraction of source that contributes
    num_source_regions: int = 0  # number of disjoint source regions used


@dataclass
class DigestScore:
    """Scored and classified digest relationship."""
    digest_id: str
    source_id: str
    classification: str  # "excerpt", "digest", "commentary", etc.
    confidence: float  # 0-1 weighted score
    containment: float
    coverage: float
    novel_fraction: float
    avg_segment_length: float
    longest_segment: int
    num_source_regions: int
    source_span: float
    has_docnumber_xref: bool = False


@dataclass
class MultiSourceDigest:
    """A text identified as a digest of multiple sources."""
    digest_id: str
    sources: list[DigestScore] = field(default_factory=list)
    combined_coverage: float = 0.0
