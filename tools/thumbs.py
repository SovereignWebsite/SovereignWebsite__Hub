#!/usr/bin/env python3
# Makes a 640-pixel-wide copy of each desktop screenshot (shots/<slug>-640.jpg), so pages can serve
# the small one by srcset and the 1280 one only to wide, sharp screens. Run after tools/take-shots.js.
import pathlib
from PIL import Image

SHOTS = pathlib.Path(__file__).resolve().parent.parent / 'site' / 'shots'
n = 0
for p in sorted(SHOTS.glob('*.jpg')):
    if p.stem.endswith(('-phone', '-640')) or p.stem.startswith('hub-design'):
        continue
    out = p.with_name(p.stem + '-640.jpg')
    if out.exists() and out.stat().st_mtime >= p.stat().st_mtime:
        continue
    im = Image.open(p).convert('RGB')
    im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS).save(out, quality=78, optimize=True, progressive=True)
    n += 1
print(f'thumbs: {n} made')
