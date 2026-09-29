#!/usr/bin/env python3
"""
Legt elk recept in recepten.json naast zijn originele bron.

De meeste receptsites zetten hun recept als JSON-LD in de pagina. Dat lezen we
uit en vergelijken we met wat wij hebben opgeslagen: aantal porties, aantal
ingrediënten, aantal stappen, en welke ingrediënten aan één kant wel en aan de
andere kant niet voorkomen.

Het oordeel blijft mensenwerk — dit script wijst alleen aan wáár het afwijkt.

Gebruik:
    python3 Scripts/controleer_bronnen.py            # alles wat een bron heeft
    python3 Scripts/controleer_bronnen.py <zoekterm> # alleen passende titels
"""

import json
import re
import ssl
import sys
import unicodedata
import urllib.request
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
RECEPTEN = WORTEL / "docs" / "data" / "recepten.json"
UITVOER = WORTEL / "Scripts" / "bronvergelijking.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()


def haal(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        rauw = r.read()
    try:
        return rauw.decode("utf8")
    except UnicodeDecodeError:
        return rauw.decode("latin-1", "replace")


def json_ld_recepten(html):
    """Alle JSON-LD blokken die een Recipe beschrijven."""
    gevonden = []
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I,
    ):
        tekst = m.group(1).strip()
        try:
            data = json.loads(tekst)
        except json.JSONDecodeError:
            continue
        stapel = [data]
        while stapel:
            knoop = stapel.pop()
            if isinstance(knoop, list):
                stapel.extend(knoop)
            elif isinstance(knoop, dict):
                if "@graph" in knoop:
                    stapel.extend(knoop["@graph"] if isinstance(knoop["@graph"], list)
                                  else [knoop["@graph"]])
                soort = knoop.get("@type")
                soorten = soort if isinstance(soort, list) else [soort]
                if "Recipe" in soorten:
                    gevonden.append(knoop)
    return gevonden


def platte_stappen(instructies):
    """recipeInstructions komt in allerlei vormen; maak er platte regels van."""
    regels = []
    stapel = [instructies]
    while stapel:
        k = stapel.pop(0)
        if isinstance(k, str):
            schoon = re.sub(r"<[^>]+>", " ", k)
            schoon = re.sub(r"\s+", " ", schoon).strip()
            if schoon:
                regels.append(schoon)
        elif isinstance(k, list):
            stapel = list(k) + stapel
        elif isinstance(k, dict):
            if k.get("@type") == "HowToSection" and "itemListElement" in k:
                stapel = list(k["itemListElement"]) + stapel
            else:
                for sleutel in ("text", "name", "description"):
                    if k.get(sleutel):
                        stapel.insert(0, k[sleutel])
                        break
    return regels


def afbeelding_van(recept):
    img = recept.get("image")
    while isinstance(img, list) and img:
        img = img[0]
    if isinstance(img, dict):
        img = img.get("url") or img.get("contentUrl")
    return img if isinstance(img, str) else None


def porties_van(recept):
    y = recept.get("recipeYield")
    while isinstance(y, list) and y:
        y = y[0]
    if isinstance(y, (int, float)):
        return int(y)
    if isinstance(y, str):
        m = re.search(r"\d+", y)
        if m:
            return int(m.group())
    return None


def kern(tekst):
    """Woordenzak van een ingrediëntregel, zonder hoeveelheden en eenheden."""
    t = unicodedata.normalize("NFD", tekst.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z\s]", " ", t)
    stop = {"gram", "el", "tl", "ml", "eetlepel", "eetlepels", "theelepel",
            "theelepels", "stuks", "stuk", "van", "de", "het", "een", "in",
            "met", "voor", "naar", "smaak", "gesneden", "fijn", "grof", "ca",
            "liter", "blik", "pak", "zak", "bosje", "teentjes", "teentje",
            "snufje", "scheutje", "verse", "vers", "kleine", "grote"}
    return {w for w in t.split() if len(w) > 3 and w not in stop}


def vergelijk(ons, bron):
    onze_woorden = [kern(i["naam"]) for i in ons["ingredienten"]]
    bron_regels = bron.get("recipeIngredient") or []
    bron_woorden = [kern(x) for x in bron_regels]

    def gedekt(woorden, andere):
        if not woorden:
            return True
        return any(woorden & b for b in andere)

    alleen_bij_ons = [ons["ingredienten"][i]["naam"]
                      for i, w in enumerate(onze_woorden)
                      if not gedekt(w, bron_woorden)]
    alleen_in_bron = [bron_regels[i]
                      for i, w in enumerate(bron_woorden)
                      if not gedekt(w, onze_woorden)]

    return {
        "titel": ons["titel"],
        "bron": ons.get("bron"),
        "bron_titel": bron.get("name"),
        "porties_ons": ons.get("porties"),
        "porties_bron": porties_van(bron),
        "ingredienten_ons": len(ons["ingredienten"]),
        "ingredienten_bron": len(bron_regels),
        "stappen_ons": len(ons["stappen"]),
        "stappen_bron": len(platte_stappen(bron.get("recipeInstructions"))),
        "afbeelding_ons": ons.get("afbeelding"),
        "afbeelding_bron": afbeelding_van(bron),
        "alleen_bij_ons": alleen_bij_ons,
        "alleen_in_bron": alleen_in_bron,
        "bron_stappen": platte_stappen(bron.get("recipeInstructions")),
        "bron_ingredienten": bron_regels,
    }


def main():
    filter_term = sys.argv[1].lower() if len(sys.argv) > 1 else None
    data = json.loads(RECEPTEN.read_text(encoding="utf8"))

    resultaten, problemen = [], []
    for r in data["recepten"]:
        if not r.get("bron"):
            continue
        if filter_term and filter_term not in r["titel"].lower():
            continue
        try:
            html = haal(r["bron"])
        except Exception as e:
            problemen.append({"titel": r["titel"], "bron": r["bron"],
                              "reden": f"niet op te halen: {e}"})
            print(f"  !  {r['titel'][:46]:48} niet op te halen ({e})")
            continue

        recepten_ld = json_ld_recepten(html)
        if not recepten_ld:
            problemen.append({"titel": r["titel"], "bron": r["bron"],
                              "reden": "geen JSON-LD recept op de pagina"})
            print(f"  ?  {r['titel'][:46]:48} geen JSON-LD op de pagina")
            continue

        v = vergelijk(r, recepten_ld[0])
        resultaten.append(v)
        vlag = "  "
        if (v["alleen_bij_ons"] or v["alleen_in_bron"]
                or (v["porties_bron"] and v["porties_bron"] != v["porties_ons"])):
            vlag = "!!"
        print(f"{vlag} {r['titel'][:46]:48} "
              f"ingr {v['ingredienten_ons']}/{v['ingredienten_bron']}  "
              f"stap {v['stappen_ons']}/{v['stappen_bron']}  "
              f"porties {v['porties_ons']}/{v['porties_bron']}")

    UITVOER.write_text(
        json.dumps({"vergelijkingen": resultaten, "problemen": problemen},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
    )
    print(f"\n{len(resultaten)} vergeleken, {len(problemen)} niet te controleren")
    print(f"Details: {UITVOER.relative_to(WORTEL)}")


if __name__ == "__main__":
    main()
