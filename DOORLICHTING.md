# Doorlichting van alle 48 recepten

1 oktober 2026. Elk recept regel voor regel nagelopen op wat er tijdens het
koken misgaat. Niet gekookt — dat kan ik niet — maar wel alles gecontroleerd
wat je op papier kunt zien: ontbrekende stappen, hoeveelheden die niet
overeenkomen, tijden die niet kloppen, en tags die iets anders beweren dan de
ingrediënten.

Herhaalbaar met `python3 Scripts/doorlicht.py` (en `<zoekterm>` voor één recept).

## Echte fouten, hersteld

| Recept | Wat er mis was |
|---|---|
| Gennaro's carbonara | Goot de spaghetti af en vroeg daarna om een scheut kookwater. Nu eerst een kopje wegscheppen. |
| Pita shoarma van oesterzwam | Verwarmde de oven voor op 230 °C en gebruikte de oven daarna nergens. De pita's gaan er nu in. |
| Elly's appeltaart | Stond op 55 min totaal; de stappen noemen 30 min koelen plus 75 min bakken. Nu 130. |
| Vegetarische lasagna | Stond op 90 min; 25 roosteren + 30 bakken + 20 rusten is 75 min wachten. Nu 115. |
| Gepofte zoete aardappel | Stap noemt 45 min poffen, passieve tijd stond op 25. |
| Gerookte-paprikarisotto | Lijst zei Grana Padano, stap zei pecorino. Twee verschillende kazen. |
| Zalm met citroen | Badia kruiden stonden in de lijst maar werden nergens gebruikt. |
| Tijmchampignons | Peper en zout stonden in de lijst maar werden nergens toegevoegd. |
| Groene groenten met bulgur | Blancheerstap voor de bimi ontbrak; stond wel in het origineel. |
| Pasta Aglio e Olio | Typefout, zout en peper niet in de lijst, en 'pan van het vuur' moest 'vuur laag' zijn. |
| Poké bowl met zalm | 'Schil de bospeen' ontbrak. |
| Tijmchampignons | Het grof hakken van de walnoten ontbrak. |
| Falafel wraps | Flatbreads opwarmen zonder temperatuur. |
| Spaghetti met tonijn | 'Kook de pasta en giet af tot al dente' stond omgekeerd. |
| Citroenpasta | 'Voeg kruiden toe' zei niet welke. |
| Pastasalade tonijn | 'Voeg alle overige ingrediënten toe' dwong je terug naar de lijst. |
| Aubergines in kaneel | 'Snijd de aubergine en ui' zei niet hoe. |

## Leesbaarheid

- Twee recepten zeiden "1/2 el per persoon" terwijl de ingrediëntenlijst al
  meeschaalt met de portieknop. Omgezet naar absolute hoeveelheden.
- Vijf stappen waren 320 tot 407 tekens lang. Gesplitst — je leest ze met een
  pan op het vuur en je vinkt ze per stap af.
- Elf ingrediënten stonden op 'stuks' terwijl je ze niet per stuk koopt
  ('1 stuks peterselie', '1 stuks hazelnoten'). Nu bosje, takjes, blaadjes of gram.
- Verpakkingseenheden die buiten hun doos niets zeggen ('2 stuks Parmigiano'
  van HelloFresh) omgezet naar gram.

## Winkelscherm

Olijfolie voor de groenten en olijfolie voor de dressing stonden als twee
aparte regels. In de winkel is dat één fles. Zelfde product en zelfde eenheid
gaan nu samen, met de hoeveelheden opgeteld, en één vinkje zet ze allebei af.
Acht recepten hadden zo'n dubbele regel. Op de receptpagina blijven ze apart,
want daar maakt het wel uit welke olie waar in gaat.

## Gecontroleerd en in orde bevonden

- **Zalm met citroen** leek niet te kloppen: 2 citroenen, maar de stappen
  raspen een halve, persen er anderhalf en vragen 4 schijfjes. Een halve
  citroen geeft prima 4 dunne schijfjes.
- De overige wachttijden die mijn telling opwierp zijn bakmomenten waar je bij
  de pan staat. Dat is actieve tijd, geen passieve.
- Alle 48 recepten hebben een maaltijdmoment in de tags.
- Geen typefouten, dubbele spaties of losse leestekens gevonden.
- Geen dubbele recepten meer (de harissa-spruitjes stonden er twee keer, al
  samengevoegd).

## Oventemperaturen: opgelost

Beide ovens in huis zijn hetelucht — AEG SteamPro BSK792280B (70 l, met stoom)
en AEG CombiQuick KMK761080B (43 l, met magnetron). Alle 21 oventemperaturen
staan nu als één getal met 'hetelucht' erbij; de 'of X °C elektrisch' is weg.

Dertien keer zei de bron niet welke stand bedoeld was. Daar is het getal
gelezen als hetelucht, omdat Nederlandse recepten voor de eigen oven van de
schrijver geschreven zijn en die vrijwel altijd hetelucht is. Mocht een gerecht
te licht uit de oven komen, dan is dat de plek om 20 graden bij te zetten:
Halloumi-pita's, Aubergines in kaneel, Traybake met orzo, Pita shoarma,
Gnocchi-traybake, Gepofte zoete aardappel, Zalm met citroen,
Gerookte-paprikarisotto, Elly's appeltaart, Kokoskoek, Falafel wraps.
De vegetarische lasagna komt van een Amerikaanse site (425 °F, conventioneel)
en is wél omgerekend: 220 -> 200, en de tweede fase 200 -> 180.

## Onze keuken staat nu in het recept

Bij Bereiding staat een regel 'Onze keuken' met het aanbevolen ovenprogramma,
afgestemd op de AEG SteamPro. Dat advies komt uit `Scripts/ovenprogramma.py` en
staat bewust niet in een bereidingsstap: het is onze eigen aanbeveling, niet
wat de bron voorschreef.

| Soort gerecht | Programma | Waarom |
|---|---|---|
| Traybake, geroosterde groenten | Hetelucht, plaat in het midden | Gelijkmatig, goede kleur |
| Gegratineerd, kaas erover | Hetelucht + laatste 5-10 min Turbogrill | Korst zonder de rest uit te drogen |
| Cake en taart in een vorm | Boven + onderwarmte | Hetelucht sluit de bovenkant voordat het midden gaar is |
| Gistdeeg | Gistdeeg rijzen, dan Pizza-instelling | Extra onderwarmte voor een krokante bodem |
| Onder de grill | Turbogrill, hoogste stand | Straling van boven, rondgeblazen |
| Vis in folie | Hetelucht, of Steamify zonder folie | Stoom houdt de zalm zachter |
| Brood opwarmen | Regenereren met stoom | Zacht in plaats van droog |

Bij pannengerechten staat er dat de Demeyere-pannen op inductie lang warmte
vasthouden. Een braadslede of bakplaat past alleen in de SteamPro (70 l);
een springvorm van 24 cm past ook in de CombiQuick.

## Wat ik niet kan beslissen

**Edamame in de noedelsoep** gaan er pas aan het eind bij, zonder te garen.
Uit de diepvries wil je ze even meekoken. De bron (eefkooktzo) blokkeert
automatisch ophalen, dus ik heb het niet kunnen nakijken.

**Groene orzo**: de ingrediënten kloppen met de bron, maar de bereidingswijze
staat bij die Instagram-post in de reacties en is zonder inloggen niet te
lezen. De stappen die erin staan zijn plausibel maar niet geverifieerd.

## Kookmodus

De tekst stond op ongeveer 21 px in een kolom van 21 tekens breed, waardoor hij
elke vier woorden afbrak, en de ingrediëntenregel stond op bijschriftgrootte.
Dat is het scherm waar grootte juist het meest uitmaakt: je leest het van een
meter afstand, met natte handen.

  staptekst      21 -> 29 px, regel van 21 naar 26 tekens breed
  ingredienten   12 -> 17 px
  timerknop      14 -> 17 px, minstens 52 px hoog
  navigatie      16 -> 17 px, minstens 56 px hoog

De maten staan in rem zodat ze met Dynamic Type meegroeien; de min() is alleen
een rem op hele grote schermen.
