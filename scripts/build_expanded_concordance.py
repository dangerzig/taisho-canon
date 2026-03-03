#!/usr/bin/env python3
"""Build an expanded cross-canon concordance by merging ALL data sources.

This script merges 12 sources, Sanskrit title matches, scholarly citation
files, and the rKTs Tohoku-to-Otani concordance into a unified concordance
with per-link provenance tracking for Tibetan (Tohoku/Otani) and Pali parallels.

Each link carries its own provenance: which source(s) attest it, with
optional confidence scores and notes.

Inputs:
  - lancaster_taisho_crossref.json (existing Lancaster data, 790 entries)
  - results/lancaster_full.json (full Lancaster K-number scrape, ~1521 entries)
  - results/84000_tohoku_extract.json (84000 TEI Tohoku extraction)
  - results/tohoku_taisho_crossref.json (acmuller Tohoku->K->Taisho scrape)
  - results/cbeta_jinglu_sanskrit.json (CBETA Jinglu Sanskrit/Pali scrape)
  - results/cbeta_jinglu_tibetan.json (CBETA Jinglu Tibetan catalogue, ~4569)
  - results/rkts_taisho.json (rKTs kernel Taisho cross-refs)
  - results/cross_reference.json (existing concordance, for comparison)
  - results/sanskrit_title_matches.json (Sanskrit title matching results)
  - data/scholarly_citations/*.json (scholarly citation files, e.g. silk2019.json)
  - results/mitra_taisho_tohoku.json (MITRA Chinese-Tibetan sentence alignments)
  - results/sc_pali_parallels.json (SuttaCentral Pali-Taisho parallels)

Output:
  - results/cross_reference_expanded.json (new expanded concordance)
  - Prints delta statistics vs. existing concordance

Output schema:
  {
    "schema_version": 3,
    "summary": { ..., "classification": { counts per type } },
    "sources": { ... },
    "tibetan_parallels": { "T08n0251": ["Otani 993", "Toh 21", ...] },
    "pali_parallels": { ... },
    "sanskrit_parallels": { ... },
    "no_parallel_found": [ ... ],
    "link_provenance": { ... },
    "link_classifications": {
      "T08n0251": {
        "Toh 21": {"type": "parallel", "basis": "catalog-attested"},
        "Otani 993": {"type": "parallel", "basis": "inherited from Toh 21"}
      }
    }
  }

Classification types:
  - parallel: Catalog-attested cross-canon parallel
  - parallel:computational: Computationally discovered, likely genuine
  - chinese_to_tibetan: Chinese text translated into Tibetan (rKTs-flagged)
  - indirect:quotation: Encyclopedic text quoting Indian sources
  - indirect:inherited: Parallel inherited via digest/excerpt chain
  - uncertain: Insufficient evidence to classify
  - error:flagged: Known catalog error (all attestations flagged)
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

# Input files
LANCASTER_PATH = BASE_DIR / "lancaster_taisho_crossref.json"
LANCASTER_FULL_PATH = RESULTS_DIR / "lancaster_full.json"
TOHOKU_84000_PATH = RESULTS_DIR / "84000_tohoku_extract.json"
TOHOKU_ACMULLER_PATH = RESULTS_DIR / "tohoku_taisho_crossref.json"
CBETA_SANSKRIT_PATH = RESULTS_DIR / "cbeta_jinglu_sanskrit.json"
CBETA_TIBETAN_PATH = RESULTS_DIR / "cbeta_jinglu_tibetan.json"
RKTS_PATH = RESULTS_DIR / "rkts_taisho.json"
EXISTING_XREF_PATH = RESULTS_DIR / "cross_reference.json"
SANSKRIT_MATCHES_PATH = RESULTS_DIR / "sanskrit_title_matches.json"
TAISHO_84000_REFS_PATH = RESULTS_DIR / "84000_taisho_refs.json"
SCHOLARLY_DIR = BASE_DIR / "data" / "scholarly_citations"
OTANI_CONCORDANCE_PATH = RESULTS_DIR / "tohoku_otani_concordance.json"
MITRA_PATH = RESULTS_DIR / "mitra_taisho_tohoku.json"
SC_PALI_PATH = RESULTS_DIR / "sc_pali_parallels.json"
KNOWN_ERRORS_PATH = BASE_DIR / "data" / "known_errors.json"

# Output
OUTPUT_PATH = RESULTS_DIR / "cross_reference_expanded.json"
VERIFIED_OUTPUT_PATH = RESULTS_DIR / "cross_reference_verified.json"

# All valid Taisho text IDs from our corpus
CORPUS_IDS_PATH = RESULTS_DIR / "digest_relationships.json"

# Current schema version for the output format
SCHEMA_VERSION = 3

# MITRA: only add links with confidence >= this threshold to the active
# tibetan_parallels set. Lower-confidence links are provenance-only.
MITRA_STRONG_THRESHOLD = 0.9

# --- Link classification constants ---

# Catalog sources: trusted, can independently establish "parallel".
CATALOG_SOURCES = {
    "lancaster", "lancaster_full", "acmuller_tohoku", "cbeta_tibetan",
    "cbeta_sanskrit", "84000_tei_refs", "rkts", "existing",
    # Scholarly citations are catalog-grade assertions
    "silk2019", "li2021",
    # Peking-only entries derived from Lancaster
    "peking_only",
    # SuttaCentral (currently Pali-only, but a curated scholarly source)
    "suttacentral_parallels",
}

# Computational sources: cannot independently establish "parallel".
# Add new computational methods here as they are integrated
# (e.g., "llm_matching", "embedding_similarity", etc.).
COMPUTATIONAL_SOURCES = {"mitra", "sanskrit_title_match"}

# A text with this many or more computational-only Toh links is considered
# encyclopedic (likely quotation rather than genuine parallel).
ENCYCLOPEDIC_THRESHOLD = 5

# Minimum computational confidence to classify as parallel:computational
# (rather than uncertain).
COMPUTATIONAL_CONFIDENCE_THRESHOLD = 0.9


def load_json(path):
    """Load a JSON file if it exists, else return None."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    print(f"  WARNING: {path} not found, skipping.")
    return None


def normalize_taisho_id(raw_id):
    """Normalize various Taisho ID formats to T##n#### format.

    Handles: T250, T0250, T1, T08n0250, etc.
    Returns the canonical CBETA format string (e.g., T08n0250) if already
    in that format, or int (bare number) for lookup via resolve_taisho_id.
    """
    # Already in T##n#### format
    m = re.match(r'^T(\d{2})n(\d{4}[A-Za-z]?)$', raw_id)
    if m:
        return raw_id

    # Bare number: T250, T0250, T1
    m = re.match(r'^T(\d+)$', raw_id)
    if m:
        return int(m.group(1))  # Return as int for lookup

    return raw_id


def build_taisho_number_to_id_map(corpus_ids):
    """Build a map from bare Taisho number (e.g. 250) to full ID (e.g. T08n0250).

    This handles the mismatch between Lancaster (bare T250) and CBETA (T08n0250).
    """
    num_to_id = {}
    for text_id in corpus_ids:
        m = re.match(r'^T(\d{2})n(\d{4})', text_id)
        if m:
            num = int(m.group(2))
            # Store first occurrence (some numbers may have vol variants)
            if num not in num_to_id:
                num_to_id[num] = text_id
            # Also store with suffix variants
            num_to_id[text_id] = text_id
    return num_to_id


def build_taisho_number_to_all_ids(corpus_ids):
    """Build a map from bare Taisho number to ALL matching corpus IDs.

    Unlike build_taisho_number_to_id_map which returns only the first match,
    this returns all volume variants. E.g., 220 -> [T05n0220, T06n0220, T07n0220].
    Also maps suffixed variants: 974 -> [T19n0974A, T19n0974B, ...].
    """
    num_to_ids = defaultdict(list)
    for text_id in sorted(corpus_ids):
        m = re.match(r'^T(\d{2})n(\d{4})', text_id)
        if m:
            num = int(m.group(2))
            num_to_ids[num].append(text_id)
    return num_to_ids


def get_corpus_ids():
    """Get the set of all text IDs in our corpus from digest results."""
    ids = set()
    data = load_json(CORPUS_IDS_PATH)
    if data:
        for rel in data:
            ids.add(rel["digest_id"])
            ids.add(rel["source_id"])
    # Also add IDs from existing cross-reference
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for section in ["tibetan_parallels", "pali_parallels", "sanskrit_parallels"]:
            if section in xref:
                ids.update(xref[section].keys())
        if "no_parallel_found" in xref:
            ids.update(xref["no_parallel_found"])
    return ids


def _make_attestation(source, confidence=None, note=None):
    """Create a single link attestation dict.

    Args:
        source: Source identifier string (e.g. "lancaster", "nattier1992").
        confidence: Float score (0.0-1.0) for probabilistic sources, or None
            for catalog assertions.
        note: Optional string note (e.g. "Heart Sutra analysis").

    Returns:
        Dict with "source", "confidence", and optionally "note" keys.
    """
    att = {"source": source}
    if confidence is not None:
        att["confidence"] = confidence
    if note:
        att["note"] = note
    return att


class ProvenanceTracker:
    """Tracks per-link provenance for (taisho_id, toh_id) pairs.

    Each link can have multiple attestations from different sources.
    Deduplication is by source name: if the same source attests the same
    link twice, only the first attestation is kept (unless the second has
    a higher confidence score).
    """

    def __init__(self):
        # (taisho_id, toh_id) -> list of attestation dicts
        self._data = defaultdict(list)

    def add(self, taisho_id, toh_id, source, confidence=None, note=None):
        """Record that `source` attests the link taisho_id -> toh_id."""
        key = (taisho_id, toh_id)
        existing = self._data[key]
        # Check for duplicate source
        for att in existing:
            if att["source"] == source:
                # Keep the one with higher confidence (or the one with a note)
                if confidence is not None and (
                    att.get("confidence") is None
                    or confidence > att.get("confidence", 0)
                ):
                    att["confidence"] = confidence
                if note and not att.get("note"):
                    att["note"] = note
                return
        existing.append(_make_attestation(source, confidence, note))

    def get(self, taisho_id, toh_id):
        """Return list of attestations for a given link, or empty list."""
        return self._data.get((taisho_id, toh_id), [])

    def get_sources(self, taisho_id, toh_id):
        """Return set of source names for a given link."""
        return {att["source"] for att in self.get(taisho_id, toh_id)}

    def all_links(self):
        """Iterate over all tracked links as (taisho_id, toh_id, attestations)."""
        for (taisho_id, toh_id), atts in self._data.items():
            yield taisho_id, toh_id, atts

    def link_count(self):
        """Total number of distinct links tracked."""
        return len(self._data)


def merge_sources():
    """Merge all data sources into a unified concordance with per-link provenance.

    Returns:
        concordance: defaultdict mapping taisho_id to
            {tibetan: set, pali: set, sanskrit: set, nanjio: set, sources: set}
        corpus_ids: set of all known Taisho text IDs
        provenance: ProvenanceTracker with per-link attestations
    """
    # Master lookup: taisho_id -> {tibetan: set(), pali: set(), ...}
    concordance = defaultdict(lambda: {
        "tibetan": set(),
        "pali": set(),
        "sanskrit": set(),
        "nanjio": set(),
        "sources": set(),
    })

    provenance = ProvenanceTracker()

    corpus_ids = get_corpus_ids()
    num_to_id = build_taisho_number_to_id_map(corpus_ids)
    num_to_all = build_taisho_number_to_all_ids(corpus_ids)
    print(f"Corpus has {len(corpus_ids)} text IDs, "
          f"{len(num_to_id)} number->ID mappings")

    def resolve_taisho_id(raw):
        """Resolve a raw Taisho reference to a canonical corpus ID."""
        norm = normalize_taisho_id(raw)
        if isinstance(norm, int):
            return num_to_id.get(norm)
        if norm in corpus_ids:
            return norm
        # Try stripping suffix
        base = re.sub(r'[A-Za-z]+$', '', norm)
        if base in corpus_ids:
            return base
        return norm if re.match(r'^T\d{2}n\d{4}', norm) else None

    # --- Source 1: Existing cross_reference.json ---
    print("\n1. Loading existing cross_reference.json...")
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for text_id, parallels in xref.get("tibetan_parallels", {}).items():
            for p in parallels:
                concordance[text_id]["tibetan"].add(p)
                if p.startswith("Toh "):
                    provenance.add(text_id, p, "existing")
            concordance[text_id]["sources"].add("existing")
        for text_id, parallels in xref.get("pali_parallels", {}).items():
            if isinstance(parallels, list):
                concordance[text_id]["pali"].update(parallels)
            concordance[text_id]["sources"].add("existing")
        for text_id, parallels in xref.get("sanskrit_parallels", {}).items():
            if isinstance(parallels, str):
                concordance[text_id]["sanskrit"].add(parallels)
            elif isinstance(parallels, list):
                concordance[text_id]["sanskrit"].update(parallels)
            concordance[text_id]["sources"].add("existing")
        existing_tib = sum(1 for v in concordance.values() if v["tibetan"])
        print(f"  Loaded: {existing_tib} texts with Tibetan parallels")

    # --- Source 2: Lancaster data ---
    print("\n2. Loading Lancaster crossref...")
    lancaster = load_json(LANCASTER_PATH)
    if lancaster:
        added = 0
        for raw_id, data in lancaster.items():
            raw_t = data["taisho"]
            # Handle entries like '974a' - strip letter suffix
            t_num_str = re.sub(r'[a-zA-Z]+$', '', str(raw_t))
            try:
                t_num = int(t_num_str)
            except ValueError:
                continue
            text_id = num_to_id.get(t_num)
            if not text_id:
                continue

            # Tohoku
            for toh in (data.get("tohoku") or []):
                toh_id = f"Toh {toh}"
                concordance[text_id]["tibetan"].add(toh_id)
                provenance.add(text_id, toh_id, "lancaster")
                added += 1
            # Otani
            for ot in (data.get("otani") or []):
                otani_id = f"Otani {ot}"
                concordance[text_id]["tibetan"].add(otani_id)
                provenance.add(text_id, otani_id, "lancaster")
            # Sanskrit
            if data.get("sanskrit_title"):
                concordance[text_id]["sanskrit"].add(data["sanskrit_title"])
            # Nanjio
            if data.get("nanjio"):
                concordance[text_id]["nanjio"].add(f"Nj {data['nanjio']}")

            concordance[text_id]["sources"].add("lancaster")
        print(f"  Added {added} Tohoku mappings from Lancaster")

    # --- Source 3: acmuller Tohoku->Taisho scrape ---
    print("\n3. Loading acmuller Tohoku->Taisho scrape...")
    tohoku_data = load_json(TOHOKU_ACMULLER_PATH)
    if tohoku_data:
        new_toh_mappings = 0
        for toh_key, entry in tohoku_data.get("entries", {}).items():
            toh_num = entry["tohoku"]
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                toh_id = f"Toh {toh_num}"
                if toh_id not in concordance[text_id]["tibetan"]:
                    new_toh_mappings += 1
                concordance[text_id]["tibetan"].add(toh_id)
                provenance.add(text_id, toh_id, "acmuller_tohoku")
                # Otani (already has "Otani " prefix)
                for ot in entry.get("otani", []):
                    concordance[text_id]["tibetan"].add(ot)
                    provenance.add(text_id, ot, "acmuller_tohoku")
                # Nanjio
                for nj in entry.get("nanjio", []):
                    concordance[text_id]["nanjio"].add(nj)
                # Sanskrit
                if entry.get("sanskrit_title"):
                    concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                concordance[text_id]["sources"].add("acmuller_tohoku")
        print(f"  Added {new_toh_mappings} new Toh mappings from acmuller")

    # --- Source 4: CBETA Jinglu Sanskrit scrape ---
    print("\n4. Loading CBETA Jinglu Sanskrit scrape...")
    cbeta_data = load_json(CBETA_SANSKRIT_PATH)
    if cbeta_data:
        new_from_cbeta = 0
        for entry_id, entry in cbeta_data.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                # Tohoku
                for toh in entry.get("tohoku", []):
                    toh_id = toh if toh.startswith("Toh ") else f"Toh {toh}"
                    if toh_id not in concordance[text_id]["tibetan"]:
                        new_from_cbeta += 1
                    concordance[text_id]["tibetan"].add(toh_id)
                    provenance.add(text_id, toh_id, "cbeta_sanskrit")
                # Otani (already has "Otani " prefix)
                for ot in entry.get("otani", []):
                    concordance[text_id]["tibetan"].add(ot)
                    provenance.add(text_id, ot, "cbeta_sanskrit")
                concordance[text_id]["sources"].add("cbeta_sanskrit")
        print(f"  Added {new_from_cbeta} new Toh mappings from CBETA Sanskrit")

    # --- Source 5: Lancaster FULL K-number scrape ---
    print("\n5. Loading Lancaster full K-number scrape...")
    lancaster_full = load_json(LANCASTER_FULL_PATH)
    if lancaster_full:
        new_from_lanc_full = 0
        for k_key, entry in lancaster_full.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                # Tohoku
                for toh in entry.get("tohoku", []):
                    toh_id = toh if toh.startswith("Toh ") else f"Toh {toh}"
                    if toh_id not in concordance[text_id]["tibetan"]:
                        new_from_lanc_full += 1
                    concordance[text_id]["tibetan"].add(toh_id)
                    provenance.add(text_id, toh_id, "lancaster_full")
                # Otani (already has "Otani " prefix)
                for ot in entry.get("otani", []):
                    concordance[text_id]["tibetan"].add(ot)
                    provenance.add(text_id, ot, "lancaster_full")
                # Nanjio
                for nj in entry.get("nanjio", []):
                    concordance[text_id]["nanjio"].add(nj)
                # Sanskrit
                if entry.get("sanskrit_title"):
                    concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                concordance[text_id]["sources"].add("lancaster_full")
        print(f"  Added {new_from_lanc_full} new Toh mappings from Lancaster full")

    # --- Source 6: CBETA Jinglu Tibetan catalogue ---
    # Uses num_to_all for bare numbers (e.g. T220) to map all volume variants.
    print("\n6. Loading CBETA Jinglu Tibetan catalogue...")
    cbeta_tib = load_json(CBETA_TIBETAN_PATH)
    if cbeta_tib:
        new_from_cbeta_tib = 0
        for entry_id, entry in cbeta_tib.get("entries", {}).items():
            for t_raw in entry.get("taisho", []):
                # Resolve bare numbers to all corpus variants
                norm = normalize_taisho_id(t_raw)
                if isinstance(norm, int):
                    text_ids = num_to_all.get(norm, [])
                elif norm in corpus_ids:
                    text_ids = [norm]
                else:
                    base = re.sub(r'[A-Za-z]+$', '', norm)
                    text_ids = [base] if base in corpus_ids else []
                for text_id in text_ids:
                    if text_id not in corpus_ids:
                        continue
                    # Entry number as Tohoku-like reference
                    if entry.get("entry_number"):
                        toh_id = f"Toh {entry['entry_number']}"
                        if toh_id not in concordance[text_id]["tibetan"]:
                            new_from_cbeta_tib += 1
                        concordance[text_id]["tibetan"].add(toh_id)
                        provenance.add(text_id, toh_id, "cbeta_tibetan")
                    # Nanjio
                    if entry.get("nanjio"):
                        concordance[text_id]["nanjio"].add(entry["nanjio"])
                    # Sanskrit
                    if entry.get("sanskrit_title"):
                        concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                    concordance[text_id]["sources"].add("cbeta_tibetan")
        print(f"  Added {new_from_cbeta_tib} new Toh mappings from CBETA Tibetan")

    # --- Source 7: rKTs kernel Taisho cross-refs ---
    print("\n7. Loading rKTs kernel Taisho cross-refs...")
    rkts_data = load_json(RKTS_PATH)
    if rkts_data:
        new_from_rkts = 0
        for rkts_id, entry in rkts_data.get("entries", {}).items():
            toh_num = entry.get("tohoku")
            for t_raw in entry.get("taisho", []):
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                if toh_num:
                    toh_id = f"Toh {toh_num}"
                    if toh_id not in concordance[text_id]["tibetan"]:
                        new_from_rkts += 1
                    concordance[text_id]["tibetan"].add(toh_id)
                    provenance.add(text_id, toh_id, "rkts")
                # Sanskrit
                if entry.get("sanskrit_title"):
                    concordance[text_id]["sanskrit"].add(entry["sanskrit_title"])
                concordance[text_id]["sources"].add("rkts")
        print(f"  Added {new_from_rkts} new Toh mappings from rKTs")

    # --- Source 8: 84000 TEI data (Toh titles for enrichment) ---
    print("\n8. Loading 84000 TEI Tohoku extraction...")
    toh_84000 = load_json(TOHOKU_84000_PATH)
    if toh_84000:
        titles_added = 0
        for toh_key, entry in toh_84000.get("entries", {}).items():
            titles = entry.get("titles", {})
            if titles.get("english") or titles.get("sanskrit"):
                # Enrich existing entries that already have this Toh number
                for text_id, data in concordance.items():
                    if toh_key in data["tibetan"]:
                        if titles.get("sanskrit"):
                            data["sanskrit"].add(titles["sanskrit"])
                            titles_added += 1
        print(f"  Enriched {titles_added} entries with 84000 titles")

    # --- Source 8b: 84000 TEI Taisho cross-references ---
    # Uses num_to_all to map bare Taisho numbers to ALL volume/suffix variants.
    print("\n8b. Loading 84000 TEI Taisho cross-references...")
    taisho_84000 = load_json(TAISHO_84000_REFS_PATH)
    if taisho_84000:
        new_from_84000_refs = 0
        for toh_key, entry in taisho_84000.get("entries", {}).items():
            toh_str = entry.get("toh")
            if not toh_str:
                continue
            toh_id = f"Toh {toh_str}"
            for t_num in entry.get("taisho_nums", []):
                # Map to ALL corpus IDs sharing this number
                for text_id in num_to_all.get(t_num, []):
                    if text_id not in corpus_ids:
                        continue
                    if toh_id not in concordance[text_id]["tibetan"]:
                        new_from_84000_refs += 1
                    concordance[text_id]["tibetan"].add(toh_id)
                    provenance.add(text_id, toh_id, "84000_tei_refs")
                    concordance[text_id]["sources"].add("84000_tei_refs")
        print(f"  Added {new_from_84000_refs} new Toh mappings "
              f"from 84000 TEI cross-references")
    else:
        print("  No 84000 TEI Taisho refs found, skipping.")

    # --- Source 9: Sanskrit title matches ---
    print("\n9. Loading Sanskrit title matches...")
    skt_matches = load_json(SANSKRIT_MATCHES_PATH)
    if skt_matches:
        new_from_skt = 0
        validated = skt_matches.get("validated", [])
        new_proposals = skt_matches.get("new_proposals", [])

        # Only merge validated matches (confirmed by existing concordance) and
        # new_proposals (not contradicted). Do NOT merge contradicted matches.
        for match in validated + new_proposals:
            taisho_id = match.get("taisho_id")
            toh_num = match.get("tohoku")
            if not taisho_id or toh_num is None or toh_num < 0:
                continue
            if taisho_id not in corpus_ids:
                continue

            toh_id = f"Toh {toh_num}"
            score = match.get("match_score")
            match_type = match.get("match_type", "unknown")
            note = f"Sanskrit title {match_type} match"
            if match.get("taisho_sanskrit") and match.get("kangyur_sanskrit"):
                note += (f": {match['taisho_sanskrit']} ~ "
                         f"{match['kangyur_sanskrit']}")

            if toh_id not in concordance[taisho_id]["tibetan"]:
                new_from_skt += 1
            concordance[taisho_id]["tibetan"].add(toh_id)
            provenance.add(
                taisho_id, toh_id, "sanskrit_title_match",
                confidence=score, note=note,
            )
            concordance[taisho_id]["sources"].add("sanskrit_title_match")

        print(f"  Merged {len(validated)} validated + {len(new_proposals)} "
              f"new proposals ({new_from_skt} new Toh mappings)")
    else:
        print("  No Sanskrit title matches found, skipping.")

    # --- Source 10: Scholarly citations (data/scholarly_citations/*.json) ---
    print("\n10. Loading scholarly citations...")
    scholarly_count = 0
    new_from_scholarly = 0
    if SCHOLARLY_DIR.is_dir():
        for citation_path in sorted(SCHOLARLY_DIR.glob("*.json")):
            citation_data = load_json(citation_path)
            if not citation_data:
                continue
            # Expected format:
            # {
            #   "citation_key": "silk2019",
            #   "full_citation": "Silk, Jonathan A. ...",
            #   "links": [
            #     {"taisho": "T08n0251", "tohoku": "Toh 21",
            #      "note": "Heart Sutra analysis"},
            #     ...
            #   ],
            #   "errors": [
            #     {"taisho": "T12n0374", "tohoku": "Toh 121",
            #      "status": "error",
            #      "note": "Wrong Tohoku assignment; should be Toh 119"}
            #   ]
            # }
            citation_key = citation_data.get(
                "citation_key", citation_path.stem
            )
            links = citation_data.get("links", [])
            errors = citation_data.get("errors", [])

            for link in links:
                t_raw = link.get("taisho", "")
                toh_raw = link.get("tohoku", "")
                note = link.get("note")

                # Resolve taisho ID
                text_id = resolve_taisho_id(t_raw) if t_raw else None
                if not text_id or text_id not in corpus_ids:
                    continue

                # Normalize tohoku ID
                if isinstance(toh_raw, int):
                    toh_id = f"Toh {toh_raw}"
                elif isinstance(toh_raw, str):
                    toh_id = toh_raw if toh_raw.startswith("Toh ") else f"Toh {toh_raw}"
                else:
                    continue

                if toh_id not in concordance[text_id]["tibetan"]:
                    new_from_scholarly += 1
                concordance[text_id]["tibetan"].add(toh_id)
                # Use per-link source_key if provided, else file-level key
                link_key = link.get("source_key", citation_key)
                provenance.add(
                    text_id, toh_id, link_key,
                    confidence=None, note=note,
                )
                concordance[text_id]["sources"].add(link_key)
                scholarly_count += 1

            # Record errors as provenance entries with status="error"
            for err in errors:
                t_raw = err.get("taisho", "")
                toh_raw = err.get("tohoku", "")
                note = err.get("note", "")
                status = err.get("status", "error")

                text_id = resolve_taisho_id(t_raw) if t_raw else None
                if not text_id:
                    continue

                if isinstance(toh_raw, int):
                    toh_id = f"Toh {toh_raw}"
                elif isinstance(toh_raw, str):
                    toh_id = toh_raw if toh_raw.startswith("Toh ") else f"Toh {toh_raw}"
                else:
                    continue

                # Do NOT add the link to the concordance; just record the error
                # provenance so downstream consumers can see it.
                error_note = f"[{status}] {note}" if note else f"[{status}]"
                provenance.add(
                    text_id, toh_id, f"{citation_key}:error",
                    confidence=None, note=error_note,
                )

        print(f"  Loaded {scholarly_count} scholarly links "
              f"({new_from_scholarly} new Toh mappings)")
    else:
        print(f"  No scholarly citations directory found at {SCHOLARLY_DIR}")

    # --- Source 11: MITRA parallel corpus (Nehrdich & Keutzer 2025) ---
    # For high precision, only add MITRA links to the active concordance
    # when they are "strong" (>=100 aligned sentences, confidence >=
    # MITRA_STRONG_THRESHOLD). Moderate links (20-99 sentences) are recorded
    # in provenance for documentation but only appear in the active tibetan
    # set if a catalog source has independently added the same link.
    print("\n11. Loading MITRA parallel corpus...")
    mitra_data = load_json(MITRA_PATH)
    if mitra_data:
        new_from_mitra = 0
        mitra_strong = 0
        mitra_moderate = 0
        mitra_entries = mitra_data.get("entries", {})
        for entry_id, entry in mitra_entries.items():
            text_id = resolve_taisho_id(entry["taisho"])
            if not text_id or text_id not in corpus_ids:
                continue
            toh_id = entry["tohoku"]
            confidence = entry.get("confidence", 0)
            # Always record in provenance
            provenance.add(
                text_id, toh_id, "mitra",
                confidence=confidence,
                note=entry.get("note"),
            )
            concordance[text_id]["sources"].add("mitra")
            # Only add to active tibetan set if strong
            if confidence >= MITRA_STRONG_THRESHOLD:
                mitra_strong += 1
                if toh_id not in concordance[text_id]["tibetan"]:
                    new_from_mitra += 1
                concordance[text_id]["tibetan"].add(toh_id)
            else:
                mitra_moderate += 1
                # Moderate links: don't add to tibetan set (but if a
                # catalog source already added this toh_id, it stays)
        print(f"  Loaded {len(mitra_entries)} MITRA pairs: "
              f"{mitra_strong} strong, {mitra_moderate} moderate "
              f"({new_from_mitra} new Toh mappings from strong links)")
    else:
        print(f"  No MITRA data found at {MITRA_PATH}")

    # --- Source 12: SuttaCentral Pali parallels ---
    print("\n12. Loading SuttaCentral Pali parallels...")
    sc_pali = load_json(SC_PALI_PATH)
    if sc_pali:
        pali_parallels_data = sc_pali.get("pali_parallels", {})
        link_details = sc_pali.get("link_details", {})
        sc_added = 0
        sc_new_texts = 0
        for text_id, pali_refs in pali_parallels_data.items():
            if text_id not in corpus_ids:
                continue
            had_pali = bool(concordance[text_id]["pali"])
            for pali_ref in pali_refs:
                concordance[text_id]["pali"].add(pali_ref)
                # Get link type for confidence
                detail = link_details.get(text_id, {}).get(pali_ref, {})
                link_type = detail.get("type", "full")
                confidence = 0.9 if link_type == "full" else 0.7
                note = None
                agama_refs = detail.get("agama_refs")
                if agama_refs:
                    note = f"via {', '.join(agama_refs)}"
                provenance.add(text_id, pali_ref,
                               "suttacentral_parallels",
                               confidence=confidence, note=note)
                sc_added += 1
            concordance[text_id]["sources"].add("suttacentral_parallels")
            if not had_pali:
                sc_new_texts += 1
        print(f"  Loaded {sc_added} Pali links for "
              f"{len(pali_parallels_data)} texts "
              f"({sc_new_texts} newly linked)")
    else:
        print(f"  No SC Pali data found at {SC_PALI_PATH}")

    # --- Post-processing: Tohoku-to-Otani concordance ---
    # After all Tohoku numbers have been collected from all sources,
    # look up corresponding Otani (Peking edition) numbers from the
    # rKTs-derived concordance.
    print("\n  Post-processing: Adding Otani numbers from Tohoku-Otani concordance...")
    otani_data = load_json(OTANI_CONCORDANCE_PATH)
    if otani_data:
        otani_conc = otani_data.get("concordance", {})
        otani_added = 0
        for text_id, data in concordance.items():
            for toh_id in list(data["tibetan"]):
                if not toh_id.startswith("Toh "):
                    continue
                otani_nums = otani_conc.get(toh_id, [])
                for otani_id in otani_nums:
                    if otani_id not in data["tibetan"]:
                        otani_added += 1
                    data["tibetan"].add(otani_id)
                    provenance.add(text_id, otani_id, "rkts_concordance")
        print(f"  Added {otani_added} Otani numbers from Tohoku-Otani concordance")
    else:
        print("  No Tohoku-Otani concordance found, skipping.")

    # --- Post-processing: Peking-only texts with Taisho parallels ---
    # Some texts exist only in the Peking (Q) edition with no Derge counterpart,
    # so they have Otani numbers but no Tohoku numbers. Add Otani-only entries
    # for those with known Taisho parallels.
    PEKING_ONLY_PATH = RESULTS_DIR / "peking_only_texts.json"
    peking_data = load_json(PEKING_ONLY_PATH)
    if peking_data:
        peking_added = 0
        for entry in peking_data.get("texts_with_taisho_parallels", []):
            otani_id = entry.get("otani")
            if not otani_id:
                continue
            # Resolve Taisho IDs from Lancaster references
            for lanc in entry.get("taisho_parallels", {}).get("from_lancaster", []):
                t_raw = lanc.get("taisho", "")
                text_id = resolve_taisho_id(t_raw)
                if not text_id or text_id not in corpus_ids:
                    continue
                concordance[text_id]["tibetan"].add(otani_id)
                provenance.add(text_id, otani_id, "lancaster")
                concordance[text_id]["sources"].add("lancaster")
                peking_added += 1
            # Also try the from_concordance references
            for t_id in entry.get("taisho_parallels", {}).get("from_concordance", []):
                if t_id in corpus_ids:
                    concordance[t_id]["tibetan"].add(otani_id)
                    provenance.add(t_id, otani_id, "peking_only")
                    peking_added += 1
        print(f"\n  Post-processing: Added {peking_added} Peking-only Otani links")
    else:
        print("\n  No Peking-only texts data found, skipping.")

    return concordance, corpus_ids, provenance


def build_output(concordance, corpus_ids, provenance):
    """Build the output JSON with backward-compatible format plus new provenance.

    The output preserves the old-format fields (tibetan_parallels as simple
    sorted lists) alongside the new link_provenance section.
    """
    tibetan_parallels = {}
    pali_parallels = {}
    sanskrit_parallels = {}
    no_parallel = []

    for text_id in sorted(corpus_ids):
        data = concordance.get(text_id)
        has_any = False

        if data and data["tibetan"]:
            tibetan_parallels[text_id] = sorted(data["tibetan"])
            has_any = True
        if data and data["pali"]:
            pali_parallels[text_id] = sorted(data["pali"])
            has_any = True
        if data and data["sanskrit"]:
            # Keep as string if single, list if multiple
            skt = sorted(data["sanskrit"])
            sanskrit_parallels[text_id] = skt[0] if len(skt) == 1 else skt
            has_any = True

        if not has_any:
            no_parallel.append(text_id)

    # Summary
    total = len(corpus_ids)
    with_tib = len(tibetan_parallels)
    with_pali = len(pali_parallels)
    with_skt = len(sanskrit_parallels)
    with_any = len(corpus_ids) - len(no_parallel)

    summary = {
        "total_texts": total,
        "with_tibetan": with_tib,
        "with_pali": with_pali,
        "with_sanskrit": with_skt,
        "with_any_parallel": with_any,
        "no_parallel": len(no_parallel),
        "pct_tibetan": round(100 * with_tib / total, 1) if total else 0,
        "pct_any": round(100 * with_any / total, 1) if total else 0,
    }

    # Per-text source tracking (backward-compatible)
    sources_used = defaultdict(int)
    for data in concordance.values():
        for s in data.get("sources", set()):
            sources_used[s] += 1

    # Build link_provenance: taisho_id -> { toh_id -> [attestations] }
    # Only include entries that have attestations (i.e., Toh links)
    link_provenance = {}
    for taisho_id, toh_id, attestations in provenance.all_links():
        if taisho_id not in link_provenance:
            link_provenance[taisho_id] = {}
        link_provenance[taisho_id][toh_id] = attestations

    # Sort the link_provenance for deterministic output
    sorted_provenance = {}
    for taisho_id in sorted(link_provenance.keys()):
        sorted_provenance[taisho_id] = {}
        for toh_id in sorted(link_provenance[taisho_id].keys()):
            atts = link_provenance[taisho_id][toh_id]
            # Sort attestations by source name for determinism
            sorted_provenance[taisho_id][toh_id] = sorted(
                atts, key=lambda a: a["source"]
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": summary,
        "sources": dict(sources_used),
        "tibetan_parallels": tibetan_parallels,
        "pali_parallels": pali_parallels,
        "sanskrit_parallels": sanskrit_parallels,
        "no_parallel_found": no_parallel,
        "link_provenance": sorted_provenance,
    }


def compare_with_existing(output, existing_path):
    """Compare expanded concordance with existing one."""
    existing = load_json(existing_path)
    if not existing:
        return

    old_tib = len(existing.get("tibetan_parallels", {}))
    new_tib = len(output["tibetan_parallels"])
    old_pali = len(existing.get("pali_parallels", {}))
    new_pali = len(output["pali_parallels"])
    old_skt = len(existing.get("sanskrit_parallels", {}))
    new_skt = len(output["sanskrit_parallels"])

    old_total = existing.get("summary", {}).get(
        "total_texts", output["summary"]["total_texts"]
    )
    old_any = old_total - len(existing.get("no_parallel_found", []))
    new_any = output["summary"]["with_any_parallel"]

    print(f"\n{'='*50}")
    print("COMPARISON: Existing vs. Expanded Concordance")
    print(f"{'='*50}")
    print(f"{'Category':<25} {'Old':>8} {'New':>8} {'Delta':>8}")
    print(f"{'-'*50}")
    print(f"{'Tibetan parallels':<25} {old_tib:>8} {new_tib:>8} "
          f"{new_tib - old_tib:>+8}")
    print(f"{'Pali parallels':<25} {old_pali:>8} {new_pali:>8} "
          f"{new_pali - old_pali:>+8}")
    print(f"{'Sanskrit parallels':<25} {old_skt:>8} {new_skt:>8} "
          f"{new_skt - old_skt:>+8}")
    print(f"{'Any parallel':<25} {old_any:>8} {new_any:>8} "
          f"{new_any - old_any:>+8}")
    print(f"{'No parallel':<25} "
          f"{len(existing.get('no_parallel_found', [])):>8} "
          f"{len(output['no_parallel_found']):>8}")

    # Show new Tibetan entries
    old_tib_set = set(existing.get("tibetan_parallels", {}).keys())
    new_tib_set = set(output["tibetan_parallels"].keys())
    newly_found = new_tib_set - old_tib_set
    if newly_found:
        print(f"\nNewly found Tibetan parallels ({len(newly_found)} texts):")
        for t_id in sorted(newly_found)[:30]:
            print(f"  {t_id}: {output['tibetan_parallels'][t_id]}")
        if len(newly_found) > 30:
            print(f"  ... and {len(newly_found) - 30} more")


def print_provenance_stats(provenance):
    """Print statistics about the per-link provenance tracking."""
    total_links = provenance.link_count()
    source_counts = defaultdict(int)
    multi_source = 0
    with_confidence = 0

    for _, _, atts in provenance.all_links():
        for att in atts:
            source_counts[att["source"]] += 1
            if att.get("confidence") is not None:
                with_confidence += 1
        if len(atts) >= 2:
            multi_source += 1

    print(f"\nPer-link provenance statistics:")
    print(f"  Total distinct links tracked: {total_links}")
    print(f"  Links with 2+ sources: {multi_source}")
    print(f"  Links with confidence scores: {with_confidence}")
    print(f"\n  Attestations by source:")
    for source, count in sorted(source_counts.items()):
        print(f"    {source}: {count} links")


def flag_known_errors(concordance, provenance):
    """Flag known catalog errors in provenance and remove from tibetan_parallels.

    Loads data/known_errors.json. For each error:
    - Marks all attestations on the erroneous (taisho_id, toh) link with
      "flagged_error": true and optionally "correct_toh".
    - Removes the erroneous Toh from the text's tibetan_parallels set.

    Returns a list of error summary dicts for inclusion in the output JSON.
    """
    errors_data = load_json(KNOWN_ERRORS_PATH)
    if not errors_data:
        print("  No known_errors.json found, skipping error flagging.")
        return []

    errors = errors_data.get("errors", [])
    summary = []

    for err in errors:
        taisho_id = err.get("taisho_id")
        erroneous_toh = err.get("erroneous_toh")
        if not taisho_id or not erroneous_toh:
            print(f"  WARNING: Malformed error entry (missing taisho_id or "
                  f"erroneous_toh): {err}")
            continue
        correct_toh = err.get("correct_toh")
        note = err.get("note", "")

        # Flag attestations in provenance
        attestations = provenance.get(taisho_id, erroneous_toh)
        flagged_count = 0
        for att in attestations:
            att["flagged_error"] = True
            if correct_toh:
                att["correct_toh"] = correct_toh
            flagged_count += 1

        # Remove erroneous Toh from the concordance's tibetan set
        removed = False
        if taisho_id in concordance:
            tib = concordance[taisho_id]["tibetan"]
            if erroneous_toh in tib:
                tib.discard(erroneous_toh)
                removed = True

        # Check that correct Toh is present (if applicable)
        correct_present = False
        if correct_toh and taisho_id in concordance:
            correct_present = correct_toh in concordance[taisho_id]["tibetan"]

        entry = {
            "taisho_id": taisho_id,
            "erroneous_toh": erroneous_toh,
            "correct_toh": correct_toh,
            "error_type": err.get("error_type", "unknown"),
            "flagged_attestations": flagged_count,
            "removed_from_parallels": removed,
            "correct_toh_present": correct_present,
            "note": note,
        }
        summary.append(entry)

        status = "FLAGGED" if flagged_count > 0 else "NO ATTESTATIONS"
        correct_str = f" (correct {correct_toh} "
        correct_str += "present)" if correct_present else "MISSING)"
        if not correct_toh:
            correct_str = " (no correct Toh known)"
        print(f"  {status}: {taisho_id} {erroneous_toh} -> "
              f"{flagged_count} attestations flagged, "
              f"removed={removed}{correct_str}")

    return summary


def _is_catalog_or_scholarly_source(source):
    """Check if a source is a catalog database or scholarly citation.

    Returns True for authoritative sources that can independently establish
    a parallel: catalog databases (e.g., "lancaster", "cbeta_tibetan") and
    scholarly citations (e.g., "silk2019", "nattier1992"). Returns False for
    computational sources, infrastructure sources, and error sources.
    """
    if source in CATALOG_SOURCES or source in COMPUTATIONAL_SOURCES:
        return source in CATALOG_SOURCES
    # rkts_concordance is an infrastructure source (Otani derivation), not
    # a catalog or computational source.
    if source == "rkts_concordance":
        return False
    # Error sources (e.g., "silk2019:error") are not positive attestations.
    if source.endswith(":error"):
        return False
    # Remaining sources (e.g., "nattier1992", "buswell1989") are scholarly.
    return True


def classify_links(concordance, provenance):
    """Classify each (taisho_id, toh_id) link by relationship type.

    Returns:
        link_classifications: dict {taisho_id: {toh_id: {type, basis}}}
        classification_summary: dict with counts per type
    """
    # --- Step 0: Build helpers ---

    # Load digest relationships for inherited-parallel detection.
    digest_rels = load_json(CORPUS_IDS_PATH) or []
    # derivative_of: maps digest_id -> [(source_id, classification, coverage)]
    derivative_of = defaultdict(list)
    for rel in digest_rels:
        derivative_of[rel["digest_id"]].append((
            rel["source_id"],
            rel["classification"],
            rel.get("coverage", 0),
        ))

    # Count per-text computational-only Toh links.
    # A Toh link is "computational-only" if it is attested ONLY by sources
    # in COMPUTATIONAL_SOURCES (zero catalog backing).
    comp_only_count = defaultdict(int)  # taisho_id -> count
    for taisho_id, toh_id, atts in provenance.all_links():
        if not toh_id.startswith("Toh "):
            continue
        sources = {att["source"] for att in atts}
        has_catalog = any(_is_catalog_or_scholarly_source(s) for s in sources)
        if not has_catalog and bool(sources & COMPUTATIONAL_SOURCES):
            comp_only_count[taisho_id] += 1

    # --- Step 1: Classify each link ---
    link_classifications = {}
    type_counts = defaultdict(int)

    for taisho_id, toh_id, atts in provenance.all_links():
        # Only classify Toh links (not Otani, not Pali, not Sanskrit)
        if not toh_id.startswith("Toh "):
            continue

        # Skip links where ALL attestations have been flagged as errors
        if all(att.get("flagged_error") for att in atts):
            if taisho_id not in link_classifications:
                link_classifications[taisho_id] = {}
            link_classifications[taisho_id][toh_id] = {
                "type": "error:flagged",
                "basis": "all attestations flagged as known catalog errors",
            }
            type_counts["error:flagged"] += 1
            continue

        sources = {att["source"] for att in atts}
        has_catalog = any(_is_catalog_or_scholarly_source(s) for s in sources)
        computational_sources = sources & COMPUTATIONAL_SOURCES
        is_computational_only = bool(computational_sources) and not has_catalog

        # Best confidence across all computational sources for this link
        best_comp_conf = 0.0
        for att in atts:
            if att["source"] in COMPUTATIONAL_SOURCES:
                conf = att.get("confidence")
                if conf is not None and conf > best_comp_conf:
                    best_comp_conf = conf

        # Check if this is a Chinese-to-Tibetan text (rKTs-flagged)
        is_chinese_origin = False
        if "rkts" in sources:
            # rKTs entries are Chinese-to-Tibetan translations
            is_chinese_origin = True

        # Check for inherited parallel (text A is excerpt/digest of B,
        # and B has catalog backing for the same Toh)
        is_inherited = False
        inherited_source = None
        if taisho_id in derivative_of:
            for source_id, classification, coverage in derivative_of[taisho_id]:
                if classification in ("excerpt", "digest"):
                    # Check if source_id has catalog-backed link to same Toh
                    source_sources = provenance.get_sources(source_id, toh_id)
                    if any(_is_catalog_or_scholarly_source(s) for s in source_sources):
                        is_inherited = True
                        inherited_source = source_id
                        break

        # Classification logic
        if has_catalog and is_chinese_origin:
            link_type = "chinese_to_tibetan"
            basis = "rKTs Chinese-origin flag with catalog confirmation"
        elif is_chinese_origin and not has_catalog:
            link_type = "chinese_to_tibetan"
            basis = "rKTs Chinese-origin flag"
        elif has_catalog:
            link_type = "parallel"
            basis = "catalog-attested"
        elif is_inherited:
            link_type = "indirect:inherited"
            basis = (f"inherited from {inherited_source} "
                     f"(digest/excerpt relationship)")
        elif is_computational_only and comp_only_count[taisho_id] >= ENCYCLOPEDIC_THRESHOLD:
            link_type = "indirect:quotation"
            basis = (f"encyclopedic pattern: {comp_only_count[taisho_id]} "
                     f"computational-only Toh links")
        elif is_computational_only and best_comp_conf >= COMPUTATIONAL_CONFIDENCE_THRESHOLD:
            link_type = "parallel:computational"
            basis = f"computationally discovered (confidence {best_comp_conf:.2f})"
        else:
            link_type = "uncertain"
            basis = "computational-only, low confidence or insufficient evidence"

        # Store classification
        if taisho_id not in link_classifications:
            link_classifications[taisho_id] = {}
        link_classifications[taisho_id][toh_id] = {
            "type": link_type,
            "basis": basis,
        }
        type_counts[link_type] += 1

    # --- Step 2: Otani numbers inherit parent Toh classification ---
    otani_inherited = 0
    otani_data = load_json(OTANI_CONCORDANCE_PATH)
    otani_conc = otani_data.get("concordance", {}) if otani_data else {}

    # Build inverted index: Otani ID -> parent Toh ID.
    # When an Otani appears under multiple Toh entries (duplicate kernel
    # IDs), keep the first parent found (matching iteration order).
    otani_to_toh = {}
    for toh_key, otani_list in otani_conc.items():
        for otani_id in otani_list:
            if otani_id not in otani_to_toh:
                otani_to_toh[otani_id] = toh_key

    for taisho_id, toh_id, atts in provenance.all_links():
        if not toh_id.startswith("Otani "):
            continue
        parent_toh = otani_to_toh.get(toh_id)
        if not parent_toh:
            continue
        # Look up parent classification
        parent_class = (link_classifications.get(taisho_id, {})
                        .get(parent_toh, {}))
        if parent_class:
            if taisho_id not in link_classifications:
                link_classifications[taisho_id] = {}
            link_classifications[taisho_id][toh_id] = {
                "type": parent_class["type"],
                "basis": f"inherited from {parent_toh}",
            }
            type_counts[parent_class["type"]] += 1
            otani_inherited += 1

    # Build summary
    classification_summary = dict(sorted(type_counts.items()))
    classification_summary["total_classified"] = sum(type_counts.values())

    print(f"\n  Link classification results:")
    for link_type, count in sorted(type_counts.items()):
        print(f"    {link_type}: {count}")
    print(f"    total classified: {classification_summary['total_classified']}")
    print(f"    Otani numbers inheriting parent type: {otani_inherited}")

    return link_classifications, classification_summary


def build_verified_output(concordance, corpus_ids, provenance,
                          link_classifications, error_summary):
    """Build a verified-only concordance containing only catalog-attested links.

    Includes links classified as 'parallel' or 'chinese_to_tibetan' (both
    require at least one catalog source or rKTs attestation). Excludes all
    computational-only links (parallel:computational, indirect:quotation,
    indirect:inherited, uncertain).

    Also filters provenance to include only catalog/scholarly sources.
    """
    VERIFIED_TYPES = {"parallel", "chinese_to_tibetan"}

    tibetan_parallels = {}
    pali_parallels = {}
    sanskrit_parallels = {}
    no_parallel = []

    # Build set of verified (taisho_id, toh_id) pairs from classifications
    verified_toh_links = set()
    for taisho_id, toh_dict in link_classifications.items():
        for toh_id, info in toh_dict.items():
            if info["type"] in VERIFIED_TYPES:
                verified_toh_links.add((taisho_id, toh_id))

    for text_id in sorted(corpus_ids):
        data = concordance.get(text_id)
        has_any = False

        if data and data["tibetan"]:
            # Filter tibetan entries to only verified Toh/Otani links
            verified_tib = set()
            for tib_id in data["tibetan"]:
                if tib_id.startswith("Toh "):
                    if (text_id, tib_id) in verified_toh_links:
                        verified_tib.add(tib_id)
                elif tib_id.startswith("Otani "):
                    # Include Otani if its parent Toh is verified
                    if (text_id, tib_id) in verified_toh_links:
                        verified_tib.add(tib_id)
            if verified_tib:
                tibetan_parallels[text_id] = sorted(verified_tib)
                has_any = True

        # Pali and Sanskrit are always catalog-derived, include as-is
        if data and data["pali"]:
            pali_parallels[text_id] = sorted(data["pali"])
            has_any = True
        if data and data["sanskrit"]:
            skt = sorted(data["sanskrit"])
            sanskrit_parallels[text_id] = skt[0] if len(skt) == 1 else skt
            # Sanskrit title identifications are metadata, not parallels;
            # they do not count toward has_any or with_any_parallel.

        if not has_any:
            no_parallel.append(text_id)

    # Filter provenance to catalog sources only
    verified_provenance = {}
    for taisho_id, toh_id, attestations in provenance.all_links():
        if (taisho_id, toh_id) not in verified_toh_links:
            continue
        catalog_atts = [
            att for att in attestations
            if att["source"] not in COMPUTATIONAL_SOURCES
        ]
        if catalog_atts:
            if taisho_id not in verified_provenance:
                verified_provenance[taisho_id] = {}
            verified_provenance[taisho_id][toh_id] = sorted(
                catalog_atts, key=lambda a: a["source"]
            )

    # Sort provenance
    sorted_provenance = {}
    for taisho_id in sorted(verified_provenance.keys()):
        sorted_provenance[taisho_id] = {}
        for toh_id in sorted(verified_provenance[taisho_id].keys()):
            sorted_provenance[taisho_id][toh_id] = (
                verified_provenance[taisho_id][toh_id]
            )

    # Verified classifications
    verified_classifications = {}
    for taisho_id in sorted(link_classifications.keys()):
        text_cls = {}
        for toh_id in sorted(link_classifications[taisho_id].keys()):
            info = link_classifications[taisho_id][toh_id]
            if info["type"] in VERIFIED_TYPES:
                text_cls[toh_id] = info
        if text_cls:
            verified_classifications[taisho_id] = text_cls

    # Count unique Toh numbers by range
    def _toh_num(toh_str):
        """Extract numeric part from Toh string, ignoring letter suffixes."""
        num_str = re.sub(r'[a-zA-Z]+$', '', toh_str.split()[1])
        try:
            return int(num_str)
        except ValueError:
            return -1

    all_toh = set()
    for toh_list in tibetan_parallels.values():
        for t in toh_list:
            if t.startswith("Toh "):
                all_toh.add(t)
    kangyur_toh = {t for t in all_toh if 1 <= _toh_num(t) <= 1108}
    tengyur_toh = {t for t in all_toh if 1109 <= _toh_num(t) <= 4569}
    out_of_range = {t for t in all_toh
                    if _toh_num(t) < 1 or _toh_num(t) > 4569}
    if out_of_range:
        print(f"  WARNING: {len(out_of_range)} Toh numbers outside "
              f"Kangyur/Tengyur range: {sorted(out_of_range)}")

    # Summary
    total = len(corpus_ids)
    with_tib = len(tibetan_parallels)
    with_pali = len(pali_parallels)
    with_skt = len(sanskrit_parallels)
    with_any = total - len(no_parallel)

    summary = {
        "total_texts": total,
        "with_tibetan": with_tib,
        "with_pali": with_pali,
        "with_sanskrit": with_skt,
        "with_any_parallel": with_any,
        "no_parallel": len(no_parallel),
        "pct_tibetan": round(100 * with_tib / total, 1) if total else 0,
        "pct_any": round(100 * with_any / total, 1) if total else 0,
        "unique_toh": len(all_toh),
        "kangyur_toh": len(kangyur_toh),
        "tengyur_toh": len(tengyur_toh),
        "pct_kangyur": round(100 * len(kangyur_toh) / 1108, 1),
        "pct_tengyur": round(100 * len(tengyur_toh) / 3461, 1),
    }

    # Classification counts for verified types only
    type_counts = {}
    for taisho_id, toh_dict in verified_classifications.items():
        for toh_id, info in toh_dict.items():
            t = info["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
    type_counts["total_classified"] = sum(type_counts.values())
    summary["classification"] = type_counts

    output = {
        "schema_version": SCHEMA_VERSION,
        "verified_only": True,
        "summary": summary,
        "tibetan_parallels": tibetan_parallels,
        "pali_parallels": pali_parallels,
        "sanskrit_parallels": sanskrit_parallels,
        "no_parallel_found": no_parallel,
        "link_provenance": sorted_provenance,
        "link_classifications": verified_classifications,
    }
    if error_summary:
        output["known_errors"] = error_summary

    return output


def print_verified_genre_coverage(verified_output, corpus_ids, concordance):
    """Print genre-stratified coverage for the verified concordance.

    Uses Taisho volume ranges as a proxy for genre.
    """
    # Genre definitions: (label, vol_start, vol_end)
    genres = [
        ("Prajnaparamita", 5, 8),
        ("Agama", 1, 2),
        ("Shastra", 25, 32),
        ("Mahayana sutra", 9, 17),
        ("Vinaya", 22, 24),
        ("Jataka/Avadana", 3, 4),
        ("Tantra/dharani", 18, 21),
        ("Commentary", 33, 44),
        ("Catalogs", 53, 55),
        ("History/biography", 49, 52),
        ("Dunhuang", 85, 85),
        ("Schools (Chan etc.)", 45, 48),
    ]

    tib_set = set(verified_output["tibetan_parallels"].keys())
    pali_set = set(verified_output["pali_parallels"].keys())
    # Sanskrit title identifications are metadata, not parallels
    any_set = tib_set | pali_set

    print(f"\n{'='*60}")
    print("VERIFIED CONCORDANCE: GENRE-STRATIFIED COVERAGE")
    print(f"{'='*60}")
    print(f"{'Genre':<25} {'Vols':>6} {'Texts':>6} {'Parallel':>8} {'Cov':>7}")
    print(f"{'-'*60}")

    total_texts = 0
    total_linked = 0

    for label, v_start, v_end in genres:
        # Find all corpus IDs in this volume range
        genre_ids = set()
        for text_id in corpus_ids:
            m = re.match(r'^T(\d{2})n', text_id)
            if m:
                vol = int(m.group(1))
                if v_start <= vol <= v_end:
                    genre_ids.add(text_id)

        n_texts = len(genre_ids)
        n_linked = len(genre_ids & any_set)
        pct = f"{100 * n_linked / n_texts:.1f}%" if n_texts else "---"
        vol_str = f"{v_start}--{v_end}" if v_start != v_end else str(v_start)
        print(f"  {label:<23} {vol_str:>6} {n_texts:>6} {n_linked:>6} {pct:>7}")
        total_texts += n_texts
        total_linked += n_linked

    pct_total = f"{100 * total_linked / total_texts:.1f}%" if total_texts else "---"
    print(f"{'-'*60}")
    print(f"  {'Total':<23} {'':>6} {total_texts:>6} {total_linked:>6} {pct_total:>7}")


def main():
    print("Building expanded cross-canon concordance (schema v3)")
    print("=" * 50)

    concordance, corpus_ids, provenance = merge_sources()

    # Flag known catalog errors before building output
    print("\n  Post-processing: Flagging known catalog errors...")
    error_summary = flag_known_errors(concordance, provenance)

    # Classify links before building output
    print("\n  Post-processing: Classifying links...")
    link_classifications, classification_summary = classify_links(
        concordance, provenance
    )

    output = build_output(concordance, corpus_ids, provenance)

    # Add known_errors summary to output
    if error_summary:
        output["known_errors"] = error_summary

    # Add link classifications to output
    sorted_classifications = {}
    for taisho_id in sorted(link_classifications.keys()):
        sorted_classifications[taisho_id] = {}
        for toh_id in sorted(link_classifications[taisho_id].keys()):
            sorted_classifications[taisho_id][toh_id] = (
                link_classifications[taisho_id][toh_id]
            )
    output["link_classifications"] = sorted_classifications
    output["summary"]["classification"] = classification_summary

    print(f"\n{'='*50}")
    print("EXPANDED CONCORDANCE SUMMARY")
    print(f"{'='*50}")
    for k, v in output["summary"].items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for k2, v2 in v.items():
                print(f"    {k2}: {v2}")
        else:
            print(f"  {k}: {v}")
    print(f"\nSources contributing (per-text):")
    for source, count in sorted(output["sources"].items()):
        print(f"  {source}: {count} texts")

    print_provenance_stats(provenance)

    compare_with_existing(output, EXISTING_XREF_PATH)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nExpanded concordance written to {OUTPUT_PATH}")
    print(f"  Schema version: {SCHEMA_VERSION}")
    print(f"  link_provenance entries: "
          f"{len(output['link_provenance'])} texts")
    print(f"  link_classifications entries: "
          f"{len(output['link_classifications'])} texts")
    if error_summary:
        print(f"  known_errors flagged: {len(error_summary)}")

    # Build and write verified-only concordance
    print(f"\n{'='*50}")
    print("BUILDING VERIFIED-ONLY CONCORDANCE")
    print(f"{'='*50}")
    verified = build_verified_output(
        concordance, corpus_ids, provenance,
        link_classifications, error_summary,
    )
    with open(VERIFIED_OUTPUT_PATH, "w") as f:
        json.dump(verified, f, indent=2, ensure_ascii=False)
    print(f"\nVerified concordance written to {VERIFIED_OUTPUT_PATH}")
    v_summary = verified["summary"]
    print(f"  Texts with Tibetan parallels: {v_summary['with_tibetan']}")
    print(f"  Unique Toh numbers: {v_summary['unique_toh']}")
    print(f"    Kangyur: {v_summary['kangyur_toh']} of 1,108 "
          f"({v_summary['pct_kangyur']}%)")
    print(f"    Tengyur: {v_summary['tengyur_toh']} of 3,461 "
          f"({v_summary['pct_tengyur']}%)")
    print(f"  Texts with any parallel: {v_summary['with_any_parallel']}")
    print(f"  Classification: {v_summary.get('classification', {})}")

    print_verified_genre_coverage(verified, corpus_ids, concordance)


if __name__ == "__main__":
    main()
