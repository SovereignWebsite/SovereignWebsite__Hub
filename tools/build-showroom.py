#!/usr/bin/env python3
# Builds site/index.html, the showroom of public hosted sites, from site/sites.json.
# Five designs of the same content, one tap apart, for Dinis to choose one.
# Only public, live sites are listed; a private or vault-only site never appears, not by name or count.
# Usage: python3 tools/build-showroom.py   (validates sites.json against the schema first)
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
data = json.loads((SITE / 'sites.json').read_text())
schema = json.loads((SITE / 'schema' / 'hub-site.schema.json').read_text())
try:
    import jsonschema
    for s in data['sites']:
        jsonschema.validate(s, schema)
except ImportError:
    print('note: jsonschema not installed, schema not checked', file=sys.stderr)

old = (SITE / 'index.html').read_text() if (SITE / 'index.html').exists() else ''
family = re.search(r'<nav class="family".*?</nav>', old, re.S)
family_css = re.search(r'\.family\{.*?(?=\n</style>|\n#|\n\.d-)', old, re.S)
family = family.group(0) if family else ''
family_css = family_css.group(0) if family_css else ''


e = lambda x: html.escape(str(x), quote=True)
host_of = lambda s: re.sub(r'^https?://|/$', '', s['address']['url'])
sites = [s for s in data['sites'] if s.get('status') == 'live']
# Featured (hand-picked rank) first; a site still waiting on something goes last.
sites.sort(key=lambda s: (bool(s.get('waiting')), s.get('featured', 10**6)))
# The showroom's sections, in order, each with one line that says what it holds.
SECTIONS = [
    ('People', 'Personal sites for real people. Kate Curtis-Evans was the first to take hers over and edit it herself.'),
    ('Startups', 'Independent brochures about the startups in the family, each made from the company\'s own public pages.'),
    ('Providers', 'Independent guides to the AI providers a sovereign website can use, cited, with browser demos that use your own key.'),
    ('Businesses', 'Sites for businesses: two made-up examples, labelled as such, and a redesign proposal made with the company\'s agreement.'),
    ('PrompTugal.news', 'The parts of PrompTugal.news that are live: Portugal\'s public data, gathered and explained by agent teams.'),
    ('Demos', 'Demonstrations: what an agent team builds from public data, and how a site is made from one request.'),
    ('Tools', 'Small working tools.'),
]
by_section = {n: [s for s in sites if s.get('section', 'Demos') == n] for n, _ in SECTIONS}
people = by_section['People']
sid = lambda n: 's-' + re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
hero = next((s for s in people if s.get('handed_over')), people[0] if people else sites[0])
handed = sum(1 for s in sites if s.get('handed_over'))
working = sum(1 for s in sites if not s.get('waiting'))
# The five designs, numbered as design.b's round 5 prototypes. The Register (2) is the lead and the home page;
# a design that is its own page links there, a design that is still a skin of the home page is a #design-N address.
DESIGNS = [(1, 'The Gallery', '/gallery/'), (2, 'The Register', '/'), (3, 'Contact Sheet', '/contact-sheet/'), (4, 'The Street', '/street/'), (5, 'The Line', '/line/')]
names = [n for _, n, _ in DESIGNS]
LEAD = 2
# Designs that are pages of their own; an old #design-N address on the home page forwards to them.
PAGES = {str(d): h for d, _, h in DESIGNS if not h.startswith('/#') and h != '/'}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
long_date = lambda d: f"{int(d[8:10])} {MONTHS[int(d[5:7]) - 1]} {d[:4]}"
# The register numbers every entry in the order the page shows them.
entry_no = {s['slug']: i + 1 for i, s in enumerate(x for n, _ in SECTIONS for x in by_section[n])}
PARTS = 'ABCDEFGHIJ'
SITE_URL = 'https://hub.sovereignweb.site/'


def shot(s, eager, sizes='(min-width:900px) 33vw, 100vw'):
    sh = s.get('shot')
    if not sh:
        return ''
    return (f'<picture><source media="(max-width:640px)" srcset="{e(sh)}-phone.jpg">'
            f'<img src="{e(sh)}.jpg" alt="Screenshot of {e(s["name"])}" loading="{"eager" if eager else "lazy"}" width="1280" height="800"></picture>')


def frame(s, eager):
    return (f'<a class="frame" href="{e(s["address"]["url"])}" aria-label="Open {e(s["name"])}">'
            f'<span class="chrome"><i></i><i></i><i></i><b>{e(host_of(s))}</b></span>{shot(s, eager)}</a>')


def chips(s):
    c = []
    if s.get('handed_over'):
        c.append(('hand', 'Handed over'))
    c += [('', x) for x in s.get('chips', [])]
    c.append(('wait', 'Not switched on yet') if s.get('waiting') else ('live', 'Live'))
    return '<p class="chips">' + ''.join(f'<span class="{k}">{e(t)}</span>' for k, t in c) + '</p>'


# Break opportunities in long addresses, so a phone wraps them at a dot or a slash, not mid-word.
soft = lambda x: re.sub(r'([./]|__)', r'\1<wbr>', e(x))


def register(s):
    # The register's own lines: shown in The Register design, hidden in the others (which say the same in chips).
    rows = [('Address', f'<a href="{e(s["address"]["url"])}">{soft(host_of(s))}</a>'), ('Kind', e(s.get('group') or s['kind']))]
    if s.get('handed_over'):
        rows.append(('Held', f"By its owner, since {e(long_date(s['handed_over']))}"))
    elif s.get('section') == 'People':
        rows.append(('Held', 'SovereignWebsite, until handed over'))
    else:
        rows.append(('Held', e(s['owner']['name'])))
    rows.append(('Status', 'Handed over' if s.get('handed_over') else 'Not switched on yet' if s.get('waiting') else 'Live'))
    repo = (s.get('repository') or {}).get('url')
    if repo:
        rows.append(('Files', f'<a href="{e(repo)}">{soft(re.sub(r"^https://github.com/", "", repo))}</a>'))
    for c in s.get('chips', []):
        if c.endswith(' designs'):
            rows.append(('Designs', e(c)))
    return '<dl class="reg">' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows) + '</dl>'


def card(s, i, small=False):
    # A handed-over site says so in its chip (and in the hero), so the note is not repeated.
    note = f'<p class="note">{e(s["note"])}</p>' if s.get('note') and not s.get('handed_over') else ''
    wait = f'<p class="wait-note">{e(s["waiting"])}</p>' if s.get('waiting') else ''
    cls = 'site small' if small else 'site'
    if s is hero:
        cls += ' is-hero'
    if s.get('waiting'):
        cls += ' waiting'
    if s.get('handed_over'):
        cls += ' sealed'
    seal = '<span class="seal" aria-hidden="true">Handed<br>over</span>' if s.get('handed_over') else ''
    return f'''<article class="{cls}">
  {seal}{frame(s, i < 3 and not small)}
  <div class="meta">
    <p class="no">Entry {entry_no[s['slug']]:02d}</p>
    <p class="kind">{e(s.get('group') or s['kind'])}</p>
    <h3><a href="{e(s['address']['url'])}">{e(s['name'])}</a></h3>
    {register(s)}
    <p class="sum">{e(s['summary'])}</p>{note}{wait}
    {chips(s)}
    <p class="go"><a href="{e(s['address']['url'])}">{e(host_of(s))} <span aria-hidden="true">&rarr;</span></a></p>
  </div>
</article>'''


demo = next((s for s in sites if s['slug'] == 'pipeline-demo'), None)
steps = ['One request', 'An agent team builds it', 'Five designs to choose from', 'The owner chooses one', "Handed over to the owner's GitHub"]
def chooser(cur):
    opts = ''.join(f'<a href="{h}" data-d="{d}"' + (' data-skin' if h.startswith('/#') or h == '/' else '') + (' aria-current="true"' if d == cur else '')
                   + f'><img src="/shots/hub-design-{d}.jpg" alt="" width="640" height="400" loading="lazy"><span>{d}. {e(n)}</span></a>' for d, n, h in DESIGNS)
    return (f'<details class="chooser"><summary>Design <span class="cur">{cur}</span><span class="nm">: {e(names[cur - 1])}</span></summary>'
            f'<nav class="opts" aria-label="Designs of this page">{opts}</nav></details>')


FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230f6e4f'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' font-weight='700' fill='%23fff' text-anchor='middle'%3ES%3C/text%3E%3C/svg%3E"


def head(title, path, scheme='light dark', extra=''):
    url = SITE_URL + path
    canon = f'\n<link rel="canonical" href="{SITE_URL}">' if path else ''
    return f'''<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="{scheme}">
<link rel="icon" href="{FAVICON}">
<title>{e(title)}</title>{canon}
<meta name="description" content="Websites their owners own: built by agent teams, then handed over. Every site here is public and live.">
<meta property="og:title" content="{e(title)}: websites their owners own">
<meta property="og:description" content="Built by agent teams, then handed over. Every site here is public and live.">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE_URL}og.jpg">
<meta property="og:site_name" content="Sovereign Website Hub">
<meta property="og:locale" content="en_GB">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Sovereign Website Hub: websites their owners own, with screenshots of three people's sites">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}: websites their owners own">
<meta name="twitter:description" content="Built by agent teams, then handed over. Every site here is public and live.">
<meta name="twitter:image" content="{SITE_URL}og.jpg">
{extra}'''


def footer(note):
    return (f'<footer>hub.sovereignweb.site · Part of the <a href="https://github.com/SovereignWebsite">SovereignWebsite</a> organisation · '
            f'<a href="/policy/">How this site is governed</a> · <a href="/operator/">Operator</a> · No cookies, no tracking, nothing stored in your browser. {note}</footer>')

BAR_CSS = r'''
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--fg)}
a{color:inherit}img{display:block;width:100%;height:auto}
.bar{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.55rem 1rem;background:var(--bg);border-bottom:1px solid var(--line);font-size:.9rem}
.brand{font-weight:700;text-decoration:none;white-space:nowrap}
.chooser summary{list-style:none;cursor:pointer;padding:.35rem .9rem;border:1px solid var(--line);border-radius:999px;white-space:nowrap}
.chooser summary::-webkit-details-marker{display:none}.chooser summary::after{content:" \25BE"}
@media (max-width:40rem){.chooser .nm{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
.chooser[open] summary{background:var(--fill);color:var(--on-fill);border-color:var(--fill)}
.opts{position:absolute;right:1rem;top:calc(100% + .4rem);width:min(60rem,calc(100vw - 2rem));display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.75rem;padding:.9rem;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 24px 60px -24px rgba(0,0,0,.45)}
.opts a{text-decoration:none;font-size:.82rem;border-radius:8px;padding:.3rem;border:2px solid transparent}.opts a[aria-current=true]{border-color:var(--fill)}
.opts img{border-radius:6px;border:1px solid var(--line);aspect-ratio:16/10;object-fit:cover;object-position:top}.opts span{display:block;margin-top:.35rem}
@media (max-width:700px){.opts{grid-template-columns:repeat(2,minmax(0,1fr));max-height:75vh;overflow:auto}}
.skip{position:absolute;left:1rem;top:-3rem;z-index:9;padding:.5rem 1rem;background:var(--fill);color:var(--on-fill);border-radius:8px}.skip:focus{top:.5rem}
footer{max-width:78rem;margin:0 auto;padding:1.5rem 1rem 3rem;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line)}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
footer a{color:var(--accent)}
'''

css = r'''
main{max-width:78rem;margin:0 auto;padding:3rem 1rem}
.hero{display:grid;gap:2rem;align-items:center}
@media (min-width:900px){.hero{grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:3.5rem}}
.kicker{text-transform:uppercase;letter-spacing:.16em;font-size:.75rem;font-weight:700;color:var(--accent);margin:0}
.hero h1{margin:.4rem 0 1rem;line-height:1.02;font-size:clamp(2.4rem,6vw,4.6rem);letter-spacing:-.02em}
.hero-text>p{color:var(--muted);font-size:1.1rem;margin:0 0 1rem;max-width:34rem}
.count{display:flex;gap:1.5rem;flex-wrap:wrap;margin:1.4rem 0 0;padding:0;list-style:none}.count li{color:var(--muted);font-size:.9rem}.count b{display:block;font-size:2rem;line-height:1.1;color:var(--fg)}
.hero-shot{display:block}.hero-shot img{object-position:left top}.badge{display:block;padding:.7rem 1rem;font-weight:600;font-size:.95rem;background:var(--fill);color:var(--on-fill)}
.frame{display:block;border-radius:12px;overflow:hidden;background:var(--card);border:1px solid var(--line);text-decoration:none;transition:transform .25s,box-shadow .25s}
.frame:hover,.frame:focus-visible{transform:translateY(-4px);box-shadow:0 18px 40px -18px rgba(0,0,0,.35)}
.frame img{aspect-ratio:16/10;object-fit:cover;object-position:top}
@media (max-width:640px){.frame img{aspect-ratio:4/3}}
.chrome{display:flex;align-items:center;gap:.35rem;padding:.5rem .75rem;border-bottom:1px solid var(--line);background:var(--card);font-size:.75rem;color:var(--muted);min-width:0}
.chrome i{flex:none;width:.6rem;height:.6rem;border-radius:50%;background:var(--line)}.chrome b{font-weight:500;margin-left:.5rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
section{margin-top:4.5rem}.sec-h{font-size:clamp(1.6rem,3.5vw,2.3rem);margin:0 0 1.5rem;line-height:1.1}
.grid{display:grid;grid-template-columns:minmax(0,1fr);gap:2rem}.site{min-width:0}
@media (min-width:640px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (min-width:960px){.people .grid,.tools .grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
.kind{margin:1rem 0 .1rem;font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);font-weight:700}
.site h3{margin:0 0 .35rem;font-size:1.45rem;line-height:1.15}.site h3 a{text-decoration:none}.site h3 a:hover{text-decoration:underline}
.small h3{font-size:1.1rem}.small .sum{font-size:.92rem}
.sum{color:var(--muted);margin:0 0 .6rem}
.note{font-size:.85rem;margin:0 0 .6rem;padding:.3rem .6rem;border-left:3px solid var(--fill);background:var(--card)}
.wait-note{font-size:.85rem;color:var(--muted);margin:0 0 .6rem;font-style:italic}
.chips{display:flex;gap:.4rem;flex-wrap:wrap;margin:.2rem 0 .6rem;padding:0}
.chips span{font-size:.75rem;padding:.12rem .6rem;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.chips .hand{background:var(--fill);border-color:var(--fill);color:var(--on-fill);font-weight:600}.chips .live{color:var(--accent);border-color:var(--accent)}
/* A waiting site is shown by its label and a muted frame; its text keeps full contrast. */
/* On phones the lead screenshot is right above, so the lead site's card drops its own. */
@media (max-width:640px){.is-hero .frame{display:none}}
.waiting .frame{border-style:dashed}.waiting .frame img{filter:grayscale(1) contrast(.85)}
/* Lines only The Register shows. */
.no,.reg,.seal,.part,.tally-n{display:none}
.go{margin:0}.go a{font-weight:600;color:var(--accent);text-decoration:none;overflow-wrap:anywhere}.go a:hover{text-decoration:underline}
.steps{list-style:none;margin:0;padding:0;display:grid;gap:1rem;counter-reset:s}
.steps li{position:relative;padding-left:3rem;min-height:2.2rem;display:flex;align-items:center;font-weight:600}
.steps li::before{counter-increment:s;content:counter(s);position:absolute;left:0;top:0;width:2.2rem;height:2.2rem;border-radius:50%;display:grid;place-items:center;background:var(--fill);color:var(--on-fill);font-weight:700}
@media (min-width:860px){.steps{grid-template-columns:repeat(5,minmax(0,1fr));gap:.5rem}
 .steps li{padding:3.2rem .3rem 0;text-align:center;justify-content:center;align-items:flex-start}
 .steps li::before{left:50%;transform:translateX(-50%)}
 .steps li:not(:last-child)::after{content:"";position:absolute;top:1.1rem;left:calc(50% + 1.4rem);right:calc(-50% + 1.4rem);height:2px;background:var(--line)}}
.made .go{margin-top:1.5rem}
.sec-intro{color:var(--muted);margin:-.8rem 0 1.5rem;max-width:44rem}
.sections{margin-top:3rem}.sections ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:.5rem}
.sections a{display:inline-block;padding:.35rem .9rem;border:1px solid var(--line);border-radius:999px;text-decoration:none;font-size:.92rem;background:var(--card)}
.sections a:hover,.sections a:focus-visible{border-color:var(--fill)}.sections span{color:var(--muted);margin-left:.2rem}
section[id]{scroll-margin-top:4rem}
.how{margin-top:4rem;padding-top:2rem;border-top:1px solid var(--line);color:var(--muted);font-size:.92rem;max-width:46rem}
.how a{color:var(--accent)}

/* Each design has a light and a dark palette; the visitor's setting chooses. --accent is for text, --fill for fills. */
/* 2 The Register: a register of title. Who holds each address, and since when. The lead design. */
.d-2{--bg:#f4f0e6;--fg:#1d2a24;--muted:#4b544f;--accent:#0d5a3f;--fill:#0d5a3f;--on-fill:#fff;--line:#c9c1ae;--card:#fbf8f1;--seal:#9e2a1f;--rule:#1d2a24}
@media (prefers-color-scheme:dark){.d-2{--bg:#121714;--fg:#e9e5da;--muted:#b4b9b3;--accent:#7fd6ae;--fill:#7fd6ae;--on-fill:#121714;--line:#39423d;--card:#18201c;--seal:#ff8a7a;--rule:#e9e5da}}
.d-2 main{max-width:62rem}
.d-2 h1,.d-2 .site h3,.d-2 .sec-h,.d-2 .count b{font-family:Georgia,"Times New Roman",serif}
.d-2 .hero{display:block;border:3px double var(--rule);background:var(--card);padding:clamp(1.2rem,4vw,2.6rem);text-align:center}
.d-2 .hero-shot{display:none}
.d-2 .kicker{font-variant:small-caps;text-transform:none;letter-spacing:.18em;font-size:1rem;font-weight:400;color:var(--fg)}
.d-2 .hero h1{font-weight:700;letter-spacing:0;font-size:clamp(2.2rem,6.5vw,3.8rem);line-height:1.06}
.d-2 .hero-text>p{margin:0 auto 1rem;color:var(--fg)}
.d-2 .count{display:inline-grid;grid-auto-flow:column;gap:1.6rem;border-top:1px solid var(--line);padding-top:.8rem;margin-top:.4rem}
.d-2 .sections{text-align:center}.d-2 .sections ul{justify-content:center}.d-2 .sections a{border-radius:0}
.d-2 section{margin-top:3rem}
.d-2 .sec-h{font-size:1.5rem;font-weight:700;border-bottom:2px solid var(--rule);padding-bottom:.3rem;margin-bottom:1rem;display:flex;justify-content:space-between;gap:1rem;align-items:baseline;flex-wrap:wrap}
.d-2 .part{display:inline}.d-2 .tally-n{display:inline;font:400 .9rem system-ui,sans-serif;color:var(--muted);margin-left:auto}
.d-2 .sec-intro{margin:0 0 1rem}
.d-2 .grid,.d-2 .people .grid,.d-2 .tools .grid{grid-template-columns:minmax(0,1fr);gap:0}
.d-2 .site{position:relative;display:grid;gap:1rem;background:var(--card);border:1px solid var(--line);border-left:6px solid var(--rule);padding:1.1rem;margin:0 0 1rem}
@media (min-width:46rem){.d-2 .site{grid-template-columns:15rem minmax(0,1fr)}}
.d-2 .frame{border-radius:0;align-self:start}.d-2 .frame:hover{transform:none;box-shadow:none}.d-2 .chrome{display:none}
.d-2 .is-hero .frame{display:block}
.d-2 .no{display:block;margin:0;font:.875rem ui-monospace,Menlo,Consolas,monospace;color:var(--muted)}
.d-2 .kind,.d-2 .chips{display:none}
.d-2 .site h3,.d-2 .small h3{font-size:1.35rem;font-weight:700;margin:.1rem 0 .5rem}
.d-2 .reg{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:.25rem .9rem;margin:0 0 .6rem;font-size:.95rem}
.d-2 .reg dt{color:var(--muted);font-variant:small-caps;letter-spacing:.06em}.d-2 .reg dd{margin:0;overflow-wrap:break-word;min-width:0}.d-2 .reg a{color:var(--accent)}
.d-2 .sum,.d-2 .small .sum{color:var(--fg);font-size:1rem}
.d-2 .go a{display:inline-flex;align-items:center;min-height:44px}
.d-2 .seal{display:grid;position:absolute;right:.8rem;top:.8rem;z-index:1;width:5.2rem;height:5.2rem;border:3px solid var(--seal);color:var(--seal);border-radius:50%;place-items:center;text-align:center;font-size:.72rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;line-height:1.15;transform:rotate(-12deg);background:var(--card)}
.d-2 .sealed h3{padding-right:5.6rem}
@media (min-width:46rem){.d-2 .sealed h3{padding-right:0}.d-2 .sealed .meta{padding-right:5.6rem}}
.d-2 .waiting{border-left-style:dashed}
.d-2 .steps li::before{border-radius:0}
@media print{.d-2 .bar,.d-2 nav.family,.d-2 footer{display:none}.d-2 .site{break-inside:avoid}}

'''

hero_note = hero.get('note') or ''
made = '\n' + f'''<section class="made" aria-labelledby="h-made"><h2 class="sec-h" id="h-made">How a site is made</h2>
<ol class="steps">{''.join(f'<li>{e(t)}</li>' for t in steps)}</ol>
{f'<p class="go"><a href="{e(demo["address"]["url"])}">See it run: the pipeline demo <span aria-hidden="true">&rarr;</span></a></p>' if demo else ''}
</section>'''
page = f'''<!doctype html>
<html lang="en" class="d-{LEAD}">
{head('Sovereign Website Hub', '', extra=f'''<script>var P={json.dumps(PAGES)},d=(location.hash.match(/design-([1-5])/)||[])[1];if(P[d])location.replace(P[d]);else if(d)document.documentElement.className='d-'+d;</script>''')}
<style>{BAR_CSS}{css}
{family_css}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the sites</a>
{family}
<header class="bar"><a class="brand" href="/">Sovereign Website Hub</a>
{chooser(LEAD)}</header>
<main id="main">
<header class="hero">
  <div class="hero-text">
    <p class="kicker">The register of title</p>
    <h1>Websites their owners own.</h1>
    <p>Built by agent teams, then handed over: the owner keeps the files, the history and the address. Every site here is public and live; open one to see it working.</p>
    <ul class="count"><li><b>{working}</b>sites working</li><li><b>{len(people)}</b>people's sites</li><li><b>{handed}</b>handed over</li></ul>
  </div>
  <a class="hero-shot frame" href="{e(hero['address']['url'])}" aria-label="Open {e(hero['name'])}"><span class="chrome"><i></i><i></i><i></i><b>{e(host_of(hero))}</b></span><picture><source media="(max-width:640px)" srcset="{e(hero['shot'])}-phone.jpg"><img src="{e(hero['shot'])}.jpg" alt="Screenshot of {e(hero['name'])}" width="1280" height="800" loading="eager"></picture>{f'<span class="badge">{e(hero_note)}</span>' if hero_note else ''}</a>
</header>
<nav class="sections" aria-label="Sections"><ul>{''.join(f'<li><a href="#{sid(n)}">{e(n)} <span>{len(by_section[n])}</span></a></li>' for n, _ in SECTIONS if by_section[n])}</ul></nav>
{chr(10).join(f'''<section class="{'people' if n == 'People' else 'tools'}" id="{sid(n)}" aria-labelledby="h-{sid(n)}"><h2 class="sec-h" id="h-{sid(n)}"><span><span class="part">Part {PARTS[k]}: </span>{e(n)}</span><small class="tally-n"> {len(by_section[n])} {'entry' if len(by_section[n]) == 1 else 'entries'}</small></h2>
<p class="sec-intro">{e(intro)}</p>
<div class="grid">
{chr(10).join(card(s, i, small=(n != 'People')) for i, s in enumerate(by_section[n]))}
</div></section>''' + (made if n == 'People' else '') for k, (n, intro) in enumerate((n, i) for n, i in SECTIONS if by_section[n]))}
<p class="how">Each entry comes from <a href="/sites.json">sites.json</a>, in the <a href="/schema/hub-site.schema.json">hub-site format</a>, and is added when the site goes live. Screenshots are taken from the live sites. Source: <a href="https://github.com/SovereignWebsite/SovereignWebsite__Hub">SovereignWebsite__Hub</a>.</p>
</main>
{footer('Design 2 of 5, The Register, the lead design; the other four are a tap away in the chooser.')}
<script>
(function(){{
  var as=document.querySelectorAll('.opts a'),ch=document.querySelector('.chooser'),cur=document.querySelector('.chooser .cur'),cnm=document.querySelector('.chooser .nm'),nm={json.dumps(names)};
  function set(d){{document.documentElement.className='d-'+d;cur.textContent=d;cnm.textContent=': '+nm[d-1];as.forEach(function(a){{a.setAttribute('aria-current',a.dataset.d===d?'true':'false');}});}}
  function fromHash(){{var m=location.hash.match(/design-([1-5])/);var P={json.dumps(PAGES)};if(m&&P[m[1]]){{location.replace(P[m[1]]);return;}}set(m?m[1]:'{LEAD}');}}
  as.forEach(function(a){{if(a.hasAttribute('data-skin'))a.onclick=function(ev){{ev.preventDefault();history.replaceState(null,'',a.dataset.d==='{LEAD}'?location.pathname:'#design-'+a.dataset.d);set(a.dataset.d);ch.open=false;}};}});
  addEventListener('hashchange',fromHash);fromHash();
  document.addEventListener('keydown',function(ev){{if(ev.key==='Escape')ch.open=false;}});
}})();
</script>
</body>
</html>
'''
(SITE / 'index.html').write_text(page)
print(f'showroom: {len(sites)} live public sites ({len(people)} people, {handed} handed over), {len(names)} designs')


# ---- Design 1, The Gallery: each site hung on a wall with a museum label (design.b round 5, prototype 1). ----
ROOMS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
GALLERY_CSS = r'''
:root{--bg:#1c1a17;--fg:#f3efe6;--muted:#c9c2b4;--accent:#ffcf70;--fill:#ffcf70;--on-fill:#1c1a17;--line:#4a453d;--card:#26231f;--label:#f6f2e8;--label-ink:#1c1a17;--label-muted:#4d473d;--gold:#ffcf70;--family-fg:#cfc8ba;--family-fg-strong:#fff}
a:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
main{max-width:80rem;margin:0 auto;padding:0 1rem;overflow-x:clip}
.intro{padding:2.6rem 0 1rem;text-align:center}
.intro .k{letter-spacing:.3em;text-transform:uppercase;font-size:.875rem;color:var(--gold);margin:0}
.intro h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(2.4rem,7vw,4.6rem);line-height:1.05;margin:.4rem 0 .8rem}
.intro .s{max-width:38rem;margin:0 auto;color:var(--muted)}
.counts{display:flex;justify-content:center;gap:2rem;flex-wrap:wrap;margin:1.2rem 0 0;padding:0;list-style:none;color:var(--muted)}
.counts b{display:block;font-family:Georgia,serif;font-size:2rem;color:var(--fg);font-weight:400}
.rooms{display:flex;flex-wrap:wrap;justify-content:center;gap:.4rem 1.2rem;list-style:none;padding:0;margin:1.6rem 0 0;font-size:.92rem}
.rooms a{color:var(--muted);text-decoration:none}.rooms a:hover{color:var(--fg);text-decoration:underline}
.room{text-align:center;font-family:Georgia,serif;font-size:1.6rem;font-weight:400;margin:2.5rem 0 0;border-top:1px solid var(--line);padding-top:1.6rem;scroll-margin-top:4rem}
.room small{display:block;font-family:system-ui,sans-serif;font-size:.875rem;letter-spacing:.2em;text-transform:uppercase;color:var(--muted)}
.room-intro{text-align:center;color:var(--muted);max-width:40rem;margin:.4rem auto 0;font-size:.95rem}
.wall{display:grid;gap:3.2rem 2.4rem;padding:3.6rem 0 1.4rem;grid-template-columns:minmax(0,1fr)}
@media(min-width:52rem){.wall{grid-template-columns:repeat(2,minmax(0,1fr))}.wall .hero{grid-column:1/-1}}
.piece{display:grid;justify-items:center;gap:1.1rem;text-decoration:none;color:inherit;min-width:0}
.spot{position:relative;display:block;width:100%}
.spot::after{content:"";position:absolute;inset:-40px -20px auto;height:140px;background:radial-gradient(closest-side,rgb(255 236 190/.18),#0000);pointer-events:none}
.frame{position:relative;display:block;background:#0e0d0b;padding:clamp(10px,2vw,22px);border:clamp(8px,1.4vw,14px) solid #3b2f22;box-shadow:0 2px 0 #574634 inset,0 30px 50px -18px rgb(0 0 0/.8);width:100%}
.frame::before{content:"";position:absolute;left:50%;top:-60px;width:1px;height:46px;background:linear-gradient(#0000,#8b7d68)}
.frame img{aspect-ratio:16/10;object-fit:cover;object-position:top}
@media(max-width:40rem){.frame img{aspect-ratio:4/3}}
.hero .frame{border-color:#8a6a2f;max-width:62rem;margin:0 auto}
.label{display:block;background:var(--label);color:var(--label-ink);padding:.8rem 1rem;max-width:26rem;width:100%;box-shadow:0 6px 14px rgb(0 0 0/.4);font-size:.95rem}
.label b{display:block;font-family:Georgia,serif;font-size:1.15rem}
.label .m{display:block;color:var(--label-muted);font-style:italic;overflow-wrap:break-word}
.label .acq{display:block;margin-top:.4rem;padding-top:.4rem;border-top:1px solid #d7cfbf}
.label .tags{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.45rem}
.label .tags span{font-size:.8rem;border:1px solid var(--label-ink);padding:.05rem .45rem;border-radius:2px}
.piece:hover .label b,.piece:focus-visible .label b{text-decoration:underline}
.waiting .frame{border-style:dashed;border-color:#6b6255}
.waiting img{filter:grayscale(1) brightness(.75)}
.how{max-width:44rem;margin:3rem auto 0;padding-top:1.6rem;border-top:1px solid var(--line);color:var(--muted);font-size:.92rem;text-align:center}
.how a{color:var(--gold)}
footer{max-width:80rem}
'''


def piece(s, eager):
    cls = 'piece' + (' hero' if s is hero else '') + (' waiting' if s.get('waiting') else '')
    acq = s['note'] if s.get('handed_over') and s.get('note') else ('Not switched on yet: ' + s['waiting'][:1].lower() + s['waiting'][1:]) if s.get('waiting') else 'Live, open to visit.'
    tags = ''.join(f'<span>{e(x)}</span>' for x in (['Handed over'] if s.get('handed_over') else []) + s.get('chips', []))
    sh = s.get('shot')
    pic = (f'<picture><source media="(max-width:40rem)" srcset="/{e(sh)}-phone.jpg"><img src="/{e(sh)}.jpg" width="1280" height="800" alt=""'
           + ('' if eager else ' loading="lazy" decoding="async"') + '></picture>') if sh else ''
    return (f'<a class="{cls}" href="{e(s["address"]["url"])}"><span class="spot"><span class="frame">{pic}</span></span>'
            f'<span class="label"><b>{e(s["name"])}</b><span class="m">{e(s.get("group") or s["kind"])}, {soft(host_of(s))}</span>{e(s["summary"])}'
            f'<span class="acq">{e(acq)}</span>' + (f'<span class="tags">{tags}</span>' if tags else '') + '</span></a>')


shown = [(n, i) for n, i in SECTIONS if by_section[n]]


def alt_page(d, path, extra_css, main, scheme='dark'):
    # A design that is a page of its own: same head, family bar, chooser and footer as the home page.
    page = f'''<!doctype html>
<html lang="en">
{head(names[d - 1] + ': Sovereign Website Hub', path, scheme=scheme)}
<style>{BAR_CSS}{extra_css}
{family_css}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the sites</a>
{family}
<header class="bar"><a class="brand" href="/">Sovereign Website Hub</a>
{chooser(d)}</header>
{main}
{footer(f'Design {d} of 5, {names[d - 1]}; the lead design is <a href="/">The Register</a>.')}
<script>document.addEventListener('keydown',function(ev){{if(ev.key==='Escape')document.querySelector('.chooser').open=false;}});</script>
</body>
</html>
'''
    (SITE / path).mkdir(exist_ok=True)
    (SITE / path / 'index.html').write_text(page)
    print(f'design {d}, {names[d - 1]}: written to site/{path}')


alt_page(1, 'gallery/', GALLERY_CSS, f'''<main id="main">
<section class="intro" aria-labelledby="g-h"><p class="k">The showroom</p><h1 id="g-h">Websites their owners own.</h1>
<p class="s">Built by agent teams, then handed over: the owner keeps the files, the history and the address. Every site here is public and live; open one to see it working.</p>
<ul class="counts"><li><b>{working}</b>sites working</li><li><b>{len(people)}</b>people's sites</li><li><b>{handed}</b>handed over</li></ul>
<nav aria-label="Rooms"><ul class="rooms">{''.join(f'<li><a href="#g-{sid(n)}">{e(n)}</a></li>' for n, _ in shown)}</ul></nav></section>
{chr(10).join(f"""<section aria-labelledby="g-{sid(n)}"><h2 class="room" id="g-{sid(n)}"><small>Room {ROOMS[k]}</small>{e(n)}</h2>
<p class="room-intro">{e(intro)}</p>
<div class="wall">{''.join(piece(s, k == 0 and i < 1) for i, s in enumerate(by_section[n]))}</div></section>""" for k, (n, intro) in enumerate(shown))}
<p class="how">Each label comes from the hub's <a href="/sites.json">sites.json</a> and is hung when the site goes live; the pictures are taken from the live sites. {f'<a href="{e(demo["address"]["url"])}">See how a site is made: the pipeline demo</a>.' if demo else ''}</p>
</main>''')



# ---- Design 3, Contact Sheet: a photographer's sheet of frames, the chosen one circled (design.b round 5, prototype 3). ----
SHEET_CSS = r'''
:root{--bg:#141414;--fg:#f2f2f0;--muted:#c4c4c0;--accent:#ffb000;--fill:#ffb000;--on-fill:#141414;--line:#3a3a38;--card:#1d1d1c;--sheet:#0a0a0a;--edge:#ffb000;--grease:#ff4d3d;--family-fg:#cfcfcb;--family-fg-strong:#fff}
a:focus-visible,summary:focus-visible{outline:3px solid #ffd400;outline-offset:2px}
main{max-width:80rem;margin:0 auto;padding:0 1rem}
.head{display:grid;gap:1rem;padding:1.6rem 0 1.2rem;border-bottom:1px solid var(--line)}
@media(min-width:56rem){.head{grid-template-columns:1.3fr 1fr;align-items:end}}
.head .k{font-family:ui-monospace,Menlo,Consolas,monospace;color:var(--edge);font-size:.9rem;margin:0;letter-spacing:.08em}
.head h1{font-size:clamp(2.4rem,7.5vw,5rem);line-height:.98;letter-spacing:-.03em;margin:.3rem 0 0;font-weight:800}
.head p{margin:0;color:var(--muted)}
.counts{font-family:ui-monospace,Menlo,Consolas,monospace;color:var(--edge);margin-top:.6rem!important}
.rolls{display:flex;flex-wrap:wrap;gap:.3rem 1rem;list-style:none;padding:0;margin:.8rem 0 0;font:.85rem ui-monospace,Menlo,Consolas,monospace}
.rolls a{color:var(--muted)}.rolls a:hover{color:var(--fg)}
.sheet{background:var(--sheet);margin:1.8rem 0;padding:1rem 0 1.2rem;border-radius:4px;scroll-margin-top:4rem}
.sheet h2{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.95rem;font-weight:600;color:var(--edge);margin:0 1rem .3rem;letter-spacing:.1em;text-transform:uppercase}
.sheet .sub{margin:0 1rem .8rem;color:var(--muted);font-size:.9rem;max-width:44rem}
.strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,19rem),1fr));gap:0;padding:22px 0;position:relative;background:#050505}
.strip::before,.strip::after{content:"";position:absolute;left:0;right:0;height:22px;background:radial-gradient(circle at 50% 50%,#2a2a28 0 4px,#0000 4.5px) 0 0/22px 22px repeat-x}
.strip::before{top:0}.strip::after{bottom:0}
.frame{position:relative;display:block;padding:14px;color:var(--fg);text-decoration:none;min-width:0}
.frame figure{margin:0}
.pic{position:relative;display:block}
.pic img{border:1px solid #222;aspect-ratio:16/10;object-fit:cover;object-position:top}
@media(max-width:40rem){.pic img{aspect-ratio:4/3}}
.num{position:absolute;left:4px;bottom:4px;font:700 .8rem ui-monospace,Menlo,Consolas,monospace;color:var(--edge);background:#000c;padding:.1rem .35rem}
figcaption{padding:.6rem .2rem 0;font-size:.95rem}
figcaption b{display:block;font-size:1.05rem}
figcaption .m{color:var(--muted);overflow-wrap:break-word}
.pick .pic::before{content:"";position:absolute;inset:-10px -6px;border:4px solid var(--grease);border-radius:48% 52% 45% 55%/55% 45% 55% 45%;transform:rotate(-2deg);pointer-events:none;z-index:2}
.mark{position:absolute;right:6px;top:4px;z-index:3;font:800 1rem/1 "Marker Felt","Comic Sans MS",cursive;color:#fff;background:#c9302c;padding:.25rem .5rem;transform:rotate(4deg)}
.x img{filter:grayscale(1) contrast(.8) brightness(.6)}
.x .cross{position:absolute;inset:0;pointer-events:none;background:linear-gradient(to top right,#0000 calc(50% - 2px),var(--grease) calc(50% - 2px) calc(50% + 2px),#0000 calc(50% + 2px))}
.x .mark{font:700 .85rem ui-monospace,monospace;background:#000;color:#fff;border:1px solid var(--grease);padding:.15rem .4rem;transform:none}
.frame:hover figcaption b,.frame:focus-visible figcaption b{text-decoration:underline}
.chip{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.8rem;color:var(--edge)}
.how{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.95rem;color:var(--muted);border-left:3px solid var(--edge);padding-left:1rem;max-width:44rem;margin:2rem 0}
.how a{color:var(--edge)}
footer{max-width:80rem}
'''


def frame_of(s, eager):
    cls = 'frame' + (' pick' if s.get('handed_over') else '') + (' x' if s.get('waiting') else '')
    sh = s.get('shot')
    pic = (f'<picture><source media="(max-width:40rem)" srcset="/{e(sh)}-phone.jpg"><img src="/{e(sh)}.jpg" width="1280" height="800" alt=""'
           + ('' if eager else ' loading="lazy" decoding="async"') + '></picture>') if sh else ''
    mark = ('<span class="mark">Handed over</span>' if s.get('handed_over') else '') + ('<span class="cross" aria-hidden="true"></span><span class="mark">Not switched on yet</span>' if s.get('waiting') else '')
    chip = ' · '.join(s.get('chips', []))
    return (f'<a class="{cls}" href="{e(s["address"]["url"])}"><figure><span class="pic">{pic}<span class="num" aria-hidden="true">{entry_no[s["slug"]]:02d}A</span>{mark}</span>'
            f'<figcaption><b>{e(s["name"])}</b><span class="m">{e(s.get("group") or s["kind"])} · {soft(host_of(s))}</span>'
            + (f'<br><span class="chip">{e(chip)}</span>' if chip else '') + '</figcaption></figure></a>')


steps_line = '; '.join(x[:1].lower() + x[1:] if i else x for i, x in enumerate(steps))
alt_page(3, 'contact-sheet/', SHEET_CSS, f'''<main id="main">
<section class="head" aria-labelledby="c-h"><div><p class="k">ROLL 01 · THE SHOWROOM</p><h1 id="c-h">Websites their owners own.</h1></div>
<div><p>Built by agent teams, then handed over: the owner keeps the files, the history and the address. Every site here is public and live; open one to see it working.</p>
<p class="counts">{working} sites working · {len(people)} people's sites · {handed} handed over</p>
<nav aria-label="Strips"><ul class="rolls">{''.join(f'<li><a href="#c-{sid(n)}">{k + 1}. {e(n)}</a></li>' for k, (n, _) in enumerate(shown))}</ul></nav></div></section>
{chr(10).join(f"""<section class="sheet" id="c-{sid(n)}" aria-labelledby="c-h-{sid(n)}"><h2 id="c-h-{sid(n)}">Strip {k + 1}: {e(n)}</h2><p class="sub">{e(intro)}</p>
<div class="strip">{''.join(frame_of(s, k == 0 and i < 2) for i, s in enumerate(by_section[n]))}</div></section>""" for k, (n, intro) in enumerate(shown))}
<p class="how">How a site is made: {e(steps_line)}. {f'<a href="{e(demo["address"]["url"])}">See it run: the pipeline demo</a>.' if demo else ''}</p>
</main>''')


# ---- Design 4, The Street: every site a shopfront, its address over the door (design.b round 5, prototype 4). ----
STREET_CSS = r'''
:root{--bg:#e9eef2;--fg:#15202b;--muted:#46525e;--accent:#0b4f8a;--fill:#0f6e4f;--on-fill:#fff;--line:#b9c3cc;--card:#f7f3ec;--sky:#cfe0ee;--road:#2d333a;--road-ink:#f3f4f6;--awning1:#0f6e4f;--awning2:#fff;--brick:#f7f3ec;--sign:#15202b;--sign-ink:#fff;--focus:#c2410c}
@media(prefers-color-scheme:dark){:root{--bg:#0d1218;--fg:#e8edf2;--muted:#aab4be;--accent:#8cc8ff;--fill:#1f8a64;--on-fill:#fff;--line:#2c3742;--card:#17202a;--sky:#141d27;--road:#05080b;--road-ink:#e8edf2;--awning1:#1f8a64;--awning2:#0d1218;--brick:#17202a;--sign:#e8edf2;--sign-ink:#0d1218;--focus:#ffa76b}}
a:focus-visible,summary:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.sky{background:linear-gradient(var(--sky),var(--bg));padding:2rem 1rem 1.4rem}
.sky>div{max-width:80rem;margin:0 auto}
.sky .k{font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:.875rem;margin:0;color:var(--muted)}
.sky h1{font-size:clamp(2.4rem,7vw,4.6rem);line-height:1;letter-spacing:-.02em;margin:.4rem 0 .7rem;font-weight:800;max-width:16ch}
.sky p{max-width:40rem}
.streets{display:flex;flex-wrap:wrap;gap:.4rem;list-style:none;padding:0;margin:1rem 0 0}
.streets a{display:inline-block;padding:.3rem .8rem;border:2px solid var(--fg);border-radius:999px;color:var(--fg);text-decoration:none;font-weight:600;font-size:.9rem}
.streets a:hover{background:var(--fg);color:var(--bg)}
.road{background:var(--road);color:var(--road-ink);padding:1.2rem 1rem;position:relative}
.road::before{content:"";position:absolute;left:0;right:0;top:50%;height:4px;background:repeating-linear-gradient(90deg,#f4c542 0 40px,#0000 40px 80px);opacity:.9}
.road ul{list-style:none;margin:0 auto;padding:0;max-width:80rem;display:flex;flex-wrap:wrap;gap:1rem 2.4rem;position:relative}
.road li{background:var(--road);padding:0 .5rem;font-size:.95rem}
.road b{font-size:1.6rem;margin-right:.3rem}
.street{max-width:80rem;margin:0 auto;padding:0 1rem;scroll-margin-top:4rem}
.street h2{font-size:1rem;letter-spacing:.14em;text-transform:uppercase;margin:2.4rem 0 0;color:var(--muted)}
.street .sub{margin:.3rem 0 0;color:var(--muted);max-width:44rem}
.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,22rem),1fr));gap:0 1rem;align-items:end}
.shop{display:block;text-decoration:none;color:var(--fg);margin-top:1.6rem;min-width:0}
.sign{display:block;background:var(--sign);color:var(--sign-ink);font:700 clamp(.85rem,2.4vw,.95rem)/1.2 ui-monospace,Menlo,Consolas,monospace;padding:.55rem .7rem;text-align:center;overflow-wrap:break-word;border-radius:4px 4px 0 0}
.awning{display:block;height:22px;background:repeating-linear-gradient(90deg,var(--awning1) 0 24px,var(--awning2) 24px 48px);clip-path:polygon(0 0,100% 0,97% 100%,3% 100%);border-bottom:2px solid var(--awning1)}
.front{background:var(--brick);border:2px solid var(--line);border-top:0;padding:12px;display:grid;gap:.7rem}
.window{display:block;border:6px solid var(--fg);border-radius:2px;background:#000;position:relative}
.window::after{content:"";position:absolute;inset:0;background:linear-gradient(115deg,rgb(255 255 255/.22),#0000 35%);pointer-events:none}
.window img{aspect-ratio:16/10;object-fit:cover;object-position:top}
@media(max-width:40rem){.window img{aspect-ratio:4/3}}
.plate b{display:block;font-size:1.15rem}
.plate span{color:var(--muted);font-size:.95rem}
.door{display:inline-flex;align-items:center;min-height:44px;padding:.4rem .9rem;border:2px solid var(--fg);border-radius:999px;font-weight:700;justify-self:start}
.shop:hover .door,.shop:focus-visible .door{background:var(--fg);color:var(--bg)}
.board{display:inline-block;background:#0f6e4f;color:#fff;font-weight:800;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;padding:.15rem .5rem;margin:0 .3rem .3rem 0}
.board.alt{background:var(--fg);color:var(--bg)}
.shut .window img{filter:grayscale(1) brightness(.6)}
.shut .awning{background:repeating-linear-gradient(90deg,#6b7480 0 24px,var(--awning2) 24px 48px);border-color:#6b7480}
.shut .door{border-style:dashed}
.kerb{height:10px;background:#9aa3ab;margin-top:2rem}
.how{max-width:80rem;margin:0 auto;padding:1.6rem 1rem 0;color:var(--muted);font-size:.92rem}
.how a{color:var(--accent)}
'''


def shop(s, eager):
    sh = s.get('shot')
    pic = (f'<picture><source media="(max-width:40rem)" srcset="/{e(sh)}-phone.jpg"><img src="/{e(sh)}.jpg" width="1280" height="800" alt=""'
           + ('' if eager else ' loading="lazy" decoding="async"') + '></picture>') if sh else ''
    boards = (['<span class="board">Handed over</span>'] if s.get('handed_over') else []) + [f'<span class="board alt">{e(x)}</span>' for x in s.get('chips', [])]
    words = ('Not switched on yet: ' + s['waiting'][:1].lower() + s['waiting'][1:]) if s.get('waiting') else s['summary']
    return (f'<a class="shop{" shut" if s.get("waiting") else ""}" href="{e(s["address"]["url"])}"><span class="sign">{soft(host_of(s))}</span>'
            f'<span class="awning" aria-hidden="true"></span><span class="front"><span class="window">{pic}</span>'
            f'<span class="plate"><b>{e(s["name"])}</b><span>{e(s.get("group") or s["kind"])}. {e(words)}</span></span>'
            + (f'<span>{"".join(boards)}</span>' if boards else '')
            + f'<span class="door">{"Not switched on yet" if s.get("waiting") else "Walk in &rarr;"}</span></span></a>')


alt_page(4, 'street/', STREET_CSS, f'''<main id="main">
<section class="sky" aria-labelledby="st-h"><div><p class="k">The showroom</p><h1 id="st-h">Websites their owners own.</h1>
<p>Built by agent teams, then handed over: the owner keeps the files, the history and the address. Every site here is public and live; open one to see it working.</p>
<nav aria-label="Streets"><ul class="streets">{''.join(f'<li><a href="#st-{sid(n)}">{e(n)}</a></li>' for n, _ in shown)}</ul></nav></div></section>
<section class="road" aria-label="On this street"><ul><li><b>{working}</b>sites working</li><li><b>{len(people)}</b>people's sites</li><li><b>{handed}</b>handed over</li></ul></section>
{chr(10).join(f"""<section class="street" id="st-{sid(n)}" aria-labelledby="st-h-{sid(n)}"><h2 id="st-h-{sid(n)}">{e(n)}</h2><p class="sub">{e(intro)}</p>
<div class="row">{''.join(shop(s, k == 0 and i < 2) for i, s in enumerate(by_section[n]))}</div></section>
<div class="kerb" aria-hidden="true"></div>""" for k, (n, intro) in enumerate(shown))}
<p class="how">Every shop's details come from the hub's <a href="/sites.json">sites.json</a>; the windows are screenshots of the live sites. {f'<a href="{e(demo["address"]["url"])}">See how a site is made: the pipeline demo</a>.' if demo else ''}</p>
</main>''', scheme='light dark')


# ---- Design 5, The Line: one request in, a handed-over site out, each person's site at its station (design.b round 5, prototype 5). ----
LINE_CSS = r'''
:root{--bg:#fafafa;--fg:#111;--muted:#4a4a4a;--accent:#0040c1;--fill:#111;--on-fill:#fff;--line:#d4d4d4;--card:#fff;--belt:#111;--hi:#ffd60a;--hi-ink:#111;--done:#0b7a43;--focus:#e4002b}
@media(prefers-color-scheme:dark){:root{--bg:#0b0b0b;--fg:#f2f2f2;--muted:#b8b8b8;--accent:#8fb4ff;--fill:#f2f2f2;--on-fill:#0b0b0b;--line:#2e2e2e;--card:#151515;--belt:#f2f2f2;--hi:#ffd60a;--hi-ink:#111;--done:#4fd18b;--focus:#ff6b81}}
a:focus-visible,summary:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
main{max-width:80rem;margin:0 auto;padding:0 1rem}
.k{font-weight:800;font-size:.875rem;letter-spacing:.16em;text-transform:uppercase;margin:1.6rem 0 0}
main h1{font-size:clamp(2.4rem,8vw,5.4rem);line-height:.95;letter-spacing:-.035em;margin:.3rem 0 .8rem;font-weight:900;max-width:14ch}
.lede{max-width:40rem;font-size:1.1rem}
.counts{display:flex;gap:.6rem;flex-wrap:wrap;list-style:none;padding:0;margin:1rem 0 0}
.counts li{border:2px solid var(--fg);padding:.3rem .7rem;font-weight:700}
.line{list-style:none;margin:2.8rem 0;padding:0 0 0 1.3rem;display:grid;gap:0;counter-reset:st}
@media(min-width:60rem){.line{grid-template-columns:repeat(5,minmax(0,1fr));padding:0}}
.st{position:relative;padding:1rem 1rem 1.2rem 2.2rem;border-left:4px solid var(--belt);counter-increment:st;min-width:0}
@media(min-width:60rem){.st{border-left:0;border-top:4px solid var(--belt);padding:2.4rem .8rem 1rem}}
.st::before{content:counter(st);position:absolute;left:-1.35rem;top:.9rem;width:2.3rem;height:2.3rem;border-radius:50%;background:var(--bg);border:4px solid var(--belt);display:grid;place-items:center;font-weight:900}
@media(min-width:60rem){.st::before{left:.8rem;top:-1.35rem}}
.st h2{font-size:1.1rem;margin:0 0 .6rem;line-height:1.2}
.st.end{border-color:var(--done)}
.st.end::before{background:var(--done);color:var(--bg);border-color:var(--done)}
.here{list-style:none;padding:0;margin:0;display:grid;gap:.6rem}
.card{display:block;color:var(--fg);text-decoration:none;border:2px solid var(--fg);background:var(--bg);min-width:0}
.card img{aspect-ratio:16/10;object-fit:cover;object-position:top}
@media(max-width:40rem){.card img{aspect-ratio:4/3}}
.card b{display:block;padding:.45rem .6rem 0}
.card .m{display:block;padding:0 .6rem .5rem;font-size:.9rem;color:var(--muted);overflow-wrap:break-word}
.card:hover,.card:focus-visible{background:var(--hi);color:var(--hi-ink)}
.card:hover .m,.card:focus-visible .m{color:var(--hi-ink)}
.card.big{border-width:3px;border-color:var(--done)}
.card.big b{font-size:1.2rem}
.card .tag{display:inline-block;background:var(--hi);color:var(--hi-ink);font-weight:800;font-size:.8rem;padding:.05rem .4rem;margin:0 .6rem .5rem}
.empty{font-size:.9rem;color:var(--muted);margin:0 0 .6rem}
.side{border-top:4px solid var(--belt);padding-top:1rem;margin-top:2.4rem;scroll-margin-top:4rem}
.side h2{font-size:1.4rem;margin:0 0 .4rem}
.side p{margin:0;max-width:44rem}
.side .row{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,17rem),1fr));gap:1rem;margin-top:1rem}
.card.off{border-style:dashed}
.card.off img{filter:grayscale(1)}
.side a:not(.card){color:var(--accent)}
'''


def lcard(s, eager, pic=True, big=False):
    sh = s.get('shot') if pic else None
    img = (f'<picture><source media="(max-width:40rem)" srcset="/{e(sh)}-phone.jpg"><img src="/{e(sh)}.jpg" width="1280" height="800" alt=""'
           + ('' if eager else ' loading="lazy" decoding="async"') + '></picture>') if sh else ''
    line2 = ('Not switched on yet: ' + s['waiting'][:1].lower() + s['waiting'][1:]) if s.get('waiting') else soft(host_of(s))
    line2 = e(line2) if s.get('waiting') else line2
    tags = ''.join(f'<span class="tag">{e(x)}</span>' for x in s.get('chips', []))
    cls = 'card' + (' big' if big else '') + (' off' if s.get('waiting') else '')
    return f'<a class="{cls}" href="{e(s["address"]["url"])}">{img}<b>{e(s["name"])}</b><span class="m">{line2}</span>' + (f'<span>{tags}</span>' if tags else '') + '</a>'


# A station with more than three sites shows compact cards, so the line stays readable.
# Each person's site at the station its record shows: handed over at the end, five designs at station 3, the rest built and live at 2.
at_end = [s for s in people if s.get('handed_over')]
many = lambda s: any(c in ('Five designs', 'Six designs') for c in s.get('chips', []))
at_five = [s for s in people if not s.get('handed_over') and many(s)]
at_built = [s for s in people if s not in at_end and s not in at_five]
STATIONS = [
    (steps[0], [], 'Every site starts here: one request, from its owner.'),
    (steps[1], at_built, 'Built and live, open to visit.'),
    (steps[2], at_five, ''),
    (steps[3], [], 'The owner picks the design they want to keep.'),
    (steps[4], at_end, ''),
]


def station(i, title, here, note):
    cards = ''.join(f'<li>{lcard(s, i == 4, pic=(len(here) <= 3), big=(i == 4))}</li>' for s in here)
    return (f'<li class="st{" end" if i == 4 else ""}"><h2>{e(title)}</h2>' + (f'<p class="empty">{e(note)}</p>' if note else '')
            + (f'<ul class="here">{cards}</ul>' if cards else '') + '</li>')


others = [(n, i) for n, i in shown if n != 'People']
alt_page(5, 'line/', LINE_CSS, f'''<main id="main">
<p class="k">The showroom</p><h1>Websites their owners own.</h1>
<p class="lede">Built by agent teams, then handed over: the owner keeps the files, the history and the address. Every site here is public and live; open one to see it working.</p>
<ul class="counts"><li>{working} sites working</li><li>{len(people)} people's sites</li><li>{handed} handed over</li></ul>
<ol class="line" aria-label="How a site is made, with each person's site where it stands">{''.join(station(i, *x) for i, x in enumerate(STATIONS))}</ol>
{chr(10).join(f"""<section class="side" id="l-{sid(n)}" aria-labelledby="l-h-{sid(n)}"><h2 id="l-h-{sid(n)}">{e(n)}</h2><p>{e(intro)}""" + (f""" Built the same way. <a href="{e(demo['address']['url'])}">See it run: the pipeline demo</a>.""" if demo and n == 'Demos' else '') + f"""</p>
<div class="row">{''.join(lcard(s, False) for s in by_section[n])}</div></section>""" for n, intro in others)}
</main>''', scheme='light dark')
