import json

with open('/Users/danzigmond/taisho-canon/results/cross_reference_expanded.json') as f:
    data = json.load(f)

lp = data['link_provenance']

# Computational (non-catalog) sources
computational_sources = {'mitra', 'sanskrit_title_match'}

# All unique source names
all_sources = set()
for tid, links in lp.items():
    for toh, provs in links.items():
        for p in provs:
            all_sources.add(p['source'])

catalog_sources = all_sources - computational_sources

print("All provenance sources:", sorted(all_sources))
print(f"Catalog sources: {sorted(catalog_sources)}")
print(f"Computational sources: {sorted(computational_sources)}")
print()

# Find Sanskrit-only links (no catalog attestation)
sanskrit_only = []       # Sanskrit match but no catalog, no MITRA
sanskrit_plus_mitra = [] # Sanskrit match + MITRA but no catalog
sanskrit_total_new = []  # Sanskrit match with no catalog (regardless of MITRA)

for tid, links in lp.items():
    for toh, provs in links.items():
        sources = {p['source'] for p in provs}

        has_sanskrit = 'sanskrit_title_match' in sources
        has_mitra = 'mitra' in sources
        has_catalog = bool(sources & catalog_sources)

        if has_sanskrit and not has_catalog:
            sanskrit_total_new.append((tid, toh, sources, provs))

            if has_mitra:
                mitra_prov = [p for p in provs if p['source'] == 'mitra']
                skt_prov = [p for p in provs if p['source'] == 'sanskrit_title_match']
                sanskrit_plus_mitra.append((tid, toh, mitra_prov, skt_prov, provs))
            else:
                sanskrit_only.append((tid, toh, sources, provs))

print(f"Sanskrit new proposals (no catalog): {len(sanskrit_total_new)}")
print(f"  Sanskrit only (no MITRA): {len(sanskrit_only)}")
print(f"  Sanskrit + MITRA (no catalog): {len(sanskrit_plus_mitra)}")
print()

# Also count: total links with sanskrit_title_match
total_sanskrit = 0
sanskrit_with_catalog = 0
for tid, links in lp.items():
    for toh, provs in links.items():
        sources = {p['source'] for p in provs}
        if 'sanskrit_title_match' in sources:
            total_sanskrit += 1
            if sources & catalog_sources:
                sanskrit_with_catalog += 1

print(f"Total links with sanskrit_title_match: {total_sanskrit}")
print(f"  With catalog attestation: {sanskrit_with_catalog}")
print(f"  Without catalog (new proposals): {len(sanskrit_total_new)}")
print()

# Show the Sanskrit+MITRA links in detail
if sanskrit_plus_mitra:
    print("=" * 80)
    print("Links with BOTH Sanskrit title match AND MITRA alignment (no catalog)")
    print("=" * 80)
    print()
    for tid, toh, mitra_prov, skt_prov, all_provs in sorted(sanskrit_plus_mitra, key=lambda x: x[0]):
        # Get MITRA details
        mitra_info = ""
        for mp in mitra_prov:
            conf = mp.get('confidence', '?')
            note = mp.get('note', '')
            mitra_info = f"conf={conf}, {note}"

        # Get Sanskrit match details
        skt_info = ""
        for sp in skt_prov:
            conf = sp.get('confidence', '?')
            note = sp.get('note', '')
            skt_info = f"conf={conf}, {note}"

        # Get classification if available
        cls_data = data.get('link_classifications', {}).get(tid, {}).get(toh, {})
        cls_type = cls_data.get('type', '?')
        cls_basis = cls_data.get('basis', '')

        print(f"  {tid} -> {toh}")
        print(f"    Classification: {cls_type} ({cls_basis})")
        print(f"    Sanskrit: {skt_info}")
        print(f"    MITRA:    {mitra_info}")
        print()

# Also show Sanskrit-only (no MITRA, no catalog) for context
if sanskrit_only:
    print("=" * 80)
    print(f"Sanskrit-only links (no MITRA, no catalog): {len(sanskrit_only)} total")
    print("=" * 80)
    print()
    for tid, toh, sources, provs in sorted(sanskrit_only, key=lambda x: x[0])[:20]:
        skt_prov = [p for p in provs if p['source'] == 'sanskrit_title_match']
        for sp in skt_prov:
            note = sp.get('note', '')
            conf = sp.get('confidence', '?')
            print(f"  {tid} -> {toh}: conf={conf}, {note}")
    if len(sanskrit_only) > 20:
        print(f"  ... ({len(sanskrit_only) - 20} more)")
