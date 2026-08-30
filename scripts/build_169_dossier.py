import json, os, re
from collections import defaultdict

RES='results'
p169=json.load(open(f'{RES}/mitra_verified_new_parallels.json'))['parallels']
def tohint(s):
    m=re.search(r'(\d+)',s); return int(m.group(1)) if m else None
keys={}  # (taisho_norm, tohint) -> parallel dict
def norm_t(t): 
    m=re.match(r'T0*(\d+)n0*(\d+)',t) or re.match(r'T(\d+)n(\d+)',t)
    return t
for par in p169:
    keys[(par['taisho'], tohint(par['toh']))]=par

# ---- Toh title lookups ----
toh_titles=defaultdict(dict)
cj=json.load(open(f'{RES}/cbeta_jinglu_tibetan.json'))['entries']
for e in (cj.values() if isinstance(cj,dict) else cj):
    n=e.get('entry_number')
    if n is not None:
        d=toh_titles[n]
        d.setdefault('cbeta_skt', e.get('sanskrit_title'))
        d.setdefault('cbeta_tib', e.get('tibetan_title'))
rk=json.load(open(f'{RES}/rkts_taisho.json'))['entries']
for e in (rk.values() if isinstance(rk,dict) else rk):
    n=e.get('tohoku')
    if n is not None:
        d=toh_titles[n]
        d['rkts_skt']=e.get('sanskrit_title'); d['rkts_en']=e.get('english_title'); d['rkts_tib']=e.get('tibetan_title')
# 84000 english slug from filenames
f8=json.load(open(f'{RES}/84000_tohoku_extract.json'))['entries']
for k,v in f8.items():
    n=tohint(k); files=v.get('files',[]) if isinstance(v,dict) else []
    slugs=set()
    for fp in files:
        m=re.search(r'toh\d+[a-z]?-([a-z0-9_\-]+)\.xml', fp)
        if m: slugs.add(m.group(1).replace('_',' '))
    if slugs: toh_titles[n]['t84_slugs']=sorted(slugs)[:3]

# Taisho titles
meta={m['text_id']:m for m in json.load(open('data/metadata.json'))}

# ---- MITRA sample aligned sentence pairs (one pass) ----
TSV=os.path.expanduser('~/taisho-canon/data/mitra-parallel/mitra-parallel/tsv')
def cjk_f(s): return sum(1 for c in s if '一'<=c<='鿿')/max(1,len(s))
def tib_f(s): return sum(1 for c in s if 'ༀ'<=c<='࿿')/max(1,len(s))
TA=re.compile(r'T(\d{2})n(\d{4}[A-Za-z]?)'); DE=re.compile(r'D(\d{4})')
samples=defaultdict(list)
files=sorted(os.listdir(TSV))
for i,fn in enumerate(files):
    if (i+1)%4000==0: print(f'  scan {i+1}/{len(files)}')
    try: fh=open(os.path.join(TSV,fn),encoding='utf-8')
    except OSError: continue
    with fh:
        fh.readline()
        for line in fh:
            p=line.rstrip('\n').split('\t')
            if len(p)<4: continue
            s_id,s_tx,t_id,t_tx=p[0],p[1],p[2],p[3]
            if not s_tx.strip() or not t_tx.strip(): continue
            if cjk_f(s_tx)>0.3 and tib_f(t_tx)>0.3: ch_id,ch,tb_id,tb=s_id,s_tx,t_id,t_tx
            elif cjk_f(t_tx)>0.3 and tib_f(s_tx)>0.3: ch_id,ch,tb_id,tb=t_id,t_tx,s_id,s_tx
            else: continue
            tm=TA.search(ch_id); dm=DE.search(tb_id)
            if not tm or not dm: continue
            key=(f"T{tm.group(1)}n{tm.group(2)}", int(dm.group(1)))
            if key in keys and len(samples[key])<6:
                samples[key].append({'ch':ch[:120],'tb':tb[:120]})

# ---- assemble dossiers ----
out=[]
for (tais,toh),par in keys.items():
    m=meta.get(tais,{})
    out.append({
        'taisho':tais,'toh':f'Toh {toh}','toh_int':toh,
        'chinese_coverage':par['chinese_coverage'],'tibetan_coverage':par['tibetan_coverage'],
        'aligned_sentences':par['aligned_sentences'],
        'basis':'chinese' if par['chinese_coverage']>=0.30 else 'tibetan',
        'taisho_title_zh':par.get('title') or m.get('title'),
        'taisho_char_count':m.get('char_count'),
        'toh_titles':toh_titles.get(toh,{}),
        'samples':samples.get((tais,toh),[]),
    })
out.sort(key=lambda x:(x['toh_int'], x['taisho']))
json.dump({'count':len(out),'dossiers':out}, open('/tmp/dossier169.json','w'), ensure_ascii=False, indent=1)
print('built dossiers:',len(out),'; with>=1 sample:',sum(1 for o in out if o['samples']),
      '; with a toh sanskrit title:',sum(1 for o in out if o['toh_titles'].get('cbeta_skt') or o['toh_titles'].get('rkts_skt')))
