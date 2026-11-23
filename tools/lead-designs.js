// Screenshots a lead site's five designs (designs/1.html to 5.html on the live site) for the hub's first screen.
// Usage: node tools/lead-designs.js <slug> <site url>   writes site/shots/<slug>-design-N.jpg (640 wide) and .webp
const { chromium } = require('playwright');
const path = require('path');
const [slug, base] = process.argv.slice(2);
(async () => {
  const S = path.join(__dirname, '..', 'site', 'shots') + '/';
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 0.5, colorScheme: 'light' });
  for (let d = 1; d <= 5; d++) {
    try {
      await p.goto(base.replace(/\/$/, '') + '/designs/' + d + '.html', { waitUntil: 'networkidle', timeout: 30000 });
      await p.evaluate(() => document.querySelectorAll('.family-credit,nav.family').forEach(x => x.style.display = 'none'));
      await p.waitForTimeout(300);
      await p.screenshot({ path: S + slug + '-design-' + d + '.jpg', type: 'jpeg', quality: 78 });
      console.log('design', d, 'taken');
    } catch (e) { console.log('design', d, 'failed, old shot kept:', e.message.split('\n')[0]); }
  }
  await b.close();
})();
