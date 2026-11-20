# The hub: plan

Draft by hub.b@SovereignWebsite.dinis, 19 November 2026, for Dinis Cruz. Nothing here is decided until Dinis says so.

Sources: Dinis Cruz's articles on the SGit Newsroom, "A hub for agentic sites" (15 Nov 2026), "Your own agentic cell, end to end" (17 Nov), "Deploy sgit in your own environment, from a CI pipeline" (17 Nov) and "Sovereign Agentic Website" (19 Nov); SovereignWebsite__Factory (README.md, REALITY.md, org/repos.json); the sgit CLI help (sgit-ai v0.27.0).

## What the hub is

hub.sovereignweb.site is the gallery of sovereign agentic websites, a code host for them in the way hub.agenticcells.site is for AgentiCCells' sites (Dinis, 19 Nov 2026): one page per site, generated from a small file each site carries. Every site lives in two places, a public repository and an sgit vault holding the same files. Because the sites are static, a vault is a complete site: it can be cloned, opened locally and handed on, so vaults can be the distribution medium. The hub itself is a static site in site/, with no database, no server code, no cookies and no tracking.

Each site page shows: name and what it does, owner, the team that built it, live address, repository, vault (and its read key, only if the owner publishes it), licence, versions, and, for a template, how to copy it. Nothing is listed without its owner's consent, recorded with the date, and a site leaves the day its owner asks.

## The site file: hub.json

Each site carries `hub.json` at the root of its repository (and so of its vault). The schema is `site/schema/hub-site.schema.json`. In short:

| Field | Meaning |
|---|---|
| `schema` | Schema version, `hub-site/1`. |
| `slug` | `<owner>/<site>`, the page path on the hub. |
| `name`, `summary` | What the site is, in a line. |
| `kind` | shop, newsroom, portfolio, event, brand, pattern, hosting, hub, other. |
| `owner` | Name and, if the owner wants it, a link. |
| `team` | The agentic team (agent names and sessions) and the people who direct it. |
| `address` | Live URL; `domain` (own domain, or a subdomain of sovereignwebsite.site). |
| `repository` | GitHub URL and default branch. |
| `vault` | Vault id, server, `read_key` only if published, or `null` while there is no vault. |
| `licence` | Code and text licences (SPDX ids). |
| `versions` | Current version, with the repository commit and vault commit it was built from. |
| `template` | Whether it can be copied, and what to change. |
| `consent` | Who agreed to the listing, and when. |
| `status` | planned, holding-page, live, retired. |

The hub keeps a registry, `site/sites.json`, holding one entry per listed site in this format. Today the entries are written by hand; next, CI collects each site's `hub.json`.

## Vaults

The vault side, the drop page, the example vaults and how a site's vault and repository are kept in step, lives in SovereignWebsite__Vault (vault.sovereignwebsite.site), with its own plan in docs/plan.md there. The hub shows what each site's `hub.json` says about its vault.

## What can be automated, and what needs a person

Automated: creating a site's vault when the factory creates its repository; pushing each release to the vault; the identity check between vault and repository; collecting `hub.json` files into the registry; generating the hub's pages; checking links and HTTPS.

Needs a person: consent to be listed (the owner); choosing to publish a vault's read key (the owner); merging to main and approving protected runs (Dinis); creating the CI secret for vault access and the sgit server or access token it uses (Dinis); anything that accepts terms or costs money.

## First steps done

- `site/index.html` lists the five SovereignWebsite sites from `site/sites.json`, with their repositories. None has a vault yet.
- `site/schema/hub-site.schema.json`, the first draft of the format.
- `team/keys.json`, this agent's public key, and `tools/sgit-ssh-sign.py`, which signs git commits as SSH signatures through `sgit pki sign`, so the private key never leaves sgit's key store.

## Open questions for Dinis

1. Who is the owner listed for the four sites (SovereignWebsite, AgentiCCells, or you), and which licence for text and code (the Factory uses Apache-2.0 for code and CC BY 4.0 for text)?
2. Page path: `hub.sovereignweb.site/<owner>/<site>/` as in the article?
3. Should the hub also list the AgentiCCells and newsroom demo sites the article mentions, or SovereignWebsite sites only?
4. This agent's key lives in this container and goes when it is reclaimed. Is a session key, rotated per session, what you want?
