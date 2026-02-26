#!/usr/bin/env python3
"""Analyze tibetan_chinese_matches.json with filtered statistics."""

import json
import re
import sys
from collections import Counter

# ── Load data ──────────────────────────────────────────────────────────────

with open("results/tibetan_chinese_matches.json") as f:
    data = json.load(f)

with open("results/cross_reference_expanded.json") as f:
    xref = json.load(f)

matches = data["matches"]
summary = data["summary"]

# ── Helper: count CJK characters ──────────────────────────────────────────

def count_cjk(text):
    """Count CJK Unified Ideographs in a string."""
    return sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf')

# ── Identify "validated" taisho IDs (those already with Tibetan parallels) ─

existing_tibetan = set(xref.get("tibetan_parallels", {}).keys())

# ── Build cbeta_id frequency table ────────────────────────────────────────

cbeta_counts = Counter(m["cbeta_id"] for m in matches)

# ── Classify each match ──────────────────────────────────────────────────

generic_matches = []
genuine_matches = []

for m in matches:
    cbeta_id = m["cbeta_id"]
    chi_title = m.get("tibetan_chinese_title", "")
    skt_title = m.get("tibetan_sanskrit_title", "") or ""

    cjk_count = count_cjk(chi_title)
    total_matches_for_cbeta = cbeta_counts[cbeta_id]

    is_generic = False
    reasons = []

    # Condition 1: short Chinese title AND no Sanskrit title
    if cjk_count <= 5 and skt_title.strip() == "":
        is_generic = True
        reasons.append(f"short_title({cjk_count}_CJK)")

    # Condition 2: overly-matched cbeta_id
    if total_matches_for_cbeta > 10:
        is_generic = True
        reasons.append(f"over_matched(cbeta={cbeta_id},count={total_matches_for_cbeta})")

    m["_is_generic"] = is_generic
    m["_generic_reasons"] = reasons

    if is_generic:
        generic_matches.append(m)
    else:
        genuine_matches.append(m)

# ── Filtered statistics ──────────────────────────────────────────────────

total_genuine = len(genuine_matches)
high_conf = [m for m in genuine_matches if m["llm_confidence"] >= 90]
med_conf = [m for m in genuine_matches if 60 <= m["llm_confidence"] <= 89]
low_conf = [m for m in genuine_matches if m["llm_confidence"] < 60]

# Normalize taisho_id to bare form for comparison with cross_reference
def normalize_taisho(tid):
    """T05n0220 -> T05n0220 (already in this format in xref)."""
    return tid

# Unique new Taisho texts: those NOT already having Tibetan parallels
genuine_taisho_ids = set(m["taisho_id"] for m in genuine_matches)
new_taisho = genuine_taisho_ids - existing_tibetan
already_known_taisho = genuine_taisho_ids & existing_tibetan

# Unique new CBETA entries
genuine_cbeta_ids = set(m["cbeta_id"] for m in genuine_matches)

# ── Sanskrit signal analysis ─────────────────────────────────────────────

SANSKRIT_SIGNALS = {"sanskrit_exact", "sanskrit_fuzzy", "sanskrit_token"}

with_sanskrit = [m for m in genuine_matches
                 if SANSKRIT_SIGNALS & set(m.get("match_signals", []))]
without_sanskrit = [m for m in genuine_matches
                    if not (SANSKRIT_SIGNALS & set(m.get("match_signals", [])))]

# ── High-confidence genuine matches detail ───────────────────────────────

high_conf_sorted = sorted(high_conf, key=lambda m: -m["llm_confidence"])

# ── Overlap with existing known parallels ────────────────────────────────

# How many filtered matches have taisho_ids already in tibetan_parallels?
overlap_matches = [m for m in genuine_matches if m["taisho_id"] in existing_tibetan]
truly_new_matches = [m for m in genuine_matches if m["taisho_id"] not in existing_tibetan]

# ── Generic match breakdown ──────────────────────────────────────────────

generic_short = sum(1 for m in matches if count_cjk(m.get("tibetan_chinese_title", "")) <= 5
                    and (m.get("tibetan_sanskrit_title", "") or "").strip() == "")
generic_over = sum(1 for m in matches if cbeta_counts[m["cbeta_id"]] > 10)
generic_both = sum(1 for m in matches if (count_cjk(m.get("tibetan_chinese_title", "")) <= 5
                   and (m.get("tibetan_sanskrit_title", "") or "").strip() == "")
                   and cbeta_counts[m["cbeta_id"]] > 10)

# ── Build output ─────────────────────────────────────────────────────────

lines = []
def p(s=""):
    lines.append(s)
    print(s)

p("# Tibetan-Chinese Match Filtered Statistics")
p()
p(f"Generated from {len(matches)} total matches in tibetan_chinese_matches.json")
p()

p("## Generic Match Filtering")
p()
p(f"- Matches with short Chinese title (<=5 CJK) and no Sanskrit title: {generic_short}")
p(f"- Matches with over-matched CBETA ID (>10 matches): {generic_over}")
p(f"- Matches meeting both conditions: {generic_both}")
p(f"- **Total filtered out as generic: {len(generic_matches)}**")
p(f"- **Remaining genuine matches: {total_genuine}**")
p()

# Show which CBETA IDs are over-matched
over_matched_cbetas = {cid: cnt for cid, cnt in cbeta_counts.items() if cnt > 10}
if over_matched_cbetas:
    p("### Over-matched CBETA IDs (>10 matches each)")
    p()
    for cid, cnt in sorted(over_matched_cbetas.items(), key=lambda x: -x[1]):
        # Get a sample title
        sample = next(m for m in matches if m["cbeta_id"] == cid)
        chi_t = sample.get("tibetan_chinese_title", "")[:30]
        p(f"- CBETA {cid}: {cnt} matches — {chi_t}")
    p()

p("## 1. Filtered Totals")
p()
p(f"| Metric | Count |")
p(f"|--------|-------|")
p(f"| Total genuine matches | {total_genuine} |")
p(f"| High-confidence (>=90) | {len(high_conf)} |")
p(f"| Medium-confidence (60-89) | {len(med_conf)} |")
p(f"| Low-confidence (<60) | {len(low_conf)} |")
p(f"| Unique Taisho texts (genuine) | {len(genuine_taisho_ids)} |")
p(f"| Unique NEW Taisho texts (no existing Tibetan parallel) | {len(new_taisho)} |")
p(f"| Unique Taisho texts already with Tibetan parallels | {len(already_known_taisho)} |")
p(f"| Unique CBETA entries (genuine) | {len(genuine_cbeta_ids)} |")
p()

p("## 2. Sanskrit Title Evidence")
p()
p(f"| Category | Count | % of genuine |")
p(f"|----------|-------|--------------|")
p(f"| With Sanskrit signal (exact/fuzzy/token) | {len(with_sanskrit)} | {100*len(with_sanskrit)/total_genuine:.1f}% |")
p(f"| Purely Chinese-title matching | {len(without_sanskrit)} | {100*len(without_sanskrit)/total_genuine:.1f}% |")
p()

# Break down Sanskrit signals
skt_signal_counts = Counter()
for m in genuine_matches:
    for sig in m.get("match_signals", []):
        skt_signal_counts[sig] += 1
p("### Signal breakdown (all genuine matches)")
p()
for sig, cnt in skt_signal_counts.most_common():
    p(f"- {sig}: {cnt}")
p()

p("## 3. High-Confidence Genuine Matches (>=90)")
p()
p(f"Total: {len(high_conf)}")
p()
p("| # | taisho_id | taisho_title | cbeta_id | tibetan_chinese_title | tibetan_sanskrit_title | confidence | signals | reason |")
p("|---|-----------|-------------|----------|----------------------|----------------------|------------|---------|--------|")
for i, m in enumerate(high_conf_sorted, 1):
    tid = m["taisho_id"]
    tt = (m.get("taisho_title") or "")[:40]
    cid = m["cbeta_id"]
    ct = (m.get("tibetan_chinese_title") or "")[:30]
    st = (m.get("tibetan_sanskrit_title") or "")[:40]
    conf = m["llm_confidence"]
    sigs = ", ".join(m.get("match_signals", []))
    reason = (m.get("llm_reason") or "")[:80]
    new_flag = " **NEW**" if tid not in existing_tibetan else ""
    p(f"| {i} | {tid}{new_flag} | {tt} | {cid} | {ct} | {st} | {conf} | {sigs} | {reason} |")
p()

p("## 4. Overlap with Existing Tibetan Parallel Data")
p()
p(f"- Genuine matches confirming already-known parallels: {len(overlap_matches)} ({100*len(overlap_matches)/total_genuine:.1f}%)")
p(f"- Genuinely NEW matches (no prior Tibetan parallel): {len(truly_new_matches)} ({100*len(truly_new_matches)/total_genuine:.1f}%)")
p()

# Break down by confidence
truly_new_high = [m for m in truly_new_matches if m["llm_confidence"] >= 90]
truly_new_med = [m for m in truly_new_matches if 60 <= m["llm_confidence"] <= 89]
p(f"### Genuinely new matches by confidence")
p()
p(f"| Confidence | Count |")
p(f"|------------|-------|")
p(f"| High (>=90) | {len(truly_new_high)} |")
p(f"| Medium (60-89) | {len(truly_new_med)} |")
p()

# List the new high-confidence ones specifically
if truly_new_high:
    p("### New high-confidence matches (not in any existing concordance)")
    p()
    for m in sorted(truly_new_high, key=lambda m: -m["llm_confidence"]):
        tid = m["taisho_id"]
        tt = m.get("taisho_title", "")
        ct = m.get("tibetan_chinese_title", "")
        st = m.get("tibetan_sanskrit_title", "") or ""
        conf = m["llm_confidence"]
        sigs = ", ".join(m.get("match_signals", []))
        p(f"- **{tid}** ({tt}) <-> CBETA {m['cbeta_id']} ({ct}) [conf={conf}, {sigs}]")
        if st:
            p(f"  Sanskrit: {st}")
    p()

# ── Write to file ────────────────────────────────────────────────────────

output_path = "reviews/tibetan_match_filtered_stats.md"
with open(output_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"\n--- Written to {output_path} ---")
