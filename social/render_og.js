// Рендер превью ссылок: social/og_build/*.html → static/og/*.png (1200×630). Запускает social/og.py
const { chromium } = require('playwright-core'); const path = require('path'); const fs = require('fs');
(async () => {
  const dir = path.join(__dirname, 'og_build'), out = path.join(__dirname, '..', 'static', 'og');
  const b = await chromium.launch({ executablePath: '/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome', args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const n of JSON.parse(fs.readFileSync(path.join(dir, 'jobs.json'), 'utf8'))) {
    await p.goto('file://' + path.join(dir, n + '.html')); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(150);
    const over = await p.evaluate(() => document.body.scrollHeight > 630 || document.querySelector('h1').scrollWidth > 1040);
    if (over) console.log('ПЕРЕПОЛНЕНИЕ', n);
    await p.screenshot({ path: path.join(out, n + '.png') });
  }
  await b.close();
})();
