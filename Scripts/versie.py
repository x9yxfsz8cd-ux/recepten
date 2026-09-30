#!/usr/bin/env python3
"""
Zet een nieuw versienummer achter css- en js-verwijzingen.

GitHub Pages cachet bestanden tien minuten. Zonder verse URL zie je na een
push nog de oude stylesheet, en dan lijkt een fix niet te werken terwijl hij
allang klaar is. Draai dit vlak voor elke commit waarin css of js verandert.

Het nummer is de tijd van draaien, dus het loopt altijd op.
"""

import re
import time
from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent
DOCS = WORTEL / "docs"
PAGINAS = ["index.html", "recept.html", "winkel.html", "import.html"]
SCRIPTS = ["gedeeld", "ingredient-icoon", "opslag"]


def main():
    versie = str(int(time.time()))[-6:]

    for naam in PAGINAS:
        pad = DOCS / naam
        if not pad.exists():
            continue
        s = pad.read_text(encoding="utf8")
        s = re.sub(r'(href="\./css/style\.css)(\?v=[^"]*)?"', rf'\1?v={versie}"', s)
        s = re.sub(rf'(src="\./js/({"|".join(SCRIPTS)})\.js)(\?v=[^"]*)?"',
                   rf'\1?v={versie}"', s)
        pad.write_text(s, encoding="utf8")

    sw = DOCS / "sw.js"
    t = sw.read_text(encoding="utf8")
    t = re.sub(r"(\./css/style\.css)(\?v=[^']*)?'", rf"\1?v={versie}'", t)
    t = re.sub(rf"(\./js/({'|'.join(SCRIPTS)})\.js)(\?v=[^']*)?'", rf"\1?v={versie}'", t)
    # De cachenaam mee ophogen, anders blijft de oude service worker serveren
    t = re.sub(r"const CACHE = 'recepten-v\d+';",
               f"const CACHE = 'recepten-v{versie}';", t)
    sw.write_text(t, encoding="utf8")

    print(f"versie {versie} gezet in {len(PAGINAS)} pagina's en sw.js")


if __name__ == "__main__":
    main()
