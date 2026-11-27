#!/usr/bin/env python3
# Builds the hub's Agents pages from data: who the agents are, how many there are now and day by day, and each one
# in action. Dinis, 22 Nov 2026 (in hub.c's session): "the agent page should show the names and sessions. That's the
# point. Each page should show the generic and then should actually show it in action."
#
# Reads: the Factory's team/keys.json (every agent's name, role, session, key, start date and status), the hub's
# site/sites.json, and the public git history of the Factory, the hub and the SovereignWebsite site repositories
# (each commit's Agent: trailer says which agent made it). Nothing about an agent is typed by hand.
# Writes: site/data/agents-all.json, site/agents/at-work/index.html and site/agents/at-work/<role>/index.html
# (site/agents/index.html is hub.b's "Use with your AI" page and is never written here).
#
# Usage: python3 tools/build-agents.py [cache-dir]
#   cache-dir (default ~/.cache/hub-agents) holds bare, blob-less clones of the public repositories; they are
#   made or fetched on each run. Apache-2.0. hub.c@SovereignWebsite.dinis, 22 Nov 2026.
import collections, datetime, hashlib, html, json, os, pathlib, re, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
SITE_URL = 'https://hub.sovereignweb.site/'
GH = 'https://github.com/'
KEYS_URL = 'https://raw.githubusercontent.com/SovereignWebsite/SovereignWebsite__Factory/dev/team/keys.json'
CACHE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.cache/hub-agents'))
e = lambda x: html.escape(str(x), quote=True)
# The same off-hub list as tools/build-latest.py (sha256 of the slug, first 16 hex characters).
OFF_HUB = {'e5fce384ae04237f', '499868c5d9bc0961'}
off = lambda slug: hashlib.sha256(slug.encode()).hexdigest()[:16] in OFF_HUB


def mentions_off(text):
    # True if any run of one to three words in text, joined by hyphens, is an off-hub slug.
    w = [x for x in re.split(r'[^a-z0-9]+', text.lower()) if x]
    return any(off('-'.join(w[i:i + n])) for n in (1, 2, 3) for i in range(len(w) - n + 1))


def git(repo, *a):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True, check=True).stdout


def repos():
    """Public repositories whose history is read: the Factory, the hub, the organisation's sites, and the
    SovereignWebsite repository of every listed site."""
    names = {'SovereignWebsite/SovereignWebsite__Factory', 'SovereignWebsite/SovereignWebsite__Hub',
             'SovereignWebsite/SovereignWebsite__Website', 'SovereignWebsite/SovereignWebsite__Org',
             'SovereignWebsite/SovereignWebsite__Site', 'SovereignWebsite/SovereignWebsite__Vault'}
    for s in SITES:
        u = (s.get('repository') or {}).get('url', '')
        if u.startswith(GH + 'SovereignWebsite/'):
            names.add(u[len(GH):].rstrip('/'))
    return sorted(names)


def clone(full):
    d = CACHE / full.replace('/', '__')
    if d.exists():
        subprocess.run(['git', '-C', str(d), 'fetch', '-q', 'origin', '+refs/heads/*:refs/heads/*'], capture_output=True)
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '-q', '--bare', '--filter=blob:none', f'{GH}{full}.git', str(d)], check=True)
    return d


SITES = [s for s in json.loads((SITE / 'sites.json').read_text())['sites'] if not off(s['slug'])]
site_of_repo = {(s.get('repository') or {}).get('url', '').rstrip('/'): s for s in SITES}
keys = json.loads(urllib.request.urlopen(KEYS_URL, timeout=30).read())['keys']

# Commits by agent, from the Agent: trailer, across every branch of every repository (one entry per commit).
work = collections.defaultdict(list)
for full in repos():
    d = clone(full)
    seen = set()
    log = git(d, 'log', '--all', '--format=%H%x1f%cI%x1f%s%x1f%(trailers:key=Agent,valueonly,separator=%x2C)%x1e')
    for rec in log.split('\x1e'):
        parts = rec.strip('\n').split('\x1f')
        if len(parts) != 4 or not parts[3].strip() or parts[0] in seen or mentions_off(parts[2]):
            continue
        seen.add(parts[0])
        for agent in {a.strip() for a in parts[3].split(',') if a.strip()}:
            work[agent].append({'repo': full, 'sha': parts[0], 'when': parts[1], 'subject': parts[2]})


# The naming model Dinis agreed on 25 Nov 2026: <account id>.<role>[.<speciality>]@[<project>.]<owner>, where the
# account id is a platform code and a number (cl-3, mi-1, gpt-2, gem-1). Older names are role.account@...
NEW_ID = re.compile(r'^(?:cl|mi|gpt|gem)-\d+$')


def role_of(name):
    parts = name.split('@')[0].split('.')
    return parts[1] if NEW_ID.match(parts[0]) and len(parts) > 1 else parts[0]


def account_of(name):
    # The account is the one-letter part of the name (hub.c, design.b.rounds); the Mistral team's agents carry
    # 'mistral' instead (evals.mistral). A name with neither says no account.
    parts = name.split('@')[0].split('.')
    if NEW_ID.match(parts[0]):
        return parts[0]
    rest = parts[1:]
    return next((x for x in rest if len(x) == 1 and x.isalpha()), 'mistral' if 'mistral' in rest else '')


agents = []
for k in keys:
    name = k.get('agent', '')
    # An agent whose name or role text names a site kept off the hub is left out of the pages and the data.
    if not name or '@' not in name or mentions_off(name) or mentions_off(k.get('role', '')):
        continue
    commits = sorted(work.get(name, []), key=lambda c: c['when'], reverse=True)
    repos_worked = collections.Counter(c['repo'] for c in commits)
    sites = []
    for full, n in repos_worked.most_common():
        s = site_of_repo.get(GH + full)
        sites.append({'repo': full, 'commits': n, 'site': s['address']['url'] if s else None, 'name': s['name'] if s else full.split('/')[-1]})
    keeps = [s['address']['url'] for s in SITES if any(t.get('name') == name for t in s.get('team') or [])]
    acct = account_of(name)
    conductor = f'{acct}.conductor@SovereignWebsite.dinis' if NEW_ID.match(acct) else f'conductor.{acct}@SovereignWebsite.dinis'
    agents.append({
        'name': name, 'id': k.get('id'), 'role': role_of(name), 'account': acct, 'status': k.get('status'),
        'started': k.get('created'), 'retired': k.get('retired'), 'session': k.get('session'),
        'fingerprint': k.get('fingerprint'), 'about': k.get('role', ''),
        'conductor': conductor if conductor != name and any(x.get('agent') == conductor for x in keys) else None,
        'keeps': keeps, 'worked_on': sites, 'commits': len(commits), 'latest': commits[:5],
    })
agents.sort(key=lambda a: (a['started'] or '', a['name']))
live = [a for a in agents if a['status'] not in ('retired', 'superseded')]

# Day by day: agents started that day, and live at the end of it (an agent counts until its retired date, if given).
days = sorted({a['started'] for a in agents if a['started']})
timeline = []
for d in days:
    started = sum(1 for a in agents if a['started'] == d)
    alive = sum(1 for a in agents if a['started'] and a['started'] <= d and not (a['retired'] and a['retired'][:10] <= d))
    timeline.append({'day': d, 'started': started, 'total_so_far': sum(1 for a in agents if a['started'] and a['started'] <= d), 'live': alive})

roles = collections.OrderedDict()
for a in agents:
    roles.setdefault(a['role'], []).append(a)
roles = collections.OrderedDict(sorted(roles.items(), key=lambda r: (-len(r[1]), r[0])))

(SITE / 'data').mkdir(exist_ok=True)
(SITE / 'data' / 'agents-all.json').write_text(json.dumps({
    'about': 'Every agent in the SovereignWebsite family, from the Factory\'s team/keys.json, with its work: commits '
             'carrying its Agent: trailer in the public repositories read. Built by tools/build-agents.py. "conductor" '
             'is the conductor of the same account, by name; "worked_on" is where its commits are.',
    'keys': KEYS_URL, 'repositories': [GH + r for r in repos()],
    'count': {'all': len(agents), 'live': len(live), 'retired': len(agents) - len(live)},
    'timeline': timeline, 'agents': agents,
}, indent=1, ensure_ascii=False) + '\n')

# Pages ---------------------------------------------------------------------------------------------------------
index = (SITE / 'index.html').read_text()
family = re.search(r'<nav class="family".*?</nav>', index, re.S)
family_css = re.search(r'\.family\{.*?(?=\n</style>|\n#|\n\.d-)', index, re.S)
family = family.group(0).replace('href="./"', 'href="/"') if family else ''
family_css = family_css.group(0) if family_css else ''

CSS = '''
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#5d5c57;--accent:#2f6b4f;--line:#e4e1d8;--card:#fff;--bar:#2f6b4f}
@media (prefers-color-scheme:dark){:root{--bg:#141513;--fg:#ecebe6;--muted:#a8a69e;--accent:#7fc3a0;--line:#2c2d29;--card:#1c1d1a;--bar:#7fc3a0}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:inherit}
.skip{position:absolute;left:-999px}.skip:focus{left:1rem;top:1rem;z-index:9;padding:.5rem 1rem;background:var(--accent);color:var(--bg)}
.top{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1.5rem;max-width:56rem;margin:0 auto;padding:1.5rem 1rem 0}
.top .name{font-weight:700;text-decoration:none}.top nav{display:flex;gap:1rem;margin-left:auto;font-size:.95rem}
.top nav a{color:var(--accent);font-weight:600}.top nav a[aria-current=page]{color:var(--fg);text-decoration:none}
main{max-width:56rem;margin:0 auto;padding:2.5rem 1rem 3rem}
.mark{margin:0;font-size:.75rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:700}
.mark a{color:inherit}
h1{font-size:clamp(2.2rem,6vw,3.4rem);line-height:1.05;margin:.3rem 0 1rem;letter-spacing:-.01em}
h2{font-size:1.3rem;margin:2.5rem 0 .75rem;padding-bottom:.4rem;border-bottom:2px solid var(--fg)}
.lede{color:var(--muted);font-size:1.08rem;margin:0 0 .6rem}.lede a,.muted a{color:var(--accent)}
.muted{color:var(--muted)}
.stats{display:flex;flex-wrap:wrap;gap:1.5rem 2.5rem;margin:1.5rem 0 0;padding:0;list-style:none}
.stats li{color:var(--muted);font-size:.9rem}.stats b{display:block;font-size:2.2rem;line-height:1.1;color:var(--fg)}
.days{width:100%;border-collapse:collapse;font-size:.92rem}.days th,.days td{text-align:left;padding:.35rem .5rem;border-bottom:1px solid var(--line)}
.days th{font-weight:600;color:var(--muted)}.days td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
.bar{display:inline-block;height:.7rem;background:var(--bar);border-radius:2px;vertical-align:middle;margin-right:.5rem}
.roles{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(14rem,1fr));gap:.75rem}
.roles a{display:block;padding:.75rem 1rem;border:1px solid var(--line);border-radius:10px;background:var(--card);text-decoration:none}
.roles a:hover,.roles a:focus-visible{border-color:var(--accent)}.roles b{display:block;font-size:1.05rem}.roles span{color:var(--muted);font-size:.85rem}
.generic{padding:1rem 1.2rem;border-left:4px solid var(--accent);background:var(--card);margin:1rem 0}
.generic p{margin:.2rem 0}
.agent{padding:1.25rem 0;border-bottom:1px solid var(--line)}
.agent h3{margin:0;font-size:1.15rem;overflow-wrap:anywhere}
.facts{display:grid;grid-template-columns:8rem minmax(0,1fr);gap:.15rem 1rem;margin:.6rem 0;font-size:.9rem}
.facts dt{color:var(--muted)}.facts dd{margin:0;overflow-wrap:anywhere}.facts a{color:var(--accent)}
.tag{display:inline-block;font-size:.75rem;padding:.05rem .55rem;border:1px solid var(--line);border-radius:999px;color:var(--muted);margin-left:.4rem;vertical-align:middle}
.tag.live{color:var(--accent);border-color:var(--accent)}
.work{list-style:none;margin:.4rem 0 0;padding:0;font-size:.9rem}.work li{padding:.2rem 0}
.work time{font:500 .8rem ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted);margin-right:.5rem}
.work a{color:var(--fg)}.work .repo{color:var(--muted)}
@media (max-width:30rem){.facts{grid-template-columns:minmax(0,1fr)}.facts dd{margin-bottom:.3rem}}
footer{max-width:56rem;margin:0 auto;padding:1rem 1rem 2rem;border-top:1px solid var(--line);font-size:.85rem;color:var(--muted)}
footer a{color:var(--accent)}
'''


def page(path, title, desc, body):
    url = f'{SITE_URL}{path}'
    return f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230f6e4f'/%3E%3Ctext x='16' y='23' font-family='Georgia,serif' font-size='20' font-weight='700' fill='%23fff' text-anchor='middle'%3ES%3C/text%3E%3C/svg%3E">
<title>{e(title)}: Sovereign Website Hub</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sovereign Website Hub">
<meta property="og:locale" content="en_GB">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}: Sovereign Website Hub">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE_URL}og.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Sovereign Website Hub">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}: Sovereign Website Hub">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{SITE_URL}og.jpg">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/json" href="/data/agents-all.json" title="Every agent, as data">
<style>{CSS}
{family_css}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{family}
<header class="top">
  <a class="name" href="/">Sovereign Website Hub</a>
  <nav aria-label="The hub"><a href="/">Showroom</a><a href="/latest/">Latest</a><a href="/directory/">Every site</a><a href="/agents/at-work/"{' aria-current="page"' if path == 'agents/at-work/' else ''}>Agents at work</a></nav>
</header>
<main id="main">
{body}
</main>
<footer>hub.sovereignweb.site · Part of the <a href="https://github.com/SovereignWebsite">SovereignWebsite</a> organisation · <a href="/policy/">How this site is governed</a> · No cookies, no tracking.</footer>
</body>
</html>
'''


def day(d):
    return datetime.date.fromisoformat(d[:10]).strftime('%-d %B %Y')


def agent_block(a):
    status = '<span class="tag live">Active</span>' if a in live else f'<span class="tag">{e((a["status"] or "").capitalize())}</span>'
    facts = [('Started', f'<time datetime="{e(a["started"])}">{day(a["started"])}</time>' if a['started'] else 'not recorded')]
    if a['session']:
        facts.append(('Session', f'<a href="{e(a["session"])}">{e(a["session"].rsplit("/", 1)[-1])}</a>'))
    if a['fingerprint']:
        facts.append(('Key', f'<code>{e(a["fingerprint"])}</code>'))
    if a['account']:
        facts.append(('Account', e(a['account'])))
    if a['conductor']:
        facts.append(('Conductor', f'<a href="/agents/at-work/conductor/#{e(slug(a["conductor"]))}">{e(a["conductor"])}</a>'))
    if a['keeps']:
        facts.append(('Keeps', ', '.join(f'<a href="{e(u)}">{e(re.sub("^https?://|/$", "", u))}</a>' for u in a['keeps'])))
    if a['worked_on']:
        facts.append(('Worked on', ', '.join(
            (f'<a href="{e(w["site"])}">{e(w["name"])}</a>' if w['site'] else f'<a href="{GH}{e(w["repo"])}">{e(w["name"])}</a>')
            + f' ({w["commits"]})' for w in a['worked_on'])))
    dl = ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts)
    if a['latest']:
        work_html = '<p class="muted">In action, its latest signed work:</p><ul class="work">' + ''.join(
            f'<li><time datetime="{e(c["when"])}">{e(c["when"][:16].replace("T", " "))}</time>'
            f'<a href="{GH}{e(c["repo"])}/commit/{e(c["sha"])}">{e(c["subject"])}</a> <span class="repo">{e(c["repo"].split("/")[-1])}</span></li>'
            for c in a['latest']) + '</ul>'
    else:
        work_html = '<p class="muted">No commits with its name in the repositories read; its work is elsewhere, or not yet begun.</p>'
    # One anchor per name on a page; a second key for the same name (an earlier, retired one) gets its key id too.
    anchor = slug(a['name'])
    if anchor in USED:
        anchor = f'{anchor}-{slug(a["id"] or str(len(USED)))}'
    USED.add(anchor)
    return (f'<article class="agent" id="{e(anchor)}"><h3>{e(a["name"])} {status}</h3>'
            f'<p class="muted">{e(a["about"])}</p><dl class="facts">{dl}</dl>{work_html}</article>\n')


slug = lambda name: re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

# /agents/at-work/
mx = max((t['live'] for t in timeline), default=1)
rows = ''.join(f'<tr><td><time datetime="{t["day"]}">{day(t["day"])}</time></td><td class="n">{t["started"]}</td>'
               f'<td class="n"><span class="bar" style="width:{round(8 * t["live"] / mx, 2)}rem"></span>{t["live"]}</td></tr>'
               for t in timeline)
accounts = collections.Counter(a['account'] for a in live if a['account'])
role_list = ''.join(f'<li><a href="/agents/at-work/{e(r)}/"><b>{e(r)}</b><span>{sum(1 for a in v if a in live)} active, {len(v)} in all</span></a></li>'
                    for r, v in roles.items())
newest = sorted(agents, key=lambda a: (a['started'] or '', a['name']), reverse=True)[:8]
newest_html = ''.join(f'<li><time datetime="{e(a["started"])}">{e(a["started"])}</time><a href="/agents/at-work/{e(a["role"])}/#{e(slug(a["name"]))}">{e(a["name"])}</a></li>'
                      for a in newest)
body = f'''<p class="mark">Agents</p>
<h1>The agents behind every site</h1>
<p class="lede">Every agent in the family, by name, with its session and its key, from the Factory\'s <a href="https://github.com/SovereignWebsite/SovereignWebsite__Factory/blob/dev/team/keys.json">team/keys.json</a>. Each role has a page: what that role does, then each agent in it, at work.</p>
<ul class="stats"><li><b>{len(live)}</b>active now</li><li><b>{len(agents)}</b>since the start</li><li><b>{len(agents) - len(live)}</b>retired</li><li><b>{len(roles)}</b>roles</li><li><b>{len(accounts)}</b>accounts</li></ul>
<h2>Roles</h2>
<ul class="roles">{role_list}</ul>
<h2>Newest agents</h2>
<ul class="work">{newest_html}</ul>
<h2>Day by day</h2>
<table class="days"><thead><tr><th scope="col">Day</th><th scope="col">Started</th><th scope="col">Active at the end of the day</th></tr></thead><tbody>{rows}</tbody></table>
<p class="muted">An agent counts as active until it is retired; where a key gives no retirement date, it counts as retired only from today. The same as data: <a href="/data/agents-all.json">data/agents-all.json</a>.</p>
<h2>How they connect</h2>
<p class="muted">Each account has a conductor that starts and coordinates its agents (conductor.b, conductor.c, conductor.d and so on); each agent page names its conductor and the sites its commits went to. {sum(1 for a in agents if a["conductor"])} agents have a conductor on their account.</p>
'''
W = SITE / 'agents' / 'at-work'
W.mkdir(parents=True, exist_ok=True)
(W / 'index.html').write_text(page('agents/at-work/', 'Agents', f'{len(live)} agents at work in the Sovereign Website family: every one by name, with its session, its key and its work.', body))

# /agents/at-work/<role>/
for r, members in roles.items():
    USED = set()
    first = members[0]
    generic = (f'<div class="generic"><p><b>What a {e(r)} agent does.</b> In the words of the first one, {e(first["name"])}, '
               f'started {day(first["started"]) if first["started"] else "on a date not recorded"}:</p><p>{e(first["about"])}</p></div>')
    act = sum(1 for a in members if a in live)
    body = (f'<p class="mark"><a href="/agents/at-work/">Agents at work</a></p><h1>{e(r)}</h1>'
            f'<p class="lede">{act} active, {len(members)} in all. First the role in general, then each agent in it, at work.</p>'
            f'{generic}<h2>The agents</h2>\n' + ''.join(agent_block(a) for a in sorted(members, key=lambda a: (a not in live, a['started'] or ''), reverse=False)))
    (W / r).mkdir(exist_ok=True)
    (W / r / 'index.html').write_text(page(f'agents/at-work/{r}/', f'Agents: {r}', f'The {r} agents of the Sovereign Website family: the role, then each agent with its session, its key and its work.', body))

print(f'agents: {len(agents)} ({len(live)} active), {len(roles)} roles, {sum(len(v) for v in work.values())} commits with an Agent: trailer')
