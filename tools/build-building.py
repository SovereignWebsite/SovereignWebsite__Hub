#!/usr/bin/env python3
# Rebuilds site/building.json (the hub's /building/ page) from sites.b's public register:
# https://sites.agents.sovereignweb.site/register/register.json (schema sws-site-register/1, public sites only).
# Keeps the sites "under-construction" (live, not finished) and "coming" (requested, not live); each live one's
# description is read from its own home page. Placeholders (the Factory's seed page) are left out.
# Usage: python3 tools/build-building.py   then python3 tools/build-showroom.py
import concurrent.futures, html, json, pathlib, re, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'site' / 'building.json'
SRC = 'https://sites.agents.sovereignweb.site/register/register.json'
GROUPS = {'agents': "Agents' own sites", 'author': 'People', 'talent': 'People', 'cv': 'People', 'frameworks': 'Guides',
          'platform': 'Platforms', 'tool': 'Tools', 'demo': 'Demos'}
UA = {'User-Agent': 'sws-hub-building'}
reg = json.loads(urllib.request.urlopen(urllib.request.Request(SRC, headers=UA), timeout=30).read().decode())
assert reg.get('schema') == 'sws-site-register/1', reg.get('schema')
old = {b['host']: b for b in json.loads(OUT.read_text())['sites']} if OUT.exists() else {}
host = lambda a: re.sub(r'^https?://|/$', '', a)


def read(r):
    h = host(r['address'])
    state = 'building' if r['state'] == 'under-construction' else 'coming'
    item = {'state': state, 'group': GROUPS.get(r.get('group') or '', "Agents' own sites"), 'host': h,
            'name': (old.get(h) or {}).get('name') or h.split('.')[0].replace('-', ' ').title(),
            'summary': (old.get(h) or {}).get('summary', ''), 'five_designs': bool(r.get('design_control'))}
    if state == 'building':
        try:
            t = urllib.request.urlopen(urllib.request.Request(f'https://{h}/', headers=UA), timeout=20).read().decode('utf8', 'replace')
            ti = re.search(r'<title>(.*?)</title>', t, re.S)
            de = re.search(r'<meta name="description" content="([^"]*)"', t)
            if ti:
                item['name'] = html.unescape(ti.group(1).strip())
            if de:
                item['summary'] = html.unescape(de.group(1))
        except Exception:
            pass  # keep what we had
    return item


keep = [r for r in reg['sites'] if r['state'] in ('under-construction', 'coming')]
with concurrent.futures.ThreadPoolExecutor(10) as pool:
    items = list(pool.map(read, keep))
# Sites sites.b sent directly that the register does not list yet.
EXTRA = ROOT / 'tools' / 'showroom' / 'building-extra.json'
if EXTRA.exists():
    listed = {i['host'] for i in items} | {host(r['address']) for r in reg['sites']}
    items += [{k: v for k, v in x.items() if k != 'sent'} for x in json.loads(EXTRA.read_text())['sites'] if x['host'] not in listed]
data = {'about': "Sites being built and sites coming, from sites.b's register. Building: live, not finished, not yet in the showroom. "
                 "Coming: requested, not live yet. Private (vault) sites are never listed; sites still on the Factory's seed page are left out.",
        'checked': reg['checked'][:10], 'checked_at': reg['checked'], 'source': reg['source'], 'sites': items}
OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print(f"building: {sum(1 for i in items if i['state'] == 'building')} building, {sum(1 for i in items if i['state'] == 'coming')} coming (register checked {reg['checked']})")
