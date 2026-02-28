"""Shared utilities for cross-reference concordance export modules.

Contains functions used by both export_csv.py and export_tei.py:
path constants, JSON loading, ID resolution, provenance reconstruction,
metadata gathering, and error pair loading.
"""

import json
import logging
import re
from collections import defaultdict
from pathlib import Path

from . import config

BASE_DIR = config.BASE_DIR
RESULTS_DIR = config.RESULTS_DIR

logger = logging.getLogger(__name__)

# Input: expanded concordance
EXPANDED_PATH = RESULTS_DIR / "cross_reference_expanded.json"
KNOWN_ERRORS_PATH = BASE_DIR / "data" / "known_errors.json"

# Source files for provenance reconstruction
LANCASTER_PATH = BASE_DIR / "lancaster_taisho_crossref.json"
LANCASTER_FULL_PATH = RESULTS_DIR / "lancaster_full.json"
ACMULLER_PATH = RESULTS_DIR / "tohoku_taisho_crossref.json"
CBETA_SANSKRIT_PATH = RESULTS_DIR / "cbeta_jinglu_sanskrit.json"
CBETA_TIBETAN_PATH = RESULTS_DIR / "cbeta_jinglu_tibetan.json"
RKTS_PATH = RESULTS_DIR / "rkts_taisho.json"
EXISTING_XREF_PATH = RESULTS_DIR / "cross_reference.json"


def load_json(path):
    """Load a JSON file if it exists."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def build_number_to_id(concordance_keys):
    """Build a map from bare Taisho number to canonical ID (e.g., 251 -> T08n0251)."""
    num_to_id = {}
    for text_id in concordance_keys:
        m = re.match(r'^T(\d{2})n(\d{4})', text_id)
        if m:
            num = int(m.group(2))
            if num not in num_to_id:
                num_to_id[num] = text_id
    return num_to_id


def resolve_taisho(raw, num_to_id, valid_ids):
    """Resolve a raw Taisho reference (e.g. 'T251', 'T08n0251') to a canonical ID."""
    # Already canonical
    if raw in valid_ids:
        return raw
    # Bare number format: T250, T0250
    m = re.match(r'^T(\d+)$', raw)
    if m:
        return num_to_id.get(int(m.group(1)))
    # Try as-is with suffix stripping
    base = re.sub(r'[A-Za-z]+$', '', raw)
    if base in valid_ids:
        return base
    return None


def _collect_all_ids(expanded):
    """Collect all Taisho IDs from the expanded concordance."""
    all_ids = set()
    for section in ("tibetan_parallels", "pali_parallels", "sanskrit_parallels"):
        all_ids.update(expanded.get(section, {}).keys())
    all_ids.update(expanded.get("no_parallel_found", []))
    return all_ids


def build_provenance(expanded):
    """Build per-mapping provenance: (taisho_id, ref_str) -> set of sources.

    Uses link_provenance from the expanded JSON for both Toh and Otani links.
    Falls back to re-scanning source files for Toh provenance when
    link_provenance is absent (backward compatibility).
    """
    provenance = defaultdict(set)

    # Use link_provenance from expanded JSON (covers both Toh and Otani)
    link_prov = expanded.get("link_provenance", {})
    if link_prov:
        for taisho_id, refs in link_prov.items():
            for ref_id, attestations in refs.items():
                for att in attestations:
                    source = att.get("source", "")
                    # Skip error-flagged attestations
                    if att.get("flagged_error"):
                        continue
                    provenance[(taisho_id, ref_id)].add(source)
        return provenance

    # Fallback: reconstruct from source files (no link_provenance available).
    # WARNING: This path only covers 7 of 11+ sources (missing MITRA,
    # Sanskrit title matches, scholarly citations, 84000 TEI refs, Otani).
    logger.warning("No link_provenance in expanded JSON; using fallback "
                   "provenance reconstruction (incomplete source coverage).")
    all_ids = _collect_all_ids(expanded)
    num_to_id = build_number_to_id(all_ids)

    # --- Source: existing cross_reference.json ---
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for text_id, parallels in xref.get("tibetan_parallels", {}).items():
            for p in parallels:
                if p.startswith("Toh "):
                    provenance[(text_id, p)].add("existing")

    # --- Source: Lancaster (original) ---
    lancaster = load_json(LANCASTER_PATH)
    if lancaster:
        for _k, entry in lancaster.items():
            t_num_str = re.sub(r'[a-zA-Z]+$', '', str(entry.get("taisho", "")))
            try:
                t_num = int(t_num_str)
            except ValueError:
                continue
            text_id = num_to_id.get(t_num)
            if not text_id:
                continue
            for toh in entry.get("tohoku") or []:
                provenance[(text_id, f"Toh {toh}")].add("lancaster")

    # --- Source: Lancaster full ---
    lancaster_full = load_json(LANCASTER_FULL_PATH)
    if lancaster_full:
        for _k, entry in lancaster_full.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                for toh in entry.get("tohoku", []):
                    toh_str = toh if toh.startswith("Toh ") else f"Toh {toh}"
                    provenance[(text_id, toh_str)].add("lancaster_full")

    # --- Source: acmuller Tohoku ---
    acmuller = load_json(ACMULLER_PATH)
    if acmuller:
        for _k, entry in acmuller.get("entries", {}).items():
            toh_num = entry.get("tohoku")
            if toh_num is None:
                continue
            toh_str = f"Toh {toh_num}"
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                provenance[(text_id, toh_str)].add("acmuller")

    # --- Source: CBETA Sanskrit ---
    cbeta_skt = load_json(CBETA_SANSKRIT_PATH)
    if cbeta_skt:
        for _k, entry in cbeta_skt.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                for toh in entry.get("tohoku", []):
                    toh_str = toh if toh.startswith("Toh ") else f"Toh {toh}"
                    provenance[(text_id, toh_str)].add("cbeta_sanskrit")

    # --- Source: CBETA Tibetan ---
    cbeta_tib = load_json(CBETA_TIBETAN_PATH)
    if cbeta_tib:
        for _k, entry in cbeta_tib.get("entries", {}).items():
            entry_num = entry.get("entry_number")
            if entry_num is None:
                continue
            toh_str = f"Toh {entry_num}"
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                provenance[(text_id, toh_str)].add("cbeta_tibetan")

    # --- Source: rKTs ---
    rkts = load_json(RKTS_PATH)
    if rkts:
        for _k, entry in rkts.get("entries", {}).items():
            toh_num = entry.get("tohoku")
            if toh_num is None:
                continue
            toh_str = f"Toh {toh_num}"
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                provenance[(text_id, toh_str)].add("rkts")

    return provenance


def gather_metadata(expanded):
    """Gather Chinese, Sanskrit, Tibetan titles, Nanjio, and Otani data from source files.

    Returns:
        titles: dict[taisho_id] -> {chinese_title, sanskrit_title, tibetan_title}
        nanjio: dict[taisho_id] -> set of Nanjio numbers
        otani_map: dict[taisho_id] -> set of Otani numbers
    """
    all_ids = _collect_all_ids(expanded)
    num_to_id = build_number_to_id(all_ids)

    titles = defaultdict(lambda: {
        "chinese_title": "",
        "sanskrit_title": "",
        "tibetan_title": "",
    })
    nanjio = defaultdict(set)
    otani_map = defaultdict(set)

    # Lancaster (original) - has Chinese, Sanskrit, Tibetan titles and Nanjio
    lancaster = load_json(LANCASTER_PATH)
    if lancaster:
        for _k, entry in lancaster.items():
            t_num_str = re.sub(r'[a-zA-Z]+$', '', str(entry.get("taisho", "")))
            try:
                t_num = int(t_num_str)
            except ValueError:
                continue
            text_id = num_to_id.get(t_num)
            if not text_id:
                continue
            if entry.get("chinese_title"):
                titles[text_id]["chinese_title"] = entry["chinese_title"]
            if entry.get("sanskrit_title"):
                titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]
            if entry.get("tibetan_title"):
                titles[text_id]["tibetan_title"] = entry["tibetan_title"]
            if entry.get("nanjio"):
                nanjio[text_id].add(f"Nj {entry['nanjio']}")
            for ot in entry.get("otani") or []:
                otani_map[text_id].add(f"Otani {ot}")

    # Lancaster full - additional titles and Nanjio
    lancaster_full = load_json(LANCASTER_FULL_PATH)
    if lancaster_full:
        for _k, entry in lancaster_full.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                if entry.get("chinese_title") and not titles[text_id]["chinese_title"]:
                    titles[text_id]["chinese_title"] = entry["chinese_title"]
                if entry.get("sanskrit_title") and not titles[text_id]["sanskrit_title"]:
                    titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]
                if entry.get("tibetan_title") and not titles[text_id]["tibetan_title"]:
                    titles[text_id]["tibetan_title"] = entry["tibetan_title"]
                for nj in entry.get("nanjio", []):
                    nanjio[text_id].add(nj)
                for ot in entry.get("otani", []):
                    otani_map[text_id].add(ot)

    # acmuller - Nanjio, Otani
    acmuller = load_json(ACMULLER_PATH)
    if acmuller:
        for _k, entry in acmuller.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                for nj in entry.get("nanjio", []):
                    nanjio[text_id].add(nj)
                for ot in entry.get("otani", []):
                    otani_map[text_id].add(ot)

    # CBETA Tibetan - has Chinese, Tibetan, Sanskrit titles and Nanjio
    cbeta_tib = load_json(CBETA_TIBETAN_PATH)
    if cbeta_tib:
        for _k, entry in cbeta_tib.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                if entry.get("chinese_title") and not titles[text_id]["chinese_title"]:
                    titles[text_id]["chinese_title"] = entry["chinese_title"]
                if entry.get("sanskrit_title") and not titles[text_id]["sanskrit_title"]:
                    titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]
                if entry.get("tibetan_title") and not titles[text_id]["tibetan_title"]:
                    titles[text_id]["tibetan_title"] = entry["tibetan_title"]
                if entry.get("nanjio"):
                    nanjio[text_id].add(entry["nanjio"])

    # rKTs - Sanskrit titles
    rkts = load_json(RKTS_PATH)
    if rkts:
        for _k, entry in rkts.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho(t_raw, num_to_id, all_ids)
                if not text_id:
                    continue
                if entry.get("sanskrit_title") and not titles[text_id]["sanskrit_title"]:
                    titles[text_id]["sanskrit_title"] = entry["sanskrit_title"]

    return titles, nanjio, otani_map


def load_known_error_pairs():
    """Load known catalog errors and return a set of (taisho_id, toh) pairs to exclude."""
    errors_data = load_json(KNOWN_ERRORS_PATH)
    if not errors_data:
        return set()
    return {
        (err["taisho_id"], err["erroneous_toh"])
        for err in errors_data.get("errors", [])
    }
