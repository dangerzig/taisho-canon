#!/usr/bin/env python3
"""Merge Tohoku-to-Otani concordance into the expanded cross-reference.

For each Taisho text in cross_reference_expanded.json that has Tohoku numbers
in its tibetan_parallels, this script looks up the corresponding Otani numbers
from the rKTs-derived concordance and adds any new ones.

Input:
  - results/cross_reference_expanded.json (existing expanded concordance)
  - results/tohoku_otani_concordance.json (Toh->Otani mapping from rKTs)

Output:
  - results/cross_reference_expanded.json (updated in place)
"""

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
CONCORDANCE_PATH = RESULTS_DIR / "cross_reference_expanded.json"
TOH_OTANI_PATH = RESULTS_DIR / "tohoku_otani_concordance.json"


def load_toh_otani_concordance(path):
    """Load the Tohoku-to-Otani concordance.

    Returns:
        Dict mapping "Toh N" -> list of "Otani M" strings.
    """
    with open(path) as f:
        data = json.load(f)
    return data["concordance"]


def merge_otani_numbers(concordance_path, toh_otani):
    """Merge new Otani numbers into the expanded concordance.

    Args:
        concordance_path: Path to cross_reference_expanded.json.
        toh_otani: Dict mapping "Toh N" -> list of "Otani M" strings.

    Returns:
        Tuple of (texts_updated, new_otani_added, new_otani_texts).
        - texts_updated: number of Taisho texts that received new Otani numbers
        - new_otani_added: total number of new Otani entries added
        - new_otani_texts: number of Taisho texts that had NO Otani before and now do
    """
    with open(concordance_path) as f:
        data = json.load(f)

    tibetan = data.get("tibetan_parallels", {})

    texts_updated = 0
    new_otani_added = 0
    new_otani_texts = 0  # texts that had zero Otani before, now have some

    for text_id, parallels in tibetan.items():
        # Find Tohoku numbers in this text's parallels
        toh_numbers = [p for p in parallels if p.startswith("Toh ")]
        if not toh_numbers:
            continue

        # Check if this text already has any Otani numbers
        existing_otani = {p for p in parallels if p.startswith("Otani ")}
        had_otani = len(existing_otani) > 0

        # Look up corresponding Otani numbers for each Tohoku number
        new_otani = set()
        for toh in toh_numbers:
            for otani in toh_otani.get(toh, []):
                if otani not in existing_otani:
                    new_otani.add(otani)

        if new_otani:
            # Add new Otani numbers and re-sort
            parallels_set = set(parallels)
            parallels_set.update(new_otani)
            tibetan[text_id] = sorted(parallels_set)
            texts_updated += 1
            new_otani_added += len(new_otani)
            if not had_otani:
                new_otani_texts += 1

    # Update sources tracking
    if "sources" not in data:
        data["sources"] = {}
    data["sources"]["rkts_otani"] = texts_updated

    # Recount Otani stats in summary
    with_otani = sum(
        1 for parallels in tibetan.values()
        if any(p.startswith("Otani ") for p in parallels)
    )

    # Write back
    with open(concordance_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return texts_updated, new_otani_added, new_otani_texts, with_otani


def main():
    print("Merging Tohoku-to-Otani concordance into expanded cross-reference")
    print("=" * 60)

    if not TOH_OTANI_PATH.exists():
        print(f"ERROR: {TOH_OTANI_PATH} not found.")
        print("Run build_otani_concordance.py first.")
        sys.exit(1)

    if not CONCORDANCE_PATH.exists():
        print(f"ERROR: {CONCORDANCE_PATH} not found.")
        sys.exit(1)

    # Load concordance
    toh_otani = load_toh_otani_concordance(TOH_OTANI_PATH)
    print(f"  Loaded Toh->Otani concordance: {len(toh_otani)} Tohoku numbers")

    # Pre-merge stats
    with open(CONCORDANCE_PATH) as f:
        pre_data = json.load(f)
    pre_tibetan = pre_data.get("tibetan_parallels", {})
    pre_otani_texts = sum(
        1 for parallels in pre_tibetan.values()
        if any(p.startswith("Otani ") for p in parallels)
    )
    pre_otani_total = sum(
        sum(1 for p in parallels if p.startswith("Otani "))
        for parallels in pre_tibetan.values()
    )
    print(f"  Pre-merge: {pre_otani_texts} Taisho texts with Otani numbers")
    print(f"  Pre-merge: {pre_otani_total} total Otani entries")

    # Merge
    texts_updated, new_otani_added, new_otani_texts, with_otani = merge_otani_numbers(
        CONCORDANCE_PATH, toh_otani
    )

    # Post-merge stats
    with open(CONCORDANCE_PATH) as f:
        post_data = json.load(f)
    post_tibetan = post_data.get("tibetan_parallels", {})
    post_otani_total = sum(
        sum(1 for p in parallels if p.startswith("Otani "))
        for parallels in post_tibetan.values()
    )

    print(f"\n{'=' * 60}")
    print("MERGE RESULTS")
    print(f"{'=' * 60}")
    print(f"  Taisho texts updated:                {texts_updated}")
    print(f"  New Otani entries added:              {new_otani_added}")
    print(f"  Texts that gained first Otani number: {new_otani_texts}")
    print(f"  Post-merge Taisho texts with Otani:  {with_otani}")
    print(f"  Post-merge total Otani entries:       {post_otani_total}")
    print(f"\n  Delta: +{new_otani_added} Otani entries across {texts_updated} texts")

    print(f"\nUpdated {CONCORDANCE_PATH}")


if __name__ == "__main__":
    main()
