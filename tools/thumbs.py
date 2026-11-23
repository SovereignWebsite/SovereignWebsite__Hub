#!/usr/bin/env python3
# Makes smaller copies of each desktop screenshot (shots/<slug>-640.jpg, -480.webp, -960.webp), so pages can serve
# a small one by srcset and the 1280 one only to wide, sharp screens. Run after tools/take-shots.js.
import pathlib
from PIL import Image

SHOTS = pathlib.Path(__file__).resolve().parent.parent / 'site' / 'shots'
# Also WebP at 480 and 960 pixels wide, and a WebP of the phone crop, offered first by the pages' <picture>.
def fresh(out, src):
    return out.exists() and out.stat().st_mtime >= src.stat().st_mtime


n = 0
for p in sorted(SHOTS.glob('*.jpg')):
    if p.stem.endswith('-640') or p.stem.startswith('hub-design'):
        continue
    im = None
    if p.stem.endswith('-phone'):
        out = p.with_suffix('.webp')
        if not fresh(out, p):
            Image.open(p).convert('RGB').save(out, quality=72, method=6)
            n += 1
        continue
    for w, ext, q in ((640, 'jpg', 78), (480, 'webp', 72), (960, 'webp', 72)):
        out = p.with_name(f'{p.stem}-{w}.{ext}')
        if fresh(out, p):
            continue
        im = im or Image.open(p).convert('RGB')
        small = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        small.save(out, quality=q, optimize=True, progressive=True) if ext == 'jpg' else small.save(out, quality=q, method=6)
        n += 1
# Portrait crops for lead entries (tools/showroom/crops.json), for phones.
import json
for slug, c in json.loads((SHOTS.parent.parent / 'tools' / 'showroom' / 'crops.json').read_text()).items():
    src = SHOTS / f'{slug}.jpg'
    if not isinstance(c, dict) or not src.exists():
        continue
    part = Image.open(src).convert('RGB').crop(tuple(c['box']))
    part.save(SHOTS / f'{slug}-portrait.jpg', quality=80, optimize=True, progressive=True)
    part.save(SHOTS / f'{slug}-portrait.webp', quality=74, method=6)
    n += 2
print(f'thumbs: {n} made')
