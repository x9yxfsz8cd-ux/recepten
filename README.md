# Onze Recepten

Persoonlijke receptenwebsite voor Shar & Robin.

## Structuur

```
docs/               → statische website (GitHub Pages)
  index.html        → receptenoverzicht met zoeken + filteren
  recept.html       → detailpagina per recept
  css/style.css     → stijlen
  data/
    recepten.json   → alle recepten
Scripts/
  shortcut-instructies.md   → hoe je de iPhone shortcut bouwt
  update-site.sh            → kopieer JSON van iCloud en push naar GitHub
```

## Website

Gepubliceerd op: https://x9yxfsz8cd-ux.github.io/recepten/

## Recept toevoegen

1. Gebruik de **Recept Saver** shortcut op iPhone
2. Recept wordt opgeslagen in Apple Notities + `iCloud Drive/recepten/recepten.json`
3. Voer `Scripts/update-site.sh` uit om de website bij te werken

## Lokaal bekijken

Open `docs/index.html` via een lokale server (niet direct als bestand — fetch() werkt anders):

```bash
cd docs
python3 -m http.server 8000
# open http://localhost:8000
```

## JSON Schema

Elk recept in `recepten.json` heeft deze velden:

| Veld | Type | Beschrijving |
|------|------|-------------|
| id | string | Unieke ID (bijv. r001) |
| titel | string | Naam van het recept |
| slug | string | URL-vriendelijke naam |
| afbeelding | string | URL of relatief pad |
| bereidingstijd | number | In minuten |
| moeilijkheidsgraad | string | makkelijk / gemiddeld / moeilijk |
| porties | number | Standaard aantal porties |
| tags | array | Uit vaste lijst (zie prompt) |
| ingredienten | array | naam + hoeveelheid + eenheid |
| stappen | array | nummer + tekst (max 3 zinnen) |
| voedingswaarden | object | kcal, eiwitten, koolhydraten, vetten |
| bron | string | Originele URL |
| bron_type | string | url / instagram / kookboek / whatsapp |
| datum_toegevoegd | string | YYYY-MM-DD |
