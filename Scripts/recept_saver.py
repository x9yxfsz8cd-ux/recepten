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


def search_duckduckgo(query):
    """Zoek via DuckDuckGo HTML (werkt zonder JS, geen blokkades)."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        results = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="[^"]*uddg=([^&"]+)', html):
            href = urllib.parse.unquote(m.group(1))
            results.append(href)

        return list(dict.fromkeys(results))[:10]
    except Exception as e:
        print(f"  DuckDuckGo fout: {e}")
        return []


def fetch_instagram_caption(instagram_url):
    """Haal de volledige caption op van een Instagram post/reel via og:description."""
    try:
        req = urllib.request.Request(instagram_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        desc = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"', html, re.I)
        if desc:
            import html as html_module
            caption = html_module.unescape(desc.group(1))
            # Strip "X likes, Y comments - user on date:" prefix
            caption = re.sub(r'^\d[\d,.]+\s+likes?,\s*\d[\d,.]+\s+comments?\s*-\s*\w+\s+on\s+\w+\s+\d+,\s*\d+:\s*"?', '', caption)
            caption = caption.rstrip('"')
            return caption
        return ""
    except Exception:
        return ""


def search_recipe_online(query):
    """Zoek een recept online en haal de inhoud op."""
    print(f"  Online zoeken: {query}")
    urls = search_duckduckgo(query + " recept")

    if not urls:
        print("  Geen zoekresultaten")
        return "", ""

    # Filter op bruikbare sites
    skip = ['youtube.', 'facebook.', 'twitter.', 'tiktok.', 'pinterest.', 'accounts.']
    urls = [u for u in urls if not any(s in u.lower() for s in skip)]

    # Instagram links apart behandelen
    instagram_urls = [u for u in urls if 'instagram.com' in u]
    other_urls = [u for u in urls if 'instagram.com' not in u]

    # 1. Probeer Instagram caption (vaak het volledige recept)
    for ig_url in instagram_urls[:2]:
        print(f"    Instagram caption: {ig_url[:80]}")
        caption = fetch_instagram_caption(ig_url)
        if caption and len(caption) > 100:
            print(f"    Caption gevonden! ({len(caption)} chars)")
            return caption, ig_url

    # 2. Probeer receptensites
    for url in other_urls[:5]:
        print(f"    Probeer: {url[:80]}")
        page_html = fetch_simple(url)
        if page_html:
            json_ld = extract_json_ld_recipe(page_html)
            if json_ld:
                print(f"    JSON-LD gevonden!")
                return json.dumps(json_ld, ensure_ascii=False), url
            plat = strip_html(page_html)
            if has_recipe_content(plat):
                print(f"    Receptinhoud gevonden!")
                return plat[:8000], url

    # 3. Playwright als fallback voor eerste resultaat
    if other_urls:
        try:
            from playwright.sync_api import sync_playwright
            best = other_urls[0]
            print(f"    Playwright: {best[:80]}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(best, timeout=15000)
                page.wait_for_timeout(5000)
                pw_tekst = page.inner_text("body")
                browser.close()
            if has_recipe_content(pw_tekst):
                return pw_tekst[:8000], best
        except Exception:
            pass

    return "", ""


def verify_recipe_from_image(image_b64, media_type, api_key):
    """
    Stap 1: Claude leest de afbeelding en extraheert wat het kan + identificeert de bron.
    Stap 2: Als er een bron is (creator, boek, Instagram account), zoek online.
    Stap 3: Combineer alles voor het meest complete recept.
    """
    # Stap 1: Lees de afbeelding
    print("  Afbeelding analyseren...")
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 2000,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                {"type": "text", "text": (
                    "Analyseer deze afbeelding van een recept. Geef EXACT dit format:\n\n"
                    "TITEL: [naam van het recept]\n"
                    "BRON: [Instagram account/@naam, kookboek titel+auteur, of website — alleen als zichtbaar]\n"
                    "COMPLEET: [ja/nee — zijn ALLE ingrediënten en stappen zichtbaar?]\n"
                    "TYPE: [instagram/kookboek/website/overig]\n\n"
                    "ZICHTBARE INGREDIENTEN:\n"
                    "- [alles wat je kunt lezen met exacte hoeveelheden]\n\n"
                    "ZICHTBARE STAPPEN:\n"
                    "1. [alles wat je kunt lezen]\n\n"
                    "Geef alles in het Nederlands. Wees heel precies met hoeveelheden."
                )}
            ]
        }]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json", "anthropic-dangerous-direct-browser-access": "true"}
    )
    with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
        data = json.loads(resp.read())

    analyse = data["content"][0]["text"]
    print(f"  Analyse: {analyse[:300]}...")

    # Extract metadata (flexibele parsing)
    def find(patterns, text, default=""):
        for p in patterns:
            m = re.search(p, text, re.I)
            if m:
                val = m.group(1).strip().strip('*').strip()
                if val and val.lower() not in ['onbekend', 'niet zichtbaar', 'n/a', '-']:
                    return val
        return default

    titel = find([r'TITEL:\s*(.+)', r'(?:^|\n)#+\s*(?:\d+\.)?\s*(.+)'], analyse)
    bron = find([r'BRON:\s*(.+)', r'(?:Creator|Account|Kookboek|Auteur)[:\s]+(.+)'], analyse)
    bron_type = find([r'TYPE:\s*(.+)'], analyse, "overig").lower()
    is_compleet = 'ja' in find([r'COMPLEET:\s*(.+)'], analyse, "nee").lower()

    # Schoon bron op — verwijder onbruikbare waarden
    skip_bron = ['niet zichtbaar', 'onbekend', 'icloud', 'shar roeters', 'gedeeld via', 'n/a']
    if any(s in bron.lower() for s in skip_bron):
        bron = ""

    # Strip markdown formatting van titel
    titel = titel.strip('*').strip('#').strip()

    # Detecteer Instagram account (@naam)
    ig_account = ""
    ig_match = re.search(r'@(\w{3,})', analyse)
    if ig_match:
        ig_account = ig_match.group(1)
    elif bron:
        ig_match2 = re.search(r'@(\w{3,})', bron)
        if ig_match2:
            ig_account = ig_match2.group(1)

    print(f"  Titel: {titel}")
    print(f"  Bron: {bron}")
    print(f"  Type: {bron_type}")
    print(f"  Instagram: @{ig_account}" if ig_account else "  Instagram: -")
    print(f"  Compleet: {'ja' if is_compleet else 'nee'}")

    # Stap 2: Zoek online — altijd als niet compleet, of als we een bron hebben
    web_tekst = ""
    web_url = ""
    afbeelding_url = ""

    if not is_compleet or bron or ig_account:
        # Zoekstrategie hangt af van het type
        if ig_account or 'instagram' in bron_type:
            # Instagram: zoek naar de post en haal caption op
            zoekterm = f"{ig_account or bron} {titel}"
            print(f"  Instagram zoeken: {zoekterm}")
            web_tekst, web_url = search_recipe_online(zoekterm)

        elif 'kookboek' in bron_type or 'boek' in bron.lower():
            # Kookboek: zoek op boektitel + receptnaam
            zoekterm = f"{bron} {titel}"
            print(f"  Kookboek zoeken: {zoekterm}")
            web_tekst, web_url = search_recipe_online(zoekterm)

        else:
            # Algemeen: zoek op titel + bron
            zoekterm = f"{bron} {titel}".strip() if bron else titel
            if zoekterm:
                print(f"  Algemeen zoeken: {zoekterm}")
                web_tekst, web_url = search_recipe_online(zoekterm)

        # Probeer ook een afbeelding te vinden van de online bron
        if web_url:
            try:
                page_html = fetch_simple(web_url)
                if page_html:
                    afbeelding_url = extract_og_image(page_html)
            except Exception:
                pass

        # Instagram: haal de grootste afbeelding op via Playwright als og:image faalt
        if not afbeelding_url and (ig_account or 'instagram.com' in web_url):
            try:
                from playwright.sync_api import sync_playwright
                ig_url = web_url if 'instagram.com' in web_url else f"https://www.instagram.com/{ig_account}/"
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(ig_url, timeout=15000)
                    page.wait_for_timeout(5000)
                    imgs = page.eval_on_selector_all(
                        'img[src*="cdninstagram"]',
                        'els => els.map(e => ({src: e.src, size: e.naturalWidth * e.naturalHeight})).sort((a,b) => b.size - a.size)'
                    )
                    browser.close()
                if imgs:
                    afbeelding_url = imgs[0]['src']
            except Exception:
                pass

        if web_tekst:
            print(f"  Online bron gevonden: {web_url[:80]}")
        else:
            print("  Geen online bron gevonden — alleen afbeelding-data gebruiken")

    return {
        "analyse": analyse,
        "titel": titel,
        "bron": bron,
        "bron_type": bron_type,
        "ig_account": ig_account,
        "is_compleet": is_compleet,
        "web_tekst": web_tekst,
        "web_url": web_url,
        "afbeelding_url": afbeelding_url,
    }


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


def extract_youtube_data(url):
    """Haal beschrijving + transcript op van een YouTube video."""
    video_id = None
    m = re.search(r'(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})', url)
    if m:
        video_id = m.group(1)
    if not video_id:
        return None

    result = {"video_id": video_id, "titel": "", "beschrijving": "", "transcript": ""}

    # 1. Haal beschrijving + titel uit de pagina HTML
    try:
        req = urllib.request.Request(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "nl"}
        )
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        desc_match = re.search(r'"shortDescription"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
        if desc_match:
            result["beschrijving"] = desc_match.group(1).encode().decode('unicode_escape')

        title_match = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
        if title_match:
            result["titel"] = title_match.group(1)

        # og:image
        og = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html, re.I)
        if og:
            result["afbeelding"] = og.group(1)
    except Exception:
        pass

    # 2. Haal transcript op
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        try:
            transcript = api.fetch(video_id, languages=["nl", "en"])
        except Exception:
            transcript = api.fetch(video_id)
        result["transcript"] = " ".join(snippet.text for snippet in transcript)
    except Exception:
        pass

    return result


def strip_html(html):
    """Verwijder HTML tags → platte tekst."""
    t = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.I)
    t = re.sub(r'<style[\s\S]*?</style>', '', t, flags=re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def extract_json_ld_recipe(html):
    """Zoek een JSON-LD Recipe schema in de HTML."""
    scripts = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>', html, re.I
    )
    for s in scripts:
        try:
            data = json.loads(s)
            items = data if isinstance(data, list) else data.get("@graph", [data])
            for item in items:
                if isinstance(item, dict):
                    t = item.get("@type", "")
                    if t == "Recipe" or (isinstance(t, list) and "Recipe" in t):
                        return item
        except Exception:
            pass
    return None


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
    """Download afbeelding en return als base64 string. Fallback via Playwright bij 403."""
    if not url:
        return ""
    # Directe download
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            return base64.b64encode(resp.read()).decode()
    except Exception:
        pass

    # Fallback: download via Playwright (omzeilt CDN-blokkades zoals Instagram)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("about:blank")
            b64 = page.evaluate(f'''async () => {{
                try {{
                    const resp = await fetch("{url}");
                    const blob = await resp.blob();
                    return new Promise((resolve) => {{
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result.split(",")[1]);
                        reader.readAsDataURL(blob);
                    }});
                }} catch {{ return ""; }}
            }}''')
            browser.close()
            if b64:
                return b64
    except Exception:
        pass

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

def save_recipe(recipe, bron_url, bron_naam, img_url, api_key):
    """Sla recept op in website + Notities. Gedeelde functie."""
    print("Website bijwerken...")
    recipe_id = update_website(recipe, bron_url, img_url, bron_naam)
    website_url = f"{WEBSITE_BASE}/recept.html?id={recipe_id}"
    print(f"  {website_url}")

    print("Notitie aanmaken...")
    img_b64 = download_image_base64(img_url)
    img_html = f'<p><img src="data:image/jpeg;base64,{img_b64}" style="width:100%"></p>' if img_b64 else ""
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in recipe["tags"])
    recept_html = body_to_html(recipe["body"])
    meta_parts = []
    if recipe["tijd"]: meta_parts.append(f"{recipe['tijd']} min")
    meta_parts.append(f"{recipe['porties']} porties")

    full_html = (
        f"<h1>{html_mod.escape(recipe['titel'])}</h1>\n{img_html}\n"
        f'<p style="color:gray">{" · ".join(meta_parts)}</p>\n<p>{hashtags}</p>\n'
        f"{recept_html}\n<br>\n<hr>\n"
        f'<p><a href="{html_mod.escape(website_url)}">Bekijk op receptensite</a></p>\n'
        f'<p>Bron: <a href="{html_mod.escape(bron_url)}">{html_mod.escape(bron_naam)}</a></p>'
    )
    note_name = create_note(recipe["titel"], full_html)
    if note_name: print(f"  Notitie: {note_name}")
    print(f"\nKlaar! {recipe['titel']}")
    return recipe["titel"]


def main():
    # Input
    is_foto = len(sys.argv) > 1 and sys.argv[1] == "--foto"

    if is_foto:
        # Foto-modus: --foto <pad naar afbeelding>
        if len(sys.argv) < 3:
            print("Gebruik: python3 recept_saver.py --foto <pad>")
            sys.exit(1)

        foto_pad = sys.argv[2]
        api_key = get_api_key()

        print(f"Foto analyseren: {foto_pad}")
        with open(foto_pad, "rb") as f:
            foto_b64 = base64.b64encode(f.read()).decode()

        ext = foto_pad.lower().rsplit(".", 1)[-1]
        media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")

        # Stap 1: Analyseer + verificeer via web
        verificatie = verify_recipe_from_image(foto_b64, media_type, api_key)

        # Stap 2: Combineer afbeelding + web-data voor het finale recept
        bronnen = [f"Uit de afbeelding gelezen:\n{verificatie['analyse']}"]
        if verificatie["web_tekst"]:
            bronnen.append(f"Online gevonden (verificatie):\n{verificatie['web_tekst'][:6000]}")
            print("  Web-verificatie succesvol — combineer bronnen")

        prompt = (
            "Combineer de onderstaande bronnen tot het meest complete recept. "
            "De online bron is het meest betrouwbaar voor exacte hoeveelheden. "
            "De afbeelding kan extra context geven.\n\n"
            + "\n\n---\n\n".join(bronnen) +
            "\n\nGeef je antwoord in dit EXACTE format:\n\n"
            "TITEL: [receptnaam]\n"
            "TAGS: [komma-gescheiden tags uit: vis, vlees, vegetarisch, vegan, snel, comfort food, Aziatisch, Italiaans, ontbijt, lunch, diner, snack]\n"
            "PORTIES: [aantal]\nTIJD: [bereidingstijd in minuten]\nBESCHRIJVING: [1 zin]\n"
            "===\nINGREDIENTEN:\n- [hoeveelheid] [eenheid] [ingrediënt]\n\n"
            "BEREIDING:\n1. [stap]\n\n"
            "Regels: altijd Nederlands, eenheden g/ml/el/tl/stuks, stappen max 3 zinnen, neem ALLES over."
        )

        print("Recept extraheren...")
        raw = call_claude(prompt, api_key)
        recipe = parse_recipe(raw)
        print(f"  Titel: {recipe['titel']}")
        print(f"  {len(recipe['ingredienten'])} ingrediënten, {len(recipe['stappen'])} stappen")

        bron_url = verificatie.get("web_url") or "Foto"
        bron_naam = verificatie.get("bron") or "Foto"
        if verificatie.get("ig_account"):
            bron_naam = f"@{verificatie['ig_account']} (Instagram)"
        img_url = verificatie.get("afbeelding_url", "")

        return save_recipe(recipe, bron_url, bron_naam, img_url, api_key)

    # URL-modus
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = sys.stdin.read().strip()

    if not url:
        print("Gebruik:\n  python3 recept_saver.py <URL>\n  python3 recept_saver.py --foto <pad>")
        sys.exit(1)

    api_key = get_api_key()
    bron_naam = get_site_name(url)

    # ── 1. Pagina ophalen ──
    print(f"Ophalen: {url}")

    # YouTube: speciale behandeling
    is_youtube = "youtube.com" in url or "youtu.be" in url
    if is_youtube:
        print("  YouTube gedetecteerd — beschrijving + transcript ophalen...")
        yt = extract_youtube_data(url)
        if yt:
            yt_parts = []
            if yt["titel"]:
                yt_parts.append(f"Video titel: {yt['titel']}")
            if yt["beschrijving"]:
                yt_parts.append(f"Video beschrijving:\n{yt['beschrijving']}")
            if yt["transcript"]:
                yt_parts.append(f"Video transcript (gesproken tekst):\n{yt['transcript'][:5000]}")

            if yt_parts:
                tekst = "\n\n".join(yt_parts)
                img_url = yt.get("afbeelding", "")
                html = None  # geen HTML pagina nodig

                print(f"  Titel: {yt['titel']}")
                print(f"  Beschrijving: {len(yt.get('beschrijving',''))} chars")
                print(f"  Transcript: {len(yt.get('transcript',''))} chars")
                print(f"  Afbeelding: {'gevonden' if img_url else 'geen'}")

                # Skip de rest van stap 1
                print("Recept extraheren...")
                prompt = (
                    "Extraheer het recept uit onderstaande YouTube video-data en vertaal alles naar het Nederlands.\n"
                    "De beschrijving bevat vaak het recept. Het transcript bevat gesproken instructies.\n"
                    "Combineer beide bronnen voor het meest complete recept.\n\n"
                    "Geef je antwoord in dit EXACTE format:\n\n"
                    "TITEL: [receptnaam]\n"
                    "TAGS: [komma-gescheiden tags uit: vis, vlees, vegetarisch, vegan, snel, comfort food, Aziatisch, Italiaans, ontbijt, lunch, diner, snack]\n"
                    "PORTIES: [aantal]\nTIJD: [bereidingstijd in minuten]\nBESCHRIJVING: [1 zin]\n"
                    "===\nINGREDIENTEN:\n- [hoeveelheid] [eenheid] [ingrediënt]\n\n"
                    "BEREIDING:\n1. [stap]\n\n"
                    "Regels:\n- Altijd Nederlands\n- Eenheden: g, ml, el, tl, stuks\n"
                    "- Stappen max 3 zinnen\n- Neem ALLE ingrediënten en stappen over met EXACTE hoeveelheden\n\n"
                    f"YouTube video data:\n{tekst[:10000]}"
                )

                raw = call_claude(prompt, api_key)
                recipe = parse_recipe(raw)
                print(f"  Titel: {recipe['titel']}")
                print(f"  Tags: {', '.join(recipe['tags'])}")
                print(f"  {recipe['tijd']} min · {recipe['porties']} porties")
                print(f"  {len(recipe['ingredienten'])} ingrediënten, {len(recipe['stappen'])} stappen")

                # Spring naar stap 3
                print("Website bijwerken...")
                recipe_id = update_website(recipe, url, img_url, bron_naam)
                website_url = f"{WEBSITE_BASE}/recept.html?id={recipe_id}"
                print(f"  {website_url}")

                print("Notitie aanmaken...")
                img_b64 = download_image_base64(img_url)
                img_html_note = f'<p><img src="data:image/jpeg;base64,{img_b64}" style="width:100%"></p>' if img_b64 else ""
                hashtags = " ".join(f"#{t.replace(' ', '')}" for t in recipe["tags"])
                recept_html_note = body_to_html(recipe["body"])
                meta_parts = []
                if recipe["tijd"]: meta_parts.append(f"{recipe['tijd']} min")
                meta_parts.append(f"{recipe['porties']} porties")
                full_html = (
                    f"<h1>{html_mod.escape(recipe['titel'])}</h1>\n{img_html_note}\n"
                    f'<p style="color:gray">{" · ".join(meta_parts)}</p>\n<p>{hashtags}</p>\n'
                    f"{recept_html_note}\n<br>\n<hr>\n"
                    f'<p><a href="{html_mod.escape(website_url)}">Bekijk op receptensite</a></p>\n'
                    f'<p>Bron: <a href="{html_mod.escape(url)}">{html_mod.escape(bron_naam)}</a></p>'
                )
                note_name = create_note(recipe["titel"], full_html)
                if note_name: print(f"  Notitie: {note_name}")
                print(f"\nKlaar! {recipe['titel']}")
                return recipe["titel"]

    html = fetch_simple(url)

    tekst = ""
    json_ld = None

    if html:
        # Probeer eerst JSON-LD (meest betrouwbare bron)
        json_ld = extract_json_ld_recipe(html)
        if json_ld:
            print("  JSON-LD Recipe gevonden (beste bron)")
            tekst = json.dumps(json_ld, ensure_ascii=False)
        else:
            tekst = strip_html(html)

    # Als geen JSON-LD en geen receptinhoud → Playwright
    if not json_ld and (not tekst or not has_recipe_content(tekst)):
        print("  Geen receptinhoud gevonden, probeer headless browser...")
        pw_html, pw_tekst = fetch_playwright(url)
        if pw_html:
            # Check JSON-LD in Playwright HTML
            json_ld = extract_json_ld_recipe(pw_html)
            if json_ld:
                print("  JSON-LD Recipe gevonden via browser")
                tekst = json.dumps(json_ld, ensure_ascii=False)
                html = pw_html
            else:
                html = pw_html
                tekst = pw_tekst if pw_tekst else strip_html(pw_html)

    if not tekst or (not json_ld and not has_recipe_content(tekst)):
        # Laatste poging: gebruik og:title, og:description, URL slug
        meta_info = []
        if html:
            og_title = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html, re.I)
            og_desc = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html, re.I)
            title_tag = re.search(r'<title>([^<]+)</title>', html, re.I)
            desc_tag = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html, re.I)
            if og_title: meta_info.append(f"Titel: {og_title.group(1)}")
            elif title_tag: meta_info.append(f"Titel: {title_tag.group(1)}")
            if og_desc: meta_info.append(f"Beschrijving: {og_desc.group(1)}")
            elif desc_tag: meta_info.append(f"Beschrijving: {desc_tag.group(1)}")
        slug_info = url.split("/")[-1].replace("-", " ").replace("?", " ")
        meta_info.append(f"URL slug: {slug_info}")
        tekst = "\n".join(meta_info) + f"\nURL: {url}"
        print(f"  Fallback op metadata: {meta_info[0] if meta_info else slug_info}")

    # Afbeelding
    img_url = extract_og_image(html) if html else ""
    # JSON-LD heeft soms ook een image
    if not img_url and json_ld:
        ld_img = json_ld.get("image", "")
        if isinstance(ld_img, list):
            img_url = ld_img[0] if ld_img else ""
        elif isinstance(ld_img, dict):
            img_url = ld_img.get("url", "")
        elif isinstance(ld_img, str):
            img_url = ld_img
    print(f"  Afbeelding: {'gevonden' if img_url else 'geen'}")

    # ── 2. Claude API ──
    print("Recept extraheren...")
    has_full_content = json_ld or has_recipe_content(tekst) if tekst else False

    if has_full_content:
        bron_type = "JSON-LD Recipe data" if json_ld else "Pagina-inhoud"
        prompt = (
            f"Extraheer het recept uit onderstaande {bron_type.lower()} en vertaal alles naar het Nederlands.\n\n"
            "Geef je antwoord in dit EXACTE format:\n\n"
            "TITEL: [receptnaam]\n"
            "TAGS: [komma-gescheiden tags uit: vis, vlees, vegetarisch, vegan, snel, comfort food, Aziatisch, Italiaans, ontbijt, lunch, diner, snack]\n"
            "PORTIES: [aantal]\nTIJD: [bereidingstijd in minuten]\nBESCHRIJVING: [1 zin]\n"
            "===\nINGREDIENTEN:\n- [hoeveelheid] [eenheid] [ingrediënt]\n\n"
            "BEREIDING:\n1. [stap]\n\n"
            "Regels:\n- Altijd Nederlands\n- Eenheden: g, ml, el, tl, stuks\n"
            "- Stappen max 3 zinnen\n- Neem ALLE stappen en ingrediënten over met EXACTE hoeveelheden\n\n"
            f"{bron_type} van {url}:\n{tekst[:10000]}"
        )
    else:
        # Fallback: vraag Claude om het recept uit zijn kennis te genereren
        prompt = (
            "Ik heb de volgende info over een recept. De pagina kon niet volledig worden opgehaald.\n"
            "Gebruik je kennis om het VOLLEDIGE recept te genereren met alle ingrediënten en stappen.\n\n"
            f"{tekst}\n\n"
            "Geef je antwoord in dit EXACTE format:\n\n"
            "TITEL: [receptnaam]\n"
            "TAGS: [komma-gescheiden tags uit: vis, vlees, vegetarisch, vegan, snel, comfort food, Aziatisch, Italiaans, ontbijt, lunch, diner, snack]\n"
            "PORTIES: [aantal]\nTIJD: [bereidingstijd in minuten]\nBESCHRIJVING: [1 zin]\n"
            "===\nINGREDIENTEN:\n- [hoeveelheid] [eenheid] [ingrediënt]\n\n"
            "BEREIDING:\n1. [stap]\n\n"
            "Regels:\n- Altijd Nederlands\n- Eenheden: g, ml, el, tl, stuks\n"
            "- Stappen max 3 zinnen\n- Geef een compleet, realistisch recept"
        )

    raw = call_claude(prompt, api_key)
    recipe = parse_recipe(raw)
    print(f"  Titel: {recipe['titel']}")
    print(f"  Tags: {', '.join(recipe['tags'])}")
    print(f"  {recipe['tijd']} min · {recipe['porties']} porties")
    print(f"  {len(recipe['ingredienten'])} ingrediënten, {len(recipe['stappen'])} stappen")

    # ── 3. Opslaan ──
    return save_recipe(recipe, url, bron_naam, img_url, api_key)


if __name__ == "__main__":
    main()
