// Page weight per design on desktop: the first screen, then the whole page after scrolling to the end.
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
for(const u of ['/','/gallery/','/contact-sheet/','/street/','/line/','/designs/']){const c=await b.newContext({viewport:{width:1366,height:900}});const p=await c.newPage();let bytes=0,first=0;
p.on('response',async r=>{try{const l=(await r.body()).length;bytes+=l}catch(e){}});
await p.goto('http://localhost:8766'+u,{waitUntil:'networkidle'});first=bytes;
await p.evaluate(async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}});await p.waitForTimeout(800);
console.log(u,'first screen',Math.round(first/1024)+'KB','whole page',Math.round(bytes/1024)+'KB');await c.close();}
await b.close();})();
