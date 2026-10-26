import fs from 'fs';
let ok = 0, fout = 0;
const test = (naam, waarde, verwacht) => {
  const goed = JSON.stringify(waarde) === JSON.stringify(verwacht);
  goed ? ok++ : fout++;
  console.log(`  ${goed ? 'ok  ' : 'FOUT'}  ${naam}${goed ? '' : `\n          kreeg ${JSON.stringify(waarde)}, verwacht ${JSON.stringify(verwacht)}`}`);
};

const opslag = new Map();
globalThis.localStorage = {
  getItem: k => opslag.has(k) ? opslag.get(k) : null,
  setItem: (k,v) => opslag.set(k,String(v)), removeItem: k => opslag.delete(k) };
const maakEl = () => ({ innerHTML:'', textContent:'', dataset:{}, hidden:false,
  querySelectorAll:()=>[], addEventListener:()=>{}, setAttribute:()=>{},
  getAttribute:()=>null, classList:{add(){},remove(){},contains(){return false}}, appendChild(){} });
const els = {};
globalThis.document = { getElementById: id => (els[id] ||= maakEl()),
  createElement: maakEl, body:{appendChild(){}}, querySelectorAll:()=>[] };
globalThis.location = { search: '' };
globalThis.window = { location:{} };
Object.defineProperty(globalThis,'navigator',{value:{clipboard:{writeText:async()=>{}}},configurable:true});
globalThis.fetch = async (u) => ({ ok:true,
  json: async () => JSON.parse(fs.readFileSync('docs/' + u.replace('./',''),'utf8')) });
globalThis.setTimeout = () => null; globalThis.clearTimeout = () => {};

const html = fs.readFileSync('docs/winkel.html','utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
const code = (fs.readFileSync('docs/js/gedeeld.js','utf8') + '\n'
  + fs.readFileSync('docs/js/ingredient-icoon.js','utf8') + '\n' + script)
  .replace(/\n\s*init\(\);\s*$/,'\n').replace(/if \('serviceWorker' in navigator\).*/,'');
const A = new Function(code + `
  return { init, renderLijst, renderRecent, naarHerinneringen, geselecteerd,
           wisselRecept, isVoorraad, portiesVoor,
           keuze: () => gekozen, zet: (x) => { gekozen = x; }, lijst: () => teHalen,
           laad: async () => { recepten = (await (await fetch('./data/recepten.json')).json()).recepten;
                               producten = await (await fetch('./data/ah-producten.json')).json(); } };`)();
await A.laad();

console.log('\n── lege keuze ──────────────────────────────────────────');
A.zet([]); A.renderLijst();
test('lege staat toont uitnodiging', /Tik hierboven aan/.test(els['lijst'].innerHTML), true);
test('samenvatting zegt "Kies een recept"', els['samenvatting'].textContent, 'Kies een recept');
test('teHalen is leeg', A.lijst().length, 0);

console.log('\n── versturen zonder lijst ──────────────────────────────');
let gestuurd = null;
globalThis.window.location = { set href(v){ gestuurd = v; }, get href(){ return gestuurd; } };
await A.naarHerinneringen();
test('stuurt niets bij lege lijst', gestuurd, null);

console.log('\n── recept aan- en uitzetten ────────────────────────────');
A.zet([]); A.wisselRecept('r001');
test('aanzetten voegt toe', A.keuze(), ['r001']);
test('bewaard in localStorage', JSON.parse(localStorage.getItem('winkel_gekozen')), ['r001']);
A.wisselRecept('r001');
test('nogmaals tikken haalt weg', A.keuze(), []);
test('leeg bewaard', JSON.parse(localStorage.getItem('winkel_gekozen')), []);

console.log('\n── verdwenen recept in de bewaarde keuze ───────────────');
opslag.set('winkel_gekozen', JSON.stringify(['r001','bestaat-niet-meer','r1791230000']));
globalThis.location.search = '';
await A.init();
test('onbekend id wordt eruit gefilterd', A.keuze(), ['r001','r1791230000']);
test('opgeschoonde keuze wordt teruggeschreven',
     JSON.parse(localStorage.getItem('winkel_gekozen')), ['r001','r1791230000']);

console.log('\n── stukgelopen opslag ──────────────────────────────────');
opslag.set('winkel_gekozen', 'geen json {{{');
await A.init();
test('kapotte json geeft geen crash', Array.isArray(A.keuze()), true);
opslag.set('winkel_gekozen', JSON.stringify({niet:'een array'}));
await A.init();
test('verkeerd type geeft lege keuze', A.keuze(), []);

console.log('\n── migratie van de oude opslag ─────────────────────────');
opslag.clear();
opslag.set('winkel_laatste', 'r001');
await A.init();
test('oude enkele keuze komt mee', A.keuze(), ['r001']);

console.log('\n── binnenkomen met ?id= ────────────────────────────────');
opslag.clear();
opslag.set('winkel_gekozen', JSON.stringify(['r001']));
globalThis.location.search = '?id=r1791230000';
await A.init();
test('?id= wordt toegevoegd, niet vervangen', A.keuze(), ['r001','r1791230000']);
globalThis.location.search = '?id=r001';
await A.init();
test('al gekozen ?id= geeft geen dubbele', A.keuze(), ['r001','r1791230000']);

console.log(`\n${ok} goed, ${fout} fout`);
process.exit(fout ? 1 : 0);
