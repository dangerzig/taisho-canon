#!/usr/bin/env python3
"""Cross-reference digest detection results against multi-canon concordance.

Loads results/digest_relationships.json and results/cross_reference.json,
then computes:
  - Retranslation validation via shared Tohoku/Otani numbers
  - Parallel coverage by classification type
  - Same-parallel, different-parallel, and no-parallel pair breakdowns
  - Overall concordance statistics

Outputs results as JSON to results/cross_reference_analysis.json.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
DIGEST_PATH = RESULTS_DIR / "digest_relationships.json"
XREF_PATH = RESULTS_DIR / "cross_reference.json"
OUTPUT_PATH = RESULTS_DIR / "cross_reference_analysis.json"


def load_data():
    with open(DIGEST_PATH) as f:
        relationships = json.load(f)
    with open(XREF_PATH) as f:
        xref = json.load(f)
    return relationships, xref


def build_parallel_lookup(xref):
    """Build a unified lookup: text_id -> {tibetan: [...], pali: [...], sanskrit: ...}."""
    lookup = {}
    all_ids = set()

    for section, key in [
        ("tibetan_parallels", "tibetan"),
        ("pali_parallels", "pali"),
        ("sanskrit_parallels", "sanskrit"),
    ]:
        for text_id, parallels in xref[section].items():
            all_ids.add(text_id)
            if text_id not in lookup:
                lookup[text_id] = {"tibetan": [], "pali": [], "sanskrit": []}
            if isinstance(parallels, list):
                lookup[text_id][key] = parallels
            else:
                # sanskrit_parallels can be a string
                lookup[text_id][key] = [parallels] if parallels else []

    return lookup, all_ids


def normalize_id(text_id):
    """Strip trailing letter suffixes (A/B/a/b/c) for cross-reference lookup.

    Digest IDs like T20n1134B or T02n0128b have sub-text suffixes that
    won't match the cross-reference, which uses base IDs like T20n1134.
    """
    return re.sub(r"[A-Za-z]+$", "", text_id)


def get_parallels(text_id, lookup):
    """Look up parallels for a text, trying exact match then normalized ID."""
    if text_id in lookup:
        return lookup[text_id]
    norm = normalize_id(text_id)
    if norm in lookup:
        return lookup[norm]
    return None


def extract_tohoku_numbers(parallels):
    """Extract Tohoku (Toh) and Otani numbers from a list of Tibetan parallels."""
    toh = set()
    otani = set()
    if not parallels:
        return toh, otani
    for p in parallels:
        if p.startswith("Toh "):
            toh.add(p)
        elif p.startswith("Otani "):
            otani.add(p)
    return toh, otani


def analyze_retranslation_validation(retranslations, lookup):
    """Check how many retranslation pairs share Tohoku/Otani numbers."""
    validated = []
    different_parallels = []
    one_has_parallel = []
    neither_has_parallel = []

    for rel in retranslations:
        digest_p = get_parallels(rel["digest_id"], lookup)
        source_p = get_parallels(rel["source_id"], lookup)

        digest_tib = digest_p["tibetan"] if digest_p else []
        source_tib = source_p["tibetan"] if source_p else []

        digest_toh, digest_otani = extract_tohoku_numbers(digest_tib)
        source_toh, source_otani = extract_tohoku_numbers(source_tib)

        common_toh = digest_toh & source_toh
        common_otani = digest_otani & source_otani

        if common_toh or common_otani:
            validated.append({
                "digest_id": rel["digest_id"],
                "source_id": rel["source_id"],
                "coverage": rel["coverage"],
                "confidence": rel["confidence"],
                "shared_tohoku": sorted(common_toh),
                "shared_otani": sorted(common_otani),
            })
        elif digest_tib and source_tib:
            different_parallels.append(
                {
                    "digest_id": rel["digest_id"],
                    "source_id": rel["source_id"],
                    "coverage": rel["coverage"],
                    "confidence": rel["confidence"],
                    "digest_tibetan": digest_tib,
                    "source_tibetan": source_tib,
                }
            )
        elif digest_tib or source_tib:
            one_has_parallel.append(
                {
                    "digest_id": rel["digest_id"],
                    "source_id": rel["source_id"],
                    "coverage": rel["coverage"],
                    "has_parallel": (
                        rel["digest_id"] if digest_tib else rel["source_id"]
                    ),
                }
            )
        else:
            neither_has_parallel.append(
                {
                    "digest_id": rel["digest_id"],
                    "source_id": rel["source_id"],
                    "coverage": rel["coverage"],
                }
            )

    # Count how many validated pairs have Toh vs Otani
    n_with_toh = sum(1 for v in validated if v["shared_tohoku"])
    n_with_otani = sum(1 for v in validated if v["shared_otani"])

    return {
        "total_retranslations": len(retranslations),
        "validated_by_shared_tibetan_id": len(validated),
        "validated_with_tohoku": n_with_toh,
        "validated_with_otani": n_with_otani,
        "different_tibetan_parallels": len(different_parallels),
        "one_has_tibetan": len(one_has_parallel),
        "neither_has_tibetan": len(neither_has_parallel),
        "validated_pairs": sorted(
            validated,
            key=lambda x: x["confidence"],
            reverse=True,
        ),
        "different_parallel_pairs": sorted(
            different_parallels,
            key=lambda x: x["confidence"],
            reverse=True,
        ),
    }


def analyze_coverage_by_classification(relationships, lookup):
    """Compute parallel coverage rates by classification type."""
    stats = defaultdict(lambda: {"total": 0, "has_any": 0, "has_tibetan": 0,
                                 "has_pali": 0, "has_sanskrit": 0})

    for rel in relationships:
        cls = rel["classification"]
        stats[cls]["total"] += 1

        # Check both texts in the pair
        for text_id in [rel["digest_id"], rel["source_id"]]:
            p = get_parallels(text_id, lookup)
            if p:
                stats[cls]["has_any"] += 1
                if p["tibetan"]:
                    stats[cls]["has_tibetan"] += 1
                if p["pali"]:
                    stats[cls]["has_pali"] += 1
                if p["sanskrit"]:
                    stats[cls]["has_sanskrit"] += 1
                break  # Count per relationship, not per text
        else:
            # Neither text has parallels — already counted in total
            pass

    # Convert to serializable dict with percentages
    result = {}
    for cls in ["full_digest", "partial_digest", "retranslation",
                 "commentary", "shared_tradition"]:
        s = stats[cls]
        total = s["total"]
        result[cls] = {
            "total": total,
            "has_any_parallel": s["has_any"],
            "pct_any": round(100 * s["has_any"] / total, 1) if total else 0,
            "has_tibetan": s["has_tibetan"],
            "pct_tibetan": round(100 * s["has_tibetan"] / total, 1) if total else 0,
            "has_pali": s["has_pali"],
            "pct_pali": round(100 * s["has_pali"] / total, 1) if total else 0,
            "has_sanskrit": s["has_sanskrit"],
            "pct_sanskrit": round(100 * s["has_sanskrit"] / total, 1) if total else 0,
        }
    return result


def analyze_pair_parallel_status(relationships, lookup):
    """Classify each relationship by whether both/one/neither text has parallels,
    and whether shared parallels point to the same Tibetan source."""
    both_have = 0
    same_tibetan = []
    different_tibetan = []
    only_digest = 0
    only_source = 0
    neither = 0

    for rel in relationships:
        dp = get_parallels(rel["digest_id"], lookup)
        sp = get_parallels(rel["source_id"], lookup)

        d_has = dp is not None
        s_has = sp is not None

        if d_has and s_has:
            both_have += 1
            # Check for shared Tibetan parallels
            d_tib = set(dp["tibetan"]) if dp["tibetan"] else set()
            s_tib = set(sp["tibetan"]) if sp["tibetan"] else set()
            common = d_tib & s_tib
            if common:
                same_tibetan.append({
                    "digest_id": rel["digest_id"],
                    "source_id": rel["source_id"],
                    "classification": rel["classification"],
                    "coverage": rel["coverage"],
                    "confidence": rel["confidence"],
                    "shared_tibetan": sorted(common),
                })
            elif d_tib and s_tib:
                different_tibetan.append({
                    "digest_id": rel["digest_id"],
                    "source_id": rel["source_id"],
                    "classification": rel["classification"],
                    "coverage": rel["coverage"],
                    "confidence": rel["confidence"],
                    "digest_tibetan": sorted(d_tib),
                    "source_tibetan": sorted(s_tib),
                })
        elif d_has:
            only_digest += 1
        elif s_has:
            only_source += 1
        else:
            neither += 1

    return {
        "total": len(relationships),
        "both_have_any_parallel": both_have,
        "only_digest_has_parallel": only_digest,
        "only_source_has_parallel": only_source,
        "neither_has_parallel": neither,
        "same_tibetan_parallel": len(same_tibetan),
        "different_tibetan_parallel": len(different_tibetan),
        "same_tibetan_pairs": sorted(
            same_tibetan, key=lambda x: x["confidence"], reverse=True
        ),
        "different_tibetan_pairs": sorted(
            different_tibetan, key=lambda x: x["confidence"], reverse=True
        )[:30],  # Top 30 for readability
    }


def analyze_unique_texts(relationships, lookup, xref_ids):
    """How many of the 1,412 unique texts in digest results have parallels?"""
    all_ids = set()
    for rel in relationships:
        all_ids.add(rel["digest_id"])
        all_ids.add(rel["source_id"])

    has_parallel = set()
    has_tibetan = set()
    has_pali = set()
    has_sanskrit = set()

    for text_id in all_ids:
        p = get_parallels(text_id, lookup)
        if p:
            has_parallel.add(text_id)
            if p["tibetan"]:
                has_tibetan.add(text_id)
            if p["pali"]:
                has_pali.add(text_id)
            if p["sanskrit"]:
                has_sanskrit.add(text_id)

    return {
        "total_unique_texts": len(all_ids),
        "with_any_parallel": len(has_parallel),
        "pct_any": round(100 * len(has_parallel) / len(all_ids), 1),
        "with_tibetan": len(has_tibetan),
        "pct_tibetan": round(100 * len(has_tibetan) / len(all_ids), 1),
        "with_pali": len(has_pali),
        "pct_pali": round(100 * len(has_pali) / len(all_ids), 1),
        "with_sanskrit": len(has_sanskrit),
        "pct_sanskrit": round(100 * len(has_sanskrit) / len(all_ids), 1),
    }


def main():
    relationships, xref = load_data()
    lookup, xref_ids = build_parallel_lookup(xref)

    print(f"Loaded {len(relationships)} digest relationships")
    print(f"Loaded {len(xref_ids)} texts with cross-canon parallels")
    print()

    # Separate retranslations
    retranslations = [r for r in relationships if r["classification"] == "retranslation"]

    # 1. Unique text coverage
    text_stats = analyze_unique_texts(relationships, lookup, xref_ids)
    print(f"Unique texts in digest results: {text_stats['total_unique_texts']}")
    print(f"  With any parallel: {text_stats['with_any_parallel']} ({text_stats['pct_any']}%)")
    print(f"  With Tibetan: {text_stats['with_tibetan']} ({text_stats['pct_tibetan']}%)")
    print(f"  With Pali: {text_stats['with_pali']} ({text_stats['pct_pali']}%)")
    print(f"  With Sanskrit: {text_stats['with_sanskrit']} ({text_stats['pct_sanskrit']}%)")
    print()

    # 2. Retranslation validation
    retrans_validation = analyze_retranslation_validation(retranslations, lookup)
    print(f"Retranslation validation:")
    print(f"  Total retranslations: {retrans_validation['total_retranslations']}")
    print(f"  Validated (shared Tibetan ID): {retrans_validation['validated_by_shared_tibetan_id']}")
    print(f"    With shared Tohoku: {retrans_validation['validated_with_tohoku']}")
    print(f"    With shared Otani: {retrans_validation['validated_with_otani']}")
    print(f"  Different Tibetan parallels: {retrans_validation['different_tibetan_parallels']}")
    print(f"  Only one has Tibetan: {retrans_validation['one_has_tibetan']}")
    print(f"  Neither has Tibetan: {retrans_validation['neither_has_tibetan']}")
    print()

    # 3. Coverage by classification
    cls_coverage = analyze_coverage_by_classification(relationships, lookup)
    print("Coverage by classification (at least one text in pair has parallel):")
    for cls in ["full_digest", "partial_digest", "retranslation",
                 "commentary", "shared_tradition"]:
        s = cls_coverage[cls]
        print(f"  {cls}: {s['has_any_parallel']}/{s['total']} ({s['pct_any']}%)")
    print()

    # 4. Pair-level parallel analysis
    pair_status = analyze_pair_parallel_status(relationships, lookup)
    print(f"Pair-level parallel status:")
    print(f"  Both texts have parallels: {pair_status['both_have_any_parallel']}")
    print(f"  Only digest has parallel: {pair_status['only_digest_has_parallel']}")
    print(f"  Only source has parallel: {pair_status['only_source_has_parallel']}")
    print(f"  Neither has parallel: {pair_status['neither_has_parallel']}")
    print(f"  Same Tibetan parallel: {pair_status['same_tibetan_parallel']}")
    print(f"  Different Tibetan parallels: {pair_status['different_tibetan_parallel']}")
    print()

    # Top validated retranslation pairs
    if retrans_validation["validated_pairs"]:
        print("Top validated retranslation pairs (shared Tibetan ID):")
        for p in retrans_validation["validated_pairs"][:10]:
            toh = p.get("shared_tohoku", [])
            otani = p.get("shared_otani", [])
            shared = ", ".join(toh + otani)
            print(f"  {p['digest_id']} <-> {p['source_id']}: "
                  f"coverage={p['coverage']:.1%}, shared={shared}")
        print()

    # Save full results
    output = {
        "unique_text_coverage": text_stats,
        "retranslation_validation": retrans_validation,
        "coverage_by_classification": cls_coverage,
        "pair_parallel_status": pair_status,
        "concordance_summary": xref["summary"],
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Full results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
