"""Compare deux séries de `captures.py` (docs/135 §7) : pour chaque capture qui a changé, une image
avant | après | différences (les pixels changés en rouge sur l'image d'avant, pâlie), et le
compte des pixels changés. Une capture identique au pixel près n'écrit rien.

    uv run --with pillow python frontend/scripts/compare.py /chemin/avant /chemin/apres /chemin/diff
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

GAP = 24


def compare(before: Path, after: Path, out: Path) -> dict[str, int]:
    out.mkdir(parents=True, exist_ok=True)
    changed: dict[str, int] = {}
    for a in sorted(before.glob("*.png")):
        b = after / a.name
        if not b.exists():
            changed[a.name] = -1
            continue
        ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        width, height = max(ia.width, ib.width), max(ia.height, ib.height)
        pa = Image.new("RGB", (width, height), "white")
        pb = Image.new("RGB", (width, height), "white")
        pa.paste(ia)
        pb.paste(ib)
        mask = ImageChops.difference(pa, pb).convert("L").point(lambda v: 255 if v > 0 else 0)
        pixels = sum(1 for v in mask.get_flattened_data() if v)
        if not pixels:
            continue
        changed[a.name] = pixels
        faded = Image.blend(pa, Image.new("RGB", pa.size, "white"), 0.7)
        faded.paste(Image.new("RGB", pa.size, (230, 30, 30)), mask=mask)
        sheet = Image.new("RGB", (width * 3 + GAP * 2, height), (200, 200, 210))
        for i, image in enumerate([pa, pb, faded]):
            sheet.paste(image, (i * (width + GAP), 0))
        sheet.save(out / a.name)
    for b in sorted(after.glob("*.png")):
        if not (before / b.name).exists():
            changed[b.name] = -2
    return changed


def main() -> int:
    before, after, out = (Path(p) for p in sys.argv[1:4])
    changed = compare(before, after, out)
    total = len(list(before.glob("*.png")))
    for name, pixels in changed.items():
        state = {-1: "absente après", -2: "absente avant"}.get(pixels, f"{pixels} pixels")
        print(f"{name}  {state}")
    print(json.dumps({"captures": total, "changées": len(changed)}, ensure_ascii=False))
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
