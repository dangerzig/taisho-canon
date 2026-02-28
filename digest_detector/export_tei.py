"""Export the cross-reference concordance as a TEI XML file.

Reads results/cross_reference_expanded.json and reconstructs per-mapping
provenance from the original source files. Outputs a TEI document using
<linkGrp> and <link> elements to results/cross_reference.tei.xml.

Usage:
    python3 -m digest_detector.export_tei
"""

from io import StringIO
from xml.etree.ElementTree import (
    Element,
    ElementTree,
    SubElement,
    indent,
)

from ._export_common import (
    RESULTS_DIR,
    build_provenance,
    gather_metadata,
    load_json,
    load_known_error_pairs,
    EXPANDED_PATH,
)

# Output
OUTPUT_PATH = RESULTS_DIR / "cross_reference.tei.xml"

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"


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

        # Pali parallels (with provenance from SuttaCentral)
        pali_refs = pali.get(taisho_id, [])
        if pali_refs:
            pali_list = pali_refs if isinstance(pali_refs, list) else [pali_refs]
            for p_ref in sorted(pali_list):
                sources = provenance.get((taisho_id, p_ref), set())
                cert = cert_from_count(len(sources)) if sources else "low"
                link = SubElement(
                    entry, "link",
                    type="pali",
                    target=p_ref,
                    cert=cert,
                )
                if sources:
                    note = SubElement(link, "note", type="sources")
                    note.text = "; ".join(sorted(sources))
                link_count += 1

        entry_count += 1

    return ElementTree(tei), entry_count, link_count


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
