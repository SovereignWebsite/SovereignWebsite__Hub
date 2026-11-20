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
names = ['Editorial', 'Night gallery', 'Grid', 'Paper', 'Studio']
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


def card(s, i, small=False):
    # A handed-over site says so in its chip (and in the hero), so the note is not repeated.
    note = f'<p class="note">{e(s["note"])}</p>' if s.get('note') and not s.get('handed_over') else ''
    wait = f'<p class="wait-note">{e(s["waiting"])}</p>' if s.get('waiting') else ''
    cls = 'site small' if small else 'site'
    if s is hero:
        cls += ' is-hero'
    if s.get('waiting'):
        cls += ' waiting'
    return f'''<article class="{cls}">
  {frame(s, i < 3 and not small)}
  <div class="meta">
    <p class="kind">{e(s.get('group') or s['kind'])}</p>
    <h3><a href="{e(s['address']['url'])}">{e(s['name'])}</a></h3>
    <p class="sum">{e(s['summary'])}</p>{note}{wait}
    {chips(s)}
    <p class="go"><a href="{e(s['address']['url'])}">{e(host_of(s))} <span aria-hidden="true">&rarr;</span></a></p>
  </div>
</article>'''


demo = next((s for s in sites if s['slug'] == 'pipeline-demo'), None)
steps = ['One request', 'An agent team builds it', 'Five designs to choose from', 'The owner chooses one', "Handed over to the owner's GitHub"]
opts = ''.join(f'<a href="#design-{i+1}" data-d="{i+1}"><img src="shots/hub-design-{i+1}.jpg" alt="" width="640" height="400" loading="lazy"><span>{i+1}. {e(n)}</span></a>'
               for i, n in enumerate(names))

css = r'''
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--fg)}
a{color:inherit}img{display:block;width:100%;height:auto}
.bar{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.55rem 1rem;background:var(--bg);border-bottom:1px solid var(--line);font-size:.9rem}
.brand{font-weight:700;text-decoration:none;white-space:nowrap}
.chooser summary{list-style:none;cursor:pointer;padding:.35rem .9rem;border:1px solid var(--line);border-radius:999px;white-space:nowrap}
.chooser summary::-webkit-details-marker{display:none}.chooser summary::after{content:" \25BE"}
.chooser[open] summary{background:var(--fill);color:var(--on-fill);border-color:var(--fill)}
.opts{position:absolute;right:1rem;top:calc(100% + .4rem);width:min(60rem,calc(100vw - 2rem));display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.75rem;padding:.9rem;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 24px 60px -24px rgba(0,0,0,.45)}
.opts a{text-decoration:none;font-size:.82rem;border-radius:8px;padding:.3rem;border:2px solid transparent}.opts a[aria-current=true]{border-color:var(--fill)}
.opts img{border-radius:6px;border:1px solid var(--line);aspect-ratio:16/10;object-fit:cover;object-position:top}.opts span{display:block;margin-top:.35rem}
@media (max-width:700px){.opts{grid-template-columns:repeat(2,minmax(0,1fr));max-height:75vh;overflow:auto}}
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
.skip{position:absolute;left:1rem;top:-3rem;z-index:9;padding:.5rem 1rem;background:var(--fill);color:var(--on-fill);border-radius:8px}.skip:focus{top:.5rem}
.waiting .frame{border-style:dashed}.waiting .frame img{filter:grayscale(1) contrast(.85)}
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
.how a,footer a{color:var(--accent)}
footer{max-width:78rem;margin:0 auto;padding:1.5rem 1rem 3rem;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line)}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

/* Each design has a light and a dark palette; the visitor's setting chooses. --accent is for text, --fill for fills. */
/* 1 Editorial: serif, calm */
.d-1{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#5d5c57;--accent:#2f6b4f;--fill:#2f6b4f;--on-fill:#fff;--line:#e4e1d8;--card:#fff}
@media (prefers-color-scheme:dark){.d-1{--bg:#141513;--fg:#ecebe6;--muted:#a8a69e;--accent:#86c9a8;--fill:#86c9a8;--on-fill:#141513;--line:#2c2d29;--card:#1c1d1a}}
.d-1 h1,.d-1 .site h3,.d-1 .sec-h{font-family:Georgia,"Times New Roman",serif;font-weight:500}

/* 2 Night gallery: dark, glowing frames */
.d-2{--bg:#0d0f12;--fg:#eef1f4;--muted:#9aa3ad;--accent:#7cf0c4;--fill:#7cf0c4;--on-fill:#0d0f12;--line:#262b31;--card:#151920;--glow:#7cf0c4}
@media (prefers-color-scheme:light){.d-2{--bg:#f6f8fb;--fg:#0e1726;--muted:#4a5568;--accent:#0f6e4f;--fill:#0f6e4f;--on-fill:#fff;--line:#d8dee8;--card:#fff;--glow:#3aa77f}}
.d-2 .hero h1{background:linear-gradient(90deg,var(--accent),#5b8def);-webkit-background-clip:text;background-clip:text;color:transparent}
.d-2 .frame{box-shadow:0 0 0 1px var(--line),0 20px 60px -30px var(--glow)}

/* 3 Grid: bold, square, monospace labels */
.d-3{--bg:#f4f1ea;--fg:#111;--muted:#333;--accent:#b3261e;--fill:#b3261e;--on-fill:#fff;--line:#111;--card:#fff;--hard:#111}
@media (prefers-color-scheme:dark){.d-3{--bg:#141414;--fg:#f4f1ea;--muted:#d6d2c8;--accent:#ff8a7a;--fill:#ff8a7a;--on-fill:#141414;--line:#f4f1ea;--card:#1e1e1e;--hard:#f4f1ea}}
.d-3 .hero h1,.d-3 .sec-h{text-transform:uppercase;font-weight:900;letter-spacing:-.03em}
.d-3 .frame,.d-3 .chooser summary,.d-3 .chips span,.d-3 .opts,.d-3 .steps li::before{border-radius:0;border-width:2px}.d-3 .frame:hover{transform:translate(-4px,-4px);box-shadow:8px 8px 0 var(--hard)}
.d-3 .chips,.d-3 .chrome,.d-3 .kind{font-family:ui-monospace,Menlo,Consolas,monospace}

/* 4 Paper: warm, bookish, sections ruled off */
.d-4{--bg:#f6efe3;--fg:#2b211a;--muted:#6f5e50;--accent:#9c4421;--fill:#9c4421;--on-fill:#fff;--line:#e2d3bf;--card:#fffaf2}
@media (prefers-color-scheme:dark){.d-4{--bg:#1e1813;--fg:#f3e9dc;--muted:#c8b8a6;--accent:#e8a07a;--fill:#e8a07a;--on-fill:#1e1813;--line:#3b3027;--card:#261f19}}
.d-4 h1,.d-4 .site h3,.d-4 .sec-h{font-family:"Palatino Linotype",Palatino,Georgia,serif}
.d-4 section{border-top:2px solid var(--line);padding-top:2rem}.d-4 .sec-h{color:var(--accent)}

/* 5 Studio: gradient stage, tilted frames */
.d-5{--bg:#14112b;--fg:#fff;--muted:#c9c3ef;--accent:#ffcf5c;--fill:#ffcf5c;--on-fill:#14112b;--line:#3a3466;--card:#201b45;--stage:radial-gradient(1200px 600px at 10% -10%,#5b3fd1 0,transparent 60%),radial-gradient(900px 500px at 110% 10%,#d13f8f 0,transparent 55%),#14112b}
@media (prefers-color-scheme:light){.d-5{--bg:#f7f5ff;--fg:#1b1640;--muted:#4b4570;--accent:#5a3fd1;--fill:#5a3fd1;--on-fill:#fff;--line:#ddd7f5;--card:#fff;--stage:radial-gradient(1200px 600px at 10% -10%,#e3dbff 0,transparent 60%),radial-gradient(900px 500px at 110% 10%,#ffd9ec 0,transparent 55%),#f7f5ff}}
.d-5 body{background:var(--stage)}.d-5 .bar{background:transparent;backdrop-filter:blur(12px)}
.d-5 .frame{border-radius:18px;transform:perspective(1200px) rotateX(4deg);box-shadow:0 30px 80px -30px rgba(0,0,0,.6)}.d-5 .frame:hover{transform:perspective(1200px) rotateX(0) translateY(-4px)}
.d-5 .site{text-align:center}.d-5 .chips{justify-content:center}
'''

hero_note = hero.get('note') or ''
made = '\n' + f'''<section class="made" aria-labelledby="h-made"><h2 class="sec-h" id="h-made">How a site is made</h2>
<ol class="steps">{''.join(f'<li>{e(t)}</li>' for t in steps)}</ol>
{f'<p class="go"><a href="{e(demo["address"]["url"])}">See it run: the pipeline demo <span aria-hidden="true">&rarr;</span></a></p>' if demo else ''}
</section>'''
page = f'''<!doctype html>
<html lang="en" class="d-1">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230f6e4f'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' font-weight='700' fill='%23fff' text-anchor='middle'%3ES%3C/text%3E%3C/svg%3E">
<title>Sovereign Website Hub</title>
<meta name="description" content="Websites their owners own: built by agent teams, then handed over. Every site here is public and live.">
<meta property="og:title" content="Sovereign Website Hub: websites their owners own">
<meta property="og:description" content="Built by agent teams, then handed over. Every site here is public and live.">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}og.jpg">
<meta property="og:site_name" content="Sovereign Website Hub">
<meta property="og:locale" content="en_GB">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Sovereign Website Hub: websites their owners own, with screenshots of three people's sites">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Sovereign Website Hub: websites their owners own">
<meta name="twitter:description" content="Built by agent teams, then handed over. Every site here is public and live.">
<meta name="twitter:image" content="{SITE_URL}og.jpg">
<script>var d=(location.hash.match(/design-([1-5])/)||[])[1];if(d)document.documentElement.className='d-'+d;</script>
<style>{css}
{family_css}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the sites</a>
{family}
<header class="bar"><a class="brand" href="./">Sovereign Website Hub</a>
<details class="chooser"><summary>Choose a design</summary><nav class="opts" aria-label="Designs of this page">{opts}</nav></details></header>
<main id="main">
<header class="hero">
  <div class="hero-text">
    <p class="kicker">The showroom</p>
    <h1>Websites their owners own.</h1>
    <p>Built by agent teams, then handed over: the owner keeps the files, the history and the address. Every site here is public and live; open one to see it working.</p>
    <ul class="count"><li><b>{working}</b>sites working</li><li><b>{len(people)}</b>people's sites</li><li><b>{handed}</b>handed over</li></ul>
  </div>
  <a class="hero-shot frame" href="{e(hero['address']['url'])}" aria-label="Open {e(hero['name'])}"><span class="chrome"><i></i><i></i><i></i><b>{e(host_of(hero))}</b></span><picture><source media="(max-width:640px)" srcset="{e(hero['shot'])}-phone.jpg"><img src="{e(hero['shot'])}.jpg" alt="Screenshot of {e(hero['name'])}" width="1280" height="800" loading="eager"></picture>{f'<span class="badge">{e(hero_note)}</span>' if hero_note else ''}</a>
</header>
<nav class="sections" aria-label="Sections"><ul>{''.join(f'<li><a href="#{sid(n)}">{e(n)} <span>{len(by_section[n])}</span></a></li>' for n, _ in SECTIONS if by_section[n])}</ul></nav>
{chr(10).join(f'''<section class="{'people' if n == 'People' else 'tools'}" id="{sid(n)}" aria-labelledby="h-{sid(n)}"><h2 class="sec-h" id="h-{sid(n)}">{e(n)}</h2>
<p class="sec-intro">{e(intro)}</p>
<div class="grid">
{chr(10).join(card(s, i, small=(n != 'People')) for i, s in enumerate(by_section[n]))}
</div></section>''' + (made if n == 'People' else '') for n, intro in SECTIONS if by_section[n])}
<p class="how">Each entry comes from <a href="sites.json">sites.json</a>, in the <a href="schema/hub-site.schema.json">hub-site format</a>, and is added when the site goes live. Screenshots are taken from the live sites. Source: <a href="https://github.com/SovereignWebsite/SovereignWebsite__Hub">SovereignWebsite__Hub</a>.</p>
</main>
<footer>hub.sovereignweb.site · Part of the <a href="https://github.com/SovereignWebsite">SovereignWebsite</a> organisation · No cookies, no tracking, nothing stored in your browser; the design you pick lives only in the address (#design-1 to #design-5).</footer>
<script>
(function(){{
  var as=document.querySelectorAll('.opts a'),ch=document.querySelector('.chooser');
  function set(d){{document.documentElement.className='d-'+d;as.forEach(function(a){{a.setAttribute('aria-current',a.dataset.d===d?'true':'false');}});}}
  function fromHash(){{var m=location.hash.match(/design-([1-5])/);set(m?m[1]:(document.documentElement.className.match(/d-([1-5])/)||[0,'1'])[1]);}}
  as.forEach(function(a){{a.onclick=function(ev){{ev.preventDefault();history.replaceState(null,'','#design-'+a.dataset.d);set(a.dataset.d);ch.open=false;}};}});
  addEventListener('hashchange',fromHash);fromHash();
  document.addEventListener('keydown',function(ev){{if(ev.key==='Escape')ch.open=false;}});
}})();
</script>
</body>
</html>
'''
(SITE / 'index.html').write_text(page)
print(f'showroom: {len(sites)} live public sites ({len(people)} people, {handed} handed over), {len(names)} designs')
