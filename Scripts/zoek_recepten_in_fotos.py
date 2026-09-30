#!/usr/bin/env python3
"""
Zoekt recepten tussen je foto's, zonder dat er ook maar één foto je Mac verlaat.

Hoe het werkt:
  1. Scripts/ocr leest de tekst uit elke foto met Apple's Vision-framework,
     volledig lokaal.
  2. Die tekst wordt hier ter plekke beoordeeld op receptkenmerken.
  3. Alleen een overzicht met bestandsnamen en scores komt op het scherm.
     De tekst zelf blijft in een bestand op deze Mac staan.

Zo kan er daarna gericht gekeken worden naar alleen de treffers, in plaats van
naar alles wat je ooit hebt gefotografeerd.

Gebruik:
    python3 Scripts/zoek_recepten_in_fotos.py <map> [--toon]

    --toon  laat ook de eerste regels van elke treffer zien
"""

import json
import re
import subprocess
import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
OCR = WORTEL / "Scripts" / "ocr"
RAPPORT = WORTEL / "Scripts" / "fotoscan.json"

AFBEELDINGEN = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tiff", ".webp"}

# Woorden die op een recept wijzen. Maten en werkwoorden wegen zwaar, want die
# komen zelden voor op een kiekje van een terras of een hond.
MATEN = r"\b\d+\s?(g|gram|kg|ml|cl|l|el|tl|eetlepel|theelepel|snuf|stuks?|teen|takjes?)\b"
KOOKWOORDEN = [
    "ingrediënt", "ingredient", "bereiding", "bereidingstijd", "voorbereiding",
    "porties", "personen", "voor:", "oven", "bakken", "koken", "roerbak",
    "snijd", "snij ", "hak ", "meng ", "roer ", "verhit", "verwarm de oven",
    "laat sudderen", "breng aan de kook", "op smaak", "zout en peper",
    "eetlepel", "theelepel", "minuten", "graden", "°c", "afgieten", "pureer",
]
# Deze wijzen juist op iets anders: een bon, een etiket, een schermafbeelding
TEGENWOORDEN = ["totaal te betalen", "btw", "kassabon", "iban", "factuur",
                "houdbaar tot", "voedingswaarde per 100", "app store"]


def ocr(pad: Path) -> str:
    try:
        uit = subprocess.run([str(OCR), str(pad)], capture_output=True,
                             text=True, timeout=60)
        return uit.stdout if uit.returncode == 0 else ""
    except Exception:
        return ""


def beoordeel(tekst: str):
    """Geeft een score en welke kenmerken gevonden zijn."""
    t = tekst.lower()
    if len(t) < 60:
        return 0, []

    kenmerken = []
    punten = 0

    maten = re.findall(MATEN, t)
    if maten:
        punten += min(len(maten) * 6, 36)
        kenmerken.append(f"{len(maten)} maataanduidingen")

    geraakt = [w for w in KOOKWOORDEN if w in t]
    punten += min(len(geraakt) * 5, 40)
    if geraakt:
        kenmerken.append(f"{len(geraakt)} kookwoorden")

    # Een ingrediëntenlijst staat vaak als korte regels onder elkaar
    regels = [r for r in tekst.splitlines() if r.strip()]
    kort = [r for r in regels if 3 < len(r.strip()) < 44]
    if len(regels) > 8 and len(kort) / max(len(regels), 1) > 0.55:
        punten += 14
        kenmerken.append("lijstachtige opmaak")

    for tegen in TEGENWOORDEN:
        if tegen in t:
            punten -= 30
            kenmerken.append(f"lijkt op {tegen}")
            break

    return max(punten, 0), kenmerken


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    if not OCR.exists():
        print("Scripts/ocr ontbreekt. Bouw hem eerst:")
        print("   swiftc -O Scripts/ocr.swift -o Scripts/ocr")
        sys.exit(1)

    map_ = Path(sys.argv[1]).expanduser()
    toon = "--toon" in sys.argv

    bestanden = sorted(p for p in map_.rglob("*")
                       if p.is_file() and p.suffix.lower() in AFBEELDINGEN)
    print(f"{len(bestanden)} afbeeldingen in {map_}\n")

    treffers, bekeken = [], 0
    for p in bestanden:
        bekeken += 1
        if bekeken % 25 == 0:
            print(f"  ... {bekeken}/{len(bestanden)}", flush=True)
        tekst = ocr(p)
        score, kenmerken = beoordeel(tekst)
        if score >= 40:
            treffers.append({"bestand": str(p), "score": score,
                             "kenmerken": kenmerken, "tekst": tekst})

    treffers.sort(key=lambda x: -x["score"])
    RAPPORT.write_text(json.dumps(treffers, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf8")

    print(f"\n{len(treffers)} mogelijke recepten van {len(bestanden)} foto's:\n")
    for t in treffers:
        naam = Path(t["bestand"]).name
        print(f"  [{t['score']:3}] {naam}   {', '.join(t['kenmerken'])}")
        if toon:
            eerste = [r for r in t["tekst"].splitlines() if r.strip()][:3]
            for r in eerste:
                print(f"         {r[:72]}")
    print(f"\nVolledige tekst staat in {RAPPORT.relative_to(WORTEL)} — die blijft op deze Mac.")


if __name__ == "__main__":
    main()
