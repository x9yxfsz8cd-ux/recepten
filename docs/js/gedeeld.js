/* Gedeeld tussen overzicht, receptpagina en winkel.
   Alles staat in localStorage, dus per apparaat. Dat is bewust: in de winkel
   sta je met je eigen telefoon, en tijdens het koken wil je niet dat iemand
   anders jouw vinkjes weghaalt. */

const FAVORIETEN = 'favorieten';
const GEKOOKT = 'gekookt';

function leesLijst(sleutel) {
  try { return JSON.parse(localStorage.getItem(sleutel) || '[]'); }
  catch { return []; }
}

function leesObject(sleutel) {
  try { return JSON.parse(localStorage.getItem(sleutel) || '{}'); }
  catch { return {}; }
}

/* ── Favorieten ── */

function laadFavorieten() { return leesLijst(FAVORIETEN); }

function isFavoriet(id) { return laadFavorieten().includes(id); }

function wisselFavoriet(id) {
  const lijst = laadFavorieten();
  const i = lijst.indexOf(id);
  if (i === -1) lijst.push(id); else lijst.splice(i, 1);
  localStorage.setItem(FAVORIETEN, JSON.stringify(lijst));
  return i === -1;
}

/* ── Kookgeschiedenis ──
   Een eigen kookboek hoort te weten wat je echt maakt. Dat is ook de
   sortering op het overzicht: wat je vaak maakt staat bovenaan. */

function laadGekookt() { return leesObject(GEKOOKT); }

function aantalGemaakt(id) { return (laadGekookt()[id] || {}).aantal || 0; }

function laatstGemaakt(id) { return (laadGekookt()[id] || {}).laatst || null; }

/* Lokale datum, niet UTC: wie 's avonds kookt zou anders de dag ervoor krijgen. */
function vandaag() {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function noteerGemaakt(id) {
  const alles = laadGekookt();
  const nu = vandaag();
  alles[id] = { aantal: ((alles[id] || {}).aantal || 0) + 1, laatst: nu };
  localStorage.setItem(GEKOOKT, JSON.stringify(alles));
  return alles[id];
}

/* "3× gemaakt" of "nog niet gemaakt" — kort genoeg voor een kaartje */
function gemaaktTekst(id) {
  const n = aantalGemaakt(id);
  return n === 0 ? 'nog niet gemaakt' : `${n}× gemaakt`;
}

/* "3× gemaakt · laatst 12 september" voor op de receptpagina */
function gemaaktLangeTekst(id) {
  const n = aantalGemaakt(id);
  if (!n) return 'Nog niet gemaakt';
  const datum = laatstGemaakt(id);
  if (!datum) return `${n}× gemaakt`;
  const d = new Date(datum + 'T12:00:00');
  const mooi = d.toLocaleDateString('nl-NL', { day: 'numeric', month: 'long' });
  return `${n}× gemaakt · laatst ${mooi}`;
}

/* ── Weergave ── */

/* Alleen de eerste letter. text-transform:capitalize zou er "Kleine Tomaten"
   van maken, en zo schrijf je geen Nederlands. */
function metHoofdletter(tekst) {
  const t = String(tekst || '').trim();
  return t ? t[0].toUpperCase() + t.slice(1) : t;
}

/* ── Hoeveelheden ── */

function formatHoeveelheid(basis, huidig, basisPorties) {
  if (!basis) return '';
  const waarde = (basis / basisPorties) * huidig;
  const afgerond = Math.round(waarde * 10) / 10;
  return afgerond % 1 === 0 ? String(afgerond | 0) : String(afgerond).replace('.', ',');
}

/* Hoeveel pakken moet je kopen? Dat is de vraag in de winkel, niet hoeveel gram.
   Alleen bij gewicht en inhoud, want "4 stuks knoflook" betekent teentjes en
   geen bollen — dan zou de rekensom er flink naast zitten. */
function aantalVerpakkingen(nodig, eenheid, verpakking) {
  if (!nodig || !verpakking) return null;
  const m = String(verpakking).match(/([\d.,]+)\s*(g|gram|kg|ml|l|stuks?)/i);
  if (!m) return null;
  let inhoud = parseFloat(m[1].replace(',', '.'));
  let eenheidVerp = m[2].toLowerCase();
  if (eenheidVerp === 'kg') { inhoud *= 1000; eenheidVerp = 'g'; }
  if (eenheidVerp === 'l') { inhoud *= 1000; eenheidVerp = 'ml'; }
  const e = String(eenheid).toLowerCase();
  const vergelijkbaar = (e === 'g' && eenheidVerp === 'g')
                     || (e === 'ml' && eenheidVerp === 'ml');
  if (!vergelijkbaar || !inhoud) return null;
  return Math.max(1, Math.ceil(nodig / inhoud));
}
