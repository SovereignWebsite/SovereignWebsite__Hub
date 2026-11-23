#!/usr/bin/env python3
# Builds site/operator/, Dinis's operator page: what shipped, what is blocked, what is waiting on him.
# Only from what the agents already publish: SovereignWebsite__IaC's status.json and site requests, each live site's
# /version.json, and team/keys.json. No backend: the page is static, rebuilt with the hub.
# Private (vault) sites and sites not yet made are never shown, and no line that names one is published.
# Usage: python3 tools/build-operator.py <path to a SovereignWebsite__IaC checkout, on dev>
import concurrent.futures, datetime, hashlib, html, json, pathlib, re, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'site' / 'operator'
IAC = pathlib.Path(sys.argv[1]).resolve()
IAC_WEB = 'https://github.com/SovereignWebsite/SovereignWebsite__IaC/blob/dev/'
e = lambda x: html.escape(str(x), quote=True)

status = json.loads((IAC / 'status.json').read_text())
keys = json.loads((IAC / 'team' / 'keys.json').read_text())['keys']
reqs = [json.loads(l) for l in subprocess.run(['node', str(ROOT / 'tools' / 'operator-hosts.mjs'), str(IAC)],
                                             capture_output=True, text=True, check=True).stdout.splitlines() if l.strip()]

# Words that would name a private or unmade site: any line carrying one is left out.
hidden = [r for r in reqs if r['private'] or not r['made']]
terms = {t.lower() for r in hidden for t in (r['host'], r['label'], r['title'], r['label'].replace('-', ' ')) if t and len(t) > 3}
# For a private site, each distinctive word of its name too, so a short mention cannot slip through.
terms |= {w for r in hidden if r['private'] for w in re.split(r'[^a-z0-9]+', (r['label'] + ' ' + r['title']).lower()) if len(w) >= 5 and w not in ('demonstration', 'sovereign', 'website')}
link_of = lambda text: (re.search(r'https://\S+', text) or [None])[0]
strip_link = lambda text: re.sub(r'\s*-?\s*https://\S+\s*$', '', text).strip()
cap = lambda s: s[:1].upper() + s[1:]


def public(text):
    low = str(text).lower()
    return not any(t in low for t in terms)

# The conductor's public-safe view, read live by the page. Second guard: any line in it that this filter would block
# is published only as a SHA-256 of the whole line, so the browser drops it without the page carrying the words.
LIVE = 'https://raw.githubusercontent.com/SovereignWebsite/SovereignWebsite__IaC/dev/board/operator.json'
try:
    with urllib.request.urlopen(urllib.request.Request(LIVE, headers={'User-Agent': 'sws-hub-operator'}), timeout=20) as r:
        live = json.loads(r.read().decode())
except Exception as ex:
    live = {}
    print(f'note: {LIVE} not read ({type(ex).__name__}); the page will still try it live', file=sys.stderr)
live_lines = [x for k in ('waiting_on_dinis', 'done_recent', 'next') for x in live.get(k, [])] + [live.get('state', '')]
blocked_hashes = sorted({hashlib.sha256(x.encode()).hexdigest() for x in live_lines if x and not public(x)})
nxt = [{'line': cap(strip_link(x)), 'url': link_of(x) or IAC_WEB + 'board/operator.json'} for x in live.get('next', []) if public(x)]

# The organisation's own sites, then every public request.
OWN = [('sovereignwebsite.ai', 'Sovereign Website'), ('sovereignwebsite.org', 'The principles'), ('sovereignwebsite.site', 'Hosted'),
       ('hub.sovereignweb.site', 'The hub'), ('vault.sovereignwebsite.site', 'The vault')]
sites = [{'host': h, 'title': t} for h, t in OWN] + [{'host': r['host'], 'title': r['title']} for r in reqs if not r['private'] and r['made']]

def probe(s):
    url = f"https://{s['host']}/"
    try:
        with urllib.request.urlopen(urllib.request.Request(url + 'version.json', headers={'User-Agent': 'sws-hub-operator'}), timeout=20) as r:
            v = json.loads(r.read().decode())
            if v.get('version'):
                return {**s, 'url': url, 'ok': True, 'version': v['version'], 'commit': v.get('commit'), 'date': v.get('date'), 'run': v.get('run')}
            return {**s, 'url': url, 'ok': True, 'version': None, 'note': 'live, its version.json names no version'}
    except Exception as ex:
        code = getattr(ex, 'code', None)
        try:  # no version.json: does the site answer at all?
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'sws-hub-operator'}), timeout=20) as r:
                return {**s, 'url': url, 'ok': True, 'version': None, 'note': 'live, no version yet (not on the site pipeline)'}
        except Exception as ex2:
            return {**s, 'url': url, 'ok': False, 'note': f"does not answer ({getattr(ex2, 'code', None) or type(ex2).__name__})"}

with concurrent.futures.ThreadPoolExecutor(12) as pool:
    probed = list(pool.map(probe, sites))

waiting = [{'line': cap(strip_link(a).removeprefix('Dinis: ')), 'url': link_of(a) or IAC_WEB + 'status.json'}
           for a in status.get('asks', []) if public(a)]
waiting += [{'line': h, 'url': IAC_WEB + 'status.json', 'tag': 'held'} for h in status.get('held_for_dinis', []) if public(h)]
blocked = [{'line': f"{p['title']}: {p['note']}", 'url': p['url']} for p in probed if not p['ok']]
shipped_sites = sorted([p for p in probed if p.get('version')], key=lambda p: (p['date'] or '', p['version'] or ''), reverse=True)
shipped = [{'line': f"{p['title']}: {p['version']} · {p['commit']} · {p['date']}", 'url': p['url'], 'run': p.get('run')} for p in shipped_sites]
done = [{'line': d, 'url': IAC_WEB + 'status.json'} for d in reversed(status.get('done', [])) if public(d)][:15]
nopipe = [p for p in probed if p['ok'] and not p.get('version')]
agents = sorted({k['agent'] for k in keys if k.get('status') == 'active' and k.get('agent')})

now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
data = {'built': now, 'status_updated': status.get('updated'), 'state': status.get('state') if public(status.get('state', '')) else None,
        'waiting_on_dinis': waiting, 'blocked': blocked, 'shipped': shipped, 'done_recently': done,
        'next': nxt, 'live_without_version': [{'line': f"{p['title']}: {p['note']}", 'url': p['url']} for p in nopipe], 'active_agents': len(agents)}

def items(rows, empty):
    if not rows:
        return f'<p class="empty">{e(empty)}</p>'
    return '<ol>' + ''.join(
        f'<li><a href="{e(r["url"])}">{e(r["line"])}</a>'
        + (' <span class="tag">held</span>' if r.get('tag') else '')
        + (f' <a class="run" href="{e(r["run"])}">build</a>' if r.get('run') else '') + '</li>' for r in rows) + '</ol>'

HOST = 'https://hub.sovereignweb.site/'
page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>Operator: Sovereign Website Hub</title>
<meta name="description" content="What shipped, what is blocked and what is waiting on Dinis, from what the agents publish.">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sovereign Website Hub">
<meta property="og:locale" content="en_GB">
<meta property="og:url" content="{HOST}operator/">
<meta property="og:title" content="Operator: Sovereign Website Hub">
<meta property="og:description" content="What shipped, what is blocked and what is waiting on Dinis.">
<meta property="og:image" content="{HOST}og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Sovereign Website Hub">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Operator: Sovereign Website Hub">
<meta name="twitter:description" content="What shipped, what is blocked and what is waiting on Dinis.">
<meta name="twitter:image" content="{HOST}og.jpg">
<style>
:root{{--bg:#f6f8fb;--fg:#0e1726;--muted:#4a5568;--accent:#0f6e4f;--line:#d8dee8;--card:#fff;--warn:#9a3412;--wait:#1d4ed8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d0f12;--fg:#eef1f4;--muted:#9aa3ad;--accent:#7cf0c4;--line:#262b31;--card:#151920;--warn:#fdba74;--wait:#93c5fd}}}}
*{{box-sizing:border-box}}body{{margin:0;font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--fg)}}
a{{color:inherit}}.skip{{position:absolute;left:1rem;top:-3rem}}.skip:focus{{top:.5rem}}
header,main,footer{{max-width:72rem;margin:0 auto;padding:1rem}}header{{padding-top:2rem}}
h1{{margin:0 0 .3rem;font-size:clamp(1.8rem,4vw,2.6rem)}}.sub{{color:var(--muted);margin:0}}
.stats{{display:flex;flex-wrap:wrap;gap:1.5rem;list-style:none;padding:0;margin:1.2rem 0 0}}.stats b{{display:block;font-size:1.8rem;line-height:1.1}}.stats li{{color:var(--muted);font-size:.9rem}}
.cols{{display:grid;gap:1.25rem;grid-template-columns:minmax(0,1fr)}}@media (min-width:760px){{.cols{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1rem 1.1rem;min-width:0}}
h2{{margin:0 0 .6rem;font-size:1.2rem;display:flex;gap:.5rem;align-items:baseline}}h2 span{{font-size:.85rem;color:var(--muted);font-weight:500}}
.wait h2{{color:var(--wait)}}.block h2{{color:var(--warn)}}.ship h2{{color:var(--accent)}}
ol{{margin:0;padding-left:1.2rem}}li{{margin:.35rem 0;overflow-wrap:anywhere}}li a{{text-decoration:none}}li a:hover{{text-decoration:underline}}
.tag{{font-size:.72rem;border:1px solid var(--line);border-radius:999px;padding:0 .45rem;color:var(--muted)}}.run{{font-size:.8rem;color:var(--muted)}}
.empty{{color:var(--muted);margin:0}}details{{margin-top:1.25rem}}summary{{cursor:pointer;font-weight:600}}
footer{{color:var(--muted);font-size:.85rem}}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to the lists</a>
<header>
<h1>Operator</h1>
<p class="sub">For Dinis: what is waiting on you, what is blocked, and what shipped. Built {e(now)} from what the agents publish; the IaC status was updated <span id="upd">{e(status.get('updated', ''))}</span>.</p>
<p class="sub" id="live" data-src="{e(LIVE)}" data-blocked="{e(' '.join(blocked_hashes))}">Waiting, next and done are read live from the conductor's <a href="{IAC_WEB}board/operator.json">operator.json</a> when your browser allows it.</p>
<ul class="stats"><li><b id="s-wait">{len(waiting)}</b>waiting on you</li><li><b>{len(blocked)}</b>blocked</li><li><b>{len(shipped)}</b>sites on the pipeline</li><li><b>{len(agents)}</b>agents with a live key</li></ul>
</header>
<main id="main">
<div class="cols">
<section class="wait" aria-labelledby="h-wait"><h2 id="h-wait">Waiting on you <span id="n-wait">{len(waiting)}</span></h2><div id="l-wait">{items(waiting, 'Nothing is waiting on you.')}</div></section>
<section class="block" aria-labelledby="h-block"><h2 id="h-block">Blocked <span>{len(blocked)}</span></h2>{items(blocked, 'Nothing is blocked: every public site answers.')}</section>
<section class="ship" aria-labelledby="h-ship"><h2 id="h-ship">Shipped <span>{len(shipped)}</span></h2>{items(shipped, 'No releases found.')}</section>
</div>
<section class="next" aria-labelledby="h-next"><h2 id="h-next">Next <span id="n-next">{len(nxt)}</span></h2><div id="l-next">{items(nxt, 'Nothing planned yet.')}</div></section>
<details><summary>Done lately, from the IaC status (<span id="n-done">{len(done)}</span>)</summary><div id="l-done">{items(done, 'None.')}</div></details>
<details><summary>Live without a version ({len(nopipe)})</summary>{items(data['live_without_version'], 'None.')}</details>
</main>
<script>
(function(){{
  // Reads the conductor's public-safe operator.json and refreshes waiting, next and done. Nothing is stored or sent.
  var box=document.getElementById('live'),blocked=box.dataset.blocked.split(' ');
  if(!window.fetch||!window.crypto||!crypto.subtle)return;
  function hex(b){{return Array.prototype.map.call(new Uint8Array(b),function(x){{return ('0'+x.toString(16)).slice(-2);}}).join('');}}
  function keep(lines){{return Promise.all(lines.map(function(l){{return crypto.subtle.digest('SHA-256',new TextEncoder().encode(l)).then(function(h){{return blocked.indexOf(hex(h))<0?l:null;}});}})).then(function(a){{return a.filter(Boolean);}});}}
  function list(id,n,lines,empty,fallback){{
    var el=document.getElementById(id);el.textContent='';document.getElementById(n).textContent=lines.length;
    if(!lines.length){{var p=document.createElement('p');p.className='empty';p.textContent=empty;el.appendChild(p);return;}}
    var ol=document.createElement('ol');
    lines.forEach(function(l){{
      var m=l.match(/https:\\/\\/\\S+/),t=l.replace(/\\s*-?\\s*https:\\/\\/\\S+\\s*$/,'').replace(/^Dinis: /,'').trim(),li=document.createElement('li'),a=document.createElement('a');
      a.href=m?m[0]:fallback;a.textContent=t.charAt(0).toUpperCase()+t.slice(1);li.appendChild(a);ol.appendChild(li);}});
    el.appendChild(ol);}}
  fetch(box.dataset.src,{{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'}}).then(function(r){{return r.ok?r.json():Promise.reject();}}).then(function(d){{
    var src='{IAC_WEB}board/operator.json';
    return Promise.all([keep(d.waiting_on_dinis||[]),keep(d.next||[]),keep((d.done_recent||[]).slice().reverse())]).then(function(r){{
      list('l-wait','n-wait',r[0],'Nothing is waiting on you.',src);document.getElementById('s-wait').textContent=r[0].length;list('l-next','n-next',r[1],'Nothing planned yet.',src);list('l-done','n-done',r[2],'None.',src);
      if(d.updated)document.getElementById('upd').textContent=d.updated;
      box.textContent='Waiting, next and done: live from the conductor\u2019s operator.json, updated '+(d.updated||'')+'.';}});
  }}).catch(function(){{}});
}})();
</script>
<footer>Sources: <a href="{IAC_WEB}status.json">IaC status.json</a>, the IaC site requests, each site's /version.json and <a href="{IAC_WEB}team/keys.json">team/keys.json</a>. Private sites are never shown. Data: <a href="data.json">data.json</a> · <a href="../">The hub</a> · <a href="../policy/">How this site is governed</a></footer>
</body>
</html>
'''
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(page)
(OUT / 'data.json').write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
print(f'operator: {len(waiting)} waiting on Dinis, {len(blocked)} blocked, {len(shipped)} shipped, {len(done)} done lately, {len(nopipe)} live without a version')
