// Prints the IaC's site requests as JSON lines: host, title, kind, and whether the site is private (a vault site) or
// not yet made. Run from the operator builder with the path of a SovereignWebsite__IaC checkout:
//   node tools/operator-hosts.mjs <iac-checkout>
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
const iac = process.argv[2];
const { load, host } = await import(pathToFileURL(join(iac, 'build', 'requests.mjs')).href);
const { requests } = load(join(iac, 'requests'));
for (const r of requests) console.log(JSON.stringify({ host: host(r), label: r.label, title: r.title, kind: r.kind, group: r.group || '', private: r.access === 'vault', made: r.apply !== 'dry-run' }));
