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
sites = [s for s in data['sites'] if s.get('status') == 'live']


def card(s, i):
    host = re.sub(r'^https?://|/$', '', s['address']['url'])
    note = f'<p class="note">{e(s["note"])}</p>' if s.get('note') else ''
    shot = s.get('shot')
    img = (f'<picture><source media="(max-width:640px)" srcset="{e(shot)}-phone.jpg">'
           f'<img src="{e(shot)}.jpg" alt="Screenshot of {e(s["name"])}" loading="lazy" width="1280" height="800"></picture>') if shot else ''
    return f'''<article class="site" style="--i:{i}">
  <a class="frame" href="{e(s['address']['url'])}" aria-label="Open {e(s['name'])}"><span class="chrome"><i></i><i></i><i></i><b>{e(host)}</b></span>{img}</a>
  <div class="meta">
    <p class="tags"><span>{e(s.get('group', ''))}</span><span>{e(s['kind'])}</span></p>
    <h2><a href="{e(s['address']['url'])}">{e(s['name'])}</a></h2>
    <p class="sum">{e(s['summary'])}</p>{note}
    <p class="go"><a href="{e(s['address']['url'])}">{e(host)} <span aria-hidden="true">&rarr;</span></a></p>
  </div>
</article>'''


cards = '\n'.join(card(s, i) for i, s in enumerate(sites))
names = ['Editorial', 'Night gallery', 'Grid', 'Magazine', 'Studio']

css = r'''
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--fg);transition:background .3s,color .3s}
a{color:inherit}img{display:block;width:100%;height:auto}
.switch{position:sticky;top:0;z-index:5;display:flex;gap:.4rem;align-items:center;flex-wrap:wrap;padding:.5rem 1rem;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);font-size:.85rem}
.switch span{color:var(--muted);margin-right:.3rem}.switch button{font:inherit;padding:.3rem .75rem;border-radius:999px;border:1px solid var(--line);background:transparent;color:var(--fg);cursor:pointer}
.switch button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
main{max-width:76rem;margin:0 auto;padding:4rem 1rem 3rem}
.hero .kicker{text-transform:uppercase;letter-spacing:.16em;font-size:.75rem;font-weight:700;color:var(--accent);margin:0}
.hero h1{margin:.4rem 0 1rem;line-height:1.02;font-size:clamp(2.4rem,7vw,5rem);letter-spacing:-.02em}
.hero p{max-width:40rem;color:var(--muted);font-size:1.1rem;margin:0}
.sites{display:grid;gap:2.5rem;margin-top:3.5rem}
.frame{display:block;border-radius:12px;overflow:hidden;background:var(--card);border:1px solid var(--line);text-decoration:none;transition:transform .25s,box-shadow .25s}
.frame:hover{transform:translateY(-4px);box-shadow:0 18px 40px -18px rgba(0,0,0,.35)}
.chrome{display:flex;align-items:center;gap:.35rem;padding:.5rem .75rem;border-bottom:1px solid var(--line);background:var(--card);font-size:.75rem;color:var(--muted)}
.chrome i{width:.6rem;height:.6rem;border-radius:50%;background:var(--line)}.chrome b{font-weight:500;margin-left:.5rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tags{display:flex;gap:.4rem;margin:1rem 0 .3rem;padding:0;flex-wrap:wrap}.tags span{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;padding:.15rem .55rem;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.tags span:empty{display:none}
.site h2{margin:.2rem 0 .4rem;font-size:1.6rem;line-height:1.15}.site h2 a{text-decoration:none}.site h2 a:hover{text-decoration:underline}
.sum{color:var(--muted);margin:0 0 .6rem}.note{font-size:.85rem;margin:0 0 .6rem;padding:.3rem .6rem;border-left:3px solid var(--accent);background:var(--card)}
.go a{font-weight:600;color:var(--accent);text-decoration:none}.go a:hover{text-decoration:underline}
.how{margin-top:4rem;padding-top:2rem;border-top:1px solid var(--line);color:var(--muted);font-size:.92rem;max-width:46rem}
footer{max-width:76rem;margin:0 auto;padding:1.5rem 1rem 3rem;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line)}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

/* 1 Editorial: light, serif headings, one site per row, large shots */
.d-1{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#5d5c57;--accent:#2f6b4f;--on-accent:#fff;--line:#e4e1d8;--card:#fff}
.d-1 h1,.d-1 .site h2{font-family:Georgia,"Times New Roman",serif;font-weight:500}
@media (min-width:900px){.d-1 .site{display:grid;grid-template-columns:1.6fr 1fr;gap:2.5rem;align-items:center}.d-1 .site:nth-child(even) .frame{order:2}}

/* 2 Night gallery: dark, glowing frames, two columns */
.d-2{--bg:#0d0f12;--fg:#eef1f4;--muted:#9aa3ad;--accent:#7cf0c4;--on-accent:#0d0f12;--line:#262b31;--card:#151920}
.d-2 .hero h1{background:linear-gradient(90deg,#7cf0c4,#8ab4ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.d-2 .frame{box-shadow:0 0 0 1px #262b31,0 20px 60px -30px #7cf0c4}
@media (min-width:800px){.d-2 .sites{grid-template-columns:1fr 1fr}.d-2 .site:first-child{grid-column:1/-1}}

/* 3 Grid: bold, square, monospace labels, three columns */
.d-3{--bg:#f4f1ea;--fg:#111;--muted:#333;--accent:#e4402f;--on-accent:#fff;--line:#111;--card:#fff}
.d-3 .hero h1{text-transform:uppercase;font-weight:900;letter-spacing:-.03em}
.d-3 .frame,.d-3 .switch button,.d-3 .tags span{border-radius:0;border-width:2px}.d-3 .frame:hover{transform:translate(-4px,-4px);box-shadow:8px 8px 0 #111}
.d-3 .tags span,.d-3 .chrome{font-family:ui-monospace,Menlo,Consolas,monospace}
@media (min-width:900px){.d-3 .sites{grid-template-columns:repeat(3,1fr);gap:1.5rem}}

/* 4 Magazine: warm cream, staggered, big numbers */
.d-4{--bg:#f6efe3;--fg:#2b211a;--muted:#6f5e50;--accent:#b4532a;--on-accent:#fff;--line:#e2d3bf;--card:#fffaf2}
.d-4 h1,.d-4 .site h2{font-family:"Palatino Linotype",Palatino,Georgia,serif}
.d-4 .site{position:relative;counter-increment:n;padding-top:2.6rem}.d-4 .site::before{content:"0" counter(n);position:absolute;top:0;right:0;font:700 3.2rem/1 Georgia,serif;color:var(--accent);opacity:.25}
@media (min-width:900px){.d-4 .sites{grid-template-columns:1fr 1fr;column-gap:3rem}.d-4 .site:nth-child(even){margin-top:6rem}}

/* 5 Studio: gradient stage, floating devices, phone shot on small screens */
.d-5{--bg:#14112b;--fg:#fff;--muted:#c9c3ef;--accent:#ffcf5c;--on-accent:#14112b;--line:#3a3466;--card:#201b45}
.d-5 body,.d-5{background:radial-gradient(1200px 600px at 10% -10%,#5b3fd1 0,transparent 60%),radial-gradient(900px 500px at 110% 10%,#d13f8f 0,transparent 55%),#14112b}
.d-5 .frame{border-radius:18px;transform:perspective(1200px) rotateX(4deg);box-shadow:0 30px 80px -30px #000}.d-5 .frame:hover{transform:perspective(1200px) rotateX(0) translateY(-4px)}
.d-5 .site{text-align:center}.d-5 .tags{justify-content:center}.d-5 .hero{text-align:center}.d-5 .hero p{margin:0 auto}
@media (min-width:900px){.d-5 .sites{grid-template-columns:repeat(3,1fr);gap:2rem}}
'''

page = f'''<!doctype html>
<html lang="en" class="d-1">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sovereign Website Hub</title>
<meta name="description" content="The showroom of public sovereign websites: built by agents, owned by the people they are for.">
<script>try{{var d=(location.hash.match(/design-([1-5])/)||[])[1]||localStorage.getItem('hub-design');if(d)document.documentElement.className='d-'+d;}}catch(e){{}}</script>
<style>{css}
{family_css}
</style>
</head>
<body>
{family}
<div class="switch" role="group" aria-label="Choose a design"><span>Design</span>{''.join(f'<button type="button" data-d="{i+1}" aria-pressed="false">{i+1}. {n}</button>' for i, n in enumerate(names))}</div>
<main>
<header class="hero">
  <p class="kicker">The showroom</p>
  <h1>Sovereign websites, live.</h1>
  <p>Sites built by agents and owned by the people they are for: their files, their history, their address. Every site here is public and live; open one to see it working.</p>
</header>
<section class="sites" aria-label="Public sites">
{cards}
</section>
<p class="how">Each entry comes from <a href="sites.json">sites.json</a>, in the <a href="schema/hub-site.schema.json">hub-site format</a>, and is added by the site's own agent when the site goes live. Screenshots are taken from the live sites. Source: <a href="https://github.com/SovereignWebsite/SovereignWebsite__Hub">SovereignWebsite__Hub</a>.</p>
</main>
<footer>hub.sovereignwebsite.site · Part of the <a href="https://github.com/SovereignWebsite">SovereignWebsite</a> organisation · No cookies, no tracking.</footer>
<script>
(function(){{
  var bs=document.querySelectorAll('.switch button');
  function set(d){{document.documentElement.className='d-'+d;bs.forEach(function(b){{b.setAttribute('aria-pressed',b.dataset.d===d?'true':'false');}});try{{localStorage.setItem('hub-design',d);}}catch(e){{}}}}
  bs.forEach(function(b){{b.onclick=function(){{set(b.dataset.d);history.replaceState(null,'','#design-'+b.dataset.d);}};}});
  set((document.documentElement.className.match(/d-([1-5])/)||[0,'1'])[1]);
}})();
</script>
</body>
</html>
'''
(SITE / 'index.html').write_text(page)
print(f'showroom: {len(sites)} live public sites, {len(names)} designs')
