#!/usr/bin/env python3
# Builds site/admin/, the hub's admin dashboard: tiles, a commits-over-time chart, sites by section, the design
# rounds and their ratings, and prompts for the hub's keeper; then "How this site was made" (tools/admin/made.html).
# Everything is gathered at build time into site/admin/data.json and drawn as inline SVG: the page makes no request
# to any other site. Sources: this repository's git history and tags, site/sites.json, and the hub's reviews in
# Site__Agents__Design (docs/reviews/hub), if a checkout of it is given.
# Usage: python3 tools/build-admin.py [path to a Site__Agents__Design checkout]
import collections, datetime, html, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
ADMIN = ROOT / 'tools' / 'admin'
DESIGN = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
DESIGN_WEB = 'https://github.com/SovereignWebsite/Site__Agents__Design/blob/dev/docs/reviews/hub/'
HUB_WEB = 'https://github.com/SovereignWebsite/SovereignWebsite__Hub'
e = lambda x: html.escape(str(x), quote=True)
git = lambda *a: subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True, check=True).stdout

# History: commits per day, tags, the last release.
days = collections.Counter(l for l in git('log', '--format=%ad', '--date=short').split() if l)
commits = sum(days.values())
sha = dict(reversed(l.split('\t')) for l in git('ls-remote', '--tags', 'origin').splitlines() if 'refs/tags/v' in l and not l.endswith('^{}'))
tags = sorted((k.split('refs/tags/')[1] for k in sha), key=lambda v: [int(x) for x in re.findall(r'\d+', v)])
last = tags[-1] if tags else None
try:
    last_date = git('log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M UTC', sha['refs/tags/' + last]).strip() if last else ''
except subprocess.CalledProcessError:
    last_date = ''  # the tagged commit is not in this checkout

# The register: live public sites by section.
sites = [s for s in json.loads((SITE / 'sites.json').read_text())['sites'] if s.get('status') == 'live']
ORDER = ['People', 'Startups', 'Providers', 'Businesses', 'PrompTugal.news', 'Demos', 'Tools']
by_section = collections.Counter(s.get('section', 'Demos') for s in sites)
sections = [(n, by_section[n]) for n in ORDER if by_section[n]]
handed = sum(1 for s in sites if s.get('handed_over'))

# Design rounds from the back office: title, date and rating, newest first.
rounds = []
if DESIGN and (DESIGN / 'docs' / 'reviews' / 'hub').is_dir():
    for f in sorted((DESIGN / 'docs' / 'reviews' / 'hub').glob('20*.md'), reverse=True):
        t = f.read_text()
        title = re.search(r'^# (.+)$', t, re.M)
        rating = re.search(r'Rat(?:ed|ing)[^0-9\n]{0,20}\**\s*(\d)(?:\s*of 5)?', t, re.I)
        rounds.append({'title': title.group(1).strip() if title else f.stem, 'date': f.name[:10],
                       'rating': int(rating.group(1)) if rating else None, 'url': DESIGN_WEB + f.name})

now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
data = {'built': now, 'commits': commits, 'tags': len(tags), 'last_release': last, 'last_release_date': last_date,
        'designs': 5, 'sites_listed': len(sites), 'handed_over': handed, 'commits_by_day': dict(sorted(days.items())),
        'sites_by_section': dict(sections), 'design_rounds': rounds}


def bars(items, label, unit):
    # A plain bar chart in SVG, one colour, values printed on the bars, with the numbers in a table beside it.
    w, bh, gap, left = 640, 26, 8, 130
    mx = max(v for _, v in items) or 1
    h = len(items) * (bh + gap)
    rows = ''.join(f'<text x="{left - 8}" y="{i * (bh + gap) + bh * .68:.1f}" text-anchor="end" class="lab">{e(k)}</text>'
                   f'<rect x="{left}" y="{i * (bh + gap)}" width="{max(2, (w - left - 40) * v / mx):.1f}" height="{bh}" rx="3" class="bar"/>'
                   f'<text x="{left + max(2, (w - left - 40) * v / mx) + 6:.1f}" y="{i * (bh + gap) + bh * .68:.1f}" class="val">{v}</text>'
                   for i, (k, v) in enumerate(items))
    table = ''.join(f'<tr><th scope="row">{e(k)}</th><td>{v}</td></tr>' for k, v in items)
    return (f'<figure class="chart"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}">{rows}</svg>'
            f'<details><summary>The numbers</summary><table><thead><tr><th scope="col">{e(label.split(",")[0])}</th><th scope="col">{e(unit)}</th></tr></thead><tbody>{table}</tbody></table></details></figure>')


tiles = [(commits, 'commits', f'{HUB_WEB}/commits/dev'), (len(tags), 'releases', f'{HUB_WEB}/tags'),
         (5, 'designs', '/designs/'), (len(sites), 'sites listed', '/sites.json'),
         (handed, 'handed over', '/'), (last or 'none', f'last deploy, {last_date}' if last else 'last deploy', f'{HUB_WEB}/actions')]
PROMPTS = [
    ('Add a site', 'Read https://hub.sovereignweb.site/llms.txt and follow the instructions for the owner. Add the public site at [address] to site/sites.json in the hub-site format, take its screenshots with tools/take-shots.js, rebuild with tools/build-showroom.py, run the checks and push to dev.'),
    ('Refresh the screenshots', 'Read https://hub.sovereignweb.site/llms.txt as the owner. Run tools/refresh.sh, tell me which sites did not answer, and push the new screenshots to dev if the checks pass.'),
    ('Take a design round', 'Read https://hub.sovereignweb.site/llms.txt as the owner. Read the latest hub review in Site__Agents__Design docs/reviews/hub, fix its items one commit each, and tell me each release tag.'),
    ('What changed this week', 'Read the commits of https://github.com/SovereignWebsite/SovereignWebsite__Hub on dev for the last seven days and summarise what changed on hub.sovereignweb.site, with a link for each point.'),
    ('Check it is still safe', 'Read https://hub.sovereignweb.site/llms.txt as the owner. Check that no private or vault-only site is named anywhere in site/, that the site sets no cookies and makes no request to another host, and report what you find.'),
]

dash = f'''<div class="mark">Admin</div>
<h1>The hub at a glance</h1>
<p>Built {e(now)} from this site's own history, its register and its design reviews. Nothing on this page asks another site for anything; the numbers are in <a href="data.json">data.json</a>.</p>
<section aria-labelledby="h-over"><h2 id="h-over">Overview</h2>
<ul class="tiles">{''.join(f'<li><a href="{e(u)}"><b>{e(v)}</b><span>{e(k)}</span></a></li>' for v, k, u in tiles)}</ul></section>
<section aria-labelledby="h-act"><h2 id="h-act">Activity: commits a day</h2>
{bars(list(data['commits_by_day'].items()), 'Day, commits to the hub', 'Commits')}</section>
<section aria-labelledby="h-sec"><h2 id="h-sec">Sites listed, by section</h2>
{bars(sections, 'Section, public sites listed', 'Sites')}</section>
<section aria-labelledby="h-des"><h2 id="h-des">Design rounds</h2>
{('<ol class="rounds">' + ''.join(f'<li><a href="{e(r["url"])}">{e(r["title"])}</a> <span class="when">{e(r["date"])}</span>' + (f' <span class="rate">rated {r["rating"]} of 5</span>' if r['rating'] else '') + '</li>' for r in rounds) + '</ol>') if rounds else '<p>No review checkout was given at build time.</p>'}
<p>The reviews are kept by design.b and design.b.rounds in <a href="https://github.com/SovereignWebsite/Site__Agents__Design/tree/dev/docs/reviews/hub">Site__Agents__Design</a>.</p></section>
<section aria-labelledby="h-ask"><h2 id="h-ask">Ask Claude</h2>
<p>For whoever keeps the hub: copy one of these into Claude, with write access to the repository.</p>
{''.join(f'<div class="ask"><h3>{e(t)}</h3><pre id="p{i}">{e(p)}</pre><button type="button" data-copy="p{i}">Copy</button></div>' for i, (t, p) in enumerate(PROMPTS))}
</section>
'''

STYLE = '''<style>
main{max-width:62rem}
.tiles{list-style:none;padding:0;margin:0;display:grid;gap:.8rem;grid-template-columns:repeat(auto-fill,minmax(9rem,1fr))}
.tiles a{display:block;padding:.8rem 1rem;border:1px solid var(--line);border-radius:8px;text-decoration:none;color:var(--fg);height:100%}
.tiles a:hover,.tiles a:focus-visible{border-color:var(--accent)}
.tiles b{display:block;font-size:1.7rem;line-height:1.1;color:var(--fg);overflow-wrap:anywhere}.tiles span{color:var(--muted);font-size:.85rem}
.chart{margin:0}.chart svg{width:100%;height:auto;display:block}
.chart .bar{fill:var(--accent)}.chart .lab{fill:var(--fg);font-size:13px}.chart .val{fill:var(--fg);font-size:13px;font-weight:600}
.chart details{margin-top:.4rem;font-size:.9rem}.chart summary{cursor:pointer;color:var(--accent)}
.chart table{border-collapse:collapse;margin-top:.4rem}.chart th,.chart td{padding:.2rem .8rem .2rem 0;text-align:left;border-bottom:1px solid var(--line)}
.rounds{padding-left:1.2rem}.rounds .when{color:var(--muted);font-size:.85rem}
.rate{display:inline-block;font-size:.8rem;font-weight:700;padding:0 .45rem;border:1px solid var(--accent);border-radius:999px;color:var(--fg)}
.ask{border:1px solid var(--line);border-radius:8px;padding:.6rem 1rem .8rem;margin:.8rem 0}
.ask h3{margin:.2rem 0 .4rem;font-size:1rem}.ask pre{margin:0 0 .5rem}
.ask button{font:inherit;font-size:.9rem;padding:.35rem .9rem;min-height:36px;border:1px solid var(--accent);background:transparent;color:var(--fg);border-radius:6px;cursor:pointer}
#made{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--line)}
</style>
'''
SCRIPT = '''<script>document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){var t=document.getElementById(b.dataset.copy).textContent;
if(navigator.clipboard)navigator.clipboard.writeText(t).then(function(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy';},1500);});});});</script>
'''

top = (ADMIN / 'shell-top.html').read_text().replace('</head>', STYLE + '</head>', 1)
bottom = (ADMIN / 'shell-bottom.html').read_text().replace('</body>', SCRIPT + '</body>', 1)
made = (ADMIN / 'made.html').read_text().replace('<div class="mark">How this site was made</div>\n', '')
(SITE / 'admin' / 'index.html').write_text(top + '\n' + dash + made + bottom)
(SITE / 'admin' / 'data.json').write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
print(f'admin: {commits} commits, {len(tags)} releases, {len(sites)} sites, {len(rounds)} design rounds')
