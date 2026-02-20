# Code Review: `digest_detector/extract.py`

**Reviewer:** Claude
**Date:** 2026-02-19
**File:** `/Users/danzigmond/taisho-canon/digest_detector/extract.py` (513 lines)

---

## Summary

This module handles Stage 1 of the pipeline: parsing CBETA TEI P5b XML files, resolving special characters via `charDecl`, extracting body text (preferring `<lem>` readings), normalizing to pure CJK, and tracking `<cb:div>` boundaries and dharani ranges. Overall it is well-structured, clearly documented, and well-tested. I found no critical bugs, no security issues, and no dead code. The issues below are mostly P2/P3.

---

## Issues

### P2-1: `build_char_map` silently prefers the first file's definition for each `char_id` (line 92)

```python
if not char_id or char_id in char_map:
    continue
```

If two XML files define the same `char_id` with *different* resolved values (e.g., one has a `normalized form` and the other has a `unicode` mapping that differs), the first file encountered wins silently. Since `build_char_map` iterates over `xml_files` in the order provided (which comes from `_group_files_by_text` -> `sorted(xml_dir.rglob(...))`), this is at least deterministic. But a discrepancy between definitions would be silently ignored with no log message.

**Recommendation:** Log at `DEBUG` level when a duplicate `char_id` is skipped, or even better, log at `WARNING` if the resolved value differs from the already-stored one. This would surface potential data quality issues in the CBETA corpus.

**Severity: P2** -- Could mask real discrepancies in character definitions across the corpus.

---

### P2-2: `_extract_text_recursive` appends `<g>` resolved text AND `elem.text` (lines 187-197)

```python
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
```

For a `<g>` element, this first appends the resolved character, then also appends `elem.text` if it exists. In the CBETA corpus, `<g>` elements are typically self-closing (`<g ref="#CB00832"/>`) or contain a fallback rendering like `<g ref="#CB00832">[覆-西+非]</g>`. If the `<g>` element has text content (the fallback rendering), it will be appended *in addition to* the resolved character, leading to duplication or garbage like `覆[覆-西+非]`.

**In practice**, `normalize_text` strips everything except CJK, so bracket notation like `[覆-西+非]` would become `覆西非` -- three spurious characters. However, if the `<g>` fallback text contains bare CJK characters (which is rarer), those would pass through normalization and create duplicated/wrong text.

**Recommendation:** After the `<g>` handler block (lines 187-193), add `return results` or skip the `elem.text` path for `<g>` tags. For example:

```python
if tag == f'{TEI}g':
    ref = elem.get('ref', '')
    if ref.startswith('#'):
        char_id = ref[1:]
        resolved = char_map.get(char_id, '')
        if resolved:
            results.append((resolved, current_div, current_dharani))
    return results  # <g> is a leaf element; skip elem.text fallback
```

**Severity: P2** -- Could introduce spurious CJK characters into the extracted text. The impact depends on how many `<g>` elements have text content in the CBETA corpus (likely low, but nonzero).

---

### P2-3: Tail text of skipped elements and `<app>` children still extracted (lines 200-205)

```python
# Recurse into children
for child in elem:
    results.extend(_extract_text_recursive(
        child, char_map, div_stack, current_dharani))
    # Tail text always belongs to the parent, even for skipped elements
    if child.tail:
        results.append((child.tail, current_div, current_dharani))
```

The comment on line 203 says "Tail text always belongs to the parent, even for skipped elements" and this is correct XML semantics. However, there is a subtlety: when a child is in `SKIP_TAGS`, `_extract_text_recursive` returns `[]` (line 163), which is fine -- but the tail is still collected at line 205. This is *intentional and correct*.

But for `<app>` (line 166-171), the function handles `<app>` by only processing `<lem>` children. After `<app>` returns, its tail is handled at line 204-205 in the *parent's* loop. However, `<rdg>` children inside `<app>` -- their tails are NOT collected because the `<app>` handler (lines 167-171) only recurses into `<lem>`. Consider:

```xml
<app><lem>正</lem><rdg resp="CBETA">政</rdg></app>後文
```

Here `<rdg>` has no tail, and `<app>` has tail "後文". But if this were:

```xml
<app><lem>正</lem>中間文<rdg resp="CBETA">政</rdg></app>
```

The text "中間文" is `<lem>.tail` -- tail text of the `<lem>` element. Since the `<app>` handler recurses into `<lem>` via `_extract_text_recursive`, and `<lem>` is in `INCLUDE_TAGS`, `<lem>` itself is processed but its tail is NOT collected by the `<app>` handler. The tail would only be collected if the *parent* of `<app>` does the tail collection. But wait -- the `<app>` handler returns early (line 171), so control returns to the parent's loop which collects `<app>.tail`, not `<lem>.tail`.

**In practice**, CBETA `<app>` elements don't typically have text between `<lem>` and `<rdg>`, so `<lem>.tail` is almost always empty or whitespace. But if it ever isn't, that text would be lost.

**Recommendation:** In the `<app>` handler, after recursing into `<lem>`, also collect `lem_child.tail`:

```python
if tag == f'{TEI}app':
    for child in elem:
        if child.tag == f'{TEI}lem':
            results.extend(_extract_text_recursive(
                child, char_map, div_stack, in_dharani))
            if child.tail:
                results.append((child.tail, current_div, in_dharani))
    return results
```

**Severity: P2** -- Potential text loss in edge cases. Low probability with real CBETA data but worth guarding against.

---

### P3-1: `_flush_segment` closes over mutable `dharani_ranges` from outer scope (line 363)

```python
dharani_ranges = []
# ...
def _flush_segment(raw_chunks, dharani_flags, div_type, seg_offset):
    # ...
    dharani_ranges.append((pos, pos + len(chunk_text)))
```

This nested function mutates the outer `dharani_ranges` list via closure. While this works correctly, it is a non-obvious side effect that could confuse future readers. The function signature suggests it is a pure helper (takes inputs, returns outputs), but it also silently mutates external state.

**Recommendation:** Either pass `dharani_ranges` as a parameter, or have `_flush_segment` return the ranges and let the caller accumulate them.

**Severity: P3** -- Readability/maintainability concern; no correctness issue.

---

### P3-2: `extract_file` returns `None` as first element on parse error (line 222)

```python
except etree.XMLSyntaxError:
    logger.warning("XML parse error: %s", xml_path)
    return None, [], {}
```

The caller `_process_text_group` (line 330) does:

```python
_, parts, file_meta = extract_file(fpath, char_map)
```

It never checks whether `text_id` is `None`, so after a parse error, processing continues with `text_id = None` for that file. Since `all_parts` would be empty (`parts = []`), this is mostly harmless. But if `file_meta` were non-empty on some error path, it could pollute the metadata.

More importantly, the return type annotation says `tuple[str, ...]` but it returns `None` for the first element. The type hint is technically violated.

**Recommendation:** Return `('', [], {})` instead of `(None, [], {})` for consistency with the return type, or check for `None` in the caller.

**Severity: P3** -- Type inconsistency; no runtime bug in current usage.

---

### P3-3: Metadata only taken from the first fascicle file (lines 332-333)

```python
if not meta:
    meta = file_meta
```

For multi-fascicle texts (e.g., T223 with 27 fascicles), only the first file's metadata is used. This is fine for `title` and `author`, which are consistent across fascicles. However, `docnumber_refs` from fascicle 1 might differ from later fascicles (though in CBETA this is unlikely -- the `<cb:docNumber>` is typically in the first fascicle only).

More subtly, `div_types` and `has_dharani` from later fascicles are lost. If fascicle 1 has no dharani but fascicle 5 does, `has_dharani` would be `False` for the whole text. And if fascicle 1 has only `jing` divs but fascicle 10 introduces a `xu` preface, that would be missed.

**Recommendation:** Merge metadata across fascicles -- at minimum, union `div_types` and OR `has_dharani`:

```python
if not meta:
    meta = file_meta
else:
    meta['div_types'] = list(set(meta.get('div_types', []))
                             | set(file_meta.get('div_types', [])))
    meta['has_dharani'] = meta.get('has_dharani', False) or file_meta.get('has_dharani', False)
    meta['docnumber_refs'] = list(set(meta.get('docnumber_refs', []))
                                  | set(file_meta.get('docnumber_refs', [])))
```

**Severity: P3** -- Could produce incomplete metadata for multi-fascicle texts with varying structures.

---

### P3-4: `_group_files_by_text` regex doesn't handle all CBETA naming conventions (line 306)

```python
pattern = re.compile(r'(T\d+n\d+[A-Za-z]?)_(\d+)\.xml$')
```

The pattern allows an optional single letter suffix after the Taisho number (e.g., `T08n0223a`). However, some CBETA texts use multi-letter suffixes or other patterns. If such files exist in the corpus, they would be silently skipped.

**Severity: P3** -- Only relevant if the corpus contains non-standard naming. The current T-collection files appear to follow this pattern consistently.

---

### P3-5: `char_map` is passed in full to every worker process (line 451-452)

```python
args_list = [
    (text_id, paths, char_map)
    for text_id, paths in file_groups.items()
]
```

When using multiprocessing, each item in `args_list` carries a copy of `char_map` (which is serialized via pickle for each worker task). With ~8,982 text groups and a char_map that could have thousands of entries, this means the same char_map is pickled ~8,982 times. This is wasteful.

**Recommendation:** Use a `Pool` initializer to pass `char_map` once as shared state (the same pattern used in other stages of this pipeline, per the MEMORY.md notes). This would change `_process_text_group` to read `char_map` from a module-level global set by the initializer.

**Severity: P3** -- Performance concern. With `imap_unordered`, the serialization is amortized but still adds overhead. The char_map is likely small enough (~2000-5000 entries) that the total overhead is modest.

---

### P4-1: `INCLUDE_TAGS` is defined but never checked (lines 48-59)

```python
INCLUDE_TAGS = frozenset([
    f'{TEI}p',
    f'{CB}div',
    f'{TEI}head',
    ...
])
```

`INCLUDE_TAGS` is defined at module level but never referenced anywhere in the code. The extraction logic relies on `SKIP_TAGS` (elements to exclude) and specific tag checks (`<app>`, `<g>`, `<cb:div>`), but never consults `INCLUDE_TAGS`. It appears to be documentary dead code -- it communicates intent but has no functional effect.

**Recommendation:** Either remove it (since it isn't used) or add a check that rejects unknown tags not in either `SKIP_TAGS` or `INCLUDE_TAGS`. If kept for documentation, add a comment like `# Documentary: tags whose content we include (no runtime check)`.

**Severity: P4** -- Dead code / style.

---

### P4-2: `json` import unused in this module (line 8)

```python
import json
```

The `json` module is imported but only used in `save_results`. However, `save_results` does use it (line 509: `json.dump`), so this is actually fine. (Confirmed: it IS used.)

**Severity: N/A** -- False alarm; import is used.

---

### P4-3: Inconsistent empty-dict check semantics (line 332)

```python
if not meta:
    meta = file_meta
```

`not meta` is truthy for both `{}` (empty dict) and `None`. Since `extract_file` returns `{}` on error (line 222), the first non-error file's metadata is used. This works correctly but `if meta is None or not meta:` would be more explicit about the intent (though functionally identical). Extremely minor.

**Severity: P4** -- Nit.

---

### P4-4: `text_id` extracted from root `xml:id` attribute, could be empty (line 225)

```python
text_id = root.get(f'{XML}id', '')
```

If the root element lacks an `xml:id` attribute, `text_id` becomes `''`. The caller `_process_text_group` already has the `text_id` from the filename (line 325: `text_id, file_paths, char_map = args`) and ignores the return value `_` from `extract_file`. So this empty string is harmless. But it means `extract_file`'s return value for `text_id` can silently disagree with the filename-derived ID, and nobody would notice.

**Severity: P4** -- Unused return value makes a minor inconsistency invisible.

---

## Things Done Well

1. **Clear module docstring and function docstrings** -- Every function explains what it does and what it returns.

2. **Correct namespace handling** -- Both `NS` dict (for XPath with `find`/`iter`) and expanded `{uri}tag` constants (for direct tag comparison) are maintained correctly.

3. **Robust XML error handling** -- `XMLSyntaxError` is caught in both `build_char_map` and `extract_file`, with appropriate logging and graceful degradation.

4. **Character resolution priority chain** -- The three-level fallback (normalized form -> normal_unicode -> unicode) correctly implements CBETA charDecl semantics.

5. **Division stack with try/finally** -- The `div_stack` is always popped in the `finally` block (line 206-208), preventing stack corruption on unexpected exceptions.

6. **Dharani tracking** -- The dual-level tracking (per-chunk flags in `_extract_text_recursive`, merged ranges in `_process_text_group`) cleanly separates dharani detection from text extraction.

7. **Good test coverage** -- Tests cover real CBETA files (T250, T251, T223) with concrete assertions about titles, authors, docnumber refs, div types, dharani presence, and text content.

8. **Deterministic file ordering** -- `sorted(xml_dir.rglob('*.xml'))` and fascicle-number sorting ensure reproducible output.

---

## Overall Assessment

**Grade: A-**

This is solid, well-organized extraction code. The XML parsing logic correctly handles the CBETA TEI P5b format's key features (charDecl, app/lem/rdg, cb:div, dharani markup). The main risks are:

- **P2-2** (`<g>` element text leakage) is the most likely to cause actual data quality issues, though the impact is probably small given CBETA's typical `<g>` usage patterns.
- **P2-3** (`<lem>.tail` loss in `<app>`) is theoretically possible but unlikely with real data.
- **P3-3** (metadata from first fascicle only) could produce incomplete metadata for multi-fascicle texts.

None of these are show-stoppers for the current pipeline, but P2-2 is worth investigating with a quick corpus scan to see how many `<g>` elements have non-empty text content.
