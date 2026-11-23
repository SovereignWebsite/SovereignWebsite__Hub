// The 20 views: each of the five designs at 390 and 1366 px, light and dark. Fails on sideways scroll or a broken image.
// Usage: python3 -m http.server 8766 -d site &  then, from a scratch folder: node <repo>/tools/checks/views.js  (writes r1-*.png there)
const { chromium } = require('playwright');
(async () => {
  const B = process.env.BASE || 'http://localhost:8766'; const errs = []; const b = await chromium.launch();
  for (const scheme of ['light', 'dark']) for (const [w, h, tag] of [[1366, 900, 'desk'], [390, 844, 'phone']]) {
    const c = await b.newContext({ viewport: { width: w, height: h }, colorScheme: scheme }); const p = await c.newPage();
    p.on('pageerror', e => errs.push(e.message)); p.on('requestfailed', r => errs.push('failed ' + r.url()));
    for (let d = 1; d <= 5; d++) {
      await p.goto(B + ({1:'/',2:'/register/',3:'/gallery/',4:'/contact-sheet/',5:'/street/'}[d])); await p.reload(); await p.waitForTimeout(300);
      const r = await p.evaluate(() => ({ ov: document.documentElement.scrollWidth > innerWidth + 1, cls: document.documentElement.className, imgH: Math.round(document.querySelector('main img').getBoundingClientRect().height), broken: [...document.images].filter(i => i.complete && !i.naturalWidth).length, ls: (() => { try { return localStorage.length } catch (e) { return -1 } })(), bands: document.querySelectorAll('.people .site').length }));
      if (r.ov) errs.push(`overflow ${scheme} ${tag} d${d}`); if (r.broken) errs.push(`broken img ${scheme} ${tag} d${d}`);
      if (tag === 'phone' && scheme === 'light') console.log(`d${d} phone frame img height ${r.imgH}px, people cards ${r.bands}, storage ${r.ls}`);
      await p.screenshot({ path: `r1-${scheme}-${tag}-${d}.png` });
    }
    await c.close();
  }
  console.log('errors:', errs); await b.close();
})();
