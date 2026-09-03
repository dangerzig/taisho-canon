#!/usr/bin/env python3
"""Threshold-sensitivity sweep for the MITRA coverage filter (RET paper,
Table: tab:sensitivity). Runs the coverage filter over a grid of Chinese-side
(covC) and Tibetan-side (covT) thresholds WITHOUT the novelty filter, over the
Indic-derived canon (base-text pairs, >=4 aligned sentences, as in the
validation figure), and reports the catalog-overlap rate at each. Shows the
0.30/0.80 operating point is not tuned to maximize catalog recovery.

Reads /tmp/edge_bidir.json (from mitra_bidirectional_coverage.py) and
results/cross_reference_expanded.json.
"""
import json, re
def base(t): return re.sub(r'([A-Za-z]|_\d+)+$', '', t)
def vol(t):
    m = re.match(r'T(\d+)n', t); return int(m.group(1)) if m else 99
def canon(t): return vol(t) <= 32 or vol(t) == 85
def tn(s):
    m = re.search(r'(\d+)', s); return m.group(1) if m else ''

bidir = json.load(open('/tmp/edge_bidir.json'))
conc = json.load(open('results/cross_reference_expanded.json'))['tibetan_parallels']
have = set((base(k), 'Toh ' + tn(x)) for k, v in conc.items()
           for x in v if x.startswith('Toh '))
pool = [r for r in bidir.values() if canon(r['taisho']) and r['sents'] >= 4]

def measure(tC, tT):
    seen = set(); flagged = known = 0
    for r in pool:
        if not ((r.get('chi_cov') or 0) >= tC or (r.get('tib_cov') or 0) >= tT):
            continue
        k = (base(r['taisho']), 'Toh ' + tn(r['toh']))
        if k in seen:
            continue
        seen.add(k); flagged += 1
        if k in have:
            known += 1
    ov = 100 * known / flagged if flagged else 0
    return flagged, known, flagged - known, ov

print(f"{'covC':>5} {'covT':>5} | {'flag':>5} {'catal':>5} {'new':>4} {'ovlp%':>6}")
print('-' * 40)
for tT in (0.70, 0.80, 0.90):
    for tC in (0.20, 0.30, 0.40, 0.50, 0.60, 0.70):
        f, k, n, ov = measure(tC, tT)
        tag = ' <-- paper' if (tC, tT) == (0.30, 0.80) else ''
        print(f"{tC:5.2f} {tT:5.2f} | {f:5d} {k:5d} {n:4d} {ov:5.1f}%{tag}")
    print()
