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
# Stap 1 — Controleer toegang tot Apple Notes door een notitie-titel te lezen
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
# Stap 2 — Parse JSON en genereer notities via Python
# ---------------------------------------------------------------------------
echo ""
echo "Recepten synchroniseren naar Apple Notes..."

python3 << 'PYEOF'
import json
import subprocess
import sys
import os

JSON_PATH = os.path.expanduser("~/Recepten/docs/data/recepten.json")
NOTES_FOLDER = "Recepten"

with open(JSON_PATH, "r") as f:
    data = json.load(f)

recepten = data.get("recepten", [])
print(f"Aantal recepten gevonden: {len(recepten)}")

for i, r in enumerate(recepten):
    titel = r.get("titel", "Zonder titel")
    actieve_tijd = r.get("actieve_tijd", 0)
    passieve_tijd = r.get("passieve_tijd", 0)
    porties = r.get("porties", 0)
    tags = r.get("tags", [])
    ingredienten = r.get("ingredienten", [])
    stappen = r.get("stappen", [])
    voeding = r.get("voedingswaarden", {})
    bron = r.get("bron", "")
    bron_naam = r.get("bron_naam", "")

    # Build note body lines
    lines = []
    lines.append(titel)
    lines.append(f"{actieve_tijd} min actief . {passieve_tijd} min oven/rust . {porties} porties")

    if tags:
        lines.append(" ".join(f"#{t}" for t in tags))
    lines.append("")

    # Ingredienten
    lines.append("Ingredienten")
    for ing in ingredienten:
        naam = ing.get("naam", "")
        hoeveelheid = ing.get("hoeveelheid", 0)
        eenheid = ing.get("eenheid", "")
        if eenheid == "naar smaak" or hoeveelheid == 0:
            lines.append(f"{naam} (naar smaak)")
        else:
            # Format number: drop .0 for whole numbers
            if isinstance(hoeveelheid, float) and hoeveelheid == int(hoeveelheid):
                hoeveelheid = int(hoeveelheid)
            lines.append(f"{naam} ({hoeveelheid} {eenheid})")
    lines.append("")

    # Bereiding
    lines.append("Bereiding")
    for stap in sorted(stappen, key=lambda s: s.get("nummer", 0)):
        lines.append(stap.get("tekst", ""))
    lines.append("")

    # Voedingswaarden
    if voeding:
        kcal = voeding.get("kcal", 0)
        eiwitten = voeding.get("eiwitten", 0)
        koolhydraten = voeding.get("koolhydraten", 0)
        vetten = voeding.get("vetten", 0)
        lines.append("Voedingswaarden per portie")
        lines.append(f"{kcal} kcal | {eiwitten}g eiwit | {koolhydraten}g koolhydraten | {vetten}g vet")
        lines.append("")

    # Bron
    if bron:
        lines.append("Bekijk op receptensite")
        lines.append(f"Bron: {bron_naam}")
    elif bron_naam:
        lines.append(f"Bron: {bron_naam}")

    note_body = "\n".join(lines)

    # Escape for AppleScript: backslashes first, then quotes
    def escape_as(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    escaped_title = escape_as(titel)
    escaped_body = escape_as(note_body)

    # Build AppleScript that checks for existing note and updates or creates
    applescript = f'''
tell application "Notes"
    set folderRef to folder "{NOTES_FOLDER}"
    set noteFound to false
    repeat with n in notes of folderRef
        if name of n is "{escaped_title}" then
            set body of n to "{escaped_body}"
            set noteFound to true
            exit repeat
        end if
    end repeat
    if not noteFound then
        make new note at folderRef with properties {{name:"{escaped_title}", body:"{escaped_body}"}}
    end if
end tell
'''

    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True, text=True
    )

    status = "OK" if result.returncode == 0 else "FOUT"
    if result.returncode != 0:
        err = result.stderr.strip()
        print(f"  [{i+1}/{len(recepten)}] {status} - {titel}")
        print(f"           {err}")
    else:
        print(f"  [{i+1}/{len(recepten)}] {status} - {titel}")

print("")
print("Synchronisatie voltooid.")
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
  "$GH" repo sync 2>/dev/null || git push
  echo "Push voltooid."
fi
