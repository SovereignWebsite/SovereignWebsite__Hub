#!/usr/bin/env python3
# Builds the hub's "Latest" list: every public site in site/sites.json, newest first, by the moment it was first
# listed on the hub. That moment is read from this repository's own history (the first commit whose
# site/sites.json holds the site's slug), so no date is typed by hand. A site not yet in any commit is shown as
# listed now. Writes site/data/latest.json (the data) and site/latest/index.html (the page).
# Only what sites.json lists is shown: a private or vault-only site never appears, not by name or count.
# Needs the full git history (git fetch --unshallow on a shallow clone).
# Usage: python3 tools/build-latest.py      Apache-2.0. hub.c@SovereignWebsite.dinis, 22 Nov 2026.
import datetime, hashlib, html, json, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
SITE_URL = 'https://hub.sovereignweb.site/'
REPO = 'https://github.com/SovereignWebsite/SovereignWebsite__Hub'
e = lambda x: html.escape(str(x), quote=True)


def git(*a):
    return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def first_listed():
    """slug -> (ISO time, commit) of the first commit whose site/sites.json lists it."""
    seen = {}
    for line in git('log', '--reverse', '--format=%H %cI', '--', 'site/sites.json').splitlines():
        sha, when = line.split()
        try:
            d = json.loads(git('show', f'{sha}:site/sites.json'))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        for s in (d.get('sites', []) if isinstance(d, dict) else d):
            slug = s.get('slug') if isinstance(s, dict) else None
            if slug and slug not in seen:
                seen[slug] = (when, sha)
    return seen


now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
seen = first_listed()
# Sites Dinis keeps off the hub (22 Nov 2026, in hub.c's session), held as the first 16 hex characters of the
# sha256 of their slug, so this file names no one. Never listed, even if an entry is added to sites.json.
OFF_HUB = {'e5fce384ae04237f', '499868c5d9bc0961'}
off = lambda slug: hashlib.sha256(slug.encode()).hexdigest()[:16] in OFF_HUB
sites = [s for s in json.loads((SITE / 'sites.json').read_text())['sites'] if s.get('status') == 'live' and not off(s['slug'])]
items = []
for s in sites:
    when, sha = seen.get(s['slug'], (now, None))
    items.append({
        'slug': s['slug'], 'name': s['name'], 'summary': s['summary'],
        'section': s.get('section', 'Demos'), 'url': s['address']['url'],
        'listed': datetime.datetime.fromisoformat(when).astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z'),
        'listed_in': f'{REPO}/commit/{sha}' if sha else None,
        'waiting': s.get('waiting'), 'handed_over': bool(s.get('handed_over')),
    })
# Newest first; sites listed in the same commit keep the registry's order.
items.sort(key=lambda i: i['listed'], reverse=True)

(SITE / 'data').mkdir(exist_ok=True)
(SITE / 'data' / 'latest.json').write_text(json.dumps({
    'about': 'The latest on the hub: every public site in sites.json, newest first, by when it was first listed on the hub '
             '(the first commit of this repository whose site/sites.json holds it). Built by tools/build-latest.py. '
             '"listed" is when the hub listed the site, not when the site itself went online.',
    'source': f'{SITE_URL}sites.json',
    'count': len(items),
    'items': items,
}, indent=1, ensure_ascii=False) + '\n')

# The page. The family bar and its CSS are taken from the showroom page, as tools/build-showroom.py does.
index = (SITE / 'index.html').read_text()
family = re.search(r'<nav class="family".*?</nav>', index, re.S)
family_css = re.search(r'\.family\{.*?(?=\n</style>|\n#|\n\.d-)', index, re.S)
family = family.group(0).replace('href="./"', 'href="/"') if family else ''
family_css = family_css.group(0) if family_css else ''


def day(iso):
    d = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return d.strftime('%-d %B %Y'), d.date().isoformat()


groups, rows = [], ''
for it in items:
    label, key = day(it['listed'])
    if not groups or groups[-1] != key:
        if groups:
            rows += '</ol>\n</section>\n'
        groups.append(key)
        n = sum(1 for x in items if day(x['listed'])[1] == key)
        rows += (f'<section class="day" aria-labelledby="d-{key}">\n<h2 id="d-{key}"><time datetime="{key}">{e(label)}</time>'
                 f' <span>{n} {"site" if n == 1 else "sites"}</span></h2>\n<ol class="items">\n')
    t = datetime.datetime.fromisoformat(it['listed'].replace('Z', '+00:00')).strftime('%H:%M')
    tags = f'<span class="tag">{e(it["section"])}</span>'
    if it['handed_over']:
        tags += '<span class="tag strong">Handed over</span>'
    if it['waiting']:
        tags += '<span class="tag">Not switched on yet</span>'
    when = f'<time datetime="{e(it["listed"])}">{t} UTC</time>'
    if it['listed_in']:
        when = f'<a href="{e(it["listed_in"])}" title="The commit that listed it">{when}</a>'
    host = re.sub(r'^https?://|/$', '', it['url'])
    rows += (f'<li class="item"><p class="when">{when}</p><div>'
             f'<h3><a href="{e(it["url"])}">{e(it["name"])}</a></h3>'
             f'<p class="sum">{e(it["summary"])}</p>'
             f'<p class="tags">{tags}<a class="host" href="{e(it["url"])}">{e(host)}</a></p></div></li>\n')
if groups:
    rows += '</ol>\n</section>\n'

desc = 'Every public site on the Sovereign Website Hub, newest first: when each was listed, what it is and where it lives.'
page = f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230f6e4f'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' font-weight='700' fill='%23fff' text-anchor='middle'%3ES%3C/text%3E%3C/svg%3E">
<title>Latest: Sovereign Website Hub</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sovereign Website Hub">
<meta property="og:locale" content="en_GB">
<meta property="og:url" content="{SITE_URL}latest/">
<meta property="og:title" content="Latest: Sovereign Website Hub">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE_URL}og.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Sovereign Website Hub">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Latest: Sovereign Website Hub">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{SITE_URL}og.jpg">
<link rel="canonical" href="{SITE_URL}latest/">
<link rel="alternate" type="application/json" href="/data/latest.json" title="The latest, as data">
<style>
:root{{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#5d5c57;--accent:#2f6b4f;--line:#e4e1d8;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141513;--fg:#ecebe6;--muted:#a8a69e;--accent:#7fc3a0;--line:#2c2d29;--card:#1c1d1a}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}
a{{color:inherit}}
.skip{{position:absolute;left:-999px}}.skip:focus{{left:1rem;top:1rem;z-index:9;padding:.5rem 1rem;background:var(--accent);color:var(--bg)}}
.top{{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1.5rem;max-width:48rem;margin:0 auto;padding:1.5rem 1rem 0}}
.top .name{{font-weight:700;text-decoration:none}}.top nav{{display:flex;gap:1rem;margin-left:auto;font-size:.95rem}}
.top nav a{{color:var(--accent);font-weight:600}}.top nav a[aria-current=page]{{color:var(--fg);text-decoration:none}}
main{{max-width:48rem;margin:0 auto;padding:2.5rem 1rem 3rem}}
.mark{{margin:0;font-size:.75rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:700}}
h1{{font-size:clamp(2.2rem,6vw,3.4rem);line-height:1.05;margin:.3rem 0 1rem;letter-spacing:-.01em}}
.lede{{color:var(--muted);font-size:1.08rem;margin:0 0 .6rem}}.lede a{{color:var(--accent)}}
.day{{margin-top:2.5rem}}
.day h2{{display:flex;align-items:baseline;gap:.75rem;font-size:1.15rem;margin:0 0 .25rem;padding-bottom:.4rem;border-bottom:2px solid var(--fg)}}
.day h2 span{{font-size:.85rem;font-weight:500;color:var(--muted)}}
.items{{list-style:none;margin:0;padding:0}}
.item{{display:grid;grid-template-columns:5.2rem minmax(0,1fr);gap:1rem;padding:1rem 0;border-bottom:1px solid var(--line)}}
.when{{margin:.2rem 0 0;font:500 .85rem/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}}
.when a{{text-decoration:none}}.when a:hover,.when a:focus-visible{{text-decoration:underline}}
.item h3{{margin:0;font-size:1.15rem;line-height:1.25}}.item h3 a{{text-decoration:none}}.item h3 a:hover{{text-decoration:underline}}
.sum{{margin:.2rem 0 .45rem;color:var(--muted)}}
.tags{{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem .5rem;margin:0;font-size:.78rem}}
.tag{{padding:.08rem .55rem;border:1px solid var(--line);border-radius:999px;color:var(--muted)}}
.tag.strong{{background:var(--accent);border-color:var(--accent);color:var(--bg);font-weight:600}}
.host{{color:var(--accent);font-weight:600;text-decoration:none;overflow-wrap:anywhere}}.host:hover{{text-decoration:underline}}
@media (max-width:30rem){{.item{{grid-template-columns:minmax(0,1fr);gap:.2rem}}}}
footer{{max-width:48rem;margin:0 auto;padding:1rem 1rem 2rem;border-top:1px solid var(--line);font-size:.85rem;color:var(--muted)}}
footer a{{color:var(--accent)}}
{family_css}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{family}
<header class="top">
  <a class="name" href="/">Sovereign Website Hub</a>
  <nav aria-label="The hub"><a href="/">Showroom</a><a href="/latest/" aria-current="page">Latest</a></nav>
</header>
<main id="main">
<p class="mark">Latest</p>
<h1>New on the hub</h1>
<p class="lede">Every public site on the hub, newest first. {len(items)} sites so far. The time is when the hub first listed the site, which links to the change that listed it; it is not always when the site itself went online.</p>
<p class="lede">The same list as data: <a href="/data/latest.json">data/latest.json</a>.</p>
{rows}</main>
<footer>hub.sovereignweb.site · Part of the <a href="https://github.com/SovereignWebsite">SovereignWebsite</a> organisation · <a href="/policy/">How this site is governed</a> · No cookies, no tracking.</footer>
</body>
</html>
'''
(SITE / 'latest').mkdir(exist_ok=True)
(SITE / 'latest' / 'index.html').write_text(page)
print(f'latest: {len(items)} sites, newest {items[0]["listed"] if items else "none"}')
