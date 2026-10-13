#!/usr/bin/env python3
"""Аватар и обложка для соцсетей: SVG со встроенными шрифтами → social/*.svg. PNG делает render_brand.js."""
import base64, pathlib
R = pathlib.Path(__file__).resolve().parent
F = R.parent / "static" / "fonts"
CYR = "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"
def face(fam, w, f, rng=None):
    b = base64.b64encode((F / f).read_bytes()).decode()
    return f'@font-face{{font-family:"{fam}";font-weight:{w};src:url(data:font/woff2;base64,{b}) format("woff2");' + (f"unicode-range:{rng}" if rng else "") + "}"
FONTS = "".join([face("Onest", "100 900", "onest-cyrillic-4c7562.woff2", CYR), face("Onest", "100 900", "onest-latin-cebbb5.woff2"),
                 face("IBM Plex Mono", "500", "ibm-plex-mono-cyrillic-5907a9.woff2", CYR), face("IBM Plex Mono", "500", "ibm-plex-mono-latin-a7544c.woff2")])
STYLE = f'<style>{FONTS}.s{{font-family:"Onest",Arial,sans-serif}}.m{{font-family:"IBM Plex Mono",monospace;font-weight:500}}</style>'

# аватар 1024×1024: соцсети режут по кругу, всё важное в центральном квадрате ~700 px
avatar = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">{STYLE}
<rect width="1024" height="1024" fill="#0e0f11"/>
<text class="s" x="512" y="520" text-anchor="middle" font-size="290" font-weight="800" letter-spacing="-10" fill="#fff">Otto</text>
<rect x="452" y="580" width="330" height="140" fill="#ffe24a"/>
<text class="m" x="617" y="686" text-anchor="middle" font-size="112" fill="#111214">.web</text>
</svg>'''

# обложка 1640×720: телефон режет края, компьютер режет верх и низ; текст в центральных 1280×560
cover = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1640 720" width="1640" height="720">{STYLE}
<rect width="1640" height="720" fill="#0e0f11"/>
<text class="s" x="190" y="170" font-size="40" font-weight="800" letter-spacing="-1.2" fill="#fff">Otto</text>
<rect x="278" y="136" width="96" height="46" fill="#ffe24a"/>
<text class="m" x="326" y="171" text-anchor="middle" font-size="31" fill="#111214">.web</text>
<text class="s" x="186" y="318" font-size="112" font-weight="800" letter-spacing="-4" fill="#fff">Сайт за вашето</text>
<text class="s" x="186" y="430" font-size="112" font-weight="800" letter-spacing="-4" fill="#ffe24a">заведение</text>
<text class="s" x="190" y="506" font-size="35" font-weight="400" fill="#a3a7ad">Меню от телефона · резервация на маса · карта</text>
<rect x="1150" y="232" width="300" height="100" fill="#ffe24a"/>
<text class="m" x="1300" y="303" text-anchor="middle" font-size="60" fill="#111214">от 79 €</text>
<text class="s" x="1450" y="378" text-anchor="end" font-size="30" font-weight="500" fill="#fff">еднократно</text>
<text class="s" x="1450" y="416" text-anchor="end" font-size="30" font-weight="400" fill="#a3a7ad">първо безплатен пример</text>
<text class="m" x="1450" y="506" text-anchor="end" font-size="35" fill="#fff">otto-web.online</text>
<rect x="190" y="560" width="1260" height="2" fill="#2a2d31"/>
<text class="s" x="190" y="606" font-size="28" font-weight="500" fill="#a3a7ad">Бургас · Кирил Лащук</text>
<text class="m" x="1450" y="606" text-anchor="end" font-size="28" fill="#a3a7ad">Telegram @klaschukk</text>
</svg>'''
(R / "otto-avatar.svg").write_text(avatar, encoding="utf-8"); (R / "otto-cover.svg").write_text(cover, encoding="utf-8")
print("svg:", len(avatar) // 1024, "KB,", len(cover) // 1024, "KB")
