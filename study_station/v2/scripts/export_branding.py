"""Export approved StudyStation masters; resize/pad only, never redraw the logo.

Run from v2: python scripts/export_branding.py
Requires the project's pinned Pillow. Generated shell HTML is refreshed separately:
python -m app.shell
"""
import base64
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

V2 = Path(__file__).resolve().parents[1]
STUDY = V2.parent
BRANDING = V2 / 'design' / 'branding'
STATIC = V2 / 'app' / 'static'
PROMO = STUDY / 'promo' / 'branding'
PLAY = BRANDING / 'play-store'
MASTER = BRANDING / 'studystation-multicolor-master.png'
EMBLEM = BRANDING / 'studystation-emblem-crop.png'
# Pixel bounds in the exact approved 1254x1254 master: entire emblem, above wordmark.
EMBLEM_CROP = (150, 55, 1105, 955)
OUTPUTS = []


def fitted(image, size, padding=0, background=(255, 255, 255, 0)):
    canvas = Image.new('RGBA', size, background)
    inner = (size[0] - padding * 2, size[1] - padding * 2)
    scaled = ImageOps.contain(image.convert('RGBA'), inner, Image.Resampling.LANCZOS)
    canvas.alpha_composite(scaled, ((size[0] - scaled.width) // 2, (size[1] - scaled.height) // 2))
    return canvas


def save(image, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.jpg':
        image.convert('RGB').save(path, quality=95, subsampling=0, optimize=True)
    elif path.suffix == '.webp':
        image.save(path, lossless=True, method=6)
    else:
        image.save(path, optimize=True)
    OUTPUTS.append(path)


def font(size, bold=False):
    name = 'NotoSans-Bold.ttf' if bold else 'NotoSans-Regular.ttf'
    return ImageFont.truetype(str(STUDY / 'promo' / 'fonts' / name), size)


def panel(master, size, logo_box, text_origin, text_size):
    canvas = Image.new('RGBA', size, 'white')
    x, y, width, height = logo_box
    canvas.alpha_composite(fitted(master, (width, height), background='white'), (x, y))
    draw = ImageDraw.Draw(canvas)
    tx, ty = text_origin
    for index, text in enumerate(('GK · Maths', 'Reasoning · English', 'Hindi-first quiz practice')):
        draw.text((tx, ty + index * int(text_size * 1.7)), text,
                  font=font(text_size if index < 2 else int(text_size * .72), bold=index < 2), fill='#062252')
    return canvas


def version_manifest_icons():
    """Change only icon src values, preserving unrelated manifest fields/formatting."""
    path = STATIC / 'manifest.webmanifest'
    text = path.read_text(encoding='utf-8')
    for size in (192, 512):
        filename = f'icon-{size}.png'
        version = hashlib.sha256((STATIC / filename).read_bytes()).hexdigest()[:12]
        pattern = r'("src"\s*:\s*")/static/' + re.escape(filename) + r'(?:\?v=[a-f0-9]+)?(")'
        text, count = re.subn(pattern, lambda match: match[1] + f'/static/{filename}?v={version}' + match[2], text)
        if count != 1:
            raise ValueError(f'Expected exactly one manifest source for {filename}')
    path.write_text(text, encoding='utf-8', newline='\n')


def main():
    OUTPUTS.clear()
    master = Image.open(MASTER).convert('RGBA')
    if master.size != (1254, 1254):
        raise ValueError('Approved full master dimensions changed; review crop before exporting')
    emblem = master.crop(EMBLEM_CROP)
    emblem.save(EMBLEM, optimize=True)
    # Preserve exact artwork on its white background: no tracing or background removal.
    for size, name in ((192, 'icon-192.png'), (512, 'icon-512.png')):
        save(fitted(emblem, (size, size), round(size * .12), background='white'), STATIC / name)
    version_manifest_icons()
    save(fitted(emblem, (96, 96), 4), STATIC / 'brand-mark.webp')
    save(fitted(emblem, (64, 64), 3), STATIC / 'favicon.png')
    # The legacy SVG URL is still accepted by the APK's bundled-asset router.
    buffer = io.BytesIO()
    fitted(emblem, (192, 192), 8).save(buffer, format='PNG', optimize=True)
    svg = STATIC / 'icon.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">'
                   '<image width="192" height="192" href="data:image/png;base64,' +
                   base64.b64encode(buffer.getvalue()).decode('ascii') + '"/></svg>\n', encoding='utf-8', newline='\n')
    OUTPUTS.append(svg)
    # Existing Android adaptive XML supplies its own 18dp inset on a 108dp layer.
    # With 80px padding the outer book corners fit the central 33dp-radius safe circle,
    # not merely its 66dp bounding square (covered by test_branding.py).
    save(fitted(emblem, (512, 512), 80),
         V2 / 'android/app/src/main/res/drawable-nodpi/brand_icon.png')
    save(fitted(master, (1024, 1024), background='white'), PROMO / 'logo.jpg')
    save(fitted(emblem, (1024, 1024), 128, background='white'), PROMO / 'profile-1024.png')
    # Keep all channel banner content inside the central 1546x423 safe rectangle.
    save(panel(master, (2560, 1440), (610, 535, 370, 370), (1050, 610), 48), PROMO / 'banner.jpg')
    save(fitted(emblem, (512, 512), 64, background='white'), PLAY / 'icon-512.png')
    save(panel(master, (1024, 500), (55, 45, 410, 410), (500, 160), 29).convert('RGB'),
         PLAY / 'feature-1024x500.png')
    provenance = {'version': 1, 'emblem_crop_xyxy': EMBLEM_CROP, 'masters': {}, 'outputs': {}}
    for group, paths in (('masters', (MASTER, EMBLEM)), ('outputs', OUTPUTS)):
        for path in paths:
            provenance[group][path.relative_to(STUDY).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (BRANDING / 'exports.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Exported {len(OUTPUTS)} brand assets. Next: python -m app.shell')


if __name__ == '__main__':
    main()
