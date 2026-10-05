/* Iconen voor ingrediënten zonder AH-productfoto.
   Water, zout en peper zijn geen boodschappen, dus daar hoort geen pak bij —
   maar een leeg vakje zegt niets. Een getekend icoontje laat in één oogopslag
   zien waar het om gaat. */

const INGREDIENT_ICONEN = [
  { sleutel: 'water',    woorden: ['water', 'kraanwater', 'kookwater', 'ijsblokjes'] },
  { sleutel: 'zout',     woorden: ['zout', 'zeezout', 'keukenzout'] },
  { sleutel: 'peper',    woorden: ['peper', 'pepervlokken', 'chilivlokken', 'chili'] },
  { sleutel: 'olie',     woorden: ['olie', 'olijfolie', 'zonnebloemolie', 'sesamolie'] },
  { sleutel: 'kruiden',  woorden: ['kruiden', 'oregano', 'tijm', 'basilicum', 'peterselie',
                                   'dille', 'bieslook', 'salie', 'dragon', 'rozemarijn',
                                   'za', 'paprikapoeder', 'komijn', 'kaneel', 'nootmuskaat'] },
  { sleutel: 'citroen',  woorden: ['citroen', 'limoen', 'citroensap'] },
  { sleutel: 'azijn',    woorden: ['azijn', 'balsamico'] },
  { sleutel: 'suiker',   woorden: ['suiker', 'honing', 'siroop', 'maple'] },
  { sleutel: 'bouillon', woorden: ['bouillon', 'bouillonblokje', 'bouillonpoeder'] },
  { sleutel: 'boter',    woorden: ['boter', 'roomboter', 'margarine'] },
  { sleutel: 'rijst',    woorden: ['rijst', 'bulgur', 'couscous', 'polenta', 'quinoa',
                                   'orzo', 'gierst',
                                   // samenstellingen: 'rijst' is te kort voor de
                                   // includes-regel, dus die staan er voluit bij
                                   'jasmijnrijst', 'langgraanrijst', 'sushirijst',
                                   'risottorijst', 'basmatirijst', 'zilvervliesrijst',
                                   'pandanrijst', 'parelgort', 'gort', 'spelt', 'farro'] },
  { sleutel: 'noten',    woorden: ['noten', 'walnoten', 'hazelnoten', 'amandelen', 'cashew',
                                   'pistache', 'amandelschaafsel', 'pijnboompitten'] },
  { sleutel: 'zaad',     woorden: ['sesamzaad', 'sesamzaadjes', 'zonnebloempitten',
                                   'pompoenpitten', 'maanzaad'] },
  { sleutel: 'kokos',    woorden: ['kokos', 'kokosmelk', 'kokosrasp'] },
  { sleutel: 'poeder',   woorden: ['poeder', 'custardpoeder', 'maizena', 'bakpoeder', 'gist'] },
  { sleutel: 'gember',   woorden: ['gember', 'kurkuma', 'galangal'] },
  { sleutel: 'saus',     woorden: ['ketchup', 'sojasaus', 'mayonaise', 'mosterd', 'sriracha',
                                   'harissa', 'miso', 'currypasta', 'vissaus'] },
  { sleutel: 'tomaat',   woorden: ['tomaat', 'tomaten', 'tomaatjes', 'passata', 'tomatenpuree'] },
  { sleutel: 'groente',  woorden: ['aardpeer', 'bleekselderij', 'knolselderij', 'pastinaak',
                                   'koolraap', 'rammenas', 'doperwten', 'erwten', 'tuinbonen'] },
  { sleutel: 'bal',      woorden: ['falafel', 'wontons', 'balletjes', 'gyoza', 'dumplings'] },
  { sleutel: 'brood',    woorden: ['brood', 'pitabrood', 'platbrood', 'flatbread',
                                   'stokbrood', 'ciabatta', 'boterham'] },
];

const ICOON_PADEN = {
  water:    '<path d="M12 3.5c3.4 4 5.5 6.7 5.5 9.3a5.5 5.5 0 1 1-11 0c0-2.6 2.1-5.3 5.5-9.3z"/>',
  zout:     '<path d="M8.5 9h7l.8 10.5H7.7zM9.5 9V6.5a2.5 2.5 0 0 1 5 0V9"/><path d="M11 12.5h.01M13 14.5h.01"/>',
  peper:    '<path d="M9 8.5h6l.7 11H8.3z"/><path d="M9.5 8.5c0-1.6.5-3 2.5-3s2.5 1.4 2.5 3"/><path d="M11 12h.01M13 14h.01M11 16h.01"/>',
  olie:     '<path d="M10 4h4v2.4l3 4.1V20H7v-9.5l3-4.1z"/><path d="M7 14h10"/>',
  kruiden:  '<path d="M12 20V9"/><path d="M12 12c0-3.3 2.7-6 6-6 0 3.3-2.7 6-6 6z"/><path d="M12 15c0-2.8-2.2-5-5-5 0 2.8 2.2 5 5 5z"/>',
  citroen:  '<ellipse cx="12" cy="12" rx="8" ry="6" transform="rotate(-30 12 12)"/><path d="M12 12l4.5-2.6M12 12l-4.5 2.6M12 12l1.3 4.8M12 12l-1.3-4.8"/>',
  azijn:    '<path d="M10.5 3.5h3V7l2.5 3.5V20H8v-9.5L10.5 7z"/><path d="M8 13h8"/><path d="M11 3.5V2.5h2v1"/>',
  suiker:   '<path d="M5 9h14v10H5z"/><path d="M5 9l2.5-4h9L19 9"/><path d="M9.5 5v4M14.5 5v4"/>',
  bouillon: '<path d="M4.5 10h15a7.5 7.5 0 0 1-7.5 7.5A7.5 7.5 0 0 1 4.5 10z"/><path d="M9 6.5c0-1 1-1.2 1-2.2M13 6.5c0-1 1-1.2 1-2.2"/><path d="M3.5 20h17"/>',
  boter:    '<path d="M3.5 12.5l4-4h13v7h-13z"/><path d="M7.5 8.5v7"/><path d="M3.5 12.5v7h13v-4"/>',
  rijst:    '<ellipse cx="12" cy="7.5" rx="5.6" ry="1.6"/><ellipse cx="10.4" cy="12" rx="5.6" ry="1.6"/><ellipse cx="13.2" cy="16.5" rx="5.6" ry="1.6"/>',
  noten:    '<path d="M12 4c3.6 0 6 2.8 6 6.6 0 4.6-3 9-6 9s-6-4.4-6-9C6 6.8 8.4 4 12 4z"/><path d="M12 5.5v13"/><path d="M12 10c1.4-1.2 2.6-1.8 4-2M12 14c1.4-1.2 2.6-1.8 4-2M12 10c-1.4-1.2-2.6-1.8-4-2M12 14c-1.4-1.2-2.6-1.8-4-2"/>',
  zaad:     '<ellipse cx="8" cy="8" rx="1.5" ry="2.4" transform="rotate(-30 8 8)"/><ellipse cx="15" cy="10" rx="1.5" ry="2.4" transform="rotate(20 15 10)"/><ellipse cx="10" cy="15" rx="1.5" ry="2.4" transform="rotate(10 10 15)"/><ellipse cx="16" cy="16.5" rx="1.5" ry="2.4" transform="rotate(-25 16 16.5)"/>',
  kokos:    '<circle cx="12" cy="12" r="8"/><circle cx="9.9" cy="9.6" r=".95"/><circle cx="14.1" cy="9.6" r=".95"/><circle cx="12" cy="13" r=".95"/>',
  poeder:   '<path d="M7 6.5h10l-1 13H8z"/><path d="M7 6.5l1-2.5h8l1 2.5"/><path d="M9.5 11h5"/>',
  gember:   '<path d="M11 19.5c-3 0-4.5-2-4.5-4.2 0-2 1.4-2.8 1.4-4.3 0-1.3-1-1.9-1-3.2C6.9 6.2 8.4 5 10.2 5c1.6 0 2.2 1 3.4 1 1 0 1.5-.7 2.5-.7 1.4 0 2.4 1.1 2.4 2.6 0 1.6-1.3 2.2-1.3 3.6 0 1.6 1.3 2.3 1.3 4 0 2.3-1.8 4-4.2 4z"/><path d="M11.5 9.5c.8.8 1.2 2 1.2 3.4"/>',
  saus:     '<path d="M10 3.5h4v2.2c0 .7.3 1 .9 1.5 1 .8 1.6 1.7 1.6 3V20H7.5V10.2c0-1.3.6-2.2 1.6-3 .6-.5.9-.8.9-1.5V3.5z"/><path d="M7.5 12h9"/>',
  tomaat:   '<circle cx="12" cy="13.5" r="6.5"/><path d="M12 7V5"/><path d="M12 7c-1.4-.2-2.4-1-3-2.2 1.4-.3 2.4.2 3 1.2.6-1 1.6-1.5 3-1.2-.6 1.2-1.6 2-3 2.2z"/>',
  groente:  '<path d="M12 20c-2.8 0-4.8-2.3-4.8-5.4 0-3 2-5.6 4.8-5.6s4.8 2.6 4.8 5.6C16.8 17.7 14.8 20 12 20z"/><path d="M12 9V4.5"/><path d="M12 6.5c1.6 0 2.8-.9 3.4-2.3-1.7-.4-2.9.3-3.4 1.5"/>',
  bal:      '<circle cx="8.5" cy="14.5" r="4"/><circle cx="15.5" cy="14.5" r="4"/><circle cx="12" cy="8" r="4"/>',
  brood:    '<path d="M4.5 11.5c0-3.3 3.4-5.5 7.5-5.5s7.5 2.2 7.5 5.5v5.5a1.5 1.5 0 0 1-1.5 1.5H6a1.5 1.5 0 0 1-1.5-1.5z"/><path d="M8 9.2c.9-.7 1.9-1.1 3-1.2M13 8c1.1.1 2.1.5 3 1.2"/>',
};

/* Welk icoon past bij deze ingrediëntnaam? Null als we het niet weten. */
function ingredientIcoon(naam) {
  const woorden = String(naam).toLowerCase().split(/[^a-zà-ÿ]+/).filter(Boolean);
  for (const { sleutel, woorden: lijst } of INGREDIENT_ICONEN) {
    const raak = woorden.some(w => lijst.some(v =>
      w === v || w.startsWith(v) || (v.length >= 6 && w.includes(v))));
    if (raak) return sleutel;
  }
  return null;
}

/* Geeft het blokje links van een ingrediënt: productfoto, icoon, of leeg. */
function ingredientVakje(naam, product) {
  if (product && product.afbeelding) {
    return `<img class="ingredient-foto" src="${product.afbeelding}" alt="" loading="lazy">`;
  }
  const icoon = ingredientIcoon(naam);
  if (icoon) {
    return `<span class="ingredient-foto--icoon" aria-hidden="true">
      <svg viewBox="0 0 24 24">${ICOON_PADEN[icoon]}</svg></span>`;
  }
  return '<span class="ingredient-foto--leeg"></span>';
}
