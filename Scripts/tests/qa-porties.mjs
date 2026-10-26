import fs from 'fs';
const opslag = new Map();
globalThis.localStorage = { getItem: k => opslag.has(k)?opslag.get(k):null,
  setItem:(k,v)=>opslag.set(k,String(v)), removeItem:k=>opslag.delete(k) };
Object.defineProperty(globalThis,"navigator",{value:{},configurable:true});
const G = new Function(fs.readFileSync('docs/js/gedeeld.js','utf8')
  + '; return { portiesVoor, formatHoeveelheid, STANDAARD_PORTIES };')();
const rs = JSON.parse(fs.readFileSync('docs/data/recepten.json','utf8')).recepten;

let ok=0, fout=0;
const test=(n,a,b)=>{const g=JSON.stringify(a)===JSON.stringify(b);g?ok++:fout++;
  console.log(`  ${g?'ok  ':'FOUT'}  ${n}${g?'':`  kreeg ${JSON.stringify(a)} verwacht ${JSON.stringify(b)}`}`);};

console.log('── standaard vier porties ─────────────────────────────────');
const gewoon = rs.find(r => r.porties === 2 && !(r.benodigdheden||[]).some(b=>/springvorm|bakvorm|taartvorm|pizzasteen/i.test(b)));
test(`"${gewoon.titel.slice(0,34)}" (recept zegt ${gewoon.porties})`, G.portiesVoor(gewoon), 4);

console.log('\n── vaste vorm houdt zijn eigen aantal ─────────────────────');
const vorm = rs.filter(r => (r.benodigdheden||[]).some(b=>/springvorm|bakvorm|taartvorm|pizzasteen/i.test(b)));
console.log(`  ${vorm.length} recepten met een vaste vorm`);
vorm.forEach(r => test(`"${r.titel.slice(0,34)}" blijft ${r.porties}`, G.portiesVoor(r), r.porties));

console.log('\n── eigen keuze wint ───────────────────────────────────────');
opslag.set(`porties_${gewoon.id}`, '6');
test('eigen keuze 6', G.portiesVoor(gewoon), 6);
if (vorm[0]) { opslag.set(`porties_${vorm[0].id}`, '16');
  test('eigen keuze wint ook bij een vaste vorm', G.portiesVoor(vorm[0]), 16); }
opslag.set(`porties_${gewoon.id}`, '0');
test('nul valt terug op standaard', G.portiesVoor(gewoon), 4);
opslag.set(`porties_${gewoon.id}`, 'onzin');
test('onzin valt terug op standaard', G.portiesVoor(gewoon), 4);
opslag.set(`porties_${gewoon.id}`, '-3');
test('negatief valt terug op standaard', G.portiesVoor(gewoon), 4);
opslag.delete(`porties_${gewoon.id}`);

console.log('\n── afronden van hoeveelheden ──────────────────────────────');
test('400 g voor 4 van 2 porties -> 800',  G.formatHoeveelheid(400,4,2,'g'), '800');
test('1 ui voor 4 van 2 porties -> 2',     G.formatHoeveelheid(1,4,2,'stuks'), '2');
test('1 teentje voor 3 van 2 -> 1,5',      G.formatHoeveelheid(1,3,2,'teentje'), '1,5');
test('1 teentje voor 7 van 2 -> 4 (heel)', G.formatHoeveelheid(1,7,2,'teentje'), '4');
test('halve bol blijft een halve',         G.formatHoeveelheid(1,1,2,'bol'), '0,5');
test('0 blijft leeg',                      G.formatHoeveelheid(0,4,2,'g'), '');
test('100 ml gelijk aantal porties',       G.formatHoeveelheid(100,4,4,'ml'), '100');

console.log(`\n${ok} goed, ${fout} fout`);
