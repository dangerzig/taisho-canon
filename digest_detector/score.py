"""Stage 4: Scoring and classification of digest relationships.

Classifies alignment results into categories (full digest, partial digest,
commentary, shared tradition, retranslation) and computes confidence scores.
Also detects multi-source digests.
"""

import logging
import math
from collections import defaultdict

from . import config
from .models import (
    AlignmentResult, AlignmentSegment, DigestScore, ExtractedText,
    MultiSourceDigest, TextMetadata,
)

logger = logging.getLogger(__name__)


def _avg_segment_length(segments: list[AlignmentSegment]) -> float:
    """Compute average length of matched (non-novel) segments."""
    matched = [s for s in segments if s.match_type != "novel"]
    if not matched:
        return 0.0
    return sum(s.digest_end - s.digest_start for s in matched) / len(matched)


def _longest_segment(segments: list[AlignmentSegment]) -> int:
    """Find the longest matched segment."""
    matched = [s for s in segments if s.match_type != "novel"]
    if not matched:
        return 0
    return max(s.digest_end - s.digest_start for s in matched)


def classify_relationship(
    alignment: AlignmentResult,
    digest_length: int,
    source_length: int,
    has_docnumber_xref: bool = False,
    digest_jing_length: int = None,
    source_jing_length: int = None,
) -> DigestScore:
    """Classify an alignment result into a relationship category.

    Categories:
    - full_digest: coverage >= 0.70, avg segment >= 15 chars
    - partial_digest: coverage 0.30-0.70, avg segment >= 10 chars
    - commentary: coverage 0.20-0.70, avg segment < 10 chars
    - shared_tradition: coverage 0.10-0.30
    - retranslation: coverage >= 0.30, similar length texts
    - no_relationship: coverage < 0.10
    """
    coverage = alignment.coverage
    avg_seg_len = _avg_segment_length(alignment.segments)
    longest_seg = _longest_segment(alignment.segments)
    # Use jing lengths for size ratio when available (avoids preface inflation)
    d_len = digest_jing_length if digest_jing_length is not None else digest_length
    s_len = source_jing_length if source_jing_length is not None else source_length
    size_ratio = s_len / d_len if d_len > 0 else 1.0

    # Classification logic
    if coverage < config.SHARED_TRADITION_THRESHOLD:
        classification = "no_relationship"
    elif coverage < config.PARTIAL_DIGEST_THRESHOLD:
        classification = "shared_tradition"
    elif size_ratio < config.RETRANSLATION_SIZE_RATIO and coverage >= config.PARTIAL_DIGEST_THRESHOLD:
        # Texts of similar length with significant overlap → retranslation
        classification = "retranslation"
    elif coverage >= config.FULL_DIGEST_THRESHOLD and avg_seg_len >= 15:
        classification = "full_digest"
    elif coverage >= config.PARTIAL_DIGEST_THRESHOLD and avg_seg_len >= config.COMMENTARY_AVG_SEG_LEN:
        classification = "partial_digest"
    elif coverage >= 0.20 and avg_seg_len < config.COMMENTARY_AVG_SEG_LEN:
        classification = "commentary"
    else:
        classification = "partial_digest"

    # Confidence score
    confidence = _compute_confidence(
        coverage=coverage,
        longest_seg=longest_seg,
        num_regions=alignment.num_source_regions,
        size_ratio=size_ratio,
        has_docnumber_xref=has_docnumber_xref,
        avg_seg_len=avg_seg_len,
        digest_length=digest_jing_length if digest_jing_length is not None else digest_length,
    )

    return DigestScore(
        digest_id=alignment.digest_id,
        source_id=alignment.source_id,
        classification=classification,
        confidence=confidence,
        containment=coverage,
        coverage=coverage,
        novel_fraction=alignment.novel_fraction,
        avg_segment_length=avg_seg_len,
        longest_segment=longest_seg,
        num_source_regions=alignment.num_source_regions,
        source_span=alignment.source_span,
        has_docnumber_xref=has_docnumber_xref,
    )


def _compute_confidence(
    coverage: float,
    longest_seg: int,
    num_regions: int,
    size_ratio: float,
    has_docnumber_xref: bool,
    avg_seg_len: float,
    digest_length: int,
) -> float:
    """Compute weighted confidence score (0-1)."""
    # Containment component (0-1)
    c_containment = min(coverage, 1.0)

    # Longest segment, normalized by digest length (0-1)
    c_longest = min(longest_seg / max(digest_length, 1), 1.0)

    # Number of source regions — more scattered excerpts are more meaningful
    # Normalize: 1 region → 0.2, 5+ regions → 1.0
    c_regions = min((num_regions - 1) / 4.0, 1.0) if num_regions > 0 else 0.0

    # Length asymmetry: extreme size ratio is more suggestive of digest
    # log2(ratio): 2x→1, 4x→2, 100x→6.6; normalize to 0-1
    c_asymmetry = min(math.log2(max(size_ratio, 1.0)) / 10.0, 1.0)

    # DocNumber cross-reference (binary)
    c_docnum = 1.0 if has_docnumber_xref else 0.0

    # Average segment length, normalized (0-1)
    # 5 chars → 0.25, 20 chars → 1.0
    c_avg_seg = min(avg_seg_len / 20.0, 1.0)

    confidence = (
        config.WEIGHT_CONTAINMENT * c_containment +
        config.WEIGHT_LONGEST_SEGMENT * c_longest +
        config.WEIGHT_NUM_REGIONS * c_regions +
        config.WEIGHT_LENGTH_ASYMMETRY * c_asymmetry +
        config.WEIGHT_DOCNUMBER_XREF * c_docnum +
        config.WEIGHT_AVG_SEGMENT_LEN * c_avg_seg
    )

    return round(min(confidence, 1.0), 4)


def score_all(
    alignments: list[AlignmentResult],
    metadata_map: dict[str, TextMetadata],
    docnumber_pairs: set[tuple[str, str]] = None,
    text_map: dict[str, ExtractedText] = None,
) -> list[DigestScore]:
    """Score and classify all alignment results.

    Returns list of DigestScore objects, filtered to exclude no_relationship.
    """
    if docnumber_pairs is None:
        docnumber_pairs = set()
    if text_map is None:
        text_map = {}

    scores = []
    for alignment in alignments:
        d_meta = metadata_map.get(alignment.digest_id)
        s_meta = metadata_map.get(alignment.source_id)
        if not d_meta or not s_meta:
            continue

        has_xref = (alignment.digest_id, alignment.source_id) in docnumber_pairs

        # Compute jing lengths for size ratio comparison
        d_extracted = text_map.get(alignment.digest_id)
        s_extracted = text_map.get(alignment.source_id)
        d_jing_len = len(d_extracted.jing_text) if d_extracted else None
        s_jing_len = len(s_extracted.jing_text) if s_extracted else None

        score = classify_relationship(
            alignment,
            digest_length=d_meta.char_count,
            source_length=s_meta.char_count,
            has_docnumber_xref=has_xref,
            digest_jing_length=d_jing_len,
            source_jing_length=s_jing_len,
        )

        if score.classification != "no_relationship":
            scores.append(score)

    scores.sort(key=lambda s: s.confidence, reverse=True)
    logger.info("Scored %d relationships (%d non-trivial)",
                len(alignments), len(scores))
    return scores


def detect_multi_source_digests(
    scores: list[DigestScore],
    alignments: list[AlignmentResult],
    metadata_map: dict[str, TextMetadata],
) -> list[MultiSourceDigest]:
    """Detect texts that are digests of multiple sources.

    If the combined coverage from multiple sources exceeds any single source,
    flag as multi-source digest.
    """
    # Group scores by digest
    by_digest = defaultdict(list)
    for score in scores:
        if score.classification in ("full_digest", "partial_digest"):
            by_digest[score.digest_id].append(score)

    # Group alignments by digest for coverage calculation
    alignment_map = {}
    for a in alignments:
        alignment_map[(a.digest_id, a.source_id)] = a

    multi_source = []
    for digest_id, digest_scores in by_digest.items():
        if len(digest_scores) < 2:
            continue

        # Best single source
        best_single = max(digest_scores, key=lambda s: s.coverage)

        # Estimate combined coverage (union of matched intervals)
        intervals = []
        for score in digest_scores:
            key = (score.digest_id, score.source_id)
            alignment = alignment_map.get(key)
            if alignment:
                for seg in alignment.segments:
                    if seg.match_type != "novel":
                        intervals.append((seg.digest_start, seg.digest_end))

        # Use actual digest length from metadata
        d_meta = metadata_map.get(digest_id)
        d_len = d_meta.char_count if d_meta else 0

        if intervals and d_len > 0:
            # Merge overlapping intervals to compute union coverage
            intervals.sort()
            merged_len = 0
            cur_start, cur_end = intervals[0]
            for s, e in intervals[1:]:
                if s <= cur_end:
                    cur_end = max(cur_end, e)
                else:
                    merged_len += cur_end - cur_start
                    cur_start, cur_end = s, e
            merged_len += cur_end - cur_start
            combined_coverage = merged_len / d_len
        else:
            combined_coverage = 0.0

        if combined_coverage > best_single.coverage * 1.1:  # 10% improvement
            multi_source.append(MultiSourceDigest(
                digest_id=digest_id,
                sources=sorted(digest_scores, key=lambda s: s.coverage, reverse=True),
                combined_coverage=combined_coverage,
            ))

    logger.info("Found %d multi-source digests", len(multi_source))
    return multi_source
