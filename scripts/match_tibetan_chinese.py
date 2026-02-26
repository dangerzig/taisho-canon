#!/usr/bin/env python3
"""Match Tibetan canon entries to Chinese Taisho texts using LLM evaluation.

4-stage pipeline:
  Stage 1: Candidate generation (section filtering, title overlap, Sanskrit matching, Nanjio)
  Stage 2: Content feature extraction (opening/closing text, metadata, names)
  Stage 3: LLM evaluation (Claude API batch calls)
  Stage 4: Validation, review, and output

Run: python3 scripts/match_tibetan_chinese.py [--dry-run] [--max-llm-pairs N]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from digest_detector.sanskrit_match import (
    normalize_title as normalize_sanskrit,
    tokenize_title,
    jaccard_similarity,
    levenshtein_ratio_threshold,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR = BASE_DIR / "data"
TEXTS_DIR = DATA_DIR / "texts"
METADATA_PATH = DATA_DIR / "metadata.json"

CBETA_TIBETAN_PATH = RESULTS_DIR / "cbeta_jinglu_tibetan.json"
CBETA_SANSKRIT_PATH = RESULTS_DIR / "cbeta_jinglu_sanskrit.json"
EXPANDED_XREF_PATH = RESULTS_DIR / "cross_reference_expanded.json"
LANCASTER_PATH = BASE_DIR / "lancaster_taisho_crossref.json"

OUTPUT_MATCHES_PATH = RESULTS_DIR / "tibetan_chinese_matches.json"
OUTPUT_REVIEW_PATH = RESULTS_DIR / "tibetan_matching_review.md"

# ---------------------------------------------------------------------------
# Stage 1: Candidate Generation
# ---------------------------------------------------------------------------

# CBETA section → plausible Taisho volume ranges
# Broad ranges to avoid missing matches; LLM will filter false positives
SECTION_TO_VOLUMES: dict[str, list[tuple[int, int]]] = {
    "律部": [(22, 24)],
    "般若部": [(5, 8), (25, 26)],
    "經部": [(1, 4), (9, 17)],
    "寶積部": [(11, 12)],
    "華嚴部": [(9, 10)],
    "本生部": [(3, 4)],
    "怛特羅部": [(18, 21)],
    "十萬怛特羅部": [(18, 21)],
    "古怛特羅": [(18, 21)],
    "陀羅尼集": [(18, 21)],
    "中觀部": [(25, 32)],
    "唯識部": [(25, 32)],
    "因明部": [(25, 32)],
    "阿毘達磨部": [(25, 32)],
    "經疏部": [(25, 32), (33, 40)],
    "禮讚部": [(25, 32)],
    # Broad sections: allow all sutra/sastra volumes
    "雜部": [(1, 21)],
    "阿底沙小部集": [(25, 32)],
    "修身部": [(25, 32)],
    "書翰部": [(25, 32), (52, 55)],
    "聲明部": [(25, 32), (54, 54)],
    "工巧明部": [(25, 32)],
    "醫方明部": [(25, 32)],
    "目錄部": [(49, 55)],
    "時輪經疏": [(18, 21)],
}

# Common Chinese title prefixes to strip for matching
_TITLE_PREFIXES = ["佛說", "大方廣", "大", "聖"]


def _vol_from_id(text_id: str) -> int:
    """Extract volume number from TXXnNNNN."""
    m = re.match(r"T(\d{2})n\d{4}", text_id)
    return int(m.group(1)) if m else 0


def _num_from_id(text_id: str) -> int:
    """Extract text number from TXXnNNNN."""
    m = re.match(r"T\d{2}n(\d{4})", text_id)
    return int(m.group(1)) if m else 0


def _cjk_chars(title: str) -> str:
    """Extract only CJK characters from a title."""
    return "".join(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", title))


def _strip_title_prefix(title: str) -> str:
    """Strip common prefixes like 佛說 for containment check."""
    for prefix in _TITLE_PREFIXES:
        if title.startswith(prefix) and len(title) > len(prefix) + 1:
            title = title[len(prefix):]
    return title


def _title_match_score(tibetan_title: str, taisho_title: str) -> tuple[float, str]:
    """Compute how well two Chinese titles match.

    Returns (score 0-1, match_type) where match_type is one of:
    'exact', 'substring', 'overlap', 'none'.
    """
    t1 = _cjk_chars(tibetan_title)
    t2 = _cjk_chars(taisho_title)
    if not t1 or not t2:
        return 0.0, "none"

    # Exact match (after CJK-only extraction)
    if t1 == t2:
        return 1.0, "exact"

    # Strip prefixes and try again
    t1s = _cjk_chars(_strip_title_prefix(tibetan_title))
    t2s = _cjk_chars(_strip_title_prefix(taisho_title))
    if t1s and t2s and t1s == t2s:
        return 0.95, "exact"

    # Substring containment: shorter ⊂ longer
    shorter, longer = (t1s or t1), (t2s or t2)
    if len(shorter) > len(longer):
        shorter, longer = longer, shorter
    if len(shorter) >= 2 and shorter in longer:
        return 0.90, "substring"

    # Character-set overlap (Jaccard on unique chars)
    set1 = set(t1s or t1)
    set2 = set(t2s or t2)
    inter = len(set1 & set2)
    union = len(set1 | set2)
    jaccard = inter / union if union else 0.0

    # For short titles (2-3 chars), require very high overlap
    min_len = min(len(t1s or t1), len(t2s or t2))
    if min_len <= 3:
        threshold = 0.7  # e.g. 2/3 chars must overlap
    else:
        threshold = 0.4  # longer titles can have more noise

    if jaccard >= threshold:
        return jaccard, "overlap"

    return 0.0, "none"


def load_taisho_metadata() -> dict[str, dict]:
    """Load Taisho text metadata into {text_id: {title, author, char_count, ...}}."""
    with open(METADATA_PATH) as f:
        meta_list = json.load(f)
    return {m["text_id"]: m for m in meta_list}


def load_cbeta_tibetan() -> dict[str, dict]:
    """Load CBETA Jinglu Tibetan entries."""
    with open(CBETA_TIBETAN_PATH) as f:
        data = json.load(f)
    return data["entries"]


def load_existing_mappings() -> dict[str, set[str]]:
    """Load existing concordance Taisho→Tibetan mappings.

    Returns {taisho_id: set of Toh/Otani identifiers}.
    """
    if not EXPANDED_XREF_PATH.exists():
        return {}
    with open(EXPANDED_XREF_PATH) as f:
        data = json.load(f)
    result = {}
    for tid, parallels in data.get("tibetan_parallels", {}).items():
        result[tid] = set(parallels)
    return result


def load_nanjio_to_taisho() -> dict[str, list[str]]:
    """Build Nanjio number → Taisho ID mapping from all sources."""
    nj_map: dict[str, list[str]] = defaultdict(list)

    # From Lancaster
    if LANCASTER_PATH.exists():
        with open(LANCASTER_PATH) as f:
            data = json.load(f)
        for entry in data.values():
            nj = entry.get("nanjio")
            t = entry.get("taisho")
            if nj and t:
                nj_key = f"Nj {nj}" if not str(nj).startswith("Nj") else str(nj)
                nj_map[nj_key].append(str(t))

    # From CBETA Sanskrit
    if CBETA_SANSKRIT_PATH.exists():
        with open(CBETA_SANSKRIT_PATH) as f:
            data = json.load(f)
        for entry in data.get("entries", {}).values():
            nj = entry.get("nanjio")
            if nj:
                for t_raw in entry.get("taisho", []):
                    nj_map[nj].append(t_raw)

    return dict(nj_map)


def generate_candidates(
    tibetan_entries: dict[str, dict],
    taisho_meta: dict[str, dict],
    existing_mappings: dict[str, set[str]],
) -> list[dict]:
    """Stage 1: Generate candidate Tibetan→Taisho pairs.

    Uses section filtering, Chinese title overlap, Sanskrit title matching,
    and Nanjio cross-references to reduce the search space.
    """
    log.info("Stage 1: Generating candidates...")

    # Pre-compute indexes
    vol_to_taisho: dict[int, list[str]] = defaultdict(list)
    for tid in taisho_meta:
        vol = _vol_from_id(tid)
        if vol:
            vol_to_taisho[vol].append(tid)

    # No pre-computation needed for title matching now

    # Sanskrit title index: normalized → [taisho_id, ...]
    # (from CBETA Sanskrit + Lancaster)
    taisho_sanskrit: dict[str, list[str]] = defaultdict(list)
    if CBETA_SANSKRIT_PATH.exists():
        with open(CBETA_SANSKRIT_PATH) as f:
            skt_data = json.load(f)
        for entry in skt_data.get("entries", {}).values():
            skt = entry.get("sanskrit_title", "")
            if skt:
                norm = normalize_sanskrit(skt)
                for t_raw in entry.get("taisho", []):
                    # Resolve bare T-number to canonical ID
                    tid = _resolve_taisho_id(t_raw, taisho_meta)
                    if tid:
                        taisho_sanskrit[norm].append(tid)
    if LANCASTER_PATH.exists():
        with open(LANCASTER_PATH) as f:
            lanc = json.load(f)
        for entry in lanc.values():
            skt = entry.get("sanskrit_title", "")
            if skt:
                norm = normalize_sanskrit(skt)
                t_raw = str(entry.get("taisho", ""))
                tid = _resolve_taisho_id(f"T{t_raw}", taisho_meta)
                if tid:
                    taisho_sanskrit[norm].append(tid)

    nj_map = load_nanjio_to_taisho()

    # Identify unmapped entries (those without existing Taisho refs)
    unmapped = {
        eid: entry for eid, entry in tibetan_entries.items()
        if not entry.get("taisho")
    }
    log.info("  %d unmapped Tibetan entries to match", len(unmapped))

    candidates: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for eid, entry in unmapped.items():
        section = entry.get("section", "")
        chinese_title = entry.get("chinese_title", "")
        sanskrit_title = entry.get("sanskrit_title", "")
        nanjio = entry.get("nanjio")

        # Determine candidate Taisho volumes from section
        vol_ranges = SECTION_TO_VOLUMES.get(section, [(1, 55)])
        candidate_tids: set[str] = set()
        for lo, hi in vol_ranges:
            for v in range(lo, hi + 1):
                candidate_tids.update(vol_to_taisho.get(v, []))

        entry_candidates: list[dict] = []

        # 1a. Nanjio direct lookup
        if nanjio:
            nj_key = nanjio if nanjio.startswith("Nj") else f"Nj {nanjio}"
            for t_raw in nj_map.get(nj_key, []):
                tid = _resolve_taisho_id(f"T{t_raw}" if not t_raw.startswith("T") else t_raw,
                                         taisho_meta)
                if tid and (eid, tid) not in seen_pairs:
                    seen_pairs.add((eid, tid))
                    entry_candidates.append({
                        "cbeta_id": eid,
                        "taisho_id": tid,
                        "match_signals": ["nanjio"],
                        "nanjio_match": True,
                    })

        # 1b. Chinese title matching
        if chinese_title:
            for tid in candidate_tids:
                if (eid, tid) in seen_pairs:
                    continue
                t_title = taisho_meta[tid].get("title", "")
                if not t_title:
                    continue

                score, match_type = _title_match_score(chinese_title, t_title)
                if score > 0:
                    seen_pairs.add((eid, tid))
                    entry_candidates.append({
                        "cbeta_id": eid,
                        "taisho_id": tid,
                        "match_signals": [f"chinese_title_{match_type}"],
                        "title_score": round(score, 3),
                    })

        # 1c. Sanskrit title matching
        if sanskrit_title:
            skt_norm = normalize_sanskrit(sanskrit_title)
            skt_tokens = tokenize_title(sanskrit_title)

            for t_norm, t_tids in taisho_sanskrit.items():
                # Exact
                if skt_norm == t_norm:
                    for tid in t_tids:
                        if (eid, tid) not in seen_pairs:
                            seen_pairs.add((eid, tid))
                            entry_candidates.append({
                                "cbeta_id": eid,
                                "taisho_id": tid,
                                "match_signals": ["sanskrit_exact"],
                                "sanskrit_score": 1.0,
                            })
                    continue

                # Token Jaccard
                t_tokens = tokenize_title(t_norm)  # already normalised
                if skt_tokens and t_tokens:
                    jacc = jaccard_similarity(skt_tokens, t_tokens)
                    if jacc >= 0.5:
                        for tid in t_tids:
                            if (eid, tid) not in seen_pairs:
                                seen_pairs.add((eid, tid))
                                entry_candidates.append({
                                    "cbeta_id": eid,
                                    "taisho_id": tid,
                                    "match_signals": ["sanskrit_token"],
                                    "sanskrit_score": round(jacc, 3),
                                })
                        continue

                # Fuzzy (Levenshtein)
                if len(skt_norm) >= 8 and len(t_norm) >= 8:
                    ratio = levenshtein_ratio_threshold(skt_norm, t_norm, 0.80)
                    if ratio >= 0.80:
                        for tid in t_tids:
                            if (eid, tid) not in seen_pairs:
                                seen_pairs.add((eid, tid))
                                entry_candidates.append({
                                    "cbeta_id": eid,
                                    "taisho_id": tid,
                                    "match_signals": ["sanskrit_fuzzy"],
                                    "sanskrit_score": round(ratio, 3),
                                })

        candidates.extend(entry_candidates)

    log.info("  Generated %d candidate pairs for %d entries",
             len(candidates), len(unmapped))

    # Count entries with at least one candidate
    entries_with_candidates = len({c["cbeta_id"] for c in candidates})
    log.info("  %d entries have >= 1 candidate, %d entries have 0 candidates",
             entries_with_candidates, len(unmapped) - entries_with_candidates)

    return candidates


def _resolve_taisho_id(raw: str, taisho_meta: dict[str, dict]) -> str | None:
    """Resolve a raw Taisho reference (T250, T08n0250) to a canonical corpus ID."""
    raw = raw.strip()
    if raw in taisho_meta:
        return raw
    m = re.match(r"T(\d+)$", raw)
    if m:
        num = int(m.group(1))
        for tid in taisho_meta:
            if _num_from_id(tid) == num:
                return tid
    return None


# ---------------------------------------------------------------------------
# Stage 2: Content Feature Extraction
# ---------------------------------------------------------------------------

def extract_features(
    candidates: list[dict],
    tibetan_entries: dict[str, dict],
    taisho_meta: dict[str, dict],
) -> list[dict]:
    """Stage 2: Extract content features for each candidate pair.

    Reads opening/closing text from Taisho files and assembles metadata
    for LLM evaluation.
    """
    log.info("Stage 2: Extracting content features...")

    # Cache text readings (same Taisho text may appear in multiple pairs)
    text_cache: dict[str, dict] = {}

    enriched: list[dict] = []
    for cand in candidates:
        tid = cand["taisho_id"]
        eid = cand["cbeta_id"]
        tib_entry = tibetan_entries[eid]
        t_meta = taisho_meta.get(tid, {})

        # Load Taisho text features (cached)
        if tid not in text_cache:
            text_cache[tid] = _extract_taisho_features(tid, t_meta)
        t_features = text_cache[tid]

        # Build feature dict
        feature = dict(cand)
        feature["taisho_title"] = t_meta.get("title", "")
        feature["taisho_author"] = t_meta.get("author", "")
        feature["taisho_char_count"] = t_meta.get("char_count", 0)
        feature["taisho_has_dharani"] = t_meta.get("has_dharani", False)
        feature["taisho_opening"] = t_features.get("opening", "")
        feature["taisho_closing"] = t_features.get("closing", "")

        feature["tibetan_chinese_title"] = tib_entry.get("chinese_title", "")
        feature["tibetan_sanskrit_title"] = tib_entry.get("sanskrit_title", "")
        feature["tibetan_title"] = tib_entry.get("tibetan_title", "")
        feature["tibetan_wylie"] = tib_entry.get("tibetan_wylie", "")
        feature["tibetan_section"] = tib_entry.get("section", "")
        feature["tibetan_nanjio"] = tib_entry.get("nanjio")

        enriched.append(feature)

    log.info("  Extracted features for %d candidate pairs", len(enriched))
    return enriched


def _extract_taisho_features(text_id: str, meta: dict) -> dict:
    """Read opening/closing text from a Taisho text file."""
    text_path = TEXTS_DIR / f"{text_id}.txt"
    if not text_path.exists():
        return {"opening": "", "closing": ""}

    text = text_path.read_text(encoding="utf-8")
    # First/last 200 CJK chars
    opening = text[:200] if len(text) >= 200 else text
    closing = text[-200:] if len(text) >= 200 else text

    return {"opening": opening, "closing": closing}


# ---------------------------------------------------------------------------
# Stage 3: LLM Evaluation
# ---------------------------------------------------------------------------

# Batch size for LLM calls (pairs per request)
LLM_BATCH_SIZE = 10
# Rate limiting
LLM_REQUESTS_PER_MINUTE = 50
LLM_REQUEST_INTERVAL = 60.0 / LLM_REQUESTS_PER_MINUTE

SYSTEM_PROMPT = """\
You are a specialist in Buddhist textual scholarship. Your task is to determine \
whether a Tibetan canon catalogue entry and a Chinese Taishō canon text are \
parallel texts — i.e. translations of the same Indic source, or direct \
translations of each other.

For each pair, evaluate:
1. **Title semantics**: Do the Chinese titles refer to the same text? Account for \
   variant translations of Sanskrit terms (e.g. 般若波羅蜜 and 般若波羅蜜多 both \
   translate prajñāpāramitā).
2. **Sanskrit title**: If both have Sanskrit titles, are they the same or closely \
   related? Ignore minor spelling/transliteration differences.
3. **Genre compatibility**: Does the Tibetan section (般若部, 經部, 怛特羅部, etc.) \
   match the Taishō volume range (vols 1-21 = sūtra, 18-21 = tantra, 22-24 = \
   vinaya, 25-32 = śāstra)?
4. **Text content**: Does the opening of the Chinese text (如是我聞 = "thus have I \
   heard", or other formulas) match expectations for this type of text?
5. **Length plausibility**: Is the Chinese text length consistent with the type of \
   text described in the Tibetan catalogue entry?

Return a JSON array with one object per pair:
```json
[
  {
    "pair_index": 0,
    "verdict": "MATCH",
    "confidence": 85,
    "reason": "Brief explanation"
  }
]
```

verdict must be one of: "MATCH", "NO_MATCH", "UNCERTAIN"
confidence must be 0-100 (integer).
"""


def _build_pair_description(pair: dict, index: int) -> str:
    """Format a single candidate pair for the LLM prompt."""
    lines = [f"### Pair {index}"]
    lines.append(f"**Tibetan catalogue entry** (CBETA #{pair['cbeta_id']}):")
    lines.append(f"  Chinese title: {pair.get('tibetan_chinese_title', '?')}")
    if pair.get("tibetan_sanskrit_title"):
        lines.append(f"  Sanskrit title: {pair['tibetan_sanskrit_title']}")
    if pair.get("tibetan_wylie"):
        lines.append(f"  Tibetan (Wylie): {pair['tibetan_wylie']}")
    lines.append(f"  Section: {pair.get('tibetan_section', '?')}")
    if pair.get("tibetan_nanjio"):
        lines.append(f"  Nanjio: {pair['tibetan_nanjio']}")
    signals = pair.get("match_signals", [])
    if signals:
        lines.append(f"  Pre-filter signals: {', '.join(signals)}")
        if pair.get("sanskrit_score"):
            lines.append(f"  Sanskrit match score: {pair['sanskrit_score']}")
        if pair.get("title_jaccard"):
            lines.append(f"  Title bigram Jaccard: {pair['title_jaccard']}")
        if pair.get("title_containment"):
            lines.append(f"  Title containment: {pair['title_containment']}")

    lines.append(f"\n**Taishō text** ({pair['taisho_id']}):")
    lines.append(f"  Title: {pair.get('taisho_title', '?')}")
    lines.append(f"  Author/translator: {pair.get('taisho_author', '?')}")
    lines.append(f"  Length: {pair.get('taisho_char_count', '?')} CJK characters")
    if pair.get("taisho_has_dharani"):
        lines.append("  Contains dhāraṇī sections")
    if pair.get("taisho_opening"):
        lines.append(f"  Opening: {pair['taisho_opening'][:150]}")
    if pair.get("taisho_closing"):
        lines.append(f"  Closing: ...{pair['taisho_closing'][-100:]}")

    return "\n".join(lines)


async def evaluate_batch(
    client: Any,
    pairs: list[dict],
    model: str,
    batch_index: int,
    total_batches: int,
) -> list[dict]:
    """Evaluate a batch of candidate pairs via Claude API."""
    descriptions = []
    for i, pair in enumerate(pairs):
        descriptions.append(_build_pair_description(pair, i))

    user_prompt = (
        f"Evaluate these {len(pairs)} candidate pairs. "
        "For each one, determine if the Tibetan catalogue entry and "
        "the Chinese Taishō text are parallel texts.\n\n"
        + "\n\n---\n\n".join(descriptions)
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text

        # Extract JSON from response
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            results = json.loads(json_match.group())
        else:
            log.warning("Batch %d/%d: No JSON found in response",
                        batch_index + 1, total_batches)
            results = []

        # Merge results back into pairs
        result_map = {r["pair_index"]: r for r in results}
        for i, pair in enumerate(pairs):
            r = result_map.get(i, {})
            pair["llm_verdict"] = r.get("verdict", "UNCERTAIN")
            pair["llm_confidence"] = r.get("confidence", 0)
            pair["llm_reason"] = r.get("reason", "No response")
            pair["llm_model"] = model

        log.info("  Batch %d/%d: %d pairs evaluated (%s)",
                 batch_index + 1, total_batches, len(pairs), model)
        return pairs

    except Exception as e:
        log.error("Batch %d/%d failed: %s", batch_index + 1, total_batches, e)
        for pair in pairs:
            pair["llm_verdict"] = "ERROR"
            pair["llm_confidence"] = 0
            pair["llm_reason"] = str(e)
            pair["llm_model"] = model
        return pairs


def run_llm_evaluation(
    enriched: list[dict],
    max_pairs: int | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Stage 3: Evaluate candidate pairs using Claude API.

    Uses Haiku for routine pairs, escalates uncertain cases to Sonnet.
    """
    import anthropic

    if dry_run:
        log.info("Stage 3: DRY RUN — skipping LLM evaluation, marking all as UNCERTAIN")
        for pair in enriched:
            pair["llm_verdict"] = "UNCERTAIN"
            pair["llm_confidence"] = 50
            pair["llm_reason"] = "Dry run — not evaluated"
            pair["llm_model"] = "dry_run"
        return enriched

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set. Use --dry-run to skip LLM evaluation.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    haiku_model = "claude-haiku-4-5-20251001"
    sonnet_model = "claude-sonnet-4-5-20250929"

    pairs_to_eval = enriched
    if max_pairs and max_pairs < len(pairs_to_eval):
        log.info("Limiting to %d pairs (of %d)", max_pairs, len(pairs_to_eval))
        pairs_to_eval = pairs_to_eval[:max_pairs]

    log.info("Stage 3: Evaluating %d candidate pairs with Claude API...", len(pairs_to_eval))

    # First pass: Haiku for all pairs
    batches = [
        pairs_to_eval[i:i + LLM_BATCH_SIZE]
        for i in range(0, len(pairs_to_eval), LLM_BATCH_SIZE)
    ]

    log.info("  Pass 1: %d batches with Haiku", len(batches))
    pass1_start = time.time()
    for i, batch in enumerate(batches):
        evaluate_batch_sync(client, batch, haiku_model, i, len(batches))
        # Progress report every 10 batches
        if (i + 1) % 10 == 0 or i == len(batches) - 1:
            _log_progress(pairs_to_eval, "Pass 1 (Haiku)", i + 1, len(batches), pass1_start)
        if i < len(batches) - 1:
            time.sleep(LLM_REQUEST_INTERVAL)

    # Second pass: Escalate uncertain cases to Sonnet
    uncertain = [p for p in pairs_to_eval if p.get("llm_verdict") == "UNCERTAIN"]
    if uncertain:
        log.info("  Pass 2: Escalating %d uncertain pairs to Sonnet", len(uncertain))
        pass2_start = time.time()
        esc_batches = [
            uncertain[i:i + LLM_BATCH_SIZE]
            for i in range(0, len(uncertain), LLM_BATCH_SIZE)
        ]
        for i, batch in enumerate(esc_batches):
            evaluate_batch_sync(client, batch, sonnet_model, i, len(esc_batches))
            # Progress report every 5 batches (Sonnet is slower)
            if (i + 1) % 5 == 0 or i == len(esc_batches) - 1:
                _log_progress(pairs_to_eval, "Pass 2 (Sonnet)", i + 1, len(esc_batches), pass2_start)
            if i < len(esc_batches) - 1:
                time.sleep(LLM_REQUEST_INTERVAL)

    matches = sum(1 for p in pairs_to_eval if p.get("llm_verdict") == "MATCH")
    no_match = sum(1 for p in pairs_to_eval if p.get("llm_verdict") == "NO_MATCH")
    uncertain_count = sum(1 for p in pairs_to_eval if p.get("llm_verdict") == "UNCERTAIN")
    errors = sum(1 for p in pairs_to_eval if p.get("llm_verdict") == "ERROR")
    log.info("  Results: %d MATCH, %d NO_MATCH, %d UNCERTAIN, %d ERROR",
             matches, no_match, uncertain_count, errors)

    return pairs_to_eval


def _log_progress(
    all_pairs: list[dict],
    pass_name: str,
    batches_done: int,
    total_batches: int,
    start_time: float,
) -> None:
    """Log a progress summary with running tallies and ETA."""
    elapsed = time.time() - start_time
    rate = batches_done / elapsed if elapsed > 0 else 0
    remaining = (total_batches - batches_done) / rate if rate > 0 else 0

    matches = sum(1 for p in all_pairs if p.get("llm_verdict") == "MATCH")
    no_match = sum(1 for p in all_pairs if p.get("llm_verdict") == "NO_MATCH")
    uncertain = sum(1 for p in all_pairs if p.get("llm_verdict") == "UNCERTAIN")
    errors = sum(1 for p in all_pairs if p.get("llm_verdict") == "ERROR")
    pending = sum(1 for p in all_pairs if "llm_verdict" not in p)

    log.info(
        "  [%s %d/%d] %.0fs elapsed, ~%.0fs remaining | "
        "MATCH=%d NO_MATCH=%d UNCERTAIN=%d ERROR=%d pending=%d",
        pass_name, batches_done, total_batches,
        elapsed, remaining,
        matches, no_match, uncertain, errors, pending,
    )


def evaluate_batch_sync(
    client: Any,
    pairs: list[dict],
    model: str,
    batch_index: int,
    total_batches: int,
) -> list[dict]:
    """Synchronous wrapper for evaluate_batch."""
    descriptions = []
    for i, pair in enumerate(pairs):
        descriptions.append(_build_pair_description(pair, i))

    user_prompt = (
        f"Evaluate these {len(pairs)} candidate pairs. "
        "For each one, determine if the Tibetan catalogue entry and "
        "the Chinese Taishō text are parallel texts.\n\n"
        + "\n\n---\n\n".join(descriptions)
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text

        # Extract JSON from response
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            results = json.loads(json_match.group())
        else:
            log.warning("Batch %d/%d: No JSON found in response",
                        batch_index + 1, total_batches)
            results = []

        # Merge results back into pairs
        result_map = {r["pair_index"]: r for r in results}
        for i, pair in enumerate(pairs):
            r = result_map.get(i, {})
            pair["llm_verdict"] = r.get("verdict", "UNCERTAIN")
            pair["llm_confidence"] = r.get("confidence", 0)
            pair["llm_reason"] = r.get("reason", "No response")
            pair["llm_model"] = model

        log.info("  Batch %d/%d: %d pairs evaluated (%s)",
                 batch_index + 1, total_batches, len(pairs), model)

    except Exception as e:
        log.error("Batch %d/%d failed: %s", batch_index + 1, total_batches, e)
        for pair in pairs:
            pair["llm_verdict"] = "ERROR"
            pair["llm_confidence"] = 0
            pair["llm_reason"] = str(e)
            pair["llm_model"] = model
        # Abort on billing/auth errors
        err_str = str(e)
        if "credit balance" in err_str or "authentication" in err_str.lower():
            raise RuntimeError(f"Fatal API error: {e}") from e

    return pairs


# ---------------------------------------------------------------------------
# Stage 3b: No-candidate classification
# ---------------------------------------------------------------------------

def classify_no_candidates(
    unmapped_no_cand: list[dict],
    client: Any | None = None,
    dry_run: bool = False,
    max_classify: int | None = None,
) -> list[dict]:
    """For entries with no candidates, ask LLM if a Chinese parallel likely exists."""
    if not unmapped_no_cand:
        return []
    if dry_run or client is None:
        for entry in unmapped_no_cand:
            entry["likely_has_chinese"] = "UNKNOWN"
            entry["classify_reason"] = "Not evaluated"
        return unmapped_no_cand

    import anthropic

    classify_prompt_sys = """\
You are a Buddhist textual scholar. For each Tibetan canon entry, assess whether \
it is likely to have a Chinese parallel in the Taishō canon.

Consider:
- Tantric texts (怛特羅部) often do NOT have Chinese parallels
- Vinaya texts usually have Chinese parallels
- Prajñāpāramitā sūtras almost always have Chinese parallels
- Short commentaries and liturgical texts rarely have Chinese parallels
- Texts with Nanjio numbers usually have Chinese parallels

Return a JSON array:
```json
[{"index": 0, "likely": "YES"|"NO"|"MAYBE", "reason": "..."}]
```
"""

    entries = unmapped_no_cand
    if max_classify and max_classify < len(entries):
        entries = entries[:max_classify]

    batches = [entries[i:i + 20] for i in range(0, len(entries), 20)]
    haiku_model = "claude-haiku-4-5-20251001"

    log.info("  Classifying %d entries with no candidates (%d batches)",
             len(entries), len(batches))

    for bi, batch in enumerate(batches):
        descriptions = []
        for i, entry in enumerate(batch):
            lines = [f"### Entry {i}"]
            lines.append(f"  Chinese title: {entry.get('chinese_title', '?')}")
            if entry.get("sanskrit_title"):
                lines.append(f"  Sanskrit: {entry['sanskrit_title']}")
            lines.append(f"  Section: {entry.get('section', '?')}")
            if entry.get("nanjio"):
                lines.append(f"  Nanjio: {entry['nanjio']}")
            descriptions.append("\n".join(lines))

        user_prompt = (
            f"For these {len(batch)} Tibetan catalogue entries, assess whether "
            "each likely has a Chinese parallel in the Taishō canon.\n\n"
            + "\n\n".join(descriptions)
        )

        try:
            response = client.messages.create(
                model=haiku_model,
                max_tokens=2048,
                system=classify_prompt_sys,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = response.content[0].text
            json_match = re.search(r"\[.*\]", text, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
                result_map = {r["index"]: r for r in results}
                for i, entry in enumerate(batch):
                    r = result_map.get(i, {})
                    entry["likely_has_chinese"] = r.get("likely", "UNKNOWN")
                    entry["classify_reason"] = r.get("reason", "")
            log.info("  Classified batch %d/%d", bi + 1, len(batches))
        except Exception as e:
            log.error("  Classification batch %d failed: %s", bi + 1, e)
            for entry in batch:
                entry["likely_has_chinese"] = "ERROR"
                entry["classify_reason"] = str(e)

        if bi < len(batches) - 1:
            time.sleep(LLM_REQUEST_INTERVAL)

    return entries


# ---------------------------------------------------------------------------
# Stage 4: Validation, Review & Output
# ---------------------------------------------------------------------------

def validate_and_output(
    evaluated: list[dict],
    tibetan_entries: dict[str, dict],
    existing_mappings: dict[str, set[str]],
    no_candidate_entries: list[dict] | None = None,
) -> dict:
    """Stage 4: Validate results and produce output files."""
    log.info("Stage 4: Validation and output...")

    # Separate by verdict
    matches = [p for p in evaluated if p.get("llm_verdict") == "MATCH"]
    no_match = [p for p in evaluated if p.get("llm_verdict") == "NO_MATCH"]
    uncertain = [p for p in evaluated
                 if p.get("llm_verdict") in ("UNCERTAIN", "ERROR")]

    # Classify by confidence
    high_conf = [m for m in matches if m.get("llm_confidence", 0) >= 90]
    medium_conf = [m for m in matches if 60 <= m.get("llm_confidence", 0) < 90]
    low_conf = [m for m in matches if m.get("llm_confidence", 0) < 60]

    # Cross-validate against known mappings (for entries that DO have taisho refs)
    # Check if any matched pairs involve entries that have known Taisho refs
    # (these weren't in our unmapped set, but we can check for consistency)
    known_cbeta_entries = {
        eid for eid, entry in tibetan_entries.items()
        if entry.get("taisho")
    }

    # Validation: check match Taisho IDs against existing concordance
    validated = []
    new_proposals = []
    for m in matches:
        tid = m["taisho_id"]
        if tid in existing_mappings:
            # This Taisho text already has Tibetan parallels
            validated.append(m)
        else:
            new_proposals.append(m)

    # Build output
    results = {
        "summary": {
            "total_candidates": len(evaluated),
            "matches": len(matches),
            "no_match": len(no_match),
            "uncertain": len(uncertain),
            "high_confidence": len(high_conf),
            "medium_confidence": len(medium_conf),
            "low_confidence": len(low_conf),
            "validated_against_concordance": len(validated),
            "new_proposals": len(new_proposals),
            "unique_new_taisho": len({m["taisho_id"] for m in new_proposals}),
            "unique_new_cbeta": len({m["cbeta_id"] for m in new_proposals}),
        },
        "matches": [_serialize_pair(m) for m in matches],
        "uncertain": [_serialize_pair(u) for u in uncertain],
        "no_match_count": len(no_match),
    }

    if no_candidate_entries:
        likely_yes = [e for e in no_candidate_entries
                      if e.get("likely_has_chinese") == "YES"]
        likely_maybe = [e for e in no_candidate_entries
                        if e.get("likely_has_chinese") == "MAYBE"]
        results["no_candidate_entries"] = {
            "total": len(no_candidate_entries),
            "likely_has_chinese_yes": len(likely_yes),
            "likely_has_chinese_maybe": len(likely_maybe),
            "likely_has_chinese_no": len(no_candidate_entries) - len(likely_yes) - len(likely_maybe),
            "entries_needing_review": [
                {
                    "cbeta_id": e.get("id") or e.get("entry_number"),
                    "chinese_title": e.get("chinese_title", ""),
                    "sanskrit_title": e.get("sanskrit_title", ""),
                    "section": e.get("section", ""),
                    "likely_has_chinese": e.get("likely_has_chinese", "UNKNOWN"),
                    "reason": e.get("classify_reason", ""),
                }
                for e in likely_yes + likely_maybe
            ],
        }

    # Write JSON results
    OUTPUT_MATCHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MATCHES_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    log.info("  Results written to %s", OUTPUT_MATCHES_PATH)

    # Write review document
    _write_review(results, matches, uncertain, no_candidate_entries)

    return results


def _serialize_pair(pair: dict) -> dict:
    """Serialize a pair for JSON output, keeping only relevant fields."""
    return {
        "cbeta_id": pair.get("cbeta_id"),
        "taisho_id": pair.get("taisho_id"),
        "tibetan_chinese_title": pair.get("tibetan_chinese_title", ""),
        "tibetan_sanskrit_title": pair.get("tibetan_sanskrit_title", ""),
        "tibetan_section": pair.get("tibetan_section", ""),
        "taisho_title": pair.get("taisho_title", ""),
        "taisho_author": pair.get("taisho_author", ""),
        "taisho_char_count": pair.get("taisho_char_count", 0),
        "match_signals": pair.get("match_signals", []),
        "title_score": pair.get("title_score"),
        "sanskrit_score": pair.get("sanskrit_score"),
        "nanjio_match": pair.get("nanjio_match"),
        "llm_verdict": pair.get("llm_verdict", ""),
        "llm_confidence": pair.get("llm_confidence", 0),
        "llm_reason": pair.get("llm_reason", ""),
        "llm_model": pair.get("llm_model", ""),
    }


def _write_review(
    results: dict,
    matches: list[dict],
    uncertain: list[dict],
    no_candidate_entries: list[dict] | None,
) -> None:
    """Write a human-readable review document."""
    lines: list[str] = []
    lines.append("# Tibetan-Chinese Concordance Matching Review")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    s = results["summary"]
    lines.append(f"- Total candidate pairs evaluated: {s['total_candidates']}")
    lines.append(f"- MATCH verdicts: {s['matches']}")
    lines.append(f"  - High confidence (>=90): {s['high_confidence']}")
    lines.append(f"  - Medium confidence (60-89): {s['medium_confidence']}")
    lines.append(f"  - Low confidence (<60): {s['low_confidence']}")
    lines.append(f"- NO_MATCH verdicts: {s['no_match']}")
    lines.append(f"- UNCERTAIN/ERROR: {s['uncertain']}")
    lines.append(f"- New Taisho texts with Tibetan parallels: {s['unique_new_taisho']}")
    lines.append(f"- New CBETA entries matched: {s['unique_new_cbeta']}")
    lines.append("")

    if "no_candidate_entries" in results:
        nc = results["no_candidate_entries"]
        lines.append("### Entries with no candidates")
        lines.append(f"- Total: {nc['total']}")
        lines.append(f"- Likely has Chinese parallel: {nc['likely_has_chinese_yes']}")
        lines.append(f"- Maybe has Chinese parallel: {nc['likely_has_chinese_maybe']}")
        lines.append(f"- Unlikely: {nc['likely_has_chinese_no']}")
        lines.append("")

    # High-confidence matches (auto-accept)
    high_conf = [m for m in matches if m.get("llm_confidence", 0) >= 90]
    if high_conf:
        lines.append("## High-Confidence Matches (auto-accept)")
        lines.append("")
        for m in sorted(high_conf, key=lambda x: x["taisho_id"]):
            lines.append(
                f"- **{m['taisho_id']}** ({m.get('taisho_title', '')}) "
                f"<-> CBETA #{m['cbeta_id']} ({m.get('tibetan_chinese_title', '')})"
            )
            lines.append(f"  - Confidence: {m.get('llm_confidence', 0)}%")
            lines.append(f"  - Signals: {', '.join(m.get('match_signals', []))}")
            lines.append(f"  - Reason: {m.get('llm_reason', '')}")
        lines.append("")

    # Medium-confidence matches (needs review)
    med_conf = [m for m in matches if 60 <= m.get("llm_confidence", 0) < 90]
    if med_conf:
        lines.append("## Medium-Confidence Matches (review recommended)")
        lines.append("")
        for m in sorted(med_conf, key=lambda x: -x.get("llm_confidence", 0)):
            lines.append(
                f"- **{m['taisho_id']}** ({m.get('taisho_title', '')}) "
                f"<-> CBETA #{m['cbeta_id']} ({m.get('tibetan_chinese_title', '')})"
            )
            lines.append(f"  - Confidence: {m.get('llm_confidence', 0)}%")
            lines.append(f"  - Signals: {', '.join(m.get('match_signals', []))}")
            lines.append(f"  - Reason: {m.get('llm_reason', '')}")
            if m.get("tibetan_sanskrit_title"):
                lines.append(f"  - Sanskrit: {m['tibetan_sanskrit_title']}")
        lines.append("")

    # Low-confidence matches (manual evaluation)
    low_conf = [m for m in matches if m.get("llm_confidence", 0) < 60]
    if low_conf:
        lines.append("## Low-Confidence Matches (manual evaluation needed)")
        lines.append("")
        for m in sorted(low_conf, key=lambda x: -x.get("llm_confidence", 0)):
            lines.append(
                f"- **{m['taisho_id']}** ({m.get('taisho_title', '')}) "
                f"<-> CBETA #{m['cbeta_id']} ({m.get('tibetan_chinese_title', '')})"
            )
            lines.append(f"  - Confidence: {m.get('llm_confidence', 0)}%")
            lines.append(f"  - Reason: {m.get('llm_reason', '')}")
        lines.append("")

    # Uncertain cases
    if uncertain:
        lines.append("## Uncertain Cases")
        lines.append("")
        for u in uncertain[:50]:
            lines.append(
                f"- {u['taisho_id']} ({u.get('taisho_title', '')}) "
                f"<-> CBETA #{u['cbeta_id']} ({u.get('tibetan_chinese_title', '')})"
            )
            lines.append(f"  - Verdict: {u.get('llm_verdict', '?')}")
            lines.append(f"  - Reason: {u.get('llm_reason', '')}")
        if len(uncertain) > 50:
            lines.append(f"\n... and {len(uncertain) - 50} more uncertain cases")
        lines.append("")

    # No-candidate entries that likely have Chinese parallels
    if no_candidate_entries:
        likely_yes = [e for e in no_candidate_entries
                      if e.get("likely_has_chinese") == "YES"]
        if likely_yes:
            lines.append("## Entries Likely Having Chinese Parallels (no candidates found)")
            lines.append("")
            lines.append("These entries were classified as likely having Chinese "
                         "parallels but our pre-filter found no candidates. "
                         "They may need manual scholarly investigation.")
            lines.append("")
            for e in likely_yes[:30]:
                eid = e.get("id") or e.get("entry_number", "?")
                lines.append(
                    f"- CBETA #{eid}: {e.get('chinese_title', '')} "
                    f"({e.get('section', '')})"
                )
                if e.get("sanskrit_title"):
                    lines.append(f"  Sanskrit: {e['sanskrit_title']}")
                lines.append(f"  Reason: {e.get('classify_reason', '')}")
            if len(likely_yes) > 30:
                lines.append(f"\n... and {len(likely_yes) - 30} more")
            lines.append("")

    with open(OUTPUT_REVIEW_PATH, "w") as f:
        f.write("\n".join(lines))
    log.info("  Review written to %s", OUTPUT_REVIEW_PATH)


# ---------------------------------------------------------------------------
# Holdout Validation
# ---------------------------------------------------------------------------

def run_holdout_validation(
    tibetan_entries: dict[str, dict],
    taisho_meta: dict[str, dict],
    existing_mappings: dict[str, set[str]],
    holdout_fraction: float = 0.20,
    seed: int = 42,
) -> dict:
    """Validate pipeline by holding out known mappings and checking recall.

    Takes entries that HAVE Taisho refs, hides some, runs candidate generation,
    and checks if we recover them.
    """
    log.info("Running holdout validation (%.0f%% holdout)...", holdout_fraction * 100)

    # Collect entries that have Taisho references
    mapped_entries = {
        eid: entry for eid, entry in tibetan_entries.items()
        if entry.get("taisho")
    }
    log.info("  %d entries with known Taisho mappings", len(mapped_entries))

    # Random holdout
    rng = random.Random(seed)
    all_eids = sorted(mapped_entries.keys())
    holdout_count = max(1, int(len(all_eids) * holdout_fraction))
    holdout_eids = set(rng.sample(all_eids, holdout_count))

    log.info("  Holding out %d entries", len(holdout_eids))

    # Create fake "unmapped" entries by hiding taisho refs
    fake_unmapped = {}
    for eid in holdout_eids:
        entry = dict(mapped_entries[eid])
        true_taisho = entry["taisho"]
        entry["taisho"] = []  # hide the ground truth
        entry["_true_taisho"] = true_taisho
        fake_unmapped[eid] = entry

    # Temporarily replace in the tibetan entries dict
    original_entries = {}
    for eid, entry in fake_unmapped.items():
        original_entries[eid] = tibetan_entries[eid]
        tibetan_entries[eid] = entry

    try:
        # Run Stage 1 on holdout entries
        candidates = generate_candidates(
            tibetan_entries, taisho_meta, existing_mappings
        )
    finally:
        # Restore originals
        for eid, orig in original_entries.items():
            tibetan_entries[eid] = orig

    # Check recall: did we find the known mappings?
    candidate_pairs = {(c["cbeta_id"], c["taisho_id"]) for c in candidates}

    found = 0
    missed = 0
    missed_entries = []
    for eid in holdout_eids:
        true_taisho = mapped_entries[eid]["taisho"]
        any_found = False
        for t_raw in true_taisho:
            tid = _resolve_taisho_id(
                f"T{t_raw}" if not t_raw.startswith("T") else t_raw,
                taisho_meta,
            )
            if tid and (eid, tid) in candidate_pairs:
                any_found = True
                break
        if any_found:
            found += 1
        else:
            missed += 1
            missed_entries.append({
                "cbeta_id": eid,
                "true_taisho": true_taisho,
                "chinese_title": mapped_entries[eid].get("chinese_title", ""),
                "section": mapped_entries[eid].get("section", ""),
            })

    recall = found / len(holdout_eids) if holdout_eids else 0.0
    log.info("  Holdout recall: %d/%d = %.1f%%", found, len(holdout_eids), recall * 100)
    if missed_entries:
        log.info("  Missed entries (first 10):")
        for m in missed_entries[:10]:
            log.info("    CBETA #%s → %s (%s, %s)",
                     m["cbeta_id"], m["true_taisho"],
                     m["chinese_title"], m["section"])

    return {
        "holdout_count": len(holdout_eids),
        "found": found,
        "missed": missed,
        "recall": round(recall, 4),
        "missed_entries": missed_entries[:20],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip LLM evaluation (mark all as UNCERTAIN)")
    parser.add_argument("--max-llm-pairs", type=int, default=None,
                        help="Max candidate pairs to send to LLM")
    parser.add_argument("--max-classify", type=int, default=None,
                        help="Max no-candidate entries to classify")
    parser.add_argument("--skip-holdout", action="store_true",
                        help="Skip holdout validation")
    parser.add_argument("--skip-classify", action="store_true",
                        help="Skip no-candidate classification")
    args = parser.parse_args()

    log.info("=" * 72)
    log.info("TIBETAN-CHINESE CONCORDANCE MATCHING PIPELINE")
    log.info("=" * 72)

    # Load data
    log.info("Loading data...")
    taisho_meta = load_taisho_metadata()
    tibetan_entries = load_cbeta_tibetan()
    existing_mappings = load_existing_mappings()
    log.info("  %d Taisho texts, %d Tibetan entries, %d existing mappings",
             len(taisho_meta), len(tibetan_entries), len(existing_mappings))

    # Holdout validation
    if not args.skip_holdout:
        holdout = run_holdout_validation(
            tibetan_entries, taisho_meta, existing_mappings
        )
    else:
        holdout = None

    # Stage 1: Candidate generation
    candidates = generate_candidates(
        tibetan_entries, taisho_meta, existing_mappings
    )

    # Stage 2: Feature extraction
    enriched = extract_features(candidates, tibetan_entries, taisho_meta)

    # Identify entries with no candidates (for classification)
    unmapped_eids = {
        eid for eid, entry in tibetan_entries.items()
        if not entry.get("taisho")
    }
    matched_eids = {c["cbeta_id"] for c in candidates}
    no_cand_eids = unmapped_eids - matched_eids
    no_cand_entries = [tibetan_entries[eid] for eid in sorted(no_cand_eids)]
    log.info("  %d unmapped entries have no candidates", len(no_cand_entries))

    # Stage 3: LLM evaluation
    evaluated = run_llm_evaluation(
        enriched,
        max_pairs=args.max_llm_pairs,
        dry_run=args.dry_run,
    )

    # Stage 3b: Classify no-candidate entries
    classified_no_cand = None
    if not args.skip_classify and not args.dry_run:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            client = anthropic.Anthropic(api_key=api_key)
            classified_no_cand = classify_no_candidates(
                no_cand_entries,
                client=client,
                max_classify=args.max_classify,
            )
    elif not args.skip_classify:
        classified_no_cand = classify_no_candidates(
            no_cand_entries, dry_run=True
        )

    # Stage 4: Validation and output
    results = validate_and_output(
        evaluated,
        tibetan_entries,
        existing_mappings,
        no_candidate_entries=classified_no_cand,
    )

    # Print final summary
    print()
    print("=" * 72)
    print("FINAL SUMMARY")
    print("=" * 72)
    s = results["summary"]
    print(f"  Candidate pairs evaluated:      {s['total_candidates']:>6}")
    print(f"  MATCH verdicts:                 {s['matches']:>6}")
    print(f"    High confidence (>=90):       {s['high_confidence']:>6}")
    print(f"    Medium confidence (60-89):    {s['medium_confidence']:>6}")
    print(f"    Low confidence (<60):         {s['low_confidence']:>6}")
    print(f"  NO_MATCH verdicts:              {s['no_match']:>6}")
    print(f"  UNCERTAIN/ERROR:                {s['uncertain']:>6}")
    print(f"  New Taisho texts matched:       {s['unique_new_taisho']:>6}")
    print(f"  New CBETA entries matched:      {s['unique_new_cbeta']:>6}")
    print()

    if holdout:
        print(f"  Holdout validation:")
        print(f"    Recall: {holdout['found']}/{holdout['holdout_count']} "
              f"= {holdout['recall']:.1%}")
        print()

    print(f"  Output: {OUTPUT_MATCHES_PATH}")
    print(f"  Review: {OUTPUT_REVIEW_PATH}")
    print("=" * 72)


if __name__ == "__main__":
    main()
