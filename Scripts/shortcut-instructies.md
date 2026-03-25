# Shortcut: Recept Saver

Open de **Opdrachten**-app op je iPhone en volg deze stappen.

Elke actie voeg je toe door onderaan in de **zoekbalk** de naam te typen.

---

## Voorbereiding

- Je **Claude API-sleutel** bij de hand (begint met `sk-ant-...`)
- In **Notities**: maak een map aan genaamd **recepten**

---

## De opdracht aanmaken

Open Opdrachten → tik **+** rechtsboven → geef de naam `Recept Saver`

---

## Actie 1: Invoer ontvangen

Zoek: `ontvang`
Kies: **Ontvang invoer van deelmenu**

Tik op de actie en stel in:
- Accepteer: **Afbeeldingen**, **URL's**, **Tekst**
- "Als er geen invoer is": kies **Vraag om invoer**

---

## Actie 2: Invoer opslaan als variabele

Zoek: `variabele`
Kies: **Stel variabele in**

- Variabelenaam: typ `Invoer`
- Waarde: tik → kies **Opdracht-invoer** (verschijnt automatisch)

---

## Actie 3: Controleer of het een foto is

Zoek: `als`
Kies: **Als**

- Invoer: tik → kies variabele **Invoer**
- Voorwaarde: **heeft type**
- Type: **Afbeelding**

---

## ALS het een afbeelding is (je zit nu in de "Als"-tak):

### Actie 4: Foto omzetten naar tekst

Zoek: `base64`
Kies: **Codeer met Base64**

- Invoer: tik → kies variabele **Invoer**

### Actie 5: Foto-data opslaan

Zoek: `variabele`
Kies: **Stel variabele in**

- Variabelenaam: typ `FotoData`
- Waarde: tik → kies **Gecodeerd met Base64** (verschijnt automatisch)

### Actie 6: API-bericht samenstellen (foto)

Zoek: `tekst`
Kies: **Tekst**

Plak dit in het tekstveld — **heel precies, inclusief alle tekens**:

```
[{"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":"
```

Tik dan in het tekstveld → tik op **Variabelen** boven het toetsenbord → kies **FotoData**

Typ dan direct daarna (zonder spatie):

```
"}},{"type":"text","text":"Extraheer het recept uit deze afbeelding en vertaal het volledig naar het Nederlands. Geef een nette samenvatting met: titel, ingrediënten met hoeveelheden, en genummerde stappen. Stappen maximaal 3 zinnen. Altijd Nederlandse eenheden (g, ml, el, tl, stuks)."}]
```

### Actie 7: Bericht opslaan als variabele

Zoek: `variabele`
Kies: **Stel variabele in**

- Variabelenaam: typ `BerichtInhoud`
- Waarde: tik → kies **Tekst** (de uitvoer van de vorige actie)

---

## ANDERS (onder de "Anders"-regel — voor URL's en tekst):

### Actie 8: API-bericht samenstellen (tekst)

Zoek: `tekst`
Kies: **Tekst**

Plak dit in het tekstveld:

```
[{"type":"text","text":"Extraheer het recept uit de onderstaande invoer en vertaal het volledig naar het Nederlands. Geef een nette samenvatting met: titel, ingrediënten met hoeveelheden, en genummerde stappen. Stappen maximaal 3 zinnen. Altijd Nederlandse eenheden (g, ml, el, tl, stuks).\n\nInvoer:\n
```

Tik dan in het tekstveld → tik op **Variabelen** boven het toetsenbord → kies **Invoer**

Typ dan direct daarna:

```
"}]
```

### Actie 9: Bericht opslaan als variabele

Zoek: `variabele`
Kies: **Stel variabele in**

- Variabelenaam: typ `BerichtInhoud`
- Waarde: tik → kies **Tekst** (de uitvoer van de vorige actie)

---

## Terug naar het hoofdniveau (na "Stop als"):

De actie **Stop als** staat er al automatisch. Alles hierna geldt voor zowel foto's als tekst/URL's.

---

## Actie 10: Claude API aanroepen

Zoek: `url`
Kies: **Haal inhoud van URL op**

Tik op de actie en stel in:

**URL:** tik op het URL-veld en typ:
```
https://api.anthropic.com/v1/messages
```

**Methode:** tik op "GET" en verander naar **POST**

Tik op **Toon meer** en stel in:

**Kopregels** (tik op "Kopregels" → voeg drie regels toe):

| Sleutel | Waarde |
|---------|--------|
| `x-api-key` | je API-sleutel (`sk-ant-...`) |
| `anthropic-version` | `2023-06-01` |
| `content-type` | `application/json` |

**Berichttekst:** tik → kies **JSON**

Voeg drie velden toe (tik op "Voeg nieuw veld toe"):

1. Sleutel: `model` — Type: **Tekst** — Waarde: `claude-haiku-4-5-20251001`
2. Sleutel: `max_tokens` — Type: **Getal** — Waarde: `2000`
3. Sleutel: `messages` — Type: **Reeks**

**messages invullen:**
- Tik op `messages` → **Voeg nieuw onderdeel toe** → type: **Woordenboek**
- In dat woordenboek, voeg twee velden toe:
  - Sleutel: `role` — Type: **Tekst** — Waarde: `user`
  - Sleutel: `content` — Type: **Tekst** — Waarde: tik → kies variabele **BerichtInhoud**

---

## Actie 11: API-resultaat opslaan

Zoek: `variabele`
Kies: **Stel variabele in**

- Variabelenaam: typ `APIResultaat`
- Waarde: tik → kies **Inhoud van URL** (verschijnt automatisch)

---

## Actie 12: "content" ophalen uit het resultaat

Zoek: `woordenboek`
Kies: **Haal woordenboekwaarde op**

- Invoer: tik → kies variabele **APIResultaat**
- Sleutel: typ `content`

---

## Actie 13: Eerste item pakken

Zoek: `onderdeel`
Kies: **Haal onderdeel op uit lijst**

- Invoer: tik → kies **Woordenboekwaarde** (verschijnt automatisch)
- Haal op: **Eerste onderdeel**

---

## Actie 14: De tekst eruit halen

Zoek: `woordenboek`
Kies: **Haal woordenboekwaarde op**

- Invoer: tik → kies **Onderdeel uit lijst** (verschijnt automatisch)
- Sleutel: typ `text`

---

## Actie 15: Recepttekst opslaan

Zoek: `variabele`
Kies: **Stel variabele in**

- Variabelenaam: typ `ReceptTekst`
- Waarde: tik → kies **Woordenboekwaarde** (verschijnt automatisch)

---

## Actie 16: Notitie aanmaken

Zoek: `notitie`
Kies: **Maak notitie aan**

- Map: tik → kies de map **recepten**
- Hoofdtekst: tik → kies variabele **ReceptTekst**

---

## Actie 17: Bevestiging tonen

Zoek: `melding`
Kies: **Toon melding**

- Titel: `Recept Saver`
- Hoofdtekst: `Recept opgeslagen!`

---

## Deelmenu activeren

Tik bovenaan op het **i-icoon** of de naam van de opdracht → kies **Details**:
- Zet **Toon in deelmenu** aan
- Onder **Typen in deelmenu**: zorg dat **Afbeeldingen**, **URL's** en **Tekst** aanstaan

---

## Testen

1. Open Safari → ga naar een receptenpagina
2. Tik op het **deelicoon** (vierkantje met pijltje)
3. Kies **Recept Saver**
4. Wacht even → je krijgt een melding "Recept opgeslagen!"
5. Open Notities → map recepten → je recept staat erin

---

## Delen met Robin

- Shar deelt de opdracht via **AirDrop** of **iMessage** (lang indrukken op de opdracht → Deel)
- Robin vult zijn eigen API-sleutel in bij actie 10
- In **Notities**: tik op de map recepten → deelicoon → **Deel map** → voeg Robin toe
- Nu zien jullie allebei dezelfde recepten
