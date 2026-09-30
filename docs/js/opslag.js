/* Opslaan en verwijderen via de GitHub API.
   De site is statisch: recepten.json staat gewoon in de repo. Om vanaf je
   telefoon iets toe te voegen of weg te gooien schrijven we dat bestand
   rechtstreeks terug met een persoonlijk toegangstoken.

   Over dat token: het staat in localStorage van dit toestel. Wie je telefoon
   in handen heeft, kan het lezen. Gebruik daarom een fine-grained token dat
   alleen déze repo mag beschrijven (Contents: read and write), niets anders,
   en geef het een vervaldatum. */

const REPO = 'x9yxfsz8cd-ux/recepten';
const BESTAND = 'docs/data/recepten.json';
const TOKEN_SLEUTEL = 'github_token';

function leesToken() {
  try { return localStorage.getItem(TOKEN_SLEUTEL) || ''; } catch { return ''; }
}

function bewaarToken(t) {
  try { localStorage.setItem(TOKEN_SLEUTEL, t.trim()); } catch {}
}

function heeftToken() { return leesToken().length > 10; }

function tak() {
  // De site draait vanaf de branch waar hij op staat; schrijf naar dezelfde.
  return window.GITHUB_TAK || 'apple-ontwerp';
}

async function githubVerzoek(pad, opties = {}) {
  const token = leesToken();
  if (!token) throw new Error('Geen GitHub-token ingesteld');
  const res = await fetch(`https://api.github.com/repos/${REPO}/${pad}`, {
    ...opties,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...(opties.headers || {}),
    },
  });
  if (!res.ok) {
    const tekst = await res.text().catch(() => '');
    if (res.status === 401) throw new Error('Token wordt niet geaccepteerd. Controleer of hij nog geldig is.');
    if (res.status === 403) throw new Error('Token mist rechten. Hij heeft Contents: read and write nodig op deze repo.');
    if (res.status === 404) throw new Error('Repo of bestand niet gevonden. Klopt de branchnaam?');
    if (res.status === 409) throw new Error('Het bestand is ondertussen gewijzigd. Probeer het opnieuw.');
    throw new Error(`GitHub gaf ${res.status}. ${tekst.slice(0, 120)}`);
  }
  return res;
}

/* Haalt recepten.json op inclusief de sha, die je nodig hebt om terug te schrijven. */
async function haalRecepten() {
  const res = await githubVerzoek(`contents/${encodeURIComponent(BESTAND)}?ref=${tak()}`);
  const data = await res.json();
  // atob geeft bytes; via TextDecoder komen de accenten goed door
  const bytes = Uint8Array.from(atob(data.content.replace(/\n/g, '')), c => c.charCodeAt(0));
  const json = JSON.parse(new TextDecoder('utf-8').decode(bytes));
  return { sha: data.sha, data: json };
}

async function schrijfRecepten(json, sha, bericht) {
  const tekst = JSON.stringify(json, null, 2) + '\n';
  const bytes = new TextEncoder().encode(tekst);
  let binair = '';
  bytes.forEach(b => { binair += String.fromCharCode(b); });
  await githubVerzoek(`contents/${encodeURIComponent(BESTAND)}`, {
    method: 'PUT',
    body: JSON.stringify({
      message: bericht,
      content: btoa(binair),
      sha,
      branch: tak(),
    }),
  });
}

/* Verwijdert één recept. Geeft terug hoeveel er over zijn. */
async function verwijderRecept(id, titel) {
  const { sha, data } = await haalRecepten();
  const voor = data.recepten.length;
  data.recepten = data.recepten.filter(r => r.id !== id);
  if (data.recepten.length === voor) throw new Error('Dat recept staat al niet meer in de lijst.');
  await schrijfRecepten(data, sha, `Recept verwijderd: ${titel}`);
  return data.recepten.length;
}

/* Voegt een recept toe of vervangt er een met hetzelfde id. */
async function bewaarRecept(recept) {
  const { sha, data } = await haalRecepten();
  const bestond = data.recepten.some(r => r.id === recept.id);
  data.recepten = data.recepten.filter(r => r.id !== recept.id);
  data.recepten.push(recept);
  await schrijfRecepten(data, sha,
    `${bestond ? 'Recept bijgewerkt' : 'Recept'}: ${recept.titel}`);
  return data.recepten.length;
}

/* Vraagt het token in de pagina zelf. Een prompt() blokkeert de hele browser
   en ziet er op iOS uit als een foutmelding; dit leest als onderdeel van de app.
   Roept `klaar()` aan zodra er een token bewaard is. */
function vraagToken(plek, klaar) {
  if (plek.querySelector('.token-veld')) return;

  const blok = document.createElement('div');
  blok.className = 'token-veld';
  blok.innerHTML = `
    <label for="token-invoer">GitHub-token</label>
    <input id="token-invoer" type="password" autocomplete="off"
           placeholder="github_pat_…" spellcheck="false">
    <button type="button" class="token-bewaar">Bewaren</button>
    <p>Maak er een aan op <b>github.com/settings/tokens?type=beta</b> met alleen
       deze repo en <b>Contents: read and write</b>. Hij blijft op dit toestel.</p>`;
  plek.appendChild(blok);

  const invoer = blok.querySelector('#token-invoer');
  invoer.focus();
  const opslaan = () => {
    const t = invoer.value.trim();
    if (t.length < 10) { invoer.focus(); return; }
    bewaarToken(t);
    blok.remove();
    klaar();
  };
  blok.querySelector('.token-bewaar').addEventListener('click', opslaan);
  invoer.addEventListener('keydown', e => { if (e.key === 'Enter') opslaan(); });
}
