#!/usr/bin/env python3
# Builds the hub's showroom from site/sites.json: five designs of the same register of public sites, each a page.
#   1 The Register (the lead, the home page)   2 The Gallery   3 Contact Sheet   4 The Street   5 The Line
# plus /designs/, the five side by side. The designs are design.b's round 5 ideas; their CSS is in tools/showroom/.
# Only public, live sites are listed; a private or vault-only site never appears, not by name or count.
# Usage: python3 tools/build-showroom.py   (validates sites.json against the schema first; run tools/thumbs.py after new shots)
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
CSS = ROOT / 'tools' / 'showroom'
data = json.loads((SITE / 'sites.json').read_text())
schema = json.loads((SITE / 'schema' / 'hub-site.schema.json').read_text())
try:
    import jsonschema
    for s in data['sites']:
        jsonschema.validate(s, schema)
except ImportError:
    print('note: jsonschema not installed, schema not checked', file=sys.stderr)

# The family bar is kept as it is on the live home page (its keeper updates it there).
old = (SITE / 'index.html').read_text() if (SITE / 'index.html').exists() else ''
family = re.search(r'<nav class="family".*?</nav>', old, re.S)
family_css = re.search(r'\.family\{.*?(?=\n</style>|\n#|\n\.d-)', old, re.S)
family = family.group(0) if family else ''
family_css = family_css.group(0) if family_css else ''

e = lambda x: html.escape(str(x), quote=True)
host_of = lambda s: re.sub(r'^https?://|/$', '', s['address']['url'])
css = lambda name: (CSS / f'{name}.css').read_text()
sites = [s for s in data['sites'] if s.get('status') == 'live']
# Featured (hand-picked rank) first; a site still waiting on something goes last.
sites.sort(key=lambda s: (bool(s.get('waiting')), s.get('featured', 10**6)))
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
shown = [(n, i) for n, i in SECTIONS if by_section[n]]
people = by_section['People']
sid = lambda n: 's-' + re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
# The lead entry: the first site handed over to its owner (Kate's), shown first in every design.
lead = next((s for s in people if s.get('handed_over')), people[0] if people else sites[0])
rest = lambda n: [s for s in by_section[n] if s is not lead]
handed = sum(1 for s in sites if s.get('handed_over'))
working = sum(1 for s in sites if not s.get('waiting'))
people_working = sum(1 for s in people if not s.get('waiting'))
waiting = len(sites) - working
demo = next((s for s in sites if s['slug'] == 'pipeline-demo'), None)
steps = ['One request', 'An agent team builds it', 'Five designs to choose from', 'The owner chooses one', "Handed over to the owner's GitHub"]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
long_date = lambda d: f"{int(d[8:10])} {MONTHS[int(d[5:7]) - 1]} {d[:4]}"
entry_no = {s['slug']: i + 1 for i, s in enumerate(x for n, _ in SECTIONS for x in by_section[n])}
SITE_URL = 'https://hub.sovereignweb.site/'

# The five designs: number, name, page, the idea in a line, and whether it is dark only.
DESIGNS = [
    (1, 'The Line', '/', 'One request in, a handed-over site out, each site at its station.', False),
    (2, 'The Register', '/register/', 'A register of title: who holds each address, and since when.', False),
    (3, 'The Gallery', '/gallery/', 'Each site hung on a wall with a museum label.', True),
    (4, 'Contact Sheet', '/contact-sheet/', "A photographer's sheet of frames, the chosen one circled.", True),
    (5, 'The Street', '/street/', 'Every site a shopfront, its address over the door.', False),
]
names = [d[1] for d in DESIGNS]

# The same words in every design.
COUNTS = (f"{working} sites working, {people_working} of them people's own; {handed} handed over to its owner so far."
          + (f" Plus {waiting} not switched on yet." if waiting else ''))
ABOUT = 'Built by agent teams, then handed over: the owner keeps the files, the history and the address. Every site here is public; open one to see it working.'
# There is no request form yet; say so, and point to how it works.
WANT = ('Want one? It starts with one request. There is no request form yet: '
        '<a href="/start/#get-one">here is how to start</a>.')
# The last step of every design: get one.
GET = ('<section class="get" aria-labelledby="get-h"><h2 id="get-h">Get one</h2><p>Every site here began with one request '
       'and was handed over to its owner. <a href="/start/#get-one">Start here: how to get a site like these</a>.</p></section>')
STEPS_LINE = '; '.join(x[:1].lower() + x[1:] if i else x for i, x in enumerate(steps))
DEMO_LINK = f' <a href="{e(demo["address"]["url"])}">See it run: the pipeline demo</a>.' if demo else ''


def soft(text):
    # Wrap an address only at a dot, never inside a name; the domain (last two labels) stays whole.
    labels = text.split('.')
    groups = [l + '.' for l in labels[:-2]] + ['.'.join(labels[-2:])] if len(labels) > 2 else [text]
    return '<wbr>'.join(f'<span class="nw">{e(g)}</span>' for g in groups)


def soft_path(text):
    # A repository path wraps after its slash or a double underscore.
    parts = re.split(r'(?<=/)|(?<=__)', text)
    return '<wbr>'.join(f'<span class="nw">{e(p)}</span>' for p in parts if p)


def waiting_line(s):
    w = s['waiting']
    return w if w.lower().startswith('not switched on yet') else 'Not switched on yet: ' + w[:1].lower() + w[1:]


CROPS = json.loads((CSS / 'crops.json').read_text())


def credit(s):
    c = CROPS.get(s['slug'])
    return f'<span class="credit">{e(c["credit"])}</span>' if isinstance(c, dict) and c.get('credit') and (SITE / 'shots' / f'{s["slug"]}-portrait.jpg').exists() else ''


def pic(s, eager=False, sizes='(min-width:52rem) 40vw, 100vw', alt='', lead=False):
    # Phones get the phone crop; wider screens a 480 or 960 WebP (JPEG 640 or 1280 where WebP is not supported).
    sh = s.get('shot')
    if not sh:
        return ''
    lazy = '' if eager else ' loading="lazy" decoding="async"'
    # A lead entry with a portrait crop shows the person on a phone, not their site's menu bar.
    phone = f'{sh}-portrait' if lead and credit(s) else f'{sh}-phone'
    return (f'<picture><source media="(max-width:40rem)" type="image/webp" srcset="/{e(phone)}.webp">'
            f'<source media="(max-width:40rem)" srcset="/{e(phone)}.jpg">'
            f'<source type="image/webp" srcset="/{e(sh)}-480.webp 480w, /{e(sh)}-960.webp 960w" sizes="{sizes}">'
            f'<img src="/{e(sh)}-640.jpg" srcset="/{e(sh)}-640.jpg 640w, /{e(sh)}.jpg 1280w" sizes="{sizes}" width="1280" height="800" alt="{e(alt)}"{lazy}></picture>')


def chooser(cur):
    opts = ''.join(f'<a href="{h}"' + (' aria-current="page"' if d == cur else '')
                   + f'><img src="/shots/hub-design-{d}.jpg" alt="" width="640" height="400" loading="lazy"><span>{d}. {e(n)}{" (home)" if h == "/" else ""}{" (dark)" if dark else ""}</span></a>'
                   for d, n, h, _, dark in DESIGNS)
    label = (f'<span class="dw">Design </span><span class="cur">{cur}</span><span class="dw">:</span> {e(names[cur - 1])}') if cur else 'Five designs'
    return (f'<details class="chooser"><summary>{label}</summary>'
            f'<nav class="opts" aria-label="Designs of this page">{opts}<a href="/designs/"' + (' aria-current="page"' if not cur else '')
            + '><span>All five, side by side</span></a></nav></details>')


FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230f6e4f'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' font-weight='700' fill='%23fff' text-anchor='middle'%3ES%3C/text%3E%3C/svg%3E"


def page(path, title, style, main, scheme='light dark', cur=0, note='', script=''):
    # Every page: the same head, family bar, chooser and footer. The version chip is added by the pipeline.
    url = SITE_URL + path
    canon = f'\n<link rel="canonical" href="{SITE_URL}">' if path else ''
    full = title if not path else f'{title}: Sovereign Website Hub'
    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="{scheme}">
<link rel="icon" href="{FAVICON}">
<title>{e(full)}</title>{canon}
<meta name="description" content="Websites their owners own: built by agent teams, then handed over. Every site here is public and live.">
<meta property="og:title" content="{e(full)}: websites their owners own">
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
<meta name="twitter:title" content="{e(full)}: websites their owners own">
<meta name="twitter:description" content="Built by agent teams, then handed over. Every site here is public and live.">
<meta name="twitter:image" content="{SITE_URL}og.jpg">{script}
<style>{css('bar')}{style}
{family_css}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the sites</a>
{family}
<header class="bar"><a class="brand" href="/">Sovereign Website Hub</a>
{chooser(cur)}</header>
{main}
<footer>hub.sovereignweb.site · Part of the <a href="https://github.com/SovereignWebsite">SovereignWebsite</a> organisation · <a href="/designs/">The five designs</a> · <a href="/features/">What it can do</a> · <a href="/policy/">How this site is governed</a> · <a href="/operator/">Operator</a> · No cookies, no tracking, nothing stored in your browser. {note}</footer>
<script>document.addEventListener('keydown',function(ev){{if(ev.key==='Escape'){{var c=document.querySelector('.chooser');if(c)c.open=false;}}}});</script>
</body>
</html>
'''
    (SITE / path).mkdir(parents=True, exist_ok=True)
    (SITE / path / 'index.html').write_text(doc)


def design_note(d):
    return f'Design {d} of 5, {names[d - 1]}' + ('; the lead design is <a href="/">The Line</a>.' if d != 1 else ', the lead design. <a href="/designs/">See all five</a>.')


# ---- 1 The Register (home page) ----
def deed(s):
    rows = [('Address', f'<a href="{e(s["address"]["url"])}">{soft(host_of(s))}</a>'), ('Kind', e(s.get('group') or s['kind']))]
    if s.get('handed_over'):
        rows.append(('Held', f"By its owner, since {e(long_date(s['handed_over']))}"))
    elif s.get('section') == 'People':
        rows.append(('Held', 'SovereignWebsite, until handed over'))
    else:
        rows.append(('Held', e(s['owner']['name'])))
    rows.append(('Status', 'Handed over' if s.get('handed_over') else e(waiting_line(s)) if s.get('waiting') else 'Live'))
    repo = (s.get('repository') or {}).get('url')
    if repo:
        rows.append(('Files', f'<a href="{e(repo)}">{soft_path(re.sub(r"^https://github.com/", "", repo))}</a>'))
    rows += [('Designs', e(c)) for c in s.get('chips', []) if c.endswith(' designs')]
    return '<dl>' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows) + '</dl>'


def entry(s, is_lead=False):
    cls = 'title' + (' lead' if is_lead else '') + (' sealed' if s.get('handed_over') else '') + (' pending' if s.get('waiting') else '')
    seal = '<span class="seal" aria-hidden="true">Handed<br>over</span>' if s.get('handed_over') else ''
    hid = 't-' + s['slug']
    hn = 'h2' if is_lead else 'h3'
    return (f'<article class="{cls}" aria-labelledby="{hid}"><div class="shot">{seal}{pic(s, is_lead, "(min-width:46rem) 22rem, 7rem" if is_lead else "(min-width:46rem) 15rem, 7rem", lead=is_lead)}{credit(s) if is_lead else ""}</div>'
            f'<div class="meta"><p class="no">Entry {entry_no[s["slug"]]:02d}</p><{hn} id="{hid}"><a href="{e(s["address"]["url"])}">{e(s["name"])}</a></{hn}>'
            f'<p class="sum">{e(s["summary"])}</p>'
            f'<details class="deed"{" open" if is_lead else ""}><summary>The register entry</summary>{deed(s)}</details>'
            f'<p class="go"><a href="{e(s["address"]["url"])}">Visit <span class="sr">{e(s["name"])} at </span>{soft(host_of(s))}&nbsp;&rarr;</a></p></div></article>')


PARTS = 'ABCDEFGHIJ'
SHOW = 3


def fold(n, render, box, where):
    # First three in the box; the rest in a "Show all" disclosure holding a second box of the same kind.
    # On a phone only two show; the third is hidden there and repeated as the first inside the disclosure
    # (display:none on the copy that does not apply, so each site is read once).
    es = rest(n)
    if len(es) <= 2:
        return f'<div class="{box}">{"".join(render(s) for s in es)}</div>'
    first = ''.join(render(s) for s in es[:2]) + ''.join(f'<div class="wide-only">{render(s)}</div>' for s in es[2:SHOW])
    inner = ''.join(f'<div class="phone-only">{render(s)}</div>' for s in es[2:SHOW]) + ''.join(render(s) for s in es[SHOW:])
    hidden_wide = len(es) - SHOW
    summary = f'Show all {len(by_section[n])} in {e(where)}'
    if hidden_wide <= 0:
        return f'<div class="{box}">{first}</div><details class="more phone-only"><summary>{summary}</summary><div class="{box}">{inner}</div></details>'
    return f'<div class="{box}">{first}</div><details class="more"><summary>{summary}</summary><div class="{box}">{inner}</div></details>'


def street_people():
    # Wide screens show the first two people's shops beside Kate's in the sky, so their street starts at the
    # fourth; a phone shows them here. Each copy is display:none where it does not apply, so each is read once.
    es = rest('People')
    summary = f'Show all {len(by_section["People"])} in People'
    phone_more = ''.join(shop(s) for s in es[2:])
    wide_more = ''.join(shop(s) for s in es[5:])
    return (f'<div class="row">{"".join(f"<div class=phone-only>{shop(s)}</div>" for s in es[:2])}'
            f'{"".join(f"<div class=wide-only>{shop(s)}</div>" for s in es[2:5])}</div>'
            + (f'<div class="phone-only"><details class="more"><summary>{summary}</summary><div class="row">{phone_more}</div></details></div>' if phone_more else '')
            + (f'<div class="wide-only"><details class="more"><summary>{summary}</summary><div class="row">{wide_more}</div></details></div>' if wide_more else ''))


def phone_fold(items, box, summary):
    # Wide screens show every item; a phone shows two and folds the rest into "Show all" (each item read once).
    if len(items) <= 2:
        return f'<div class="{box}">{"".join(items)}</div>'
    return (f'<div class="{box}">{"".join(items[:2])}{"".join(f"<div class=wide-only>{x}</div>" for x in items[2:])}</div>'
            f'<details class="more phone-only"><summary>{summary}</summary><div class="{box}">{"".join(items[2:])}</div></details>')


def entries(n, k):
    # Each part shows its first three entries; the rest fold into a disclosure that works without script.
    es = rest(n)
    more = es[SHOW:]
    out = ''.join(entry(s) for s in es[:SHOW])
    if more:
        out += (f'<details class="more"><summary>Show all {len(by_section[n])} entries in Part {PARTS[k]}, {e(n)} '
                f'<span class="sr">({len(more)} more)</span></summary>{"".join(entry(s) for s in more)}</details>')
    return out


register_main = f'''<main id="main">
<section class="cover" aria-labelledby="r-h"><p class="k">The register of title</p><h1 id="r-h">Websites their owners own.</h1>
<p class="lede">{e(ABOUT)} <span class="tally">{e(COUNTS)}</span></p>
{entry(lead, True)}
<div class="about"><p class="want">{WANT}</p>
<nav aria-label="Parts of the register"><ul class="parts">{''.join(f'<li><a href="#{sid(n)}">Part {PARTS[k]}: {e(n)}</a></li>' for k, (n, _) in enumerate(shown))}</ul></nav></div></section>
{chr(10).join(f"""<section class="part" id="{sid(n)}" aria-labelledby="h-{sid(n)}"><h2 id="h-{sid(n)}"><span>Part {PARTS[k]}: {e(n)}</span><small>{len(by_section[n])} {'entry' if len(by_section[n]) == 1 else 'entries'}{', Entry 01 above' if lead in by_section[n] else ''}</small></h2>
<p class="intro">{e(intro)}</p>
{entries(n, k)}</section>""" for k, (n, intro) in enumerate(shown))}
<p class="how">How a site is made: {e(STEPS_LINE)}.{DEMO_LINK} Each entry comes from <a href="/sites.json">sites.json</a>, in the <a href="/schema/hub-site.schema.json">hub-site format</a>; the screenshots are taken from the live sites. Source: <a href="https://github.com/SovereignWebsite/SovereignWebsite__Hub">SovereignWebsite__Hub</a>.</p>
{GET}
</main>'''
# Old #design-N addresses on the home page (the skins it used to carry) forward to the page that design now is.
FORWARD = json.dumps({str(d): h for d, _, h, _, _ in DESIGNS if h != '/'})
# Wide screens open each register entry; on a phone they stay folded so the page is short.
HOME_SCRIPT = f"\n<script>var F={FORWARD},m=location.hash.match(/^#design-([1-5])$/);if(m&&F[m[1]])location.replace(F[m[1]]);</script>"
REG_SCRIPT = ("\n<script>"
              "addEventListener('DOMContentLoaded',function(){if(matchMedia('(min-width:46rem)').matches)document.querySelectorAll('details.deed').forEach(function(d){d.open=true;});});</script>")
page('register/', 'The Register', css('register'), register_main, cur=2, note=design_note(2), script=REG_SCRIPT)


# ---- 2 The Gallery ----
ROOMS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']


def piece(s, is_lead=False):
    cls = 'piece' + (' hero' if is_lead else '') + (' waiting' if s.get('waiting') else '')
    acq = s['note'] if s.get('handed_over') and s.get('note') else waiting_line(s) if s.get('waiting') else 'Live, open to visit.'
    tags = ''.join(f'<span>{e(x)}</span>' for x in (['Handed over'] if s.get('handed_over') else []) + s.get('chips', []))
    return (f'<a class="{cls}" href="{e(s["address"]["url"])}"><span class="spot"><span class="frame">{pic(s, is_lead, "(min-width:52rem) 62rem, 100vw" if is_lead else "(min-width:52rem) 38rem, 100vw", lead=is_lead)}</span>{credit(s) if is_lead else ""}</span>'
            f'<span class="label"><b>{e(s["name"])}</b><span class="m">{e(s.get("group") or s["kind"])}, {soft(host_of(s))}</span><span class="sum">{e(s["summary"])}</span>'
            f'<span class="acq">{e(acq)}</span>' + (f'<span class="tags">{tags}</span>' if tags else '') + '</span></a>')


page('gallery/', 'The Gallery', css('gallery'), f'''<main id="main">
<section class="intro" aria-labelledby="g-h"><p class="k">The showroom</p><h1 id="g-h">Websites their owners own.</h1>
<p class="lede">{e(ABOUT)} <span class="tally">{e(COUNTS)}</span></p>
<div class="wall lead-wall">{piece(lead, True)}</div>
<div class="about"><p class="want">{WANT}</p>
<nav aria-label="Rooms"><ul class="rooms">{''.join(f'<li><a href="#g-{sid(n)}">{e(n)}</a></li>' for n, _ in shown)}</ul></nav></div></section>
{chr(10).join(f"""<section aria-labelledby="g-{sid(n)}"><h2 class="room" id="g-{sid(n)}"><small>Room {ROOMS[k]}</small>{e(n)}</h2>
<p class="room-intro">{e(intro)}</p>
{fold(n, piece, 'wall', f'Room {ROOMS[k]}, {n}')}</section>""" for k, (n, intro) in enumerate(shown))}
<p class="how">Each label comes from the hub's <a href="/sites.json">sites.json</a> and is hung when the site goes live; the pictures are taken from the live sites. How a site is made: {e(STEPS_LINE)}.{DEMO_LINK}</p>
{GET}
</main>''', scheme='dark', cur=3, note=design_note(3))


# ---- 3 Contact Sheet ----
def frame_of(s, eager):
    cls = 'frame' + (' pick' if s.get('handed_over') else '') + (' x' if s.get('waiting') else '')
    cross = '<span class="cross" aria-hidden="true"></span>' if s.get('waiting') else ''
    mark = '<span class="mark">Handed over</span>' if s.get('handed_over') else '<span class="mark">Not switched on yet</span>' if s.get('waiting') else ''
    chip = ' · '.join(s.get('chips', []))
    return (f'<a class="{cls}" href="{e(s["address"]["url"])}"><figure><span class="pic">{pic(s, eager, "(min-width:40rem) 20rem, 100vw", lead=s is lead)}{cross}'
            f'<span class="rebate"><span class="num">{entry_no[s["slug"]]:02d}A</span>{mark}</span></span>'
            f'<figcaption><b>{e(s["name"])}</b><span class="m">{e(s.get("group") or s["kind"])} · {soft(host_of(s))}</span>'
            + (f'<br><span class="chip">{e(chip)}</span>' if chip else '') + (credit(s) if s is lead else '') + '</figcaption></figure></a>')


page('contact-sheet/', 'Contact Sheet', css('contact-sheet'), f'''<main id="main">
<section class="head" aria-labelledby="c-h"><div><p class="k">ROLL 01 · THE SHOWROOM</p><h1 id="c-h">Websites their owners own.</h1></div>
<div><p>{e(ABOUT)}</p>
<p class="counts">{e(COUNTS)}</p><p class="want">{WANT}</p>
<nav aria-label="Strips"><ul class="rolls">{''.join(f'<li><a href="#c-{sid(n)}">{k + 1}. {e(n)}</a></li>' for k, (n, _) in enumerate(shown))}</ul></nav></div></section>
{chr(10).join(f"""<section class="sheet" id="c-{sid(n)}" aria-labelledby="c-h-{sid(n)}"><h2 id="c-h-{sid(n)}">Strip {k + 1}: {e(n)}</h2><p class="sub">{e(intro)}</p>
{phone_fold([frame_of(s, k == 0 and i < 2) for i, s in enumerate(by_section[n])], 'strip', f'Show all {len(by_section[n])} frames in strip {k + 1}')}</section>""" for k, (n, intro) in enumerate(shown))}
<p class="how">How a site is made: {e(STEPS_LINE)}.{DEMO_LINK}</p>
{GET}
</main>''', scheme='dark', cur=4, note=design_note(4))


# ---- 4 The Street ----
def shop(s, is_lead=False):
    boards = (['<span class="board">Handed over</span>'] if s.get('handed_over') else []) + [f'<span class="board alt">{e(x)}</span>' for x in s.get('chips', [])]
    words = waiting_line(s) if s.get('waiting') else s['summary']
    return (f'<a class="shop{" shut" if s.get("waiting") else ""}{" lead" if is_lead else ""}" href="{e(s["address"]["url"])}"><span class="sign">{soft(host_of(s))}</span>'
            f'<span class="awning" aria-hidden="true"></span><span class="front"><span class="window">{pic(s, is_lead, "(min-width:52rem) 26rem, 100vw", lead=is_lead)}</span>{credit(s) if is_lead else ""}'
            f'<span class="plate"><b>{e(s["name"])}</b><span>{e(s.get("group") or s["kind"])}. {e(words)}</span></span>'
            + (f'<span>{"".join(boards)}</span>' if boards else '')
            + f'<span class="door">{"Not switched on yet" if s.get("waiting") else "Walk in &rarr;"}</span></span></a>')


page('street/', 'The Street', css('street'), f'''<main id="main">
<section class="sky" aria-labelledby="st-h"><div><p class="k">The showroom</p><h1 id="st-h">Websites their owners own.</h1>
<p class="lede">{e(ABOUT)}</p>
<div class="lead-row">{shop(lead, True)}{''.join(f'<div class="wide-only">{shop(s)}</div>' for s in rest('People')[:2])}</div>
<div class="about"><p class="want">{WANT}</p>
<nav aria-label="Streets"><ul class="streets">{''.join(f'<li><a href="#st-{sid(n)}">{e(n)}</a></li>' for n, _ in shown)}</ul></nav></div></div></section>
<section class="road" aria-label="On this street"><p>{e(COUNTS)}</p></section>
{chr(10).join(f"""<section class="street" id="st-{sid(n)}" aria-labelledby="st-h-{sid(n)}"><h2 id="st-h-{sid(n)}">{e(n)}</h2><p class="sub">{e(intro)}</p>
{street_people() if n == 'People' else fold(n, shop, 'row', n)}</section>
<div class="kerb" aria-hidden="true"></div>""" for n, intro in shown)}
<p class="how">Every shop's details come from the hub's <a href="/sites.json">sites.json</a>; the windows are screenshots of the live sites.{DEMO_LINK}</p>
{GET}
</main>''', cur=5, note=design_note(5))


# ---- 5 The Line ----
def lcard(s, eager, img=True, big=False):
    line2 = e(waiting_line(s)) if s.get('waiting') else soft(host_of(s))
    tags = ''.join(f'<span class="tag">{e(x)}</span>' for x in s.get('chips', []))
    cls = 'card' + (' big' if big else '') + (' off' if s.get('waiting') else '')
    return (f'<a class="{cls}" href="{e(s["address"]["url"])}">{pic(s, eager, "(min-width:60rem) 15rem, 100vw", lead=big) if img else ""}{credit(s) if big else ""}<b>{e(s["name"])}</b>'
            f'<span class="m">{line2}</span>' + (f'<span>{tags}</span>' if tags else '') + '</a>')


# Each person's site at the station its record shows: handed over at the end, five or more designs at station 3,
# the rest built and live at 2. A station with more than three sites shows compact cards, so the line stays readable.
many = lambda s: any(c in ('Five designs', 'Six designs') for c in s.get('chips', []))
at_end = [s for s in people if s.get('handed_over')]
at_five = [s for s in people if not s.get('handed_over') and many(s)]
at_built = [s for s in people if s not in at_end and s not in at_five]
STATIONS = [(steps[0], [], WANT), (steps[1], at_built, 'Built and live, open to visit.'), (steps[2], at_five, ''),
            (steps[3], [], 'The owner picks the design they want to keep. None at this step today.'), (steps[4], at_end, ''),
            ('Get one', [], '<a href="/start/#get-one">Start here: how to get a site like these</a>.')]


def station(i, title, here, note):
    li = [f'<li>{lcard(s, i == 4, img=(len(here) <= 3), big=(i == 4))}</li>' for s in here]
    cards = ''.join(li[:2])
    # A busy station shows two sites; the rest fold into "Show all", in a list of their own.
    if len(li) > 2:
        cards += (f'<li class="fold"><details class="more"><summary>Show all {len(li)} at this step</summary>'
                  f'<ul class="here">{"".join(li[2:])}</ul></details></li>')
    return (f'<li class="st{" end" if i == 4 else ""}{" get-st" if i == 5 else ""}"><h2>{e(title)}</h2>' + (f'<p class="empty">{note if i in (0, 5) else e(note)}</p>' if note else '')
            + (f'<ul class="here">{cards}</ul>' if cards else '') + '</li>')


# The case, on the home page's first screen: one sentence, one real site in its five designs, one action.
KATE = 'https://kate-curtis-evans.founder.sovereignweb.site/'


def case():
    items = []
    for d in range(1, 6):
        lazy = '' if d < 3 else ' loading="lazy"'
        items.append(f'<li><a href="{KATE}designs/{d}.html"><picture><source type="image/webp" srcset="/shots/kate-curtis-evans-design-{d}.webp">'
                     f'<img src="/shots/kate-curtis-evans-design-{d}.jpg" width="640" height="400" alt="Design {d} of Kate Curtis-Evans\'s site"{lazy}></picture>'
                     f'<span>Design {d}</span></a></li>')
    return ('<section class="case" aria-labelledby="case-h">\n'
            '<h1 id="case-h">Your own website, made for you by an agent team, in five designs. Yours to keep.</h1>\n'
            f'<ul class="kate5" aria-label="Kate Curtis-Evans\'s site in its five designs">{"".join(items)}</ul>\n'
            f'<p class="case-note"><a href="{KATE}">Kate Curtis-Evans</a> chose one of her five and now edits her site herself on GitHub.</p>\n'
            '<p><a class="want-btn" href="/start/#get-one">I want one</a></p>\n</section>')


LINE_MAIN = f'''<main id="main">
{case()}
<p class="lede">{e(ABOUT)}</p>
<p class="counts">{e(COUNTS)}</p>
<ol class="line" aria-label="How a site is made, with each person's site where it stands">{''.join(station(i, *x) for i, x in enumerate(STATIONS))}</ol>
{chr(10).join(f"""<section class="side" id="l-{sid(n)}" aria-labelledby="l-h-{sid(n)}"><h2 id="l-h-{sid(n)}">{e(n)}</h2><p>{e(intro)}""" + (f""" Built the same way.{DEMO_LINK}""" if n == 'Demos' else '') + f"""</p>
{phone_fold([lcard(s, False) for s in by_section[n]], 'row', f'Show all {len(by_section[n])} in {e(n)}')}</section>""" for n, intro in shown if n != 'People')}
</main>'''
page('', 'Sovereign Website Hub', css('line'), LINE_MAIN, cur=1, note=design_note(1), script=HOME_SCRIPT)
page('line/', 'The Line', css('line'), LINE_MAIN, cur=1, note=design_note(1))


# ---- /designs/: the five side by side ----
page('designs/', 'The five designs', css('designs'), f'''<main id="main">
<h1>The five designs</h1>
<p class="lede">The same register of {len(sites)} public sites, five ways. Each is a real idea, not a colour change; The Line is the lead and the home page.</p>
<ul class="five">{''.join(f"""<li><a href="{h}"{' class="lead"' if d == 1 else ''}><img src="/shots/hub-design-{d}.jpg" alt="" width="640" height="400" loading="lazy"><b>{d}. {e(n)}</b><span>{e(idea)}{' Dark only.' if dark else ' Light and dark.'}</span></a></li>""" for d, n, h, idea, dark in DESIGNS)}</ul>
<p class="how">Designed by design.b (rounds 5 and 6) and built by hub.b from <a href="/sites.json">sites.json</a>.</p>
</main>''', cur=0, note='')


# ---- /features/: what a sovereign website can do, feature by feature, searchable ----
FEAT = json.loads((SITE / 'features.json').read_text())


def feature(f):
    ex = ''.join(f'<li><a href="{e(u)}">{e(t)}</a></li>' for t, u in f['examples'])
    words = ' '.join([f['name'], f['keywords'], f['today']]).lower()
    return (f'<li class="feat st-{e(f["status"])}" data-words="{e(words)}"><h2>{e(f["name"])} <span class="badge">{e(FEAT["statuses"][f["status"]])}</span></h2>'
            f'<p>{e(f["today"])}</p>' + (f'<ul class="ex">{ex}</ul>' if ex else '')
            + f'<dl><dt>Who is on it</dt><dd>{e(f["agent"])}</dd><dt>What holds it up</dt><dd>{e(f["bottleneck"])}</dd></dl></li>')


FEATURES_JS = '''<script>addEventListener('DOMContentLoaded',function(){var q=document.getElementById('q'),fs=[].slice.call(document.querySelectorAll('.feat')),n=document.getElementById('none'),nq=document.getElementById('nq'),c=document.getElementById('count');
function run(){var v=q.value.trim().toLowerCase(),k=0;fs.forEach(function(f){var s=!v||f.dataset.words.indexOf(v)>-1;f.hidden=!s;if(s)k++;});
n.hidden=k>0;nq.textContent=q.value.trim();c.textContent=v?k+' of '+fs.length+' match':fs.length+' features';}
q.addEventListener('input',run);var m=location.hash.match(/^#q=(.+)$/);if(m){q.value=decodeURIComponent(m[1]);}run();});</script>'''
page('features/', 'What it can do', css('features'), f'''<main id="main">
<h1>What can a sovereign website do?</h1>
<p class="lede">Look up a feature: whether it works today, where to see it live, which agent is on it and what is holding it up. Checked {e(FEAT["checked"])}; the list is <a href="/features.json">features.json</a>.</p>
<form class="find" role="search" onsubmit="return false"><label for="q">Find a feature</label><input id="q" type="search" placeholder="Spotify, a shop, a contact form..." autocomplete="off"><span id="count" aria-live="polite"></span></form>
<p id="none" class="none" hidden>Nothing here matches "<span id="nq"></span>" yet. <a href="/start/#get-one">Ask for it</a>: every feature on this list started as a request.</p>
<ul class="feats">{"".join(feature(f) for f in FEAT["features"])}</ul>
{GET}
</main>''', cur=0, script='\n' + FEATURES_JS)

print(f'showroom: {len(sites)} live public sites ({len(people)} people, {handed} handed over); 5 designs and /designs/ written')
