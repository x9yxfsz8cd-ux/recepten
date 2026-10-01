#!/usr/bin/env python3
"""
Leidt per recept af wat je uit de kast moet halen, en zet dat in het veld
'benodigdheden'. Dat verschijnt bovenaan Bereiding als "Pak alvast".

Alleen gereedschap dat je tevoorschijn moet halen of verbruiksartikelen die op
kunnen zijn. Een koekenpan, een mes en een snijplank staan er bewust niet bij:
die heb je toch wel, en een lijst die alles noemt leest niemand meer.

Woordgrenzen overal. Zonder \b zit 'folie' ook in 'olijfolie', en dan krijgt
driekwart van je recepten aluminiumfolie.
"""
import json
import pathlib
import re

WORTEL = pathlib.Path(__file__).resolve().parent.parent
RECEPTEN = WORTEL / "docs" / "data" / "recepten.json"

REGELS = [
    ("blender",           r"\bblender\b|\bblenden\b"),
    ("staafmixer",        r"\bstaafmixer\b"),
    ("keukenmachine",     r"\bkeukenmachine\b|\bfoodprocessor\b"),
    ("grillpan",          r"\bgrillpan\b|\bgrillplaat\b"),
    ("braadslede",        r"\bbraadslede\b|\bbraadsleden\b"),
    ("bakplaat",          r"\bbakplaat\b|\bbakplaten\b"),
    ("ovenschaal",        r"\bovenschaal\b|\bovenvaste schaal\b"),
    ("bakpapier",         r"\bbakpapier\b"),
    ("aluminiumfolie",    r"\baluminiumfolie\b|\bzilverpapier\b"),
    ("vijzel",            r"\bvijzel\b|\bvijzelen\b"),
    ("pureestamper",      r"\bstamper\b|\bstamppot\b|stamp.{0,24}\b(aardappel|puree)"),
    ("springvorm",        r"\bspringvorm\b|\btaartvorm\b|\bbakvorm\b"),
    ("pizzasteen",        r"\bpizzasteen\b"),
    ("deegroller",        r"\bdeegroller\b|\brol\b.{0,30}\buit\b|\buitgerold|\buitrollen\b"),
    ("mandoline",         r"\bmandoline\b"),
    ("vergiet",           r"\bvergiet\b"),
    ("schuimspaan",       r"\bschuimspaan\b"),
    ("schone theedoek",   r"\btheedoek\b"),
    ("keukenthermometer", r"\bthermometer\b"),
    ("spiraalsnijder",    r"\bspiraalsnijder\b"),
    ("stoommandje",       r"\bstoommandje\b|\bstoompan\b"),
    ("microplane",        r"\bmicroplane\b"),
]
# 'pureer' zonder dat er een apparaat bij staat: dan heb je er toch een nodig
PUREER = re.compile(r"\bpureer\b|\bpureren\b")
MIXERS = {"blender", "staafmixer", "keukenmachine"}


def voor(recept):
    tekst = " ".join(s["tekst"] for s in recept["stappen"]).lower()
    tekst += " " + " ".join(i["naam"] for i in recept["ingredienten"]).lower()

    uit = [naam for naam, patroon in REGELS if re.search(patroon, tekst)]

    # Staat er allebei, dan noemt het recept ze als alternatief
    if {"blender", "staafmixer"} <= set(uit):
        uit = [x for x in uit if x not in ("blender", "staafmixer")]
        uit.insert(0, "blender of staafmixer")
    elif PUREER.search(tekst) and not MIXERS & set(uit):
        uit.append("staafmixer of blender")
    return uit


def main():
    data = json.loads(RECEPTEN.read_text())
    lijst = data if isinstance(data, list) else data["recepten"]

    gewijzigd = 0
    for r in lijst:
        nieuw = voor(r)
        if nieuw != r.get("benodigdheden", []):
            r["benodigdheden"] = nieuw
            gewijzigd += 1
        if nieuw:
            print(f"  {r['titel'][:46]:48} {', '.join(nieuw)}")

    RECEPTEN.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf8")
    met = sum(1 for r in lijst if r.get("benodigdheden"))
    print(f"\n{met} van {len(lijst)} recepten hebben benodigdheden, "
          f"{gewijzigd} gewijzigd.")


if __name__ == "__main__":
    main()
