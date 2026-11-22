# The hub, rebuilt as the map of the whole family: plan

Draft by hub.c@SovereignWebsite.dinis, 22 November 2026, for Dinis Cruz. Nothing here is decided until Dinis says so. It builds on hub.b's docs/plan.md and the showroom hub.b and hub.d made; it replaces none of it.

Dinis, voice memo, about 17:30 UTC on 22 November 2026 (summarised): the hub should let him navigate the entire universe (do we have a Google Maps site? which agents?), show how many agents there are, now and over time, and how they connect, and be a newsroom: every site brought online, every new thing connected, and above all customers, arrives on the hub first. A very few sites stay off.

## What exists today

- The showroom at hub.sovereignweb.site: 34 public live sites in site/sites.json (hub-site/1 entries, one per site, added by each site's agent), built into site/index.html by tools/build-showroom.py, in seven sections: People, Startups, Providers, Businesses, PrompTugal.news, Demos, Tools.
- site/data/agents.json: only the hub's own agent.
- The Factory's registry, read as data: org/repos.json lists 7 SovereignWebsite repositories (no site list, no dates); org/dns.json the DNS records; team/keys.json 42 agent keys (id, agent, role, created date, status, session), 38 active and 4 retired, created 19 to 22 November.
- What is missing for the newsroom: no entry in sites.json carries a date. The only honest date today is when the hub first listed a site, which this repository's history records.

## The new structure

One static site, four parts, one top navigation: Latest, Showroom, Sites, Agents.

| Part | What it shows | Data it reads |
|---|---|---|
| Latest (the newsroom) | Every new thing, newest first: sites listed, then agents joining, then customers and handovers. Each item links to its proof (the commit or the key entry). | site/sites.json and its git history (first listing); the Factory's team/keys.json (agent created dates); later a `listed`, `online` and `customer` field in each hub-site/1 entry. |
| Showroom | Today's page, unchanged: the best sites with screenshots. | site/sites.json (hub.b's builder). |
| Sites | Every site, by section, with a search box (name, address, section, owner, summary) that works without a server: a small script filtering a list already in the page, which also works with the script off. "Do we have a Google Maps site?" is one word typed. | site/sites.json, and the Factory's org/repos.json for the organisation's own sites. |
| Agents | Dinis, 22 Nov: "the agent page should show the names and sessions. That's the point. Each page should show the generic and then should actually show it in action." So: one page per role (conductor, hub, sites, factory, design and so on) saying what that role does in general, then every agent in that role, by name, with its session, its key, when it started, and its work in action: its latest signed commits and the sites it keeps. Above them, how many agents (a count by day from created dates, active against retired), grouped by account (.b, .c, .d, mistral) and by role, and how they connect: conductor to agents, agent to the sites it keeps. | The Factory's team/keys.json; each site's keeper from its sites.json entry; the hub's agents.json. Connections not in any file today are added as data first, never drawn by hand. |

Everything is built by a script from data and committed as static files: no server, no cookies, no tracking, nothing stored in the browser.

## Which sites stay off

The registry rule stays: only public, live sites with their owner's agreement; a private or vault-only site never appears, not by name or count.

Dinis, 22 November 2026 (in hub.c's session): only a couple stay off: the Algarve Evolution site and one request not yet built (named in his session, not here). Neither is in sites.json today. tools/build-latest.py also holds them as hashes of their slugs, so they are never listed even if an entry is added; the Sites and Agents pages will use the same list. To be confirmed with Dinis before anything else goes on it.

## First slice (built in this branch)

"Latest": every public site in site/sites.json, newest first, by when the hub first listed it, grouped by day, each time linking to the commit that listed it.

- tools/build-latest.py builds site/data/latest.json (the data) and site/latest/index.html (the page) from sites.json and git history. No date is typed by hand. The page says plainly that the time is when the hub listed the site, not always when the site went online.
- New files only: the showroom, its builder and sites.json are untouched. A link from the showroom to Latest is one line in tools/build-showroom.py, left for hub.b or the conductor to agree.
- Checks run locally and pass: share check, internal and external links, no em dashes, leak scan, Agent Behaviour Policy, HTML validity, axe on /, /latest/ and /policy/.

## Next slices, in order

1. Agents joining, in Latest and on an Agents page: counts now and by day, from the Factory's team/keys.json.
2. Sites: every site by section with a search.
3. Dates and customers in the data: optional `listed`, `online` and `customer` fields in hub-site/1, so a customer's site leads Latest the moment it is listed.
4. How agents connect: who conducts whom, and who keeps which site, as data first.

## Open questions for Dinis

1. Answered: the Algarve Evolution site and one unbuilt request stay off; to double-check with Dinis.
2. Should Latest become the hub's front page, with the showroom one tap away, or stay a second page?
3. Answered: yes, the Agents pages show names and sessions, the role in general and then each agent in action.
4. May hub.c push to this repository's dev (hub.b is its keeper)?
