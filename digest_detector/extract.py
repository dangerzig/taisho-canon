"""Stage 1: XML parsing, text extraction, and character normalization.

Parses CBETA TEI P5b XML files, resolves special characters via charDecl,
extracts body text preferring <lem> readings, normalizes to pure CJK, and
tracks <cb:div> boundaries for segment-level analysis.
"""

import json
import re
import logging
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

from lxml import etree
from tqdm import tqdm

from . import config
from .models import TextMetadata, DivSegment, ExtractedText

logger = logging.getLogger(__name__)

# Namespaces used in CBETA TEI P5b
NS = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'cb': 'http://www.cbeta.org/ns/1.0',
    'xml': 'http://www.w3.org/XML/1998/namespace',
}

TEI = '{http://www.tei-c.org/ns/1.0}'
CB = '{http://www.cbeta.org/ns/1.0}'
XML = '{http://www.w3.org/XML/1998/namespace}'

# Tags to skip entirely (their text/tail/children are ignored)
SKIP_TAGS = frozenset([
    f'{TEI}note',
    f'{TEI}rdg',
    f'{TEI}byline',
    f'{CB}docNumber',
    f'{CB}juan',
    f'{TEI}lb',
    f'{TEI}pb',
    f'{TEI}milestone',
    f'{CB}mulu',
])

# Tags whose text content we include
INCLUDE_TAGS = frozenset([
    f'{TEI}p',
    f'{CB}div',
    f'{TEI}head',
    f'{TEI}lem',
    f'{TEI}title',
    f'{TEI}l',       # verse lines
    f'{TEI}lg',      # verse groups
    f'{TEI}body',
    f'{TEI}text',
    f'{TEI}app',     # we walk into app to find lem
])

# CJK character ranges
CJK_RE = re.compile(
    r'[\u4E00-\u9FFF'       # CJK Unified Ideographs
    r'\u3400-\u4DBF'         # CJK Extension A
    r'\U00020000-\U0002A6DF' # CJK Extension B
    r'\U0002A700-\U0002B73F' # CJK Extension C
    r'\U0002B740-\U0002B81F' # CJK Extension D
    r']'
)


def build_char_map(xml_files: list[Path]) -> dict[str, str]:
    """Scan all XML files and build a global CB character → Unicode map.

    Priority:
    1. <localName>normalized form</localName> → use <value>
    2. <mapping type="normal_unicode"> → decode hex
    3. <mapping type="unicode"> → decode hex
    4. Fallback: skip (log warning)
    """
    char_map = {}

    for xml_path in xml_files:
        try:
            tree = etree.parse(str(xml_path))
        except etree.XMLSyntaxError:
            logger.warning("XML parse error in %s, skipping for charDecl", xml_path)
            continue

        for char_elem in tree.iter(f'{TEI}char'):
            char_id = char_elem.get(f'{XML}id')
            if not char_id or char_id in char_map:
                continue

            resolved = None

            # Priority 1: normalized form
            for prop in char_elem.iter(f'{TEI}charProp'):
                local_name = prop.findtext(f'{TEI}localName')
                if local_name == 'normalized form':
                    value = prop.findtext(f'{TEI}value')
                    if value:
                        resolved = value
                        break

            # Priority 2: normal_unicode mapping
            if not resolved:
                for mapping in char_elem.iter(f'{TEI}mapping'):
                    if mapping.get('type') == 'normal_unicode':
                        hex_val = mapping.text
                        if hex_val:
                            resolved = _decode_unicode_hex(hex_val)
                            break

            # Priority 3: unicode mapping
            if not resolved:
                for mapping in char_elem.iter(f'{TEI}mapping'):
                    if mapping.get('type') == 'unicode':
                        hex_val = mapping.text
                        if hex_val:
                            resolved = _decode_unicode_hex(hex_val)
                            break

            if resolved:
                char_map[char_id] = resolved
            else:
                logger.debug("No Unicode mapping for %s", char_id)

    logger.info("Built character map with %d entries", len(char_map))
    return char_map


def _decode_unicode_hex(hex_str: str) -> str | None:
    """Decode 'U+XXXX' or 'U+XXXXX' to a Python character."""
    hex_str = hex_str.strip()
    if hex_str.startswith('U+') or hex_str.startswith('u+'):
        try:
            code_point = int(hex_str[2:], 16)
            return chr(code_point)
        except (ValueError, OverflowError):
            return None
    return None


def normalize_text(text: str) -> str:
    """Strip everything except CJK ideographs."""
    return ''.join(CJK_RE.findall(text))


def _extract_text_recursive(
    elem, char_map: dict[str, str], div_stack: list[str],
    in_dharani: bool = False,
) -> list[tuple[str, str, bool]]:
    """Recursively extract text from an element tree.

    Returns list of (raw_text, div_type, is_dharani) tuples.
    """
    results = []
    tag = elem.tag

    # Skip certain tags entirely
    if tag in SKIP_TAGS:
        return results

    # Handle <app>: only process <lem>, skip <rdg>
    if tag == f'{TEI}app':
        for child in elem:
            if child.tag == f'{TEI}lem':
                results.extend(_extract_text_recursive(
                    child, char_map, div_stack, in_dharani))
        return results

    # Track div type
    current_div = div_stack[-1] if div_stack else 'body'
    is_div = tag == f'{CB}div'
    if is_div:
        div_type = elem.get('type', 'unknown')
        div_stack.append(div_type)
        current_div = div_type

    # Track dharani <p> elements
    is_dharani_p = (tag == f'{TEI}p' and elem.get(f'{CB}type') == 'dharani')
    current_dharani = in_dharani or is_dharani_p

    try:
        # Handle <g ref="#CBnnnnn"/> (special character reference)
        if tag == f'{TEI}g':
            ref = elem.get('ref', '')
            if ref.startswith('#'):
                char_id = ref[1:]
                resolved = char_map.get(char_id, '')
                if resolved:
                    results.append((resolved, current_div, current_dharani))

        # Include text content from this element
        if elem.text:
            results.append((elem.text, current_div, current_dharani))

        # Recurse into children
        for child in elem:
            results.extend(_extract_text_recursive(
                child, char_map, div_stack, current_dharani))
            # Tail text always belongs to the parent, even for skipped elements
            if child.tail:
                results.append((child.tail, current_div, current_dharani))
    finally:
        if is_div:
            div_stack.pop()

    return results


def extract_file(xml_path: Path, char_map: dict[str, str]) -> tuple[str, list[tuple[str, str, bool]], dict]:
    """Extract text and metadata from a single XML file.

    Returns (text_id, [(raw_text, div_type, is_dharani), ...], metadata_dict).
    """
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError:
        logger.warning("XML parse error: %s", xml_path)
        return None, [], {}

    root = tree.getroot()
    text_id = root.get(f'{XML}id', '')

    # Extract metadata from teiHeader
    meta = {}
    header = root.find(f'{TEI}teiHeader')
    if header is not None:
        # Title
        for title in header.iter(f'{TEI}title'):
            lang = title.get(f'{XML}lang', '')
            if lang == 'zh-Hant' and title.get('level') == 'm':
                meta['title'] = title.text or ''
                break

        # Author
        author_elem = header.find(f'.//{TEI}author')
        if author_elem is not None:
            meta['author'] = author_elem.text or ''

        # Extent
        extent_elem = header.find(f'.//{TEI}extent')
        if extent_elem is not None:
            extent_text = extent_elem.text or ''
            m = re.search(r'(\d+)', extent_text)
            meta['extent_juan'] = int(m.group(1)) if m else 1

    # Extract docNumber cross-references
    docnumber_refs = []
    body = root.find(f'.//{TEI}body')
    if body is not None:
        for dn in body.iter(f'{CB}docNumber'):
            dn_text = dn.text or ''
            # Parse "No. 250 [Nos. 251-255, 257]"
            # Extract all numbers after "Nos." or within brackets
            bracket_match = re.search(r'\[.*?\]', dn_text)
            if bracket_match:
                bracket_content = bracket_match.group()
                # Find all number references, handling ranges like "251-255"
                for part in re.findall(r'(\d+)(?:\s*-\s*(\d+))?', bracket_content):
                    start = int(part[0])
                    if part[1]:
                        end = int(part[1])
                        for n in range(start, end + 1):
                            docnumber_refs.append(str(n))
                    else:
                        docnumber_refs.append(part[0])
            # Also extract the main doc number
            main_match = re.match(r'No\.\s*(\d+)', dn_text)
            if main_match:
                meta['main_docnumber'] = main_match.group(1)

    meta['docnumber_refs'] = docnumber_refs

    # Check for dharani
    has_dharani = False
    if body is not None:
        for p in body.iter(f'{TEI}p'):
            if p.get(f'{CB}type') == 'dharani':
                has_dharani = True
                break
    meta['has_dharani'] = has_dharani

    # Track div types
    div_types = set()
    if body is not None:
        for div in body.iter(f'{CB}div'):
            dt = div.get('type', '')
            if dt:
                div_types.add(dt)
    meta['div_types'] = list(div_types)

    # Extract body text
    text_parts = []
    if body is not None:
        text_parts = _extract_text_recursive(body, char_map, [])

    return text_id, text_parts, meta


def _group_files_by_text(xml_dir: Path) -> dict[str, list[Path]]:
    """Group XML files by text ID, sorted by fascicle number."""
    groups = defaultdict(list)
    pattern = re.compile(r'(T\d+n\d+[A-Za-z]?)_(\d+)\.xml$')

    for xml_path in sorted(xml_dir.rglob('*.xml')):
        m = pattern.search(xml_path.name)
        if m:
            text_id = m.group(1)
            fascicle = int(m.group(2))
            groups[text_id].append((fascicle, xml_path))

    # Sort each group by fascicle number
    for text_id in groups:
        groups[text_id].sort(key=lambda x: x[0])
        groups[text_id] = [path for _, path in groups[text_id]]

    return dict(groups)


def _process_text_group(args: tuple) -> ExtractedText | None:
    """Process a group of files for one text (for multiprocessing)."""
    text_id, file_paths, char_map = args
    all_parts = []
    meta = {}

    for fpath in file_paths:
        _, parts, file_meta = extract_file(fpath, char_map)
        all_parts.extend(parts)
        if not meta:
            meta = file_meta

    # Build segments by div type and normalize, tracking dharani ranges
    segments = []
    current_div = None
    current_raw = []
    current_dharani_flags = []  # parallel list: is_dharani per raw_text chunk
    offset = 0
    dharani_ranges = []

    def _flush_segment(raw_chunks, dharani_flags, div_type, seg_offset):
        """Normalize a segment and record dharani char ranges."""
        # Normalize each chunk individually to track dharani boundaries
        chunk_texts = []
        for raw, is_dh in zip(raw_chunks, dharani_flags):
            normalized = normalize_text(raw)
            if normalized:
                chunk_texts.append((normalized, is_dh))

        if not chunk_texts:
            return None, seg_offset

        joined = ''.join(ct for ct, _ in chunk_texts)
        if not joined:
            return None, seg_offset

        # Build dharani ranges within this segment
        pos = seg_offset
        for chunk_text, is_dh in chunk_texts:
            if is_dh and chunk_text:
                dharani_ranges.append((pos, pos + len(chunk_text)))
            pos += len(chunk_text)

        seg = DivSegment(
            div_type=div_type,
            text=joined,
            start=seg_offset,
            end=seg_offset + len(joined),
        )
        return seg, seg_offset + len(joined)

    for raw_text, div_type, is_dharani in all_parts:
        if div_type != current_div:
            if current_raw and current_div is not None:
                seg, offset = _flush_segment(
                    current_raw, current_dharani_flags, current_div, offset)
                if seg:
                    segments.append(seg)
            current_div = div_type
            current_raw = [raw_text]
            current_dharani_flags = [is_dharani]
        else:
            current_raw.append(raw_text)
            current_dharani_flags.append(is_dharani)

    # Flush last segment
    if current_raw and current_div is not None:
        seg, offset = _flush_segment(
            current_raw, current_dharani_flags, current_div, offset)
        if seg:
            segments.append(seg)

    full_text = ''.join(seg.text for seg in segments)

    if len(full_text) < config.MIN_TEXT_LENGTH:
        return None

    # Merge adjacent dharani ranges
    merged_dharani = []
    for start, end in dharani_ranges:
        if merged_dharani and start <= merged_dharani[-1][1]:
            merged_dharani[-1] = (merged_dharani[-1][0], max(merged_dharani[-1][1], end))
        else:
            merged_dharani.append((start, end))

    metadata = TextMetadata(
        text_id=text_id,
        title=meta.get('title', ''),
        author=meta.get('author', ''),
        extent_juan=meta.get('extent_juan', 1),
        char_count=len(full_text),
        file_count=len(file_paths),
        docnumber_refs=meta.get('docnumber_refs', []),
        div_types=meta.get('div_types', []),
        has_dharani=meta.get('has_dharani', False),
    )

    return ExtractedText(
        text_id=text_id,
        full_text=full_text,
        segments=segments,
        metadata=metadata,
        dharani_ranges=merged_dharani,
    )


def extract_all(xml_dir: Path = None, num_workers: int = None) -> list[ExtractedText]:
    """Run Stage 1: extract all texts from the XML corpus.

    Returns list of ExtractedText objects.
    """
    if xml_dir is None:
        xml_dir = config.XML_DIR
    num_workers = config.resolve_worker_count(num_workers)

    logger.info("Scanning XML files in %s", xml_dir)
    file_groups = _group_files_by_text(xml_dir)
    logger.info("Found %d texts across XML files", len(file_groups))

    # Collect all XML files for charDecl scanning
    all_files = []
    for paths in file_groups.values():
        all_files.extend(paths)

    logger.info("Building global character map from %d files...", len(all_files))
    char_map = build_char_map(all_files)

    # Process texts in parallel
    args_list = [
        (text_id, paths, char_map)
        for text_id, paths in file_groups.items()
    ]

    results = []
    logger.info("Extracting %d texts with %d workers...", len(args_list), num_workers)

    if num_workers <= 1:
        for args in tqdm(args_list, desc="Extracting"):
            result = _process_text_group(args)
            if result is not None:
                results.append(result)
    else:
        with Pool(num_workers, maxtasksperchild=config.MAXTASKSPERCHILD) as pool:
            for result in tqdm(
                pool.imap_unordered(_process_text_group, args_list),
                total=len(args_list),
                desc="Extracting",
            ):
                if result is not None:
                    results.append(result)

    logger.info("Extracted %d texts (skipped %d short texts)",
                len(results), len(args_list) - len(results))
    return results


def save_results(texts: list[ExtractedText], data_dir: Path = None):
    """Save extracted texts and metadata to disk."""
    if data_dir is None:
        data_dir = config.DATA_DIR
    texts_dir = data_dir / "texts"
    texts_dir.mkdir(parents=True, exist_ok=True)

    metadata_list = []
    for text in texts:
        # Save plain text
        text_path = texts_dir / f"{text.text_id}.txt"
        text_path.write_text(text.full_text, encoding='utf-8')

        # Collect metadata
        m = text.metadata
        metadata_list.append({
            'text_id': m.text_id,
            'title': m.title,
            'author': m.author,
            'extent_juan': m.extent_juan,
            'char_count': m.char_count,
            'file_count': m.file_count,
            'docnumber_refs': m.docnumber_refs,
            'div_types': m.div_types,
            'has_dharani': m.has_dharani,
        })

    # Save metadata index
    metadata_path = data_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)

    logger.info("Saved %d texts to %s and metadata to %s",
                len(texts), texts_dir, metadata_path)
