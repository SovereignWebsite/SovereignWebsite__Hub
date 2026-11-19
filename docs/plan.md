# The hub: plan

Draft by hub.b@SovereignWebsite.dinis, 19 November 2026, for Dinis Cruz. Nothing here is decided until Dinis says so.

Sources: Dinis Cruz's articles on the SGit Newsroom, "A hub for agentic sites" (15 Nov 2026), "Your own agentic cell, end to end" (17 Nov), "Deploy sgit in your own environment, from a CI pipeline" (17 Nov) and "Sovereign Agentic Website" (19 Nov); SovereignWebsite__Factory (README.md, REALITY.md, org/repos.json); the sgit CLI help (sgit-ai v0.27.0).

## What the hub is

hub.sovereignwebsite.site is a code host for sovereign agentic websites: one page per site, generated from a small file each site carries. Every site lives in two places, a public repository and an sgit vault holding the same files. Because the sites are static, a vault is a complete site: it can be cloned, opened locally and handed on, so vaults can be the distribution medium. The hub itself is a static site in site/, with no database, no server code, no cookies and no tracking.

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

## Keeping a site's vault and repository in step

The repository stays the source of truth for now, as the articles describe: GitHub Pages serves the site, the vault follows.

1. On every push to a site's release branch, a CI job copies the built files into the site's vault (`sgit write` or a clone, commit and `sgit push`) with the repository commit in the vault commit message.
2. The same job compares the two trees (file list and hashes from the checkout against `sgit ls` / `sgit cat`) and writes the result, with both commit ids, to a `status.json` the hub reads. A mismatch shows on the site's hub page.
3. If the owner chooses a public vault, `sgit publish --visibility public` produces the static plaintext surface; that publishes the read key and cannot be undone, so it is the owner's decision, never the pipeline's default.
4. The vault key the job uses is a CI secret in a protected environment, never in the repository, following the factory pattern (protected environment, person's approval for real runs, least privilege, check workflows first).

## What can be automated, and what needs a person

Automated: creating a site's vault when the factory creates its repository; pushing each release to the vault; the identity check between vault and repository; collecting `hub.json` files into the registry; generating the hub's pages; checking links and HTTPS.

Needs a person: consent to be listed (the owner); choosing to publish a vault's read key (the owner); merging to main and approving protected runs (Dinis); creating the CI secret for vault access and the sgit server or access token it uses (Dinis); anything that accepts terms or costs money.

## First steps done

- `site/index.html` lists the four SovereignWebsite sites from `site/sites.json`, with their repositories. None has a vault yet.
- `site/schema/hub-site.schema.json`, the first draft of the format.
- `team/keys.json`, this agent's public key, and `tools/sgit-ssh-sign.py`, which signs git commits as SSH signatures through `sgit pki sign`, so the private key never leaves sgit's key store.

## Open questions for Dinis

1. Which sgit server holds the sites' vaults: the public SG/Send server, or one deployed in our own account from CI?
2. Should the factory create each site's vault, or should this hub's CI do it? Where does the vault key for CI live?
3. Public read keys: on by default for SovereignWebsite's own sites, or bare vaults first?
4. Who is the owner listed for the four sites (SovereignWebsite, AgentiCCells, or you), and which licence for text and code (the Factory uses Apache-2.0 for code and CC BY 4.0 for text)?
5. Page path: `hub.sovereignwebsite.site/<owner>/<site>/` as in the article?
6. Should the hub also list the AgentiCCells and newsroom demo sites the article mentions, or SovereignWebsite sites only?
7. This agent's key lives in this container and goes when it is reclaimed. Is a session key, rotated per session, what you want?
