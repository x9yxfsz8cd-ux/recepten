import fs from 'fs';
const html = fs.readFileSync('docs/recept.html','utf8');
const fn = html.slice(html.indexOf('function secondenInTekst'),
                      html.indexOf('return (!seconden || seconden > 4 * 3600) ? 0 : seconden;\n    }')
                      + 'return (!seconden || seconden > 4 * 3600) ? 0 : seconden;\n    }'.length);
const secondenInTekst = new Function(fn + '; return secondenInTekst;')();
const mmss = s => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;

let ok=0, fout=0;
const t = (tekst, verwacht) => {
  const g = secondenInTekst(tekst);
  const goed = g === verwacht; goed ? ok++ : fout++;
  console.log(`  ${goed?'ok  ':'FOUT'}  ${JSON.stringify(tekst).slice(0,62).padEnd(64)} ${mmss(g)}${goed?'':`  verwacht ${mmss(verwacht)}`}`);
};
console.log('── losse gevallen ─────────────────────────────────────────────────────────');
t('Zet 30 minuten in de oven.', 1800);
t('Roerbak 6-8 minuten totdat ze bruin zijn.', 480);
t('Bak 30 seconden.', 30);
t('Laat 2 uur in de koelkast rusten.', 7200);
t('Verwarm de oven voor tot 200 °C hetelucht.', 0);
t('Snijd in blokjes van 2 cm en bak 10 minuten.', 600);
t('Kook de pasta 1 minuut korter dan de verpakking zegt.', 60);
t('Laat 10 à 12 minuten staan.', 720);
t('Zet het geheel 30 minuten in de oven op 180 graden.', 1800);
t('Voeg 400 g tomatenblokjes toe.', 0);
t('Laat 1,5 uur rijzen.', 0);              // 'vijf uur' zou fout zijn, 0 is veilig
t('Bak 12 minuten op 220 °C.', 720);
t('Rooster de walnoten 2-3 minuten.', 180);
t('Laat 20 minuten sudderen.', 1200);

console.log('\n── alle 289 stappen: waar vindt hij een tijd, en klopt die? ───────────────');
const rs = JSON.parse(fs.readFileSync('docs/data/recepten.json','utf8')).recepten;
let met=0, zonder=0;
const verdacht = [];
rs.forEach(r => r.stappen.forEach(s => {
  const sec = secondenInTekst(s.tekst);
  if (!sec) { zonder++; return; }
  met++;
  // verdacht: tijd gevonden terwijl er geen tijdwoord in de buurt staat,
  // of een tijd die veel langer is dan de totale bereidingstijd
  if (sec > (r.bereidingstijd || 0) * 60) verdacht.push([r.titel, mmss(sec), r.bereidingstijd, s.tekst]);
}));
console.log(`  ${met} stappen met een timer, ${zonder} zonder`);
if (verdacht.length) {
  console.log(`\n  ${verdacht.length} stappen met een timer langer dan de totale bereidingstijd:`);
  verdacht.forEach(([t_,s,b,tx]) => console.log(`    ${s} > ${b} min   ${t_.slice(0,32)}\n        ${tx.slice(0,100)}`));
} else console.log('  geen timer langer dan de bereidingstijd');
console.log(`\n${ok} goed, ${fout} fout`);
