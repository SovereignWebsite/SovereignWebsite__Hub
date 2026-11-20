// Retakes every live site's showroom screenshots from the live site: desktop 1280x800, and phone
// 390 wide from below the shared family bar if the site has one. A site that fails to load keeps
// its previous screenshots and is reported, so one bad fetch never blanks a card.
// Usage: node tools/take-shots.js [slug ...]    (needs Playwright with Chromium)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const site = path.join(__dirname, '..', 'site'), only = process.argv.slice(2);
  const sites = JSON.parse(fs.readFileSync(path.join(site, 'sites.json'))).sites
    .filter(s => s.status === 'live' && s.shot && (!only.length || only.includes(s.slug)));
  const b = await chromium.launch(), failed = [];
  for (const s of sites) {
    const base = path.join(site, s.shot), u = s.address.url;
    try {
      const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
      const r = await p.goto(u, { waitUntil: 'networkidle', timeout: 45000 });
      if (!r || !r.ok()) throw new Error('HTTP ' + (r && r.status()));
      await p.waitForTimeout(1200);
      const desk = await p.screenshot({ type: 'jpeg', quality: 78 });
      const m = await b.newPage({ viewport: { width: 390, height: 780 } });
      await m.goto(u, { waitUntil: 'networkidle', timeout: 45000 }); await m.waitForTimeout(800);
      const y = await m.evaluate(() => { const f = document.querySelector('nav.family'); return f ? Math.round(f.getBoundingClientRect().bottom + scrollY) : 0; });
      const phone = await m.screenshot({ type: 'jpeg', quality: 78, clip: { x: 0, y, width: 390, height: 780 - y }, fullPage: true });
      fs.writeFileSync(base + '.jpg', desk); fs.writeFileSync(base + '-phone.jpg', phone);
      console.log('ok', s.slug); await p.close(); await m.close();
    } catch (e) { failed.push(s.slug); console.log('FAILED', s.slug, '(kept the previous screenshots):', e.message.split('\n')[0]); }
  }
  await b.close();
  if (failed.length) process.exitCode = 1;
})();
