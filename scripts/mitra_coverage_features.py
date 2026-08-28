import json, os, re
from collections import defaultdict
TSV = os.path.expanduser('~/taisho-canon/data/mitra-parallel/mitra-parallel/tsv')
def cjk_f(s): return sum(1 for c in s if '一' <= c <= '鿿') / max(1, len(s))
def tib_f(s): return sum(1 for c in s if 'ༀ' <= c <= '࿿') / max(1, len(s))
TA = re.compile(r'T(\d{2})n(\d{4}[A-Za-z]?)')
DE = re.compile(r'D(\d{4})')

seg_chars = defaultdict(dict)   # (taisho,toh) -> {chinese_segid: nchars}
sents = defaultdict(int)
files = sorted(os.listdir(TSV))
for i, fn in enumerate(files):
    if (i + 1) % 3000 == 0:
        print(f"  {i+1}/{len(files)}")
    try:
        fh = open(os.path.join(TSV, fn), encoding='utf-8')
    except OSError:
        continue
    with fh:
        fh.readline()
        for line in fh:
            p = line.rstrip('\n').split('\t')
            if len(p) < 4:
                continue
            s_id, s_tx, t_id, t_tx = p[0], p[1], p[2], p[3]
            if not s_tx.strip() or not t_tx.strip():
                continue
            if cjk_f(s_tx) > 0.3 and tib_f(t_tx) > 0.3:
                ch_id, ch_tx, tib_id = s_id, s_tx, t_id
            elif cjk_f(t_tx) > 0.3 and tib_f(s_tx) > 0.3:
                ch_id, ch_tx, tib_id = t_id, t_tx, s_id
            else:
                continue
            tm = TA.search(ch_id)
            dm = DE.search(tib_id)
            if not tm or not dm:
                continue
            key = (f"T{tm.group(1)}n{tm.group(2)}", int(dm.group(1)))
            seg_chars[key][ch_id] = len(ch_tx.replace(' ', ''))
            sents[key] += 1

meta = {m['text_id']: m for m in json.load(open('data/metadata.json'))}
out = {}
for key, segs in seg_chars.items():
    tais, toh = key
    aligned = sum(segs.values())
    m = meta.get(tais, {})
    cc = m.get('char_count', 0)
    out[f"{tais}|Toh {toh}"] = {
        "taisho": tais, "toh": f"Toh {toh}", "sents": sents[key],
        "aligned_chars": aligned, "char_count": cc,
        "coverage": round(aligned / cc, 3) if cc else None,
        "title": m.get('title', ''), "dharani": m.get('has_dharani', False)}
json.dump(out, open('/tmp/edge_features.json', 'w'), ensure_ascii=False)
print(f"\nBuilt features for {len(out)} Chinese-Tibetan pairs -> /tmp/edge_features.json")
