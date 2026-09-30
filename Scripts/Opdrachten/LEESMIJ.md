# De twee Opdrachten

De website kan twee dingen aan je iPhone vragen. Daar zijn deze Opdrachten
(Shortcuts) voor. Je installeert ze één keer.

| Opdracht | Wat hij doet | Wie roept hem aan |
|---|---|---|
| **Boodschappen** | Zet de ingrediënten in je lijst in Herinneringen | Knop *Zet op boodschappenlijst* op de receptpagina |
| **Kooktimer** | Start een timer in de Klok-app, met de naam van de stap | Het klokje in de timerbalk tijdens het koken |

De namen moeten **exact** zo blijven. De site roept ze op naam aan.

## Installeren

1. AirDrop `Boodschappen.shortcut` en `Kooktimer.shortcut` naar je iPhone.
2. Open ze en tik op **Voeg opdracht toe**.
3. Eerste keer: Instellingen → Opdrachten → **Onbetrouwbare opdrachten
   toestaan** moet aan staan. Die schakelaar verschijnt pas nadat je één keer
   zelf een opdracht hebt gemaakt of uitgevoerd.

## Waarom de timer dit nodig heeft

De timer ín de webpagina loopt alleen zolang je scherm aan staat en Safari
vooraan is. Zodra je je telefoon wegdraait of een appje leest, bevriest iOS die
timer — precies op het moment dat je hem nodig hebt. De Klok-app loopt wél door
en geeft een melding.

## Twee velden die je moet controleren

Deze twee kon ik hier niet testen, omdat ze pas op een iPhone blijken te
kloppen. Open de opdracht na het installeren en kijk even:

**Boodschappen** → actie *Voeg nieuwe herinnering toe*
De lijst moet op **Boodschappen** staan. Staat er iets anders of niets, tik
erop en kies je eigen lijst.

**Kooktimer** → actie *Start timer*
Bij de duur hoort **Onderdeel uit lijst** te staan (de seconden uit de
website), met eenheid **seconden**. Is het veld leeg, tik erop, kies
*Variabele* en dan het resultaat van de eerste *Onderdeel uit lijst*.

## Hoe de site ze aanroept

    shortcuts://run-shortcut?name=Boodschappen&input=text&text=<ingrediënten>
    shortcuts://run-shortcut?name=Kooktimer&input=text&text=300|Stap 4 — Noedelsoep

Boodschappen krijgt één ingrediënt per regel. Kooktimer krijgt het aantal
seconden, een streepje, en de naam van de stap.

## Zelf opnieuw bouwen

    python3 Scripts/maak_shortcuts.py

Dat schrijft ze opnieuw en ondertekent ze met `shortcuts sign`, dat op elke Mac
zit. Een Apple-ontwikkelaarsaccount is niet nodig.

## Voorraadkast aanpassen

Wat je standaard in huis hebt komt niet op de boodschappenlijst. Die lijst staat
bovenin `docs/recept.html` bij `const VOORRAADKAST`. Woorden toevoegen of
weghalen mag.
