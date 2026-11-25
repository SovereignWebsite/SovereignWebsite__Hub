#!/usr/bin/env python3
# Rebuilds site/directory.json: every public site that answers, for the hub's /directory/ page and site/registry.json.
# Sources, both read at build time, never by hand:
#   - sites.b's pipeline, https://sites.agents.sovereignweb.site/pipeline/pipeline.json (sws-pipeline/1; private sites
#     are already left out there), keeping the sites that answered 200 when it was checked;
#   - the hub's own site/sites.json, for live showroom sites the pipeline does not list.
# The first handed-over site is listed but its owner is not named (record 2026-11-23__asks-2-8-31-revised, ask 31).
# Usage: python3 tools/build-directory.py   then python3 tools/build-showroom.py
import json, pathlib, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
SRC = 'https://sites.agents.sovereignweb.site/pipeline/pipeline.json'
UNNAMED = {'kate-curtis-evans.founder.sovereignweb.site': "A founder's site, handed over"}
# The pipeline's groups, folded into the groups a visitor looks for.
GROUP = {'agents': 'agents', 'tool': 'tools', 'platform': 'platforms', 'demo': 'demos', 'startups': 'startups',
         'provider': 'providers', 'frameworks': 'guides', 'presentations': 'guides',
         'company': 'businesses', 'organisation': 'businesses'}
SECTION = {'People': 'people', 'Startups': 'startups', 'Providers': 'providers', 'Businesses': 'businesses',
           'PrompTugal.news': 'news', 'Demos': 'demos', 'Tools': 'tools', 'Guides': 'guides', 'Platforms': 'platforms'}
GROUPS = [('agents', 'Agents', 'Each agent of the team has a site of its own: what it does, what it is working on, how to reach it.'),
          ('people', 'People', "People's own sites, made for them and handed over."),
          ('tools', 'Tools', 'Tools that run in your browser.'),
          ('platforms', 'Platforms', 'Guides and consoles for the platforms we use.'),
          ('startups', 'Startups', 'Startups and their sites.'),
          ('businesses', 'Businesses and organisations', 'Companies and organisations.'),
          ('providers', 'AI providers', 'Guides to AI providers, with demos on your own key.'),
          ('guides', 'Guides and talks', 'Frameworks, guides and presentations.'),
          ('news', 'News', 'News sites.'),
          ('demos', 'Demos', 'Demonstrations, not real businesses.')]
# Hosts whose pipeline group is empty or too broad.
HOST_GROUP = {'agents.sovereignweb.site': 'agents', 'presentations.sovereignweb.site': 'guides'}
STAGE = {'live': 'live', 'seeded': 'setting-up', 'building': 'building', 'approved': 'coming', 'asked': 'coming'}

req = urllib.request.Request(f'{SRC}?t={int(time.time())}', headers={'User-Agent': 'sws-hub-directory', 'Cache-Control': 'no-cache'})
pipe = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
assert pipe.get('schema') == 'sws-pipeline/1', pipe.get('schema')

sites = {}
for p in pipe['sites']:
    if p.get('http') != 200:
        continue
    h = p['address'].strip('/').replace('https://', '')
    sites[h] = {'host': h, 'name': UNNAMED.get(h, p['title']), 'group': HOST_GROUP.get(h) or GROUP.get(p['group']) or ('demos' if p.get('kind') == 'demo' else 'people'),
                'state': STAGE.get(p['stage'], 'setting-up'), 'repository': f"SovereignWebsite/{p['repository']}" if p.get('repository') else None}
for s in json.loads((SITE / 'sites.json').read_text())['sites']:
    if s.get('status') != 'live':
        continue
    h = s['address']['url'].split('/')[2]
    item = sites.setdefault(h, {'host': h, 'name': s['name'], 'group': SECTION.get(s.get('section'), 'demos'), 'state': 'live',
                                'repository': None})
    item['name'] = UNNAMED.get(h, s['name'])
    item['group'] = SECTION.get(s.get('section'), item['group'])
    item['state'] = 'live'
    item['showroom'] = True
    if s.get('repository') and h not in UNNAMED:
        item['repository'] = s['repository'] if '/' in s['repository'] else f"SovereignWebsite/{s['repository']}"
for h in UNNAMED:
    if h in sites:
        sites[h]['repository'] = None

out = {'about': 'Every public site that answered when checked, from sites.b\'s pipeline and the hub\'s sites.json. Built by tools/build-directory.py; private sites are never listed.',
       'checked': pipe.get('checked'), 'source': SRC, 'groups': [{'id': g, 'name': n, 'about': a} for g, n, a in GROUPS],
       'sites': sorted(sites.values(), key=lambda s: (s['group'], s['name'].lower()))}
(SITE / 'directory.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
print(f"directory: {len(out['sites'])} sites (pipeline checked {pipe.get('checked')})")
