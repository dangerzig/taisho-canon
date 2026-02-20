"""Stage 5: Validation and report generation.

Validates results against known T250/T251→T223 ground truth and generates
JSON + Markdown reports with alignment visualizations.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path

try:
    import orjson
    _HAS_ORJSON = True
except ImportError:
    _HAS_ORJSON = False

from . import config
from .models import (
    AlignmentResult, AlignmentSegment, DigestScore, MultiSourceDigest,
    TextMetadata,
)

logger = logging.getLogger(__name__)

# Ground truth expectations
GROUND_TRUTH = {
    ('T08n0250', 'T08n0223'): {
        'expected_class': 'digest',
        'min_coverage': 0.70,
        'description': 'T250 (Kumārajīva Heart Sutra) is a digest of T223',
    },
    ('T08n0251', 'T08n0223'): {
        'expected_class': 'digest',
        'min_coverage': 0.30,
        'description': 'T251 (Xuanzang Heart Sutra) jing section is a digest of T223',
    },
}


def validate_ground_truth(
    scores: list[DigestScore],
    alignments: list[AlignmentResult],
    metadata_map: dict[str, TextMetadata],
) -> dict:
    """Validate pipeline results against known digest relationships.

    Returns a validation report dict.
    """
    score_map = {(s.digest_id, s.source_id): s for s in scores}
    alignment_map = {(a.digest_id, a.source_id): a for a in alignments}

    report = {'tests': [], 'passed': 0, 'failed': 0}

    for (digest_id, source_id), expected in GROUND_TRUTH.items():
        test = {
            'digest_id': digest_id,
            'source_id': source_id,
            'description': expected['description'],
            'checks': [],
        }

        score = score_map.get((digest_id, source_id))
        alignment = alignment_map.get((digest_id, source_id))

        if score is None:
            test['checks'].append({
                'check': 'pair_found',
                'passed': False,
                'detail': 'Pair not found in scored results',
            })
            report['failed'] += 1
        else:
            # Check classification
            class_ok = score.classification == expected['expected_class']
            test['checks'].append({
                'check': 'classification',
                'passed': class_ok,
                'expected': expected['expected_class'],
                'actual': score.classification,
            })
            if class_ok:
                report['passed'] += 1
            else:
                report['failed'] += 1

            # Check minimum coverage
            cov_ok = score.coverage >= expected['min_coverage']
            test['checks'].append({
                'check': 'coverage',
                'passed': cov_ok,
                'expected': f">= {expected['min_coverage']}",
                'actual': round(score.coverage, 4),
            })
            if cov_ok:
                report['passed'] += 1
            else:
                report['failed'] += 1

            # Additional info
            test['score'] = {
                'classification': score.classification,
                'confidence': score.confidence,
                'coverage': round(score.coverage, 4),
                'novel_fraction': round(score.novel_fraction, 4),
                'avg_segment_length': round(score.avg_segment_length, 2),
                'longest_segment': score.longest_segment,
                'num_source_regions': score.num_source_regions,
            }

        report['tests'].append(test)

    # Check T250 is NOT classified as digest of T251 (or vice versa)
    for d, s in [('T08n0250', 'T08n0251'), ('T08n0251', 'T08n0250')]:
        score = score_map.get((d, s))
        check_ok = score is None or score.classification in ('shared_tradition', 'retranslation', 'no_relationship')
        report['tests'].append({
            'digest_id': d,
            'source_id': s,
            'description': f'{d} should NOT be classified as digest of {s}',
            'checks': [{
                'check': 'not_digest_of_each_other',
                'passed': check_ok,
                'actual': score.classification if score else 'not_found',
            }],
        })
        if check_ok:
            report['passed'] += 1
        else:
            report['failed'] += 1

    return report


def _format_alignment_visualization(
    alignment: AlignmentResult,
    score: DigestScore,
    metadata_map: dict[str, TextMetadata],
    max_text_preview: int = 30,
) -> str:
    """Generate text-based alignment visualization."""
    d_meta = metadata_map.get(alignment.digest_id)
    s_meta = metadata_map.get(alignment.source_id)
    d_title = d_meta.title if d_meta else ''
    s_title = s_meta.title if s_meta else ''

    lines = []
    lines.append(f"{alignment.digest_id} ({d_title}) → {alignment.source_id} ({s_title})")
    cov_line = (f"Coverage: {score.coverage:.0%} | "
                f"Novel: {score.novel_fraction:.0%} | "
                f"Confidence: {score.confidence:.2f} | "
                f"Class: {score.classification}")
    if score.phonetic_coverage > 0:
        cov_line += f" | Phonetic: {score.phonetic_coverage:.0%}"
    lines.append(cov_line)
    lines.append("")
    lines.append(f"{'DIGEST':<45} SOURCE")
    lines.append("-" * 90)

    for seg in alignment.segments:
        d_preview = seg.digest_text[:max_text_preview]
        if len(seg.digest_text) > max_text_preview:
            d_preview += "..."
        d_range = f"[{seg.digest_start}-{seg.digest_end}]"

        if seg.match_type == "novel":
            lines.append(f"{d_range:<10} {d_preview:<34} [NOVEL]")
        else:
            s_preview = seg.source_text[:max_text_preview]
            if len(seg.source_text) > max_text_preview:
                s_preview += "..."
            s_range = f"pos {seg.source_start}-{seg.source_end}"
            match_label = seg.match_type.upper()
            lines.append(
                f"{d_range:<10} {d_preview:<34} "
                f"{alignment.source_id} {s_range} ({match_label})"
            )
            if seg.match_type == "phonetic" and seg.phonetic_mapping:
                # Show char-by-char transliteration mapping
                mapping_strs = [f"{d_ch}→{syl}←{s_ch}"
                                for d_ch, syl, s_ch in seg.phonetic_mapping
                                if d_ch != s_ch]
                if mapping_strs:
                    lines.append(f"{'':10} Transliteration: "
                                 + " ".join(mapping_strs[:15]))

    return '\n'.join(lines)


def _segment_to_dict(seg: AlignmentSegment) -> dict:
    """Convert an AlignmentSegment to a JSON-serializable dict."""
    d = {
        'digest_start': seg.digest_start,
        'digest_end': seg.digest_end,
        'source_start': seg.source_start,
        'source_end': seg.source_end,
        'match_type': seg.match_type,
        'digest_text': seg.digest_text,
        'source_text': seg.source_text,
    }
    if seg.match_type == "phonetic" and seg.phonetic_mapping:
        d['phonetic_mapping'] = [
            {'digest_char': d_ch, 'syllable': syl, 'source_char': s_ch}
            for d_ch, syl, s_ch in seg.phonetic_mapping
        ]
    return d


def _write_json(path: Path, data) -> None:
    """Write JSON to file, using orjson if available for speed."""
    if _HAS_ORJSON:
        with open(path, 'wb') as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    else:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def generate_reports(
    scores: list[DigestScore],
    alignments: list[AlignmentResult],
    multi_source: list[MultiSourceDigest],
    metadata_map: dict[str, TextMetadata],
    validation: dict,
    results_dir: Path = None,
):
    """Generate all output reports."""
    if results_dir is None:
        results_dir = config.RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)
    alignments_dir = results_dir / "alignments"
    alignments_dir.mkdir(parents=True, exist_ok=True)

    score_map = {(s.digest_id, s.source_id): s for s in scores}
    alignment_map = {(a.digest_id, a.source_id): a for a in alignments}

    # 1. digest_relationships.json
    relationships = []
    for s in scores:
        rel = {
            'digest_id': s.digest_id,
            'source_id': s.source_id,
            'classification': s.classification,
            'confidence': s.confidence,
            'coverage': round(s.coverage, 4),
            'novel_fraction': round(s.novel_fraction, 4),
            'avg_segment_length': round(s.avg_segment_length, 2),
            'longest_segment': s.longest_segment,
            'num_source_regions': s.num_source_regions,
            'source_span': round(s.source_span, 6),
            'has_docnumber_xref': s.has_docnumber_xref,
        }
        if s.phonetic_coverage > 0:
            rel['phonetic_coverage'] = round(s.phonetic_coverage, 4)
        relationships.append(rel)

    _write_json(results_dir / "digest_relationships.json", relationships)

    # 2. Per-pair alignment JSON files
    for alignment in alignments:
        key = (alignment.digest_id, alignment.source_id)
        score = score_map.get(key)
        if score and score.classification != "no_relationship":
            fname = f"{alignment.digest_id}_{alignment.source_id}.json"
            data = {
                'digest_id': alignment.digest_id,
                'source_id': alignment.source_id,
                'coverage': round(alignment.coverage, 4),
                'novel_fraction': round(alignment.novel_fraction, 4),
                'source_span': round(alignment.source_span, 6),
                'num_source_regions': alignment.num_source_regions,
                'segments': [
                    _segment_to_dict(seg)
                    for seg in alignment.segments
                ],
            }
            _write_json(alignments_dir / fname, data)

    # 3. summary.md
    _generate_summary(scores, alignments, multi_source, metadata_map, results_dir)

    # 4. validation.md
    _generate_validation_report(validation, results_dir)

    logger.info("Reports written to %s", results_dir)


def _generate_summary(
    scores: list[DigestScore],
    alignments: list[AlignmentResult],
    multi_source: list[MultiSourceDigest],
    metadata_map: dict[str, TextMetadata],
    results_dir: Path,
):
    """Generate human-readable summary.md."""
    score_map = {(s.digest_id, s.source_id): s for s in scores}
    alignment_map = {(a.digest_id, a.source_id): a for a in alignments}

    lines = []
    lines.append("# Taisho Canon Digest Detection Results\n")

    # Summary statistics
    by_class = defaultdict(list)
    for s in scores:
        by_class[s.classification].append(s)

    lines.append("## Summary Statistics\n")
    lines.append(f"- Total relationships detected: {len(scores)}")
    for cls in ['excerpt', 'digest', 'commentary',
                'shared_tradition', 'retranslation']:
        count = len(by_class.get(cls, []))
        if count > 0:
            lines.append(f"- {cls}: {count}")
    lines.append(f"- Multi-source digests: {len(multi_source)}")
    lines.append("")

    # Top results ranked by confidence
    lines.append("## Top Digest Relationships (by confidence)\n")
    lines.append("| Rank | Digest | Source | Classification | Confidence | Coverage |")
    lines.append("|------|--------|--------|----------------|------------|----------|")

    for i, s in enumerate(scores[:50], 1):
        d_meta = metadata_map.get(s.digest_id)
        d_title = d_meta.title if d_meta else ''
        lines.append(
            f"| {i} | {s.digest_id} ({d_title}) | {s.source_id} | "
            f"{s.classification} | {s.confidence:.3f} | {s.coverage:.1%} |"
        )
    lines.append("")

    # Cluster analysis: multiple digests of the same source
    lines.append("## Cluster Analysis: Source Texts with Multiple Digests\n")
    by_source = defaultdict(list)
    for s in scores:
        if s.classification in ('excerpt', 'digest'):
            by_source[s.source_id].append(s)

    for source_id in sorted(by_source, key=lambda x: len(by_source[x]), reverse=True):
        digests = by_source[source_id]
        if len(digests) < 2:
            continue
        s_meta = metadata_map.get(source_id)
        s_title = s_meta.title if s_meta else ''
        lines.append(f"### {source_id} ({s_title})\n")
        for s in sorted(digests, key=lambda x: x.confidence, reverse=True):
            d_meta = metadata_map.get(s.digest_id)
            d_title = d_meta.title if d_meta else ''
            lines.append(
                f"- {s.digest_id} ({d_title}): {s.classification}, "
                f"coverage={s.coverage:.1%}, confidence={s.confidence:.3f}"
            )
        lines.append("")

    # Multi-source digests
    if multi_source:
        lines.append("## Multi-Source Digests\n")
        for ms in multi_source:
            d_meta = metadata_map.get(ms.digest_id)
            d_title = d_meta.title if d_meta else ''
            lines.append(f"### {ms.digest_id} ({d_title})")
            lines.append(f"Combined coverage: {ms.combined_coverage:.1%}\n")
            for src in ms.sources:
                lines.append(f"- {src.source_id}: coverage={src.coverage:.1%}")
            lines.append("")

    # Alignment visualizations for top results
    lines.append("## Alignment Visualizations (Top 20)\n")
    for s in scores[:20]:
        key = (s.digest_id, s.source_id)
        alignment = alignment_map.get(key)
        if alignment:
            lines.append("```")
            lines.append(_format_alignment_visualization(
                alignment, s, metadata_map))
            lines.append("```\n")

    with open(results_dir / "summary.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _generate_validation_report(validation: dict, results_dir: Path):
    """Generate validation.md comparing against ground truth."""
    lines = []
    lines.append("# Validation Report: Ground Truth Comparison\n")
    lines.append(f"**Passed:** {validation['passed']} | "
                 f"**Failed:** {validation['failed']}\n")

    for test in validation['tests']:
        status = "PASS" if all(c['passed'] for c in test['checks']) else "FAIL"
        lines.append(f"## [{status}] {test['digest_id']} → {test['source_id']}\n")
        lines.append(f"_{test['description']}_\n")

        for check in test['checks']:
            icon = "PASS" if check['passed'] else "FAIL"
            detail = check.get('detail', '')
            expected = check.get('expected', '')
            actual = check.get('actual', '')
            if expected:
                lines.append(f"- [{icon}] {check['check']}: expected={expected}, actual={actual}")
            elif detail:
                lines.append(f"- [{icon}] {check['check']}: {detail}")
            else:
                lines.append(f"- [{icon}] {check['check']}: actual={actual}")

        if 'score' in test:
            lines.append(f"\nDetailed scores:")
            for k, v in test['score'].items():
                lines.append(f"  - {k}: {v}")
        lines.append("")

    with open(results_dir / "validation.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
