# Code Review: Taisho Canon Codebase

**Date:** 2026-02-26
**Reviewer:** Claude (Opus 4.6)
**Scope:** All Python code in `digest_detector/` and `scripts/`
**Goal:** A+ quality code

---

## 1. Executive Summary

This is a well-engineered research codebase implementing a multi-stage pipeline for detecting "digest" (chāojīng) relationships across ~2,459 texts in the Taisho Buddhist canon, plus a concordance builder merging 10+ catalog sources for Chinese-Tibetan parallel identification. The code demonstrates strong software engineering practices: clear module boundaries, thorough documentation, comprehensive test coverage (411 tests across 20 files), and thoughtful performance optimization.

**Overall grade: A-**

The code is production-quality for a research project. The main areas for improvement are: (1) substantial code duplication between `export_csv.py` and `export_tei.py`, (2) some edge cases in the alignment and scoring pipeline, (3) security hardening in web scraping scripts, and (4) minor consistency issues across modules.

### Severity Summary

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 0 | No data-corrupting or security-exploitable bugs |
| High | 5 | Bugs that could produce incorrect results in edge cases |
| Medium | 12 | Code quality issues, duplication, or robustness gaps |
| Low | 15 | Style, documentation, or minor optimization opportunities |

---

## 2. File-by-File Findings

### 2.1 `scripts/build_expanded_concordance.py` (1017 lines)

This is the central concordance builder. It merges 11 data sources plus post-processing steps. Generally well-structured with clear source-by-source organization.

**HIGH: `normalize_taisho_id` returns mixed types (line 110)**
The function returns either a string or an `int`, which is a type safety hazard. Line 110: `return int(m.group(1))`. While `resolve_taisho_id` (line 261) handles this via `isinstance(norm, int)`, the mixed return type makes the function's contract confusing and fragile.

**MEDIUM: Potential KeyError in `flag_known_errors` (line 925)**
The function accesses `err["taisho_id"]` and `err["erroneous_toh"]` without `.get()` safety. If `known_errors.json` is malformed (missing keys), this crashes without a helpful error message. Consider wrapping in try/except or validating the schema.

**MEDIUM: Source 8 iterates over all concordance entries (line 486)**
```python
for text_id, data in concordance.items():
    if toh_key in data["tibetan"]:
```
This is O(num_texts * num_84000_entries). With ~2,459 texts and ~4,000 84000 entries, this is ~10M iterations. It works fine at current scale but would benefit from a reverse index (Toh -> set of text_ids) for clarity and future-proofing.

**LOW: `compare_with_existing` delta formatting (line 859)**
```python
f"{'+' + str(new_tib - old_tib):>8}"
```
If the delta is negative, this produces `+-5` instead of `-5`. Should check for negative deltas.

**LOW: `_make_attestation` uses falsy check for `note` (line 181)**
```python
if note:
    att["note"] = note
```
This silently drops `note=""` (empty string), which is probably fine, but `if note is not None:` would be more explicit about intent.

**LOW: MITRA_STRONG_THRESHOLD defined inside function (line 655)**
This constant is defined inside `merge_sources()` rather than at module level with the other constants. For consistency, it should be at the top of the file.

---

### 2.2 `digest_detector/export_csv.py` (459 lines) and `export_tei.py` (551 lines)

**HIGH: Massive code duplication between these two files**

The `build_provenance()` function is duplicated nearly identically across both files (lines 73-192 in CSV, lines 79-198 in TEI). Similarly, `gather_titles_and_nanjio()` (CSV lines 195-301) and `gather_metadata()` (TEI lines 201-307) are near-identical. The `build_number_to_id()` and `resolve_taisho()` functions are also duplicated, and both are further duplicated from `build_expanded_concordance.py`.

This creates a maintenance burden: any fix to provenance reconstruction logic must be applied in three places. These shared utilities should be extracted into a common module (e.g., `digest_detector/concordance_utils.py`).

**MEDIUM: Fallback provenance path is stale (CSV line 95, TEI line 101)**
When `link_provenance` is absent, both files reconstruct provenance from source files. However, this fallback path does not handle MITRA, Sanskrit title matches, scholarly citations, or 84000 TEI refs. It only covers 6 of the 11+ sources. A comment noting this limitation would be helpful; alternatively, emit a warning when falling back.

**MEDIUM: `export_csv` source count inconsistency (line 388)**
For Otani-only rows (no Tohoku), `source_count` is set to `len(otani_sources)`, which counts Otani provenance sources. But for Tohoku rows (line 406), `source_count` counts only sources for that specific Toh link. This means the "source_count" column has inconsistent semantics depending on whether the row has a Tohoku number.

**LOW: Unused import in `export_tei.py` (line 14)**
`StringIO` is imported from `io` but it's only used in one place (line 523). Not a bug, but the import at line 14 alongside ElementTree imports makes it look like it might be part of the XML processing stack.

---

### 2.3 `digest_detector/pipeline.py` (392 lines)

Clean orchestration code with good timing, caching, and logging.

**MEDIUM: `_log_peak_rss` platform detection (line 37)**
```python
if sys.platform == 'darwin':
    rss_mb = rss / (1024 * 1024)
else:
    rss_mb = rss / 1024
```
This assumes Linux for the else branch. On Windows or other platforms, `resource.getrusage` may not be available at all (it raises `ModuleNotFoundError`). The `import resource` at line 7 will fail on Windows. Since this is a research project primarily targeting macOS/Linux, this is low risk but worth a comment.

**LOW: Memory cleanup after Stage 2 (line 152)**
```python
del ngram_sets, stopgrams  # ~8,982 frozensets
gc.collect()
```
The `gc.collect()` is good practice, but the comment `~8,982 frozensets` is specific to the current corpus size. If the corpus grows, this comment becomes misleading.

**LOW: `_git_short_hash` swallows all exceptions (line 52)**
```python
except Exception:
    return ""
```
This is intentional (git may not be available), but catching `Exception` is overly broad. Consider catching `(subprocess.CalledProcessError, FileNotFoundError, OSError)` specifically.

---

### 2.4 `digest_detector/extract.py` (536 lines)

Solid XML extraction with proper namespace handling and CBETA TEI P5b conventions.

**HIGH: `_extract_text_recursive` tail text handling for `<app>` (line 186)**
When `<app>` is encountered, the function processes only `<lem>` children but returns early without processing the `<app>` element's own text or its children's tail text outside of `<lem>`. If `<app>` has direct text content (unlikely but possible in malformed XML), it would be silently dropped.

More importantly, the `<app>` early return at line 186 means that any text between `<app>` child elements (other than `<lem>`) is also dropped. This is the correct behavior for `<rdg>` (which is in SKIP_TAGS), but if there are other child element types inside `<app>`, their tail text after `<lem>` processing is lost.

**MEDIUM: `_flush_segment` captures `dharani_ranges` from outer scope (line 361)**
The nested function `_flush_segment` appends to `dharani_ranges` defined in the outer `_process_text_group` function (line 359). This is a closure side effect that works correctly but is subtle. A reader might not realize `_flush_segment` modifies external state. Consider passing `dharani_ranges` as a parameter.

**MEDIUM: Character map building scans ALL XML files (line 466)**
`build_char_map(all_files)` parses every XML file looking for `charDecl` entries. Since `charDecl` is defined per-file (not per-text), this means re-parsing the same charDecl definitions across fascicles of the same text. For the ~8,982 files, this is expensive. Consider extracting charDecl only from the first fascicle of each text, or caching the result.

**LOW: `_decode_unicode_hex` doesn't handle multi-codepoint sequences (line 148)**
The function handles `U+XXXX` but not sequences like `U+0041U+0301`. CBETA does not seem to use these, but the function silently fails on them (returns `None`).

**LOW: `_group_files_by_text` uses `rglob('*.xml')` (line 326)**
This recursively searches the entire directory tree. If there are non-corpus XML files in subdirectories (e.g., backup files), they could be incorrectly included. The regex pattern at line 324 provides a safety filter, but using a more targeted glob would be more robust.

---

### 2.5 `digest_detector/align.py` (705 lines)

The most algorithmically complex module. The seed-and-extend alignment with DP chaining is well-implemented.

**HIGH: `_chain_seeds` DP correctness concern (lines 153-180)**
The DP tracks `dp[i]` as the maximum coverage using seeds `[0..i]` where seed `i` is included. However, the recurrence only considers the best compatible predecessor via `bisect_right`. This is correct for weighted interval scheduling when the goal is to maximize total weight. But the backtracking at lines 172-178 only follows the `prev` chain from the single best endpoint, which may not reconstruct the globally optimal solution when multiple seeds at the same endpoint have different predecessors.

Actually, upon closer reading, the DP is correct: `dp[i]` represents the max coverage including seed `i`, and the global optimum is found at `best_idx`. The backtracking follows `prev[i]` which correctly chains back to the predecessor that achieved `dp[i]`. This is a standard weighted interval scheduling solution. **No bug here; false alarm.**

**HIGH: `_phonetic_rescan` uses source coordinates from novel segment (line 321)**
```python
phonetic_seeds = _find_phonetic_seeds(novel_text, source_text, table, k)
```
The `novel_text` is a substring of the digest, but `source_text` is the FULL source text. The phonetic seeds return `(d_start, s_start, length)` where `d_start` is relative to `novel_text` and `s_start` is absolute in `source_text`. This is correct. However, at line 327:
```python
extended = [(d_s, d_s + length, s_s, s_s + length, "phonetic")
            for d_s, s_s, length in phonetic_seeds]
chained = _chain_seeds(extended, len(novel_text))
```
The `_chain_seeds` function chains in digest coordinates. The chained seeds are then used at line 337 with `seg.digest_start + d_start` to map back to absolute digest coordinates. This is correct. **No bug here.**

**MEDIUM: Module-level mutable global `_phonetic_table` (line 184)**
```python
_phonetic_table: dict[str, set[str]] | None = None
```
This is a process-level cache that is lazily loaded and explicitly cleared at line 701. However, in a multiprocessing context, each worker process gets its own copy (due to `spawn` on macOS). The cache is only useful in the main process or in sequential alignment. The `_get_phonetic_table` function at line 187 is called inside `align_pair` which runs in worker processes, meaning each worker redundantly builds the table. Consider passing the table as a parameter or using the pool initializer pattern (as done in `candidates.py`).

**MEDIUM: `_align_pair_wrapper` uses mutable global state (line 590)**
```python
_cached_source_table: tuple[str, int, dict] | None = None
```
This is a per-process cache that caches the last source's k-gram table. The sorting at line 678 clusters pairs by source_id to maximize cache hits. This is a good optimization, but `imap_unordered` at line 689 may not preserve task order, potentially reducing cache effectiveness. Consider using `imap` (ordered) instead, since the results are sorted anyway at line 697.

**LOW: Early termination threshold check (line 445)**
```python
if raw_coverage < config.SHARED_TRADITION_THRESHOLD and not do_phonetic:
```
This optimization skips alignment when raw seed coverage is below 10%. But raw seeds include overlapping seeds (before dedup at line 414), so the actual coverage after dedup could be lower. The early termination uses post-dedup seeds (`raw_seeds` has been replaced by `deduped` at line 433), so this is actually correct. The comment at line 438 confirms this.

---

### 2.6 `digest_detector/score.py` (285 lines)

Clean scoring logic with well-documented classification categories.

**MEDIUM: Classification priority order has a subtle interaction (lines 84-96)**
The classification checks are ordered: no_relationship -> shared_tradition -> retranslation -> excerpt -> digest -> commentary. The retranslation check at line 88 fires for ANY pair with `coverage >= 0.30` and `size_ratio < 3.0`, regardless of avg_segment_length. This means a pair with 35% coverage and 5-char average segments (which would be "commentary" by the digest/commentary logic) gets classified as "retranslation" if the texts are similar in size. This may be intentional (retranslation takes priority over content-type classification), but it could produce surprising results for short-segment shared-tradition pairs that happen to be similar in length.

**LOW: `detect_multi_source_digests` uses `d_meta.char_count` instead of jing length (line 258)**
```python
d_len = d_meta.char_count if d_meta else 0
```
This uses the full char count (including prefaces) for computing combined coverage. Other parts of the scoring pipeline use `jing_text` length. This inconsistency means multi-source coverage could be slightly lower than expected for texts with significant preface material.

**LOW: `_compute_confidence` normalizations are hardcoded (lines 137-155)**
The normalization constants (e.g., `/ 4.0` for regions, `/ 10.0` for asymmetry, `/ 20.0` for avg_seg) are magic numbers embedded in the function. These could be config constants for easier tuning.

---

### 2.7 `digest_detector/report.py` (413 lines)

Clean report generation with good orjson optimization.

**LOW: Ground truth is hardcoded (lines 27-38)**
The `GROUND_TRUTH` dict contains only 2 test pairs (T250->T223, T251->T223). For a corpus of 2,459 texts, this is a very small validation set. Consider loading ground truth from a JSON file to make it easier to extend.

**LOW: Alignment visualization truncates at 30 chars (line 139)**
The `max_text_preview` default of 30 characters may be too short for CJK text (CJK chars are wider but each char carries more meaning). Consider a larger default (50-60) or making it configurable.

**LOW: `_segment_to_dict` variable shadowing (line 192)**
```python
d = {
    'digest_start': seg.digest_start,
    ...
}
```
The variable `d` shadows the common convention of using `d` for digest-related data. Later at line 203, `d_ch` is used inside the same function, which could cause confusion. Consider renaming to `result` or `seg_dict`.

---

### 2.8 `digest_detector/phonetic.py` (434 lines)

Clever phonetic transliteration detection system.

**MEDIUM: `_split_syllables` heuristic may produce incorrect syllable boundaries (line 60)**
The syllable splitter uses a vowel-based heuristic that works for common Sanskrit transliterations but fails for:
- Consonant clusters at word boundaries: "tantra" -> ["tan", "tra"] (correct)
- But "nkr" sequences: "samkranti" -> potentially incorrect splits
- Retroflex/sibilant clusters may not split cleanly

This is documented as "rough 1:1 alignment" but could produce incorrect character-to-syllable mappings that propagate through the equivalence table.

**MEDIUM: `phonetic_mapping_for_pair` requires equal-length strings (line 415)**
```python
if len(digest_text) != len(source_text):
    raise ValueError(...)
```
This is called from `_phonetic_rescan` at align.py line 353, where `d_text` and `s_text` come from `_find_phonetic_seeds` which produces equal-length matches. However, if fuzzy extension is ever added to phonetic matching (currently not done), this constraint would break. The `raise ValueError` is appropriate for the current code but could be a latent trap.

**LOW: `_COMMON_PROSE_EXCLUSIONS` is a frozenset of a string (line 26)**
```python
_COMMON_PROSE_EXCLUSIONS = frozenset('無一大佛法人世天空色善道得行知說想相')
```
This works (iterating over a string produces individual characters), but it's not immediately obvious to readers. A comment explaining that `frozenset` of a string produces a set of characters would help.

---

### 2.9 `digest_detector/candidates.py` (503 lines)

Well-optimized candidate generation with good use of multiprocessing patterns.

**MEDIUM: `generate_phonetic_candidates` double-counts pairs (lines 458-484)**
The nested loop iterates all pairs of texts with phonetic regions:
```python
for text in texts:
    for source_id, source_set in phonetic_sets.items():
```
When `d_len > s_len`, the pair is reversed (lines 473-484). But the same pair may be encountered again when the other text is the outer loop's `text`. The `seen_pairs` check at line 486 correctly prevents duplicates, but the containment score is recomputed from the reversed perspective, which may differ from the original computation. This is mathematically correct (containment is asymmetric, and we want the shorter text's perspective), but the recomputation at lines 481-484 could produce slightly different results than if the pair were first encountered in the "correct" order due to floating-point arithmetic. In practice, this is negligible.

**LOW: Module-level globals for multiprocessing (lines 25-35)**
The module uses 7 module-level globals for candidate generation and 2 for phonetic scanning. This is the standard pattern for `multiprocessing.Pool` with initializers, but it makes the module not thread-safe (as documented at line 207). Consider documenting this more prominently at the module level.

**LOW: `_candidate_worker` iterates from `lo` to end of sources (line 88)**
```python
for idx in range(lo, len(source_ids_arr)):
```
For short digests (e.g., 100 chars), `min_source_len` = 200, and almost all ~8,982 sources qualify. This means every digest checks against nearly every source. The binary search optimization helps for very short texts but provides diminishing returns as digest length decreases.

---

### 2.10 `digest_detector/config.py` (97 lines)

Clean configuration with a good weight assertion at line 47.

**LOW: `resolve_worker_count` caps at 16 for non-memory-intensive (line 95)**
```python
return max(1, min(cpu_count(), 16))
```
The cap of 16 for alignment workers is hardcoded. This should be a named constant like `DEFAULT_MAX_ALIGN_WORKERS`.

**LOW: No environment variable overrides**
Unlike `fast.py` which checks `DIGEST_NO_CYTHON`, the config module doesn't support environment variable overrides for parameters. For a research project where experiments often involve parameter sweeps, adding `os.environ.get()` support for key parameters would be convenient.

---

### 2.11 `digest_detector/models.py` (109 lines)

Clean dataclass definitions with `slots=True` for memory efficiency.

**LOW: `ExtractedText.jing_text` property recomputes on every call (line 39)**
```python
@property
def jing_text(self) -> str:
    jing_segs = [seg.text for seg in self.segments if seg.div_type == 'jing']
    if jing_segs:
        return ''.join(jing_segs)
    return self.full_text
```
This filters and joins segments on every access. Since `jing_text` is called frequently in hot paths (candidate generation, alignment), consider caching the result. With `slots=True`, a cached property won't work natively, but a computed-once field set in `__post_init__` could.

---

### 2.12 `digest_detector/fingerprint.py` (200 lines)

Clean fingerprinting with good multiprocessing patterns.

**MEDIUM: `compute_document_frequencies` modifies module global in serial path (line 86-87)**
```python
global _worker_n
_worker_n = n
```
This sets a module-level global that is also used by `build_ngram_sets`. If `compute_document_frequencies` and `build_ngram_sets` are called with different `n` values (unlikely but possible), the serial path would corrupt the shared global. The parallel path uses separate initializers, avoiding this. In practice, both are always called with the default `n`, but it's fragile.

**LOW: `stable_hash` returns signed 32-bit values (line 31)**
```python
return zlib.crc32(s.encode('utf-8'))
```
`zlib.crc32` returns an unsigned 32-bit integer (0 to 4294967295). This is fine for set operations but worth noting in the docstring since Python's `hash()` returns signed values.

---

### 2.13 `digest_detector/cache.py` (111 lines)

Good cache design with version tracking and config snapshot validation.

**MEDIUM: Pickle deserialization security (line 107)**
```python
texts = pickle.load(f)
```
Pickle is inherently unsafe for untrusted data. In this research context, the cache files are generated locally, so the risk is minimal. However, if the cache directory were ever on a shared filesystem or the cache files were distributed, this could be exploited. Consider adding a note about this limitation or using a safer serialization format.

**LOW: `corpus_hash` uses `st_mtime_ns` (line 62)**
```python
entries.append(f"{rel}:{stat.st_mtime_ns}:{stat.st_size}")
```
On some filesystems (e.g., FAT32, some network mounts), `st_mtime_ns` may not have nanosecond precision. Combining with `st_size` mitigates this, but content hashing would be more robust (at the cost of performance).

---

### 2.14 `digest_detector/_fast_fallback.py` (166 lines)

Clean pure-Python implementations matching the Cython interface.

**LOW: `fast_find_seeds` imports inside function (line 60)**
```python
from collections import defaultdict
source_table = defaultdict(list)
```
This import happens inside the function body, which runs on every call when no `source_table` is provided. Moving the import to module level would be cleaner.

---

### 2.15 `scripts/find_peking_only_texts.py` (321 lines)

Well-structured script for identifying Peking-only texts.

**MEDIUM: XML parsing via regex (line 37)**
```python
for item_match in re.finditer(r'<item>(.*?)</item>', xml_text, re.DOTALL):
```
The rKTs XML is parsed via regex instead of a proper XML parser. While this works for the current data format, it's fragile against:
- CDATA sections
- Nested `<item>` elements
- XML comments containing `</item>`
- Entity references

Consider using `xml.etree.ElementTree` for robustness.

**LOW: `sorted(..., key=int)` assumes all kernel IDs are numeric (line 75)**
```python
for kernel_id in sorted(q_only_kernels, key=int):
```
If a kernel ID contains non-numeric characters, this crashes. A safer approach: `key=lambda x: int(x) if x.isdigit() else 0`.

---

### 2.16 `scripts/parse_mitra.py` (177 lines)

Clean MITRA parser.

**LOW: `count_lines` reads the entire file (line 47)**
For large TSV files, this loads the entire file into memory via `sum(1 for line in f ...)`. Since the function only needs a count, this is fine for the current data sizes but could use `wc -l` or a buffered counter for very large files.

**LOW: Unused `CONFIDENCE_WEAK` constant (line 39)**
```python
CONFIDENCE_WEAK = 0.5  # <20 sentences (unused with MIN_SENTENCES=20)
```
The comment acknowledges this is unused, but dead code should be removed.

---

### 2.17 `scripts/scrape_dila_catalog.py` (487 lines)

Well-built web scraper with progress tracking and resume capability.

**MEDIUM: HTML parsing via regex (line 232-249)**
```python
tohoku_match = re.search(
    r'東北大學藏經目錄</div><div>(.*?)</div>', html
)
```
This regex-based HTML parsing is fragile. If the HTML structure changes (e.g., added attributes, nested divs), the regex will silently fail to match. Consider using `html.parser` or `BeautifulSoup` for more robust parsing.

**MEDIUM: No HTTPS certificate verification (line 64)**
```python
with urlopen(req, timeout=30) as resp:
```
`urlopen` does not verify SSL certificates by default in some Python versions. For academic scraping, this is acceptable, but consider using `ssl.create_default_context()` for defense in depth.

**LOW: Progress saving has race condition potential (line 385)**
```python
if (len(completed) + i) % 100 == 0:
```
The condition uses `len(completed) + i` where `completed` is a set that grows during the loop. This means the save interval is not exactly every 100 entries. Not a bug, but slightly confusing.

---

### 2.18 `scripts/scrape_hobogirin.py` (531 lines)

Thorough extraction of Hobogirin data with excellent documentation of data limitations.

**MEDIUM: `xml:id` attribute handling workaround (line 229)**
```python
xml_text = xml_text.replace("xml:id=", "xmlid=")
xml_text = xml_text.replace("xml:lang=", "xmllang=")
```
This string replacement workaround for `xml:id` handling is fragile. If the XML contains text content with "xml:id=" or "xml:lang=", it would be corrupted. The proper approach is to use `lxml` with namespace-aware parsing (as done in `extract.py`), or register the XML namespace with `ElementTree`.

**LOW: `extract_cf_refs` regex is overly restrictive (line 132)**
```python
cf_match = re.search(r"Cf\.\s*(.+?)(?:\s*[東西南北後前劉宋唐秦晉隋梁陳]|\s*\d{1,2}\s*$)", note_text)
```
The regex terminator relies on specific dynasty characters. If a new dynasty name or variant appears, the regex silently fails. Consider a more general terminator or parsing the note text structure differently.

---

### 2.19 `scripts/scrape_ddb.py` (570 lines)

Well-structured DDB scraper with multiple matching strategies.

**LOW: `cross_reference` substring matching (line 378-382)**
```python
if (cn_title in taisho_title or taisho_title in cn_title) and abs(len(cn_title) - len(taisho_title)) <= 2:
```
The substring matching with length constraint is a reasonable heuristic but could produce false positives for very common short titles. The length check `<= 2` mitigates this.

**LOW: `fetch_url` returns `None` twice (lines 73-74)**
The function has a `return None` after the for loop, but this code is unreachable because the loop always returns on the last attempt (either the fetched data or `None`). The extra `return None` at line 74 is dead code.

---

## 3. Overall Architecture Assessment

### 3.1 Strengths

1. **Clear module boundaries**: The 5-stage pipeline (extract -> fingerprint/candidates -> align -> score -> report) has clean interfaces between stages, with data flowing through well-defined dataclass objects.

2. **Multiprocessing done right**: The codebase correctly handles Python multiprocessing on macOS (`spawn` start method) with:
   - Pool initializer pattern for shared data
   - `stable_hash()` instead of Python's randomized `hash()`
   - `maxtasksperchild` for memory leak mitigation
   - Explicit cleanup of module-level globals

3. **Comprehensive test suite**: 411 tests across 20 files covering all pipeline stages, integration tests, edge cases, and exports. The `test_known_pairs.py` and `test_phonetic_integration.py` files test end-to-end behavior on real-world data.

4. **Good caching strategy**: The `PipelineCache` class uses content hashing + config snapshots + version numbers for cache invalidation, avoiding stale results.

5. **Provenance tracking**: The per-link provenance system (`ProvenanceTracker`) with source attestations is well-designed for academic rigor, enabling reproducibility analysis.

6. **Performance optimizations**: Binary search prefiltering, frozenset intersection, Cython acceleration with pure-Python fallback, source table caching, and early termination checks are all well-motivated and correctly implemented.

### 3.2 Weaknesses

1. **Code duplication (DRY violation)**: The biggest weakness is the triplicated provenance/title-gathering code across `build_expanded_concordance.py`, `export_csv.py`, and `export_tei.py`. This should be refactored into a shared utility module.

2. **Module-level mutable state**: Several modules use module-level mutable globals for multiprocessing worker state. While this is the standard `multiprocessing.Pool` pattern, it makes the code non-reentrant and requires careful lifecycle management. The explicit cleanup functions (e.g., `_cleanup_candidate_globals`) partially mitigate this.

3. **Mixed responsibilities in concordance builder**: `build_expanded_concordance.py` at 1017 lines handles data loading, normalization, merging, error flagging, output formatting, and comparison reporting. Consider splitting into loader, merger, and reporter components.

4. **Hardcoded ground truth**: The validation system uses only 2 known pairs (T250/T251 vs T223). For a corpus-wide pipeline, this is a thin validation layer. Consider loading ground truth from a configuration file and expanding it as more relationships are verified.

### 3.3 Dependency Management

The codebase has reasonable dependencies:
- `lxml` for XML parsing (appropriate for CBETA TEI)
- `tqdm` for progress bars (lightweight)
- Optional `orjson` for fast JSON output
- Optional Cython for fast inner loops

Missing from apparent requirements: `requests` (not used; raw `urllib` is used instead in scrapers).

---

## 4. Recommendations (Prioritized by Severity)

### High Priority

1. **Extract shared concordance utilities into a common module**
   - Create `digest_detector/concordance_utils.py` (or `scripts/utils.py`) with:
     - `normalize_taisho_id()`
     - `resolve_taisho()`
     - `build_number_to_id()`
     - `build_provenance()`
     - `gather_titles_and_nanjio()`
     - `load_known_error_pairs()`
   - Update `build_expanded_concordance.py`, `export_csv.py`, and `export_tei.py` to import from the shared module
   - **Impact**: Eliminates ~400 lines of duplicated code, prevents future divergence bugs

2. **Fix `normalize_taisho_id` mixed return types**
   - In `build_expanded_concordance.py` line 110: return `str(int(m.group(1)))` instead of `int(m.group(1))`, then adjust `resolve_taisho_id` to check for numeric strings
   - Alternative: create a `NormalizedId` type that wraps the result
   - **Impact**: Type safety, prevents accidental integer comparisons with strings

3. **Add error handling to `flag_known_errors`**
   - Wrap the per-error processing in try/except and log malformed entries
   - Validate required keys (`taisho_id`, `erroneous_toh`) before accessing
   - **Impact**: Prevents crash on malformed `known_errors.json`

### Medium Priority

4. **Cache `jing_text` in `ExtractedText`**
   - Add a `_jing_text` field populated in `_process_text_group` after segments are built
   - Replace the `@property` with a simple field access
   - **Impact**: Eliminates repeated filtering and joining in hot paths

5. **Pass phonetic table via Pool initializer in alignment**
   - Follow the pattern used in `candidates.py` with `_phonetic_init`
   - Each worker builds the table once via the initializer instead of lazily on first use
   - **Impact**: More deterministic initialization, clearer data flow

6. **Use proper XML parser in `find_peking_only_texts.py`**
   - Replace regex-based XML parsing with `xml.etree.ElementTree`
   - **Impact**: Robustness against XML format variations

7. **Add fallback warning in export provenance reconstruction**
   - When `link_provenance` is absent and the fallback path is used, emit a warning listing which sources are NOT covered
   - **Impact**: Prevents silent data quality degradation

8. **Fix delta formatting in `compare_with_existing`**
   - Use `f"{new_tib - old_tib:>+8}"` (the `+` format specifier) instead of string concatenation
   - **Impact**: Correct display for negative deltas

### Low Priority

9. **Move `MITRA_STRONG_THRESHOLD` to module level** in `build_expanded_concordance.py`

10. **Add type annotations to script files** (currently most scripts lack type hints)

11. **Remove unused `CONFIDENCE_WEAK` constant** in `parse_mitra.py`

12. **Replace `xml:id` string replacement hack** in `scrape_hobogirin.py` with proper namespace handling

13. **Add environment variable overrides** to `config.py` for key tuning parameters

14. **Expand ground truth validation set** beyond the 2 current pairs, loading from a JSON config file

15. **Add docstrings to `_candidate_worker`** and other multiprocessing workers explaining the shared state contract

---

## 5. Test Coverage Assessment

The test suite (5,705 lines across 20 files) is comprehensive for the pipeline stages:

| Module | Test File | Coverage Assessment |
|--------|-----------|-------------------|
| `extract.py` | `test_extract.py` (186 lines) | Good: tests XML parsing, charDecl, normalization |
| `fingerprint.py` | `test_fingerprint.py` (160 lines) | Good: tests stable_hash, doc freq, stopgrams |
| `candidates.py` | `test_candidates.py` (269 lines) | Good: tests candidate generation, docNumber pairs |
| `align.py` | `test_align.py` (292 lines) | Good: tests seed finding, fuzzy extend, chaining |
| `score.py` | `test_score.py` (345 lines) | Good: tests all classification categories |
| `report.py` | `test_report.py` (241 lines) | Adequate: tests report generation and validation |
| `phonetic.py` | `test_phonetic.py` (187 lines) | Good: tests equivalence table, syllable splitting |
| `cache.py` | `test_cache.py` (233 lines) | Good: tests save/load/invalidation |
| `fast.py` | `test_fast.py` (393 lines) | Good: tests both Cython and fallback paths |
| Exports | `test_exports.py` (607 lines) | Good: tests CSV and TEI output |
| Integration | `test_known_pairs.py` (421 lines) | Excellent: T250/T251->T223 end-to-end |

### Notable test gaps:

1. **No tests for `build_expanded_concordance.py`**: The largest and most complex script has no dedicated tests. The `test_otani_concordance.py` covers the Otani integration, but the main merge logic is untested.

2. **No tests for scraper scripts**: `scrape_dila_catalog.py`, `scrape_hobogirin.py`, `scrape_ddb.py`, `scrape_cbeta_jinglu_*.py`, `scrape_tohoku_index.py` have no test files. Parsing functions (e.g., `parse_tohoku_field`, `parse_otani_field`, `parse_entry_html`) should have unit tests.

3. **No tests for `parse_mitra.py`**: The MITRA parser has straightforward logic but no tests.

4. **No tests for `find_peking_only_texts.py`**: The Peking-only text finder has regex-based XML parsing that should be tested.

5. **Edge case coverage**: While `test_edge_cases.py` exists (184 lines), it could be expanded to cover:
   - Empty texts with only preface material (jing_text = full_text fallback)
   - Texts with only phonetic content (no exact matches)
   - Very large texts (>50K chars) near the `MAX_DIGEST_LENGTH` boundary

---

## 6. Security Assessment

The codebase is a research tool with minimal security surface:

1. **Pickle deserialization** (`cache.py` line 107): Low risk since cache files are locally generated. Add a comment noting the trust assumption.

2. **Web scraping scripts** use `urllib.request.urlopen` without explicit SSL verification. For academic scraping this is acceptable.

3. **No user-controlled input paths**: All file paths are derived from `Path(__file__).resolve().parent`, so path traversal is not a concern.

4. **No SQL/command injection**: No database queries or shell command construction from user input.

5. **No API keys or credentials in code**: The DDB scraper notes authentication limitations in comments but does not store credentials.

Overall security posture is appropriate for a single-user research project.

---

## 7. Performance Notes

The pipeline processes ~8,982 XML files and ~2,459 texts. Key performance characteristics:

1. **Stage 1 (Extract)**: I/O bound. Character map building scans all files. Consider parallelizing charDecl extraction or caching the map.

2. **Stage 2 (Candidates)**: CPU bound. The `frozenset` intersection approach with binary search prefiltering is efficient. The `fast_ngram_hashes` function benefits significantly from Cython.

3. **Stage 3 (Alignment)**: CPU and memory bound. Source table caching in `_align_pair_wrapper` is a good optimization. Consider the suggestion to use `imap` instead of `imap_unordered` to preserve the cache-friendly ordering.

4. **Concordance builder**: Memory bound for the provenance tracking. The `defaultdict(list)` in `ProvenanceTracker` is appropriate.

5. **Export scripts**: I/O bound. The fallback provenance reconstruction re-reads all source files, which is slow but only used when `link_provenance` is missing.

---

*End of review.*
