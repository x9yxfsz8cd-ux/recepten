#!/bin/bash
# update.sh — draait alle afgeleide stappen in de juiste volgorde.
#
# Na een wijziging in recepten.json of in css/js moeten er zes scripts draaien.
# Vergeet je er één, dan merk je dat pas dagen later: een ingrediënt zonder
# productfoto, een kaartje dat de grote foto laadt, of een stylesheet die uit
# de cache komt zodat een fix niet lijkt te werken. Daarom één commando.
#
# Gebruik:
#   Scripts/update.sh              # alles afleiden en nakijken
#   Scripts/update.sh --push       # en daarna committen en pushen
#
# Het pad komt uit de locatie van dit script, niet uit een vaste map. De vorige
# versie wees naar ~/Recepten, een kloon die twee maanden stil stond, en deed
# daardoor niets meer.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

PUSH=0
[ "${1:-}" = "--push" ] && PUSH=1

mislukt=0

# Een stap die het internet nodig heeft mag struikelen zonder de rest te
# blokkeren: zonder bereik moet je nog steeds een typfout kunnen rechtzetten.
stap() {
  local soort="$1" naam="$2"; shift 2
  printf '\n\033[1m%s\033[0m\n' "$naam"
  if "$@"; then
    return 0
  fi
  if [ "$soort" = "netwerk" ]; then
    echo "   overgeslagen — geen verbinding of de bron deed niet mee"
    return 0
  fi
  echo "   MISLUKT"
  mislukt=1
  return 1
}

# Volgorde telt. De eerste vijf schrijven in recepten.json en halen foto's
# binnen; versie.py stempelt daarna de html. Omgekeerd zou de stempel de
# wijziging van die stappen missen.
stap netwerk "Albert Heijn koppelen"      python3 Scripts/ah_verrijken.py
stap netwerk "Foto's lokaal opslaan"      python3 Scripts/foto_lokaal.py
stap lokaal  "Kaartfoto's verkleinen"     python3 Scripts/kaartfotos.py
stap lokaal  "Benodigdheden afleiden"     python3 Scripts/benodigdheden.py
stap lokaal  "Ovenprogramma afleiden"     python3 Scripts/ovenprogramma.py

# Het versienummer verschoont de cache. Niet elke keer stempelen, want dan
# verandert ook de naam van de service-worker-cache en haalt iedereen de hele
# site opnieuw op terwijl er niets veranderde.
#
# Het gaat om alles wat de service worker vooraf opslaat, en dat is meer dan css
# en js: de html-pagina's staan er zonder versienummer in en worden cache-first
# geserveerd. Een wijziging in de inline javascript van winkel.html bereikt je
# telefoon dus alleen als de cachenaam meegaat. sw.js staat er bewust niet bij,
# die wordt door versie.py zelf herschreven.
BEWAARD="docs/css docs/js docs/index.html docs/recept.html docs/winkel.html docs/import.html docs/manifest.json"
if [ -n "$(git status --porcelain -- $BEWAARD 2>/dev/null)" ]; then
  stap lokaal "Versienummer stempelen" python3 Scripts/versie.py
else
  printf '\n\033[1mVersienummer stempelen\033[0m\n   niet nodig, er is niets gewijzigd dat in de cache zit\n'
fi

if [ "$mislukt" = 1 ]; then
  printf '\n\033[1mGestopt.\033[0m Een stap ging mis, hierboven staat welke.\n'
  exit 1
fi

# ---------------------------------------------------------------------------
# Nakijken
# ---------------------------------------------------------------------------
printf '\n\033[1mRecepten nakijken\033[0m\n'
RAPPORT="$(python3 Scripts/doorlicht.py)"
SAMENVATTING="$(printf '%s' "$RAPPORT" | tail -1)"
FOUTEN="$(printf '%s' "$SAMENVATTING" | sed -n 's/^\([0-9]*\) fouten.*/\1/p')"
echo "   $SAMENVATTING"

if [ "${FOUTEN:-0}" != "0" ]; then
  printf '%s\n' "$RAPPORT" | grep -n 'FOUT' | head -20
  printf '\n\033[1mEr staan fouten in de recepten.\033[0m Draai Scripts/doorlicht.py voor het hele rapport.\n'
  [ "$PUSH" = 1 ] && { echo "Niet gepusht."; exit 1; }
  exit 1
fi

# ---------------------------------------------------------------------------
# Wat is er veranderd
# ---------------------------------------------------------------------------
printf '\n\033[1mGewijzigd\033[0m\n'
if [ -z "$(git status --porcelain)" ]; then
  echo "   niets — alles was al bijgewerkt"
  exit 0
fi
git status --short | sed 's/^/   /'

if [ "$PUSH" = 0 ]; then
  printf '\nKlaar. Pushen? Scripts/update.sh --push\n'
  exit 0
fi

printf '\n\033[1mPushen\033[0m\n'
git add -A
git commit -q -m "Site bijgewerkt $(date '+%Y-%m-%d')" || { echo "   niets te committen"; exit 0; }
if git push -q; then
  echo "   gepusht — GitHub Pages staat er over ongeveer een minuut op"
else
  echo "   push mislukt"
  exit 1
fi
