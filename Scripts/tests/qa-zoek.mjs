import fs from 'fs';
const html = fs.readFileSync('docs/index.html','utf8');
const fn = html.slice(html.indexOf('const GEEN_INGREDIENT'), html.indexOf('function renderRecepten'));
const zoekMatch = new Function(fn + '; return zoekMatch;')();
const rs = JSON.parse(fs.readFileSync('docs/data/recepten.json','utf8')).recepten;
const tel = t => rs.filter(r => zoekMatch(r, t.toLowerCase())).length;

let ok=0, fout=0;
const test=(n,a,b)=>{const g=a===b;g?ok++:fout++;console.log(`  ${g?'ok  ':'FOUT'}  ${n}: ${a}${g?'':` (verwacht ${b})`}`);};
const hoogstens=(n,t,max)=>{const a=tel(t);const g=a<=max;g?ok++:fout++;
  console.log(`  ${g?'ok  ':'FOUT'}  "${t}" geeft ${a} recepten${g?'':` — te veel, hoogstens ${max}`}`);};
const minstens=(n,t,min)=>{const a=tel(t);const g=a>=min;g?ok++:fout++;
  console.log(`  ${g?'ok  ':'FOUT'}  "${t}" geeft ${a} recepten${g?'':` — te weinig, minstens ${min}`}`);};

console.log('── korte termen mogen niet alles raken ────────────────────');
hoogstens('ui','ui',22);
hoogstens('ei','ei',8);
hoogstens('ui','ui',22);

console.log('\n── maar moeten wel vinden wat er is ───────────────────────');
minstens('zalm','zalm',3);
minstens('pasta','pasta',5);
minstens('citroen','citroen',4);

console.log('\n── samenstellingen vanaf vier letters ─────────────────────');
minstens('kool','kool',1);
console.log('    (kool hoort bloemkool en boerenkool te vinden)');
const koolhits = rs.filter(r => zoekMatch(r,'kool')).map(r=>r.titel.slice(0,40));
koolhits.forEach(t => console.log('      ' + t));

console.log('\n── leeg en rare invoer ────────────────────────────────────');
test('lege term raakt alles', tel(''), rs.length);
test('regex-tekens geven geen crash', typeof tel('a+b('), 'number');
test('accent', typeof tel('crème'), 'number');

console.log(`\n${ok} goed, ${fout} fout`);
