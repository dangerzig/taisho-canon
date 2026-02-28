"""Pipeline orchestrator: runs all 5 stages end-to-end."""

import gc
import json
import logging
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .extract import extract_all, save_results
from .fingerprint import (
    compute_document_frequencies,
    identify_stopgrams,
    build_ngram_sets,
)
from .cache import PipelineCache, CacheCorruptionError
from .candidates import generate_candidates
from .align import align_candidates
from .score import score_all, detect_multi_source_digests
from .report import validate_ground_truth, generate_reports

logger = logging.getLogger(__name__)

TIMING_LOG = config.DATA_DIR / "timing_log.jsonl"


def _log_peak_rss(stage_name: str) -> int:
    """Log and return peak RSS in MB.

    On macOS, ru_maxrss is in bytes; on Linux it's in KB.
    """
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == 'darwin':
        rss_mb = rss / (1024 * 1024)
    else:
        rss_mb = rss / 1024
    logger.info("Peak RSS after %s: %.0f MB", stage_name, rss_mb)
    return int(rss_mb)


def _git_short_hash() -> str:
    """Return the current git short commit hash, or '' if unavailable."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=config.BASE_DIR, stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return ""


def _save_timing(stage_times: dict, counts: dict, total_time: float,
                 used_cache: bool, num_workers: int = 0) -> None:
    """Append one JSON record to the timing log."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_short_hash(),
        "used_cache": used_cache,
        "num_workers": num_workers,
        "stages": stage_times,
        "counts": counts,
        "total_seconds": round(total_time, 1),
    }
    TIMING_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(TIMING_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("Timing record appended to %s", TIMING_LOG)


def run_pipeline(
    xml_dir: Path = None,
    results_dir: Path = None,
    num_workers: int = None,
    save_extracted: bool = True,
    no_cache: bool = False,
) -> dict:
    """Run the full 5-stage digest detection pipeline.

    Args:
        xml_dir: Path to XML corpus directory.
        results_dir: Path to output directory.
        num_workers: Number of parallel workers (None = min(cpu_count, 4)).
        save_extracted: Whether to save extracted texts to disk.
        no_cache: Force recomputation, ignoring any cached results.

    Returns dict with all pipeline results.
    """
    if xml_dir is None:
        xml_dir = config.XML_DIR
    if results_dir is None:
        results_dir = config.RESULTS_DIR
    num_workers = config.resolve_worker_count(num_workers)

    total_start = time.time()
    stage_times = {}
    counts = {}

    # Check cache for Stages 1-2b
    cache = PipelineCache(config.CACHE_DIR)
    used_cache = not no_cache and cache.is_valid(xml_dir)
    if used_cache:
        logger.info("=" * 60)
        logger.info("LOADING FROM CACHE")
        logger.info("=" * 60)
        t0 = time.time()
        try:
            texts, candidates = cache.load()
        except CacheCorruptionError as e:
            logger.warning("Cache corrupted, falling back to recomputation: %s", e)
            used_cache = False
        else:
            text_map = {t.text_id: t for t in texts}
            metadata_map = {t.text_id: t.metadata for t in texts}
            elapsed = round(time.time() - t0, 1)
            stage_times["cache_load"] = elapsed
            counts["texts"] = len(texts)
            counts["candidates"] = len(candidates)
            logger.info("Loaded %d texts, %d candidates from cache in %.1f seconds",
                         len(texts), len(candidates), elapsed)
    if not used_cache:
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

        elapsed = round(time.time() - t0, 1)
        stage_times["stage1_extract"] = elapsed
        counts["texts"] = len(texts)
        logger.info("Stage 1 complete: %d texts in %.1f seconds",
                     len(texts), elapsed)
        _log_peak_rss("Stage 1")

        # ---- Stage 2: Candidate Generation ----
        logger.info("=" * 60)
        logger.info("STAGE 2: Candidate Generation")
        logger.info("=" * 60)
        t0 = time.time()

        doc_freq = compute_document_frequencies(texts, num_workers=num_workers)
        stopgrams = identify_stopgrams(doc_freq, len(texts))
        counts["stopgrams"] = len(stopgrams)
        del doc_freq  # millions of n-gram→count entries, only needed for stopgrams
        ngram_sets = build_ngram_sets(texts, stopgrams, num_workers=num_workers)
        candidates = generate_candidates(texts, ngram_sets, stopgrams,
                                         num_workers=num_workers)
        counts["char_candidates"] = len(candidates)
        del ngram_sets, stopgrams  # ~8,982 frozensets, only needed for candidates
        gc.collect()

        elapsed = round(time.time() - t0, 1)
        stage_times["stage2_candidates"] = elapsed
        counts["stage2_candidates"] = len(candidates)
        logger.info("Stage 2 complete: %d candidates in %.1f seconds",
                     len(candidates), elapsed)
        _log_peak_rss("Stage 2")

        # ---- Stage 2b: Phonetic Candidate Generation ----
        if config.ENABLE_PHONETIC_SCAN:
            logger.info("=" * 60)
            logger.info("STAGE 2b: Phonetic Candidate Generation")
            logger.info("=" * 60)
            t0 = time.time()

            from .phonetic import build_equivalence_table
            from .candidates import generate_phonetic_candidates

            phonetic_table = build_equivalence_table()
            phonetic_candidates = generate_phonetic_candidates(
                texts, phonetic_table, num_workers=num_workers,
            )

            # Merge, deduplicating against existing candidates
            existing_pairs = {(c.digest_id, c.source_id) for c in candidates}
            new_phonetic = [c for c in phonetic_candidates
                            if (c.digest_id, c.source_id) not in existing_pairs]
            candidates.extend(new_phonetic)
            candidates.sort(key=lambda c: c.containment_score, reverse=True)

            elapsed = round(time.time() - t0, 1)
            stage_times["stage2b_phonetic"] = elapsed
            counts["phonetic_new"] = len(new_phonetic)
            counts["candidates"] = len(candidates)
            logger.info("Stage 2b complete: %d new phonetic candidates "
                         "(total now %d) in %.1f seconds",
                         len(new_phonetic), len(candidates), elapsed)
            del phonetic_table  # only needed for Stage 2b
            _log_peak_rss("Stage 2b")
        else:
            counts["candidates"] = len(candidates)

        # Save to cache
        cache.save(texts, candidates, xml_dir)

    # ---- Stage 3: Detailed Alignment ----
    logger.info("=" * 60)
    logger.info("STAGE 3: Detailed Alignment")
    logger.info("=" * 60)
    t0 = time.time()

    # Alignment is memory-light, so allow more workers than fingerprinting
    align_workers = config.resolve_worker_count(
        config.ALIGN_NUM_WORKERS, memory_intensive=False)
    alignments = align_candidates(candidates, text_map,
                                   num_workers=align_workers)

    elapsed = round(time.time() - t0, 1)
    stage_times["stage3_align"] = elapsed
    counts["alignments"] = len(alignments)
    logger.info("Stage 3 complete: %d alignments in %.1f seconds",
                len(alignments), elapsed)
    _log_peak_rss("Stage 3")

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

    elapsed = round(time.time() - t0, 1)
    stage_times["stage4_score"] = elapsed
    counts["scores"] = len(scores)
    logger.info("Stage 4 complete: %d scored relationships in %.1f seconds",
                len(scores), elapsed)
    _log_peak_rss("Stage 4")

    # ---- Stage 5: Validate & Report ----
    logger.info("=" * 60)
    logger.info("STAGE 5: Validation and Reporting")
    logger.info("=" * 60)
    t0 = time.time()

    validation = validate_ground_truth(scores, alignments, metadata_map)
    pipeline_stats = {
        'num_texts': counts.get('texts', 0),
        'num_stopgrams': counts.get('stopgrams', 0),
        'num_candidates': counts.get('char_candidates', 0),
        'num_phonetic_candidates': counts.get('phonetic_new', 0),
        'total_candidates': counts.get('candidates', 0),
    }
    generate_reports(
        scores, alignments, multi_source, metadata_map, validation,
        results_dir=results_dir,
        pipeline_stats=pipeline_stats,
    )

    elapsed = round(time.time() - t0, 1)
    stage_times["stage5_report"] = elapsed
    logger.info("Stage 5 complete in %.1f seconds", elapsed)
    _log_peak_rss("Stage 5")

    total_time = time.time() - total_start
    counts["validation_passed"] = validation['passed']
    counts["validation_failed"] = validation['failed']

    _save_timing(stage_times, counts, total_time, used_cache, num_workers)

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


def _print_timing_history() -> None:
    """Print a table of past pipeline runs from the timing log."""
    if not TIMING_LOG.exists():
        print("No timing records found.")
        return

    records = []
    with open(TIMING_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        print("No timing records found.")
        return

    # Column definitions: (header, key function)
    stage_keys = [
        ("Stage 1", "stage1_extract"),
        ("Stage 2", "stage2_candidates"),
        ("Stage 2b", "stage2b_phonetic"),
        ("Stage 3", "stage3_align"),
        ("Stage 4", "stage4_score"),
        ("Stage 5", "stage5_report"),
    ]

    # Header
    print(f"{'Date':>19s}  {'Commit':>7s}  {'Cache':>5s}  ", end="")
    for header, _ in stage_keys:
        print(f"{header:>9s}  ", end="")
    print(f"{'Total':>8s}  {'Pairs':>7s}  {'Texts':>5s}")
    print("-" * 110)

    for r in records:
        ts = r["timestamp"][:19].replace("T", " ")
        commit = r.get("git_commit", "")[:7]
        cached = "yes" if r.get("used_cache") else "no"
        stages = r.get("stages", {})
        counts = r.get("counts", {})

        print(f"{ts:>19s}  {commit:>7s}  {cached:>5s}  ", end="")
        for _, key in stage_keys:
            val = stages.get(key)
            if val is not None:
                print(f"{val:>8.1f}s  ", end="")
            else:
                print(f"{'---':>9s}  ", end="")
        total = r.get("total_seconds", 0)
        mins = total / 60
        print(f"{mins:>7.1f}m  ", end="")
        print(f"{counts.get('candidates', ''):>7}  ", end="")
        print(f"{counts.get('texts', ''):>5}")


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
        help='Number of parallel workers (default: min(cpu_count, 4))'
    )
    parser.add_argument(
        '--no-save', action='store_true',
        help='Skip saving extracted texts to disk'
    )
    parser.add_argument(
        '--no-cache', action='store_true',
        help='Force recomputation, ignoring any cached results'
    )
    parser.add_argument(
        '--log-level', default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
    )
    parser.add_argument(
        '--show-timing', action='store_true',
        help='Print past timing records and exit'
    )
    args = parser.parse_args()

    if args.show_timing:
        _print_timing_history()
        return

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
        no_cache=args.no_cache,
    )


if __name__ == '__main__':
    main()
