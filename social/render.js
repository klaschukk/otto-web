// node render.js  → static/social/otto-post-{bg,ru}.jpg (1080×1350)
const {chromium}=require('playwright-core');const path=require('path');
(async()=>{const b=await chromium.launch({executablePath:'/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',args:['--no-sandbox','--allow-file-access-from-files']});
for(const l of ['bg','ru']){const p=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:1});
 await p.goto('file://'+path.join(__dirname,'post.html')+'?'+l);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
 console.log(l,await p.evaluate(()=>[[...document.fonts].filter(f=>f.status==='loaded').length,[...document.images].every(i=>i.naturalWidth>0)]));
 await p.screenshot({path:path.join(__dirname,'../static/social/otto-post-'+l+'.jpg'),type:'jpeg',quality:92});await p.close()}
await b.close()})();
