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
# Left out of the directory and the registry until its owner, or Dinis, says its address may be shown (design.b, round 13).
HIDDEN = {'kate-curtis-evans.founder.sovereignweb.site', 'hub.sovereignweb.site/start/#first-handover'}
UNNAMED = {}
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
STAGE = {'live': 'live', 'seeded': 'setting-up', 'building': 'setting-up', 'approved': 'setting-up', 'asked': 'setting-up'}

req = urllib.request.Request(f'{SRC}?t={int(time.time())}', headers={'User-Agent': 'sws-hub-directory', 'Cache-Control': 'no-cache'})
pipe = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
assert pipe.get('schema') == 'sws-pipeline/1', pipe.get('schema')

# Each pipeline site is re-read live over https at build time (sites.a, 25 Nov): one that answers is linked; one still being
# built that does not answer yet is listed as "coming soon (https pending)", with no link.
import concurrent.futures


def answers(h):
    try:
        return urllib.request.urlopen(urllib.request.Request(f'https://{h}/', headers={'User-Agent': 'sws-hub-directory'}), timeout=20).status == 200
    except Exception:
        return False


hosts = {p['address'].strip('/').replace('https://', '').replace('http://', ''): p for p in pipe['sites']}
with concurrent.futures.ThreadPoolExecutor(16) as ex:
    live = dict(zip(hosts, ex.map(answers, hosts)))
sites = {}
for h, p in hosts.items():
    if h in HIDDEN:
        continue
    if live[h]:
        state = 'setting-up' if p['stage'] in ('building', 'approved', 'asked') else STAGE.get(p['stage'], 'setting-up')
    elif p['stage'] in ('building', 'approved', 'asked'):
        state = 'pending'
    else:
        continue
    sites[h] = {'host': h, 'name': UNNAMED.get(h, p['title']), 'group': HOST_GROUP.get(h) or GROUP.get(p['group']) or ('demos' if p.get('kind') == 'demo' else 'people'),
                'state': state, 'repository': f"SovereignWebsite/{p['repository']}" if p.get('repository') else None}
for s in json.loads((SITE / 'sites.json').read_text())['sites']:
    if s.get('status') != 'live':
        continue
    h = s['address']['url'].split('/')[2]
    if s.get('slug') == 'first-handover' or h in HIDDEN:
        continue
    item = sites.setdefault(h, {'host': h, 'name': s['name'], 'group': SECTION.get(s.get('section'), 'demos'), 'state': 'live',
                                'repository': None})
    item['name'] = UNNAMED.get(h, s['name'])
    item['group'] = SECTION.get(s.get('section'), item['group'])
    item['state'] = 'live'
    item['showroom'] = True
    if s.get('group'):
        item['label'] = s['group']
    if s.get('summary'):
        item['summary'] = s['summary']
    if s.get('repository') and h not in UNNAMED:
        item['repository'] = s['repository'] if '/' in s['repository'] else f"SovereignWebsite/{s['repository']}"
for h in UNNAMED:
    if h in sites:
        sites[h]['repository'] = None

# Groups: design.b's brief hub-map (1ffcf43), six fixed groups (confirmed by design.b after round 13), in the order
# of its review (873b6dd): People first, Agents last. Each site keeps its finer label as a tag.
SIX = [('people', 'People', "Founders, artists, designers, musicians and other people's own sites."),
       ('tools', 'Tools', 'Tools and platform consoles that run in your browser.'),
       ('startups', 'Startups', 'The startup brochures.'),
       ('businesses-demos', 'Businesses and demos', 'Made-up companies, demonstrations, AI providers and guides.'),
       ('family', 'The family', 'Our own sites: Sovereign Website, its principles, hosting, this hub, the vault and the news.'),
       ('agents', 'Agents', 'Each agent of the team has a site of its own: what it does, what it is working on, how to reach it.')]
TO_SIX = {'people': 'people', 'startups': 'startups', 'businesses': 'businesses-demos', 'demos': 'businesses-demos',
          'providers': 'businesses-demos', 'guides': 'businesses-demos', 'tools': 'tools', 'platforms': 'tools',
          'news': 'family', 'agents': 'agents'}
HOST_SIX = {'dinis-cruz.presentations.sovereignweb.site': 'people'}
FINE = {g: n for g, n, _ in GROUPS}
# Our own family of sites, checked live at build time; listed only if they answer.
FAMILY = [('sovereignwebsite.ai', 'Sovereign Website'), ('sovereignwebsite.org', 'The principles'),
          ('sovereignwebsite.site', 'Hosted sovereign websites'), ('hub.sovereignweb.site', 'This hub'),
          ('vault.sovereignwebsite.site', 'The vault'), ('promptugal.news', 'PrompTugal.news')]
for h, n in FAMILY:
    try:
        ok = urllib.request.urlopen(urllib.request.Request(f'https://{h}/', headers={'User-Agent': 'sws-hub-directory'}), timeout=20).status == 200
    except Exception:
        ok = False
    if ok:
        sites.setdefault(h, {'host': h, 'name': n, 'group': 'family', 'state': 'live', 'repository': None})
for s in sites.values():
    s['tag'] = s.pop('label', None) or FINE.get(s['group'], 'Our own')
    s['group'] = HOST_SIX.get(s['host']) or TO_SIX.get(s['group'], s['group'])
assert all(s['group'] in {g for g, _, _ in SIX} for s in sites.values()), 'a site with no group fails the build'
GROUPS = SIX

out = {'about': 'Every public site that answered when checked, from sites.b\'s pipeline and the hub\'s sites.json. Built by tools/build-directory.py; private sites are never listed.',
       'checked': pipe.get('checked'), 'source': SRC, 'groups': [{'id': g, 'name': n, 'about': a} for g, n, a in GROUPS],
       'sites': sorted(sites.values(), key=lambda s: (s['group'], s['name'].lower()))}
(SITE / 'directory.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
print(f"directory: {len(out['sites'])} sites (pipeline checked {pipe.get('checked')})")
