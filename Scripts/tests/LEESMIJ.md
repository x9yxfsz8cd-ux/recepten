# Tests

Node-tests die de echte code uit de pagina's halen en tegen de echte
`recepten.json` draaien. Geen framework, geen browser: ze lezen het bestand,
knippen de functie eruit en voeren hem uit met een nagebootste DOM en opslag.

```bash
for t in Scripts/tests/qa-*.mjs; do node "$t"; done
```

- `qa-winkel.mjs`   keuze bewaren, migratie van de oude opslag, `?id=`,
                    verdwenen recepten, kapotte json, lege staat
- `qa-porties.mjs`  vier porties standaard, vaste vorm houdt zijn aantal,
                    eigen keuze wint, afronden van hoeveelheden
- `qa-tijd.mjs`     welke tijd uit een staptekst een timer wordt
- `qa-zoek.mjs`     korte zoektermen raken niet het halve boek

Het harnas knipt op een vaste tekst uit de bron. Verander je de naam van een
functie of wat eromheen staat, pas dan ook de `indexOf` in de test aan — anders
crasht hij in plaats van te falen, en dat las ik een keer verkeerd als groen.
