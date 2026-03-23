# Shortcut: Recept Saver

## Wat doet deze shortcut?
- Ontvang een URL, tekst of foto
- Stuur dit naar Claude (AI) om het recept te extraheren en te vertalen naar Nederlands
- Sla het op in Apple Notities (map "recepten")
- Sla de JSON op in iCloud Drive zodat je de website kunt bijwerken

---

## Stap 0 — Claude API-sleutel aanmaken

1. Ga naar **console.anthropic.com**
2. Maak een account aan (gratis tier is voldoende voor persoonlijk gebruik)
3. Ga naar **API Keys** → **Create Key**
4. Kopieer de sleutel (begint met `sk-ant-...`)
5. Sla hem op in Apple Notities in een notitie genaamd **"API Sleutels"** zodat de shortcut hem kan ophalen

---

## Stap 1 — Nieuwe shortcut aanmaken

Open de **Shortcuts app** op iPhone → **+** rechtsboven → naam: `Recept Saver` → icoon 🍳, kleur groen.

---

## Stap 2 — Invoer ontvangen

**Voeg toe:** `Receive` → selecteer: **Tekst + URL's + Afbeeldingen**
- "Als er geen invoer is" → **Vraag om invoer**
- Sla op als variabele: `Invoer`

---

## Stap 3 — API-sleutel ophalen

**Voeg toe:** `Zoek Notities`
- Filter: Naam bevat `API Sleutels`
- Limiet: 1

**Voeg toe:** `Haal tekst op uit Notitie` → sla op als: `NotitieInhoud`

**Voeg toe:** `Haal overeenkomsten op in tekst`
- Invoer: `NotitieInhoud`
- Patroon (regex): `sk-ant-[A-Za-z0-9\-_]+`
- Sla op als: `APISleutel`

---

## Stap 4 — Bepaal invoertype

**Voeg toe:** `Als`
- Voorwaarde: `Invoer` → **is van type** → **Afbeelding**

**In de Als-tak:** Base64-codering van de afbeelding
```
Voeg toe: Encodeer [Invoer] → base64 → sla op als: AfbeeldingBase64
Stel tekst in:
{
  "type": "image",
  "source": {
    "type": "base64",
    "media_type": "image/jpeg",
    "data": "[AfbeeldingBase64]"
  }
}
Sla op als: InvoerBlok
```

**In de Anders-tak:**
```
Stel tekst in:
{
  "type": "text",
  "text": "[Invoer]"
}
Sla op als: InvoerBlok
```

**Voeg toe:** `Eindigen als`

---

## Stap 5 — Claude API aanroepen

**Voeg toe:** `Haal inhoud van URL op`

**URL:** `https://api.anthropic.com/v1/messages`
**Methode:** POST
**Headers:**
- `x-api-key`: `[APISleutel]`
- `anthropic-version`: `2023-06-01`
- `content-type`: `application/json`

**Body (JSON):**
```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 2000,
  "messages": [
    {
      "role": "user",
      "content": [
        [InvoerBlok],
        {
          "type": "text",
          "text": "Extraheer het recept uit de bovenstaande invoer en vertaal het volledig naar het Nederlands. Geef de output als geldig JSON met exact deze structuur:\n\n{\n  \"id\": \"r[timestamp]\",\n  \"titel\": \"\",\n  \"slug\": \"\",\n  \"afbeelding\": \"\",\n  \"bereidingstijd\": 0,\n  \"moeilijkheidsgraad\": \"makkelijk\",\n  \"porties\": 4,\n  \"tags\": [],\n  \"ingredienten\": [{\"naam\": \"\", \"hoeveelheid\": 0, \"eenheid\": \"\"}],\n  \"stappen\": [{\"nummer\": 1, \"tekst\": \"\"}],\n  \"voedingswaarden\": {\"kcal\": 0, \"eiwitten\": 0, \"koolhydraten\": 0, \"vetten\": 0},\n  \"bron\": \"\",\n  \"bron_type\": \"url\",\n  \"datum_toegevoegd\": \"[datum]\"\n}\n\nRegels:\n- Altijd in het Nederlands\n- Gebruik Nederlandse eenheden: g, ml, el, tl, stuks, snuf, naar smaak\n- Bereidingstijd in minuten\n- Moeilijkheidsgraad: makkelijk / gemiddeld / moeilijk\n- Tags alleen uit: vegetarisch, vegan, vis, vlees, snel, comfort food, Aziatisch, Italiaans, ontbijt, lunch, diner, snack\n- Stappen maximaal 3 zinnen elk\n- Geef ALLEEN de JSON terug, geen uitleg"
        }
      ]
    }
  ]
}
```

Sla de uitvoer op als: `APIReactie`

---

## Stap 6 — JSON verwerken

**Voeg toe:** `Haal waarde op in woordenboek`
- Invoer: `APIReactie`
- Sleutel: `content`
→ Sla op als: `ContentArray`

**Voeg toe:** `Haal item op uit lijst`
- Invoer: `ContentArray` → Eerste item
→ Sla op als: `EersteContent`

**Voeg toe:** `Haal waarde op in woordenboek`
- Invoer: `EersteContent`
- Sleutel: `text`
→ Sla op als: `ReceptJSON`

---

## Stap 7 — Opslaan in Apple Notities

**Voeg toe:** `Haal waarde op in woordenboek`
- Invoer: `ReceptJSON` (parse als JSON)
- Sleutel: `titel`
→ Sla op als: `ReceptTitel`

**Voeg toe:** `Maak notitie aan`
- Map: **recepten**
- Naam: `[ReceptTitel]`
- Inhoud:
```
🍳 [ReceptTitel]

[Afbeelding als bijlage indien beschikbaar]

🔗 Bekijk op website: https://x9yxfsz8cd-ux.github.io/recepten/recept.html?id=[id]

---
[ReceptJSON]
```

---

## Stap 8 — JSON opslaan in iCloud

**Voeg toe:** `Haal inhoud van bestand op`
- Pad: `iCloud Drive/recepten/recepten.json`
→ Sla op als: `HuidigJSON`

*(Als het bestand niet bestaat, sla dan een leeg `{"recepten":[]}` op als startpunt)*

**Voeg toe:** `Stel tekst in` → bouw de bijgewerkte JSON handmatig samen of gebruik de Siri-suggestie "Voeg toe aan lijst"

**Voeg toe:** `Sla bestand op`
- Pad: `iCloud Drive/recepten/recepten.json`
- Inhoud: bijgewerkte JSON

---

## Stap 9 — Share Sheet activeren

- Tik op de shortcut → **Deel** → **Aan beginscherm toevoegen**
- Ga naar Instellingen shortcut → zet **"In aandeel-menu weergeven"** aan

---

## Gebruik

- **Instagram:** Bekijk een reels/post → tik op **Delen** → **Recept Saver**
- **Foto van kookboek:** Kies de foto vanuit Foto's → Delen → Recept Saver
- **WhatsApp-tekst:** Selecteer tekst → Delen → Recept Saver
- **URL:** Kopieer een URL → open Shortcuts → tik op Recept Saver

---

## Website bijwerken

Na het opslaan van een recept:

1. Kopieer `iCloud Drive/recepten/recepten.json` naar `recepten/docs/data/recepten.json` in je Git-repo
2. Push naar GitHub:
   ```
   cd ~/Documents/recepten
   git add docs/data/recepten.json
   git commit -m "Nieuw recept toegevoegd"
   git push
   ```
3. Na ±1 minuut is het recept zichtbaar op de website

Zie ook: `Scripts/update-site.sh` voor een snelle terminal-opdracht.
