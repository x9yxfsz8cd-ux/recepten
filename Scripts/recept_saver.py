#!/usr/bin/env python3
"""
Recept Saver — haalt een recept op van een URL, slaat op in Apple Notities + website.

Gebruik:
    python3 recept_saver.py "https://www.ah.nl/allerhande/recept/..."
    echo "https://..." | python3 recept_saver.py
"""

import json, urllib.request, urllib.parse, ssl, re, subprocess, sys, os, time, base64
import html as html_mod

# ── Config ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RECEPTEN_JSON = os.path.join(PROJECT_DIR, "docs/data/recepten.json")
WEBSITE_BASE = "https://x9yxfsz8cd-ux.github.io/recepten"
API_KEY_FILE = os.path.expanduser("~/.config/recept-saver/api-key")
CTX = ssl.create_default_context()

SITE_NAMEN = {
    "ah.nl": "Albert Heijn", "marleyspoon.nl": "Marley Spoon",
    "marleyspoon.com": "Marley Spoon", "hellofresh.nl": "HelloFresh",
    "hellofresh.com": "HelloFresh", "cooking.nytimes.com": "NYT Cooking",
    "instagram.com": "Instagram", "youtube.com": "YouTube",
}

RECEPT_WOORDEN = ["ingredi", "bereid", "stap ", "minuten", "eetlepel", " el ", " tl ",
                   " gram ", "snijd", "bak ", "kook", "verhit", "voeg"]


def get_api_key():
    """Lees API key uit bestand of environment."""
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE) as f:
            return f.read().strip()
    key = os.environ.get("CLAUDE_API_KEY", "")
    if not key:
        print("Geen API key gevonden. Sla op in ~/.config/recept-saver/api-key")
        sys.exit(1)
    return key


def get_site_name(url):
    host = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if not host:
        return ""
    h = host.group(1)
    return SITE_NAMEN.get(h, h.split('.')[0].capitalize())


def slugify(t):
    t = t.lower()
    for a, b in [("é","e"),("è","e"),("ë","e"),("ê","e"),("á","a"),("à","a"),
                  ("ä","a"),("ö","o"),("ü","u"),("ú","u"),("ñ","n"),("ï","i")]:
        t = t.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


def fetch_simple(url):
    """Probeer de pagina op te halen met een simpele HTTP request."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def fetch_playwright(url):
    """Haal pagina op met headless Chromium (voor JS-gerenderde sites)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(5000)
            html = page.content()
            tekst = page.inner_text("body")
            browser.close()
        return html, tekst
    except Exception as e:
        print(f"  Playwright fout: {e}")
        return None, None


def has_recipe_content(tekst):
    """Check of de tekst receptinhoud bevat."""
    tekst_lower = tekst.lower()
    matches = sum(1 for w in RECEPT_WOORDEN if w in tekst_lower)
    return matches >= 3


def extract_og_image(html):
    """Haal og:image URL uit HTML."""
    for pattern in [
        r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
        r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
    ]:
        m = re.search(pattern, html, re.I)
        if m:
            return m.group(1)
    # JSON-LD image
    m = re.search(r'"image"\s*:\s*"(https?://[^"]+)"', html)
    if m:
        return m.group(1)
    return ""


def strip_html(html):
    """Verwijder HTML tags → platte tekst."""
    t = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.I)
    t = re.sub(r'<style[\s\S]*?</style>', '', t, flags=re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def call_claude(prompt, api_key):
    """Stuur prompt naar Claude Haiku en ontvang het antwoord."""
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "anthropic-dangerous-direct-browser-access": "true"
        }
    )
    with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
        data = json.loads(resp.read())

    if "error" in data:
        raise Exception(data["error"].get("message", str(data["error"])))

    return data["content"][0]["text"]


def parse_recipe(raw):
    """Parse Claude's gestructureerde antwoord."""
    def get(pattern, default=""):
        m = re.search(pattern, raw)
        return m.group(1).strip() if m else default

    titel = get(r'TITEL:\s*(.+)', "Recept")
    tags_str = get(r'TAGS:\s*(.+)')
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    porties = int(get(r'PORTIES:\s*(\d+)', "4"))
    tijd = int(get(r'TIJD:\s*(\d+)', "30"))
    beschrijving = get(r'BESCHRIJVING:\s*(.+)')

    parts = raw.split("===", 1)
    body = parts[1].strip() if len(parts) > 1 else raw

    # Parse ingrediënten
    ingredienten = []
    for m in re.finditer(r'^- (.+)$', body, re.M):
        line = m.group(1)
        pm = re.match(r'^([\d.,½¼¾⅓⅔]+(?:-[\d.,]+)?)\s*(g|ml|el|tl|stuks|snuf)\s+(.+)$', line)
        if pm:
            h_str = pm.group(1).split('-')[0].replace(',','.').replace('½','0.5').replace('¼','0.25').replace('¾','0.75')
            try:
                h = float(h_str)
            except:
                h = 0
            ingredienten.append({"naam": pm.group(3), "hoeveelheid": h, "eenheid": pm.group(2)})
        else:
            ingredienten.append({"naam": line, "hoeveelheid": 0, "eenheid": "naar smaak"})

    # Parse stappen
    stappen = []
    for m in re.finditer(r'^(\d+)\.\s+(.+)$', body, re.M):
        stappen.append({"nummer": int(m.group(1)), "tekst": m.group(2)})

    return {
        "titel": titel, "tags": tags, "porties": porties, "tijd": tijd,
        "beschrijving": beschrijving, "body": body,
        "ingredienten": ingredienten, "stappen": stappen
    }


def body_to_html(body):
    """Converteer recept body-tekst naar HTML."""
    lines = body.split("\n")
    html_lines = []
    in_ul = False
    in_ol = False
    step_pat = re.compile(r'^\d+\.\s+')

    for line in lines:
        line = line.strip()
        if not line:
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            continue

        if re.match(r'^(INGREDI|BEREIDING|STAPPEN)', line, re.I):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<br><h2>{html_mod.escape(line.rstrip(':'))}</h2>")
            continue

        if line.startswith("**") and "**" in line[2:]:
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<br><h2>{html_mod.escape(line.strip('*').rstrip(':'))}</h2>")
            continue

        if line.startswith("- "):
            if not in_ul: html_lines.append("<ul>"); in_ul = True
            html_lines.append(f"<li>{html_mod.escape(line[2:])}</li>")
            continue

        if step_pat.match(line):
            if not in_ol: html_lines.append("<ol>"); in_ol = True
            step_text = step_pat.sub('', line)
            html_lines.append(f"<li>{html_mod.escape(step_text)}</li>")
            continue

        html_lines.append(f"<p>{html_mod.escape(line)}</p>")

    if in_ul: html_lines.append("</ul>")
    if in_ol: html_lines.append("</ol>")
    return "\n".join(html_lines)


def download_image_base64(url):
    """Download afbeelding en return als base64 string."""
    if not url:
        return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            return base64.b64encode(resp.read()).decode()
    except Exception:
        return ""


def create_note(titel, html_body):
    """Maak een notitie aan in Apple Notities via AppleScript."""
    escaped = html_body.replace('\\', '\\\\').replace('"', '\\"')
    script = f'''
    tell application "Notes"
        tell account "iCloud"
            if not (exists folder "recepten") then
                make new folder with properties {{name:"recepten"}}
            end if
            tell folder "recepten"
                -- Verwijder bestaande met dezelfde naam
                set oldNotes to every note whose name is "{titel.replace(chr(34), chr(92)+chr(34))}"
                repeat with n in oldNotes
                    delete n
                end repeat
                -- Maak nieuwe
                set newNote to make new note with properties {{body:"{escaped}"}}
                return name of newNote
            end tell
        end tell
    end tell
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode == 0:
        return r.stdout.strip()
    else:
        print(f"  Notitie fout: {r.stderr[:200]}")
        return None


def update_website(recipe_data, url, img_url, bron_naam):
    """Voeg recept toe aan recepten.json en push naar GitHub."""
    recipe_id = f"r{int(time.time())}"

    website_recipe = {
        "id": recipe_id,
        "titel": recipe_data["titel"],
        "slug": slugify(recipe_data["titel"]),
        "beschrijving": recipe_data["beschrijving"],
        "afbeelding": img_url,
        "bereidingstijd": recipe_data["tijd"],
        "moeilijkheidsgraad": "gemiddeld",
        "porties": recipe_data["porties"],
        "tags": recipe_data["tags"],
        "ingredienten": recipe_data["ingredienten"],
        "stappen": recipe_data["stappen"],
        "voedingswaarden": {"kcal": 0, "eiwitten": 0, "koolhydraten": 0, "vetten": 0},
        "bron": url,
        "bron_naam": bron_naam,
        "bron_type": "url",
        "datum_toegevoegd": time.strftime("%Y-%m-%d")
    }

    with open(RECEPTEN_JSON, "r") as f:
        db = json.load(f)
    db["recepten"] = [r for r in db["recepten"] if r.get("bron") != url]
    db["recepten"].append(website_recipe)
    with open(RECEPTEN_JSON, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    os.chdir(PROJECT_DIR)
    subprocess.run(["git", "add", "docs/data/recepten.json"], capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Recept: {recipe_data['titel']}"], capture_output=True)
    subprocess.run(["git", "push"], capture_output=True)

    return recipe_id


# ── Main ──

def main():
    # Input
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = sys.stdin.read().strip()

    if not url:
        print("Gebruik: python3 recept_saver.py <URL>")
        sys.exit(1)

    api_key = get_api_key()
    bron_naam = get_site_name(url)

    # ── 1. Pagina ophalen ──
    print(f"Ophalen: {url}")
    html = fetch_simple(url)

    tekst = ""
    if html:
        tekst = strip_html(html)

    # Check of er daadwerkelijk receptinhoud in zit
    if not tekst or not has_recipe_content(tekst):
        print("  Geen receptinhoud gevonden, probeer headless browser...")
        pw_html, pw_tekst = fetch_playwright(url)
        if pw_html:
            html = pw_html
            tekst = pw_tekst if pw_tekst else strip_html(pw_html)
        if not tekst or not has_recipe_content(tekst):
            print("  Nog steeds geen receptinhoud. Claude probeert het op basis van de URL.")
            tekst = f"URL: {url} (pagina kon niet worden opgehaald)"

    # Afbeelding
    img_url = extract_og_image(html) if html else ""
    print(f"  Afbeelding: {'gevonden' if img_url else 'geen'}")

    # ── 2. Claude API ──
    print("Recept extraheren...")
    prompt = (
        "Extraheer het recept uit onderstaande pagina-inhoud en vertaal alles naar het Nederlands.\n\n"
        "Geef je antwoord in dit EXACTE format:\n\n"
        "TITEL: [receptnaam]\n"
        "TAGS: [komma-gescheiden tags uit: vis, vlees, vegetarisch, vegan, snel, comfort food, Aziatisch, Italiaans, ontbijt, lunch, diner, snack]\n"
        "PORTIES: [aantal]\nTIJD: [bereidingstijd in minuten]\nBESCHRIJVING: [1 zin]\n"
        "===\nINGREDIENTEN:\n- [hoeveelheid] [eenheid] [ingrediënt]\n\n"
        "BEREIDING:\n1. [stap]\n\n"
        "Regels:\n- Altijd Nederlands\n- Eenheden: g, ml, el, tl, stuks\n"
        "- Stappen max 3 zinnen\n- Neem ALLE stappen en ingrediënten over met EXACTE hoeveelheden\n\n"
        f"Pagina-inhoud van {url}:\n{tekst[:10000]}"
    )

    raw = call_claude(prompt, api_key)
    recipe = parse_recipe(raw)
    print(f"  Titel: {recipe['titel']}")
    print(f"  Tags: {', '.join(recipe['tags'])}")
    print(f"  {recipe['tijd']} min · {recipe['porties']} porties")
    print(f"  {len(recipe['ingredienten'])} ingrediënten, {len(recipe['stappen'])} stappen")

    # ── 3. Website bijwerken ──
    print("Website bijwerken...")
    recipe_id = update_website(recipe, url, img_url, bron_naam)
    website_url = f"{WEBSITE_BASE}/recept.html?id={recipe_id}"
    print(f"  {website_url}")

    # ── 4. Notitie aanmaken ──
    print("Notitie aanmaken...")
    img_b64 = download_image_base64(img_url)
    img_html = f'<p><img src="data:image/jpeg;base64,{img_b64}" style="width:100%"></p>' if img_b64 else ""

    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in recipe["tags"])
    recept_html = body_to_html(recipe["body"])

    meta_parts = []
    if recipe["tijd"]:
        meta_parts.append(f"{recipe['tijd']} min")
    meta_parts.append(f"{recipe['porties']} porties")

    full_html = (
        f"<h1>{html_mod.escape(recipe['titel'])}</h1>\n"
        f"{img_html}\n"
        f'<p style="color:gray">{" · ".join(meta_parts)}</p>\n'
        f"<p>{hashtags}</p>\n"
        f"{recept_html}\n"
        f"<br>\n<hr>\n"
        f'<p><a href="{html_mod.escape(website_url)}">Bekijk op receptensite</a></p>\n'
        f'<p>Bron: <a href="{html_mod.escape(url)}">{html_mod.escape(bron_naam)}</a></p>'
    )

    note_name = create_note(recipe["titel"], full_html)
    if note_name:
        print(f"  Notitie: {note_name}")

    print(f"\nKlaar! {recipe['titel']}")
    return recipe["titel"]


if __name__ == "__main__":
    main()
