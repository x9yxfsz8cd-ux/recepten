#!/bin/bash
# Exporteert één album uit Photos naar een tijdelijke map en scant het op recepten.
# Alles blijft lokaal: exporteren, OCR en beoordelen gebeuren op deze Mac.
# Gebruik:  ./Scripts/exporteer_album.sh "Recepten"
set -e
ALBUM="${1:?geef de albumnaam op, bijvoorbeeld: ./Scripts/exporteer_album.sh Recepten}"
MAP="$HOME/.claude/jobs/dedfd50e/tmp/album"
rm -rf "$MAP"; mkdir -p "$MAP"
echo "Album '$ALBUM' exporteren..."
osascript <<APPLESCRIPT
set doel to POSIX file "$MAP" as alias
tell application "Photos"
  set a to album "$ALBUM"
  export (get media items of a) to doel with using originals
end tell
APPLESCRIPT
echo "$(ls "$MAP" | wc -l | tr -d ' ') foto's geëxporteerd. Nu scannen..."
python3 "$(dirname "$0")/zoek_recepten_in_fotos.py" "$MAP" --toon
