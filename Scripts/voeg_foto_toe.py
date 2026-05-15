#!/usr/bin/env python3
"""
Voeg een foto toe aan een recept.
Dubbelklik op 'Voeg Foto Toe.command' — geen argumenten nodig.
"""
import sys, json, shutil, subprocess
from pathlib import Path

root     = Path(__file__).parent.parent
json_pad = root / "docs/data/recepten.json"

with open(json_pad, encoding="utf-8") as f:
    data = json.load(f)
recepten = data["recepten"]

def dialoog(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None

def kies_recept():
    zonder_foto = [r for r in recepten if not r.get("afbeelding")]
    if not zonder_foto:
        dialoog('display alert "Alle recepten hebben al een foto." as informational')
        return None
    titels = [r["titel"] for r in zonder_foto]
    lijst  = ", ".join(f'"{t}"' for t in titels)
    keuze  = dialoog(f'choose from list {{{lijst}}} with prompt "Voor welk recept is de foto? ({len(zonder_foto)} zonder foto)" without multiple selections allowed')
    if not keuze or keuze == "false":
        return None
    return next(r for r in zonder_foto if r["titel"] == keuze)

def kies_foto():
    pad = dialoog('POSIX path of (choose file of type {"public.image"} with prompt "Kies een foto:")')
    return Path(pad.strip()) if pad else None

def melding(tekst):
    dialoog(f'display notification "{tekst}" with title "Recepten"')

# ── Kies recept
recept = kies_recept()
if not recept:
    sys.exit(0)

# ── Kies foto
foto = kies_foto()
if not foto:
    sys.exit(0)

# ── Kopieer & verklein
images_dir = root / "docs/images"
images_dir.mkdir(exist_ok=True)

slug = recept.get("slug", recept["id"]).replace("'", "")
veld = "afbeelding_2" if recept.get("afbeelding") and not recept.get("afbeelding_2") else "afbeelding"
suffix = "-2" if veld == "afbeelding_2" else ""
doel = images_dir / f"{slug}{suffix}.jpg"

shutil.copy(foto, doel)
subprocess.run(["sips", "-Z", "1200", str(doel)], capture_output=True)

# ── Update JSON
recept[veld] = f"./images/{doel.name}"
with open(json_pad, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# ── Git push
def git(*args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)

git("add", str(json_pad.relative_to(root)), str(doel.relative_to(root)))
git("commit", "-m", f"Foto: {recept['titel']}")
push = git("push")

if push.returncode == 0:
    melding(f"Foto toegevoegd aan {recept['titel']} ✓")
    print(f"Klaar: foto toegevoegd aan '{recept['titel']}'")
else:
    melding("Push mislukt — check Terminal")
    print(push.stderr)
