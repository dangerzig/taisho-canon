#!/usr/bin/env python3
"""Final coverage-verified harvest of new Chinese<->Tibetan parallels from MITRA.

Pipeline (see the RET concordance paper, sec. Sentence-Level Alignment):
  1. mitra_bidirectional_coverage.py -> /tmp/edge_bidir.json  (per-pair chi/tib coverage)
  2. this script: restrict to Indic-derived canon (Taisho vols 1-32, 85),
     drop pairs already in the concordance (id-normalized), and accept a pair
     when covC>=0.30 (exact CBETA length) OR covT>=0.80 (estimated length,
     stricter bar). Yields 169 verified parallels, 132 texts, 53 newly linked.
Writes results/mitra_verified_new_parallels.json.
"""
import json, re
def base(t): return re.sub(r'([A-Za-z]|_\d+)+$','',t)
def vol(t):
    m=re.match(r'T(\d+)n',t); return int(m.group(1)) if m else 99
def canon(t): return vol(t)<=32 or vol(t)==85
def tn(s):
    m=re.search(r'(\d+)',s); return m.group(1) if m else ''
bidir=json.load(open('/tmp/edge_bidir.json'))
conc=json.load(open('results/cross_reference_expanded.json'))['tibetan_parallels']
meta={m['text_id']:m for m in json.load(open('data/metadata.json'))}
have=set((base(k),'Toh '+tn(x)) for k,v in conc.items() for x in v if x.startswith('Toh '))
concbase=set(base(k) for k in conc)
sel=[r for r in bidir.values() if canon(r['taisho']) and r['sents']>=4
     and (base(r['taisho']),'Toh '+tn(r['toh'])) not in have
     and ((r.get('chi_cov') or 0)>=0.30 or (r.get('tib_cov') or 0)>=0.80)]
u=set(base(r['taisho']) for r in sel); nn=[t for t in u if t not in concbase]
res=[{"taisho":r['taisho'],"toh":r['toh'],"chinese_coverage":r.get('chi_cov'),
      "tibetan_coverage":r.get('tib_cov'),"aligned_sentences":r['sents'],
      "title":meta.get(r['taisho'],{}).get('title','')}
     for r in sorted(sel,key=lambda r:-max((r.get('chi_cov') or 0),(r.get('tib_cov') or 0)))]
json.dump({"count":len(res),"distinct_taisho":len(u),"net_new_texts":len(nn),"parallels":res},
          open('results/mitra_verified_new_parallels.json','w'),ensure_ascii=False,indent=1)
print(f"{len(res)} verified parallels, {len(u)} texts, {len(nn)} newly linked")
