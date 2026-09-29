# Shortcut: Boodschappen (recept → Herinneringen)

De receptpagina heeft een knop **"Zet op boodschappenlijst"**. Die stuurt de
ingrediënten (zonder voorraadkast-items, geschaald op de gekozen porties) naar
een Apple Shortcut met de naam **Boodschappen**. Die Shortcut zet elk item in je
boodschappenlijst in Herinneringen.

Je hoeft dit maar **één keer** in te stellen (op je iPhone).

---

## De Shortcut aanmaken

Open de **Opdrachten**-app → tik **+** rechtsboven → naam: `Boodschappen`

> Belangrijk: de naam moet exact **Boodschappen** zijn (dat verwacht de website).

### Actie 1 — Invoer ontvangen
Zoek: `ontvang` → kies **Ontvang invoer van deelmenu / snelle acties**
- Als er geen invoer is: kies **Stop en antwoord** (of laat op standaard)

### Actie 2 — Tekst splitsen op regels
Zoek: `splits tekst` → kies **Splits tekst**
- Tekst: tik → kies **Opdracht-invoer**
- Splits op: **Nieuwe regels**

### Actie 3 — Herhaal voor elk item
Zoek: `herhaal met elk` → kies **Herhaal met elk**
- Invoer: **Splits-tekst** (resultaat van actie 2)

Binnen de herhaling:

### Actie 4 — Voeg toe aan Herinneringen
Zoek: `herinnering` → kies **Voeg nieuwe herinnering toe**
- Titel: tik → kies **Herhaal-item**
- Lijst: kies je boodschappenlijst (bijv. **Boodschappen**)

Klaar. Tik op **Gereed**.

---

## Gebruik

1. Open een recept op de website
2. Zet eventueel de porties goed
3. Tik **Zet op boodschappenlijst**
4. De Shortcut opent en zet alle items in je Herinneringen-lijst

De lijst wordt ook naar je **klembord** gekopieerd als vangnet — mocht de
Shortcut (nog) niet bestaan, dan kun je zelf plakken.

---

## Voorraadkast aanpassen

Items die je standaard in huis hebt komen niet op de lijst. Die lijst staat in
`docs/recept.html`, bovenin het script bij `const VOORRAADKAST = [...]`.
Voeg woorden toe of haal ze weg naar smaak (bijv. `melk`, `eieren`, `rijst`).
