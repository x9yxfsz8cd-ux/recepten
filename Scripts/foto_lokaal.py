#!/usr/bin/env python3
"""
Haalt afbeeldingen binnen en zet ze in docs/img/, zodat de site offline werkt.

In de supermarkt heb je vaak geen bereik, en juist daar leunt het winkelscherm
op de productfoto's van Albert Heijn. Die moeten dus mee in de service worker
cache, en dat kan alleen als ze van onze eigen site komen.

Gebruik:
    python3 Scripts/foto_lokaal.py            # producten en recepten
    python3 Scripts/foto_lokaal.py producten  # alleen AH-productfoto's
    python3 Scripts/foto_lokaal.py recepten   # alleen gerechtfoto's
"""

import json
import re
import ssl
import subprocess
import time
import sys
import urllib.request
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
IMG = WORTEL / "docs" / "img"
PRODUCTEN = WORTEL / "docs" / "data" / "ah-producten.json"
RECEPTEN = WORTEL / "docs" / "data" / "recepten.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()


def haal(url, doel, breedte, pogingen=3):
    """Downloadt en verkleint naar JPEG. Geeft False als het niet lukte.

    Beeldservers gaan knijpen als je er honderden achter elkaar opvraagt, dus
    we wachten tussen pogingen in plaats van de afbeelding meteen op te geven.
    """
    tijdelijk = doel.with_suffix(".tmp")
    for poging in range(pogingen):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "image/avif,image/webp,image/apng,*/*",
            })
            with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
                tijdelijk.write_bytes(r.read())
            break
        except Exception:
            tijdelijk.unlink(missing_ok=True)
            if poging == pogingen - 1:
                return False
            time.sleep(2 * (poging + 1))

    # sips zit op elke Mac en slikt AVIF, WebP, PNG en JPEG, maar het loopt vast
    # als je het in een lus op grote afbeeldingen loslaat. Elke poging krijgt
    # daarom zijn eigen kans, en lukt verkleinen niet, dan bewaren we het
    # origineel: een iets te grote foto is beter dan geen foto.
    doel.unlink(missing_ok=True)
    for _ in range(2):
        klaar = subprocess.run(
            ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72",
             "-Z", str(breedte), str(tijdelijk), "--out", str(doel)],
            capture_output=True,
        )
        if klaar.returncode == 0 and doel.exists() and doel.stat().st_size > 0:
            tijdelijk.unlink(missing_ok=True)
            return True
        doel.unlink(missing_ok=True)
        time.sleep(0.5)

    rauw = tijdelijk.read_bytes()
    tijdelijk.unlink(missing_ok=True)
    if rauw[:3] == b"\xff\xd8\xff":          # al JPEG, dan kan hij zo mee
        doel.write_bytes(rauw)
        return True
    return False


def producten():
    map_ = IMG / "ah"
    map_.mkdir(parents=True, exist_ok=True)
    cache = json.loads(PRODUCTEN.read_text(encoding="utf8"))

    gelukt = mislukt = overgeslagen = 0
    for i, (term, p) in enumerate(sorted(cache.items()), 1):
        if not p or not p.get("afbeelding"):
            continue
        if p["afbeelding"].startswith("img/"):
            overgeslagen += 1
            continue

        naam = re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-") + ".jpg"
        doel = map_ / naam
        time.sleep(0.15)
        if haal(p["afbeelding"], doel, 240):
            p["bron_afbeelding"] = p["afbeelding"]     # origineel bewaren
            p["afbeelding"] = f"img/ah/{naam}"
            gelukt += 1
            print(f"  [{i}] {term} -> img/ah/{naam}")
        else:
            mislukt += 1
            print(f"  [{i}] {term}: niet op te halen")

    PRODUCTEN.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf8")
    print(f"\nProducten: {gelukt} lokaal, {mislukt} mislukt, {overgeslagen} al lokaal")


def recepten():
    map_ = IMG / "recept"
    map_.mkdir(parents=True, exist_ok=True)
    data = json.loads(RECEPTEN.read_text(encoding="utf8"))

    gelukt = mislukt = overgeslagen = 0
    for r in data["recepten"]:
        url = (r.get("afbeelding") or "").strip()
        if not url.startswith("http"):
            overgeslagen += 1
            continue
        naam = (r.get("slug") or r["id"]) + ".jpg"
        doel = map_ / naam
        time.sleep(0.4)
        if haal(url, doel, 1000):
            r["bron_afbeelding"] = url
            r["afbeelding"] = f"img/recept/{naam}"
            gelukt += 1
            print(f"  {r['titel'][:44]} -> img/recept/{naam}")
        else:
            mislukt += 1
            print(f"  {r['titel'][:44]}: niet op te halen (blijft extern)")

    RECEPTEN.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf8")
    print(f"\nRecepten: {gelukt} lokaal, {mislukt} mislukt, {overgeslagen} al lokaal")


if __name__ == "__main__":
    wat = sys.argv[1] if len(sys.argv) > 1 else "alles"
    if wat in ("alles", "producten"):
        print("AH-productfoto's ophalen...")
        producten()
    if wat in ("alles", "recepten"):
        print("\nGerechtfoto's ophalen...")
        recepten()
