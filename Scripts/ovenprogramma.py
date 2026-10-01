#!/usr/bin/env python3
"""
Zet per recept een advies voor het ovenprogramma in het veld 'ovenprogramma'.

Afgestemd op de AEG 9000 SteamPro (BSK792280B). De functienamen hieronder staan
zo op die oven. Het is een aanbeveling op basis van wat het gerecht nodig heeft,
niet iets wat in het recept zelf staat — vandaar dat het in de app apart staat
en niet in een bereidingsstap.

Woordgrenzen overal: zonder \b zit 'koek' in 'koekenpan' en 'rijzen' in
'zelfrijzend bakmeel', en dan krijgt een pitabroodje een taartprogramma.
"""
import json
import pathlib
import re

WORTEL = pathlib.Path(__file__).resolve().parent.parent
RECEPTEN = WORTEL / "docs" / "data" / "recepten.json"


def advies(r):
    t = " ".join(s["tekst"] for s in r["stappen"]).lower()
    ing = " ".join(i["naam"] for i in r["ingredienten"]).lower()
    zonder_pan = re.sub(r"grillpan\w*", " ", t)
    gebruikt_oven = re.search(r"\boven\b|\bovenschaal\b|\bbraadslede\b|\bbakplaat\b|\bgrill\w*\b", zonder_pan)
    if not gebruikt_oven:
        return None

    # Grillen vraagt stralingswarmte van boven; turbogrill blaast die rond
    # zodat een volle plaat gelijkmatig kleurt.
    if re.search(r"\bonder de grill\b|\bgrill voor\b|\bgrillplaat\b", t):
        return "Turbogrill op de hoogste stand. Houd hem in de gaten, dit gaat snel."

    # Gistdeeg: de oven heeft een stand om te laten rijzen, en de
    # pizza-instelling geeft extra onderwarmte voor een krokante bodem.
    if re.search(r"\bgist\b|\bgistdeeg\b", ing + " " + t):
        return ("Laat rijzen met Gistdeeg rijzen; bak daarna op Pizza-instelling "
                "— die geeft extra onderwarmte voor een krokante bodem.")

    # Cake en taart willen rustige warmte van twee kanten, anders rijst de
    # bovenkant dicht voordat het midden gaar is.
    if re.search(r"\bspringvorm\b|\btaart\b|\bkoek\b|\bbeslag\b|\bbakvorm\b", t):
        return ("Boven + onderwarmte. Hetelucht droogt de bovenkant uit voordat "
                "het midden gaar is.")

    # Gegratineerd: de laatste minuten van bovenaf kleuren
    if re.search(r"\bgegratineerd?\b|\bgratin\b|kaas.{0,30}goudbruin|\bbubbelend\b"
                 r"|(mozzarella|kaas)\w*\s+(is\s+)?gesmolten|smelt", t):
        return ("Hetelucht, en de laatste 5-10 minuten Turbogrill voor de kaaskorst.")

    # Vis in een pakketje: stoom houdt hem zacht, de folie kan dan weg
    if re.search(r"\bzilverpapier\b|\baluminiumfolie\b", t) and re.search(r"\bzalm\b|\bvis\b", ing):
        return ("Hetelucht in de folie, of Steamify op dezelfde temperatuur zonder "
                "folie — dat houdt de zalm zachter.")

    # Brood opwarmen zonder uit te drogen: daar is Regenereren voor
    if re.search(r"verwarm de \w*\s?(pita|flatbread|brood)", t):
        return "Regenereren met stoom houdt het brood zacht in plaats van droog."

    return "Hetelucht. Zet de plaat in het midden."


def main():
    data = json.loads(RECEPTEN.read_text())
    lijst = data if isinstance(data, list) else data["recepten"]
    n = 0
    for r in lijst:
        a = advies(r)
        if a:
            r["ovenprogramma"] = a
            n += 1
            print(f"  {r['titel'][:40]:42} {a[:62]}")
        elif "ovenprogramma" in r:
            del r["ovenprogramma"]
    RECEPTEN.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf8")
    print(f"\n{n} van de {len(lijst)} recepten hebben een ovenadvies.")


if __name__ == "__main__":
    main()
