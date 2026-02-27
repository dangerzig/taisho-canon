"""Export the cross-reference concordance as a TEI XML file.

Reads results/cross_reference_expanded.json and reconstructs per-mapping
provenance from the original source files. Outputs a TEI document using
<linkGrp> and <link> elements to results/cross_reference.tei.xml.

Usage:
    python3 -m digest_detector.export_tei
"""

import json
import re
from collections import defaultdict
from io import StringIO
from pathlib import Path
from xml.etree.ElementTree import (
    Element,
    ElementTree,
    SubElement,
    indent,
)

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

# Input: expanded concordance
EXPANDED_PATH = RESULTS_DIR / "cross_reference_expanded.json"
KNOWN_ERRORS_PATH = BASE_DIR / "data" / "known_errors.json"

# Source files for provenance reconstruction (same as export_csv)
LANCASTER_PATH = BASE_DIR / "lancaster_taisho_crossref.json"
LANCASTER_FULL_PATH = RESULTS_DIR / "lancaster_full.json"
ACMULLER_PATH = RESULTS_DIR / "tohoku_taisho_crossref.json"
CBETA_SANSKRIT_PATH = RESULTS_DIR / "cbeta_jinglu_sanskrit.json"
CBETA_TIBETAN_PATH = RESULTS_DIR / "cbeta_jinglu_tibetan.json"
RKTS_PATH = RESULTS_DIR / "rkts_taisho.json"
EXISTING_XREF_PATH = RESULTS_DIR / "cross_reference.json"

# Output
OUTPUT_PATH = RESULTS_DIR / "cross_reference.tei.xml"

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def load_json(path):
    """Load a JSON file if it exists."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def build_number_to_id(concordance_keys):
    """Build a map from bare Taisho number to canonical ID."""
    num_to_id = {}
    for text_id in concordance_keys:
        m = re.match(r'^T(\d{2})n(\d{4})', text_id)
        if m:
            num = int(m.group(2))
            if num not in num_to_id:
                num_to_id[num] = text_id
    return num_to_id


def resolve_taisho(raw, num_to_id, valid_ids):
    """Resolve a raw Taisho reference to a canonical ID."""
    if raw in valid_ids:
        return raw
    m = re.match(r'^T(\d+)$', raw)
    if m:
        return num_to_id.get(int(m.group(1)))
    base = re.sub(r'[A-Za-z]+$', '', raw)
    if base in valid_ids:
        return base
    return None


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
    print("  WARNING: No link_provenance in expanded JSON; using fallback "
          "provenance reconstruction (incomplete source coverage).")
    all_ids = set()
    for section in ("tibetan_parallels", "pali_parallels", "sanskrit_parallels"):
        all_ids.update(expanded.get(section, {}).keys())
    all_ids.update(expanded.get("no_parallel_found", []))

    num_to_id = build_number_to_id(all_ids)

    # existing cross_reference.json
    xref = load_json(EXISTING_XREF_PATH)
    if xref:
        for text_id, parallels in xref.get("tibetan_parallels", {}).items():
            for p in parallels:
                if p.startswith("Toh "):
                    provenance[(text_id, p)].add("existing")

    # Lancaster (original)
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

    # Lancaster full
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

    # acmuller
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

    # CBETA Sanskrit
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

    # CBETA Tibetan
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

    # rKTs
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
    """Gather titles, Nanjio, and Otani data from source files.

    Returns:
        titles: dict[taisho_id] -> {chinese_title, sanskrit_title, tibetan_title}
        nanjio: dict[taisho_id] -> set of Nanjio numbers
        otani_map: dict[taisho_id] -> set of Otani numbers
    """
    all_ids = set()
    for section in ("tibetan_parallels", "pali_parallels", "sanskrit_parallels"):
        all_ids.update(expanded.get(section, {}).keys())
    all_ids.update(expanded.get("no_parallel_found", []))

    num_to_id = build_number_to_id(all_ids)

    titles = defaultdict(lambda: {
        "chinese_title": "",
        "sanskrit_title": "",
        "tibetan_title": "",
    })
    nanjio = defaultdict(set)
    otani_map = defaultdict(set)

    # Lancaster (original)
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

    # Lancaster full
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

    # acmuller
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

    # CBETA Tibetan
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

    # rKTs
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


def cert_from_count(n):
    """Map source count to TEI certainty attribute value."""
    if n >= 3:
        return "high"
    elif n == 2:
        return "medium"
    else:
        return "low"


def toh_to_target(toh_str):
    """Convert 'Toh 21' to 'Toh_21' for use as an XML target reference."""
    return toh_str.replace(" ", "_")


def build_tei(expanded, provenance, titles, nanjio_map, otani_map,
              error_pairs=None):
    """Build a TEI XML ElementTree from the concordance data."""
    # Register namespace so output uses the default namespace
    # (ElementTree will write xmlns on root)
    tei = Element("TEI", xmlns=TEI_NS)

    # --- teiHeader ---
    header = SubElement(tei, "teiHeader")

    file_desc = SubElement(header, "fileDesc")

    title_stmt = SubElement(file_desc, "titleStmt")
    title_el = SubElement(title_stmt, "title")
    title_el.text = "Concordance of the Chinese and Tibetan Buddhist Canons"
    author_el = SubElement(title_stmt, "author")
    author_el.text = "Dan Zigmond"

    pub_stmt = SubElement(file_desc, "publicationStmt")
    avail = SubElement(pub_stmt, "availability")
    licence = SubElement(
        avail, "licence",
        target="https://creativecommons.org/licenses/by/4.0/",
    )
    licence.text = "CC BY 4.0"

    source_desc = SubElement(file_desc, "sourceDesc")
    source_p = SubElement(source_desc, "p")
    source_p.text = (
        "Compiled from eight sources: SuttaCentral (existing), Lancaster catalogue, "
        "Lancaster full K-number scrape, Muller Tohoku index (acmuller), "
        "CBETA Jinglu Tibetan, CBETA Jinglu Sanskrit, rKTs, and 84000 TEI."
    )

    # --- text/body ---
    text_el = SubElement(tei, "text")
    body = SubElement(text_el, "body")

    summary = expanded.get("summary", {})
    summary_div = SubElement(body, "div", type="summary")
    summary_p = SubElement(summary_div, "p")
    summary_p.text = (
        f"Total texts in corpus: {summary.get('total_texts', 0)}. "
        f"Texts with Tibetan parallels: {summary.get('with_tibetan', 0)} "
        f"({summary.get('pct_tibetan', 0)}%). "
        f"Texts with any parallel: {summary.get('with_any_parallel', 0)} "
        f"({summary.get('pct_any', 0)}%)."
    )

    link_grp = SubElement(body, "linkGrp", type="concordance")

    tibetan = expanded.get("tibetan_parallels", {})
    pali = expanded.get("pali_parallels", {})
    sanskrit = expanded.get("sanskrit_parallels", {})

    # Collect all taisho IDs that have any parallel
    all_taisho = sorted(
        set(tibetan.keys()) | set(pali.keys()) | set(sanskrit.keys())
    )

    _errors = error_pairs or set()
    entry_count = 0
    link_count = 0

    for taisho_id in all_taisho:
        entry = SubElement(link_grp, "entry")
        entry.set(f"{{{XML_NS}}}id", taisho_id)

        # Tibetan links (Tohoku), excluding known errors
        tib_parallels = tibetan.get(taisho_id, [])
        toh_entries = sorted(
            p for p in tib_parallels
            if p.startswith("Toh ") and (taisho_id, p) not in _errors
        )
        otani_entries = sorted(p for p in tib_parallels if p.startswith("Otani "))
        other_tib = sorted(
            p for p in tib_parallels
            if not p.startswith("Toh ") and not p.startswith("Otani ")
        )

        for toh in toh_entries:
            sources = provenance.get((taisho_id, toh), set())
            cert = cert_from_count(len(sources))
            link = SubElement(
                entry, "link",
                type="tibetan",
                target=toh_to_target(toh),
                cert=cert,
            )
            if sources:
                note = SubElement(link, "note", type="sources")
                note.text = "; ".join(sorted(sources))
            link_count += 1

        # Other Tibetan refs (non-Toh, non-Otani, e.g. "up3.050")
        for ref in other_tib:
            link = SubElement(
                entry, "link",
                type="tibetan",
                target=ref,
                cert="low",
            )
            link_count += 1

        # Otani numbers as link elements with provenance
        all_otani = sorted(set(otani_entries) | otani_map.get(taisho_id, set()))
        for ot in all_otani:
            sources = provenance.get((taisho_id, ot), set())
            cert = cert_from_count(len(sources)) if sources else "low"
            link = SubElement(
                entry, "link",
                type="otani",
                target=ot.replace(" ", "_"),
                cert=cert,
            )
            if sources:
                note = SubElement(link, "note", type="sources")
                note.text = "; ".join(sorted(sources))
            link_count += 1

        # Nanjio numbers
        nj_set = nanjio_map.get(taisho_id, set())
        for nj in sorted(nj_set):
            idno = SubElement(entry, "idno", type="nanjio")
            idno.text = nj

        # Sanskrit title(s)
        skt_data = sanskrit.get(taisho_id)
        if skt_data:
            skt_list = skt_data if isinstance(skt_data, list) else [skt_data]
            for skt in sorted(skt_list):
                idno = SubElement(entry, "idno", type="sanskrit")
                idno.text = skt

        # Titles from source files
        t = titles.get(taisho_id, {})
        if t.get("chinese_title"):
            title_el = SubElement(entry, "title", type="chinese")
            title_el.text = t["chinese_title"]
        if t.get("tibetan_title"):
            title_el = SubElement(entry, "title", type="tibetan")
            title_el.text = t["tibetan_title"]

        # Pali parallels
        pali_refs = pali.get(taisho_id, [])
        if pali_refs:
            pali_list = pali_refs if isinstance(pali_refs, list) else [pali_refs]
            for p_ref in sorted(pali_list):
                link = SubElement(
                    entry, "link",
                    type="pali",
                    target=p_ref,
                )
                link_count += 1

        entry_count += 1

    return ElementTree(tei), entry_count, link_count


def load_known_error_pairs():
    """Load known catalog errors and return a set of (taisho_id, toh) pairs to exclude."""
    errors_data = load_json(KNOWN_ERRORS_PATH)
    if not errors_data:
        return set()
    return {
        (err["taisho_id"], err["erroneous_toh"])
        for err in errors_data.get("errors", [])
    }


def export_tei():
    """Export the concordance as a TEI XML file."""
    expanded = load_json(EXPANDED_PATH)
    if not expanded:
        print(f"ERROR: {EXPANDED_PATH} not found.")
        return

    error_pairs = load_known_error_pairs()
    if error_pairs:
        print(f"Loaded {len(error_pairs)} known error pairs to exclude.")

    print("Reconstructing per-mapping provenance from source files...")
    provenance = build_provenance(expanded)

    print("Gathering titles and auxiliary data from source files...")
    titles, nanjio_map, otani_map = gather_metadata(expanded)

    print("Building TEI XML document...")
    tree, entry_count, link_count = build_tei(
        expanded, provenance, titles, nanjio_map, otani_map,
        error_pairs=error_pairs,
    )

    # Pretty-print with indentation
    indent(tree.getroot(), space="  ")

    # Write XML to string, then prepend a proper declaration and save as UTF-8
    buf = StringIO()
    tree.write(buf, encoding="unicode", xml_declaration=False)
    xml_body = buf.getvalue()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_body)

    print(f"\nTEI XML exported to {OUTPUT_PATH}")
    print(f"  Total <entry> elements: {entry_count}")
    print(f"  Total <link> elements: {link_count}")

    # Certainty distribution
    high = sum(
        1 for (_, _), sources in provenance.items()
        if len(sources) >= 3
    )
    medium = sum(
        1 for (_, _), sources in provenance.items()
        if len(sources) == 2
    )
    low = sum(
        1 for (_, _), sources in provenance.items()
        if len(sources) == 1
    )
    print(f"  Certainty distribution: high={high}, medium={medium}, low={low}")


if __name__ == "__main__":
    export_tei()
