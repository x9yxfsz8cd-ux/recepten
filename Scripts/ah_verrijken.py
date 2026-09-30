#!/usr/bin/env python3
"""
Koppelt ingrediënten uit recepten.json aan producten van Albert Heijn.

Schrijft docs/data/ah-producten.json: een lookup van genormaliseerde
ingrediëntnaam -> AH-product (titel, afbeelding, eenheid, prijs, link).
Zet daarnaast op elk ingrediënt een veld "ah" met de sleutel naar die lookup.

De website gebruikt dit voor productfoto's bij de ingrediënten en voor de
boodschappenlijst. De AH-API is niet officieel en stuurt geen CORS-headers,
dus dit moet hier gebeuren en niet in de browser: de data wordt ingebakken.

Gebruik:
    python3 Scripts/ah_verrijken.py            # alleen nieuwe ingrediënten
    python3 Scripts/ah_verrijken.py --opnieuw  # alles opnieuw opzoeken
"""

import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
RECEPTEN = WORTEL / "docs" / "data" / "recepten.json"
PRODUCTEN = WORTEL / "docs" / "data" / "ah-producten.json"

API = "https://api.ah.nl"
UA = "Appie/8.22.3"

# Woorden die een bereidingswijze beschrijven, geen product. Alles vanaf het
# eerste van deze woorden valt weg uit de zoekterm.
BEREIDING = {
    "fijngehakt", "gehakt", "kleingehakt", "grofgehakt", "gesnipperd",
    "gesneden", "geraspt", "geplet", "geperst", "geroosterd", "gerooster",
    "verwijderd", "schoongemaakt", "gewassen", "uitgelekt", "afgespoeld",
    "gepeld", "geschild", "ontpit", "in", "naar", "optioneel", "alleen",
    "eventueel",
}

# Woorden die niets toevoegen aan een AH-zoekopdracht. Anders dan BEREIDING
# stoppen deze de regel niet, ze vallen alleen zelf weg: "verse dille" moet
# "dille" worden en niet leeg.
RUIS = {
    "grote", "kleine", "middelgrote", "grof", "fijn", "dunne", "dikke",
    "halve", "hele", "stuk", "stukje", "blik", "pak", "zak", "bosje", "bol",
    "teentje", "teentjes", "snufje", "scheutje", "handje", "handvol",
    "goede", "kwaliteit", "biologische", "koud", "koude", "warm", "warme",
    "vers", "verse", "extra", "vierge", "vergine", "rijpe", "eetrijpe",
    "van", "met", "om", "te", "het", "de", "een", "bijv", "keuze",
}


# Dingen die je altijd in huis hebt. Ze staan niet op de boodschappenlijst, en
# opzoeken levert vooral rare treffers op ('water' -> tonijn in water).
VOORRAADKAST = {
    "water", "koud water", "lauw water", "kraanwater",
    # Gecombineerde regels ('zout en peper') slaan nooit op één product.
    "zout en peper", "peper en zout", "zout en zwarte peper",
    "zout en gemalen zwarte",
}


def norm(naam: str) -> str:
    """Maakt van een rommelige ingrediëntregel een bruikbare zoekterm."""
    s = naam.lower().strip()
    s = re.sub(r"\(.*?\)", " ", s)          # (30 g), (optioneel)
    s = s.split(",")[0]                      # alles na de komma is bereiding
    s = re.split(r"\bof\b", s)[0]            # "halloumi of oesterzwam" -> halloumi
    s = re.sub(r"[0-9]+([.,][0-9]+)?", " ", s)
    s = re.sub(r"[^a-zà-ÿ\s-]", " ", s)

    woorden = []
    for w in s.split():
        if w in BEREIDING:
            break
        if w in RUIS or len(w) < 2:
            continue
        woorden.append(w)

    # Meervoud laten we staan: de AH-zoekmachine gaat daar zelf goed mee om,
    # terwijl afkappen in het Nederlands te vaak misgaat (citroen -> citro).
    return " ".join(woorden[:4]).strip()


# Termen waar de AH-zoekmachine op zichzelf de verkeerde kant op gaat.
ALIAS = {
    "bloem": "tarwebloem",
    "olie": "zonnebloemolie",
    "boter": "roomboter",
    "yoghurt": "yoghurt naturel",
    "ui": "gele uien",
    "uien": "gele uien",
    "geitenkaas": "zachte geitenkaas",
    "chilipeper vlokken": "chilivlokken",
    "appels": "elstar appels",
    "dragon en peterselie": "dragon",
    "zout": "keukenzout",
    "parmezaan": "parmigiano reggiano",
    "parmezaanse kaas": "parmigiano reggiano",
    "parmigiano geraspte kaas": "parmigiano reggiano",
    "italiaanse harde kaas": "parmigiano reggiano",
    "ei": "eieren",
    "pasta": "penne",
    "platbrood": "flatbread",
    "mini-hamburgerbol": "hamburgerbroodjes",
    "queen butter beans": "witte bonen",
    "sui kau": "wontons",
    "rode pepervlokken": "chilivlokken",
    "witte balsamicoazijn": "balsamicoazijn wit",
    "zeezout vlokken voor garnering": "zeezout vlokken",
    "walnootstukjes": "walnoten",
    "knoflooktenen": "knoflook",
    "preien": "prei",
    "bosuien": "bosui",
    "zoete aardappelen": "zoete aardappel",
    "tros pruimtomaatjes": "pruimtomaten",
    # AH's zoekmachine leidt hier zelf de verkeerde kant op
    "rode uien": "rode ui",
    "vegan yoghurt": "plantaardige yoghurt",
    "stevige tofu": "tofu",
    "splijtkool": "boerenkool",
    "tonnarelli": "spaghetti",
    "zoete aardappels": "oranje zoete aardappel",
    "zwarte peperkorrels": "zwarte peper heel",
    "parmezaanse kaaskorst": "parmigiano reggiano",
    "citroentijm": "tijm",
    "ras el hanout": "verstegen ras el hanout",
    "rode chilipeper": "rode peper",
    # AH's zoekmachine geeft op deze termen niets of alleen verwante onzin terug
    "bladpeterselie": "platte peterselie",
    "hazelnoten": "ongebrande hazelnoten",
    "kerstomaten": "cherrytomaten",
    "cherrytomaatjes": "cherrytomaten",
    "lente-uitjes": "bosui",
    "lente-ui": "bosui",
    "mini-portobello": "portobello",
    "shiitakes": "shiitake",
    "ansjovisfilets": "ansjovis",
    "radijsjes": "radijs",
    "eierdooiers": "eieren",
    "granaatappelpitten": "granaatappel",
    "laurierblaadjes": "laurierblad",
    "salieblaadjes": "salie",
    "geraspte grana padano dop": "grana padano",
    "kastanjechampignonplakjes": "kastanjechampignons",
    "bospenen": "bospeen",
    "jalapenopepers": "jalapeno",
    "groentebouillon": "bouillon groente",
    "kokende groentebouillon": "bouillon groente",
    "zoutarme groentebouillon": "bouillon groente",
    "ravioli": "ravioli verse",
    "tonijn op oliebasis": "tonijn in olijfolie",
    "witte wijn": "droge witte wijn",
    "aubergines": "aubergine",
}


def enkelvoud(term: str) -> str:
    """Grove enkelvoudsvorm van het laatste woord: 'preien' -> 'prei'."""
    woorden = term.split()
    if not woorden:
        return term
    w = woorden[-1]
    for uitgang in ("eren", "en", "s"):
        if w.endswith(uitgang) and len(w) - len(uitgang) >= 3:
            woorden[-1] = w[: -len(uitgang)]
            break
    return " ".join(woorden)


def varianten(term: str):
    """Paren (zoekterm, maatstaf) om te proberen, van meest naar minst specifiek.

    De AH-zoekmachine is gevoelig voor meervoud en voor lange samenstellingen,
    dus we proberen ook het enkelvoud en alleen het kernwoord. Die afgeleiden
    worden beoordeeld tegen de oorspronkelijke term. Een ALIAS is een bewuste
    correctie en is dus zijn eigen maatstaf: anders verliest 'zonnebloemolie'
    het alsnog van een product dat toevallig 'olie' in de titel heeft.
    """
    kandidaten = []
    if term in ALIAS:
        # Een alias is een bewuste correctie; de ruwe term proberen we dan niet
        # meer, anders wint alsnog het product waar die term toevallig in staat.
        kandidaten.append((ALIAS[term], ALIAS[term]))
        return kandidaten
    kandidaten.append((term, term))
    kandidaten.append((enkelvoud(term), term))
    woorden = term.split()
    if len(woorden) > 1:
        kandidaten.append((woorden[-1], term))
        kandidaten.append((enkelvoud(woorden[-1]), term))

    gezien, uniek = set(), []
    for zoekterm, maatstaf in kandidaten:
        zoekterm = zoekterm.strip()
        if zoekterm and zoekterm not in gezien:
            gezien.add(zoekterm)
            uniek.append((zoekterm, maatstaf))
    return uniek


def ontdiakritiseer(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


class AH:
    """Dunne client op de mobiele AH-API."""

    def __init__(self):
        self.token = None

    def _login(self):
        antwoord = self._call(
            "/mobile-auth/v1/auth/token/anonymous",
            data={"clientId": "appie"},
        )
        self.token = antwoord["access_token"]

    def _call(self, pad, data=None):
        kop = {
            "User-Agent": UA,
            "Content-Type": "application/json",
            # Zonder deze header antwoordt de API met een 500.
            "X-Application": "AHWEBSHOP",
        }
        if self.token:
            kop["Authorization"] = "Bearer " + self.token
        body = json.dumps(data).encode() if data is not None else None
        verzoek = urllib.request.Request(API + pad, data=body, headers=kop)
        with urllib.request.urlopen(verzoek, timeout=25) as resp:
            return json.loads(resp.read().decode())

    def zoek(self, term, aantal=10):
        if not self.token:
            self._login()
        pad = (f"/mobile-services/product/search/v2"
               f"?query={urllib.parse.quote(term)}&size={aantal}")
        for poging in range(3):
            try:
                return self._call(pad).get("products", [])
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    self._login()
                    continue
                if e.code in (429, 500, 502, 503):
                    time.sleep(1.5 * (poging + 1))
                    continue
                raise
            except Exception:
                time.sleep(1.5 * (poging + 1))
        return []


# AH deelt producten zelf in categorieën in, en dat is een veel betrouwbaarder
# signaal dan losse woorden in de titel: 'AH Parmezaanse kaas biscuits' valt op
# de titel niet te onderscheiden van kaas, maar staat onder "Borrel, chips,
# snacks". Deze categorieën leveren nooit een kookingrediënt op.
GEEN_INGREDIENT_CATEGORIE = {
    "Borrel, chips, snacks",
    "Koek, snoep, chocolade",
    "Maaltijden, salades",
    "Koken, tafelen, vrije tijd",
    "Huishouden",
    "Drogisterij",
    "Baby en kind",
    "Huisdier",
    "Bloemen, planten",
}


# Woorden achteraan een AH-titel die niets zeggen over wát het product is:
# verpakking, formaat en bijvoeglijke bepalingen.
STAARTRUIS = {
    "pack", "stuks", "stuk", "gram", "kg", "ml", "cl", "liter", "l", "g",
    "kleinverpakking", "grootverpakking", "voordeelverpakking", "familieverpakking",
    "biologisch", "biologische", "traditioneel", "origineel", "naturel",
    "vers", "verse", "mild", "milde", "extra", "light", "zero", "halfvolle",
    "volle", "magere", "ongezouten", "gezouten", "ongebrand", "gebrand",
    "geraspt", "geraspte", "gezeefd", "gesneden", "gewassen", "gekookt",
    "rauw", "rauwe", "fijn", "fijne", "grof", "grove", "groot", "klein",
    "wit", "witte", "bruin", "bruine", "rood", "rode", "groen", "groene",
    "geel", "gele", "zwart", "zwarte", "blauw", "blauwe",
}


def kernwoord(titelwoorden_op_volgorde):
    """Het laatste woord dat zegt wát het product is.

    In het Nederlands draagt het laatste zelfstandig naamwoord de betekenis:
    'parmezaanse kaas biscuits' is een biscuit, niet kaas. Verpakkings- en
    bijvoeglijke woorden achteraan tellen daarbij niet mee.
    """
    for w in reversed(titelwoorden_op_volgorde):
        if w in STAARTRUIS or len(w) <= 2 or re.fullmatch(r"\d+[a-z]*", w):
            continue
        return w
    return None


def plat(s: str) -> str:
    """'AH Risotto rijst' -> 'ahrisottorijst'. Maakt samenstellingen matchbaar."""
    return re.sub(r"[^a-z0-9]", "", ontdiakritiseer(s.lower()))


def score(term, product):
    """Hoe goed past dit product bij de zoekterm? Hoger is beter.

    Werkt op hele woorden, niet op deelstrings: anders matcht 'water' op
    'watermeloen' en 'zout' op 'pretzels zeezout'. Daarnaast wordt alles ook
    plat vergeleken, omdat het Nederlands samenstellingen aan elkaar plakt
    ('risottorijst') waar AH ze los schrijft ('Risotto rijst').
    """
    rauwe_titel = product.get("title") or ""
    titel = ontdiakritiseer(rauwe_titel.lower())
    t = ontdiakritiseer(term.lower())

    titelwoorden = set(re.findall(r"[a-z0-9]+", titel))
    termwoorden = [w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 1]
    if not termwoorden:
        return -999

    # Zonder merknaam vooraan vergelijkt het eerlijker
    kaal = re.sub(r"^(ah|ah biologisch|ah terra|ah excellent)\s+", "", titel)

    plat_term, plat_kaal = plat(t), plat(kaal)
    kern = termwoorden[-1]  # het zelfstandig naamwoord draagt de betekenis

    # De subcategorie van AH ís de productsoort: walnoten staan onder
    # "Walnoten", kaaskoekjes onder "Kaaszoutjes". Dat is het scherpste
    # signaal dat er is, scherper dan de titel of de hoofdcategorie.
    # Op hele woorden, niet op deelstring: 'bloem' zit anders in 'Bloemkool'.
    sub = ontdiakritiseer((product.get("subCategory") or "").lower())
    subwoorden = set(re.findall(r"[a-z0-9]+", sub))
    plat_sub = plat(sub)
    soort_klopt = bool(plat_sub and (plat_term == plat_sub or kern in subwoorden))

    # De titel hoeft het kernwoord niet te noemen als de categorie het bevestigt:
    # 'AH Elstar' onder "Appels los" is wel degelijk appels.
    if not (kern in titelwoorden or plat_term in plat_kaal or soort_klopt):
        return -999

    punten = 0
    if plat_kaal == plat_term:
        punten += 60                      # exact hetzelfde product
    elif plat_kaal.startswith(plat_term):
        punten += 35                      # 'risottorijst' <- 'Risotto rijst 1kg'
    elif plat_kaal.endswith(plat_term):
        punten += 25                      # merk vooraan: 'Maldon Zeezoutvlokken'
    punten += sum(14 for w in termwoorden if w in titelwoorden)

    # Enkelvoud/meervoud en verkleinwoord: 'ui' <-> 'uien', 'tomaat' <-> 'tomaatjes'
    for w in termwoorden:
        if w in titelwoorden or len(w) < 4:
            continue
        if any(tw.startswith(w) or w.startswith(tw) for tw in titelwoorden
               if len(tw) >= 4):
            punten += 9

    if titel.startswith("ah "):
        punten += 6                       # huismerk: stabielere prijs en voorraad

    # Elk woord in de titel dat niet in de zoekterm zit, is een afwijking.
    # Begrensd, anders verliest een merknaam vooraan het van een slechte match.
    extra = len(titelwoorden - set(termwoorden) - {"ah", "biologisch", "terra"})
    punten -= min(extra * 4, 20)

    if soort_klopt:
        punten += 50

    # Waar de titel over gaat moet overeenkomen met waar de zoekterm over gaat.
    # 'parmezaanse kaas biscuits' en 'pita broodjes' zijn grammaticaal gelijk,
    # dus alleen een kloppende subcategorie pleit een afwijkende kop vrij.
    titelvolgorde = re.findall(r"[a-z0-9]+", kaal)
    kop = kernwoord(titelvolgorde)
    if kop and kop not in termwoorden and not soort_klopt:
        verwant = (
            any(kop.startswith(w) or w.startswith(kop)
                for w in termwoorden if len(w) >= 4 and len(kop) >= 4)
            or plat(kop) in plat_term          # 'passata' in 'tomatenpassata'
        )
        if not verwant:
            punten -= 45

    if product.get("mainCategory") in GEEN_INGREDIENT_CATEGORIE and not soort_klopt:
        punten -= 45

    if not product.get("images"):
        punten -= 15
    if product.get("orderAvailabilityStatus") not in (None, "IN_ASSORTMENT"):
        punten -= 10
    return punten


def beste_afbeelding(product):
    afbeeldingen = product.get("images") or []
    if not afbeeldingen:
        return None
    # Rond de 400px is genoeg voor een thumbnail naast een ingrediënt
    gesorteerd = sorted(afbeeldingen, key=lambda i: abs(i.get("width", 0) - 400))
    return gesorteerd[0].get("url")


def prijs_van(product):
    prijs = product.get("priceBeforeBonus")
    if prijs is None:
        huidig = product.get("currentPrice")
        prijs = huidig if isinstance(huidig, (int, float)) else None
    return prijs


def main():
    opnieuw = "--opnieuw" in sys.argv

    data = json.loads(RECEPTEN.read_text(encoding="utf8"))
    recepten = data["recepten"]

    cache = {}
    if PRODUCTEN.exists() and not opnieuw:
        cache = json.loads(PRODUCTEN.read_text(encoding="utf8"))

    # Verzamel de zoektermen en hang ze meteen aan de ingrediënten
    termen = {}
    for recept in recepten:
        for ing in recept["ingredienten"]:
            term = norm(ing["naam"])
            if not term:
                ing.pop("ah", None)
                continue
            ing["ah"] = term
            termen.setdefault(term, ing["naam"])

    # Een eerdere misser met inmiddels een ALIAS verdient een nieuwe poging
    nieuw = [
        t for t in termen
        if t not in VOORRAADKAST
        and (t not in cache or (cache[t] is None and t in ALIAS))
    ]
    print(f"{len(termen)} unieke zoektermen, {len(nieuw)} nog op te zoeken")

    ah = AH()
    gevonden = 0
    for i, term in enumerate(sorted(nieuw), 1):
        best, beste_punten, via = None, -10**9, term
        for kandidaat, maatstaf in varianten(term):
            producten = ah.zoek(kandidaat)
            time.sleep(0.2)
            if not producten:
                continue
            kop = max(producten, key=lambda p: score(maatstaf, p))
            punten = score(maatstaf, kop)
            if punten > beste_punten:
                best, beste_punten, via = kop, punten, kandidaat
            if beste_punten >= 60:
                break               # goed genoeg, verder zoeken heeft geen zin

        if best is None or beste_punten < 12:
            cache[term] = None
            gemist = f" (beste was '{best.get('title')}')" if best else ""
            print(f"  [{i}/{len(nieuw)}] {term}: geen goede match{gemist}")
            continue

        webshop_id = best.get("webshopId")
        cache[term] = {
            "id": webshop_id,
            "titel": best.get("title"),
            "afbeelding": beste_afbeelding(best),
            "eenheid": best.get("salesUnitSize"),
            "prijs": prijs_van(best),
            "url": f"https://www.ah.nl/producten/product/wi{webshop_id}",
            # De indeling van AH zelf. Daarmee kan de winkelweergave de
            # ingrediënten op schapvolgorde zetten in plaats van receptvolgorde.
            "schap": best.get("mainCategory"),
            "subschap": best.get("subCategory"),
        }
        gevonden += 1
        gezocht = "" if via == term else f"  [via '{via}']"
        print(f"  [{i}/{len(nieuw)}] {term} -> {best.get('title')}{gezocht}")

    PRODUCTEN.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf8",
    )
    RECEPTEN.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
    )

    gekoppeld = sum(1 for t in termen if cache.get(t))
    print(f"\nKlaar. {gekoppeld}/{len(termen)} termen gekoppeld "
          f"({gevonden} nieuw deze ronde).")
    print(f"  {PRODUCTEN.relative_to(WORTEL)}")
    print(f"  {RECEPTEN.relative_to(WORTEL)}")


if __name__ == "__main__":
    main()
