import json, os, re
from collections import defaultdict
TSV = os.path.expanduser('~/taisho-canon/data/mitra-parallel/mitra-parallel/tsv')
def cjk_f(s): return sum(1 for c in s if '一' <= c <= '鿿') / max(1, len(s))
def tib_f(s): return sum(1 for c in s if 'ༀ' <= c <= '࿿') / max(1, len(s))
def tiblen(s): return sum(1 for c in s if 'ༀ' <= c <= '࿿')
TA = re.compile(r'T(\d{2})n(\d{4}[A-Za-z]?)')
DE = re.compile(r'D(\d{4})')

pair_chi = defaultdict(dict)   # (taisho,toh) -> {chi_segid: nchars}
pair_tib = defaultdict(dict)   # (taisho,toh) -> {tib_segid: ntibchars}
toh_len  = defaultdict(dict)   # toh -> {tib_segid: ntibchars}  (from ALL rows w/ Tibetan)

files = sorted(os.listdir(TSV))
for i, fn in enumerate(files):
    if (i + 1) % 3000 == 0: print(f"  {i+1}/{len(files)}")
    try:
        fh = open(os.path.join(TSV, fn), encoding='utf-8')
    except OSError:
        continue
    with fh:
        fh.readline()
        for line in fh:
            p = line.rstrip('\n').split('\t')
            if len(p) < 4: continue
            s_id, s_tx, t_id, t_tx = p[0], p[1], p[2], p[3]
            # record Toh length from ANY tibetan-bearing column
            for sid, tx in ((s_id, s_tx), (t_id, t_tx)):
                if tib_f(tx) > 0.3:
                    dm = DE.search(sid)
                    if dm: toh_len[int(dm.group(1))][sid] = tiblen(tx)
            if not s_tx.strip() or not t_tx.strip(): continue
            if cjk_f(s_tx) > 0.3 and tib_f(t_tx) > 0.3:
                ch_id, ch_tx, tb_id, tb_tx = s_id, s_tx, t_id, t_tx
            elif cjk_f(t_tx) > 0.3 and tib_f(s_tx) > 0.3:
                ch_id, ch_tx, tb_id, tb_tx = t_id, t_tx, s_id, s_tx
            else:
                continue
            tm = TA.search(ch_id); dm = DE.search(tb_id)
            if not tm or not dm: continue
            key = (f"T{tm.group(1)}n{tm.group(2)}", int(dm.group(1)))
            pair_chi[key][ch_id] = len(ch_tx.replace(' ', ''))
            pair_tib[key][tb_id] = tiblen(tb_tx)

meta = {m['text_id']: m for m in json.load(open(os.path.expanduser('~/taisho-canon/data/metadata.json')))}
toh_total = {toh: sum(d.values()) for toh, d in toh_len.items()}
out = {}
for key in pair_chi:
    tais, toh = key
    chi_al = sum(pair_chi[key].values())
    tib_al = sum(pair_tib[key].values())
    cc = meta.get(tais, {}).get('char_count', 0)
    tt = toh_total.get(toh, 0)
    chi_cov = round(chi_al / cc, 3) if cc else None
    tib_cov = round(tib_al / tt, 3) if tt else None
    out[f"{tais}|Toh {toh}"] = {
        "taisho": tais, "toh": f"Toh {toh}", "sents": len(pair_chi[key]),
        "chi_cov": chi_cov, "tib_cov": tib_cov,
        "max_cov": max([c for c in (chi_cov, tib_cov) if c is not None], default=None),
        "title": meta.get(tais, {}).get('title', '')}
json.dump(out, open('/tmp/edge_bidir.json', 'w'), ensure_ascii=False)
print(f"\nBuilt bidirectional features for {len(out)} pairs -> /tmp/edge_bidir.json")
