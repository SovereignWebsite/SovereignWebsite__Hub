// First screens and full heights: each design and /designs/ at 1366 and 390 px. Every design must stay under 8,000 px on a phone.
// Usage: node tools/checks/first-screens.js <folder for f*-desk.png and f*-phone.png>
const {chromium}=require('playwright');const D=process.argv[2];
const U={1:'/',2:'/register/',3:'/gallery/',4:'/contact-sheet/',5:'/street/',6:'/designs/'};
(async()=>{const b=await chromium.launch();const errs=[];
for(const [n,w,h] of [['desk',1366,900],['phone',390,844]]){const c=await b.newContext({viewport:{width:w,height:h}});const p=await c.newPage();
 p.on('pageerror',x=>errs.push(x.message));p.on('requestfailed',r=>errs.push('failed '+r.url()));
 for(const d of [1,2,3,4,5,6]){await p.goto('http://localhost:8766'+U[d]);await p.waitForTimeout(500);
  await p.screenshot({path:`${D}/f${d}-${n}.png`});
  const r=await p.evaluate(()=>({H:document.documentElement.scrollHeight,ov:document.documentElement.scrollWidth>innerWidth}));
  const kb=await p.evaluate(()=>Math.round(performance.getEntriesByType('resource').reduce((a,x)=>a+(x.transferSize||0),0)/1024));
  console.log(n,d,'height',r.H,'overflow',r.ov,'loadedKB',kb);}
 await c.close();}
console.log('errors',errs);await b.close();})();
