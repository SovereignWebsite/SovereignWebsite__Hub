// Usage: serve site/ on port 8766 (or BASE), then node tools/hub-shots.js
// Thumbnails of the hub in each design (for its own design chooser) and the 1200x630 social card.
const { chromium } = require('playwright');
(async () => {
  const S = require('path').join(__dirname, '..', 'site') + '/', B = process.env.BASE || 'http://localhost:8766';
  const b = await chromium.launch();
  const c = await b.newContext({ viewport: { width: 1280, height: 800 }, colorScheme: 'light', deviceScaleFactor: 0.5 });
  const p = await c.newPage();
  for (let d = 1; d <= 5; d++) {
    await p.goto(B + ({1:'/gallery/',2:'/'}[d] || '/#design-' + d)); await p.reload({ waitUntil: 'networkidle' }); await p.waitForTimeout(400);
    await p.evaluate(() => { const f = document.querySelector('nav.family'); if (f) f.style.display = 'none'; });
    await p.screenshot({ path: S + 'shots/hub-design-' + d + '.jpg', type: 'jpeg', quality: 72 });
  }
  const o = await b.newPage({ viewport: { width: 1200, height: 630 } });
  const img = n => B + '/shots/' + n + '.jpg'; await o.goto(B + '/sites.json');
  await o.setContent(`<html><body style="margin:0;width:1200px;height:630px;background:#0d0f12;color:#eef1f4;font-family:system-ui,sans-serif;overflow:hidden">
  <div style="padding:56px 64px 0"><div style="font-size:22px;letter-spacing:.16em;text-transform:uppercase;color:#7cf0c4;font-weight:700">Sovereign Website Hub</div>
  <div style="font-size:64px;font-weight:800;line-height:1.05;margin-top:12px">Websites their owners own.</div></div>
  <div style="display:flex;gap:28px;padding:44px 64px 0">${['kate-curtis-evans','emily-cruz','sarah-cruz'].map(n=>`<img src="${img(n)}" style="width:336px;height:210px;object-fit:cover;object-position:top;border-radius:12px;border:1px solid #262b31;box-shadow:0 20px 50px -20px #7cf0c4">`).join('')}</div>
  <div style="position:absolute;bottom:34px;left:64px;font-size:22px;color:#9aa3ad">hub.sovereignweb.site</div></body></html>`, { waitUntil: 'networkidle' });
  await o.screenshot({ path: S + 'og.jpg', type: 'jpeg', quality: 82 });
  await b.close(); console.log('hub thumbnails and og.jpg written');
})();
