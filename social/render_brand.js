// node render_brand.js → static/social/otto-avatar.png (1024²), otto-cover.png (1640×720) и превью в круге
const {chromium}=require('playwright-core');const path=require('path');
(async()=>{const b=await chromium.launch({executablePath:'/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',args:['--no-sandbox']});
for(const [f,w,h] of [['otto-avatar',1024,1024],['otto-cover',1640,720]]){const p=await b.newPage({viewport:{width:w,height:h}});
 await p.goto('file://'+path.join(__dirname,f+'.svg'));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
 await p.screenshot({path:path.join(__dirname,'../static/social/'+f+'.png')});await p.close()}
await b.close()})();
