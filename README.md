# SovereignWebsite__Hub
hub.sovereignweb.site: the hub for sovereign websites powered by sgit vaults; every site lives in a public repository and a vault holding the same files.

## For people working on this repository

The site is static files in `site/`: no server code, no cookies, no tracking. It is published from the `dev` branch; `main` is locked.

### How to build and check
1. Change the data or the generator, not the built pages:
   - the data is `site/sites.json`, `site/features.json` and `tools/showroom/building-extra.json`;
   - the generator is `tools/build-showroom.py` and `tools/showroom/*.css`.
2. Rebuild with `python3 tools/build-showroom.py`. `tools/build-building.py` refreshes `/building/` from sites.b's register.
3. Run the pipeline's checks locally:
   `rm -rf _site; SITE_VERSION=v0.1.99 node .github/ci/build.mjs; node .github/ci/share-check.mjs _site; SWS_OWN_SITE=1 node .github/ci/quality.mjs _site; npx --yes html-validate@8.24.0 --config .github/ci/htmlvalidate.json "_site/**/*.html"`
4. Push to `dev`. The Pages workflow runs the same checks and tags `v0.1.N` when they pass.

### What not to touch
- `main`, `.github/`, `team/keys.json` and `site/keys/`.
- Never commit a private key or token.
- Never name or list a private (vault) site, or a private person.
- Never publish a price, offer or customer that no signed decision record holds.
- The first handed-over site is listed but its owner is not named (`UNNAMED` in `tools/build-showroom.py`).
- Every design must stay under 8,000 px tall on a phone.

### Who reviews
- hub.b keeps the site. Its area is https://hub.sovereignweb.site/factory/dinis-cruz/account-b/ and a fresh session starts at `docs/handover/START.md`.
- design.b and design.b.rounds review the design in Site__Agents__Design (`docs/reviews/hub`).
- Decisions are Dinis Cruz's, through decisions.b: https://decisions.agents.sovereignweb.site/ask/.
