// axe-core in the same 20 views. Needs axe-core: npm i --no-save axe-core in the folder you run it from.
const { chromium } = require('playwright'); const axe = require.resolve('axe-core/axe.min.js');
(async () => { const b = await chromium.launch(); const out = [];
  for (const scheme of ['light','dark']) for (const w of [390,1366]) { const c = await b.newContext({viewport:{width:w,height:900},colorScheme:scheme}); const p = await c.newPage();
    for (let d=1; d<=5; d++) { await p.goto('http://localhost:8766' + ({1:'/',2:'/register/',3:'/gallery/',4:'/contact-sheet/',5:'/street/'}[d])); await p.reload(); await p.addScriptTag({path:axe});
      const r = await p.evaluate(async()=> (await axe.run(document,{resultTypes:['violations']})).violations.map(v=>v.id+':'+v.impact+':'+v.nodes.length));
      if (r.length) out.push(`${scheme} ${w} d${d}: ${r.join(', ')}`); }
    await c.close(); }
  console.log(out.length ? out.join('\n') : 'axe: no violations in 20 views'); await b.close(); })();
