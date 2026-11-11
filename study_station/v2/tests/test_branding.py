"""Keep shipped brand surfaces tied to the approved artwork, without stale exports."""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

V2 = Path(__file__).resolve().parents[1]
STUDY = V2.parent
BRANDING = V2 / 'design' / 'branding'


def test_brand_exports_match_recorded_source_and_ship_all_active_surfaces():
    record = json.loads((BRANDING / 'exports.json').read_text(encoding='utf-8'))
    for group in ('masters', 'outputs'):
        for relative, expected in record[group].items():
            assert hashlib.sha256((STUDY / relative).read_bytes()).hexdigest() == expected, relative
    assert len(record['outputs']) == 11
    assert not (BRANDING / 'study-station-3d-master.png').exists()
    with Image.open(BRANDING / 'studystation-multicolor-master.png') as master:
        with Image.open(BRANDING / 'studystation-emblem-crop.png') as emblem:
            assert master.convert('RGBA').crop(record['emblem_crop_xyxy']).tobytes() == emblem.tobytes()


def test_play_listing_assets_have_required_sizes_and_formats():
    with Image.open(BRANDING / 'play-store' / 'icon-512.png') as icon:
        assert icon.size == (512, 512) and icon.mode == 'RGBA'
        assert icon.getchannel('A').getextrema() == (255, 255)
        assert (BRANDING / 'play-store' / 'icon-512.png').stat().st_size <= 1024 * 1024
    with Image.open(BRANDING / 'play-store' / 'feature-1024x500.png') as feature:
        assert feature.size == (1024, 500) and feature.mode == 'RGB'


def test_android_emblem_fits_adaptive_icon_safe_circle():
    # Existing 18dp insets map the image to a 72dp layer inside the 108dp icon.
    # White source-paper pixels match the white launcher background; test actual ink.
    with Image.open(V2 / 'android/app/src/main/res/drawable-nodpi/brand_icon.png') as image:
        rgb = image.convert('RGB')
        radii = [math.hypot(x - 255.5, y - 255.5) * 72 / 512
                 for y in range(512) for x in range(512) if min(rgb.getpixel((x, y))) < 230]
        assert radii and max(radii) <= 33
