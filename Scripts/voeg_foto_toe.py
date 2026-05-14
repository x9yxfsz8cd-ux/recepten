#!/usr/bin/env python3
"""
Voeg een foto toe aan een recept op de site.

Gebruik:
  python3 Scripts/voeg_foto_toe.py <recept-id> <pad-naar-foto>

Voorbeeld:
  python3 Scripts/voeg_foto_toe.py r1778095207 ~/Desktop/tonijnsalade.jpg

De foto wordt automatisch:
  - gekopieerd naar docs/images/
  - verkleind naar max 1200px
  - toegevoegd aan het recept in recepten.json
  - gecommit en gepushed naar GitHub
"""
import sys, json, shutil, subprocess
from pathlib import Path

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)

recept_id = sys.argv[1]
foto_pad  = Path(sys.argv[2]).expanduser().resolve()

if not foto_pad.exists():
    print(f"Foto niet gevonden: {foto_pad}")
    sys.exit(1)

root       = Path(__file__).parent.parent
json_pad   = root / "docs/data/recepten.json"
images_dir = root / "docs/images"
images_dir.mkdir(exist_ok=True)

with open(json_pad, encoding="utf-8") as f:
    data = json.load(f)

recept = next((r for r in data["recepten"] if r["id"] == recept_id), None)

if not recept:
    print(f"Recept '{recept_id}' niet gevonden.\n")
    print("Beschikbare recepten:")
    for r in data["recepten"]:
        print(f"  {r['id']}  —  {r['titel']}")
    sys.exit(1)

# Bestandsnaam op basis van slug
slug = recept.get("slug", recept_id).replace("'", "").replace(" ", "-")

# Tweede foto als eerste al bestaat
if recept.get("afbeelding") and not recept.get("afbeelding_2"):
    bestandsnaam = f"{slug}-2.jpg"
    json_veld = "afbeelding_2"
else:
    bestandsnaam = f"{slug}.jpg"
    json_veld = "afbeelding"

doel = images_dir / bestandsnaam
shutil.copy(foto_pad, doel)

# Verklein naar max 1200px breedte via sips (ingebouwd in macOS)
r = subprocess.run(["sips", "-Z", "1200", str(doel)], capture_output=True)
if r.returncode != 0:
    print("Waarschuwing: sips niet beschikbaar, foto niet verkleind.")

# Update JSON
recept[json_veld] = f"./images/{bestandsnaam}"

with open(json_pad, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nFoto toegevoegd aan: {recept['titel']}")
print(f"  Veld:    {json_veld}")
print(f"  Bestand: docs/images/{bestandsnaam}")

# Git commit + push
def git(*args):
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True)

git("add", str(json_pad.relative_to(root)), str(doel.relative_to(root)))
commit = git("commit", "-m", f"Foto: {recept['titel']}")
if commit.returncode != 0:
    print(f"Commit mislukt: {commit.stderr.strip()}")
    sys.exit(1)

push = git("push")
if push.returncode == 0:
    print("Gepushed naar GitHub. Wacht ~1 min en refresh de site.")
else:
    print(f"Push mislukt: {push.stderr.strip()}")
