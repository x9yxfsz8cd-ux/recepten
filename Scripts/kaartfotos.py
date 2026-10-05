#!/usr/bin/env python3
"""
Maakt kleine versies van de receptfoto's voor het overzicht.

Een kaartje is op een telefoon ongeveer 171 px breed. De grote foto is 1400 px.
Dat is acht keer zo veel pixels als er op het scherm passen, en je laadt het
over mobiel internet. 640 px is ruim genoeg, ook op een scherm met drievoudige
pixeldichtheid, en scheelt ruim zeventig procent.

De grote foto blijft staan: die is voor de receptpagina zelf.

    python3 Scripts/kaartfotos.py
"""
import json
import pathlib

from PIL import Image, ImageOps

WORTEL = pathlib.Path(__file__).resolve().parent.parent
RECEPTEN = WORTEL / "docs" / "data" / "recepten.json"
GROOT = WORTEL / "docs" / "img" / "recept"
KLEIN = WORTEL / "docs" / "img" / "kaart"
BREEDTE = 640


def main():
    KLEIN.mkdir(parents=True, exist_ok=True)
    data = json.loads(RECEPTEN.read_text())
    lijst = data if isinstance(data, list) else data["recepten"]

    gemaakt = overgeslagen = 0
    bespaard = 0
    gebruikt = set()
    for r in lijst:
        a = r.get("afbeelding", "")
        if not a or a.startswith("http"):
            continue
        bron = WORTEL / "docs" / a
        if not bron.exists():
            continue
        doel = KLEIN / bron.name
        gebruikt.add(bron.name)
        if doel.exists() and doel.stat().st_mtime >= bron.stat().st_mtime:
            overgeslagen += 1
            continue
        im = ImageOps.exif_transpose(Image.open(bron)).convert("RGB")
        im.thumbnail((BREEDTE, BREEDTE), Image.LANCZOS)
        im.save(doel, "JPEG", quality=80, optimize=True)
        bespaard += bron.stat().st_size - doel.stat().st_size
        gemaakt += 1

    # kaartfoto's van verwijderde recepten opruimen
    weg = 0
    for p in KLEIN.iterdir():
        if p.is_file() and p.name not in gebruikt:
            p.unlink()
            weg += 1

    print(f"{gemaakt} gemaakt, {overgeslagen} ongewijzigd, {weg} opgeruimd")
    if bespaard:
        print(f"bespaard: {bespaard // 1024 // 1024} MB")


if __name__ == "__main__":
    main()
