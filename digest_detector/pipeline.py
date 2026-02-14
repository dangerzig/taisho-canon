"""Pipeline orchestrator: runs all 5 stages end-to-end."""

import logging
import time
from pathlib import Path

from . import config
from .extract import extract_all, save_results
from .fingerprint import (
    compute_document_frequencies,
    identify_stopgrams,
    build_inverted_index,
)
from .candidates import generate_candidates
from .align import align_candidates
from .score import score_all, detect_multi_source_digests
from .report import validate_ground_truth, generate_reports

logger = logging.getLogger(__name__)


def run_pipeline(
    xml_dir: Path = None,
    results_dir: Path = None,
    num_workers: int = None,
    save_extracted: bool = True,
) -> dict:
    """Run the full 5-stage digest detection pipeline.

    Args:
        xml_dir: Path to XML corpus directory.
        results_dir: Path to output directory.
        num_workers: Number of parallel workers (None = cpu_count).
        save_extracted: Whether to save extracted texts to disk.

    Returns dict with all pipeline results.
    """
    if xml_dir is None:
        xml_dir = config.XML_DIR
    if results_dir is None:
        results_dir = config.RESULTS_DIR

    total_start = time.time()

    # ---- Stage 1: Extract ----
    logger.info("=" * 60)
    logger.info("STAGE 1: Text Extraction")
    logger.info("=" * 60)
    t0 = time.time()

    texts = extract_all(xml_dir=xml_dir, num_workers=num_workers)
    text_map = {t.text_id: t for t in texts}
    metadata_map = {t.text_id: t.metadata for t in texts}

    if save_extracted:
        save_results(texts)

    logger.info("Stage 1 complete: %d texts in %.1f seconds",
                len(texts), time.time() - t0)

    # ---- Stage 2: Candidate Generation ----
    logger.info("=" * 60)
    logger.info("STAGE 2: Candidate Generation")
    logger.info("=" * 60)
    t0 = time.time()

    doc_freq = compute_document_frequencies(texts)
    stopgrams = identify_stopgrams(doc_freq, len(texts))
    inverted_index = build_inverted_index(texts, stopgrams)
    candidates = generate_candidates(texts, inverted_index, stopgrams)

    logger.info("Stage 2 complete: %d candidates in %.1f seconds",
                len(candidates), time.time() - t0)

    # ---- Stage 3: Detailed Alignment ----
    logger.info("=" * 60)
    logger.info("STAGE 3: Detailed Alignment")
    logger.info("=" * 60)
    t0 = time.time()

    alignments = align_candidates(candidates, text_map, num_workers=num_workers)

    logger.info("Stage 3 complete: %d alignments in %.1f seconds",
                len(alignments), time.time() - t0)

    # ---- Stage 4: Score & Classify ----
    logger.info("=" * 60)
    logger.info("STAGE 4: Scoring and Classification")
    logger.info("=" * 60)
    t0 = time.time()

    docnum_pair_set = {
        (c.digest_id, c.source_id) for c in candidates if c.from_docnumber
    }
    scores = score_all(alignments, metadata_map, docnum_pair_set, text_map=text_map)
    multi_source = detect_multi_source_digests(scores, alignments, metadata_map)

    logger.info("Stage 4 complete: %d scored relationships in %.1f seconds",
                len(scores), time.time() - t0)

    # ---- Stage 5: Validate & Report ----
    logger.info("=" * 60)
    logger.info("STAGE 5: Validation and Reporting")
    logger.info("=" * 60)
    t0 = time.time()

    validation = validate_ground_truth(scores, alignments, metadata_map)
    generate_reports(
        scores, alignments, multi_source, metadata_map, validation,
        results_dir=results_dir,
    )

    logger.info("Stage 5 complete in %.1f seconds", time.time() - t0)

    total_time = time.time() - total_start
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE in %.1f seconds (%.1f min)",
                total_time, total_time / 60)
    logger.info("Results written to %s", results_dir)
    logger.info("Validation: %d passed, %d failed",
                validation['passed'], validation['failed'])
    logger.info("=" * 60)

    return {
        'texts': texts,
        'candidates': candidates,
        'alignments': alignments,
        'scores': scores,
        'multi_source': multi_source,
        'validation': validation,
        'total_time': total_time,
    }


def main():
    """Entry point for running the pipeline from command line."""
    import argparse  # lazy: only needed when invoked as CLI

    parser = argparse.ArgumentParser(
        description='Taisho Canon Digest Detection Pipeline'
    )
    parser.add_argument(
        '--xml-dir', type=Path, default=config.XML_DIR,
        help='Path to XML corpus directory'
    )
    parser.add_argument(
        '--results-dir', type=Path, default=config.RESULTS_DIR,
        help='Path to output directory'
    )
    parser.add_argument(
        '--workers', type=int, default=None,
        help='Number of parallel workers (default: cpu_count)'
    )
    parser.add_argument(
        '--no-save', action='store_true',
        help='Skip saving extracted texts to disk'
    )
    parser.add_argument(
        '--log-level', default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )

    run_pipeline(
        xml_dir=args.xml_dir,
        results_dir=args.results_dir,
        num_workers=args.workers,
        save_extracted=not args.no_save,
    )


if __name__ == '__main__':
    main()
