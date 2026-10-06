#!/usr/bin/env python3
"""
Licht elk recept door op de dingen die tijdens het koken misgaan.

Geen smaakoordeel — dat kan een script niet. Wel: staat elk ingrediënt in een
stap, kloppen de hoeveelheden tussen lijst en stappen, loopt de volgorde,
kloppen de tijden, en liegen de tags niet.

    python3 Scripts/doorlicht.py            alle bevindingen
    python3 Scripts/doorlicht.py <zoekterm> alleen die recepten
"""
import json
import pathlib
import re
import sys
import unicodedata

WORTEL = pathlib.Path(__file__).resolve().parent.parent
RECEPTEN = WORTEL / "docs" / "data" / "recepten.json"

# Hetzelfde rijtje als import.html hanteert; anders staat er na een jaar
# 'foto', 'website' en 'url' naast elkaar voor hetzelfde.
SOORTEN = ["url", "kookboek", "tijdschrift", "instagram", "notitie", "klassiek"]

VLEES = ["kip", "rund", "varken", "spek", "pancetta", "gehakt", "worst", "ham",
         "chorizo", "bacon", "lam", "kalkoen", "shoarma", "biefstuk"]
VIS = ["zalm", "tonijn", "ansjovis", "garnaal", "garnalen", "vis", "kabeljauw",
       "makreel", "sardine", "wonton"]
DIERLIJK = ["kaas", "boter", "room", "melk", "yoghurt", "ei", "eieren", "honing",
            "parmigiano", "parmezaan", "pecorino", "mozzarella", "feta", "ricotta",
            "halloumi", "mascarpone", "geitenkaas", "grana", "creme fraiche",
            "crème fraîche", "sour cream", "cheddar", "comté", "burrata"]


def plat(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9 ]", " ", t)


def kernwoorden(naam):
    """De woorden die ertoe doen in een ingrediëntnaam."""
    # Haakjes eerst weg: plat() maakt er spaties van, waardoor de split hieronder
    # niets meer deed en 'ui (geel of rood)' als kernwoorden 'geel' en 'rood'
    # overhield. Die staan natuurlijk in geen enkele stap.
    n = re.sub(r"\(.*?\)", " ", naam).split(",")[0]
    n = plat(n)
    ruis = {"rode", "gele", "groene", "witte", "bruine", "zwarte", "blauwe",
            "paarse", "rood", "geel", "groen", "bruin", "zwart",
            "verse", "vers", "grote", "kleine", "fijngesneden", "gesneden", "gesnipperd",
            "geraspte", "geraspt", "gehakt", "fijngehakt", "biologische",
            "biologisch", "naar", "smaak", "optioneel", "voor", "het", "een",
            "van", "met", "dikke", "dunne", "extra", "vergine", "vierge",
            "goede", "kwaliteit", "stuks", "blokjes", "plakjes", "reepjes",
            "roosjes", "ringetjes", "partjes", "stukjes", "halve", "hele"}
    return [w for w in n.split() if len(w) > 3 and w not in ruis]


# Een stap mag de rest ook als groep noemen: "alle overige ingrediënten".
# Dan valt er over losse ingrediënten niets te zeggen.
SAMEN = re.compile(r"(alle |de |rest van de )?overige ingredi|alle ingredi")

# Het recept noemt de soort, de stap het soortnaam-woord: je koopt linguine,
# maar in stap 3 staat "kook de pasta".
SOORT = {
    "pasta": ["spaghetti", "linguine", "tagliatelle", "penne", "fusilli", "orzo",
              "tonnarelli", "macaroni", "farfalle", "rigatoni", "pappardelle",
              "lasagne", "ravioli", "orecchiette", "gnocchi"],
    "noedel": ["eiernoedels", "snelkooknoedels", "ramen", "udon", "mihoen",
               "wonton", "noedels"],
    "rijst": ["jasmijnrijst", "basmatirijst", "risottorijst", "arborio", "sushirijst"],
    "ei": ["scharreleieren", "eieren", "eierdooiers"],
    "zalm": ["sushizalm", "zalmfilets"],
    "paddenstoel": ["portobello", "champignon", "shiitake", "oesterzwam",
                    "cantharel", "eekhoorntjesbrood"],
}


def haakjeswoorden(naam):
    """Woorden tussen haakjes. Bij 'queen butter beans (of andere witte bonen)'
    staat het woord dat de stap gebruikt juist daar."""
    uit = []
    for stuk in re.findall(r"\((.*?)\)", naam):
        uit += [w for w in plat(stuk).split() if len(w) > 3]
    return uit


def getallen_en_meervoud(w):
    """Enkelvoud en meervoud met open lettergreep: 'tomaten' hoort bij een stap
    over 'tomaat', en 'bospenen' bij 'bospeen'."""
    uit = set()
    if w.endswith("en") and len(w) > 4:
        stam = w[:-2]
        uit.add(stam)
        if len(stam) > 2 and stam[-1] not in "aeiou" and stam[-2] in "aeiou":
            uit.add(stam[:-1] + stam[-2] + stam[-1])
    for dubbel in ("aa", "ee", "oo", "uu"):
        if dubbel in w:
            uit.add(w.replace(dubbel, dubbel[0]) + "en")
    return {x for x in uit if len(x) > 3}


def controleer(r):
    """Geeft een lijst (ernst, tekst) terug. ernst: 'fout' of 'let op'."""
    uit = []
    stapt = " ".join(s["tekst"] for s in r["stappen"])
    sp = plat(stapt)
    namen = [i["naam"] for i in r["ingredienten"]]

    # 1. Ingrediënt dat nergens in een stap voorkomt
    #
    # Alleen zinvol als de stappen de ingrediënten ook echt bij naam noemen.
    # Zegt er één "en alle overige ingrediënten", dan is elk los ingrediënt
    # gedekt en valt er niets te controleren.
    if not SAMEN.search(sp):
        for i in r["ingredienten"]:
            ws = kernwoorden(i["naam"])
            if not ws:
                continue
            kandidaten = set(haakjeswoorden(i["naam"]))
            for w in ws:
                kandidaten.add(w[:6])
                kandidaten |= getallen_en_meervoud(w)
                # Een samenstelling mag ook op zijn staart gevonden worden: een
                # stap die 'doperwten' zegt dekt 'diepvriesdoperwten', en
                # 'eieren' dekt 'scharreleieren'. Vanaf vijf letters, want
                # korter levert toevalstreffers op.
                for k in range(1, len(w) - 4):
                    kandidaten.add(w[k:])
                # Korte staarten kunnen dat niet zelf, dus die staan er los bij:
                # 'zeezout' hoort bij een stap over zout, 'sesamolie' bij olie.
                for staart in ("bouillon", "champignon", "tomaat", "tomaten",
                               "peterselie", "aardappel", "ui", "olie", "azijn",
                               "kaas", "noten", "rijst", "zout", "peper",
                               "broodje", "brood", "suiker", "melk", "room", "meel"):
                    if staart in w and len(w) > len(staart):
                        kandidaten.add(staart[:6])
                # En de soortnaam: 'linguine' hoort bij een stap over 'pasta'.
                for generiek, soorten in SOORT.items():
                    if any(so in w for so in soorten):
                        kandidaten.add(generiek)
            if not any(k in sp for k in kandidaten):
                uit.append(("let op", f"'{i['naam']}' komt in geen enkele stap voor"))

    # 2. Oven gebruikt zonder voorverwarmen
    if re.search(r"\bin de oven\b|\bovenschaal\b|\bbraadslede\b", sp) \
            and not re.search(r"kort.{0,40}oven|oven.{0,30}magnetron|magnetron", sp):
        if not re.search(r"verwarm de (oven|grill)|oven voor|zet de oven op|oven aan op|oven op \d", sp):
            uit.append(("fout", "de oven wordt gebruikt maar nergens voorverwarmd"))

    # 3. Voorverwarmen hoort in stap 1 te staan
    for n, s in enumerate(r["stappen"], 1):
        if re.search(r"verwarm de oven", plat(s["tekst"])) and n > 2:
            uit.append(("let op", f"de oven wordt pas in stap {n} voorverwarmd"))

    # 4. 'de rest van X' zonder dat eerder een deel is gebruikt
    for n, s in enumerate(r["stappen"], 1):
        m = re.search(r"\b(de rest van de|resterende|overgebleven)\s+([a-zà-ÿ]+)", plat(s["tekst"]))
        if m:
            eerder = " ".join(plat(x["tekst"]) for x in r["stappen"][:n-1])
            if m.group(2)[:6] not in eerder:
                uit.append(("let op", f"stap {n} noemt '{m.group(0)}' maar dat is nog niet eerder gebruikt"))

    # 5. Pastawater bewaren
    if re.search(r"pastawater|kookwater|kookvocht", sp):
        if not re.search(r"bewaar|reserveer|achterblijft|apart|\bweg\b|houd.{0,20}achter|giet.{0,24}losjes|schep.{0,60}kookwater|kopje.{0,20}(kookwater|pastawater)", sp):
            uit.append(("fout", "er wordt kookwater gebruikt maar nergens apart gehouden"))

    # 6. Tags tegen de ingrediënten
    tags = [t.lower() for t in r.get("tags", [])]

    def bevat(lijst):
        """Alleen hele woorden, en 'plantaardige spekjes' telt niet als spek.
        Zonder dit vindt hij vlees in 'gehakte peterselie', 'hamburgerbol'
        en 'granaatappel'."""
        raak = []
        for naam in namen:
            n = plat(naam)
            plantaardig = re.search(r"\bvegan\b|\bvega\b|\bvegetarisch|\bplantaardig", n)
            eerste = (kernwoorden(naam) or [""])[0]
            for w in lijst:
                # 'gehakt' is meestal een deelwoord ('peterselie gehakt').
                # Als vlees staat het vooraan, niet achter een ander woord.
                if w == "gehakt" and eerste != "gehakt":
                    continue
                if re.search(rf"\b{w}(s|e|en|je|jes)?\b", n) and not plantaardig:
                    raak.append(f"{w} (in '{naam}')")
        return raak
    if "vegetarisch" in tags:
        for w in bevat(VLEES) + bevat(VIS):
            uit.append(("fout", f"tag 'vegetarisch' maar bevat {w}"))
    if "vegan" in tags:
        for w in bevat(VLEES) + bevat(VIS) + bevat(DIERLIJK):
            if w in ("ei",) and not re.search(r"\bei\b|\beieren\b", alles):
                continue
            uit.append(("fout", f"tag 'vegan' maar bevat {w}"))

    # 7. Tijden
    a, p, b = r.get("actieve_tijd"), r.get("passieve_tijd"), r.get("bereidingstijd")
    if a is not None and p is not None and b and a + p != b:
        uit.append(("fout", f"actief {a} + passief {p} is niet {b}"))
    oventijden = [int(x) for x in re.findall(r"(\d{1,3})\s*minuten in de oven", sp)]
    if oventijden and p is not None and max(oventijden) > p:
        uit.append(("let op", f"een stap noemt {max(oventijden)} min oven, passieve tijd is {p}"))

    # 8. Hoeveelheden tussen lijst en stap
    for i in r["ingredienten"]:
        if i["eenheid"] not in ("el", "tl") or not i["hoeveelheid"]:
            continue
        ws = kernwoorden(i["naam"])
        if not ws:
            continue
        kern = ws[0][:6]
        ruw = stapt.lower()
        for m in re.finditer(rf"(?<![\d/])(\d+(?:[.,]\d+)?)(?!\s*/)\s*(el|tl|eetlepels?|theelepels?)\s+(?:\w+\s+){{0,2}}{kern}", ruw):
            genoemd = float(m.group(1).replace(",", "."))
            if genoemd > i["hoeveelheid"]:
                uit.append(("fout", f"stap noemt {m.group(0)} maar de lijst heeft "
                                    f"{i['hoeveelheid']} {i['eenheid']} {i['naam']}"))

    # 9. Zout en peper wel in de lijst, nooit in een stap
    heeft_zout = any(re.search(r"\bzout\b|\bpeper\b", plat(n)) for n in namen)
    if heeft_zout and not re.search(r"\bzout\b|\bpeper\b|op smaak", sp):
        uit.append(("let op", "zout/peper staat in de lijst maar wordt nergens toegevoegd"))

    # 10. Stappen zonder werkwoord aan het begin lezen als een notitie
    for n, s in enumerate(r["stappen"], 1):
        if len(s["tekst"]) < 30:
            uit.append(("let op", f"stap {n} is erg kort: \"{s['tekst']}\""))

    # 11. Porties en hoeveelheden
    if not r.get("porties"):
        uit.append(("fout", "geen aantal porties"))
    for i in r["ingredienten"]:
        if i["hoeveelheid"] and i["eenheid"] == "naar smaak":
            uit.append(("let op", f"'{i['naam']}' heeft hoeveelheid {i['hoeveelheid']} én eenheid 'naar smaak'"))

    # 12. Foto's. Het overzicht maakt van img/recept/x.jpg zelf img/kaart/x.jpg;
    #     staat een foto ergens anders, dan laadt een kaartje stil de volle
    #     1400 px. Vier recepten stonden zo los in img/ zonder dat iets het liet
    #     zien, dus dit hoort een controle te zijn en geen oplettendheid.
    afb = r.get("afbeelding") or ""
    if not afb:
        uit.append(("let op", "geen afbeelding"))
    elif afb.startswith("http"):
        uit.append(("let op", f"foto staat op een andere site, werkt niet offline: {afb}"))
    elif not afb.startswith("img/recept/"):
        uit.append(("fout", f"foto hoort in img/recept/ te staan, niet in {afb.rsplit('/', 1)[0]}/"))
    else:
        if not (WORTEL / "docs" / afb).exists():
            uit.append(("fout", f"afbeelding bestaat niet: {afb}"))
        klein = afb.replace("img/recept/", "img/kaart/")
        if not (WORTEL / "docs" / klein).exists():
            uit.append(("fout", f"kaartfoto ontbreekt, draai Scripts/kaartfotos.py: {klein}"))

    # 13. Bron
    if not r.get("bron_type"):
        uit.append(("fout", "geen bron_type"))
    elif r["bron_type"] not in SOORTEN:
        uit.append(("fout", f"bron_type '{r['bron_type']}' staat niet in het vaste rijtje {'/'.join(SOORTEN)}"))
    if not r.get("bron_naam"):
        uit.append(("let op", "geen bron_naam"))

    # 14. AH-koppeling, want zonder sleutel geen productfoto en geen regel in
    #     de boodschappenlijst met de juiste naam.
    for i in r["ingredienten"]:
        if "ah" not in i:
            uit.append(("let op", f"'{i['naam']}' is niet aan een AH-product gekoppeld"))
    return uit


def main():
    data = json.loads(RECEPTEN.read_text())
    lijst = data if isinstance(data, list) else data["recepten"]
    filt = sys.argv[1].lower() if len(sys.argv) > 1 else None

    totaal_fout = totaal_let = schoon = 0
    for r in sorted(lijst, key=lambda x: x["titel"]):
        if filt and filt not in r["titel"].lower():
            continue
        bev = controleer(r)
        fouten = [b for b in bev if b[0] == "fout"]
        letop = [b for b in bev if b[0] == "let op"]
        totaal_fout += len(fouten)
        totaal_let += len(letop)
        if not bev:
            schoon += 1
            continue
        print(f"\n### {r['titel']}  ({r['porties']} porties, {r['bereidingstijd']} min)")
        for _, t in fouten:
            print(f"   FOUT    {t}")
        for _, t in letop:
            print(f"   let op  {t}")

    print(f"\n{'='*70}")
    print(f"{totaal_fout} fouten, {totaal_let} aandachtspunten, {schoon} recepten schoon")


if __name__ == "__main__":
    main()
