# Onze Recepten

Persoonlijke receptenwebsite voor Shar & Robin — 52 recepten, offline te gebruiken,
gemaakt om op een telefoon in de keuken en in de supermarkt te lezen.

Gepubliceerd op <https://x9yxfsz8cd-ux.github.io/recepten/>

## Structuur

```
docs/                        de website zelf (GitHub Pages serveert deze map)
  index.html                 overzicht: zoeken, filteren, favorieten
  recept.html                recept met kookmodus, timers en porties schalen
  winkel.html                boodschappenlijst over één of meer recepten tegelijk
  import.html                recept toevoegen uit een link, foto of tekst
  css/style.css              het hele ontwerp, opgebouwd uit tokens
  js/gedeeld.js              favorieten, porties schalen, opslag vastzetten
  js/opslag.js               localStorage met terugvaloptie
  js/ingredient-icoon.js     icoontjes voor de boodschappenlijst
  data/recepten.json         alle recepten — de enige bron van waarheid
  data/ah-producten.json     ingrediënt -> Albert Heijn-product (foto, prijs, link)
  img/recept/                gerechtfoto's, 1400 px, voor de receptpagina
  img/kaart/                 dezelfde foto's op 640 px, voor het overzicht
  img/ah/                    productfoto's van de AH, zodat de winkel offline werkt
  sw.js                      service worker: shell vooraf, foto's bij gebruik
Scripts/
  update.sh                  draait alles hieronder in de juiste volgorde
  ah_verrijken.py            koppelt ingrediënten aan AH-producten
  foto_lokaal.py             haalt foto's binnen naar docs/img/
  kaartfotos.py              maakt de 640 px-versies voor het overzicht
  benodigdheden.py           leidt "Pak alvast" af uit de stappen
  ovenprogramma.py           advies per recept voor de AEG SteamPro
  versie.py                  stempelt css/js-urls tegen de cache van Pages
  doorlicht.py               controleert elk recept op kookfouten
  ocr.swift                  tekst uit een foto via Apple Vision
  zoek_recepten_in_fotos.py  zoekt receptfoto's in de Fotobibliotheek
```

## Recept toevoegen

Open **import.html** op de site (het plusje rechtsboven). Drie manieren:

| Tabblad | Waarvoor |
|---|---|
| Link | een receptpagina of een Instagram-post |
| Recept uitlezen | foto's van een kookboek- of tijdschriftpagina |
| Recept toevoegen | tekst die je zelf intypt of plakt |

Je voert één keer een API-sleutel in (onderaan, onder "Sleutel"); die blijft
daarna staan. Foto's worden in de browser verkleind voordat ze weggaan, en de
gerechtfoto wordt uit de pagina gesneden met het kader dat het model teruggeeft.
Je ziet een voorbeeld met alles wat er automatisch bij gezet is voordat je opslaat.

Opslaan commit rechtstreeks naar GitHub. Draai daarna `Scripts/update.sh`, zodat
de AH-koppeling, de foto's en de kaartversies kloppen.

## Wijziging doorvoeren

```bash
Scripts/update.sh          # alles afleiden en nakijken
Scripts/update.sh --push   # en daarna committen en pushen
```

Zes scripts moeten in deze volgorde draaien na een wijziging, en `update.sh` doet
dat. Vergeet je er één, dan merk je dat pas dagen later — een ingrediënt zonder
productfoto, of een stylesheet die uit de cache komt waardoor een fix niet lijkt
te werken. Het script weigert te pushen als `doorlicht.py` fouten vindt.

## Lokaal bekijken

`fetch()` werkt niet vanaf `file://`, dus via een server:

```bash
cd docs && python3 -m http.server 8000   # http://localhost:8000
```

## Onze keuken

De adviezen in de app gaan uit van wat hier staat: een **AEG 9000 SteamPro
(BSK792280B)** oven, een **Bora X Pure** inductiekookplaat en **Demeyere**-pannen.
Dat staat zo in `ovenprogramma.py` en in de keukentips.

## recepten.json

Eén object met de sleutel `recepten`. Per recept:

| Veld | Type | Beschrijving |
|---|---|---|
| id | string | `r001` of `r` + tijdstempel |
| titel | string | naam van het recept |
| slug | string | url-vriendelijke naam |
| beschrijving | string | één zin |
| afbeelding | string | altijd `img/recept/<slug>.jpg` |
| bereidingstijd | number | totaal in minuten |
| actieve_tijd | number | hoe lang je zelf bezig bent |
| passieve_tijd | number | oven, koelkast, rijzen — moet optellen tot bereidingstijd |
| moeilijkheidsgraad | string | makkelijk / gemiddeld / moeilijk |
| porties | number | waar de hoeveelheden bij horen; de app schaalt naar 4 |
| tags | array | uit de lijst in `index.html` |
| ingredienten | array | `naam`, `hoeveelheid`, `eenheid`, `ah` (sleutel in ah-producten.json) |
| stappen | array | `nummer` + `tekst`, hoogstens 3 zinnen per stap |
| voedingswaarden | object | kcal, eiwitten, koolhydraten, vetten — per portie |
| benodigdheden | array | afgeleid; verschijnt als "Pak alvast" |
| ovenprogramma | string | afgeleid; alleen bij een ovenrecept |
| bron | string | url naar het origineel |
| bron_naam | string | naam van de bron, bijv. het kookboek |
| bron_type | string | url / kookboek / tijdschrift / instagram / notitie / klassiek |
| datum_toegevoegd | string | JJJJ-MM-DD |

`benodigdheden` en `ovenprogramma` worden door scripts gezet — met de hand
aanpassen heeft geen zin, de volgende `update.sh` overschrijft het.
