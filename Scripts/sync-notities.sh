#!/bin/bash
# sync-notities.sh — Sync recepten.json naar Apple Notes (map "Recepten")
# Gebruik: ./sync-notities.sh [--push]

set -euo pipefail

REPO_DIR="$HOME/Recepten"
JSON_FILE="$REPO_DIR/docs/data/recepten.json"
GH="/tmp/gh/gh_2.67.0_macOS_arm64/bin/gh"
NOTES_FOLDER="Recepten"

# ---------------------------------------------------------------------------
# Stap 0 — Controleer vereisten
# ---------------------------------------------------------------------------
if [ ! -f "$JSON_FILE" ]; then
  echo "Fout: recepten.json niet gevonden op $JSON_FILE"
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "Fout: python3 is niet beschikbaar"
  exit 1
fi

# ---------------------------------------------------------------------------
# Stap 1 — Controleer toegang tot Apple Notes
# ---------------------------------------------------------------------------
echo "Toegang tot Apple Notes controleren..."
TEST_TITLE=$(osascript -e '
tell application "Notes"
  try
    set notesList to notes of folder "'"$NOTES_FOLDER"'"
    if (count of notesList) > 0 then
      return name of item 1 of notesList
    else
      return "LEEG"
    end if
  on error
    return "FOUT"
  end try
end tell
')

if [ "$TEST_TITLE" = "FOUT" ]; then
  echo "Fout: Kan Apple Notes niet benaderen. Controleer of de map '$NOTES_FOLDER' bestaat."
  exit 1
elif [ "$TEST_TITLE" = "LEEG" ]; then
  echo "Map '$NOTES_FOLDER' is leeg — notities worden aangemaakt."
else
  echo "Toegang OK — gevonden notitie: $TEST_TITLE"
fi

# ---------------------------------------------------------------------------
# Stap 2 — Parse JSON en genereer notities via Python + AppleScript (HTML)
# ---------------------------------------------------------------------------
echo ""
echo "Recepten synchroniseren naar Apple Notes..."

python3 << 'PYEOF'
import json
import subprocess
import os

JSON_PATH = os.path.expanduser("~/Recepten/docs/data/recepten.json")
NOTES_FOLDER = "Recepten"

with open(JSON_PATH, "r") as f:
    data = json.load(f)

recepten = data.get("recepten", [])
print(f"Aantal recepten gevonden: {len(recepten)}")

def escape_as(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')

def html_for_recipe(r):
    lines = []
    lines.append(f"<h1>{r['titel']}</h1>")

    tijd = f"{r.get('actieve_tijd', r.get('bereidingstijd', 0))} min actief"
    if r.get('passieve_tijd'):
        tijd += f" . {r['passieve_tijd']} min oven/rust"
    tijd += f" . {r['porties']} porties"
    lines.append(f"<div>{tijd}</div>")

    if r.get('tags'):
        tags = ' '.join(f"#{t}" for t in r['tags'])
        lines.append(f"<div>{tags}</div>")

    lines.append("<br>")
    lines.append("<div><b>Ingredienten</b></div>")

    for ing in r.get('ingredienten', []):
        naam = ing.get('naam', '')
        h = ing.get('hoeveelheid', 0)
        eenheid = ing.get('eenheid', '')
        if eenheid == 'naar smaak' or h == 0:
            lines.append(f"<div>{naam} (naar smaak)</div>")
        else:
            h_str = str(int(h)) if h == int(h) else str(h)
            lines.append(f"<div>{naam} ({h_str} {eenheid})</div>")

    lines.append("<br>")
    lines.append("<div><b>Bereiding</b></div>")

    for stap in sorted(r.get('stappen', []), key=lambda s: s.get('nummer', 0)):
        lines.append(f"<div>{stap.get('tekst', '')}</div>")

    v = r.get('voedingswaarden', {})
    if v and v.get('kcal', 0) > 0:
        lines.append("<br>")
        lines.append("<div><b>Voedingswaarden per portie</b></div>")
        lines.append(f"<div>{v['kcal']} kcal | {v['eiwitten']}g eiwit | {v['koolhydraten']}g koolhydraten | {v['vetten']}g vet</div>")

    lines.append("<br>")
    bron_naam = r.get('bron_naam', '') or r.get('bron_type', 'onbekend')
    if r.get('bron'):
        lines.append("<div>Bekijk op receptensite</div>")
    lines.append(f"<div>Bron: {bron_naam}</div>")

    return '\n'.join(lines)

for i, r in enumerate(recepten):
    titel = r.get("titel", "Zonder titel")
    html = html_for_recipe(r)
    escaped_title = escape_as(titel)
    escaped_html = escape_as(html)

    applescript = f'''
tell application "Notes"
    set folderRef to folder "{NOTES_FOLDER}"
    set noteFound to false
    repeat with n in notes of folderRef
        if name of n is "{escaped_title}" then
            set body of n to "{escaped_html}"
            set noteFound to true
            exit repeat
        end if
    end repeat
    if not noteFound then
        make new note at folderRef with properties {{body:"{escaped_html}"}}
    end if
end tell
'''

    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True, text=True, timeout=15
    )

    if result.returncode == 0:
        print(f"  [{i+1}/{len(recepten)}] OK - {titel}")
    else:
        print(f"  [{i+1}/{len(recepten)}] FOUT - {titel}: {result.stderr.strip()}")

print("\nSynchronisatie voltooid.")
PYEOF

# ---------------------------------------------------------------------------
# Stap 3 — Optioneel: push naar GitHub
# ---------------------------------------------------------------------------
if [ "${1:-}" = "--push" ]; then
  echo ""
  echo "Push naar GitHub..."
  cd "$REPO_DIR"
  git add docs/data/recepten.json
  git commit -m "Recepten bijgewerkt $(date '+%Y-%m-%d')" || echo "Geen wijzigingen om te committen."
  GIT_ASKPASS="$GH" GH_TOKEN=$("$GH" auth token) git push
  echo "Push voltooid."
fi
